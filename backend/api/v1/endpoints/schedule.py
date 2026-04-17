from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apscheduler.triggers.cron import CronTrigger

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
    parts = request.cron_expression.strip().split()
    if len(parts) != 5:
        raise HTTPException(status_code=422, detail="cron 표현식은 '분 시 일 월 요일' 5개 필드여야 합니다.")
    try:
        minute, hour, day, month, dow = parts
        CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"잘못된 cron 표현식: {e}")

    result = update_schedule(request.cron_expression, request.enabled)
    refresh_scheduler()
    return result


@router.get("/status")
async def schedule_batch_status():
    """현재 배치 실행 진행 상태를 반환한다."""
    return get_batch_status()
