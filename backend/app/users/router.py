from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.core.internal_auth import require_internal_key
from app.db.session import engine
from app.discord_rest import revoke_role, sync_team_role
from app.teamrole.service import get_team_role_ids
from app.users.models import User

router = APIRouter(prefix="/internal", tags=["users"], dependencies=[Depends(require_internal_key)])


class UserInfoResponse(BaseModel):
    discord_id: str
    verification_method: str
    player_id: str | None
    team_name: str | None
    overall: int | None
    verified_at: str


@router.get("/users/{discord_id}", response_model=UserInfoResponse)
def get_user_info(discord_id: str):
    with Session(engine) as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="아직 인증하지 않은 사용자입니다")
        return UserInfoResponse(
            discord_id=user.discord_id,
            verification_method=user.verification_method,
            player_id=user.player_id,
            team_name=user.team_name,
            overall=user.overall,
            verified_at=user.verified_at.isoformat(),
        )


@router.delete("/users/{discord_id}")
async def delete_user(discord_id: str):
    with Session(engine) as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="인증 기록이 없는 사용자입니다")
        guild_id = user.guild_id
        team_role_ids = get_team_role_ids(session, guild_id)
        session.delete(user)
        session.commit()

    await revoke_role(guild_id, discord_id, settings.verified_role_id)
    await sync_team_role(guild_id, discord_id, None, team_role_ids)
    return {"ok": True}


class UpdateUserStatsBody(BaseModel):
    team_name: str
    overall: int


@router.patch("/users/{discord_id}")
async def update_user_stats(discord_id: str, body: UpdateUserStatsBody):
    with Session(engine) as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="아직 인증하지 않은 사용자입니다")
        user.team_name = body.team_name
        user.overall = body.overall
        session.add(user)
        session.commit()
        guild_id, team_role_ids = user.guild_id, get_team_role_ids(session, user.guild_id)

    role_synced = True
    try:
        await sync_team_role(guild_id, discord_id, body.team_name, team_role_ids)
    except RuntimeError:
        role_synced = False

    return {"ok": True, "role_synced": role_synced}
