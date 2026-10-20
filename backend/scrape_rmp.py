import sqlite3
import time
from rmp_client import RMPClient
# https://github.com/amaanjaved1/Rate-My-Professors-API-Client-Python

DB_PATH = "syllabi.db"
SCHOOL_ID = "1003" # corresponding to "Texas A&M University at College Station"

# pull unique professor (editor) names from syllabi db
def get_professor_names(conn):
    rows = conn.execute("SELECT editors FROM syllabi WHERE editors IS NOT NULL").fetchall()

    names = set()

    for (editors,) in rows:
        for name in editors.split(","):
            name = name.strip()
            if name:
                names.add(name)

    return names

def create_table():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("""
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

        conn.executemany("""
            INSERT OR REPLACE INTO rmp (
                professor_id,
                name,
                department,
                overall_rating,
                num_ratings,
                percent_take_again,
                difficulty
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
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