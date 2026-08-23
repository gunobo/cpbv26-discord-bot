"""쿠폰 목록을 주기적으로 미리 가져와 캐싱한다. /internal/coupons는 매 요청마다
커뮤니티 사이트를 긁는 대신 이 캐시를 즉시 반환한다."""
import asyncio
import logging

from app.community.client import CommunityFetchError, fetch_coupons

logger = logging.getLogger(__name__)

_cache: list[dict] = []


def get_cached_coupons() -> list[dict]:
    return _cache


async def refresh_coupon_cache() -> None:
    global _cache
    try:
        _cache = await fetch_coupons()
    except CommunityFetchError:
        logger.exception("쿠폰 캐시 갱신 실패 — 이전 캐시를 유지합니다")


async def run_coupon_cache_scheduler(interval_seconds: int) -> None:
    await refresh_coupon_cache()  # 기동 시 1회 즉시 채워서 첫 요청부터 바로 응답
    while True:
        await asyncio.sleep(interval_seconds)
        await refresh_coupon_cache()
