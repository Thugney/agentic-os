from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTIC_OS_", env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "Agentic OS"
    app_host: str = "0.0.0.0"
    app_port: int = 3737
    public_url: str = "http://0.0.0.0:3737"
    environment: str = "production"
    data_dir: Path = Path("/data")
    config_dir: Path = Path("config")
    sqlite_path: Path | None = None
    admin_token: str | None = None
    openwebui_url: str = "http://127.0.0.1:18790"
    hermes_url: str = "http://127.0.0.1:9119"

    @property
    def db_path(self) -> Path:
        return self.sqlite_path or self.data_dir / "agentic-os.db"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.data_dir.mkdir(parents=True, exist_ok=True)
    s.logs_dir.mkdir(parents=True, exist_ok=True)
    return s
