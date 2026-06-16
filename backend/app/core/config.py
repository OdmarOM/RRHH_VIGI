from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sistema RRHH y Vigilancia"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{Path(__file__).parent.parent.parent / 'rrhh_dev.db'}"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    # Host y puerto de producción (sin chocar con 8000-8003)
    host: str = "0.0.0.0"
    port: int = 8090
    # En producción el frontend se sirve en el mismo origen, por lo que
    # CORS no es estrictamente necesario; se mantienen los orígenes de
    # desarrollo y se puede ampliar vía variable de entorno.
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
