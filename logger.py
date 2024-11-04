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
    try:
        logger.log(level, message)
        print(f"Logged: {level} - {message}")  # Отладочная информация
    except Exception as e:
        print(f"Logging error: {e}")

# Функция для обработки события и записи в лог
def handle_some_event():
    log_event(logging.DEBUG, "This is a debug message: handling event started.")
    log_event(logging.INFO, "Some event occurred that may need attention.")
    log_event(logging.WARNING, "This is a warning message: something unusual happened.")
    log_event(logging.ERROR, "This is an error message: something went wrong.")
    log_event(logging.CRITICAL, "This is a critical message: a serious error occurred.")
    logger.debug("Debug: Event handled successfully.")
    print("Event handled")  # Отладочное сообщение на экран

# Пример вызова функции
handle_some_event()
