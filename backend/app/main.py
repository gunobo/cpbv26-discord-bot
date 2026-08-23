from fastapi import FastAPI

from app.db.session import init_db
from app.routers import internal, verify

app = FastAPI(title="컴프야v26 인증 백엔드")

app.include_router(verify.router)
app.include_router(internal.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}
