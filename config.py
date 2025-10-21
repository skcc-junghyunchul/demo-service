from dotenv import load_dotenv
import os
import yaml
import sys
import logging
import redis

# load .env
load_dotenv()

# 필수 환경 변수 확인
required_env_vars = ['NCP_REDIS_HOST', 'LOG_PATH']
for var in required_env_vars:
    if os.environ.get(var) is None:
        raise Exception(f"필수 환경 변수 '{var}'가 설정되어 있지 않습니다.")

# 데이터베이스 URL 설정
DATABASE_URL = 'your_database_url_here'

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
NCP_REDIS_HOST = os.environ.get('NCP_REDIS_HOST').strip()

# 로그 파일 경로 설정 추가
LOG_PATH = os.environ.get('LOG_PATH')

# 로그 파일 권한 확인 및 생성 로직 추가
if LOG_PATH:
    # 로그 파일이 존재하지 않으면 생성
    if not os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH, 'w') as f:
                pass
        except Exception as e:
            raise Exception(f"로그 파일 생성 실패: {str(e)}")
    
    # 로그 파일에 대한 쓰기 권한 확인
    if not os.access(LOG_PATH, os.W_OK):
        try:
            os.chmod(LOG_PATH, 0o666)  # 모든 사용자에게 쓰기 권한 부여
        except Exception as e:
            raise Exception(f"로그 파일에 대한 쓰기 권한 수정 실패: {str(e)}")
    
    # 여전히 쓰기 권한이 없는 경우 예외 발생
    if not os.access(LOG_PATH, os.W_OK):
        raise Exception(f"로그 파일에 대한 쓰기 권한이 없습니다: {LOG_PATH}")

# 로거 설정
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Redis 연결 설정 검사
try:
    redis_client = redis.StrictRedis(
        host=NCP_REDIS_HOST,
        port=NCP_REDIS_PORT,
        db=NCP_REDIS_DB_CHATHISTORY,
        max_connections=10  # pool_size 증가
    )
    redis_client.ping()
except redis.ConnectionError as e:
    logging.error(f"Redis 연결 실패: {str(e)}")
    raise Exception(f"Redis 연결 실패: {str(e)}")

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