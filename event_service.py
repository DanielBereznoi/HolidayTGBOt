from datetime import datetime, timedelta
from collections import defaultdict
import time
import subprocess
import bot_utils
import database
import holidays
from logger import log_event
nearest_event_datetime = None
user_blacklist = []

def get_data_from_db():
    # Выполняем запрос для получения всех данных из таблицы
    rows = database.execute_query('SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events"')

    # Выводим данные
    print("Данные из таблицы:")
    try:
        if rows:
            for row in rows:
                print(row)
                log_event("INFO", f"Data retrieved from DB: {rows}")
        else:
            print("Нет данных в таблице.")
            log_event("WARNING", "No data found in the table.")
        return rows
    except Exception as e:
        log_event("ERROR", f"Error occurred while retrieving data from DB: {e}")

def add_data_to_db(chat_ID, event_date, hour, minute, event_name, repeating):
    """SQL-запрос добавления данных с новым столбцом"""
    try:
        event_date = datetime.strptime(event_date, '%d.%m.%Y').date()
        event_timestamp = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=int(hour),
                                                                                        minutes=int(minute))
        log_event("INFO", f"Attempting to add event: {event_name} at {event_timestamp} for chat_ID {chat_ID}")
        print(event_timestamp)
        if check_record_exists(chat_ID, event_timestamp, event_name):
            print("Ошибка: запись уже существует.")
            log_event("WARNING", f"Record already exists for {event_name} at {event_timestamp}")
            return False

        database.execute_query(
            'INSERT INTO "Events" ("chat_ID", "event_name", "event_timestamp", "repeating") VALUES (%s, %s, %s, %s)',
            (chat_ID, event_name, event_timestamp, repeating))
        update_date()
        log_event("INFO", f"Event added successfully: {event_name} for chat_ID {chat_ID}")
        return True
    except Exception as e:
        log_event("ERROR", f"Error occurred while adding data to DB: {e}")
        return False

def check_record_exists(chat_ID, event_timestamp, event_name):
    """Проверка существования записи"""
    try:
        query = 'SELECT "ID" FROM "Events" WHERE "chat_ID" = %s AND "event_name" = %s AND "event_timestamp" = %s'
        result = database.execute_query(query, (chat_ID, event_name, event_timestamp))
        if result:
            log_event("INFO", f"Record exists for event: {event_name} at {event_timestamp}")
        else:
            log_event("INFO", f"No record found for event: {event_name} at {event_timestamp}")
        return bool(result)  # Возвращаем True, если запись существует, и False в противном случае
    except Exception as e:
        log_event("ERROR", f"Error occurred while checking record existence: {e}")
        return False

def delete_data_from_db(event_id):
    try:    
        # SQL-запрос удаления данных
        database.execute_query(f'DELETE FROM "Events" WHERE "ID" = {event_id}')
        log_event("INFO", f"Event with ID {event_id} deleted from DB.")
        update_date()
    except Exception as e:
        log_event("ERROR", f"Error occurred while deleting data from DB: {e}")

def get_events_by_chat_id(chat_id):
    # Получение всех событий для пользователя, отсортированных по дате
    try:
        query = 'SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events" WHERE "chat_ID" = %s ORDER BY "event_timestamp"'
        rows = database.execute_query(query, (chat_id,))
        if rows:
            log_event("INFO", f"Events retrieved for chat_ID {chat_id}: {rows}")
        else:
            log_event("WARNING", f"No events found for chat_ID {chat_id}.")
        return rows
    except Exception as e:
        log_event("ERROR", f"Error occurred while retrieving events for chat_ID {chat_id}: {e}")
        return []
def get_events_by_datetime():
    try:
        """Получение всех событий для пользователя за сегодня"""
        query = f'''
            SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events" 
            WHERE "event_timestamp" = '{nearest_event_datetime}'
        '''
        rows = database.execute_query(query)
        if rows:
            log_event("INFO", f"Events retrieved for datetime {nearest_event_datetime}: {rows}")
        else:
            log_event("WARNING", f"No events found for datetime {nearest_event_datetime}.")
        return rows
    except Exception as e:
        log_event("ERROR", f"Error occurred while retrieving events for datetime {nearest_event_datetime}: {e}")
        return []

