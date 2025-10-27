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

async def get_slot_by_rag(user_question, category, is_clear, chat_history=None, company_code=None, user_id=None, message:Message=None):
    
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
        
    try:
        results = await call_rag_api(query_params={}, body=body)
        return results
    
    except ValueError as ve:  
        logger.exception(ve,extra={"tenant":company_code})
        return {"error": str(ve)}
    except Exception as e:  
        logger.exception(e,extra={"tenant":company_code})
        return {"error": str(e)}
    finally:
        # Explicit deletion is unnecessary; Python's garbage collector handles it.
        pass


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
    match = re.search(r'"user_id"\s*:\s*"(\w+)"', string)
    return match.group(1) if match else None


def remove_prefix_tag(text):
    return re.sub(r'^<[^>]+>\s*', '', text)