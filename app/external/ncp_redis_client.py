import json
import redis
import config as config

def validate_redis_data(data):
    """
    Validate the Redis data format.
    Returns True if valid, raises ValueError otherwise.
    """
    if not isinstance(data, dict):
        raise ValueError("Redis data must be a dictionary.")
    return True

def save_to_redis(client: redis.Redis, key: str, data: dict):
    """
    Save validated data to Redis.
    """
    try:
        validate_redis_data(data)
        client.set(key, json.dumps(data))
    except ValueError as e:
        print(f"Error saving data to Redis: {e}")
        raise

def get_redis_client(db: int) -> redis.Redis:
    return redis.Redis(
        host=config.NCP_REDIS_HOST,
        port=config.NCP_REDIS_PORT,
        db=db,
        decode_responses=True
    )
