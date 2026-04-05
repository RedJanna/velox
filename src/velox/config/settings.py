"""Application settings loaded from environment variables."""

# ruff: noqa: S104, S105

from ipaddress import IPv4Network, IPv6Network, ip_network
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"
    app_debug: bool = False
    app_port: int = 8001
    app_host: str = "0.0.0.0"
    app_log_level: str = "INFO"
    app_secret_key: str = "change-me-in-production"
    app_trusted_hosts: str = "127.0.0.1,localhost,nexlumeai.com,www.nexlumeai.com,velox.nexlumeai.com"
    public_base_url: str = "https://nexlumeai.com"
    admin_panel_path: str = "/admin"
    phone_hash_salt: str = ""

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "velox"
    db_user: str = "velox"
    db_password: str = "change-me"
    db_pool_min: int = 5
    db_pool_max: int = 20

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def trusted_hosts(self) -> list[str]:
        return [item.strip() for item in self.app_trusted_hosts.split(",") if item.strip()]

    @property
    def admin_panel_url(self) -> str:
        base = self.public_base_url.rstrip("/")
        path = self.admin_panel_path if self.admin_panel_path.startswith("/") else f"/{self.admin_panel_path}"
        return f"{base}{path}"

    @property
    def public_host(self) -> str:
        parsed = urlsplit(self.public_base_url)
        return parsed.netloc or self.public_base_url

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl_seconds: int = 1800
    redis_rate_limit_ttl_seconds: int = 60
    metrics_allow_public: bool = False
    metrics_allowed_cidrs: str = "127.0.0.1/32,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_fallback_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 2048
    openai_temperature: float = 0.3

    # Operation Mode — controls outbound WhatsApp messaging behaviour.
    # "test":     system receives messages and generates replies but NEVER sends
    #             anything to WhatsApp; all outbound calls are blocked and logged.
    # "ai":       system sends messages automatically with human-handoff rules.
    # "approval": system generates replies and queues them; admin must approve
    #             each message before it is sent via WhatsApp.
    # "off":      system records data only; no reply generation, no sending.
    operation_mode: str = "test"

    # WhatsApp
    whatsapp_api_version: str = "v21.0"
    whatsapp_api_base_url: str = "https://graph.facebook.com"
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""

    # Elektraweb
    elektra_api_base_url: str = ""
    elektra_api_key: str = ""
    elektra_hotel_id: int = 21966

    # Admin
    admin_jwt_secret: str = "change-me-in-production"
    admin_jwt_algorithm: str = "HS256"
    admin_jwt_expire_minutes: int = 60
    admin_webhook_secret: str = ""
    admin_bootstrap_token: str = ""
    admin_totp_issuer: str = "NexlumeAI"

    # Rate Limiting
    rate_limit_per_phone_per_minute: int = 30
    rate_limit_per_phone_per_hour: int = 200
    rate_limit_webhook_per_minute: int = 100

    # Burst Buffer — aggregates rapid successive messages before LLM processing
    burst_debounce_seconds: float = 2.5
    burst_max_messages: int = 5
    burst_max_wait_seconds: float = 10.0
    burst_lock_ttl_seconds: int = 60

    # Media Analysis
    media_analysis_enabled: bool = True
    media_max_bytes: int = 8 * 1024 * 1024
    media_max_image_dimension: int = 2048
    media_retention_hours: int = 24
    media_supported_mime_types: str = (
        "image/jpeg,image/jpg,image/png,image/webp,image/tiff,image/heic,image/heif"
    )
    audio_transcription_enabled: bool = True
    audio_max_bytes: int = 16 * 1024 * 1024
    audio_supported_mime_types: str = (
        "audio/ogg,audio/oga,audio/mpeg,audio/mp3,audio/mp4,audio/aac,audio/amr,audio/wav,audio/x-wav,audio/webm"
    )
    audio_transcription_min_confidence: float = 0.55
    audio_transcription_fallback_language: str = "en"

    @property
    def audio_supported_mime_type_list(self) -> list[str]:
        """Normalized list of supported audio mime types."""
        return [
            item.strip().lower()
            for item in self.audio_supported_mime_types.split(",")
            if item.strip()
        ]

    @property
    def media_supported_mime_type_list(self) -> list[str]:
        """Normalized list of supported media mime types."""
        return [
            item.strip().lower()
            for item in self.media_supported_mime_types.split(",")
            if item.strip()
        ]

    @property
    def metrics_allowed_networks(self) -> tuple[IPv4Network | IPv6Network, ...]:
        """Normalized private/public CIDR allowlist for the metrics endpoint."""
        return tuple(
            ip_network(item.strip(), strict=False)
            for item in self.metrics_allowed_cidrs.split(",")
            if item.strip()
        )

    # Paths
    hotel_profiles_dir: str = "data/hotel_profiles"
    escalation_matrix_path: str = "data/escalation_matrix.yaml"
    templates_dir: str = "data/templates"
    scenarios_dir: str = "data/scenarios"
    chat_lab_feedback_dir: str = "data/chat_lab_feedback"
    chat_lab_imports_dir: str = "data/chat_lab_imports"


settings = Settings()
