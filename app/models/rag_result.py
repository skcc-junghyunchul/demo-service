from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


    
class RagResult(BaseModel):
    
    status_code: int
    message: str
    user_query: str
    answer: str
    answer_type: str
    document_path: str
    document_id: Optional [str] = None
    doc_page_num: int
    doc_qna_num: int
    image_paths: list
    detail_manual_urls: list
    similar_questions: list
    expected_questions: list
    complex_questions: list
    retrieved_document: dict
    sf_ticket_category_id: Optional [str] = None
    sf_request_name: Optional [str] = None
    rag_result: dict
