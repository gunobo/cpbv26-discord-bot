from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    discord_id: str = Field(primary_key=True)
    guild_id: str
    # "hive": Hive 로그인으로 PlayerID까지 확인된 인증. "rules": Hive 연동 전, 규칙 체크만으로 인증.
    verification_method: str = "hive"
    player_id: str | None = None
    idp_user_id: str | None = None
    idp_index: int | None = None
    team_name: str | None = None
    overall: int | None = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    stats_updated_at: datetime | None = None
