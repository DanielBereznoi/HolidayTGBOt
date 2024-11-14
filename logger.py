import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
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

def setup_logger(log_dir="logs"):
    logger = logging.getLogger("bot_logger")
    logger.setLevel(logging.DEBUG)
    log_filename = datetime.now(TALLINN).strftime("%Y-%m-%d___%H-%M-%S") + ".log"
    log_path = os.path.join(log_dir, log_filename)
    handler = RotatingFileHandler(log_path, maxBytes=10**6, backupCount=360)  # 1MB limit and ~3 months
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger

logger = setup_logger(log_dir=log_dir)

def log_event(level, message):
    log_level = getattr(logging, level.upper(), None)
    if log_level is None:
        raise ValueError(f"Invalid log level: {level}")
    logger.log(log_level, message)

def get_last_log_lines(log_dir="logs", num_lines=100):
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    
    if not log_files:
        return ""

    latest_log_file = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))

    log_path = os.path.join(log_dir, latest_log_file)

    with open(log_path, 'r') as f:
        lines = f.readlines()

    return lines[-num_lines:]
