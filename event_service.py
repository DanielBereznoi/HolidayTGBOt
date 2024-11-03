from datetime import datetime, timedelta
from collections import defaultdict
import time
import database

nearest_date = None
user_blacklist = []

def get_data_from_db():
    # Выполняем запрос для получения всех данных из таблицы
    rows = database.execute_query('SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events"')

    # Выводим данные
    print("Данные из таблицы:")
    if rows:
        for row in rows:
            print(row)
    else:
        print("Нет данных в таблице.")

def add_data_to_db(chat_ID, event_date, hour, minute, event_name, repeating):
    """SQL-запрос добавления данных с новым столбцом"""
    event_date = datetime.strptime(event_date, '%d.%m.%Y').date()
    event_timestamp = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=int(hour), minutes=int(minute))
    
    if check_record_exists(chat_ID, event_timestamp, event_name):
        print("Ошибка: запись уже существует.")
        return False

    database.execute_query('INSERT INTO "Events" ("chat_ID", "event_name", "event_timestamp", "repeating") VALUES (%s, %s, %s, %s)',
                  (chat_ID, event_name, event_timestamp, repeating))
    update_date()
    return True

def check_record_exists(chat_ID, event_timestamp, event_name):
    """Проверка существования записи"""
    query = 'SELECT "ID" FROM "Events" WHERE "chat_ID" = %s AND "event_name" = %s AND "event_timestamp" = %s'
    result = database.execute_query(query, (chat_ID, event_name, event_timestamp))
    return bool(result)  # Возвращаем True, если запись существует, и False в противном случае

def delete_data_from_db(identifier):
    # SQL-запрос удаления данных
    database.execute_query('DELETE FROM "Events" WHERE "ID" = %s', (identifier,))
    print("Данные удалены.")
    update_date()

def get_events_by_chat_id(chat_ID):
    # Получение всех событий для пользователя, отсортированных по дате
    query = 'SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events" WHERE "chat_ID" = %s ORDER BY "event_timestamp"'
    rows = database.execute_query(query, (chat_ID,))
    return rows

def get_events_by_today():
    """Получение всех событий для пользователя за сегодня"""
    query = '''
        SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events" 
        WHERE "event_timestamp" = CURRENT_DATE
    '''
    rows = database.execute_query(query)
    return rows  # Добавлено

def update_date():
    global nearest_date
    """Получение всех событий и обновление ближайшей даты"""
    updating_date = '''
        SELECT "event_timestamp" from "Events" order by "event_timestamp" limit 1
    '''

    result = database.execute_query(updating_date)
    if result:
        nearest_date = result[0][0]
        print("nearest_date = " + str(nearest_date))

def check_dates():
    global nearest_date
    if nearest_date is None:
        update_date()
    current_date = datetime.today()

    # compared
    if nearest_date is not None:
        print("Comparing dates")
        if current_date < nearest_date:
            return False
        elif current_date > nearest_date:
            return False
        else:
            return True

def update_events(events):
    updated_events = []
    deleted_events = []
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

    if len(deleted_events) > 0:
        deleted_events_str = ", ".join(map(str, deleted_events))
        delete_sql = (f'DELETE FROM "Events" '
                      f'WHERE "Events"."ID" IN ({deleted_events_str});')
        database.execute_query(delete_sql)

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
        context.bot.reply_to(chat_id=update.effective_chat.id, text="Вы заблокированы, обратитесь к создателям этого шедевра")
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
        context.bot.reply_to(chat_id=update.effective_chat.id, text="Вы превысили лимит сообщений. Пожалуйста, подождите.")
        return

    if user_activity[user_id]['messages'] > 20:  # Лимит на 20 сообщений
        add_to_blacklist(user_id)  # Добавление в черный список
        notify_admin(user_id)  # Уведомление администраторов
        context.bot.reply_to(chat_id=update.effective_chat.id, text="Вы были заблокированы за спам, обратитесь к создателям этого шедевра")
        return

    # Ответ на сообщение
    context.bot.reply_to(chat_id=update.effective_chat.id, text="Сообщение принято!")

# Вызов функции для получения данных
if __name__ == "__main__":
    import datetime
