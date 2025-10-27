from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
import redis.asyncio as redis
import json
from app.models.message import Message
from app.core.chatbot_scenario import chatbot_scenario
from app.external.ncp_redis_utils import set_conversation, get_conversation, update_conversation, delete_conversation
from app.core.logic import remove_prefix_tag
from app import logger

# Validation for router prefix
def validate_router_prefix(prefix: str):
    if not prefix.startswith("/v1"):
        raise ValueError("Router prefix must start with '/v1'")

# Validate and set router prefix
router_prefix = "/v1/conversation"
validate_router_prefix(router_prefix)
router = APIRouter(prefix=router_prefix)


@router.post("/{api_key}/message")
async def send_message(message: Message):
    try:
        # Ensure conversation_id is initialized
        if not message.conversation_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="conversation_id is required")

        # Ensure user_id is initialized
        if not message.user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

        conversation_id = message.conversation_id
        user_question = message.message
        company_code = message.company_code
        user_id = message.user_id

        # 질문에서 < > 태그 삭제 전처리
        user_question = remove_prefix_tag(user_question)
        logger.info(f"user_input: {user_question}")

        # 회사코드 + conversation_id 결합
        unique_id = f"{company_code}_{conversation_id}"

        # 사용자 식별 로직 추가
        logger.info(f"Identifying user with ID: {user_id}")

        # Run chatbot scenario
        response = await chatbot_scenario(unique_id, company_code, user_id, user_question, message)

        # 첫번째 text 후에는 history가 없음
        conversation = get_conversation(unique_id)

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

        return response

    except Exception as e:
        logger.exception(e, extra={"tenant": company_code})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))