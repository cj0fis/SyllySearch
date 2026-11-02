import psycopg2
import os
import json
from dotenv import load_dotenv
# https://github.com/amaanjaved1/Rate-My-Professors-API-Client-Python
from rmp_client import RMPClient

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SCHOOL_ID = "1003" # corresponding to "Texas A&M University at College Station"

# pull unique professor (editor) names from syllabi db
def get_professor_names(conn):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT first_name, last_name 
        FROM instructors 
        WHERE first_name IS NOT NULL OR last_name IS NOT NULL""")
        rows = cur.fetchall()

    names = set()

    # assuming pattern is first_name " " last_name
    for (first_name, last_name) in rows:
        name = " ".join(
            part.strip()
            for part in (first_name or "", last_name or "")
            if part and part.strip()
        )

        if name:
            names.add(name)

    return names

def create_table():
    conn = psycopg2.connect(DATABASE_URL)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS rmp (
                    professor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT,
                    overall_rating REAL,
                    num_ratings INTEGER,
                    percent_take_again REAL,
                    difficulty REAL
                )
            """)
        conn.commit()

        syllabus_names = get_professor_names(conn)
        print(f"Pulling {len(syllabus_names)} names from syllabi.db...")
        prof_dict = {}

        # use RMP-client to find corresponding RMP pages based on EXACT professor name
        # if professors share name, both are added to the results (should we change this?)
        # later maybe need to consider issue of alias/nicknames
        # ex: Christopher Menzel in syllabi.db corresponds to professor Chris Menzel in RMP (but EXACT match will fail this)
        with RMPClient() as client:
            for professor in client.iter_professors_for_school(SCHOOL_ID, page_size = 50):
                # syllabi don't have corresponding professor_id, so can only use name to match
                key = professor.name.strip().casefold()

                # Record professors with the same name (possible to have shared names)
                prof_dict.setdefault(key, []).append(professor)

        # Match the names from syllabi collection to names found via RMP
        matched_ids = set()
        unmatched_names = []
        rows_to_insert = []

        for name in syllabus_names:
            matches = prof_dict.get(name.strip().casefold(), [])

            if not matches:
                unmatched_names.append(name)
                continue

            for professor in matches:
                professor_id = str(professor.id)

                # Only add unique professor_id
                if professor_id in matched_ids:
                    continue

                matched_ids.add(professor_id)

                rows_to_insert.append((
                    professor_id,
                    professor.name,
                    professor.department,
                    professor.overall_rating,
                    professor.num_ratings,
                    professor.percent_take_again,
                    professor.level_of_difficulty,
                ))

        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO rmp (
                    professor_id,
                    name,
                    department,
                    overall_rating,
                    num_ratings,
                    percent_take_again,
                    difficulty
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (professor_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    department = EXCLUDED.department,
                    overall_rating = EXCLUDED.overall_rating,
                    num_ratings = EXCLUDED.num_ratings,
                    percent_take_again = EXCLUDED.percent_take_again,
                    difficulty = EXCLUDED.difficulty
            """, rows_to_insert)
        conn.commit()
        print(f"Finished inserting {len(rows_to_insert)} professor records into the rmp table.")

        # Unmatched names (name in syllabi that did not find RMP page) go here just in case
        with open("unmatched_professors.json", "w", encoding="utf-8") as f:
            import json
            json.dump(sorted(unmatched_names), f, indent = 2)

    finally:
        conn.close()

if __name__ == "__main__":
    create_table()