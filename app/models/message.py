from pydantic import BaseModel
from typing import Optional

class Message(BaseModel):
    message: str
    conversation_id: str
    company_code: str
    user_id: Optional[str] = ""
    aip_app_id: Optional[str] = ""
    aip_chat_id: Optional[str] = ""
    aip_department: Optional[str] = ""
    aip_transaction_id: Optional[str] = ""