from app.gamedata.provider import GameDataProvider, PlayerStats


class MockGameDataProvider(GameDataProvider):
    """실제 게임 데이터 API가 없으므로 값을 채우지 않는다.
    운영자가 /스탯설정 커맨드로 직접 팀/오버롤을 입력해야 리더보드에 표시된다."""

    async def get_player_stats(self, player_id: str) -> PlayerStats:
        return PlayerStats(team_name=None, overall=None)
