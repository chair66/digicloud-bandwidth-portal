from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "NTInet LNP Portal"
    app_env: str = "development"
    app_secret_key: str = "change-me"
    bandwidth_account_id: str
    bandwidth_client_id: str
    bandwidth_client_secret: str
    bandwidth_token_url: str = "https://api.bandwidth.com/api/v1/oauth2/token"
    bandwidth_api_base: str = "https://api.bandwidth.com/api/v2"
    request_timeout_seconds: int = 30
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()
