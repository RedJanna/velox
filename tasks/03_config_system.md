# Task 03: Configuration System

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`

## Objective
Implement the hotel profile loader (YAML to Pydantic), the escalation matrix loader, and the template engine. Ensure all configuration data is cached in memory and available at app startup.

## Prerequisites
- Task 01 completed (project setup)
- Task 02 completed (database layer)
- YAML data files exist:
  - `data/hotel_profiles/kassandra_oludeniz.yaml`
  - `data/escalation_matrix.yaml`

---

## Step 1: Review Existing Configuration

The following files already exist and should NOT be modified unless specified:

- `src/velox/config/settings.py` — Application settings loaded from `.env`. Contains paths:
  - `hotel_profiles_dir: str = "data/hotel_profiles"`
  - `escalation_matrix_path: str = "data/escalation_matrix.yaml"`
  - `templates_dir: str = "data/templates"`
  - `scenarios_dir: str = "data/scenarios"`

- `src/velox/config/constants.py` — All enums (Intent, ConversationState, RiskFlag, Role, etc.)

- `src/velox/models/hotel_profile.py` — Pydantic model `HotelProfile` with nested models:
  - `LocalizedText`, `ContactInfo`, `RoomType`, `BoardType`, `RateMapping`
  - `CancellationRule`, `TransferRouteConfig`, `RestaurantConfig`

- `src/velox/models/escalation.py` — Pydantic models:
  - `EscalationMatrixEntry` (risk_flag, level, route_to_role, priority, action, etc.)
  - `EscalationResult`

- `data/hotel_profiles/kassandra_oludeniz.yaml` — Full hotel profile for Kassandra Oludeniz (hotel_id: 21966)

- `data/escalation_matrix.yaml` — 25 risk flag entries across L0-L3 levels

**Source files**: Listed above

---

## Step 2: Implement Hotel Profile Loader

Create `src/velox/core/hotel_profile_loader.py`:

```python
"""Hotel profile loader — loads YAML files and parses into HotelProfile Pydantic models."""

from pathlib import Path

import yaml
import structlog

from velox.config.settings import settings
from velox.models.hotel_profile import HotelProfile

logger = structlog.get_logger(__name__)

# In-memory cache: hotel_id -> HotelProfile
_profiles: dict[int, HotelProfile] = {}


def load_all_profiles() -> dict[int, HotelProfile]:
    """
    Load all hotel profile YAML files from the configured directory.

    Reads every .yaml/.yml file in settings.hotel_profiles_dir,
    parses each into a HotelProfile model, and stores in the cache.

    Returns:
        dict mapping hotel_id (int) to HotelProfile
    """
    global _profiles
    _profiles.clear()

    profiles_dir = Path(settings.hotel_profiles_dir)
    if not profiles_dir.exists():
        logger.warning("Hotel profiles directory not found", path=str(profiles_dir))
        return _profiles

    yaml_files = list(profiles_dir.glob("*.yaml")) + list(profiles_dir.glob("*.yml"))
    logger.info("Loading hotel profiles", count=len(yaml_files), dir=str(profiles_dir))

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, encoding="utf-8") as f:
                raw = yaml.safe_load(f)

            if raw is None:
                logger.warning("Empty YAML file skipped", file=str(yaml_file))
                continue

            profile = HotelProfile(**raw)
            _profiles[profile.hotel_id] = profile
            logger.info(
                "Hotel profile loaded",
                hotel_id=profile.hotel_id,
                hotel_name=profile.hotel_name.en,
                file=yaml_file.name,
            )
        except Exception:
            logger.exception("Failed to load hotel profile", file=str(yaml_file))

    return _profiles


def get_profile(hotel_id: int) -> HotelProfile | None:
    """Get a cached hotel profile by hotel_id."""
    return _profiles.get(hotel_id)


def get_all_profiles() -> dict[int, HotelProfile]:
    """Get all cached hotel profiles."""
    return _profiles.copy()


def reload_profiles() -> dict[int, HotelProfile]:
    """
    Reload all profiles from disk. Call this on admin API reload request
    or on SIGHUP signal.
    """
    logger.info("Reloading hotel profiles")
    return load_all_profiles()
```

### Key behaviors:
- Reads ALL `.yaml` and `.yml` files from `data/hotel_profiles/`
- Parses each into a `HotelProfile` Pydantic model (validation errors are logged and skipped)
- Caches in module-level `_profiles` dict keyed by `hotel_id`
- `reload_profiles()` clears and reloads the cache
- `get_profile(hotel_id)` returns a specific profile or `None`

**File to create**: `src/velox/core/hotel_profile_loader.py`

---

## Step 3: Implement Escalation Matrix Loader

Create `src/velox/escalation/matrix.py`:

```python
"""Escalation matrix loader — loads YAML and parses into EscalationMatrixEntry list."""

