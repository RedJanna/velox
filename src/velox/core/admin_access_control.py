"""Admin access-control catalog and permission helpers."""

from __future__ import annotations

from dataclasses import dataclass

from velox.config.constants import DepartmentCode, Role


@dataclass(frozen=True, slots=True)
class DepartmentDefinition:
    """Hotel department metadata used by the admin panel."""

    code: str
    label: str
    description: str


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """Granular permission metadata exposed to the admin panel."""

    key: str
    group: str
    label: str
    description: str
    is_sensitive: bool = False


@dataclass(frozen=True, slots=True)
class RoleDefinition:
    """Role template metadata for hotel admin users."""

    role: Role
    label: str
    description: str
    default_department_code: str


DEPARTMENT_CATALOG: dict[str, DepartmentDefinition] = {
    DepartmentCode.MANAGEMENT.value: DepartmentDefinition(
        code=DepartmentCode.MANAGEMENT.value,
        label="Yönetim",
        description="Genel müdürlük, yönetici ofisi ve otel liderliği.",
    ),
    DepartmentCode.FRONT_OFFICE.value: DepartmentDefinition(
        code=DepartmentCode.FRONT_OFFICE.value,
        label="Ön Büro / Resepsiyon",
        description="Resepsiyon, giriş-çıkış işlemleri ve günlük misafir operasyonları.",
    ),
    DepartmentCode.RESERVATION_SALES.value: DepartmentDefinition(
        code=DepartmentCode.RESERVATION_SALES.value,
        label="Rezervasyon ve Satış",
        description="Rezervasyon kabulü, fiyat takibi ve satış koordinasyonu.",
    ),
    DepartmentCode.GUEST_RELATIONS.value: DepartmentDefinition(
        code=DepartmentCode.GUEST_RELATIONS.value,
        label="Misafir İlişkileri / Konsiyerj",
        description="Misafir iletişimi, konsiyerj talepleri ve memnuniyet takibi.",
    ),
    DepartmentCode.FOOD_BEVERAGE.value: DepartmentDefinition(
        code=DepartmentCode.FOOD_BEVERAGE.value,
        label="Yiyecek ve İçecek",
        description="Restoran, mutfak ve masa operasyonu iş akışları.",
    ),
    DepartmentCode.HOUSEKEEPING.value: DepartmentDefinition(
        code=DepartmentCode.HOUSEKEEPING.value,
        label="Kat Hizmetleri",
        description="Oda hazırlığı, temizlik ve kat operasyonları.",
    ),
    DepartmentCode.MAINTENANCE.value: DepartmentDefinition(
        code=DepartmentCode.MAINTENANCE.value,
        label="Bakım / Teknik Servis",
        description="Tesis bakımı, onarım ve teknik müdahale süreçleri.",
    ),
    DepartmentCode.FINANCE.value: DepartmentDefinition(
        code=DepartmentCode.FINANCE.value,
        label="Finans / Muhasebe",
        description="Faturalama, mutabakat ve iç finans kontrolleri.",
    ),
    DepartmentCode.SECURITY.value: DepartmentDefinition(
        code=DepartmentCode.SECURITY.value,
        label="Güvenlik",
        description="Güvenlik operasyonları, olay yönetimi ve erişim takibi.",
    ),
    DepartmentCode.OTHER.value: DepartmentDefinition(
        code=DepartmentCode.OTHER.value,
        label="Diğer",
        description="Standart otel departmanları dışındaki geçici veya çapraz görevler.",
    ),
}


ROLE_CATALOG: dict[Role, RoleDefinition] = {
    Role.ADMIN: RoleDefinition(
        role=Role.ADMIN,
        label="Otel Yöneticisi",
        description="Kullanıcı, rol ve izin yönetimi dahil otel düzeyinde tam erişim.",
        default_department_code=DepartmentCode.MANAGEMENT.value,
    ),
    Role.SALES: RoleDefinition(
        role=Role.SALES,
        label="Rezervasyon ve Satış",
        description="Rezervasyon süreci, misafir iletişimi ve ticari takip izinleri.",
        default_department_code=DepartmentCode.RESERVATION_SALES.value,
    ),
    Role.OPS: RoleDefinition(
        role=Role.OPS,
        label="Ön Büro ve Operasyon",
        description="Otel, konaklama ve transfer iş akışları için operasyon kuyruğu yönetimi.",
        default_department_code=DepartmentCode.FRONT_OFFICE.value,
    ),
    Role.CHEF: RoleDefinition(
        role=Role.CHEF,
        label="Yiyecek ve İçecek Onay Yetkilisi",
        description="Restoran ve mutfak onay süreçleri için sınırlı operasyon görünürlüğü.",
        default_department_code=DepartmentCode.FOOD_BEVERAGE.value,
    ),
}


