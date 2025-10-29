from dotenv import load_dotenv
import os
import yaml
import sys
import logging
import redis
import socket

# load .env
load_dotenv()

# 필수 환경 변수 확인 및 기본값 설정
required_env_vars = {
    'NCP_REDIS_HOST': 'localhost',
    'LOG_PATH': './logs/app.log',
    'DATABASE_URL': 'sqlite:///default.db',
    'CONFIG_FILE_PATH': './config.yaml',
    'REDIS_PASSWORD': None
}

for var, default_value in required_env_vars.items():
    if os.environ.get(var) is None:
        os.environ[var] = default_value
        logging.info(f"환경 변수 '{var}'가 설정되지 않아 기본값 '{default_value}'로 설정되었습니다.")
        with open('.env', 'a') as f:
            f.write(f"{var}={default_value}\n")

# Redis 비밀번호 검증 및 업데이트
REDIS_PASSWORD = os.environ['REDIS_PASSWORD']
if not REDIS_PASSWORD or REDIS_PASSWORD.strip() == "":
    logging.warning("Redis 비밀번호가 설정되지 않았습니다. 기본값으로 설정합니다.")
    REDIS_PASSWORD = "default_password"  # 기본 비밀번호 설정
    os.environ['REDIS_PASSWORD'] = REDIS_PASSWORD
    with open('.env', 'a') as f:
        f.write(f"REDIS_PASSWORD={REDIS_PASSWORD}\n")
else:
    logging.info("Redis 비밀번호가 정상적으로 설정되었습니다.")

# Redis 설정
NCP_REDIS_HOST = os.environ['NCP_REDIS_HOST'].strip()
DATABASE_URL = os.environ['DATABASE_URL'].strip()
CONFIG_FILE_PATH = os.environ['CONFIG_FILE_PATH'].strip()

# 설정 파일 로드
try:
    if not os.path.exists(CONFIG_FILE_PATH):
        raise FileNotFoundError(f"설정 파일 '{CONFIG_FILE_PATH}'이 존재하지 않습니다.")
    if not os.access(CONFIG_FILE_PATH, os.R_OK):
        raise PermissionError(f"설정 파일 '{CONFIG_FILE_PATH}'에 대한 읽기 권한이 없습니다.")
    if not CONFIG_FILE_PATH.endswith('.yaml'):
        raise ValueError(f"설정 파일 '{CONFIG_FILE_PATH}'은 YAML 형식이 아닙니다.")
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
except Exception as e:
    logging.error(f"설정 파일 로드 실패: {str(e)}")
    raise

# Redis 포트 설정
def find_available_port(start_port):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
        port += 1

NCP_REDIS_PORT = config_data["misc"].get("ncp_redis_port", 6379)
NCP_REDIS_PORT = find_available_port(NCP_REDIS_PORT)

# Redis 연결 설정
try:
    redis_client = redis.StrictRedis(
        host=NCP_REDIS_HOST,
        port=NCP_REDIS_PORT,
        db=config_data["misc"].get("ncp_redis_db_chathistory", 0),
        password=os.environ['REDIS_PASSWORD'],
        max_connections=10
    )
    redis_client.ping()
except redis.ConnectionError as e:
    logging.error(f"Redis 연결 실패: {str(e)}")
    raise

# 리소스 초기화
multi_tenant_resource = {}

def initialize_multi_tenant_resource():
    global multi_tenant_resource
    from app.enums.llm_resource import LLMType
    from app.enums.storage_resource import StorageType
    from app.enums.chit_chat_resource import ChitChatType
    from app.api.v1.multi_resource import get_multi_resource

    for enum_class in [LLMType, StorageType, ChitChatType]:
        for item in enum_class.__members__.values():
            try:
                resource = get_multi_resource(item)
                if resource and resource.get("resource_value") is not None:
                    multi_tenant_resource[item] = resource
                    setattr(sys.modules[__name__], item.name, resource)
                else:
                    logging.warning(f"리소스 초기화 실패: {item.name}에 유효한 리소스 값이 없습니다.")
            except Exception as e:
                logging.error(f"리소스 초기화 중 오류 발생: {item.name}, {str(e)}")
                multi_tenant_resource[item] = {"resource_value": "default"}

    multi_tenant_resource["tenant_storage"] = {
        "default_storage": "s3",
        "backup_storage": "gcs"
    }

initialize_multi_tenant_resource()