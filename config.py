from dotenv import load_dotenv
import os
import yaml
import sys
import logging
import redis
import socket

# load .env
load_dotenv()

# 필수 환경 변수 확인
required_env_vars = ['NCP_REDIS_HOST', 'LOG_PATH', 'DATABASE_URL']
for var in required_env_vars:
    if os.environ.get(var) is None:
        raise Exception(f"필수 환경 변수 '{var}'가 설정되어 있지 않습니다.")

# Redis 설정 추가
NCP_REDIS_HOST = os.environ.get('NCP_REDIS_HOST')
if NCP_REDIS_HOST is None or NCP_REDIS_HOST.strip() == "":
    logging.warning("Redis 설정 오류: 'NCP_REDIS_HOST' 환경 변수가 설정되어 있지 않습니다. 기본값 'localhost'를 사용합니다.")
    NCP_REDIS_HOST = "localhost"
NCP_REDIS_HOST = NCP_REDIS_HOST.strip()

# 데이터베이스 URL 설정
DATABASE_URL = os.environ.get('DATABASE_URL')

try:
    # 설정 파일 존재 여부 확인
    if not os.path.exists("/home/config.yaml"):
        raise FileNotFoundError("설정 파일 '/home/config.yaml'이 존재하지 않습니다.")
    
    # 설정 파일 읽기 가능 여부 확인
    if not os.access("/home/config.yaml", os.R_OK):
        raise PermissionError("설정 파일 '/home/config.yaml'에 대한 읽기 권한이 없습니다.")
    
    # 설정 파일 로드
    with open("/home/config.yaml", 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
except FileNotFoundError as e:
    logging.error(str(e))
    raise Exception(str(e))
except PermissionError as e:
    logging.error(str(e))
    raise Exception(str(e))
except Exception as e:
    logging.error(f"설정 파일 '/home/config.yaml' 로드 실패: {str(e)}")
    raise Exception(f"설정 파일 '/home/config.yaml' 로드 실패: {str(e)}")

RAG_API_URL = config_data["misc"]["rag_api_url"].strip()
NCP_REDIS_PORT = config_data["misc"]["ncp_redis_port"]
NCP_REDIS_DB_CHATHISTORY = config_data["misc"].get("ncp_redis_db_chathistory", 0)  # 기본값 0으로 설정
NCP_REDIS_DB_MULTI_RESOURCE = config_data["misc"].get("ncp_redis_db_multi_resource", 1)  # 기본값 1로 설정
WELCOME_MESSAGE_PREFIX =  config_data["misc"]["welcome_message_prefix"].strip()

# 데이터베이스 연결 타임아웃 설정
DB_TIMEOUT = 30

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
            logging.error(f"로그 파일 생성 실패: {str(e)}")
            raise Exception(f"로그 파일 생성 실패: {str(e)}")
    
    # 로그 파일에 대한 쓰기 권한 확인
    if not os.access(LOG_PATH, os.W_OK):
        try:
            os.chmod(LOG_PATH, 0o666)  # 모든 사용자에게 쓰기 권한 부여
        except Exception as e:
            logging.error(f"로그 파일에 대한 쓰기 권한 수정 실패: {str(e)}")
            raise Exception(f"로그 파일에 대한 쓰기 권한 수정 실패: {str(e)}")
    
    # 여전히 쓰기 권한이 없는 경우 예외 발생
    if not os.access(LOG_PATH, os.W_OK):
        logging.error(f"로그 파일에 대한 쓰기 권한이 없습니다: {LOG_PATH}")
        raise Exception(f"로그 파일에 대한 쓰기 권한이 없습니다: {LOG_PATH}")

# 로거 설정
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 포트 사용 여부 확인 함수
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Redis 포트 사용 여부 확인 및 대체 포트 설정
if is_port_in_use(NCP_REDIS_PORT):
    logging.warning(f"포트 {NCP_REDIS_PORT}가 사용 중입니다. 다른 포트를 사용합니다.")
    NCP_REDIS_PORT += 1  # 포트를 1 증가시켜 사용 가능한 포트로 설정

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

    # 추가된 스토리지 설정
    tenant_storage_config = {
        "default_storage": "s3",
        "backup_storage": "gcs"
    }
    multi_tenant_resource["tenant_storage"] = tenant_storage_config

# .env 파일에 DATABASE_URL 추가
with open('.env', 'a') as f:
    f.write('DATABASE_URL=<your_database_url_here>\n')