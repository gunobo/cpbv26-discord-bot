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
