from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.internal_auth import require_internal_key
from app.db.session import engine
from app.users.models import User

router = APIRouter(prefix="/internal", tags=["leaderboard"], dependencies=[Depends(require_internal_key)])


class LeaderboardEntry(BaseModel):
    discord_id: str
    team_name: str | None
    overall: int | None


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def get_leaderboard(guild_id: str):
    with Session(engine) as session:
        users = session.exec(
            select(User)
            .where(User.guild_id == guild_id)
            .order_by(User.overall.desc().nulls_last())
        ).all()
    return [
        LeaderboardEntry(discord_id=u.discord_id, team_name=u.team_name, overall=u.overall)
        for u in users
    ]
