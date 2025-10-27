from app.core.logic import get_slot_by_rag
from app.core.logic import parse_user_id
from app.models.responses import response_generator
from app.external.ncp_redis_utils import set_conversation, get_conversation, update_conversation, delete_conversation
from app.external.openai_platform import query_openai
from app.core.chat_history_parser import chat_history_parser
from app.enums.llm_resource import LLMType
from app.models.message import Message
import json
import time
import config
from config import multi_tenant_resource
from app import logger

import re

WELCOME_MESSAGE_PREFIX = "/welcome"

def validate_input(conversation_id, company_code, user_id, user_question):
    if not isinstance(conversation_id, str) or not conversation_id.strip():
        raise ValueError("Invalid conversation_id: must be a non-empty string.")
    if not isinstance(company_code, str) or not company_code.strip():
        raise ValueError("Invalid company_code: must be a non-empty string.")
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("Invalid user_id: must be a non-empty string.")
    if not isinstance(user_question, str) or not user_question.strip():
        raise ValueError("Invalid user_question: must be a non-empty string.")
    if user_question.startswith(WELCOME_MESSAGE_PREFIX):
        if not re.match(r"^/welcome\s+\w+$", user_question):
            raise ValueError("Invalid user_question format for welcome message.")

def parse_response(response):
    try:
        parsed_response = json.loads(response)
        if not isinstance(parsed_response, dict):
            raise ValueError("Parsed response is not a dictionary.")
        return parsed_response
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse response: {e}")
        return {"error": "Invalid response format."}

async def chatbot_scenario(conversation_id, company_code, user_id, user_question, message: Message):
    # Validate inputs
    try:
        validate_input(conversation_id, company_code, user_id, user_question)
    except ValueError as e:
        logger.error(f"Input validation error: {e}")
        return {"error": str(e)}

    messages = []

    active_conversations = get_conversation(conversation_id)

    if active_conversations:
        state = active_conversations['state']
    else:
        state = None

    # 해결여부 확인 분기 처리
    if state == "resolution_yes_no":
        if user_question == "해결되었습니다":
            response = await response_generator(conversation_id, user_question, "대화종료", message=message)
            parsed_response = parse_response(response)
            update_conversation(conversation_id, "finished")
            return parsed_response
        elif user_question == "해결되지 않았습니다":
            update_conversation(conversation_id, "awaiting_resolution")
            response = await response_generator(conversation_id, user_question, "재탐색/상담요청 여부", message=message)
            parsed_response = parse_response(response)
            return parsed_response
        else:
            update_conversation(conversation_id, "continuing")
            response = await response_generator(conversation_id, user_question, "상태 지속", message=message)
            parsed_response = parse_response(response)
            return parsed_response

    # 기타 상태 처리
    if state == "awaiting_resolution":
        response = await response_generator(conversation_id, user_question, "상담 진행 중", message=message)
        parsed_response = parse_response(response)
        update_conversation(conversation_id, "in_progress")
        return parsed_response

    if state == "finished":
        return {"message": "Conversation has already been finished."}

    # 기본 상태 처리
    response = await response_generator(conversation_id, user_question, "기본 상태", message=message)
    parsed_response = parse_response(response)
    update_conversation(conversation_id, "default")
    return parsed_response
