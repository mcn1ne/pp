from pydantic import BaseModel
from datetime import datetime


class VideoMetrics(BaseModel):
    video_id: str
    title: str
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    thumbnail_url: str
    engagement_rate: float  # (likes + comments) / views * 100


class VideoList(BaseModel):
    videos: list[VideoMetrics]
    avg_views: float
    avg_engagement_rate: float
    upload_frequency_days: float  # avg days between uploads
