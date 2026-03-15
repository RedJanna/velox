"""Template engine — loads templates from YAML and renders with substitutions."""

from pathlib import Path

import structlog
import yaml

from velox.config.settings import settings

logger = structlog.get_logger(__name__)


class Template:
    """A single message template."""

    def __init__(self, template_id: str, intent: str, state: str, language: str, template: str) -> None:
        """Initialize template entity."""
        self.id = template_id
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


def reload_templates() -> list[Template]:
    """Reload all templates from disk."""
    logger.info("templates_reloading")
    return load_templates()
