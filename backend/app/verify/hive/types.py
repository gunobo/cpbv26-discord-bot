from dataclasses import dataclass


@dataclass
class IdpInfo:
    appid: str
    idp_index: int
    idp_user_id: str


@dataclass
class PlayerIdResult:
    player_id: str
