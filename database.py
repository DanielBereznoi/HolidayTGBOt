import psycopg2
import secret_parser

def get_connection():
    return psycopg2.connect(
        database=secret_parser.db_name,
        user=secret_parser.db_username,
        password=secret_parser.db_password,
        host='127.0.0.1',
        port='5432'
    )
    
def execute_query(query, params=None):
    """Выполняет SQL-запрос и возвращает результат для SELECT-запросов"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().lower().startswith('select'):
                    return cursor.fetchall()
    except psycopg2.Error as e:
        print(f"Ошибка при выполнении запроса: {e}")