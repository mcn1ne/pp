from pydantic import BaseModel
from datetime import datetime
from typing import Literal

from backend.schemas.channel import ChannelInfo
from backend.schemas.video import VideoList
from backend.schemas.sentiment import SentimentSummary


class ScoreBreakdown(BaseModel):
    subscriber_score: float       # 0-100, weight 20%
    engagement_score: float       # 0-100, weight 25%
    growth_score: float           # 0-100, weight 20%
    sentiment_score: float        # 0-100, weight 20%
    consistency_score: float      # 0-100, weight 15%


class EvaluationResult(BaseModel):
    channel: ChannelInfo
    videos: VideoList
    supercent_video_count: int      # 슈퍼센트 관련 영상 수
    total_comments_analyzed: int    # 수집된 총 댓글 수
    supercent_filter_active: bool   # 슈퍼센트 필터 적용 여부
    used_fallback: bool             # 필터 결과 없어서 전체 영상으로 폴백했는지
    sentiment: SentimentSummary
    score_breakdown: ScoreBreakdown
    composite_score: float
    pass_threshold: bool
    recommendation: Literal["PASS", "FAIL", "REVIEW"]
    ai_summary: str
    evaluated_at: datetime
