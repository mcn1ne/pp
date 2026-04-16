import math
from typing import Literal
from backend.schemas.evaluation import ScoreBreakdown
from backend.schemas.video import VideoList
from backend.schemas.sentiment import SentimentSummary
from backend.config import settings


def calculate_subscriber_score(subscriber_count: int) -> float:
    """구독자 점수 (0-100). 500명 미만이면 0, 로그 스케일."""
    if subscriber_count < settings.min_subscriber_count:
        return 0.0
    # 500 -> ~40, 5K -> ~60, 50K -> ~80, 500K+ -> 100
    score = (math.log10(subscriber_count) - math.log10(500)) / (math.log10(500000) - math.log10(500)) * 100
    return min(round(score, 1), 100.0)


def calculate_engagement_score(avg_engagement_rate: float) -> float:
    """참여도 점수 (0-100). 게임 유튜브 벤치마크 기준 3-5%."""
    if avg_engagement_rate >= 8.0:
        return 100.0
    if avg_engagement_rate >= 5.0:
        return 80.0 + (avg_engagement_rate - 5.0) / 3.0 * 20.0
    if avg_engagement_rate >= 3.0:
        return 60.0 + (avg_engagement_rate - 3.0) / 2.0 * 20.0
    if avg_engagement_rate >= 1.0:
        return 30.0 + (avg_engagement_rate - 1.0) / 2.0 * 30.0
    return max(avg_engagement_rate / 1.0 * 30.0, 0.0)


def calculate_growth_score(video_list: VideoList) -> float:
    """성장률 점수 (0-100). 최근 영상 vs 이전 영상 조회수 비교."""
    videos = video_list.videos
    if len(videos) < 4:
        return 50.0  # 데이터 부족 시 중간값

    mid = len(videos) // 2
    recent_avg = sum(v.view_count for v in videos[:mid]) / mid
    older_avg = sum(v.view_count for v in videos[mid:]) / (len(videos) - mid)

    if older_avg == 0:
        return 50.0

    growth_ratio = recent_avg / older_avg

    if growth_ratio >= 2.0:
        return 100.0
    if growth_ratio >= 1.5:
        return 80.0 + (growth_ratio - 1.5) / 0.5 * 20.0
    if growth_ratio >= 1.0:
        return 50.0 + (growth_ratio - 1.0) / 0.5 * 30.0
    if growth_ratio >= 0.5:
        return 20.0 + (growth_ratio - 0.5) / 0.5 * 30.0
    return max(growth_ratio * 40.0, 0.0)


def calculate_sentiment_score(sentiment: SentimentSummary) -> float:
    """감성 점수 (0-100). 긍정 비율 기반."""
    if sentiment.analyzed_count == 0:
        return 50.0
    # 긍정 비율 0.8+ -> 90+, 0.5 -> 50, 0.2 이하 -> 20 이하
    score = sentiment.positive_ratio * 100
    # 부정 비율이 높으면 감점
    penalty = sentiment.negative_ratio * 30
    return min(max(round(score - penalty, 1), 0.0), 100.0)


def calculate_consistency_score(upload_frequency_days: float) -> float:
    """일관성 점수 (0-100). 업로드 빈도 기반."""
    if upload_frequency_days <= 0:
        return 0.0
    if upload_frequency_days <= 3:   # 3일 이내 (주 2-3회)
        return 100.0
    if upload_frequency_days <= 7:   # 주 1회
        return 80.0
    if upload_frequency_days <= 14:  # 격주 1회
        return 60.0
    if upload_frequency_days <= 30:  # 월 1회
        return 40.0
    return 20.0


def calculate_scores(
    subscriber_count: int,
    video_list: VideoList,
    sentiment: SentimentSummary,
) -> tuple[ScoreBreakdown, float, Literal["PASS", "FAIL", "REVIEW"]]:
    """종합 점수를 계산하고 추천 결과를 반환한다."""
    breakdown = ScoreBreakdown(
        subscriber_score=calculate_subscriber_score(subscriber_count),
        engagement_score=calculate_engagement_score(video_list.avg_engagement_rate),
        growth_score=calculate_growth_score(video_list),
        sentiment_score=calculate_sentiment_score(sentiment),
        consistency_score=calculate_consistency_score(video_list.upload_frequency_days),
    )

    composite = (
        breakdown.subscriber_score * 0.20 +
        breakdown.engagement_score * 0.25 +
        breakdown.growth_score * 0.20 +
        breakdown.sentiment_score * 0.20 +
        breakdown.consistency_score * 0.15
    )
    composite = round(composite, 1)

    # 추천 로직
    meets_subscriber = subscriber_count >= settings.min_subscriber_count
    meets_score = composite >= settings.pass_score_threshold

    if meets_score and meets_subscriber:
        recommendation = "PASS"
    elif meets_score or meets_subscriber:
        recommendation = "REVIEW"
    else:
        recommendation = "FAIL"

    return breakdown, composite, recommendation
