import psycopg2
from db_connection import get_connection
from datetime import datetime, timedelta, date

nearest_date = None


def execute_query(query, params=None):
    """Optimisation"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().lower().startswith('select'):
                    return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"Ошибка при выполнении запроса: {e}")


def get_data_from_db():
    # Выполняем запрос для получения всех данных из таблицы
    rows = execute_query('SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events"')

    # Выводим данные
    print("Данные из таблицы:")
    if rows:
        for row in rows:
            print(row)
    else:
        print("Нет данных в таблице.")


def add_data_to_db(chat_ID, event_date, hour, minute, event_name, repeating):
    """SQL-запрос добавления данных с новым столбцом"""
    # Проверяем, существует ли уже запись с таким chat_ID, event_timestamp и event_name
    event_timestamp = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
    
    if check_record_exists(chat_ID, event_timestamp, event_name):
        print("Ошибка: запись уже существует.")
        return False

    # Если записи нет, добавляем новую
    execute_query('INSERT INTO "Events" ("chat_ID", "event_name", "event_timestamp", "repeating") VALUES (%s, %s, %s, %s)',
                  (chat_ID, event_name, event_timestamp, repeating))
    update_date()
    return True


def check_record_exists(chat_ID, event_timestamp, event_name):
    """Проверка существования записи"""
    query = 'SELECT "ID" FROM "Events" WHERE "chat_ID" = %s AND "event_name" = %s AND "event_timestamp" = %s'
    result = execute_query(query, (chat_ID, event_name, event_timestamp))
    return bool(result)  # Возвращаем True, если запись существует, и False в противном случае


def delete_data_from_db(identifier):
    # SQL-запрос удаления данных
    execute_query('DELETE FROM "Events" WHERE "ID" = %s', (identifier,))
    print("Данные удалены.")
    update_date()


def get_events_by_chat_id(chat_ID):
    # Получение всех событий для пользователя, отсортированных по дате
    query = 'SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events" WHERE "chat_ID" = %s ORDER BY "event_timestamp"'
    rows = execute_query(query, (chat_ID,))
    return rows


def get_events_by_today():
    """Получение всех событий для пользователя за сегодня"""
    query = '''
        SELECT "chat_ID", "event_timestamp", "event_name", "ID", "repeating" FROM "Events" 
        WHERE "event_timestamp" = CURRENT_DATE
    '''
    rows = execute_query(query)
    return rows  # Добавлено


def update_date():
    global nearest_date
    """Получение всех событий и обновление ближайшей даты"""
    updating_date = '''
        SELECT "event_timestamp" from "Events" order by "event_timestamp" limit 1
    '''
    nearest_date = execute_query(updating_date)[0][0]
    print("nearest_date = " + str(nearest_date))


def check_dates():
    global nearest_date
    if nearest_date is None:
        update_date()
    print("comparing nearest_date = " + str(nearest_date))
    print(type(nearest_date))
    current_date = date.today()

    print(type(current_date))
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
        print(update_sql)
        execute_query(update_sql)

    if len(deleted_events) > 0:
        deleted_events_str = ", ".join(map(str, deleted_events))
        delete_sql = (f'DELETE FROM "Events" '
                      f'WHERE "Events"."ID" IN ({deleted_events_str});')
        print(delete_sql)
        execute_query(delete_sql)





# Вызов функции для получения данных
if __name__ == "__main__":
    import datetime
    # get_data_from_db()
    events = [(5167789151, datetime.date(2024, 10, 14), 'Poshol nahs', 7, True),
              (5167789151, datetime.date(2024, 10, 13), 'Poshol nah', 8, True),
              (466698059, datetime.date(2025, 2, 17), 'курва език', 10, False),
              (5167789151, datetime.date(2024, 12, 10), 'Pidor', 11, True),
              (5167789151, datetime.date(2024, 10, 20), 'Homo', 12, True),
              (5167789151, datetime.date(2024, 10, 20), 'Homo1', 13, True),
              (5167789151, datetime.date(2024, 10, 20), 'Homo12', 14, True)]
    update_events(events)
# data = [(1,2), (3,4), (5,6)]
# print(str(data).replace("[", "").replace("]", ""))
