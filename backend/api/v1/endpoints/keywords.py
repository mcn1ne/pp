from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import require_admin
from backend.database import list_keywords, add_keyword, delete_keyword

router = APIRouter(
    prefix="/keywords",
    tags=["keywords"],
    dependencies=[Depends(require_admin)],
)


class KeywordCreateRequest(BaseModel):
    keyword: str


@router.get("")
async def get_keywords_list():
    """등록된 슈퍼센트 필터 키워드 전체를 반환한다."""
    return list_keywords()


@router.post("")
async def create_keyword(request: KeywordCreateRequest):
    """키워드를 추가한다."""
    try:
        return add_keyword(request.keyword)
    except ValueError as e:
        # 빈 값이면 400, 중복이면 409
        msg = str(e)
        code = 409 if "이미" in msg else 400
        raise HTTPException(status_code=code, detail=msg)


@router.delete("/{keyword_id}")
async def remove_keyword(keyword_id: int):
    """키워드를 삭제한다."""
    if not delete_keyword(keyword_id):
        raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
    return {"status": "deleted"}
