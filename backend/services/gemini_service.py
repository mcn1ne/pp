import json
import logging
import os
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from google import genai
from google.genai import types
from backend.config import settings
from backend.schemas.sentiment import SentimentSummary, NotableComment

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_MAX_RETRIES = 2
_BACKOFF = [2, 4]
_VALID_LABELS = {"positive", "negative", "neutral"}


@lru_cache(maxsize=1)
def _get_client():
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=1200_000),
    )


BATCH_SIZE = 100  # 배치당 댓글 수
# 배치 동시 처리 수 (Gemini RPM 한도에 따라 조정). 환경변수로 덮어쓰기 가능.
BATCH_CONCURRENCY = max(1, int(os.environ.get("GEMINI_BATCH_CONCURRENCY", "3")))


def analyze_comments(comments: list[str], channel_name: str) -> SentimentSummary:
    """Gemini API로 댓글 감성분석을 수행한다.

    Stage 1: 배치별로 댓글마다 positive/negative/neutral 라벨만 분류
    Stage 2: Python 으로 라벨 개수 정확 집계 후, 전체 기반 요약 문장을 Gemini 에 1회 요청
    """
    if not comments:
        return SentimentSummary(
            positive_ratio=0, negative_ratio=0, neutral_ratio=0,
            key_themes=[], notable_comments=[], overall_sentiment="데이터 없음",
            analyzed_count=0,
        )

    # Stage 1: 배치 분할 후 병렬 호출
    batches = [comments[i:i + BATCH_SIZE] for i in range(0, len(comments), BATCH_SIZE)]
    workers = min(BATCH_CONCURRENCY, len(batches))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(
            executor.map(lambda b: _analyze_batch(b, channel_name), batches)
        )

    # 실패 배치 제외
    successful = [(r, batch) for r, batch in zip(results, batches) if r is not None]

    if not successful:
        return SentimentSummary(
            positive_ratio=0, negative_ratio=0, neutral_ratio=0,
            key_themes=[], notable_comments=[], overall_sentiment="분석 실패",
            analyzed_count=len(comments),
        )

    # Stage 2: Python 으로 정확 집계
    # 각 배치의 sentiments 배열을 평탄화해 Counter 로 개수 집계
    all_labels: list[str] = []
    all_themes: list[str] = []
    all_notable: list[dict] = []
    for r, batch in successful:
        labels = _normalize_labels(r.get("sentiments", []), len(batch))
        all_labels.extend(labels)
        all_themes.extend(r.get("key_themes", []))
        for nc in r.get("notable_comments", []):
            if isinstance(nc, dict) and "text" in nc and nc.get("sentiment") in _VALID_LABELS:
                all_notable.append(nc)

    counts = Counter(all_labels)
    total = sum(counts.values())
    positive_count = counts.get("positive", 0)
    negative_count = counts.get("negative", 0)
    neutral_count = counts.get("neutral", 0)

    if total == 0:
        # 성공 배치는 있지만 유효 라벨이 없는 이례적 케이스
        return SentimentSummary(
            positive_ratio=0, negative_ratio=0, neutral_ratio=0,
            key_themes=[], notable_comments=[], overall_sentiment="분석 실패",
            analyzed_count=len(comments),
        )

    positive_ratio = positive_count / total
    negative_ratio = negative_count / total
    neutral_ratio = neutral_count / total

    # 테마는 모든 배치에서 합쳐서 중복 제거 후 상위 5개
    unique_themes = list(dict.fromkeys(all_themes))[:5]

    # 감정별로 주목할 댓글 선별: 긍정 2, 부정 2, 중립 1
    positive_comments = [c for c in all_notable if c["sentiment"] == "positive"][:2]
    negative_comments = [c for c in all_notable if c["sentiment"] == "negative"][:2]
    neutral_comments = [c for c in all_notable if c["sentiment"] == "neutral"][:1]
    selected_comments = [
        NotableComment(text=c["text"], sentiment=c["sentiment"])
        for c in positive_comments + negative_comments + neutral_comments
    ]

    # Stage 2: 전체 배치를 묶어 최종 요약 문장 1회 생성
    overall = _generate_overall_sentiment(
        channel_name=channel_name,
        total=total,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
        themes=unique_themes,
        notable=selected_comments,
    )

    return SentimentSummary(
        positive_ratio=round(positive_ratio, 3),
        negative_ratio=round(negative_ratio, 3),
        neutral_ratio=round(neutral_ratio, 3),
        key_themes=unique_themes,
        notable_comments=selected_comments,
        overall_sentiment=overall,
        analyzed_count=len(comments),
    )


def _normalize_labels(raw: list, expected_len: int) -> list[str]:
    """Gemini 가 돌려준 sentiments 배열을 길이·유효값 모두 맞춰서 반환한다.

    - 길이가 짧으면 나머지는 'neutral' 로 채움
    - 길이가 길면 잘라냄
    - 유효 라벨이 아니면 'neutral' 로 보정
    """
    normalized: list[str] = []
    for i in range(expected_len):
        if i < len(raw):
            label = str(raw[i]).strip().lower()
            if label not in _VALID_LABELS:
                label = "neutral"
        else:
            label = "neutral"
        normalized.append(label)
    return normalized


