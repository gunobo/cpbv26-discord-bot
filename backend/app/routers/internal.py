from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.community import CommunityFetchError, fetch_ongoing_events
from app.core.config import settings
from app.db.models import TeamRole, User, VerificationState
from app.db.session import engine
from app.discord_rest import grant_verified_role, revoke_role, sync_team_role

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[])


def _team_role_ids(session: Session, guild_id: str) -> dict[str, str]:
    rows = session.exec(select(TeamRole).where(TeamRole.guild_id == guild_id)).all()
    return {row.team_name: row.role_id for row in rows}


def require_internal_key(x_internal_key: str = Header(default="")) -> None:
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="invalid internal key")


class CreateVerifyRequestBody(BaseModel):
    discord_id: str
    guild_id: str


class VerifyRequestResponse(BaseModel):
    mode: str  # "hive" | "rules"
    verify_url: str | None = None
    role_granted: bool | None = None  # mode == "rules" 일 때만 의미 있음


@router.get("/status", dependencies=[Depends(require_internal_key)])
def get_status():
    return {"hive_connected": settings.hive_connected, "hive_mock_mode": settings.hive_mock_mode}


@router.post(
    "/verify-requests",
    response_model=VerifyRequestResponse,
    dependencies=[Depends(require_internal_key)],
)
async def create_verify_request(body: CreateVerifyRequestBody):
    if settings.hive_connected:
        with Session(engine) as session:
            state = VerificationState(discord_id=body.discord_id, guild_id=body.guild_id)
            session.add(state)
            session.commit()
            session.refresh(state)
            token = state.token

        return VerifyRequestResponse(
            mode="hive",
            verify_url=f"{settings.web_base_url}/verify/start?token={token}",
        )

    # Hive 연동 전: 규칙 체크(봇에서 이미 확인됨)만으로 즉시 인증 완료 처리
    with Session(engine) as session:
        user = session.get(User, body.discord_id)
        if user is None:
            user = User(
                discord_id=body.discord_id,
                guild_id=body.guild_id,
                verification_method="rules",
            )
        else:
            user.verification_method = "rules"
        session.add(user)
        session.commit()

    role_granted = True
    try:
        await grant_verified_role(body.guild_id, body.discord_id)
    except RuntimeError:
        role_granted = False

    return VerifyRequestResponse(mode="rules", role_granted=role_granted)


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


class UserInfoResponse(BaseModel):
    discord_id: str
    verification_method: str
    player_id: str | None
    team_name: str | None
    overall: int | None
    verified_at: str


@router.get(
    "/users/{discord_id}",
    response_model=UserInfoResponse,
    dependencies=[Depends(require_internal_key)],
)
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


@router.delete("/users/{discord_id}", dependencies=[Depends(require_internal_key)])
async def delete_user(discord_id: str):
    with Session(engine) as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="인증 기록이 없는 사용자입니다")
        guild_id = user.guild_id
        team_role_ids = _team_role_ids(session, guild_id)
        session.delete(user)
        session.commit()

    await revoke_role(guild_id, discord_id, settings.verified_role_id)
    await sync_team_role(guild_id, discord_id, None, team_role_ids)
    return {"ok": True}


class UpdateUserStatsBody(BaseModel):
    team_name: str
    overall: int


@router.patch("/users/{discord_id}", dependencies=[Depends(require_internal_key)])
async def update_user_stats(discord_id: str, body: UpdateUserStatsBody):
    with Session(engine) as session:
        user = session.get(User, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="아직 인증하지 않은 사용자입니다")
        user.team_name = body.team_name
        user.overall = body.overall
        session.add(user)
        session.commit()
        guild_id, team_role_ids = user.guild_id, _team_role_ids(session, user.guild_id)

    role_synced = True
    try:
        await sync_team_role(guild_id, discord_id, body.team_name, team_role_ids)
    except RuntimeError:
        role_synced = False

    return {"ok": True, "role_synced": role_synced}


class SetTeamRoleBody(BaseModel):
    guild_id: str
    team_name: str
    role_id: str


@router.put("/team-roles", dependencies=[Depends(require_internal_key)])
def set_team_role(body: SetTeamRoleBody):
    with Session(engine) as session:
        row = session.get(TeamRole, (body.guild_id, body.team_name))
        if row is None:
            row = TeamRole(guild_id=body.guild_id, team_name=body.team_name, role_id=body.role_id)
        else:
            row.role_id = body.role_id
        session.add(row)
        session.commit()
    return {"ok": True}


class TeamRoleEntry(BaseModel):
    team_name: str
    role_id: str


@router.get(
    "/team-roles",
    response_model=list[TeamRoleEntry],
    dependencies=[Depends(require_internal_key)],
)
def list_team_roles(guild_id: str):
    with Session(engine) as session:
        rows = session.exec(select(TeamRole).where(TeamRole.guild_id == guild_id)).all()
    return [TeamRoleEntry(team_name=r.team_name, role_id=r.role_id) for r in rows]


class EventEntry(BaseModel):
    title: str
    url: str
    regdate: str


@router.get(
    "/events",
    response_model=list[EventEntry],
    dependencies=[Depends(require_internal_key)],
)
async def get_events():
    try:
        events = await fetch_ongoing_events()
    except CommunityFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return [EventEntry(**e) for e in events]
