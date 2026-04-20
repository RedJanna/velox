"""Template engine — loads templates from YAML and renders with substitutions."""

from __future__ import annotations

import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

import structlog
import yaml

from velox.config.settings import settings

logger = structlog.get_logger(__name__)


class Template:
    """A single message template."""

    def __init__(
        self,
        template_id: str,
        title: str,
        intent: str,
        state: str,
        language: str,
        template: str,
    ) -> None:
        """Initialize template entity."""
        self.id = template_id
        self.title = title
        self.intent = intent
        self.state = state
        self.language = language
        self.template = template

    def render(self, **kwargs: object) -> str:
        """Render template with variables."""
        try:
            return self.template.format_map(kwargs)
        except KeyError as error:
            logger.warning("template_missing_variable", template_id=self.id, missing_key=str(error))
            return self.template


_templates: list[Template] = []


def load_templates() -> list[Template]:
    """Load all template YAML files from configured templates directory."""
    global _templates
    _templates.clear()

    templates_dir = Path(settings.templates_dir)
    if not templates_dir.exists():
        logger.warning("templates_dir_not_found", path=str(templates_dir))
        return _templates

    yaml_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
    logger.info("templates_loading", count=len(yaml_files), directory=str(templates_dir))

    for yaml_file in yaml_files:
        try:
            with yaml_file.open(encoding="utf-8") as file_obj:
                raw_list = yaml.safe_load(file_obj)

            if not isinstance(raw_list, list):
                logger.warning("template_yaml_not_list_skipped", file=str(yaml_file))
                continue

            for entry in raw_list:
                template = Template(
                    template_id=entry["id"],
                    title=entry.get("title", entry["id"]),
                    intent=entry.get("intent", ""),
                    state=entry.get("state", ""),
                    language=entry.get("language", "tr"),
                    template=entry["template"],
                )
                _templates.append(template)

            logger.info("templates_loaded_from_file", file=yaml_file.name, count=len(raw_list))
        except Exception:
            logger.exception("template_file_load_failed", file=str(yaml_file))

    return _templates


def find_template(intent: str, state: str, language: str = "tr") -> Template | None:
    """Find best matching template by intent/state/language priority."""
    for template in _templates:
        if template.intent == intent and template.state == state and template.language == language:
            return template

    for template in _templates:
        if template.intent == intent and template.language == language:
            return template

    if language != "en":
        for template in _templates:
            if template.intent == intent and template.state == state and template.language == "en":
                return template

    return None


def render_template(intent: str, state: str, language: str = "tr", **variables: object) -> str | None:
    """Find and render a template string."""
    template = find_template(intent, state, language)
    if template is None:
        return None
    return template.render(**variables)


def get_all_templates() -> list[Template]:
    """Get all cached templates."""
    return _templates.copy()


def find_template_by_id(template_id: str) -> Template | None:
    """Return one cached template by its ID."""
    for template in _templates:
        if template.id == template_id:
            return template
    return None


def reload_templates() -> list[Template]:
    """Reload all templates from disk."""
    logger.info("templates_reloading")
    return load_templates()


def create_template_definition(
    *,
    title: str,
    intent: str,
    state: str,
    language: str,
    template_text: str,
    template_id: str | None = None,
) -> dict[str, str]:
    """Persist one template into the Chat Lab custom template file."""
    target_path = Path(settings.templates_dir) / "chatlab_custom.yaml"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    resolved_id = _slugify_template_id(template_id or title)
    existing_items = _read_template_entries(target_path)

    if any(str(item.get("id") or "").strip() == resolved_id for item in existing_items):
        raise ValueError("Ayni template kimligi zaten mevcut.")

    entry = {
        "id": resolved_id,
        "title": str(title).strip(),
        "intent": str(intent).strip(),
        "state": str(state).strip(),
        "language": str(language).strip() or "tr",
        "template": str(template_text).strip(),
    }
    existing_items.append(entry)
    _write_template_entries(target_path, existing_items)
    reload_templates()
    return entry


def _read_template_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or []
    if not isinstance(data, list):
        raise ValueError("Template dosyasi liste formatinda degil.")
    return [item for item in data if isinstance(item, dict)]


def _write_template_entries(path: Path, entries: list[dict[str, Any]]) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as file_obj:
            yaml.safe_dump(
                entries,
                file_obj,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
            temp_path = Path(file_obj.name)
        temp_path.replace(path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _slugify_template_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    compact = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    if not compact:
        raise ValueError("Template kimligi veya basligi bos olamaz.")
    return compact
