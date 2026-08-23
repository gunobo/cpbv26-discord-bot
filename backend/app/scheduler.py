"""주기적으로 인증된 유저의 팀/오버롤을 게임 데이터 API에서 다시 조회해 갱신한다.

지금은 GameDataProvider가 MockGameDataProvider(항상 None 반환)라서 실제로
바뀌는 값은 없다. 나중에 진짜 게임 데이터 API 구현체로 교체되면 코드 변경
없이 이 스케줄러가 그대로 동작한다.
"""
import asyncio
import logging
from datetime import datetime

from sqlmodel import Session, select

from app.db.session import engine
from app.discord_rest import sync_team_role
from app.gamedata.provider import GameDataProvider
from app.teamrole.service import get_team_role_ids
from app.users.models import User

logger = logging.getLogger(__name__)


async def refresh_all_stats(game_data_provider: GameDataProvider) -> None:
    with Session(engine) as session:
        players = [
            (u.discord_id, u.player_id)
            for u in session.exec(select(User).where(User.player_id.is_not(None))).all()
        ]

    for discord_id, player_id in players:
        try:
            stats = await game_data_provider.get_player_stats(player_id)
        except Exception:
            logger.exception("스탯 조회 실패: discord_id=%s", discord_id)
            continue

        if stats.team_name is None and stats.overall is None:
            continue  # 실제 게임 데이터 API가 없는 동안은 항상 이 경로

        with Session(engine) as session:
            user = session.get(User, discord_id)
            if user is None:
                continue
            if user.team_name == stats.team_name and user.overall == stats.overall:
                continue

            user.team_name = stats.team_name
            user.overall = stats.overall
            user.stats_updated_at = datetime.utcnow()
            session.add(user)
            session.commit()
            guild_id, team_role_ids = user.guild_id, get_team_role_ids(session, user.guild_id)

        try:
            await sync_team_role(guild_id, discord_id, stats.team_name, team_role_ids)
        except RuntimeError:
            logger.warning("구단 역할 동기화 실패: discord_id=%s", discord_id)


async def run_scheduler(game_data_provider: GameDataProvider, interval_seconds: int) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await refresh_all_stats(game_data_provider)
        except Exception:
            logger.exception("스탯 갱신 스케줄러 실행 중 오류")
