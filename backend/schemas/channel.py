from pydantic import BaseModel
from datetime import datetime


class ChannelInfo(BaseModel):
    channel_id: str
    title: str
    description: str
    thumbnail_url: str
    custom_url: str | None = None
    published_at: datetime | None = None
    subscriber_count: int
    total_view_count: int
    video_count: int
    country: str | None = None
