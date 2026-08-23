import base64
import json
from urllib.parse import quote, unquote

import httpx

from app.core.config import settings
from app.verify.hive.types import IdpInfo, PlayerIdResult

WEBLOGIN_HOSTS = {
    "production": "https://weblogin.withhive.com",
    "sandbox": "https://sandbox-weblogin.withhive.com",
}
AUTH_HOSTS = {
    "production": "https://auth.qpyou.cn",
    "sandbox": "https://sandbox-auth.qpyou.cn",
}


class HiveError(Exception):
    pass


class NoLinkedPlayerError(HiveError):
    """이 Hive/소셜 계정에 컴프야v26 캐릭터가 연결되어 있지 않을 때 (result_code 2002)."""


def _weblogin_host() -> str:
    return WEBLOGIN_HOSTS[settings.hive_env]


def _auth_host() -> str:
    return AUTH_HOSTS[settings.hive_env]


def build_login_url(*, country: str = "KR", language: str = "ko") -> str:
    """https://developers.hiveplatform.ai 웹 로그인 v2: JSON -> urlencode -> base64."""
    payload = {
        "appid": settings.hive_appid,
        "gindex": settings.hive_gindex,
        "url": settings.hive_redirect_url,
        "country": country,
        "language": language,
    }
    encoded = quote(json.dumps(payload, separators=(",", ":")))
    param = base64.b64encode(encoded.encode()).decode()
    return f"{_weblogin_host()}/login?param={param}"


def decode_login_result(res: str) -> dict:
    """콜백의 res 쿼리파라미터(base64(urlencode(json)))를 디코드한다."""
    decoded_b64 = base64.b64decode(res).decode()
    decoded_json = unquote(decoded_b64)
    return json.loads(decoded_json)


async def verify_state(state: str) -> IdpInfo:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_weblogin_host()}/idp_info_v2",
            json={"state": state},
        )
    data = resp.json()
    if data.get("code") != 100:
        raise HiveError(f"idp_info_v2 실패: {data}")
    return IdpInfo(
        appid=data["appid"],
        idp_index=data["idp_index"],
        idp_user_id=data["idp_user_id"],
    )


async def get_player_id(idp_info: IdpInfo) -> PlayerIdResult:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{_auth_host()}/game/player/get-playerid",
            headers={"ISCRYPT": "0"},
            json={
                "appid": idp_info.appid,
                "idp_user_id": idp_info.idp_user_id,
                "idp_index": idp_info.idp_index,
                "hive_certification_key": settings.hive_certification_key,
            },
        )
    data = resp.json()
    result_code = data.get("result_code")
    if result_code == 2002:
        raise NoLinkedPlayerError("이 계정에는 컴프야v26 캐릭터가 연결되어 있지 않습니다.")
    if result_code != 0:
        raise HiveError(f"get-playerid 실패: {data}")
    return PlayerIdResult(player_id=data["data"]["player_id"])
