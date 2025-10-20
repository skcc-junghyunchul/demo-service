import json
import redis
from app import logger
import config as config
from app.external.ncp_redis_client import get_redis_client

NCP_REDIS_DB_CHATHISTORY = config.NCP_REDIS_DB_CHATHISTORY

def set_conversation(conversation_id: str, state: str = "", history: dict | None = None) -> None:
    """ 대화 상태를 Redis에 저장 (예외 처리 추가) """
    history = history or {}
    try:
        get_redis_client(NCP_REDIS_DB_CHATHISTORY, timeout=config.DB_TIMEOUT).hset(conversation_id, mapping={"state": state, "history": json.dumps(history)})
        get_redis_client(NCP_REDIS_DB_CHATHISTORY, timeout=config.DB_TIMEOUT).expire(conversation_id, 1800)  # 30분 후 만료
    except redis.RedisError as e:
        logger.exception(f"Redis 저장 중 오류 발생: {e}")


def get_conversation(conversation_id: str) -> dict | None:
    """ 대화 상태를 Redis에서 가져옴 (예외 처리 추가) """
    try:
        data = get_redis_client(NCP_REDIS_DB_CHATHISTORY, timeout=config.DB_TIMEOUT).hgetall(conversation_id)
        if not data:
            return None

        try:
            history = json.loads(data.get("history", "{}"))
        except json.JSONDecodeError:
            history = {}

        return {"state": data.get("state", ""), "history": history}
    except redis.RedisError as e:
        logger.exception(f"Redis 조회 중 오류 발생: {e}")
        return None


def update_conversation(
    conversation_id: str | None = None, 
    state: str | None = None, 
    history: list | None = None, 
    user_id: str | None = None
) -> None:
    """ 대화 상태를 업데이트 (append 방식 적용) """
    if not conversation_id:
        logger.exception("Error: conversation_id가 제공되지 않았습니다.")
        return

    try:
        data = get_conversation(conversation_id) or {"state": "", "history": []}

        if state is not None:
            data["state"] = state

        # history가 리스트인 경우 append 방식으로 추가
        if history:
            if not isinstance(data["history"], list):
                data["history"] = []
            data["history"].extend(history)

        set_conversation(conversation_id, state=data["state"], history=data["history"])
    
    except redis.RedisError as e:
        logger.exception(f"Redis 업데이트 중 오류 발생: {e}")


def delete_conversation(conversation_id: str) -> None:
    """ 대화 상태를 삭제 """
    if not conversation_id:
        logger.exception("Error: conversation_id가 제공되지 않았습니다.")
        return

    try:
        get_redis_client(NCP_REDIS_DB_CHATHISTORY, timeout=config.DB_TIMEOUT).delete(conversation_id)
    except redis.RedisError as e:
        logger.exception(f"Redis 삭제 중 오류 발생: {e}")