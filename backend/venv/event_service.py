import psycopg2
from db_connection import get_connection

def execute_query(query, params=None):
    """Optimisation"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if query.strip().lower().startswith('select'):
                return cursor.fetchall()

def get_data_from_db():
    # Выполняем запрос для получения всех данных из таблицы
    rows = execute_query('SELECT * FROM "Events"')
    
    # Выводим данные
    print("Данные из таблицы:")
    for row in rows:
        print(row)

def add_data_to_db(new_data):
    # SQL-запрос добавления данных
    execute_query('INSERT INTO "Events" (column1, column2) VALUES (%s, %s)', new_data)
    print("Данные добавлены.")

def delete_data_from_db(identifier):
    # SQL-запрос удаления данных по id
    execute_query('DELETE FROM "Events" WHERE id = %s', (identifier,))
    print("Данные удалены.")

# Вызов функции для получения данных
if __name__ == "__main__":
    get_data_from_db()
