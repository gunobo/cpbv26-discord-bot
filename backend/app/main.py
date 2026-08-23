import asyncio

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import init_db
from app.routers import internal, verify
from app.scheduler import run_scheduler

app = FastAPI(title="컴프야v26 인증 백엔드")

app.include_router(verify.router)
app.include_router(internal.router)


@app.on_event("startup")
async def on_startup():
    init_db()
    app.state.scheduler_task = asyncio.create_task(
        run_scheduler(verify.game_data_provider, settings.stats_refresh_interval_seconds)
    )


@app.on_event("shutdown")
async def on_shutdown():
    task = getattr(app.state, "scheduler_task", None)
    if task is not None:
        task.cancel()


@app.get("/health")
def health():
    return {"ok": True}
