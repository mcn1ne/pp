import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database import get_all_creators, get_schedule, update_schedule_last_run

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
JOB_ID = "auto_evaluate_all"


def run_all_evaluations():
    """등록된 모든 크리에이터를 순차 평가한다."""
    from backend.api.v1.endpoints.creators import run_evaluation

    creators = get_all_creators()
    logger.info(f"스케줄 실행: {len(creators)}개 크리에이터 평가 시작")

    for creator in creators:
        try:
            result = run_evaluation(creator)
            logger.info(f"  [{creator['url']}] → {result['recommendation']} ({result['composite_score']}점)")
        except Exception as e:
            logger.error(f"  [{creator['url']}] 평가 실패: {e}")

    update_schedule_last_run()
    logger.info("스케줄 실행 완료")


def start_scheduler():
    """스케줄러를 시작한다."""
    schedule = get_schedule()
    if schedule and schedule["enabled"]:
        _apply_schedule(schedule["cron_expression"])
    scheduler.start()
    logger.info("스케줄러 시작됨")


def refresh_scheduler():
    """DB의 스케줄 설정을 다시 읽어 적용한다."""
    schedule = get_schedule()
    if not schedule:
        return

    # 기존 작업 제거
    if scheduler.get_job(JOB_ID):
        scheduler.remove_job(JOB_ID)

    if schedule["enabled"]:
        _apply_schedule(schedule["cron_expression"])
        logger.info(f"스케줄 갱신: {schedule['cron_expression']} (활성)")
    else:
        logger.info("스케줄 비활성화됨")


def _apply_schedule(cron_expression: str):
    """cron 표현식으로 작업을 등록한다."""
    parts = cron_expression.split()
    if len(parts) != 5:
        logger.error(f"잘못된 cron 표현식: {cron_expression}")
        return

    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
    )
    scheduler.add_job(
        run_all_evaluations,
        trigger,
        id=JOB_ID,
        replace_existing=True,
        misfire_grace_time=3600,
    )
