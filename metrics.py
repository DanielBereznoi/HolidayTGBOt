from prometheus_client import CollectorRegistry, Gauge, Summary, Counter, start_http_server
import time

# Регистрируем метрики
registry = CollectorRegistry()

# Метрика для общего числа сообщений
total_messages = Gauge('total_messages', 'Total number of messages received', registry=registry)

# Метрика для времени обработки команд
command_processing_time = Summary('command_processing_time', 'Time spent processing commands', registry=registry)

# Метрика для общего числа пользователей
total_users = Counter('total_users', 'Total number of users interacted with the bot', registry=registry)

# Метрика для количества ошибок
error_count = Counter('error_count', 'Total number of errors occurred', registry=registry)

# Старт HTTP-сервера для метрик
def start_metrics_server():
    start_http_server(8000)  # Порт, на котором будет доступен эндпоинт метрик

# Функция для увеличения счётчика сообщений
def increment_message_count():
    total_messages.inc()

# Функция для увеличения общего числа пользователей
def increment_total_users():
    total_users.inc()

# Функция для увеличения счётчика ошибок
def increment_error_count():
    error_count.inc()

# Декоратор для измерения времени выполнения команд
def track_command_time(func):
    def wrapper(*args, **kwargs):
        with command_processing_time.time():
            return func(*args, **kwargs)
    return wrapper
