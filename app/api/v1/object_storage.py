import os
from fastapi import FastAPI, APIRouter, HTTPException, Request, status, Response
from typing import Optional
from fastapi.responses import FileResponse
from app import logger
from app.models.blob import Blob, DownloadFile
from app.models.object_storage import ObjectStorage, CompanyCodeRequest
from app.external.object_storage import download_object_to_stream, create_bucket, delete_bucket, upload_file
from app.enums.storage_resource import StorageType
import asyncio

def validate_service_name(service_name: str) -> bool:
    # Example validation logic
    return service_name in ["service1", "service2", "service3"]

router = APIRouter(prefix="/api/v1")

async def retry_operation(operation, retries=3, delay=2, *args, **kwargs):
    for attempt in range(retries):
        try:
            return await operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise

@router.post("/file/download")
async def get_file(object_storage: ObjectStorage):
    try:
        company_code = object_storage.company_code
        object_name = object_storage.object_name
        local_file_path = object_storage.local_file_path
        service_name = object_storage.service_name  # Assuming service_name is part of ObjectStorage

        # Validate service_name
        if not validate_service_name(service_name):
            raise ValueError("Invalid service_name")

        # Implement retry logic for stream operations
        file_stream, mime_type = await retry_operation(
            download_object_to_stream, 
            retries=3, 
            delay=2, 
            company_code=company_code, 
            object_name=object_name, 
            local_file_path=local_file_path
        )
        
        return Response(
            content=file_stream,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={object_name}"}
        )
    except Exception as e:
        logger.exception(e, extra={"tenant": company_code})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/file/bucket")
async def make_bucket(company_code: CompanyCodeRequest):
    try:
        company_code = company_code.company_code
        
        await create_bucket(company_code)
        
        return f"{company_code}의 bucket이 생성되었습니다."
    
    except Exception as e:
        logger.exception(e, extra={"tenant": company_code})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/file/bucket")
async def remove_bucket(company_code: CompanyCodeRequest):
    try:
        company_code = company_code.company_code
        
        await delete_bucket(company_code)
        
        return f"{company_code}의 bucket이 삭제되었습니다."
    
    except Exception as e:
        logger.exception(e, extra={"tenant": company_code})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/file/upload")
async def uploadfile(object_storage: ObjectStorage):
    try:
        company_code = object_storage.company_code
        object_name = object_storage.object_name
        local_file_path = object_storage.local_file_path
        service_name = object_storage.service_name  # Assuming service_name is part of ObjectStorage

        # Validate service_name
        if not validate_service_name(service_name):
            raise ValueError("Invalid service_name")
        
        await upload_file(company_code, object_name, local_file_path)
        
        return f"{company_code}의 bucket에 {object_name} 파일의 업로드가 성공하였습니다."
    
    except Exception as e:
        logger.exception(e, extra={"tenant": company_code})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))