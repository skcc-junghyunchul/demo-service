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


log_level = os.environ.get('LOG_LEVEL').upper() if os.environ.get('LOG_LEVEL') else logging._nameToLevel["INFO"]
log_level= getattr(logging, log_level,logging.INFO)

# 디렉토리 설정
BASEDIR = os.getenv("BASEDIR", os.getcwd())
POD_NAME = os.getenv("POD_NAME", "default-pod")[-5:]
LOGGING_DIR = os.path.join(BASEDIR, "logs")
# LOGGING_DIR = "/tmp"
print(LOGGING_DIR)

# 기존 로그 파일 설정
# LOGGING_FILE = os.path.join(LOGGING_DIR, "chatbot-server.log")
# LOGGING_FILE = os.path.join(LOGGING_DIR, f"{POD_NAME}-chatbot-server.log")
os.makedirs(LOGGING_DIR, exist_ok=True)


# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(log_level)


COMMON = "common"
#커스텀 포멧 코드의 기본값 셋팅을 위한 필터정의
class UserFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "tenant"):
            record.tenant = COMMON  # 기본값 설정
        return True

#formatter = DefaultFormatter("%(levelprefix)s %(asctime).22s %(message)s")
#file_formatter = DefaultFormatter("%(levelprefix)s %(asctime).22s %(message)s", use_colors=False)

# 로거 포멧 공통으로 변경
formatter = DefaultFormatter("%(asctime)s - %(tenant)s - %(module)s - %(name)s - %(levelname)s - %(message)s")
file_formatter = DefaultFormatter("%(asctime)s - %(tenant)s - %(module)s - %(name)s - %(levelname)s - %(message)s")

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.addFilter(UserFilter())
console_handler.setFormatter(formatter)

# 타임로테이팅 파일 핸들러 설정 (매 분마다 새로운 파일 생성)
# file_handler = TimedRotatingFileHandler(LOGGING_FILE, when='midnight', interval=1, backupCount=30, encoding='utf-8', utc=False)
# file_handler.setLevel(log_level)
# file_handler.addFilter(UserFilter())
# file_handler.setFormatter(file_formatter)
#file_handler.suffix = "%Y-%m-%d_%H-%M-%S"
#file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")
# file_handler.suffix = "%Y%m%d"
# file_handler.extMatch = re.compile(r"^\d{8}$")
# 포맷터 설정
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


logger_provider = LoggerProvider(
    resource=Resource.create(
        {
            #"service.name": "example",
            "service.instance.id": os.uname().nodename,
        }
    ),
)


# OTLP Exporter
otlp_exporter = OTLPLogExporter(endpoint="http://grafana-alloy.grafana-alloy:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter,max_export_batch_size=512,schedule_delay_millis=5000,export_timeout_millis=30000))
set_logger_provider(logger_provider)

otel_handler = LoggingHandler(level=logging.INFO,logger_provider=logger_provider)
otel_handler.addFilter(UserFilter())
otel_handler.setFormatter(formatter)

# 핸들러를 로거에 추가
logger.addHandler(console_handler)
# logger.addHandler(file_handler)
logger.addHandler(otel_handler)