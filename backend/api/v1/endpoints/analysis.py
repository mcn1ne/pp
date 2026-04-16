from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.channel_resolver import resolve_channel_id
from backend.services.youtube_service import (
    get_channel_info, get_recent_videos, get_all_video_comments,
    filter_supercent_videos,
)
from backend.services.gemini_service import analyze_comments, generate_evaluation_summary
from backend.services.scoring_service import calculate_scores
from backend.schemas.evaluation import EvaluationResult

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    url: str
    days: int = 30                 # 최근 N일 이내 영상
    supercent_filter: bool = True  # 슈퍼센트 필터 ON/OFF


@router.post("", response_model=EvaluationResult)
async def analyze_creator(request: AnalyzeRequest):
    """크리에이터 전체 분석 파이프라인을 실행한다."""
    try:
        # 1) 채널 ID 변환
        resolved = resolve_channel_id(request.url)
        channel_id = resolved["channel_id"]

        # 2) 채널 정보 수집
        channel = get_channel_info(channel_id)

        # 3) 최근 N일 이내 영상 수집
        video_list = get_recent_videos(channel_id, days=request.days)

        # 4) 필터 적용 여부에 따라 대상 영상 결정
        if request.supercent_filter:
            supercent_videos = filter_supercent_videos(video_list.videos)
            # 슈퍼센트 관련 영상이 없으면 전체 영상으로 폴백
            if supercent_videos:
                target_videos = supercent_videos
            else:
                target_videos = video_list.videos
        else:
            supercent_videos = []
            target_videos = video_list.videos

        # 5) 대상 영상의 모든 댓글 수집
        all_comments = []
        for video in target_videos:
            comments = get_all_video_comments(video.video_id, max_pages=10)
            all_comments.extend(comments)

        # 6) Gemini 감성분석
        sentiment = analyze_comments(all_comments, channel.title)

        # 6) 점수 계산
        breakdown, composite, recommendation = calculate_scores(
            channel.subscriber_count, video_list, sentiment
        )

        # 7) AI 평가 요약 생성
        ai_summary = generate_evaluation_summary(
            channel_name=channel.title,
            subscriber_count=channel.subscriber_count,
            composite_score=composite,
            recommendation=recommendation,
            sentiment_summary=sentiment.overall_sentiment,
            avg_views=video_list.avg_views,
            avg_engagement=video_list.avg_engagement_rate,
        )

        return EvaluationResult(
            channel=channel,
            videos=video_list,
            supercent_video_count=len(supercent_videos),
            total_comments_analyzed=len(all_comments),
            supercent_filter_active=request.supercent_filter,
            used_fallback=request.supercent_filter and len(supercent_videos) == 0,
            sentiment=sentiment,
            score_breakdown=breakdown,
            composite_score=composite,
            pass_threshold=composite >= 60 and channel.subscriber_count >= 500,
            recommendation=recommendation,
            ai_summary=ai_summary,
            evaluated_at=datetime.now(timezone.utc),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")