from pathlib import Path

import yaml
import structlog

from velox.config.settings import settings
from velox.models.escalation import EscalationMatrixEntry

logger = structlog.get_logger(__name__)

# In-memory cache
_matrix: list[EscalationMatrixEntry] = []
_matrix_by_flag: dict[str, EscalationMatrixEntry] = {}


def load_escalation_matrix() -> list[EscalationMatrixEntry]:
    """
    Load the escalation matrix from YAML file.

    Reads settings.escalation_matrix_path, parses each entry into
    an EscalationMatrixEntry model, and stores in cache.

    Returns:
        List of EscalationMatrixEntry objects
    """
    global _matrix, _matrix_by_flag
    _matrix.clear()
    _matrix_by_flag.clear()

    matrix_path = Path(settings.escalation_matrix_path)
    if not matrix_path.exists():
        logger.warning("Escalation matrix file not found", path=str(matrix_path))
        return _matrix

    try:
        with open(matrix_path, encoding="utf-8") as f:
            raw_list = yaml.safe_load(f)

        if not isinstance(raw_list, list):
            logger.error("Escalation matrix YAML is not a list", path=str(matrix_path))
            return _matrix

        for entry_dict in raw_list:
            try:
                entry = EscalationMatrixEntry(**entry_dict)
                _matrix.append(entry)
                _matrix_by_flag[entry.risk_flag] = entry
            except Exception:
                logger.exception("Failed to parse escalation entry", entry=entry_dict)

        logger.info("Escalation matrix loaded", count=len(_matrix), path=str(matrix_path))
    except Exception:
        logger.exception("Failed to load escalation matrix", path=str(matrix_path))

    return _matrix


def get_entry_by_flag(risk_flag: str) -> EscalationMatrixEntry | None:
    """Look up escalation entry by risk flag name."""
    return _matrix_by_flag.get(risk_flag)


def get_all_entries() -> list[EscalationMatrixEntry]:
    """Get all cached escalation matrix entries."""
    return _matrix.copy()


def get_highest_entry(risk_flags: list[str]) -> EscalationMatrixEntry | None:
    """
    Given multiple risk flags, return the entry with the highest escalation level.
    Tie-breaking: L3 > L2 > L1 > L0. Within same level, higher priority wins.

    Args:
        risk_flags: List of risk flag strings detected in conversation

    Returns:
        The highest-priority EscalationMatrixEntry, or None if no flags match
    """
    level_order = {"L3": 4, "L2": 3, "L1": 2, "L0": 1}
    priority_order = {"high": 3, "medium": 2, "low": 1}

    matched: list[EscalationMatrixEntry] = []
    for flag in risk_flags:
        entry = _matrix_by_flag.get(flag)
        if entry:
            matched.append(entry)

    if not matched:
        return None

    return max(
        matched,
        key=lambda e: (level_order.get(e.level, 0), priority_order.get(e.priority, 0)),
    )


def reload_matrix() -> list[EscalationMatrixEntry]:
    """Reload the escalation matrix from disk."""
    logger.info("Reloading escalation matrix")
    return load_escalation_matrix()
```

### Key behaviors:
- Reads `data/escalation_matrix.yaml` (a YAML list of entries)
- Parses each entry into `EscalationMatrixEntry` Pydantic model
- Provides `get_entry_by_flag(flag)` for single lookup
- Provides `get_highest_entry(flags)` for multi-flag resolution (highest level wins, then highest priority)
- `reload_matrix()` for hot reload

**File to create**: `src/velox/escalation/matrix.py`

---

## Step 4: Implement Template Engine

Create the templates directory and a sample template:

```bash
mkdir -p data/templates
```

Create `data/templates/greeting.yaml`:

```yaml
# Greeting templates
- id: "greeting_new_guest"
  intent: "greeting"
  state: "GREETING"
  language: "tr"
  template: "Merhaba! {hotel_name} ailesine hosgeldiniz. Size nasil yardimci olabilirim?"

- id: "greeting_new_guest_en"
  intent: "greeting"
  state: "GREETING"
  language: "en"
  template: "Hello! Welcome to {hotel_name}. How may I assist you today?"

- id: "greeting_returning"
  intent: "greeting"
  state: "GREETING"
  language: "tr"
  template: "Tekrar hosgeldiniz! Onceki talebinizle ilgili mi, yoksa yeni bir konuda mi yardimci olabilirim?"

- id: "greeting_returning_en"
  intent: "greeting"
  state: "GREETING"
  language: "en"
  template: "Welcome back! Would you like to continue with your previous request, or may I help with something new?"