def update_date():
    global nearest_event_datetime
    try:
        """Получение всех событий и обновление ближайшей даты"""
        updating_date = f'''
            SELECT "event_timestamp" FROM "Events"
            WHERE "event_timestamp" >= '{datetime.now().strftime(bot_utils.datetime_strformat)}'
            ORDER BY "event_timestamp" LIMIT 1
        '''

        result = database.execute_query(updating_date)
        if result:
            print(datetime.now().strftime(bot_utils.datetime_strformat))
            print("nearest_date = " + str(nearest_event_datetime))

            nearest_event_datetime = result[0][0]
            log_event("INFO", f"Nearest event datetime updated: {nearest_event_datetime}")
        else:
            nearest_event_datetime =  None
            log_event("WARNING", "No events found to update nearest event datetime.")
    except Exception as e:
        log_event("ERROR", f"Error occurred while updating nearest event datetime: {e}")

def check_dates():
    global nearest_event_datetime
    try:
        if nearest_event_datetime is None:
            update_date()
        current_datetime = datetime.today()

        # compared
        if nearest_event_datetime is not None:
            log_event("INFO", f"Comparing current datetime {current_datetime} with nearest event datetime {nearest_event_datetime}")

            minute_delta = timedelta(minutes=1)
            start = nearest_event_datetime - minute_delta
            end = nearest_event_datetime + minute_delta
            if start <= current_datetime <= end:
                log_event("INFO", "Event is within 1-minute range of current time.")
                return True
            else:
                log_event("INFO", "Event is not within 1-minute range of current time.")
            return False
        else:
            log_event("WARNING", "No nearest event datetime available for comparison.")
            return False
    except Exception as e:
        log_event("ERROR", f"Error occurred while checking dates: {e}")
        return False

def update_events(events):
    updated_events = []
    deleted_events = []
    try:
        for event in events:
            chat_id, event_timestamp, event_name, ID, repeating = event
            if repeating:  # Если repeating равно True Добавляем 1 год к дате события
                updated_date = event_timestamp.replace(year=event_timestamp.year + 1)
                updated_events.append((ID, updated_date))  # Append a tuple (ID, updated_date)
            else:
                deleted_events.append(ID)
        if len(updated_events) > 0:
            updated_values = ", ".join(
                f"({ID}, CAST('{updated_date.strftime('%Y-%m-%d')}' AS DATE))"  # Correctly access tuple elements
                for ID, updated_date in updated_events
            )
            update_sql = (f'UPDATE "Events" '
                        f'SET "event_timestamp" = updated_event.event_timestamp '
                        f'FROM (VALUES {updated_values}) AS updated_event(ID, event_timestamp) '
                        f'WHERE "Events"."ID" = updated_event.ID;')
            database.execute_query(update_sql)
            log_event("INFO", f"Updated events: {updated_events}")

        if len(deleted_events) > 0:
            deleted_events_str = ", ".join(map(str, deleted_events))
            delete_sql = (f'DELETE FROM "Events" '
                        f'WHERE "Events"."ID" IN ({deleted_events_str});')
            database.execute_query(delete_sql)
            log_event("INFO", f"Deleted events: {deleted_events}")
    except Exception as e:
        log_event("ERROR", f"Error occurred while updating events: {e}")

# Словари для отслеживания сообщений и активности
message_count = defaultdict(int)
last_message_time = defaultdict(float)
user_activity = defaultdict(lambda: {'messages': 0, 'last_activity': 0})

# Функция для проверки, есть ли пользователь в черном списке
def is_blacklisted(user_id):
    return user_id in user_blacklist

def fetch_blacklist():
    global user_blacklist
    user_blacklist = database.execute_query('SELECT chat_id FROM blacklist')

