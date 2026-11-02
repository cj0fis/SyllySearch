
"""
Populate rmp.dept using the departments of an instructor's syllabi.

If an instructor has exactly one unique syllabus department:
    rmp.dept = syllabi.dept

If no syllabi or multiple departments:
    Leave rmp.dept as NULL.

Existing non-NULL rmp.dept values are not modified.

Usage:
    python3 backend/add_dept_rmp.py
"""

import os
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv


def main():
    load_dotenv()

    DATABASE_URL = os.environ["DATABASE_URL"]

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # 1. Retrieve instructor IDs and syllabus departments
        cur.execute("""
            SELECT
                isy.instructor_id,
                s.dept::text
            FROM instructors_syllabi isy
            JOIN syllabi s
                ON isy.syllabus_id = s.entity_id
            WHERE s.dept IS NOT NULL
        """)

        rows = cur.fetchall()

        # 2. Build dictionary: instructor_id -> set of departments
        instructor_depts = defaultdict(set)

        for instructor_id, dept in rows:
            instructor_depts[instructor_id].add(dept)

        # 3. Retrieve RMP professors
        cur.execute("""
            SELECT
                professor_id,
                name,
                instructor_id,
                dept::text
            FROM rmp
        """)

        rmp_rows = cur.fetchall()

        matches = []

        matched = 0
        unmatched = 0
        ambiguous = 0
        already_filled = 0

        # 4. Determine each professor's department
        for (
            professor_id,
            name,
            instructor_id,
            current_dept
        ) in rmp_rows:

            # Do not overwrite existing departments
            if current_dept is not None:
                already_filled += 1
                continue

            syllabus_depts = instructor_depts.get(
                instructor_id, set()
            )

            if len(syllabus_depts) == 1:
                dept = next(iter(syllabus_depts))

                matches.append((dept, professor_id))
                matched += 1

            elif len(syllabus_depts) == 0:
                unmatched += 1

            else:
                ambiguous += 1

        # 5. Update Supabase
        total = len(matches)

        print(f"Updating {total} RMP departments...", flush=True)

        for i, (dept, professor_id) in enumerate(matches, start=1):
            cur.execute("""
                UPDATE rmp
                SET dept = %s::dept_code
                WHERE professor_id = %s
                  AND dept IS NULL
            """, (dept, professor_id))

            if i % 100 == 0 or i == total:
                print(
                    f"Updated {i}/{total} departments",
                    flush=True
                )

        conn.commit()

        print("Database updated successfully!")

        # 6. Print summary
        print("\n===== RMP DEPARTMENT MATCHING =====")
        print(f"Total RMP professors: {len(rmp_rows)}")
        print(f"Matched: {matched}")
        print(f"Unmatched: {unmatched}")
        print(f"Ambiguous: {ambiguous}")
        print(f"Already filled: {already_filled}")

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
