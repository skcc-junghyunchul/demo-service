from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models import ResponseBaseModel

class ObjectStorage(BaseModel):
    company_code: str
    object_name: str = Field(None, examples=["DYWT_v1.1_20241120.pdf"], description="다운로드 할 파일명, 확장자 포함")
    local_file_path: str = Field(examples=["/tmp/DYWT_v1.1_20241120.pdf"],description="다운로드 받을 로컬 파일 경로")


class CompanyCodeRequest(BaseModel):
    company_code: str
