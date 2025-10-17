import os
import json
from fastapi import FastAPI, APIRouter, HTTPException, Request, status, Response
from typing import Optional
from app import logger
from app.models.muilti_resource import MultiResourceModel
import redis
from app.external.ncp_redis_client import get_redis_client
import config as config

NCP_REDIS_DB_MULTI_RESOURCE = config.NCP_REDIS_DB_MULTI_RESOURCE

router = APIRouter(prefix="/v1/multi_resource")


# Redis에 MultiResource 초기화 API
@router.post("/init_resources")
def init_multi_resources():
    for key, value in COMPANY_ENDPOINTS.items():
        if value:
            get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).setnx(key, value)
    return {"message": "Resources initialized in Redis"}


# MultiResource 저장 API
@router.post("/set_endpoint")
def set_multi_resource(data: MultiResourceModel):
    try:
        get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).set(
            data.resource_name,
            json.dumps(data.resource_value, ensure_ascii=False)
        )
        return {"message": "Endpoint saved"}
    except redis.RedisError as e:
        logger.exception(f"Redis 저장 중 오류 발생: {e}")


# MultiResource 불러오기 API
@router.get("/get_endpoint/{resource_name}")
def get_multi_resource(resource_name: str):
    try:
        resource_value = get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).get(resource_name)
        if resource_value is None:
            # raise HTTPException(status_code=404, detail="Resource not found")
            logger.info(f"Redis에 {resource_name} 자원이 없습니다.")

        return {"resource_name": resource_name, "resource_value": resource_value}
    except redis.RedisError as e:
        logger.exception(f"Redis 조회 중 오류 발생: {e}")

# MultiResource 업데이트 API
@router.put("/update_endpoint")
def update_multi_resource(data: MultiResourceModel):
    try:
        if not get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).exists(data.resource_name):
            raise HTTPException(status_code=404, detail="Resource not found")
        get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).set(
            data.resource_name,
            json.dumps(data.resource_value, ensure_ascii=False)
        )
        return {"message": "Resource updated"}
    except redis.RedisError as e:
        logger.exception(f"Redis 업데이트 중 오류 발생: {e}")

# MultiResource API
@router.delete("/delete_endpoint/{resource_name}")
def delete_multi_resource(resource_name: str):
    try:
        if not get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).exists(resource_name):
            raise HTTPException(status_code=404, detail="Resource not found")
        get_redis_client(NCP_REDIS_DB_MULTI_RESOURCE).delete(resource_name)
        return {"message": "Resource deleted"}
    except redis.RedisError as e:
        logger.exception(f"Redis 삭제 중 오류 발생: {e}")