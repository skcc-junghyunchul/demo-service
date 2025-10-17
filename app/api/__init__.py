from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.message import router as message
from app.api.v1.multi_resource import router as multi_resource
from app.api.v1.object_storage import router as object_storage
from app.exception import (CustomException, custom_exception_handler,
                            validation_exception_handler, http_exception_handler)

from config import initialize_multi_tenant_resource  # 🔹 config에서 import

app = FastAPI()

# ✅ 리소스 초기화: 앱 시작 시 한 번만 실행됨
@app.on_event("startup")
async def startup_event():
    initialize_multi_tenant_resource()

# 라우터 등록
app.include_router(message)
app.include_router(multi_resource)
app.include_router(object_storage)

# 예외 핸들러 등록
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
