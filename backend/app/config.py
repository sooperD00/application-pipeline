"""
Config via pydantic-settings. Railway injects DATABASE_PUBLIC_URL and ANTHROPIC_API_KEY
automatically once you link the Postgres plugin and add the secret.
Pydantic-settings maps field names → env var names (case-insensitive), so they must match.

note: DATABASE_PUBLIC_URL/database_public_url = Railway external URL (use this locally and in prod)
      DATABASE_URL/database_url = Railway internal URL (service-to-service only, never in .env)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Required (Railway provides these) ───────────────────────────────────
    database_public_url: str       # see database.py — asyncpg rewrite happens there
    anthropic_api_key: str

    # ── Defaults ─────────────────────────────────────────────────────────────
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    default_model: str = "claude-opus-4-6"          # ADR-003, no redeploy to change
    tailoring_parallelism: int = 4                  # ADR-008; paid tier → 8

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()