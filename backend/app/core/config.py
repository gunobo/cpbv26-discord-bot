from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    discord_token: str = ""
    discord_guild_id: str = ""
    verified_role_id: str = ""

    web_base_url: str = "http://localhost:8000"
    port: int = 8000
    cookie_secret: str = "dev-secret"

    internal_api_key: str = "dev-internal-key"

    hive_mock_mode: bool = True
    hive_env: str = "sandbox"
    hive_appid: str = ""
    hive_gindex: str = ""
    hive_certification_key: str = ""
    hive_redirect_url: str = "http://localhost:8000/verify/callback"

    database_url: str = "sqlite:///./app.db"


settings = Settings()
