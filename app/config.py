from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    api_keys: str = "dev-key-change-me"
    database_path: str = "data/developers.duckdb"
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
