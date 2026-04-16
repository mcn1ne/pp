from fastapi import APIRouter
from backend.api.v1.endpoints.channel import router as channel_router
from backend.api.v1.endpoints.analysis import router as analysis_router
from backend.api.v1.endpoints.creators import router as creators_router
from backend.api.v1.endpoints.schedule import router as schedule_router
from backend.api.v1.endpoints.keywords import router as keywords_router

router = APIRouter()
router.include_router(channel_router)
router.include_router(analysis_router)
router.include_router(creators_router)
router.include_router(schedule_router)
router.include_router(keywords_router)


@router.get("/health")
async def health_check():
    return {"status": "ok"}
