"""Background worker that processes queued admin debug runs."""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import os
import time
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import structlog
from fastapi import FastAPI

from velox.api.middleware.debug_report_only import REPORT_ONLY_BLOCK_MESSAGE
from velox.config.settings import settings
from velox.core.admin_debug_scan_registry import ScanTarget, build_scan_targets
from velox.db.repositories.admin_debug import AdminDebugRepository
from velox.models.admin_debug import (
    DebugArtifactType,
    DebugFindingCategory,
    DebugFindingSeverity,
    DebugRunResponse,
    DebugRunStatus,
)
from velox.utils.admin_debug_security import DEBUG_SESSION_HEADER, create_debug_session_token

logger = structlog.get_logger(__name__)

DEBUG_RUNNER_LOOP_IDLE_SECONDS = 3
DEBUG_HTTP_TIMEOUT_SECONDS = 15.0
DEBUG_ARTIFACT_ROOT = Path("data/admin_debug_runs")


@dataclass(frozen=True)
class DebugBrowserCapability:
    """Resolved Playwright browser-scan readiness for admin debug runs."""

    available: bool
    reason: str | None
    mode: str
    target_base_url: str


def _fingerprint(*parts: object) -> str:
    normalized = "|".join(str(part).strip().lower() for part in parts if str(part).strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _summarize_duration(duration_ms: int, budget_ms: int) -> tuple[DebugFindingSeverity, str]:
    if duration_ms >= budget_ms * 2:
        return DebugFindingSeverity.HIGH, "Yanıt süresi kritik eşiği aştı."
    return DebugFindingSeverity.MEDIUM, "Yanıt süresi hedef bütçeyi aştı."


def _response_excerpt(response: httpx.Response) -> str:
    body = response.text.strip()
    if not body:
        return ""
    return body[:400]


async def run_admin_debug_loop(app: FastAPI) -> None:
    """Continuously claim and process queued admin debug runs."""
    repository = AdminDebugRepository()
    while True:
        try:
            run = await repository.claim_next_queued_run(
                worker_meta_json={
                    "worker_name": "admin_debug_http_runner",
                    "runtime": "httpx_asgi",
                    "report_only": True,
                }
            )
            if run is None:
                await asyncio.sleep(DEBUG_RUNNER_LOOP_IDLE_SECONDS)
                continue
            await _process_run(app, repository, run)
        except asyncio.CancelledError:
            logger.info("admin_debug_worker_cancelled")
            return
        except Exception:
            logger.exception("admin_debug_worker_unexpected_error")
            await asyncio.sleep(DEBUG_RUNNER_LOOP_IDLE_SECONDS)


async def _process_run(
    app: FastAPI,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
) -> None:
    started = time.perf_counter()
    run_id = UUID(run.id)
    summary_counts = {
        DebugFindingSeverity.CRITICAL: 0,
        DebugFindingSeverity.HIGH: 0,
        DebugFindingSeverity.MEDIUM: 0,
        DebugFindingSeverity.LOW: 0,
        DebugFindingSeverity.INFO: 0,
    }
    iframes_scanned = 0
    blocked_mutation_attempts = 0
    scanned_screens: set[str] = set()
    scan_targets = build_scan_targets(run.scope, hotel_id=run.hotel_id)
    token = create_debug_session_token(
        run_id=run_id,
        hotel_id=run.hotel_id,
        triggered_by_user_id=run.triggered_by_user_id,
    )
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)

    async with httpx.AsyncClient(
        transport=transport,
        base_url=_scan_base_url(),
        timeout=DEBUG_HTTP_TIMEOUT_SECONDS,
        headers={DEBUG_SESSION_HEADER: token},
        follow_redirects=True,
    ) as client:
        if not scan_targets:
            await _record_finding(
                repository=repository,
                run=run,
                severity=DebugFindingSeverity.MEDIUM,
                category=DebugFindingCategory.ROUTING_ISSUE,
                screen="Hata Taraması",
                description="Bu kapsam için tanımlı bir tarama reçetesi bulunamadı.",
                action_label=f"Kapsam: {run.scope.target}",
                technical_cause="current_view için eşleşen tarama hedefi tanımlı değil.",
                suggested_fix="İlgili admin görünümü için scan registry kaydı eklenmeli.",
                evidence={"target_view": run.scope.target_view, "scope": run.scope.model_dump(mode="json")},
            )
            summary_counts[DebugFindingSeverity.MEDIUM] += 1
        for target in scan_targets:
            current_run = await repository.get_run(run_id=run_id, hotel_id=run.hotel_id)
            if current_run is None:
                logger.warning("admin_debug_run_missing_during_execution", run_id=run.id)
                return
            if current_run.status == DebugRunStatus.CANCELLED or current_run.cancel_requested_at is not None:
                await _finish_cancelled_run(
                    repository=repository,
                    run=current_run,
                    summary=_build_summary(
                        counts=summary_counts,
                        scanned_screens=scanned_screens,
                        duration_seconds=int(time.perf_counter() - started),
                        iframes_scanned=iframes_scanned,
                        blocked_mutation_attempts=blocked_mutation_attempts,
                    ),
                )
                return
            await repository.touch_heartbeat(run_id=run_id, hotel_id=run.hotel_id)
            scanned_screens.add(target.screen)
            if target.key == "chatlab_shell":
                iframes_scanned += 1
            blocked = await _scan_target(
                client=client,
                repository=repository,
                run=run,
                target=target,
                debug_session_token=token,
                summary_counts=summary_counts,
            )
            blocked_mutation_attempts += blocked

    await repository.mark_completed(
        run_id=run_id,
        hotel_id=run.hotel_id,
        summary_json=_build_summary(
            counts=summary_counts,
            scanned_screens=scanned_screens,
            duration_seconds=int(time.perf_counter() - started),
            iframes_scanned=iframes_scanned,
            blocked_mutation_attempts=blocked_mutation_attempts,
        ),
    )


