from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth import require_admin
from backend.database import get_schedule, update_schedule
from backend.scheduler import refresh_scheduler, get_batch_status

router = APIRouter(
    prefix="/schedule",
    tags=["schedule"],
    dependencies=[Depends(require_admin)],
)


class ScheduleUpdateRequest(BaseModel):
    cron_expression: str
    enabled: bool


@router.get("")
async def get_current_schedule():
    """현재 스케줄 설정을 반환한다."""
    return get_schedule()


@router.put("")
async def update_current_schedule(request: ScheduleUpdateRequest):
    """스케줄 설정을 변경한다. 변경 후 스케줄러가 자동 반영."""
    result = update_schedule(request.cron_expression, request.enabled)
    refresh_scheduler()
    return result


@router.get("/status")
async def schedule_batch_status():
    """현재 배치 실행 진행 상태를 반환한다."""
    return get_batch_status()