```

Create `data/templates/booking.yaml`:

```yaml
- id: "stay_hold_created"
  intent: "stay_booking_create"
  state: "PENDING_APPROVAL"
  language: "tr"
  template: |
    Rezervasyon talebiniz olusturuldu!

    {summary}

    Talebiniz yonetimimize iletildi. Onay alir almaz sizi bilgilendiririz.

- id: "stay_hold_created_en"
  intent: "stay_booking_create"
  state: "PENDING_APPROVAL"
  language: "en"
  template: |
    Your reservation request has been created!

    {summary}

    Your request has been forwarded to our management. We will inform you as soon as it is approved.
```

Now create `src/velox/core/template_engine.py`:

```python
"""Template engine — loads templates from YAML and renders with variable substitution."""

from pathlib import Path

import yaml
import structlog

from velox.config.settings import settings

logger = structlog.get_logger(__name__)


class Template:
    """A single message template."""

    def __init__(self, id: str, intent: str, state: str, language: str, template: str) -> None:
        self.id = id
        self.intent = intent
        self.state = state
        self.language = language
        self.template = template

    def render(self, **kwargs: object) -> str:
        """Render the template with variable substitution using str.format_map."""
        try:
            return self.template.format_map(kwargs)
        except KeyError as e:
            logger.warning("Missing template variable", template_id=self.id, missing_key=str(e))
            # Return template as-is with unfilled variables
            return self.template


# In-memory cache
_templates: list[Template] = []


def load_templates() -> list[Template]:
    """
    Load all template YAML files from the configured directory.

    Each YAML file contains a list of template objects with fields:
    id, intent, state, language, template.

    Returns:
        List of Template objects
    """
    global _templates
    _templates.clear()

    templates_dir = Path(settings.templates_dir)
    if not templates_dir.exists():
        logger.warning("Templates directory not found", path=str(templates_dir))
        return _templates

    yaml_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
    logger.info("Loading templates", count=len(yaml_files), dir=str(templates_dir))

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, encoding="utf-8") as f:
                raw_list = yaml.safe_load(f)

            if not isinstance(raw_list, list):
                logger.warning("Template YAML is not a list, skipping", file=str(yaml_file))
                continue

            for entry in raw_list:
                tpl = Template(
                    id=entry["id"],
                    intent=entry.get("intent", ""),
                    state=entry.get("state", ""),
                    language=entry.get("language", "tr"),
                    template=entry["template"],
                )
                _templates.append(tpl)

            logger.info("Templates loaded from file", file=yaml_file.name, count=len(raw_list))
        except Exception:
            logger.exception("Failed to load template file", file=str(yaml_file))

    return _templates


def find_template(
    intent: str,
    state: str,
    language: str = "tr",
) -> Template | None:
    """
    Find the best matching template for the given intent, state, and language.

    Matching priority:
    1. Exact match on intent + state + language
    2. Match on intent + language (any state)
    3. Match on intent + state (fallback to 'en')
    4. None if no match
    """
    # Exact match
    for tpl in _templates:
        if tpl.intent == intent and tpl.state == state and tpl.language == language:
            return tpl

    # Intent + language (any state)
    for tpl in _templates:
        if tpl.intent == intent and tpl.language == language:
            return tpl

    # Intent + state, fallback language to 'en'
    if language != "en":
        for tpl in _templates:
            if tpl.intent == intent and tpl.state == state and tpl.language == "en":
                return tpl

    return None


def render_template(
    intent: str,
    state: str,
    language: str = "tr",
    **variables: object,
) -> str | None:
    """
    Find and render a template. Returns the rendered string or None if no template found.
    """
    tpl = find_template(intent, state, language)
    if tpl is None:
        return None
    return tpl.render(**variables)


def get_all_templates() -> list[Template]:
    """Get all cached templates."""
    return _templates.copy()


def reload_templates() -> list[Template]:
    """Reload all templates from disk."""
    logger.info("Reloading templates")
    return load_templates()
```

**Files to create**:
- `src/velox/core/template_engine.py`
- `data/templates/greeting.yaml`
- `data/templates/booking.yaml`

---

## Step 5: Wire Up Config Loading in main.py

Modify `src/velox/main.py` to load all configs during startup:

```python
from velox.core.hotel_profile_loader import load_all_profiles
from velox.escalation.matrix import load_escalation_matrix
from velox.core.template_engine import load_templates

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    setup_logging()
    await init_db_pool()
    # TODO: Initialize Redis connection

    # Load configuration
    profiles = load_all_profiles()
    logger.info("Hotel profiles loaded", count=len(profiles))

    matrix = load_escalation_matrix()
    logger.info("Escalation matrix loaded", count=len(matrix))

    templates = load_templates()
    logger.info("Templates loaded", count=len(templates))

    yield

    # Shutdown
    await close_db_pool()
    # TODO: Close Redis connection
