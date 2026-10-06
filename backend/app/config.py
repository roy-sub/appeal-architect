"""Settings, read from the environment once.

Nothing here has a secret default. Where a service is unconfigured the app still
starts and says so -- ``/healthz`` reports which halves are wired -- because a
developer who has cloned the repo and not yet made a Supabase project should get
a running app and a clear message, not a stack trace.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["development", "production"] = "development"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Anthropic -- phase 4. Only app/services/llm.py may read these.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    llm_monthly_call_cap: int = 200

    # Email -- phase 6
    resend_api_key: str = ""
    from_email: str = ""

    # Stripe -- phase 8
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Pinned engine versions. Recorded on every determination so a conclusion is
    # reproducible against the exact rules that produced it.
    rulebase_version: str = "1.0.0"
    schemes_version: str = "1.0.0"

    internal_job_secret: str = ""
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    # ---- configuration gates -------------------------------------------------
    # Each half of the app checks its own gate and degrades with a message rather
    # than failing at import time.

    @property
    def supabase_configured(self) -> bool:
        return bool(
            self.supabase_url and self.supabase_service_role_key and self.supabase_jwt_secret
        )

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def email_configured(self) -> bool:
        return bool(self.resend_api_key and self.from_email)

    @property
    def stripe_configured(self) -> bool:
        return bool(self.stripe_secret_key and self.stripe_webhook_secret)

    @property
    def reminders_configured(self) -> bool:
        return bool(self.internal_job_secret) and self.email_configured

    def service_status(self) -> dict[str, bool]:
        """What /healthz reports. No secret values, only whether each is present."""
        return {
            "supabase": self.supabase_configured,
            "anthropic": self.anthropic_configured,
            "email": self.email_configured,
            "stripe": self.stripe_configured,
            "reminders": self.reminders_configured,
        }

    def missing_for_production(self) -> list[str]:
        """Settings that must be present before this is deployed.

        Called at startup in production so a misconfigured deploy fails loudly
        instead of silently not sending deadline reminders.
        """
        missing: list[str] = []
        if not self.supabase_configured:
            missing.append("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY / SUPABASE_JWT_SECRET")
        if not self.anthropic_configured:
            missing.append("ANTHROPIC_API_KEY")
        if not self.email_configured:
            missing.append("RESEND_API_KEY / FROM_EMAIL")
        if not self.internal_job_secret:
            missing.append("INTERNAL_JOB_SECRET")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()
