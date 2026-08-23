from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.core.internal_auth import require_internal_key
from app.db.session import engine
from app.discord_rest import grant_verified_role, sync_team_role
from app.gamedata.mock_provider import MockGameDataProvider
from app.teamrole.service import get_team_role_ids
from app.users.models import User
from app.verify.cookies import COOKIE_MAX_AGE_SECONDS, COOKIE_NAME, sign_token, unsign_token
from app.verify.hive import client as hive_client
from app.verify.hive import mock as hive_mock
from app.verify.models import VerificationState

router = APIRouter(prefix="/verify", tags=["verify"])
internal_router = APIRouter(prefix="/internal", tags=["verify"], dependencies=[Depends(require_internal_key)])

game_data_provider = MockGameDataProvider()


def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title></head>"
        f"<body style='font-family:sans-serif;text-align:center;padding-top:80px'>"
        f"<h2>{title}</h2><p>{body}</p></body></html>"
    )


@router.get("/start")
def verify_start(token: str):
    with Session(engine) as session:
        state = session.get(VerificationState, token)
        if state is None or not state.is_valid():
            return _page("인증 링크가 유효하지 않습니다", "디스코드에서 /인증 을 다시 실행해주세요.")

    redirect_target = (
        hive_mock.mock_login_redirect_target(f"{settings.web_base_url}/verify/callback")
        if settings.hive_mock_mode
        else hive_client.build_login_url()
    )
    resp = RedirectResponse(redirect_target)
    resp.set_cookie(
        COOKIE_NAME,
        sign_token(token),
        max_age=COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return resp


@router.get("/callback")
async def verify_callback(request: Request, res: str | None = None, state: str | None = None):
    signed_cookie = request.cookies.get(COOKIE_NAME)
    token = unsign_token(signed_cookie) if signed_cookie else None
    if token is None:
        return _page("인증 세션을 찾을 수 없습니다", "디스코드에서 /인증 을 다시 실행해주세요.")

    with Session(engine) as session:
        v_state = session.get(VerificationState, token)
        if v_state is None or not v_state.is_valid():
            return _page("인증 링크가 만료되었습니다", "디스코드에서 /인증 을 다시 실행해주세요.")

        if settings.hive_mock_mode:
            hive_state = state or "mock-state"
        else:
            if not res:
                return _page("인증에 실패했습니다", "Hive 로그인 응답이 없습니다.")
            decoded = hive_client.decode_login_result(res)
            if str(decoded.get("code")) != "100":
                return _page("인증에 실패했습니다", f"Hive 오류 코드: {decoded.get('code')}")
            hive_state = decoded["state"]

        try:
            if settings.hive_mock_mode:
                idp_info = hive_mock.mock_verify_state(hive_state)
                player_result = hive_mock.mock_get_player_id(idp_info)
            else:
                idp_info = await hive_client.verify_state(hive_state)
                player_result = await hive_client.get_player_id(idp_info)
        except hive_client.NoLinkedPlayerError:
            return _page(
                "컴프야v26 계정을 찾을 수 없습니다",
                "이 Hive 계정으로 컴프야v26을 먼저 플레이한 뒤 다시 시도해주세요.",
            )
        except hive_client.HiveError as exc:
            return _page("인증에 실패했습니다", str(exc))

        stats = await game_data_provider.get_player_stats(player_result.player_id)

        user = session.get(User, v_state.discord_id)
        if user is None:
            user = User(discord_id=v_state.discord_id, guild_id=v_state.guild_id,
                        verification_method="hive", player_id=player_result.player_id,
                        idp_user_id=idp_info.idp_user_id, idp_index=idp_info.idp_index)
        else:
            user.verification_method = "hive"
            user.player_id = player_result.player_id
            user.idp_user_id = idp_info.idp_user_id
            user.idp_index = idp_info.idp_index
        if stats.team_name is not None:
            user.team_name = stats.team_name
        if stats.overall is not None:
            user.overall = stats.overall

        v_state.consumed = True
        session.add(user)
        session.add(v_state)
        session.commit()

        discord_id, guild_id, team_name = user.discord_id, user.guild_id, user.team_name
        team_role_ids = get_team_role_ids(session, guild_id)

    try:
        await grant_verified_role(guild_id, discord_id)
    except RuntimeError as exc:
        return _page("역할 부여 중 오류가 발생했습니다", f"관리자에게 문의해주세요. ({exc})")

    try:
        await sync_team_role(guild_id, discord_id, team_name, team_role_ids)
    except RuntimeError:
        pass  # 팀 정보가 아직 없거나(모킹 상태) 역할 매핑이 안 된 경우 — 인증 자체는 성공으로 처리

    resp = _page("인증이 완료되었습니다", "디스코드로 돌아가서 /리더보드 를 사용해보세요.")
    resp.delete_cookie(COOKIE_NAME)
    return resp


class CreateVerifyRequestBody(BaseModel):
    discord_id: str
    guild_id: str


class VerifyRequestResponse(BaseModel):
    mode: str  # "hive" | "rules"
    verify_url: str | None = None
    role_granted: bool | None = None  # mode == "rules" 일 때만 의미 있음


@internal_router.get("/status")
def get_status():
    return {"hive_connected": settings.hive_connected, "hive_mock_mode": settings.hive_mock_mode}


@internal_router.post("/verify-requests", response_model=VerifyRequestResponse)
async def create_verify_request(body: CreateVerifyRequestBody):
    if settings.hive_connected:
        with Session(engine) as session:
            state = VerificationState(discord_id=body.discord_id, guild_id=body.guild_id)
            session.add(state)
            session.commit()
            session.refresh(state)
            token = state.token

        return VerifyRequestResponse(
            mode="hive",
            verify_url=f"{settings.web_base_url}/verify/start?token={token}",
        )

    # Hive 연동 전: 규칙 체크(봇에서 이미 확인됨)만으로 즉시 인증 완료 처리
    with Session(engine) as session:
        user = session.get(User, body.discord_id)
        if user is None:
            user = User(
                discord_id=body.discord_id,
                guild_id=body.guild_id,
                verification_method="rules",
            )
        else:
            user.verification_method = "rules"
        session.add(user)
        session.commit()

    role_granted = True
    try:
        await grant_verified_role(body.guild_id, body.discord_id)
    except RuntimeError:
        role_granted = False

    return VerifyRequestResponse(mode="rules", role_granted=role_granted)
