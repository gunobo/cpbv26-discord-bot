import httpx

from app.core.config import settings

DISCORD_API = "https://discord.com/api/v10"


async def grant_verified_role(guild_id: str, user_id: str) -> None:
    if not settings.discord_token or not settings.verified_role_id:
        return
    url = f"{DISCORD_API}/guilds/{guild_id}/members/{user_id}/roles/{settings.verified_role_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.put(
            url,
            headers={"Authorization": f"Bot {settings.discord_token}"},
        )
    if resp.status_code not in (204, 201):
        raise RuntimeError(f"역할 부여 실패 ({resp.status_code}): {resp.text}")


async def revoke_role(guild_id: str, user_id: str, role_id: str) -> None:
    if not settings.discord_token or not role_id:
        return
    url = f"{DISCORD_API}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.delete(url, headers={"Authorization": f"Bot {settings.discord_token}"})


async def sync_team_role(
    guild_id: str, user_id: str, team_name: str | None, team_role_ids: dict[str, str]
) -> None:
    """team_name에 해당하는 구단 역할만 남기고 나머지 구단 역할은 제거한다.
    team_role_ids: {구단명: 역할ID} — TeamRole 테이블에서 조회해 전달한다."""
    if not settings.discord_token or not team_role_ids:
        return

    target_role_id = team_role_ids.get(team_name) if team_name else None
    headers = {"Authorization": f"Bot {settings.discord_token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        for name, role_id in team_role_ids.items():
            if role_id == target_role_id:
                continue
            await client.delete(
                f"{DISCORD_API}/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
                headers=headers,
            )

        if target_role_id:
            resp = await client.put(
                f"{DISCORD_API}/guilds/{guild_id}/members/{user_id}/roles/{target_role_id}",
                headers=headers,
            )
            if resp.status_code not in (204, 201):
                raise RuntimeError(f"구단 역할 부여 실패 ({resp.status_code}): {resp.text}")
