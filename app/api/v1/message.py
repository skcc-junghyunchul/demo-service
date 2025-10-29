import logging
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
import redis.asyncio as redis
import json
from app.models.message import Message
from app.core.chatbot_scenario import chatbot_scenario
from app.external.ncp_redis_utils import set_conversation, get_conversation, update_conversation, delete_conversation
from app.core.logic import remove_prefix_tag
from app import logger
import uuid

# Configure logger
logging.basicConfig(level=logging.INFO)

# Validation for router prefix
def validate_router_prefix(prefix: str):
    if not prefix.startswith("/v1"):
        raise ValueError("Router prefix must start with '/v1'")

# Validate and set router prefix
router_prefix = "/v1/conversation"
validate_router_prefix(router_prefix)
router = APIRouter(prefix=router_prefix)

# Allowed methods
ALLOWED_METHODS = ["POST"]

def validate_method(method: str):
    if method not in ALLOWED_METHODS:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=f"Method {method} is not allowed")

@router.post("/{api_key}/message")
async def send_message(message: Message):
    try:
        # Validate method
        validate_method("POST")

        # Ensure conversation_id is initialized
        if not message.conversation_id:
            conversation_id = generate_conversation_id()  # Initialize conversation_id
            message.conversation_id = conversation_id

        # Ensure user_id is initialized
        if not message.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

        # Validate message content
        if not message.message or not isinstance(message.message, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message content is invalid or missing")

        # Validate company_code
        if not message.company_code or not isinstance(message.company_code, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="company_code is invalid or missing")

        # Ensure dependencies are correctly injected
        if chatbot_scenario is None:
            raise ConfigurationError("Dependency 'chatbot_scenario' not provided")

        if get_conversation is None or set_conversation is None:
            raise ConfigurationError("Redis utilities are not properly configured")

        conversation_id = message.conversation_id
        user_question = message.message
        company_code = message.company_code
        user_id = message.user_id

        # 질문에서 < > 태그 삭제 전처리
        user_question = remove_prefix_tag(user_question)
        logger.info(f"user_input: {user_question}")

        # 회사코드 + conversation_id + user_id 결합 및 UUID 생성
        unique_id = str(uuid.uuid4())

        # 사용자 식별 로직 추가
        logger.info(f"Identifying user with ID: {user_id}")

        # Run chatbot scenario
        response = await chatbot_scenario(unique_id, company_code, user_id, user_question, message)

        # 첫번째 text 후에는 history가 없음
        conversation = await get_conversation(unique_id)

        # Conversation이 있으면
        if conversation:
            history = conversation["history"]
            state = conversation["state"]

            # 기존 history가 리스트가 아니면 리스트로 변환
            if not isinstance(history, list):
                history = [history] if history else []

            # 여기서는 질문과, 답변을 history에 append함
            history.append({"user": user_question, "agent": response})

            # 업데이트
            set_conversation(unique_id, state=state, history=history)

        # Convert response to JSON serializable format
        response = json.dumps(response, default=str)

        return response

    except Exception as e:
        logger.exception(e, extra={"tenant": company_code})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))