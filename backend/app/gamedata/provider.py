"""컴프야v26 게임 데이터(팀/오버롤) 조회 인터페이스.

Hive 플랫폼 API에는 이 데이터가 없다 (인증/빌링/알림 API만 제공).
컴투스 쪽에서 별도 API가 확정되면 이 인터페이스의 새 구현체를 만들어
main.py에서 provider를 교체하면 된다. 그 전까지는 MockGameDataProvider
(항상 None 반환) + /스탯설정 운영자 커맨드로 수동 입력해서 운영한다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PlayerStats:
    team_name: str | None
    overall: int | None


class GameDataProvider(ABC):
    @abstractmethod
    async def get_player_stats(self, player_id: str) -> PlayerStats:
        raise NotImplementedError
