import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "Ru_Express"

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT PRIMARY KEY,
        nome VARCHAR(50) NOT NULL
    )
    """,
    """
    INSERT IGNORE INTO usuarios VALUES (1, 'teste')
    """,
]


def make_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def init_db():
    conn = make_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)

        conn.commit()
        cursor.close()
    finally:
        conn.close()


def get_db():
    conn = make_connection()
    conn.database = DB_NAME
    try:
        yield conn
    finally:
        conn.close()