async def _finish_cancelled_run(
    *,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    summary: dict[str, int],
) -> None:
    await repository.mark_cancelled(
        run_id=UUID(run.id),
        hotel_id=run.hotel_id,
        summary_json=summary,
    )


async def _scan_target(
    *,
    client: httpx.AsyncClient,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    target: ScanTarget,
    debug_session_token: str,
    summary_counts: dict[DebugFindingSeverity, int],
) -> int:
    started = time.perf_counter()
    response: httpx.Response | None = None
    blocked_mutation_attempts = 0
    try:
        response = await client.get(target.path)
    except httpx.HTTPError as exc:
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=DebugFindingSeverity.HIGH,
            category=DebugFindingCategory.NETWORK_FAILURE,
            screen=target.screen,
            description=f"{target.screen} tarama isteği başarısız oldu.",
            action_label=f"GET {target.path}",
            technical_cause=type(exc).__name__,
            suggested_fix="İlgili route veya bağımlılık hataları loglarla birlikte doğrulanmalı.",
            evidence={"path": target.path, "response_type": target.response_type},
        )
        return blocked_mutation_attempts

    duration_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code == 409 and REPORT_ONLY_BLOCK_MESSAGE in response.text:
        blocked_mutation_attempts += 1

    if response.status_code != 200:
        category = DebugFindingCategory.NETWORK_FAILURE
        severity = DebugFindingSeverity.MEDIUM
        technical_cause = f"HTTP {response.status_code}"
        if response.status_code in {401, 403}:
            category = DebugFindingCategory.AUTH_SESSION_ISSUE
            severity = DebugFindingSeverity.HIGH
        elif response.status_code >= 500:
            severity = DebugFindingSeverity.HIGH
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=severity,
            category=category,
            screen=target.screen,
            description=f"{target.screen} hedefi beklenen 200 yanıtını döndürmedi.",
            action_label=f"GET {target.path}",
            technical_cause=technical_cause,
            suggested_fix="İlgili endpoint logları, bağımlılık durumu ve auth akışı kontrol edilmeli.",
            evidence={
                "path": target.path,
                "status_code": response.status_code,
                "response_excerpt": _response_excerpt(response),
                "duration_ms": duration_ms,
            },
        )
        return blocked_mutation_attempts

    if target.response_type == "json":
        await _validate_json_target(
            repository=repository,
            run=run,
            target=target,
            response=response,
            summary_counts=summary_counts,
            duration_ms=duration_ms,
        )
    else:
        await _validate_html_target(
            repository=repository,
            run=run,
            target=target,
            response=response,
            summary_counts=summary_counts,
            duration_ms=duration_ms,
        )
        await _maybe_capture_browser_screenshot(
            repository=repository,
            run=run,
            target=target,
            debug_session_token=debug_session_token,
        )

    if duration_ms > target.performance_budget_ms:
        severity, description = _summarize_duration(duration_ms, target.performance_budget_ms)
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=severity,
            category=DebugFindingCategory.PERFORMANCE_ISSUE,
            screen=target.screen,
            description=f"{target.screen}: {description}",
            action_label=f"GET {target.path}",
            technical_cause="Yanıt süresi hedef bütçeyi aştı.",
            suggested_fix="İlgili endpoint sorguları ve bağımlılık çağrıları performans açısından incelenmeli.",
            evidence={
                "path": target.path,
                "duration_ms": duration_ms,
                "budget_ms": target.performance_budget_ms,
            },
        )
    return blocked_mutation_attempts


