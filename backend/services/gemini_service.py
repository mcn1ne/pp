import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from google import genai
from google.genai import types
from backend.config import settings
from backend.schemas.sentiment import SentimentSummary, NotableComment

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_BACKOFF = [2, 4]


@lru_cache(maxsize=1)
def _get_client():
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=1200),
    )


BATCH_SIZE = 100  # 배치당 댓글 수
# 배치 동시 처리 수 (Gemini RPM 한도에 따라 조정). 환경변수로 덮어쓰기 가능.
BATCH_CONCURRENCY = max(1, int(os.environ.get("GEMINI_BATCH_CONCURRENCY", "3")))


def analyze_comments(comments: list[str], channel_name: str) -> SentimentSummary:
    """Gemini API로 댓글 감성분석을 수행한다. 댓글이 많으면 배치로 나눠 병렬 분석."""
    if not comments:
        return SentimentSummary(
            positive_ratio=0, negative_ratio=0, neutral_ratio=0,
            key_themes=[], notable_comments=[], overall_sentiment="데이터 없음",
            analyzed_count=0,
        )

    # 배치로 분할
    batches = [comments[i:i + BATCH_SIZE] for i in range(0, len(comments), BATCH_SIZE)]

    # 배치별 Gemini 호출을 ThreadPoolExecutor로 병렬 처리
    # (google-genai SDK가 동기라 I/O bound 작업에는 쓰레드풀이 효과적)
    workers = min(BATCH_CONCURRENCY, len(batches))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(
            executor.map(lambda b: _analyze_batch(b, channel_name), batches)
        )

    # 실패한 배치는 제외하되, 가중치 계산을 위해 원본 배치 크기와 짝을 맞춰 유지
    paired = [
        (r, len(batch))
        for r, batch in zip(results, batches)
        if r is not None
    ]

    if not paired:
        return SentimentSummary(
            positive_ratio=0, negative_ratio=0, neutral_ratio=0,
            key_themes=[], notable_comments=[], overall_sentiment="분석 실패",
            analyzed_count=len(comments),
        )

    batch_results = [r for r, _ in paired]

    # 댓글 수를 가중치로 한 가중 평균.
    # 성공한 배치들의 댓글 수 합이 분모이므로 실패 배치는 자연스럽게 제외된다.
    total_weight = sum(w for _, w in paired)
    avg_positive = sum(r.get("positive_ratio", 0) * w for r, w in paired) / total_weight
    avg_negative = sum(r.get("negative_ratio", 0) * w for r, w in paired) / total_weight
    avg_neutral = sum(r.get("neutral_ratio", 0) * w for r, w in paired) / total_weight

    # 비율 합이 1.0이 되도록 정규화 (Gemini 응답이 정확히 1이 아닐 때 보정)
    total = avg_positive + avg_negative + avg_neutral
    if total > 0:
        avg_positive /= total
        avg_negative /= total
        avg_neutral /= total

    # 테마는 모든 배치에서 합쳐서 중복 제거
    all_themes = []
    all_notable = []
    for r in batch_results:
        all_themes.extend(r.get("key_themes", []))
        for nc in r.get("notable_comments", []):
            if isinstance(nc, dict) and "text" in nc and "sentiment" in nc:
                all_notable.append(nc)

    unique_themes = list(dict.fromkeys(all_themes))[:5]

    # 감정별로 주목할 댓글 선별: 긍정 2개, 부정 2개, 중립 1개
    positive_comments = [c for c in all_notable if c["sentiment"] == "positive"][:2]
    negative_comments = [c for c in all_notable if c["sentiment"] == "negative"][:2]
    neutral_comments = [c for c in all_notable if c["sentiment"] == "neutral"][:1]
    selected_comments = [
        NotableComment(text=c["text"], sentiment=c["sentiment"])
        for c in positive_comments + negative_comments + neutral_comments
    ]

    overall = batch_results[-1].get("overall_sentiment", "분석 완료")

    return SentimentSummary(
        positive_ratio=round(avg_positive, 3),
        negative_ratio=round(avg_negative, 3),
        neutral_ratio=round(avg_neutral, 3),
        key_themes=unique_themes,
        notable_comments=selected_comments,
        overall_sentiment=overall,
        analyzed_count=len(comments),
    )


