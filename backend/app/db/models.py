import uuid
from datetime import datetime, timedelta

from sqlmodel import SQLModel, Field


def new_token() -> str:
    return uuid.uuid4().hex


class VerificationState(SQLModel, table=True):
    token: str = Field(default_factory=new_token, primary_key=True)
    discord_id: str
    guild_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=10)
    )
    consumed: bool = False

    def is_valid(self) -> bool:
        return not self.consumed and datetime.utcnow() < self.expires_at


class TeamRole(SQLModel, table=True):
    """구단명 <-> 디스코드 역할ID 매핑. /구단역할설정 봇 명령어로 관리한다."""

    guild_id: str = Field(primary_key=True)
    team_name: str = Field(primary_key=True)
    role_id: str


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