PERMISSION_GROUP_LABELS: dict[str, str] = {
    "overview": "Genel Bakış",
    "access_control": "Erişim Yönetimi",
    "hotel": "Otel Yapılandırması",
    "conversation": "Konuşmalar",
    "hold": "Rezervasyon ve Onay Akışları",
    "ticket": "Destek Talepleri",
    "notification": "Bildirim Numaraları",
}


PERMISSION_CATALOG: dict[str, PermissionDefinition] = {
    "dashboard:read": PermissionDefinition(
        key="dashboard:read",
        group="overview",
        label="Genel bakışı görüntüleme",
        description="Özet kartlara, operasyon kartlarına ve genel bakış kuyruklarına erişim sağlar.",
    ),
    "access_control:read": PermissionDefinition(
        key="access_control:read",
        group="access_control",
        label="Kullanıcıları ve rolleri görüntüleme",
        description="Yönetici kullanıcılarını, kullanılabilir rolleri, departmanları ve izin şablonlarını gösterir.",
        is_sensitive=True,
    ),
    "access_control:write": PermissionDefinition(
        key="access_control:write",
        group="access_control",
        label="Kullanıcıları ve rolleri yönetme",
        description="Kullanıcı oluşturma, rol değiştirme, TOTP kurulumunu yenileme ve izin atamalarını düzenleme yetkisi verir.",
        is_sensitive=True,
    ),
    "hotels:read": PermissionDefinition(
        key="hotels:read",
        group="hotel",
        label="Otel yapılandırmasını görüntüleme",
        description="Otel profilini, bilgi kayıtlarını ve operasyonel yapılandırma değerlerini görüntüler.",
    ),
    "hotels:write": PermissionDefinition(
        key="hotels:write",
        group="hotel",
        label="Otel yapılandırmasını düzenleme",
        description="Otel profilini, bilgi kayıtlarını ve operasyonel yapılandırma değerlerini değiştirir.",
        is_sensitive=True,
    ),
    "conversations:read": PermissionDefinition(
        key="conversations:read",
        group="conversation",
        label="Konuşmaları görüntüleme",
        description="Misafir konuşma geçmişini, durumunu ve insan devri bilgisini inceler.",
    ),
    "holds:read": PermissionDefinition(
        key="holds:read",
        group="hold",
        label="Onay kayıtlarını görüntüleme",
        description="Konaklama, restoran ve transfer onay kuyruklarını görüntüler.",
    ),
    "holds:approve": PermissionDefinition(
        key="holds:approve",
        group="hold",
        label="Onay kayıtlarını onaylama",
        description="Operasyonel onay kayıtlarını ve rezervasyon iş akışlarını onaylama, oluşturma veya güncelleme yetkisi verir.",
        is_sensitive=True,
    ),
    "holds:reject": PermissionDefinition(
        key="holds:reject",
        group="hold",
        label="Onay kayıtlarını reddetme",
        description="Onay akışlarını ve rezervasyon taleplerini reddetme veya arşivleme yetkisi verir.",
        is_sensitive=True,
    ),
    "tickets:read": PermissionDefinition(
        key="tickets:read",
        group="ticket",
        label="Destek taleplerini görüntüleme",
        description="Destek talebi kuyruklarını ve servis devri geçmişini inceler.",
    ),
    "tickets:write": PermissionDefinition(
        key="tickets:write",
        group="ticket",
        label="Destek taleplerini güncelleme",
        description="Operasyonel destek taleplerini yeniden atama, çözme veya kapatma yetkisi verir.",
        is_sensitive=True,
    ),
    "notification_phones:read": PermissionDefinition(
        key="notification_phones:read",
        group="notification",
        label="Bildirim numaralarını görüntüleme",
        description="Otel için WhatsApp bildirim numarası eşleşmelerini görüntüler.",
    ),
    "notification_phones:write": PermissionDefinition(
        key="notification_phones:write",
        group="notification",
        label="Bildirim numaralarını yönetme",
        description="Eskalasyonlarda kullanılan bildirim numarası eşleşmelerini ekleme veya kaldırma yetkisi verir.",
        is_sensitive=True,
    ),
}


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "dashboard:read",
        "access_control:read",
        "access_control:write",
        "hotels:read",
        "hotels:write",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "tickets:write",
        "notification_phones:read",
        "notification_phones:write",
    },
    Role.SALES: {
        "dashboard:read",
        "hotels:read",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "notification_phones:read",
    },
    Role.OPS: {
        "dashboard:read",
        "hotels:read",
        "conversations:read",
        "holds:read",
        "holds:approve",
        "holds:reject",
        "tickets:read",
        "tickets:write",
        "notification_phones:read",
        "notification_phones:write",
    },
    Role.CHEF: {
        "dashboard:read",
        "holds:read",
        "holds:approve",
    },
    Role.NONE: set(),
}


SUPER_ADMIN_USERNAMES: frozenset[str] = frozenset({"H893453klkads"})


