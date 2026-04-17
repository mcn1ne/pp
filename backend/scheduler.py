import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.database import get_all_creators, get_schedule, update_schedule_last_run

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
JOB_ID = "auto_evaluate_all"

_batch_status: dict = {
    "running": False,
    "total": 0,
    "done": 0,
    "current": None,
    "started_at": None,
}


def get_batch_status() -> dict:
    return dict(_batch_status)


def run_all_evaluations():
    """등록된 모든 크리에이터를 순차 평가한다."""
    global _batch_status

    if _batch_status["running"]:
        logger.warning("이전 배치 실행이 아직 진행 중입니다. 중복 실행을 건너뜁니다.")
        return

    from backend.api.v1.endpoints.creators import run_evaluation

    creators = get_all_creators()
    _batch_status = {
        "running": True,
        "total": len(creators),
        "done": 0,
        "current": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"스케줄 실행: {len(creators)}개 크리에이터 평가 시작")

      failed = []
      try:
          with ThreadPoolExecutor(max_workers=3) as executor:
              future_to_creator = {
                  executor.submit(run_evaluation, c): c for c in creators
              }
              for future in as_completed(future_to_creator):
                  creator = future_to_creator[future]
                  name = creator.get("channel_name") or creator["url"]
                  try:
                      result = future.result()
                      logger.info(f"  [{name}] → {result['recommendation']} ({result['composite_score']}점)")
                  except Exception as e:
                      logger.error(f"  [{name}] 평가 실패: {e}")
                      failed.append(name)
                  finally:
                      _batch_status["done"] += 1
                      _batch_status["current"] = name
      finally:
          _batch_status["running"] = False
          _batch_status["current"] = None
          update_schedule_last_run()
          if failed:
              logger.warning(f"실패한 크리에이터 ({len(failed)}건): {', '.join(failed)}")
          logger.info(f"스케줄 실행 완료 (성공 {len(creators) - len(failed)}/{len(creators)})")


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
        max_instances=1,
        coalesce=True,
    )
