from typing import Any, Optional

from fastapi import HTTPException


class BaseAPIException(HTTPException):
    def __init__(
        self,
        status_code,
        detail: Any = None,
        error_code: Optional[str] = None,
        extra: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}