async def _validate_json_target(
    *,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    target: ScanTarget,
    response: httpx.Response,
    summary_counts: dict[DebugFindingSeverity, int],
    duration_ms: int,
) -> None:
    try:
        payload = response.json()
    except ValueError as exc:
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=DebugFindingSeverity.HIGH,
            category=DebugFindingCategory.NETWORK_FAILURE,
            screen=target.screen,
            description=f"{target.screen} JSON yanıtı çözümlenemedi.",
            action_label=f"GET {target.path}",
            technical_cause=type(exc).__name__,
            suggested_fix="Yanıt gövdesi ve ilgili route dönüş tipi doğrulanmalı.",
            evidence={"path": target.path, "response_excerpt": _response_excerpt(response), "duration_ms": duration_ms},
        )
        return

    if isinstance(payload, list):
        if target.expected_json_keys:
            await _counted_finding(
                repository=repository,
                run=run,
                summary_counts=summary_counts,
                severity=DebugFindingSeverity.MEDIUM,
                category=target.failure_category,
                screen=target.screen,
                description=f"{target.screen} yanıt biçimi beklenen nesne yapısında değil.",
                action_label=f"GET {target.path}",
                technical_cause="Endpoint beklenen JSON obje yapısı yerine liste döndürdü.",
                suggested_fix=(
                    "İlgili endpoint response contract sabitlenmeli veya tarama "
                    "reçetesi liste yanitini kabul edecek sekilde guncellenmeli."
                ),
                evidence={"path": target.path, "duration_ms": duration_ms},
            )
        return

    if not isinstance(payload, Mapping):
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=DebugFindingSeverity.MEDIUM,
            category=target.failure_category,
            screen=target.screen,
            description=f"{target.screen} yanıt biçimi beklenen nesne yapısında değil.",
            action_label=f"GET {target.path}",
            technical_cause="Endpoint beklenen JSON obje yapısı yerine farklı bir payload döndürdü.",
            suggested_fix="İlgili endpoint response contract sabitlenmeli.",
            evidence={"path": target.path, "duration_ms": duration_ms},
        )
        return

    missing_keys = [key for key in target.expected_json_keys if key not in payload]
    if missing_keys:
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=DebugFindingSeverity.MEDIUM,
            category=target.failure_category,
            screen=target.screen,
            description=f"{target.screen} yanıtında beklenen alanlar eksik.",
            action_label=f"GET {target.path}",
            technical_cause="Endpoint response contract'ı ile UI tarama beklentisi uyuşmuyor.",
            suggested_fix="Eksik alanlar geri eklenmeli veya tarama reçetesi yeni sözleşmeye göre güncellenmeli.",
            evidence={
                "path": target.path,
                "missing_keys": missing_keys,
                "returned_keys": sorted(str(key) for key in payload),
                "duration_ms": duration_ms,
            },
        )


