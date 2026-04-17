import re
from urllib.parse import unquote
from googleapiclient.discovery import build
from backend.config import settings


def resolve_channel_id(url_or_input: str) -> dict:
    """YouTube URL 또는 핸들을 채널 ID로 변환한다."""
    url = url_or_input.strip()

    # 이미 채널 ID인 경우 (UC로 시작하는 24자)
    if re.match(r"^UC[\w-]{22}$", url):
        return {"channel_id": url, "method": "direct_id"}

    # /channel/UCxxxx 형식
    match = re.search(r"youtube\.com/channel/(UC[\w-]{22})", url)
    if match:
        return {"channel_id": match.group(1), "method": "url_channel"}

    # /@handle 형식
    match = re.search(r"youtube\.com/@([\w.-]+)", url)
    if match:
        handle = unquote(match.group(1))
        return _resolve_by_handle(handle)

    # @handle만 입력한 경우
    if url.startswith("@"):
        return _resolve_by_handle(unquote(url[1:]))

    # /c/customname 또는 /user/username 형식
    match = re.search(r"youtube\.com/(?:c|user)/([\w.-]+)", url)
    if match:
        return _resolve_by_search(match.group(1))

    # 그 외 - 검색으로 시도
    return _resolve_by_search(url)


def _resolve_by_handle(handle: str) -> dict:
    """@handle로 채널 ID를 찾는다."""
    handle = unquote(handle)
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
    response = youtube.channels().list(
        part="id",
        forHandle=handle
    ).execute()

    items = response.get("items", [])
    if not items:
        raise ValueError(f"채널을 찾을 수 없습니다: @{handle}")
    return {"channel_id": items[0]["id"], "method": "handle"}


def _resolve_by_search(query: str) -> dict:
    """검색으로 채널 ID를 찾는다."""
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
    response = youtube.search().list(
        part="snippet",
        q=query,
        type="channel",
        maxResults=1
    ).execute()

    items = response.get("items", [])
    if not items:
        raise ValueError(f"채널을 찾을 수 없습니다: {query}")
    return {"channel_id": items[0]["snippet"]["channelId"], "method": "search"}
