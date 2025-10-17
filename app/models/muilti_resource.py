from pydantic import BaseModel
from typing import List, Optional


class MultiResourceModel(BaseModel):
    resource_name: str
    resource_value: dict