async def _validate_html_target(
    *,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    target: ScanTarget,
    response: httpx.Response,
    summary_counts: dict[DebugFindingSeverity, int],
    duration_ms: int,
) -> None:
    body = response.text
    missing_markers = [marker for marker in target.expected_markers if marker not in body]
    if missing_markers:
        await _counted_finding(
            repository=repository,
            run=run,
            summary_counts=summary_counts,
            severity=DebugFindingSeverity.MEDIUM,
            category=target.failure_category,
            screen=target.screen,
            description=f"{target.screen} HTML yüzeyinde beklenen işaretler bulunamadı.",
            action_label=f"GET {target.path}",
            technical_cause="HTML iskeleti beklenen modül veya etiketleri üretmedi.",
            suggested_fix="İlgili HTML route çıktısı ve embed edilen asset işaretleri gözden geçirilmeli.",
            evidence={"path": target.path, "missing_markers": missing_markers, "duration_ms": duration_ms},
        )


def _build_summary(
    *,
    counts: dict[DebugFindingSeverity, int],
    scanned_screens: set[str],
    duration_seconds: int,
    iframes_scanned: int,
    blocked_mutation_attempts: int,
) -> dict[str, int]:
    finding_count = sum(counts.values())
    return {
        "finding_count": finding_count,
        "critical_count": counts[DebugFindingSeverity.CRITICAL],
        "high_count": counts[DebugFindingSeverity.HIGH],
        "medium_count": counts[DebugFindingSeverity.MEDIUM],
        "low_count": counts[DebugFindingSeverity.LOW],
        "info_count": counts[DebugFindingSeverity.INFO],
        "screens_scanned": len(scanned_screens),
        "iframes_scanned": iframes_scanned,
        "popups_scanned": 0,
        "blocked_mutation_attempts": blocked_mutation_attempts,
        "duration_seconds": max(duration_seconds, 0),
    }


async def _counted_finding(
    *,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    summary_counts: dict[DebugFindingSeverity, int],
    severity: DebugFindingSeverity,
    category: DebugFindingCategory,
    screen: str,
    description: str,
    action_label: str,
    technical_cause: str,
    suggested_fix: str,
    evidence: dict[str, Any],
) -> None:
    summary_counts[severity] += 1
    await _record_finding(
        repository=repository,
        run=run,
        severity=severity,
        category=category,
        screen=screen,
        description=description,
        action_label=action_label,
        technical_cause=technical_cause,
        suggested_fix=suggested_fix,
        evidence=evidence,
    )


async def _record_finding(
    *,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    severity: DebugFindingSeverity,
    category: DebugFindingCategory,
    screen: str,
    description: str,
    action_label: str,
    technical_cause: str | None,
    suggested_fix: str | None,
    evidence: dict[str, Any],
) -> None:
    await repository.append_finding(
        run_id=UUID(run.id),
        hotel_id=run.hotel_id,
        category=category,
        severity=severity,
        screen=screen,
        description=description,
        action_label=action_label,
        technical_cause=technical_cause,
        suggested_fix=suggested_fix,
        fingerprint=_fingerprint(category.value, severity.value, screen, action_label, description),
        evidence=evidence,
    )


