import math
import sqlite3
import json
import time

import requests




import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = connection.cursor()


ORG_ID = {
    "Texas A&M University": "e49cc748-bf42-494b-b463-a84e8e35a878",
    "College of Engineering": "3be77ee4-1aeb-44ff-8110-42e8c2949b21"
    }

SEARCH_URL = "https://tamu.simplesyllabus.com/api2/doc-library-search"
DOC_URL = "https://tamu.simplesyllabus.com/api2/doc-full-page-get"


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) SyllabusScraper/1.0",
    "Accept": "application/json, text/plain, */*",
})

def fetch_page(page: int):
    params = {
        "organization_id": ORG_ID["Texas A&M University"],
        "page": page,
        "term_statuses[]": ["future", "current"],   #"historical" for past syllabi
    }

    r = session.get(SEARCH_URL, params=params)
    r.raise_for_status()
    data = r.json()
    return data

def clean_item(item) -> str:

    return (
        item["code"],
        item["title"],
        item["sub_title"],
        item["entity_id"],
        ",".join([e["full_name"] for e in item["editors"]]),
    )

def fetch_items():
    first = fetch_page(0)
    total = first["pagination"]["total"]
    page_size = first["pagination"]["page_size"]
    num_pages = math.ceil(total / page_size)

    total_retrieved = len(first["items"])
    
    print(f"Total syllabi: {total}, pages: {num_pages}")
    for page in range(1, num_pages):
        data = fetch_page(page)
        cleaned = [clean_item(i) for i in data["items"]]
        total_retrieved += len(cleaned)
        
        print(f"Fetched page {page}, total items: {total_retrieved}")
        
        
      
        cur.executemany("""
            INSERT INTO syllabi_list (code, title, subtitle, course_id, editors)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                subtitle = EXCLUDED.subtitle,
                course_id = EXCLUDED.course_id,
                editors = EXCLUDED.editors
        """, cleaned)
        #time.sleep(0.2) # rate limiting
        conn.commit()



if __name__ == "__main__":
    # fetch_items()
    pass

conn.close()


## TAMU GRAD DIST URL
"https://anex.us/grades/?dept=CSCE&number=470"