# Функция для добавления пользователя в черный список
def add_to_blacklist(user_id):
    if user_id not in user_blacklist:
        user_blacklist.append(user_id)
        database.execute_query('INSERT INTO blacklist (chat_id) VALUES (%s)', (user_id,))

# Функция для отправки уведомления администратору
def notify_admin(context, user_id):
    admin_chat_id = '5167789151'
    admin_chat_id1 = '466698059'
    message = f"Пользователь {user_id} был заблокирован за спам."
    context.bot.send_message(chat_id=admin_chat_id, text=message)
    context.bot.send_message(chat_id=admin_chat_id1, text=message)

# Обработка входящих сообщений
def handle_message(update, context):
    user_id = update.message.from_user.id

    # Проверка на наличие в черном списке
    if is_blacklisted(user_id):
        context.bot.reply_to(chat_id=update.effective_chat.id,
            text="Вы заблокированы, обратитесь к создателям этого шедевра")
        return

    # Установка текущего времени
    current_time = time.time()

    # Проверка лимитов на сообщения
    if current_time - last_message_time[user_id] < 60:  # 60 секунд
        message_count[user_id] += 1
    else:
        message_count[user_id] = 1  # Сброс счетчика после 60 секунд
        last_message_time[user_id] = current_time

    # Отслеживание активности
    user_activity[user_id]['messages'] += 1
    user_activity[user_id]['last_activity'] = current_time

    if message_count[user_id] > 20:  # Лимит на 20 сообщений в минуту
        context.bot.reply_to(chat_id=update.effective_chat.id,
            text="Вы превысили лимит сообщений. Пожалуйста, подождите.")
        return

    if user_activity[user_id]['messages'] > 20:  # Лимит на 20 сообщений
        add_to_blacklist(user_id)  # Добавление в черный список
        notify_admin(user_id)  # Уведомление администраторов
        context.bot.reply_to(chat_id=update.effective_chat.id,
            text="Вы были заблокированы за спам, обратитесь к создателям этого шедевра")
        return

    context.bot.reply_to(chat_id=update.effective_chat.id, text="Сообщение принято!")

def shutdown_system():
    try:
        subprocess.run(['sudo', 'shutdown', 'now'], check=True)
        print("System is shutdown...")
    except subprocess.CalledProcessError as e:
        print(f"Возникла ошибка при попытке shutting систему: {e}")

def reboot_system():
    try:
        subprocess.run(['sudo', 'reboot'], check=True)
        print("Система перезагружается...")
    except subprocess.CalledProcessError as e:
        print(f"Возникла ошибка при попытке перезагрузить систему: {e}")
        
def sleep_system():
    try:
        subprocess.run(['sudo', 'systemctl', 'suspend'], check=True)
        print("Система переходит в спящий режим...")
    except subprocess.CalledProcessError as e:
        print(f"Возникла ошибка при попытке перевести систему в спящий режим: {e}")

def choose_special_event_date(special_holiday_key, event_type):
    cur_year = datetime.now().year
    next_year = cur_year + 1
    holiday_date = None
    if event_type in ['est', 'rus']:
        dm = None
        if event_type == 'est':
            est_holidays = holidays.estonian_fixed_holidays
            dm = est_holidays[special_holiday_key]['date']
        else:
            rus_holidays = holidays.russian_fixed_holidays
        holiday_date = datetime.strptime(f'{dm}.{cur_year}', '%d.%m.%Y')
        if holiday_date < datetime.now():
           holiday_date = datetime.strptime(f'{dm}.{next_year}', '%d.%m.%Y')
    else:
        cur_year_events = holidays.get_floating_holidays(cur_year)
        holiday_date = datetime.strptime(cur_year_events[event_type]['date'], '%d.%m.%Y')
        if holiday_date < datetime.now():
            holiday_date = holidays.get_floating_holidays(next_year)[event_type]['date']
    return holiday_date


    pass