def _analyze_batch(comments: list[str], channel_name: str) -> dict | None:
    """단일 배치의 댓글을 Gemini 로 분류한다 (댓글당 라벨 + 테마 + 주목 댓글 후보)."""
    client = _get_client()
    comments_text = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(comments))

    prompt = f"""당신은 게임 회사의 YouTube 크리에이터 파트너십 평가를 돕는 AI 분석가입니다.

아래는 YouTube 채널 "{channel_name}"의 최근 영상 댓글 {len(comments)}개입니다.
각 댓글의 감성을 정확히 하나씩 분류하고, 주요 테마와 대표 댓글을 뽑아주세요.

댓글 목록(번호 순):
{comments_text}

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운은 포함하지 마세요:
{{
  "sentiments": ["positive", "negative", "neutral", ...],
  "key_themes": ["테마1", "테마2", "테마3"],
  "notable_comments": [
    {{"text": "긍정 댓글 원문", "sentiment": "positive"}},
    {{"text": "긍정 댓글 원문", "sentiment": "positive"}},
    {{"text": "부정 댓글 원문", "sentiment": "negative"}},
    {{"text": "부정 댓글 원문", "sentiment": "negative"}},
    {{"text": "중립 댓글 원문", "sentiment": "neutral"}}
  ]
}}

주의사항:
- sentiments 배열의 길이는 반드시 {len(comments)} 이어야 하고, 위 번호 순서와 동일해야 합니다.
- sentiments 의 각 값은 반드시 "positive", "negative", "neutral" 중 하나입니다.
- key_themes 는 3-5개
- notable_comments 는 긍정 2, 부정 2, 중립 1 = 총 5개 (text 는 위 댓글 원문 그대로 인용)
- 한국어로 작성하세요.
"""

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw_text = response.text or ""
            logger.info(
                f"[Gemini 배치 응답] 댓글 {len(comments)}개 | 시도 {attempt + 1} | "
                f"응답 길이 {len(raw_text)}자\n{raw_text}"
            )
            result = _parse_json_response(raw_text)
            if result:
                return result
            logger.warning(f"Gemini 배치 응답 JSON 파싱 실패 (시도 {attempt + 1}/{_MAX_RETRIES + 1})")
        except Exception as e:
            logger.warning(f"Gemini 배치 분석 실패 (시도 {attempt + 1}/{_MAX_RETRIES + 1}): {e}")
        if attempt < _MAX_RETRIES:
            time.sleep(_BACKOFF[attempt])
    return None


def _generate_overall_sentiment(
    channel_name: str,
    total: int,
    positive_count: int,
    negative_count: int,
    neutral_count: int,
    themes: list[str],
    notable: list[NotableComment],
) -> str:
    """집계된 전체 분류 결과로 두 문장 요약을 생성한다. 실패 시 결정론적 폴백."""
    client = _get_client()

    themes_text = ", ".join(themes) if themes else "없음"
    notable_text = "\n".join(f"- [{c.sentiment}] {c.text}" for c in notable) if notable else "없음"
    positive_pct = positive_count / total * 100
    negative_pct = negative_count / total * 100
    neutral_pct = neutral_count / total * 100

    prompt = f"""아래는 YouTube 채널 "{channel_name}" 댓글 {total}개를 분류한 최종 집계 결과입니다.

집계:
- 긍정: {positive_count}개 ({positive_pct:.1f}%)
- 부정: {negative_count}개 ({negative_pct:.1f}%)
- 중립: {neutral_count}개 ({neutral_pct:.1f}%)

주요 테마: {themes_text}

대표 댓글:
{notable_text}

위 집계를 바탕으로 전체 시청자 반응을 한국어 두 문장으로 요약해주세요.
요약 문장만 출력하고, 다른 부연 설명이나 마크다운은 포함하지 마세요.
"""

    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            raw_text = response.text or ""
            logger.info(
                f"[Gemini 전체 요약 응답] 시도 {attempt + 1} | "
                f"응답 길이 {len(raw_text)}자\n{raw_text}"
            )
            text = raw_text.strip()
            if text:
                return text
            logger.warning(f"Gemini 전체 요약 응답 비어있음 (시도 {attempt + 1}/{_MAX_RETRIES + 1})")
        except Exception as e:
            logger.warning(f"Gemini 전체 요약 생성 실패 (시도 {attempt + 1}/{_MAX_RETRIES + 1}): {e}")
        if attempt < _MAX_RETRIES:
            time.sleep(_BACKOFF[attempt])

    logger.warning("[Gemini 전체 요약] 결정론적 폴백 사용")
    return (
        f"댓글 {total}개 중 긍정 {positive_count}개, 부정 {negative_count}개, "
        f"중립 {neutral_count}개로 분석되었습니다."
    )


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
            raw_text = response.text or ""
            logger.info(
                f"[Gemini 평가 요약 응답] 시도 {attempt + 1} | "
                f"응답 길이 {len(raw_text)}자\n{raw_text}"
            )
            text = raw_text.strip()
            if text:
                return text
            logger.warning(f"Gemini 평가 요약 응답 비어있음 (시도 {attempt + 1}/{_MAX_RETRIES + 1})")
        except Exception as e:
            logger.warning(f"Gemini 요약 생성 실패 (시도 {attempt + 1}/{_MAX_RETRIES + 1}): {e}")
        if attempt < _MAX_RETRIES:
            time.sleep(_BACKOFF[attempt])
    logger.warning("[Gemini 평가 요약] 최종 실패 — 폴백 메시지 반환")
    return "평가 요약 생성에 실패했습니다."


def _parse_json_response(text: str) -> dict:
    """Gemini 응답에서 JSON을 추출한다."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return {}
