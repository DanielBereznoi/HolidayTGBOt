import time
import schedule
from events import get_all_events_today  # Импорт новой функции из другого файла

def check_events_daily():
    """Проверка наличия событий на сегодня и уведомление пользователя."""
    try:
        print("Checking events daily...")
        rows = get_all_events_today()
        if rows:
            # Логика уведомления пользователя
            print("Сегодня у вас есть следующие события:")
            for row in rows:
                print(row)  # Или другую логику вывода
        else:
            print("Сегодня нет событий.")
    except Exception as e:
        print(f"Ошибка при проверке событий: {e}")


def job():
    """Работа"""
    print("Проверка событий на сегодня...")
    check_events_daily()

def run_scheduler():
    """Запуск планировщика для проверки каждый час."""
    schedule.every().hour.do(job)
    print("Running...")
    while True:
        schedule.run_pending()
        time.sleep(3500)  # Проверка в сек

# Пример использования
if __name__ == "__main__":
    run_scheduler()
