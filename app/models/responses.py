import json
from app.models.rag_result import RagResult
from app.external.ncp_redis_utils import set_conversation, get_conversation, update_conversation, delete_conversation
from app.enums.chit_chat_resource import ChitChatType
from app.api.v1.multi_resource import set_multi_resource, get_multi_resource, update_multi_resource, delete_multi_resource
from app import logger
from app.models.message import Message
import config
from config import multi_tenant_resource

def validate_rag_result(rag_result):
    if isinstance(rag_result, dict):
        return RagResult(**rag_result)
    return rag_result

def generate_common_template(user_question):
    return {
        "entities": [],
        "intent": [],
        "intent_ranking": [],
        "text": user_question,
    }

def generate_response(conversation_id, message, text=None, custom_data=None):
    return {
        "conversation_id": conversation_id,
        "aip_transaction_id": "" if not message.aip_transaction_id else message.aip_transaction_id,
        "text": text,
        "image": None,
        "buttons": None,
        "custom": {"data": custom_data} if custom_data else None,
    }

async def response_generator(conversation_id, user_question, response_type, rag_result=None, similar_index=None, company_code=None, message=None):
    rag_result = validate_rag_result(rag_result)
    template = generate_common_template(user_question)

    try:
        if response_type in ["text", "step"]:
            template["responses"] = [
                generate_response(
                    conversation_id,
                    message,
                    text=f"문의하신 '{rag_result.user_query}'에 대해 안내드리겠습니다.",
                ),
                generate_response(
                    conversation_id,
                    message,
                    custom_data={
                        "answer": rag_result.answer,
                        "answer_type": rag_result.answer_type,
                        "image_paths": rag_result.image_paths or "",
                        "document_path": rag_result.document_path,
                        "doc_page_num": rag_result.doc_page_num,
                        "detail_manual_urls": rag_result.detail_manual_urls or "",
                        "similar_questions": rag_result.similar_questions or "",
                        "expected_questions": rag_result.expected_questions or "",
                        "document_id": rag_result.document_id,
                        "doc_qna_num": rag_result.doc_qna_num,
                        "top_doc_question": rag_result.retrieved_document.get("doc_question", ""),
                        "top_doc_answer": rag_result.retrieved_document.get("doc_answer", ""),
                        "top_doc_reranker_score": rag_result.rag_result.get("reranker_score", ""),
                        "sf_ticket_category_id": rag_result.sf_ticket_category_id,
                        "buttons": [
                            {"title": "해결되지 않았습니다", "payload": "해결되지 않았습니다"},
                            {"title": "해결되었습니다", "payload": "해결되었습니다"},
                        ],
                    },
                ),
            ]

        elif response_type == "unclear":
            template["responses"] = [
                generate_response(
                    conversation_id,
                    message,
                    text="정확한 답변을 드리기 위해 아래에서 문의하신 내용과 가장 적합한 증상을 선택해주세요.",
                ),
                generate_response(
                    conversation_id,
                    message,
                    custom_data={
                        "answer_type": "screen",
                        "similar_questions": rag_result.complex_questions or "",
                        "top_doc_reranker_score": rag_result.rag_result.get("reranker_score", ""),
                        "buttons": [
                            {"title": "여기에 없는 문제에요", "payload": "여기에 없는 문제에요"},
                        ],
                    },
                ),
            ]

        elif response_type == "noanswer":
            template["responses"] = [
                generate_response(
                    conversation_id,
                    message,
                    text="죄송합니다, 등록된 정보에서는 요청에 대한 답변을 제공할 수 없습니다. 다른 질문이 있으시면 도와드리겠습니다.",
                ),
                generate_response(
                    conversation_id,
                    message,
                    custom_data={
                        "answer_type": rag_result.answer_type,
                        "similar_questions": rag_result.similar_questions or "",
                        "top_doc_question": rag_result.retrieved_document.get("doc_question", ""),
                        "top_doc_answer": rag_result.retrieved_document.get("doc_answer", ""),
                        "top_doc_reranker_score": rag_result.rag_result.get("reranker_score", ""),
                        "buttons": [
                            {"title": "IT문의", "payload": "/상담신청완료"},
                            {"title": "에이닷 문의", "payload": "A.Biz 상담"},
                        ],
                    },
                ),
            ]

        else:
            raise ValueError(f"Unsupported response_type: {response_type}")

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        template["responses"] = [
            generate_response(
                conversation_id,
                message,
                text="시스템 오류로 인해 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.",
            )
        ]

    return template
