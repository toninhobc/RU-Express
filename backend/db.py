import os
import re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "Ru_Express"

SQL_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "ru_express.sql")


def make_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def _parse_sql_file(filepath: str) -> list[str]:
    """
    Splits a .sql file into individual statements, respecting DELIMITER
    changes used by triggers/procedures.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    # Remove comment lines and block comments
    raw = re.sub(r"--.*", "", raw)
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)

    statements: list[str] = []
    current_delimiter = ";"
    buf: list[str] = []

    for line in raw.splitlines():
        stripped = line.strip()

        if stripped.upper().startswith("DELIMITER "):
            if buf:
                stmt = " ".join(buf).strip()
                if stmt:
                    statements.append(stmt)
                buf = []
            current_delimiter = stripped.split(maxsplit=1)[1].strip()
            continue

        buf.append(line)

        if stripped.endswith(current_delimiter):
            full = " ".join(buf).strip()
            if full.endswith(current_delimiter):
                full = full[: -len(current_delimiter)].strip()
            if full:
                statements.append(full)
            buf = []

    if buf:
        stmt = " ".join(buf).strip()
        if stmt:
            statements.append(stmt)

    return [s for s in statements if s and not s.isspace()]


def init_db():
    conn = make_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        # Parse and execute the full DDL/DML script
        statements = _parse_sql_file(SQL_SCRIPT)
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except mysql.connector.Error as err:
                # Allow script to continue even if a statement fails
                # (e.g. inserting duplicates on re-run)
                print(f"[WARN] {err}")

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
