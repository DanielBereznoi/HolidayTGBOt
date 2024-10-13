import psycopg2

def get_connection():
    return psycopg2.connect(
        database="Project_Birthday",
        user='postgres',
        password='admin',
        host='127.0.0.1',
        port='5432'
    )