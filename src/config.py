"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class APIConfig:
    """Ducks Unlimited ArcGIS API settings."""

    base_url: str = (
        "https://services2.arcgis.com/5I7u4SJE1vUr79JC/arcgis/rest/services"
        "/UniversityChapters_Public/FeatureServer/0/query"
    )
    state_filter: str = "CA"
    out_fields: str = "ChapterID,University_Chapter,City,State"
    spatial_ref: int = 4326
    timeout_seconds: int = 30


@dataclass(frozen=True)
class DBConfig:
    """Postgres connection settings."""

    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def connection_string(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


def load_db_config() -> DBConfig:
    """Build DBConfig from environment variables."""
    return DBConfig(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        name=os.environ.get("DB_NAME", "du_chapters"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
    )


def load_api_config() -> APIConfig:
    """Build APIConfig, allowing env-var overrides for state filter."""
    return APIConfig(
        state_filter=os.environ.get("STATE_FILTER", "CA"),
    )