def _artifact_relative_path(run_id: UUID, target_key: str) -> str:
    return (Path(str(run_id)) / "screenshots" / f"{target_key}.png").as_posix()


def _artifact_destination(run_id: UUID, target_key: str) -> Path:
    destination = DEBUG_ARTIFACT_ROOT / _artifact_relative_path(run_id, target_key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _playwright_browser_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    configured_root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    if configured_root and configured_root != "0":
        roots.append(Path(configured_root))
    roots.extend((Path.home() / ".cache" / "ms-playwright", Path("/ms-playwright")))

    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(root)
    return tuple(deduped)


def _has_playwright_browser_installation() -> bool:
    for root in _playwright_browser_roots():
        try:
            if not root.exists():
                continue
            if any(root.glob("chromium-*")) or any(root.glob("chromium_headless_shell-*")):
                return True
        except OSError:
            continue
    return False


def get_browser_scan_capability() -> DebugBrowserCapability:
    """Return the current Playwright/browser availability for debug scans."""
    mode = settings.admin_debug_browser_mode
    target_base_url = settings.admin_debug_browser_base_url

    try:
        importlib.import_module("playwright.async_api")
    except Exception:
        return DebugBrowserCapability(
            available=False,
            reason="Playwright Python paketi yuklu degil.",
            mode=mode,
            target_base_url=target_base_url,
        )

    if not _has_playwright_browser_installation():
        return DebugBrowserCapability(
            available=False,
            reason="Chromium browser paketi yuklu degil.",
            mode=mode,
            target_base_url=target_base_url,
        )

    return DebugBrowserCapability(
        available=True,
        reason=None,
        mode=mode,
        target_base_url=target_base_url,
    )


def _scan_base_url() -> str:
    return settings.admin_debug_browser_base_url


def _browser_target_url(target: ScanTarget) -> str:
    base_url = _scan_base_url()
    if target.path == "/admin" and target.view_key:
        return f"{base_url}{target.path}#{target.view_key}"
    return f"{base_url}{target.path}"


async def _maybe_capture_browser_screenshot(
    *,
    repository: AdminDebugRepository,
    run: DebugRunResponse,
    target: ScanTarget,
    debug_session_token: str,
) -> None:
    if target.response_type != "html":
        return

    try:
        playwright_module = importlib.import_module("playwright.async_api")
        async_playwright = playwright_module.async_playwright
    except Exception as exc:
        logger.info(
            "admin_debug_browser_scan_unavailable",
            run_id=run.id,
            target=target.key,
            reason=type(exc).__name__,
        )
        return

    try:
        async with async_playwright() as playwright:
            browser = None
            context = None
            try:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1440, "height": 1024},
                    ignore_https_errors=True,
                    extra_http_headers={DEBUG_SESSION_HEADER: debug_session_token},
                )
                page = await context.new_page()
                await page.goto(_browser_target_url(target), wait_until="domcontentloaded", timeout=10000)
                with suppress(Exception):
                    await page.wait_for_load_state("networkidle", timeout=3000)
                await page.wait_for_timeout(800)
                screenshot_bytes = await page.screenshot(type="png", full_page=True)
                destination = _artifact_destination(UUID(run.id), target.key)
                destination.write_bytes(screenshot_bytes)
                await repository.append_artifact(
                    run_id=UUID(run.id),
                    artifact_type=DebugArtifactType.SCREENSHOT,
                    storage_path=_artifact_relative_path(UUID(run.id), target.key),
                    mime_type="image/png",
                    metadata={
                        "source": "browser_scan",
                        "target_key": target.key,
                        "target_path": target.path,
                        "screen": target.screen,
                    },
                )
            finally:
                if context is not None:
                    await context.close()
                if browser is not None:
                    await browser.close()
    except Exception:
        logger.exception(
            "admin_debug_browser_scan_failed",
            run_id=run.id,
            target=target.key,
        )
