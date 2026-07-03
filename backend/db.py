import os
import re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "Ru_Express"

SQL_SCHEMA_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "ru_express.sql")
SQL_SEED_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "seed.sql")


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

        with open(SQL_SCHEMA_SCRIPT, encoding="utf-8") as f:
            cursor.execute(f.read())

        while cursor.nextset():
            pass

        cursor.execute("SELECT COUNT(*) FROM Campus")
        if cursor.fetchone()[0] == 0:
            with open(SQL_SEED_SCRIPT, encoding="utf-8") as f:
                cursor.execute(f.read())

            while cursor.nextset():
                pass

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
