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

    stats_refresh_interval_seconds: int = 300
    coupon_refresh_interval_seconds: int = 600

    @property
    def hive_connected(self) -> bool:
        """실제 Hive 연동이 가능한 상태인지. 모킹 모드거나 콘솔 키가 하나라도
        비어있으면 False — 이땐 /인증이 규칙 체크만으로 완료되는 방식으로 대체된다."""
        return (
            not self.hive_mock_mode
            and bool(self.hive_appid)
            and bool(self.hive_gindex)
            and bool(self.hive_certification_key)
        )


settings = Settings()
