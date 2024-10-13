import psycopg2
from db_connection import get_connection

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
    rows = execute_query('SELECT * FROM "Events"')
    
    # Выводим данные
    print("Данные из таблицы:")
    for row in rows:
        print(row)

def add_data_to_db(chat_ID, event_date, event_name, repeating):
    """SQL-запрос добавления данных с новым столбцом"""
    execute_query('INSERT INTO "Events" ("chat_ID", "event_name", "event_date", "repeating") VALUES (%s, %s, %s, %s)', 
                  (chat_ID, event_name, event_date, repeating))
    print("Данные добавлены.")


def check_record_exists(chat_ID, event_date, event_name):
    # Проверка существования записи
    query = 'SELECT id FROM "Events" WHERE "chat_ID" = %s AND "event_name" = %s AND "event_date" = %s'
    result = execute_query(query, (chat_ID, event_name, event_date))
    return result

def delete_data_from_db(identifier):
    # SQL-запрос удаления данных
    record = check_record_exists(identifier)
    if record:
        execute_query('DELETE FROM "Events" WHERE id = %s', (identifier,))
        print("Данные удалены.")
    else:
        print("Ошибка: Запись не найдена.")


def get_events_by_chat_id(chat_ID):
    # Получение всех событий для пользователя, отсортированных по дате
    query = 'SELECT * FROM "Events" WHERE "chat_ID" = %s ORDER BY "event_date"'
    rows = execute_query(query, (chat_ID,))
    return rows

def get_events_by_today(chat_ID):
    """Получение всех событий для пользователя за сегодня"""
    query = '''
        SELECT * FROM "Events" 
        WHERE "chat_ID" = %s AND "event_date" = CURRENT_DATE
    '''
    rows = execute_query(query, (chat_ID,))
    
    print(f"События для Вас {chat_ID} на сегодня:")
    if rows:
        for row in rows:
            print(row)
    else:
        print("Нет событий на сегодня для данного Вас.")
    return rows

# Вызов функции для получения данных
if __name__ == "__main__":
    get_data_from_db()
