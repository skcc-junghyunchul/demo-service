from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class ChatHistory(BaseModel):
    role: str
    content: Optional[str] = None
    answer_type: Optional[str] = None
    
class Rag(BaseModel):
    user_question: str
    category: Optional[str] = Field(default=None, examples=["VDI"], description="중분류명")
    is_clear: Optional[bool] = Field(default=None, examples=[True], description="의도가 명확한 질문인 경우 True, 의도가 불명확한 질문인 경우 False")
    chat_history: Optional[List[ChatHistory]] = None
    
'''
    body = {
        "user_question": "",
        "category": "",
        "is_clear": "",
        "chat_history": ""
    }
'''