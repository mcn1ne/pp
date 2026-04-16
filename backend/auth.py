import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

_REALM = "Supercent Admin Console"
security = HTTPBasic(realm=_REALM)


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Basic Auth 기반 관리자 인증. 환경변수로 자격증명을 주입받는다."""
    expected_user = os.environ.get("ADMIN_USERNAME", "admin")
    expected_pass = os.environ.get("ADMIN_PASSWORD", "supercent")

    user_ok = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        expected_user.encode("utf-8"),
    )
    pass_ok = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        expected_pass.encode("utf-8"),
    )
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증에 실패했습니다.",
            headers={"WWW-Authenticate": f'Basic realm="{_REALM}"'},
        )
    return credentials.username
