import aiohttp
import re
from app.external.rag import call_rag_api
from app.models.rag import Rag
from app import logger
from app.models.message import Message
import subprocess

# Check aiohttp version and update if necessary
def check_and_update_aiohttp():
    try:
        import pkg_resources
        current_version = pkg_resources.get_distribution("aiohttp").version
        print(f"Current aiohttp version: {current_version}")
        
        # Update aiohttp to the latest version
        subprocess.run(["pip", "install", "--upgrade", "aiohttp"], check=True)
        print("aiohttp has been updated to the latest version.")
    except Exception as e:
        logger.exception(e)
        print(f"Failed to check or update aiohttp: {e}")

check_and_update_aiohttp()

def validate_rag_params(params):
    required_keys = ["user_question", "aip_app_id", "aip_chat_id", "aip_department", "aip_user", "aip_transaction_id"]
    for key in required_keys:
        if key not in params or not params[key]:
            return False
    return True

async def get_slot_by_rag(user_question, category, is_clear, chat_history=None, company_code=None, user_id=None, message:Message=None):
    # Validate input data
    if not user_question or not isinstance(user_question, str):
        return {"error": "Invalid user_question provided."}
    if category is not None and not isinstance(category, str):
        return {"error": "Invalid category provided."}
    if is_clear is not None and not isinstance(is_clear, bool):
        return {"error": "Invalid is_clear value provided."}
    if not isinstance(message, Message):
        return {"error": "Invalid message object provided."}
    if company_code is not None and not isinstance(company_code, str):
        return {"error": "Invalid company_code provided."}

    # Ensure all required AIP fields are initialized
    message.aip_app_id = message.aip_app_id or "default_app_id"
    message.aip_chat_id = message.aip_chat_id or "default_chat_id"
    message.aip_department = message.aip_department or "default_department"
    message.user_id = message.user_id or "default_user_id"
    message.aip_transaction_id = message.aip_transaction_id or "default_transaction_id"

    # Construct the RAG body
    body = {
        "user_question": user_question,
        "chat_history": chat_history,
        "aip_app_id": message.aip_app_id,
        "aip_chat_id": message.aip_chat_id,
        "aip_company": company_code,
        "aip_department": message.aip_department,
        "aip_user": message.user_id,
        "aip_transaction_id": message.aip_transaction_id 
    }
    
    if category is not None:
        body["category"] = category
    
    if is_clear is not None:
        body["is_clear"] = is_clear

    # Validate RAG body parameters before construction
    if not all([body.get("user_question"), body.get("aip_app_id"), body.get("aip_chat_id"), body.get("aip_department"), body.get("aip_user"), body.get("aip_transaction_id")]):
        raise MissingParameterError("One or more required parameters are missing.")

    try:
        results = await call_rag_api(query_params={}, body=body)
        
        # Handle edge cases for RAG results
        if results is None:
            raise ValueError("RAG results cannot be None")
        if not isinstance(results, dict):
            return {"error": "Unexpected RAG results format."}
        return results
    
    except ValueError as ve:  
        logger.exception(ve, extra={"tenant": company_code})
        return {"error": str(ve)}
    except aiohttp.ClientError as ce:
        logger.error(f"Client error occurred while calling RAG API: {ce}")
        return {"error": "Client error occurred while processing the request."}
    except Exception as e:  
        logger.exception(e, extra={"tenant": company_code})
        return {"error": "An unexpected issue occurred. Please try again later."}


def parse_user_id(string):
    # 입력 데이터가 문자열인지 확인
    if not isinstance(string, str):
        return None
    
    # 입력 문자열이 JSON 형식인지 검증
    try:
        import json
        json.loads(string)
    except json.JSONDecodeError:
        return None
    
    # 기존 로직 유지
    if string.strip() == "":
        return None
    match = re.search(r'"user_id"\s*:\s*"([a-zA-Z0-9]+)"', string)
    return match.group(1) if match else None


def remove_prefix_tag(text):
    # 텍스트 인코딩을 UTF-8로 변환
    if isinstance(text, str):
        text = text.encode('utf-8').decode('utf-8')
    return re.sub(r'^<[^>]+>\s*', '', text)