import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import re
from uvicorn.logging import DefaultFormatter
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

# 로그 레벨 설정
default_log_level = logging.INFO
log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, default_log_level)

# 기본 로거 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# 디렉토리 설정
BASEDIR = os.getenv("BASEDIR", os.getcwd())
POD_NAME = os.getenv("POD_NAME", "default-pod")[-5:]
LOGGING_DIR = os.path.join(BASEDIR, "logs")
os.makedirs(LOGGING_DIR, exist_ok=True)

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

COMMON = "common"

# 커스텀 포멧 코드의 기본값 셋팅을 위한 필터 정의
class UserFilter(logging.Filter):
    def filter(self, record):
        # 테넌트 유효성 검사 추가
        if not hasattr(record, "tenant"):
            record.tenant = COMMON  # 기본값 설정
        elif not self.is_valid_tenant(record.tenant):
            raise ValueError(f"Invalid tenant: {record.tenant}")
        return True

    @staticmethod
    def is_valid_tenant(tenant):
        # 테넌트 이름이 알파벳과 숫자로만 구성되어 있는지 확인
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", tenant))

formatter = DefaultFormatter("%(asctime)s - %(tenant)s - %(module)s - %(name)s - %(levelname)s - %(message)s")
file_formatter = DefaultFormatter("%(asctime)s - %(tenant)s - %(module)s - %(name)s - %(levelname)s - %(message)s")

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.addFilter(UserFilter())
console_handler.setFormatter(formatter)

logger_provider = LoggerProvider(
    resource=Resource.create(
        {
            "service.instance.id": generate_instance_id(),
        }
    ),
)

# Ensure the service instance ID is set and verified during initialization
if not logger_provider.resource.attributes.get("service.instance.id"):
    raise ValueError("Service instance ID missing")

# OTLP Exporter
otlp_exporter = OTLPLogExporter(endpoint="http://grafana-alloy.grafana-alloy:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter, max_export_batch_size=512, schedule_delay_millis=5000, export_timeout_millis=30000))
set_logger_provider(logger_provider)

otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
otel_handler.addFilter(UserFilter())
otel_handler.setFormatter(formatter)

# 핸들러를 로거에 추가
logger.addHandler(console_handler)
logger.addHandler(otel_handler)