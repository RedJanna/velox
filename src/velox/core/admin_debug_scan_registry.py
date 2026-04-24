"""Static scan registry for report-only admin debug runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from velox.models.admin_debug import DebugFindingCategory, DebugRunScope

ScanResponseType = Literal["html", "json"]


@dataclass(frozen=True)
class ScanTarget:
    """One safe report-only target evaluated by the admin debug worker."""

    key: str
    view_key: str
    screen: str
    path: str
    response_type: ScanResponseType
    performance_budget_ms: int
    expected_json_keys: tuple[str, ...] = ()
    expected_markers: tuple[str, ...] = ()
    failure_category: DebugFindingCategory = DebugFindingCategory.ROUTING_ISSUE


def build_scan_targets(scope: DebugRunScope, *, hotel_id: int) -> list[ScanTarget]:
    """Return safe scan targets for the requested debug scope."""
    targets = [
        ScanTarget(
            key="admin_shell",
            view_key="dashboard",
            screen="Admin Panel",
            path="/admin",
            response_type="html",
            performance_budget_ms=3000,
            expected_markers=("NexlumeAI Yönetim Paneli", "Hata Taraması", "Hata Raporları"),
            failure_category=DebugFindingCategory.ROUTING_ISSUE,
        ),
        ScanTarget(
            key="dashboard_overview",
            view_key="dashboard",
            screen="Genel Bakış",
            path=f"/api/v1/admin/dashboard/overview?hotel_id={hotel_id}",
            response_type="json",
            performance_budget_ms=3000,
            expected_json_keys=("cards", "recent_conversations", "recent_tickets", "recent_holds"),
            failure_category=DebugFindingCategory.ROUTING_ISSUE,
        ),
        ScanTarget(
            key="conversations",
            view_key="conversations",
            screen="Konuşmalar",
            path=f"/api/v1/admin/conversations?hotel_id={hotel_id}&page=1&per_page=20",
            response_type="json",
            performance_budget_ms=3000,
            expected_json_keys=("items", "total", "page", "per_page"),
            failure_category=DebugFindingCategory.BROKEN_INTERACTION,
        ),
        ScanTarget(
            key="holds",
            view_key="holds",
            screen="Onay Bekleyenler",
            path=f"/api/v1/admin/holds?hotel_id={hotel_id}&page=1&per_page=20",
            response_type="json",
            performance_budget_ms=3500,
            expected_json_keys=("items", "total", "page", "per_page"),
            failure_category=DebugFindingCategory.BROKEN_INTERACTION,
        ),
        ScanTarget(
            key="tickets",
            view_key="tickets",
            screen="Destek Talepleri",
            path=f"/api/v1/admin/tickets?hotel_id={hotel_id}&page=1&per_page=20",
            response_type="json",
            performance_budget_ms=3000,
            expected_json_keys=("items", "total", "page", "per_page"),
            failure_category=DebugFindingCategory.BROKEN_INTERACTION,
        ),
        ScanTarget(
            key="hotels",
            view_key="hotels",
            screen="Otel Bilgileri",
            path="/api/v1/admin/hotels",
            response_type="json",
            performance_budget_ms=3000,
            expected_json_keys=("items",),
            failure_category=DebugFindingCategory.ROUTING_ISSUE,
        ),
        ScanTarget(
            key="faq",
            view_key="faq",
            screen="Sık Sorulan Sorular",
            path=f"/api/v1/admin/hotels/{hotel_id}/faq",
            response_type="json",
            performance_budget_ms=3000,
            expected_json_keys=("items", "total"),
            failure_category=DebugFindingCategory.BROKEN_INTERACTION,
        ),
        ScanTarget(
            key="restaurant_slots",
            view_key="restaurant",
            screen="Restoran Yönetimi",
            path=f"/api/v1/admin/hotels/{hotel_id}/restaurant/slots",
            response_type="json",
            performance_budget_ms=3500,
            expected_json_keys=("items", "total"),
            failure_category=DebugFindingCategory.BROKEN_INTERACTION,
        ),
        ScanTarget(
            key="notification_phones",
            view_key="notifications",
            screen="Bildirim Ayarları",
            path="/api/v1/admin/notification-phones",
            response_type="json",
            performance_budget_ms=2500,
            failure_category=DebugFindingCategory.BROKEN_INTERACTION,
        ),
        ScanTarget(
            key="system_overview",
            view_key="system",
            screen="Sistem Durumu",
            path="/api/v1/admin/system/overview",
            response_type="json",
            performance_budget_ms=4000,
            expected_json_keys=("status", "checks", "panel_url"),
            failure_category=DebugFindingCategory.PERFORMANCE_ISSUE,
        ),
        ScanTarget(
            key="debug_runs",
            view_key="debug",
            screen="Hata Raporları",
            path="/api/v1/admin/debug/runs?limit=20",
            response_type="json",
            performance_budget_ms=2500,
            expected_json_keys=("items",),
            failure_category=DebugFindingCategory.ROUTING_ISSUE,
        ),
        ScanTarget(
            key="session_preferences",
            view_key="system",
            screen="Kimlik ve Oturum",
            path="/api/v1/admin/session/preferences",
            response_type="json",
            performance_budget_ms=2500,
            expected_json_keys=("has_access_cookie", "has_trusted_device", "session_active"),
            failure_category=DebugFindingCategory.AUTH_SESSION_ISSUE,
        ),
    ]
    if scope.include_chatlab_iframe:
        targets.extend(
            [
                ScanTarget(
                    key="chatlab_shell",
                    view_key="chatlab",
                    screen="Chat Lab",
                    path="/admin/chat-lab",
                    response_type="html",
                    performance_budget_ms=3000,
                    expected_markers=("Velox Chat Lab", "Ayarlar", "Tanılama"),
                    failure_category=DebugFindingCategory.IFRAME_ISSUE,
                ),
                ScanTarget(
                    key="chatlab_live_feed",
                    view_key="chatlab",
                    screen="Chat Lab",
                    path="/api/v1/test/chat/live-feed",
                    response_type="json",
                    performance_budget_ms=3500,
                    expected_json_keys=("conversations", "operation_mode", "total"),
                    failure_category=DebugFindingCategory.IFRAME_ISSUE,
                ),
                ScanTarget(
                    key="chatlab_templates",
                    view_key="chatlab",
                    screen="Chat Lab",
                    path=f"/api/v1/test/chat/templates?hotel_id={hotel_id}",
                    response_type="json",
                    performance_budget_ms=3500,
                    expected_json_keys=("context", "templates"),
                    failure_category=DebugFindingCategory.BROKEN_INTERACTION,
                ),
                ScanTarget(
                    key="chatlab_models",
                    view_key="chatlab",
                    screen="Chat Lab",
                    path="/api/v1/test/models",
                    response_type="json",
                    performance_budget_ms=3500,
                    expected_json_keys=("models", "current"),
                    failure_category=DebugFindingCategory.BROKEN_INTERACTION,
                ),
            ]
        )

    if scope.target == "all_panel":
        return targets

    requested_view = str(scope.target_view or "").strip().lower()
    filtered = [target for target in targets if target.view_key == requested_view]
    return filtered or [
        ScanTarget(
            key="admin_shell_fallback",
            view_key=requested_view or "unknown",
            screen="Admin Panel",
            path="/admin",
            response_type="html",
            performance_budget_ms=3000,
            expected_markers=("NexlumeAI Yönetim Paneli",),
            failure_category=DebugFindingCategory.ROUTING_ISSUE,
        )
    ]
