import json
import redis
import config as config



# NCP_REDIS_HOST = config.NCP_REDIS_HOST
# NCP_REDIS_PORT = config.NCP_REDIS_PORT
# NCP_REDIS_DB = config.NCP_REDIS_DB
    
# Redis 클라이언트 초기화
# redis_client: redis.Redis = redis.Redis(
#     host=NCP_REDIS_HOST,
#     port=NCP_REDIS_PORT,
#     db=NCP_REDIS_DB,
#     decode_responses=True # 추가
# )

def get_redis_client(db: int) -> redis.Redis:
    return redis.Redis(
        host=config.NCP_REDIS_HOST,
        port=config.NCP_REDIS_PORT,
        db=db,
        decode_responses=True
    )
