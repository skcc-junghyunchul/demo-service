from typing import Any, Optional
from pydantic import BaseModel, Field


class ResponseBaseModel(BaseModel):
    status_code: Optional[int] = Field(default=None, description="status_code값입니다.")
    message: Optional[str] = Field(default=None, examples=["처리가 완료되었습니다."], description="시스템용 메시지입니다.")
    # outputs: Optional[Any] = None
