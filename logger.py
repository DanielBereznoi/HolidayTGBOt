import logging
import json
import os
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'level': record.levelname,
            'message': record.getMessage(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(log_entry)

def setup_logger(log_dir="logs", log_filename="bot.log"):
    # Создаём логгер
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.DEBUG)  # Уровень логирования

    # Обработчик с ротацией логов (ежедневно, с хранением 30 последних логов)
    log_path = os.path.join(log_dir, log_filename)
    handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1, backupCount=30)
    handler.setFormatter(JsonFormatter())
    
    # Добавляем обработчик в логгер
    logger.addHandler(handler)

    return logger

logger = setup_logger(log_dir=log_dir)

# Функция для записи сообщений лога
def log_event(level, message):
    levels = {key: getattr(logging, key) for key in ['INFO', 'ERROR', 'CRITICAL', 'WARNING', 'DEBUG']}
    logger.log(levels.get(level), message)

# Функция для обработки события и записи в лог
def handle_some_event():
    log_event("DEBUG", "This is a debug message: handling event started.")
    log_event("INFO", "Some event occurred that may need attention.")
    log_event("WARNING", "This is a warning message: something unusual happened.")
    log_event("ERROR", "This is an error message: something went wrong.")
    log_event("CRITICAL", "This is a critical message: a serious error occurred.")
    print("Event handled")  # Отладочное сообщение на экран

# Пример вызова функции