def normalize_admin_username(username: str | None) -> str:
    """Normalize admin usernames for stable access-control comparisons."""
    return (username or "").strip()


def is_super_admin_username(username: str | None) -> bool:
    """Return whether one username is a protected owner-level super admin."""
    return normalize_admin_username(username) in SUPER_ADMIN_USERNAMES


def build_super_admin_permissions() -> set[str]:
    """Return every known granular permission for protected super admins."""
    return set(PERMISSION_CATALOG)


def get_role_label(role: Role) -> str:
    """Return the human-readable label for a role."""
    definition = ROLE_CATALOG.get(role)
    return definition.label if definition is not None else role.value.title()


def get_department_label(department_code: str | None) -> str | None:
    """Return the human-readable label for one department code."""
    if not department_code:
        return None
    definition = DEPARTMENT_CATALOG.get(department_code)
    return definition.label if definition is not None else department_code


def default_department_for_role(role: Role) -> str:
    """Return the default department assignment for one role template."""
    definition = ROLE_CATALOG.get(role)
    if definition is None:
        return DepartmentCode.OTHER.value
    return definition.default_department_code


def normalize_department_code(value: str | None, *, role: Role | None = None) -> str:
    """Normalize one department code and fill sane defaults for empty values."""
    normalized = (value or "").strip().upper()
    if not normalized:
        return default_department_for_role(role or Role.NONE)
    if normalized not in DEPARTMENT_CATALOG:
        raise ValueError(f"Desteklenmeyen departman kodu: {normalized}")
    return normalized


def validate_permission_keys(permission_keys: set[str] | list[str]) -> set[str]:
    """Reject unknown permission keys and return a normalized set."""
    normalized = {item.strip() for item in permission_keys if item and item.strip()}
    invalid = sorted(normalized - set(PERMISSION_CATALOG))
    if invalid:
        raise ValueError(f"Desteklenmeyen izin anahtarları: {', '.join(invalid)}")
    return normalized


def build_effective_permissions(role: Role, overrides: dict[str, bool] | None = None) -> set[str]:
    """Build the effective permission set from one role plus explicit overrides."""
    permissions = set(ROLE_PERMISSIONS.get(role, set()))
    for permission_key, is_allowed in (overrides or {}).items():
        if permission_key not in PERMISSION_CATALOG:
            continue
        if is_allowed:
            permissions.add(permission_key)
        else:
            permissions.discard(permission_key)
    return permissions


def build_admin_effective_permissions(
    *,
    username: str | None,
    role: Role,
    overrides: dict[str, bool] | None = None,
) -> set[str]:
    """Build effective admin permissions, forcing protected super admins to full access."""
    if is_super_admin_username(username):
        return build_super_admin_permissions()
    return build_effective_permissions(role, overrides)


def get_role_catalog() -> list[dict[str, object]]:
    """Return the stable role template catalog for API responses."""
    items: list[dict[str, object]] = []
    for role in (Role.ADMIN, Role.SALES, Role.OPS, Role.CHEF):
        definition = ROLE_CATALOG[role]
        items.append(
            {
                "code": role.value,
                "label": definition.label,
                "description": definition.description,
                "default_department_code": definition.default_department_code,
                "default_permissions": sorted(ROLE_PERMISSIONS.get(role, set())),
            }
        )
    return items


def get_department_catalog() -> list[dict[str, str]]:
    """Return the stable hotel department catalog for API responses."""
    ordered_codes = [
        DepartmentCode.MANAGEMENT.value,
        DepartmentCode.FRONT_OFFICE.value,
        DepartmentCode.RESERVATION_SALES.value,
        DepartmentCode.GUEST_RELATIONS.value,
        DepartmentCode.FOOD_BEVERAGE.value,
        DepartmentCode.HOUSEKEEPING.value,
        DepartmentCode.MAINTENANCE.value,
        DepartmentCode.FINANCE.value,
        DepartmentCode.SECURITY.value,
        DepartmentCode.OTHER.value,
    ]
    return [
        {
            "code": DEPARTMENT_CATALOG[code].code,
            "label": DEPARTMENT_CATALOG[code].label,
            "description": DEPARTMENT_CATALOG[code].description,
        }
        for code in ordered_codes
    ]


def get_permission_catalog() -> list[dict[str, object]]:
    """Return grouped permission metadata for the admin panel."""
    grouped_items: list[dict[str, object]] = []
    for group_key, group_label in PERMISSION_GROUP_LABELS.items():
        items = [
            {
                "key": definition.key,
                "label": definition.label,
                "description": definition.description,
                "is_sensitive": definition.is_sensitive,
            }
            for definition in PERMISSION_CATALOG.values()
            if definition.group == group_key
        ]
        if not items:
            continue
        items.sort(key=lambda item: str(item["label"]))
        grouped_items.append(
            {
                "group": group_key,
                "group_label": group_label,
                "items": items,
            }
        )
    return grouped_items
