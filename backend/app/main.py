import asyncio

from fastapi import FastAPI

from app.community.cache import run_coupon_cache_scheduler
from app.community.router import router as community_router
from app.core.config import settings
from app.db.session import init_db
from app.leaderboard.router import router as leaderboard_router
from app.scheduler import run_scheduler
from app.teamrole.router import router as teamrole_router
from app.users.router import router as users_router
from app.verify.router import game_data_provider
from app.verify.router import internal_router as verify_internal_router
from app.verify.router import router as verify_router

app = FastAPI(title="컴프야v26 인증 백엔드")

app.include_router(verify_router)
app.include_router(verify_internal_router)
app.include_router(users_router)
app.include_router(leaderboard_router)
app.include_router(teamrole_router)
app.include_router(community_router)


@app.on_event("startup")
async def on_startup():
    init_db()
    app.state.stats_scheduler_task = asyncio.create_task(
        run_scheduler(game_data_provider, settings.stats_refresh_interval_seconds)
    )
    app.state.coupon_scheduler_task = asyncio.create_task(
        run_coupon_cache_scheduler(settings.coupon_refresh_interval_seconds)
    )


@app.on_event("shutdown")
async def on_shutdown():
    for attr in ("stats_scheduler_task", "coupon_scheduler_task"):
        task = getattr(app.state, attr, None)
        if task is not None:
            task.cancel()


@app.get("/health")
def health():
    return {"ok": True}
