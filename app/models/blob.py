from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models import ResponseBaseModel

class Blob(BaseModel):
    blob_name: str

class DownloadFile(ResponseBaseModel):
    content: Any
    media_type: str
    headers: Dict = None