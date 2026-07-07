import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_NAME = "Ru_Express"


def make_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        port=int(os.getenv("DB_PORT", 3306)),
        database=DB_NAME,
    )
