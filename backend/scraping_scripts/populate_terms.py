## relies on the syllabi table to be complete
## populates the terms table with terms that are referenced by syllabi

import psycopg2
from dotenv import load_dotenv
import os

import requests

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

def get_doc_data(code: str) -> dict:
    url = "https://tamu.simplesyllabus.com/api2/doc-full-page-get"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }
    resp = requests.get(url, headers=headers, params={"code": code})
    resp.raise_for_status()
    return resp.json()["items"][0]["doc_data"]


if __name__ == "__main__":

    ## searches syllabi table for term_id
    ## gets one row for each unique term_id
    cur.execute("""
        SELECT DISTINCT ON (term_id) code
        FROM syllabi
        WHERE term_id IS NOT NULL
        ORDER BY term_id;
    """)

    codes = cur.fetchall()

    for code in codes:
        data = get_doc_data(code)
        term = data["term"]

        cur.execute("""
        INSERT INTO terms (entity_id, name, start_date, end_date)
        VALUES (%s, %s, %s, %s)
        """, (term["entity_id"], term["name"], term["start_date"], term["end_date"]))

    conn.commit()
    print(codes)