import sqlite3
import time
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

sqlite_conn = sqlite3.connect("syllabi.db")
sqlite_cur = sqlite_conn.cursor()
sqlite_cur.execute("SELECT code, title, subtitle, course_id, editors FROM syllabi")
rows = sqlite_cur.fetchall()

DATABASE_URL = os.getenv("DATABASE_URL")
BATCH_SIZE = 100  # Insert 100 rows at a time

def get_pg_connection():
    return psycopg2.connect(DATABASE_URL)

def insert_batch(batch):
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    try:
        pg_cur.executemany("""
            INSERT INTO syllabi_list (code, title, subtitle, course_id, editors)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                subtitle = EXCLUDED.subtitle,
                course_id = EXCLUDED.course_id,
                editors = EXCLUDED.editors
        """, batch)
        pg_conn.commit()
    except Exception as e:
        print(f"BATCH ERROR: {e}")
    finally:
        pg_cur.close()
        pg_conn.close()

i = 8000
total = len(rows)
while i < total:
    batch = rows[i:i+BATCH_SIZE]
    print(f"Inserting batch {i}–{i+len(batch)} of {total}...")
    insert_batch(batch)
    i += BATCH_SIZE
    time.sleep(0.2)  # avoid rate limiting by pooler


sqlite_cur.close()
sqlite_conn.close()
