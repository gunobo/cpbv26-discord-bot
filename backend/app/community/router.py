from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.community.client import CommunityFetchError, fetch_coupons, fetch_ongoing_events
from app.core.internal_auth import require_internal_key

router = APIRouter(prefix="/internal", tags=["community"], dependencies=[Depends(require_internal_key)])


class EventEntry(BaseModel):
    title: str
    url: str
    regdate: str


@router.get("/events", response_model=list[EventEntry])
async def get_events():
    try:
        events = await fetch_ongoing_events()
    except CommunityFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return [EventEntry(**e) for e in events]


class CouponEntry(BaseModel):
    code: str
    reward: str
    period: str
    url: str | None


@router.get("/coupons", response_model=list[CouponEntry])
async def get_coupons():
    try:
        coupons = await fetch_coupons()
    except CommunityFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return [CouponEntry(**c) for c in coupons]
