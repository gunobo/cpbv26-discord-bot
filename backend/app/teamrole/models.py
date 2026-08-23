from sqlmodel import Field, SQLModel


class TeamRole(SQLModel, table=True):
    """구단명 <-> 디스코드 역할ID 매핑. /구단역할설정 봇 명령어로 관리한다."""

    guild_id: str = Field(primary_key=True)
    team_name: str = Field(primary_key=True)
    role_id: str
