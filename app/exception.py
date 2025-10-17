from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
# from app import logger
from app.models import ResponseBaseModel


class CustomException(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Server Error"

    def __init__(self, *args: object, **kwargs):
        super().__init__(*args)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
        content=ResponseBaseModel(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=str(exc)).model_dump(exclude_defaults=True),
    )


async def custom_exception_handler(_: Request, e: CustomException):
    return JSONResponse(
        status_code=e.status_code, 
        content=ResponseBaseModel(status_code=e.status_code, message=str(e)).model_dump(exclude_defaults=True)
    )


async def http_exception_handler(_: Request, e: HTTPException):
    return JSONResponse(
        status_code=e.status_code,
        content=ResponseBaseModel(status_code=e.status_code, message=e.detail).model_dump(exclude_defaults=True)
    )


class AzureSearchError(CustomException):
    ...


class BlobError(CustomException):
    ...


class NoFileError(CustomException):
    ...


class ChatRoleError(CustomException):
    ...


class FileTypeError(CustomException):
    ...


class AzureSearchTypeError(CustomException):
    ...


class QATagFormatError(CustomException):
    ...


class SendTypeError(CustomException):
    ...


class AdminBackendCallFailed(CustomException):
    ...


class ContentFilteringError(CustomException):
    ...


class CustomInputValueError(CustomException):
    ...