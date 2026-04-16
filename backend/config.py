from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    youtube_api_key: str = ""
    gemini_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    min_subscriber_count: int = 500
    pass_score_threshold: float = 60.0

    # 2차 Gemini Vision 필터 (썸네일 기반 관련성 분류). 기본 OFF — 비용/지연 절감.
    sc_vision_filter_enabled: bool = False

    # 슈퍼센트 게임 키워드 (영상 필터링에 사용)
    supercent_keywords: list[str] = [
        "supercent", "슈퍼센트",
        # 대표 게임 타이틀
        "woodoku", "우도쿠",
        "burger please", "버거 플리즈",
        "going balls", "고잉볼즈",
        "triple match", "트리플매치",
        "make it perfect", "메이크잇퍼펙트",
        "cooking sort", "쿠킹소트",
        "ore blitz", "오어블리츠",
        "idle breakout", "아이들 브레이크아웃",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
