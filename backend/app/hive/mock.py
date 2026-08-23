"""HIVE_MOCK_MODE=true일 때 사용하는 가짜 Hive 응답.

Hive 콘솔 키(appid/gindex/hive_certification_key)가 발급되기 전까지
전체 인증 플로우를 실제 Hive 서버 없이 개발/테스트할 수 있게 해준다.
"""
import uuid

from app.hive.types import IdpInfo, PlayerIdResult


def mock_login_redirect_target(callback_url: str) -> str:
    """실제로는 Hive 로그인 페이지로 보내야 하지만, 모킹 모드에서는
    로그인이 즉시 성공한 것처럼 콜백 URL로 바로 이동시킨다."""
    fake_state = f"mock-state-{uuid.uuid4().hex[:8]}"
    return f"{callback_url}?res=MOCK&state={fake_state}"


def mock_verify_state(state: str) -> IdpInfo:
    return IdpInfo(
        appid="mock-appid",
        idp_index=1,
        idp_user_id=f"mock-idp-{state}",
    )


def mock_get_player_id(idp_info: IdpInfo) -> PlayerIdResult:
    return PlayerIdResult(player_id=f"mock-player-{idp_info.idp_user_id[-8:]}")