```

Add a `logger` at module level:
```python
import structlog
logger = structlog.get_logger(__name__)
```

**File to modify**: `src/velox/main.py`

---

## Step 6: Add Admin Reload Endpoint

Create `src/velox/api/routes/admin.py` (or add to existing):

```python
"""Admin API routes for configuration management."""

from fastapi import APIRouter

from velox.core.hotel_profile_loader import reload_profiles
from velox.escalation.matrix import reload_matrix
from velox.core.template_engine import reload_templates

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reload-config")
async def reload_config() -> dict[str, object]:
    """Reload all configuration from disk (hotel profiles, escalation matrix, templates)."""
    profiles = reload_profiles()
    matrix = reload_matrix()
    templates = reload_templates()

    return {
        "reloaded": True,
        "profiles_count": len(profiles),
        "matrix_entries_count": len(matrix),
        "templates_count": len(templates),
    }
```

Register in `main.py`:
```python
from velox.api.routes import admin
app.include_router(admin.router, prefix="/api/v1")
```

**Files to create**:
- `src/velox/api/routes/admin.py`

**Files to modify**:
- `src/velox/main.py` — add admin router

---

## Step 7: Sync Hotel Profile to Database

After loading profiles, sync them to the `hotels` table so that foreign key references work.

Add to the lifespan function in `src/velox/main.py`, after `load_all_profiles()`:

```python
from velox.db.repositories.hotel import HotelRepository

hotel_repo = HotelRepository()
for hotel_id, profile in profiles.items():
    await hotel_repo.upsert(
        hotel_id=profile.hotel_id,
        name_tr=profile.hotel_name.tr,
        name_en=profile.hotel_name.en,
        profile_json=profile.model_dump(),
        hotel_type=profile.hotel_type,
        timezone=profile.timezone,
        currency_base=profile.currency_base,
        pms=profile.pms,
        whatsapp_number=profile.whatsapp_number,
        season_open=profile.season.get("open"),
        season_close=profile.season.get("close"),
    )
    logger.info("Hotel synced to DB", hotel_id=hotel_id)
```

**File to modify**: `src/velox/main.py`

---

## Verification Checklist

- [ ] `src/velox/core/hotel_profile_loader.py` exists and `load_all_profiles()` returns a dict with hotel_id 21966
- [ ] `get_profile(21966)` returns a `HotelProfile` with `hotel_name.en == "Kassandra Oludeniz"`
- [ ] `get_profile(21966).room_types` has 7 room types
- [ ] `get_profile(21966).transfer_routes` has 4 routes
- [ ] `get_profile(21966).restaurant` is not None and has `name == "Kassandra Restoran"`
- [ ] `get_profile(21966).faq_data` has 14 FAQ entries
- [ ] `src/velox/escalation/matrix.py` exists and `load_escalation_matrix()` returns 25 entries
- [ ] `get_entry_by_flag("LEGAL_REQUEST")` returns an entry with `level == "L3"` and `route_to_role == "ADMIN"`
- [ ] `get_highest_entry(["ALLERGY_ALERT", "LEGAL_REQUEST"])` returns the L3 entry (LEGAL_REQUEST)
- [ ] `src/velox/core/template_engine.py` exists and `load_templates()` loads templates from `data/templates/`
- [ ] `find_template("greeting", "GREETING", "tr")` returns a template
- [ ] `render_template("greeting", "GREETING", "tr", hotel_name="Kassandra Oludeniz")` returns a string containing "Kassandra Oludeniz"
- [ ] `POST /api/v1/admin/reload-config` reloads all configs and returns counts
- [ ] Hotel profile is synced to the `hotels` table in PostgreSQL on startup
- [ ] App startup logs show all config loading counts

---

## Files Created in This Task
| File | Purpose |
|------|---------|
| `src/velox/core/hotel_profile_loader.py` | YAML hotel profile loader with caching |
| `src/velox/escalation/matrix.py` | Escalation matrix YAML loader with lookup |
| `src/velox/core/template_engine.py` | Template engine with variable substitution |
| `src/velox/api/routes/admin.py` | Admin API for config reload |
| `data/templates/greeting.yaml` | Greeting message templates |
| `data/templates/booking.yaml` | Booking message templates |

## Files Modified in This Task
| File | Change |
|------|--------|
| `src/velox/main.py` | Load profiles, matrix, templates on startup; sync hotel to DB; register admin router |
