from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.internal_auth import require_internal_key
from app.db.session import engine
from app.teamrole.models import TeamRole

router = APIRouter(prefix="/internal", tags=["teamrole"], dependencies=[Depends(require_internal_key)])


class SetTeamRoleBody(BaseModel):
    guild_id: str
    team_name: str
    role_id: str


@router.put("/team-roles")
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


@router.get("/team-roles", response_model=list[TeamRoleEntry])
def list_team_roles(guild_id: str):
    with Session(engine) as session:
        rows = session.exec(select(TeamRole).where(TeamRole.guild_id == guild_id)).all()
    return [TeamRoleEntry(team_name=r.team_name, role_id=r.role_id) for r in rows]
