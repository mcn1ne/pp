"""2차 필터 — 썸네일 이미지 + 메타를 Gemini Vision 에 넘겨 슈퍼센트 관련성을 판정한다."""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

from google import genai
from google.genai import types

from backend.config import settings
from backend.schemas.video import VideoMetrics

_VISION_MODEL = "gemini-2.5-flash"
_THUMB_TIMEOUT = 5.0
_BATCH_CONCURRENCY = max(1, int(os.environ.get("GEMINI_BATCH_CONCURRENCY", "3")))


def _get_client():
    return genai.Client(api_key=settings.gemini_api_key)


def _fetch_thumbnail(url: str) -> bytes | None:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=_THUMB_TIMEOUT) as resp:
            return resp.read()
    except Exception:
        return None


def _classify_one(video: VideoMetrics) -> bool:
    """단일 영상을 슈퍼센트 관련성 기준으로 분류. 실패/타임아웃은 False."""
    img_bytes = _fetch_thumbnail(video.thumbnail_url)
    if not img_bytes:
        return False

    client = _get_client()
    description = (video.description or "")[:500]
    prompt = (
        f"영상 제목: {video.title}\n"
        f"설명: {description}\n\n"
        "첨부된 이미지는 이 YouTube 영상의 썸네일입니다. "
        "이 영상이 슈퍼센트(Supercent) 의 모바일 게임 "
        "(예: Woodoku, Burger Please, Going Balls, Triple Match, Cooking Sort, Ore Blitz, Make It Perfect 등) "
        "의 플레이·리뷰·홍보 영상인지 판단하세요.\n"
        "반드시 아래 JSON 한 줄로만 응답하세요:\n"
        '{"is_supercent": true}  또는  {"is_supercent": false}'
    )

    try:
        response = client.models.generate_content(
            model=_VISION_MODEL,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                prompt,
            ],
        )
    except Exception:
        return False

    return _parse_is_supercent(response.text)


def _parse_is_supercent(text: str | None) -> bool:
    if not text:
        return False
    # JSON 우선
    try:
        data = json.loads(text)
        return bool(data.get("is_supercent"))
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\{[\s\S]*?\}", text)
    if match:
        try:
            data = json.loads(match.group(0))
            return bool(data.get("is_supercent"))
        except json.JSONDecodeError:
            pass
    # 최후 폴백 — 키워드 직관 매칭
    lowered = text.lower()
    if '"is_supercent": true' in lowered or "is_supercent: true" in lowered:
        return True
    return False


def classify_by_thumbnail(videos: list[VideoMetrics]) -> list[VideoMetrics]:
    """썸네일 기반으로 슈퍼센트 관련 판정. 관련 있다고 분류된 영상만 반환한다."""
    if not videos:
        return []
    workers = min(_BATCH_CONCURRENCY, len(videos))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        verdicts = list(executor.map(_classify_one, videos))
    return [v for v, keep in zip(videos, verdicts) if keep]
