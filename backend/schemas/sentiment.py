from pydantic import BaseModel


class NotableComment(BaseModel):
    text: str
    sentiment: str  # "positive", "negative", "neutral"


class SentimentSummary(BaseModel):
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    key_themes: list[str]
    notable_comments: list[NotableComment]
    overall_sentiment: str
    analyzed_count: int
