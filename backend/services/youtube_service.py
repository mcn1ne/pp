from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from backend.config import settings
from backend.schemas.channel import ChannelInfo
from backend.schemas.video import VideoMetrics, VideoList


def _get_youtube():
    return build("youtube", "v3", developerKey=settings.youtube_api_key)


def get_channel_info(channel_id: str) -> ChannelInfo:
    """채널 기본 정보 및 통계를 가져온다."""
    youtube = _get_youtube()
    response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    items = response.get("items", [])
    if not items:
        raise ValueError(f"채널을 찾을 수 없습니다: {channel_id}")

    item = items[0]
    snippet = item["snippet"]
    stats = item["statistics"]

    return ChannelInfo(
        channel_id=channel_id,
        title=snippet["title"],
        description=snippet.get("description", ""),
        thumbnail_url=snippet["thumbnails"]["high"]["url"],
        custom_url=snippet.get("customUrl"),
        published_at=snippet.get("publishedAt"),
        subscriber_count=int(stats.get("subscriberCount", 0)),
        total_view_count=int(stats.get("viewCount", 0)),
        video_count=int(stats.get("videoCount", 0)),
        country=snippet.get("country"),
    )


def get_recent_videos(channel_id: str, days: int = 30) -> VideoList:
    """채널의 최근 N일 이내 영상 목록과 상세 지표를 가져온다."""
    youtube = _get_youtube()

    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # 1) 기간 내 영상 ID 검색 (페이지네이션, 최대 20페이지)
    video_ids = []
    next_page_token = None
    for _ in range(20):
        search_response = youtube.search().list(
            part="id",
            channelId=channel_id,
            order="date",
            type="video",
            publishedAfter=published_after,
            maxResults=50,
            pageToken=next_page_token,
        ).execute()

        for item in search_response.get("items", []):
            video_ids.append(item["id"]["videoId"])

        next_page_token = search_response.get("nextPageToken")
        if not next_page_token:
            break
    if not video_ids:
        return VideoList(videos=[], avg_views=0, avg_engagement_rate=0, upload_frequency_days=0)

    # 2) 영상 상세 정보 (API 한도 50개씩 청크 처리)
    videos = []
    for chunk_start in range(0, len(video_ids), 50):
        chunk = video_ids[chunk_start:chunk_start + 50]
        videos_response = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(chunk)
        ).execute()
        for item in videos_response.get("items", []):
            snippet = item["snippet"]
            stats = item["statistics"]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            engagement = ((likes + comments) / views * 100) if views > 0 else 0
            videos.append(VideoMetrics(
                video_id=item["id"],
                title=snippet["title"],
                published_at=snippet["publishedAt"],
                view_count=views,
                like_count=likes,
                comment_count=comments,
                thumbnail_url=snippet["thumbnails"]["medium"]["url"],
                engagement_rate=round(engagement, 2),
                description=snippet.get("description", ""),
                tags=snippet.get("tags", []) or [],
            ))

    # 날짜순 정렬 (최신 먼저)
    videos.sort(key=lambda v: v.published_at, reverse=True)

    # 통계 계산
    avg_views = sum(v.view_count for v in videos) / len(videos) if videos else 0
    avg_engagement = sum(v.engagement_rate for v in videos) / len(videos) if videos else 0

    # 업로드 빈도 계산 (일 단위)
    upload_freq = 0.0
    if len(videos) >= 2:
        dates = [v.published_at for v in videos]
        total_days = (max(dates) - min(dates)).days
        upload_freq = total_days / (len(videos) - 1) if total_days > 0 else 0

    return VideoList(
        videos=videos,
        avg_views=round(avg_views, 1),
        avg_engagement_rate=round(avg_engagement, 2),
        upload_frequency_days=round(upload_freq, 1),
    )


def _load_keywords() -> list[str]:
    """관리자가 편집한 DB 키워드를 우선 사용하고, 비었으면 설정 기본값으로 폴백."""
    try:
        from backend.database import get_keywords
        kws = get_keywords()
        if kws:
            return kws
    except Exception:
        pass
    return settings.supercent_keywords


def _matches_keywords(video: VideoMetrics, keywords: list[str]) -> bool:
    haystack = " ".join([
        video.title or "",
        video.description or "",
        " ".join(video.tags or []),
    ]).lower()
    return any(kw in haystack for kw in keywords)


def filter_supercent_videos(videos: list[VideoMetrics]) -> list[VideoMetrics]:
    """슈퍼센트 게임과 관련된 영상만 필터링한다. title + description + tags 를 모두 확인."""
    keywords = [kw.lower() for kw in _load_keywords()]
    return [v for v in videos if _matches_keywords(v, keywords)]


def split_supercent_videos(videos: list[VideoMetrics]) -> tuple[list[VideoMetrics], list[VideoMetrics]]:
    """텍스트 키워드 매칭으로 (관련, 비관련) 두 리스트로 나눈다. 2차 비전 판정용."""
    keywords = [kw.lower() for kw in _load_keywords()]
    matched, unmatched = [], []
    for v in videos:
        (matched if _matches_keywords(v, keywords) else unmatched).append(v)
    return matched, unmatched


def get_video_comments(video_id: str, max_results: int = 20) -> list[str]:
    """영상의 인기 댓글을 가져온다."""
    youtube = _get_youtube()
    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="relevance",
            textFormat="plainText",
            maxResults=max_results
        ).execute()
    except Exception:
        # 댓글이 비활성화된 영상
        return []

    comments = []
    for item in response.get("items", []):
        text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(text)

    return comments


def get_all_video_comments(video_id: str, max_pages: int = 10) -> list[str]:
    """영상의 모든 댓글을 페이지네이션으로 수집한다. (최대 max_pages 페이지)"""
    youtube = _get_youtube()
    comments = []
    next_page_token = None
    page = 0

    while page < max_pages:
        try:
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                order="relevance",
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token,
            ).execute()
        except Exception:
            break

        for item in response.get("items", []):
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        page += 1

    return comments
