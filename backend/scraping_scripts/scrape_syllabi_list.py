import math
import requests


import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


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

def process_editors(editors: list[dict], syllabus_id: str):
    """
    Adds the editor to the database if it isn't already there
    returns rows for the instructors_syllabi junction table
    """

    ## add row to instructors database. email will be added later, but that info is not available now
    editor_rows = [(e["entity_id"], e["first_name"], e["last_name"]) for e in editors]
    cur.executemany("""
        INSERT INTO instructors (entity_id, first_name, last_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (entity_id) DO NOTHING
    """, editor_rows)

    return [(syllabus_id, e["entity_id"]) for e in editors]


def parse_title(title: str):
    parts = title.split()

    return {
        "dept_code": parts[0],
        "course_num": parts[1],             # Also not a number sometimes. one row has this as "test" ???
        "section_num": parts[2],            # This isn't always a number for some reason. sometimes it is M90
        "course_id": int(parts[3].strip("()"))
    }

def add_dept_codes(dept_codes: set[str]):
    """
    Checks if each code is in the enum. If not, id adds the code to the enum
    """
    for code in dept_codes:
        cur.execute("""
            SELECT 1
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname = 'dept_code' AND e.enumlabel = %s
        """, (code,))
        exists = cur.fetchone() is not None
        if not exists:
            # type name is constant and trusted
            cur.execute("ALTER TYPE dept_code ADD VALUE %s", (code,))
            print(f"[ADDED CODE]: {code}")
    conn.commit()

def process_items(items) -> int:
    processed = []
    junc = []
    dept_codes = set()

    for item in items:
        ## add editors to database
        junc_rows = process_editors(item["editors"], item["entity_id"])
        junc.extend(junc_rows)

        ## get course info 
        course_info = parse_title(item["title"])
        if course_info["dept_code"] not in dept_codes:
            dept_codes.add(course_info["dept_code"])

        processed.append( (
            item["entity_id"],
            item["code"],
            item["title"],
            item["sub_title"],
            course_info["dept_code"],
            course_info["course_num"],
            course_info["section_num"],
            course_info["course_id"],
            item["term_id"],
        ) )

    ## add dept codes to enum
    add_dept_codes(dept_codes)

    ## add syllabi to database
    cur.executemany("""
        INSERT INTO syllabi (entity_id, code, title, subtitle, dept, course_number, section_number, course_id, term_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (entity_id) DO UPDATE SET
            code = EXCLUDED.code,
            title = EXCLUDED.title,
            subtitle = EXCLUDED.subtitle,
            dept = EXCLUDED.dept,
            course_number = EXCLUDED.course_number,
            section_number = EXCLUDED.section_number,
            course_id = EXCLUDED.course_id
            term_id = EXCLUDED.term_id
            
    """, processed)

    cur.executemany("""
            INSERT INTO instructors_syllabi (syllabus_id, instructor_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, junc)
    #time.sleep(0.2) # rate limiting
    conn.commit()

    return len(items)

def update_terms(items) -> int:
    processed = [(
        e["term_id"],
        e["entity_id"]
    ) for e in items]
    cur.executemany("""
        UPDATE syllabi
        SET term_id = %s
        WHERE entity_id = %s 
        """, processed)
    conn.commit()
    return len(items)

def fetch_items():
    first = fetch_page(0)
    # process_items(first["items"])

    total = first["pagination"]["total"]
    page_size = first["pagination"]["page_size"]
    num_pages = math.ceil(total / page_size)

    total_retrieved = 0
    print(f"Total syllabi: {total}, pages: {num_pages}")
    print()

    
    for page in range(0, num_pages):
        data = fetch_page(page)
        
        #num_processed = process_items(data["items"])
        num_processed = update_terms(data["items"])
        total_retrieved += num_processed
        
        print(f"Fetched page {page}, total items: {total_retrieved}")
        
        



if __name__ == "__main__":
    fetch_items()
    

conn.close()


## TAMU GRAD DIST URL
"https://anex.us/grades/?dept=CSCE&number=470"