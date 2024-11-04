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
    os.path.join(logs, "bot.log"), when="M", interval=2, backupCount=30
)
handler.setFormatter(JsonFormatter())

# Инициализируем логгер
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Функция для записи сообщений лога
def log_event(level, message):
    levels = {
        'INFO': logging.INFO,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        'WARNING': logging.WARNING,
        'DEBUG': logging.DEBUG,
    }
    
    print(levels.get(level))
    logger.log(levels.get(level), message)
    print(type(levels.get(level)))

# Функция для обработки события и записи в лог
def handle_some_event():
    log_event("DEBUG", "This is a debug message: handling event started.")
    log_event("INFO", "Some event occurred that may need attention.")
    log_event("WARNING", "This is a warning message: something unusual happened.")
    log_event("ERROR", "This is an error message: something went wrong.")
    log_event("CRITICAL", "This is a critical message: a serious error occurred.")
    logger.debug("Debug: Event handled successfully.")
    print("Event handled")  # Отладочное сообщение на экран

# Пример вызова функцииF
handle_some_event()
