import logging
import json
import os
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

logs = 'logs'
os.makedirs(logs, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'level': record.levelname,
            'message': record.getMessage(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(log_entry)

# Настраиваем обработчик для ротации логов
handler = TimedRotatingFileHandler(
    #os.path.join(logs, "bot.log"), when="midnight", interval=1, backupCount=30
    os.path.join(logs, "bot.log"), when="M", interval=2, backupCount=30
)
handler.setFormatter(JsonFormatter())

# Инициализируем логгер
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Функция для записи сообщений лога
def log_event(level, message):
    logger.log(level, message)

# Функция для обработки события и записи в лог
def handle_some_event():
    log_event(logging.WARNING, "Some event occurred that may need attention.")
