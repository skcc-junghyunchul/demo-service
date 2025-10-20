from dotenv import load_dotenv
import os
import yaml
import sys
# load .env
load_dotenv()

try:
    with open("/home/config.yaml", 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
except Exception as e:
    raise Exception(f"설정 파일 '/home/config.yaml' 로드 실패: {str(e)}")

RAG_API_URL = config_data["misc"]["rag_api_url"].strip()
NCP_REDIS_PORT = config_data["misc"]["ncp_redis_port"]
NCP_REDIS_DB_CHATHISTORY = config_data["misc"]["ncp_redis_db_chathistory"]
NCP_REDIS_DB_MULTI_RESOURCE = config_data["misc"]["ncp_redis_db_multi_resource"]    
WELCOME_MESSAGE_PREFIX =  config_data["misc"]["welcome_message_prefix"].strip()

# 데이터베이스 연결 타임아웃 설정
DB_TIMEOUT = 30

# from secrets
NCP_REDIS_HOST=os.environ.get('NCP_REDIS_HOST').strip()

# 로그 파일 경로 설정 추가
LOG_PATH = os.environ.get('LOG_PATH')

# 로그 파일 권한 확인 추가
if LOG_PATH and not os.access(LOG_PATH, os.W_OK):
    raise Exception(f"로그 파일에 대한 쓰기 권한이 없습니다: {LOG_PATH}")

# Redis 자원 맵핑
multi_tenant_resource = {}

def initialize_multi_tenant_resource():
    global multi_tenant_resource

    from app.enums.llm_resource import LLMType
    from app.enums.storage_resource import StorageType
    from app.enums.chit_chat_resource import ChitChatType
    from app.api.v1.multi_resource import get_multi_resource

    for enum_class in [LLMType, StorageType, ChitChatType]:
        for item in enum_class.__members__.values():
            resource = get_multi_resource(item)
            if resource and resource.get("resource_value") is not None:
                multi_tenant_resource[item] = resource
                setattr(sys.modules[__name__], item.name, resource)  # ✅ 모듈 속성 등록