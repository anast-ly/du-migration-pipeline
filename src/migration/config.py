"""Centralised configuration, loaded from environment variables / .env.

All runtime configuration lives here so the rest of the code never reads
os.environ directly. This keeps config separate from logic and makes the pipeline trivially testable.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- API source ---
    du_api_url: str = (
        "https://services2.arcgis.com/5I7u4SJE1vUr79JC/arcgis/rest/services/"
        "UniversityChapters_Public/FeatureServer/0/query"
    )
    du_api_page_size: int = 1000

    # --- Target backend: "bigquery" | "postgres" ---
    target_backend: str = "bigquery"

    # --- BigQuery ---
    gcp_project_id: str = "assessment-500800"
    bq_dataset: str = "du_migration"
    bq_table: str = "university_chapters"
    bq_location: str = "europe-west2"

    # --- Postgres ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "du_migration"
    postgres_user: str = "migration"
    postgres_password: str = "changeme"

    # --- Run config ---
    log_level: str = "INFO"
    dry_run: bool = False

    # Comma-separated US state codes to migrate (case-insensitive).
    target_states: str = "CA,OR,WA"

settings = Settings()
