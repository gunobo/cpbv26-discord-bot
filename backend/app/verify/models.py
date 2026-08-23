import uuid
from datetime import datetime, timedelta

from sqlmodel import Field, SQLModel


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
