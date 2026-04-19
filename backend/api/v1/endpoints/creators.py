import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from googleapiclient.errors import HttpError
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from backend.auth import require_admin
from backend.database import (
    create_creator, get_all_creators, get_creator, delete_creator,
    update_creator_evaluation, get_creator_history,
)
from backend.config import settings
from backend.services.channel_resolver import resolve_channel_id
from backend.services.youtube_service import (
    get_channel_info, get_recent_videos, get_all_video_comments,
    filter_supercent_videos, split_supercent_videos,
)
from backend.services.gemini_service import analyze_comments, generate_evaluation_summary
from backend.services.scoring_service import calculate_scores
from backend.services.vision_filter import classify_by_thumbnail
from backend.schemas.evaluation import EvaluationResult

router = APIRouter(
    prefix="/creators",
    tags=["creators"],
    dependencies=[Depends(require_admin)],
)


class CreatorCreateRequest(BaseModel):
    url: str
    supercent_filter: bool = True


@router.get("")
async def list_creators():
    """등록된 모든 크리에이터 목록을 반환한다."""
    return get_all_creators()


@router.post("")
async def add_creator(request: CreatorCreateRequest):
    """크리에이터를 등록한다."""
    try:
        creator = create_creator(request.url, request.supercent_filter)
        return creator
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{creator_id}")
async def remove_creator(creator_id: int):
    """크리에이터를 삭제한다."""
    if not delete_creator(creator_id):
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")
    return {"status": "deleted"}


@router.get("/{creator_id}/history")
async def creator_history(creator_id: int):
    """크리에이터의 평가 히스토리를 반환한다."""
    creator = get_creator(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")
    return get_creator_history(creator_id)


@router.get("/{creator_id}/latest-result")
async def creator_latest_result(creator_id: int):
    """최근 평가 결과의 전체 내역(JSON)을 반환한다. 상세 대시보드 렌더용."""
    creator = get_creator(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")

    history = get_creator_history(creator_id, limit=1)
    if not history or not history[0].get("result_json"):
        raise HTTPException(status_code=404, detail="평가 이력이 없습니다.")

    try:
        payload = json.loads(history[0]["result_json"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=500, detail="평가 결과를 해석할 수 없습니다.")

    return payload


@router.post("/evaluate-all")
def evaluate_all_creators():
    """등록된 모든 크리에이터를 백그라운드에서 일괄 평가한다.

    스케줄 실행과 동일한 `run_all_evaluations()` 경로를 재사용한다.
    진행 상태는 `GET /api/v1/schedule/status` 로 폴링한다.
    """
    from backend.scheduler import run_all_evaluations, get_batch_status

    status = get_batch_status()
    if status.get("running"):
        raise HTTPException(status_code=409, detail="이미 일괄 평가가 진행 중입니다.")

    thread = threading.Thread(target=run_all_evaluations, daemon=True)
    thread.start()
    logger.info("수동 일괄 평가 시작 (관리자 콘솔)")
    return {"status": "started"}


@router.post("/{creator_id}/evaluate")
def evaluate_creator(creator_id: int):
    """특정 크리에이터를 즉시 평가한다. 스케줄과 동일하게 모든 예외를 잡아 로그에 남긴다."""
    creator = get_creator(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="크리에이터를 찾을 수 없습니다.")

    name = creator.get("channel_name") or creator.get("url") or f"id={creator_id}"
    try:
        result = run_evaluation(creator)
    except HttpError as e:
        if e.resp.status == 403 and "quotaExceeded" in str(e):
            logger.warning(f"[{name}] YouTube 할당량 초과")
            raise HTTPException(
                status_code=429,
                detail="YouTube Data API 일일 할당량을 초과했습니다. 태평양 시간 자정(한국시간 오후 4시)에 리셋됩니다.",
            )
        logger.exception(f"[{name}] YouTube API 오류")
        raise HTTPException(status_code=502, detail=f"YouTube API 오류: {e}")
    except ValueError as e:
        logger.warning(f"[{name}] 평가 입력 오류: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"[{name}] 평가 실패")
        raise HTTPException(status_code=500, detail=f"평가 실패: {e}")

    return result


def run_evaluation(creator: dict) -> dict:
    """크리에이터 평가를 실행하고 DB에 저장한다."""
    url = creator["url"]
    supercent_filter = bool(creator["supercent_filter"])

    resolved = resolve_channel_id(url)
    channel_id = resolved["channel_id"]
    channel = get_channel_info(channel_id)
    video_list = get_recent_videos(channel_id, days=30)

    if supercent_filter:
        sc_videos, unmatched = split_supercent_videos(video_list.videos)
        if settings.sc_vision_filter_enabled and unmatched:
            vision_hits = classify_by_thumbnail(unmatched)
            if vision_hits:
                hit_ids = {v.video_id for v in sc_videos} | {v.video_id for v in vision_hits}
                sc_videos = [v for v in video_list.videos if v.video_id in hit_ids]
        target_videos = sc_videos if sc_videos else video_list.videos
    else:
        sc_videos = []
        target_videos = video_list.videos

    all_comments = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_all_video_comments, v.video_id, 10): v for v in target_videos}
        for future in futures:
            all_comments.extend(future.result())

    sentiment = analyze_comments(all_comments, channel.title)

    breakdown, composite, recommendation = calculate_scores(
        channel.subscriber_count, video_list, sentiment
    )

    ai_summary = generate_evaluation_summary(
        channel_name=channel.title,
        subscriber_count=channel.subscriber_count,
        composite_score=composite,
        recommendation=recommendation,
        sentiment_summary=sentiment.overall_sentiment,
        avg_views=video_list.avg_views,
        avg_engagement=video_list.avg_engagement_rate,
    )

    sc_count = len(sc_videos) if supercent_filter else 0

    full_result = EvaluationResult(
        channel=channel,
        videos=video_list,
        supercent_video_count=sc_count,
        total_comments_analyzed=len(all_comments),
        supercent_filter_active=supercent_filter,
        used_fallback=supercent_filter and sc_count == 0,
        sentiment=sentiment,
        score_breakdown=breakdown,
        composite_score=composite,
        pass_threshold=composite >= 60 and channel.subscriber_count >= 500,
        recommendation=recommendation,
        ai_summary=ai_summary,
        evaluated_at=datetime.now(timezone.utc),
    )

    result_json = full_result.model_dump_json()

    update_creator_evaluation(
        creator_id=creator["id"],
        channel_id=channel_id,
        channel_name=channel.title,
        thumbnail_url=channel.thumbnail_url,
        subscriber_count=channel.subscriber_count,
        score=composite,
        recommendation=recommendation,
        ai_summary=ai_summary,
        result_json=result_json,
    )

    return {
        "composite_score": composite,
        "recommendation": recommendation,
        "ai_summary": ai_summary,
        "subscriber_count": channel.subscriber_count,
        "channel_name": channel.title,
    }
