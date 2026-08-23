from sqlmodel import Session, select

from app.teamrole.models import TeamRole


def get_team_role_ids(session: Session, guild_id: str) -> dict[str, str]:
    rows = session.exec(select(TeamRole).where(TeamRole.guild_id == guild_id)).all()
    return {row.team_name: row.role_id for row in rows}
