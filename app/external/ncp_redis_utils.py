import json
import redis
from app import logger
import config as config
from app.external.ncp_redis_client import get_redis_client

NCP_REDIS_DB_CHATHISTORY = config.NCP_REDIS_DB_CHATHISTORY

def verify_redis_connection(redis_client):
    """Redis 연결 확인 및 매개변수 검증"""
    try:
        # Redis 연결 매개변수 검증
        if not redis_client.connection_pool.connection_kwargs.get("host"):
            raise ValueError("Redis 호스트가 설정되지 않았습니다.")
        if not redis_client.connection_pool.connection_kwargs.get("port"):
            raise ValueError("Redis 포트가 설정되지 않았습니다.")
        
        redis_client.ping()
        return True
    except (redis.RedisError, ValueError) as e:
        logger.exception(f"Redis 연결 확인 중 오류 발생: {e}")
        return False

def set_conversation(conversation_id: str, state: str = "", history: dict | None = None) -> None:
    """ 대화 상태를 Redis에 저장 (예외 처리 추가 및 데이터 검증) """
    history = history or {}
    try:
        # 데이터 직렬화 전에 검증
        if not isinstance(history, dict):
            raise ValueError("History는 dict 형식이어야 합니다.")
        serialized_history = json.dumps(history)

        redis_client = get_redis_client(NCP_REDIS_DB_CHATHISTORY, timeout=config.DB_TIMEOUT)
        if not verify_redis_connection(redis_client):
            raise redis.RedisError("Redis 연결 실패")

        # Redis 메모리 설정 추가
        redis_client.config_set("maxmemory", "512mb")
        redis_client.config_set("maxmemory-policy", "allkeys-lru")

        # 고유 키 생성
        unique_key = f"conversation:{conversation_id}"

        # 파이프라인 사용
        with redis_client.pipeline() as pipe:
            pipe.set(unique_key, json.dumps({"state": state, "history": serialized_history}))
            pipe.expire(unique_key, 1800)  # 30분 후 만료
            pipe.execute()
    except (redis.RedisError, ValueError) as e:
        logger.exception(f"Redis 저장 중 오류 발생: {e}")

def update_conversation(
    conversation_id: str | None = None, 
    state: str | None = None, 
    history: list | None = None, 
    user_id: str | None = None
) -> None:
    """ 대화 상태를 업데이트 (append 방식 적용 및 데이터 검증 추가) """
    if not conversation_id:
        logger.exception("Error: conversation_id가 제공되지 않았습니다.")
        return

    retry_count = 3

    for attempt in range(retry_count):
        try:
            redis_client = get_redis_client(NCP_REDIS_DB_CHATHISTORY, timeout=config.DB_TIMEOUT)
            if not verify_redis_connection(redis_client):
                raise redis.RedisError("Redis 연결 실패")

            unique_key = f"conversation:{conversation_id}"
            
            # 키 존재 여부 확인
            if redis_client.exists(unique_key):
                data = redis_client.get(unique_key)
                if data:
                    data = json.loads(data)
                else:
                    data = {"state": "", "history": []}

                if state is not None:
                    data["state"] = state

                # history가 리스트인지 확인하고 append 방식으로 추가
                if history:
                    if not isinstance(history, list):
                        raise ValueError("History는 list 형식이어야 합니다.")
                    if not isinstance(data["history"], list):
                        data["history"] = []
                    data["history"].extend(history)

                set_conversation(conversation_id, state=data["state"], history=data["history"])
            else:
                logger.warning(f"키 {unique_key}가 Redis에 존재하지 않습니다.")
            break
        except (redis.RedisError, ValueError) as e:
            logger.exception(f"Redis 업데이트 중 오류 발생: {e}")
            if attempt < retry_count - 1:
                logger.info(f"재시도 중... ({attempt + 1}/{retry_count})")
            else:
                logger.error("최대 재시도 횟수 초과")