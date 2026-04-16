from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from backend.auth import require_admin
from backend.config import settings
from backend.api.v1.router import router as v1_router
from backend.database import init_db
from backend.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(title="파트너 크리에이터 평가 도구", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ADMIN_CONSOLE_FILE = os.path.join(
    os.path.dirname(__file__), "templates", "admin_console.html"
)
# 추측이 어려운 관리자 콘솔 경로. 필요 시 ADMIN_CONSOLE_PATH 환경변수로 교체 가능.
ADMIN_CONSOLE_PATH = os.environ.get("ADMIN_CONSOLE_PATH", "/sc-9f3b2a7c")


@app.get(ADMIN_CONSOLE_PATH, include_in_schema=False)
async def admin_console(_: str = Depends(require_admin)):
    return FileResponse(ADMIN_CONSOLE_FILE, media_type="text/html")


frontend_dir = os.path.join(BASE_DIR, "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
