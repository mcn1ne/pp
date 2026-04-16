from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.channel_resolver import resolve_channel_id
from backend.services.youtube_service import get_channel_info

router = APIRouter(prefix="/channel", tags=["channel"])


class ResolveRequest(BaseModel):
    url: str


class ResolveResponse(BaseModel):
    channel_id: str
    method: str


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_channel(request: ResolveRequest):
    """YouTube URL/핸들을 채널 ID로 변환한다."""
    try:
        result = resolve_channel_id(request.url)
        return ResolveResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채널 ID 변환 실패: {str(e)}")


@router.get("/{channel_id}")
async def get_channel(channel_id: str):
    """채널 기본 정보를 조회한다."""
    try:
        return get_channel_info(channel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채널 정보 조회 실패: {str(e)}")