def _analyze_batch(comments: list[str], channel_name: str) -> dict | None:
    """단일 배치의 댓글을 Gemini로 분석한다."""
    client = _get_client()
    comments_text = "\n".join(f"- {c}" for c in comments)

    prompt = f"""당신은 게임 회사의 YouTube 크리에이터 파트너십 평가를 돕는 AI 분석가입니다.

아래는 YouTube 채널 "{channel_name}"의 최근 영상 댓글 {len(comments)}개입니다.
각 댓글의 감성(긍정/부정/중립)을 분석하고, 전체 요약을 제공해주세요.

댓글 목록:
{comments_text}

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:
{{
  "positive_ratio": 0.0,
  "negative_ratio": 0.0,
  "neutral_ratio": 0.0,
  "key_themes": ["테마1", "테마2", "테마3"],
  "notable_comments": [
    {{"text": "긍정적인 댓글 원문", "sentiment": "positive"}},
    {{"text": "긍정적인 댓글 원문", "sentiment": "positive"}},
    {{"text": "부정적인 댓글 원문", "sentiment": "negative"}},
    {{"text": "부정적인 댓글 원문", "sentiment": "negative"}},
    {{"text": "중립적인 댓글 원문", "sentiment": "neutral"}}
  ],
  "overall_sentiment": "전체 감성을 한 문장으로 요약"
}}

주의사항:
- positive_ratio + negative_ratio + neutral_ratio = 1.0
- key_themes는 3-5개
- notable_comments는 반드시 긍정 2개, 부정 2개, 중립 1개 = 총 5개를 선별
- notable_comments의 text는 위 댓글 목록에서 그대로 인용
- sentiment 값은 반드시 "positive", "negative", "neutral" 중 하나
- 한국어로 작성하세요
"""

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            result = _parse_json_response(response.text or "")
            return result if result else None
        except Exception as e:
            logger.warning(f"Gemini 배치 분석 실패 (시도 {attempt + 1}/{_MAX_RETRIES + 1}): {e}")
            if attempt < _MAX_RETRIES:
                time.sleep(_BACKOFF[attempt])
    return None


def generate_evaluation_summary(
    channel_name: str,
    subscriber_count: int,
    composite_score: float,
    recommendation: str,
    sentiment_summary: str,
    avg_views: float,
    avg_engagement: float,
) -> str:
    """Gemini API로 한국어 평가 요약문을 생성한다."""
    client = _get_client()

    prompt = f"""당신은 게임 회사 슈퍼센트의 파트너 크리에이터 평가 담당자입니다.
아래 데이터를 바탕으로 마케팅 팀에게 보고할 3-4문장의 한국어 평가 요약문을 작성해주세요.

채널명: {channel_name}
구독자 수: {subscriber_count:,}명
종합 점수: {composite_score:.1f}/100
추천 결과: {recommendation}
평균 조회수: {avg_views:,.0f}회
평균 참여율: {avg_engagement:.2f}%
댓글 감성: {sentiment_summary}

요약문만 작성하세요. 마크다운이나 제목은 사용하지 마세요.
파트너십 확대/유지/축소에 대한 의견을 포함해주세요.
"""

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt,
            )
            return (response.text or "").strip() or "평가 요약 생성에 실패했습니다."
        except Exception as e:
            logger.warning(f"Gemini 요약 생성 실패 (시도 {attempt + 1}/{_MAX_RETRIES + 1}): {e}")
            if attempt < _MAX_RETRIES:
                time.sleep(_BACKOFF[attempt])
    return "평가 요약 생성에 실패했습니다."


def _parse_json_response(text: str) -> dict:
    """Gemini 응답에서 JSON을 추출한다."""
    # 먼저 직접 파싱 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 코드 블록에서 JSON 추출
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # { } 블록 추출
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
