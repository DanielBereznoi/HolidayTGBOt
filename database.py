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