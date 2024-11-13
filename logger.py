import logging
import json
import os
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import pytz

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
TALLINN = pytz.timezone("Europe/Tallinn")

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps([
            datetime.now(TALLINN).strftime('%Y-%m-%d %H:%M:%S'),
            record.levelname,
            record.getMessage()
        ])

def setup_logger(log_dir="logs", log_filename="log"):
    logger = logging.getLogger("bot_logger")    # Создаём логгер
    logger.setLevel(logging.DEBUG)  # Уровень логирования

    log_path = os.path.join(log_dir, log_filename)
    handler = RotatingFileHandler(log_path, maxBytes=10**6, backupCount=30)  # 1MB
    handler.setFormatter(JsonFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger(log_dir=log_dir)

def log_event(level, message):  # Функция для лога
    logger.log(getattr(logging, level), message)
