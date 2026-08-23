from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.config import settings
from app.db.models import User, VerificationState
from app.db.session import engine

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[])


def require_internal_key(x_internal_key: str = Header(default="")) -> None:
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="invalid internal key")


class CreateVerifyRequestBody(BaseModel):
    discord_id: str
    guild_id: str


class VerifyRequestResponse(BaseModel):
    token: str
    verify_url: str


@router.post(
    "/verify-requests",
    response_model=VerifyRequestResponse,
    dependencies=[Depends(require_internal_key)],
)
def create_verify_request(body: CreateVerifyRequestBody):
    with Session(engine) as session:
        state = VerificationState(discord_id=body.discord_id, guild_id=body.guild_id)
        session.add(state)
        session.commit()
        session.refresh(state)
        token = state.token

    return VerifyRequestResponse(
        token=token,
        verify_url=f"{settings.web_base_url}/verify/start?token={token}",
    )


class LeaderboardEntry(BaseModel):
    discord_id: str
    team_name: str | None
    overall: int | None


@router.get(
    "/leaderboard",
    response_model=list[LeaderboardEntry],
    dependencies=[Depends(require_internal_key)],
)
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


class UpdateUserStatsBody(BaseModel):
    team_name: str
    overall: int


@router.patch("/users/{discord_id}", dependencies=[Depends(require_internal_key)])
def update_user_stats(discord_id: str, body: UpdateUserStatsBody):
    with Session(engine) as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="아직 인증하지 않은 사용자입니다")
        user.team_name = body.team_name
        user.overall = body.overall
        session.add(user)
        session.commit()
    return {"ok": True}
