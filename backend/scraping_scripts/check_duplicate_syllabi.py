"""
Checks:
  1. Repeated entity_id or code
  2. Same term + CRN (course_id) (I also have it ignoring template/test placeholders)
  3. Same term + dept + course + section + identical instructor set
  4. Duplicate rows in instructors_syllabi

Usage (from backend/): python3 check_duplicate_syllabi.py
"""
import os
import json
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Template/test placeholders (e.g. "A&S Test 000 001", CRN 1) are not real classes
NOT_TEST = "NOT (s.course_number = '000' OR s.course_id < 100)"

CHECKS = {
    "repeated_entity_id": """
        SELECT entity_id, COUNT(*) AS n FROM syllabi
        GROUP BY entity_id HAVING COUNT(*) > 1
    """,
    "repeated_code": """
        SELECT code, COUNT(*) AS n FROM syllabi
        GROUP BY code HAVING COUNT(*) > 1
    """,
    "same_term_and_crn": f"""
        SELECT s.term_id, s.course_id, COUNT(*) AS n,
               array_agg(s.entity_id) AS entity_ids
        FROM syllabi s
        WHERE {NOT_TEST}
        GROUP BY s.term_id, s.course_id
        HAVING COUNT(*) > 1
    """,
    "same_section_same_instructors": f"""
        WITH x AS (
            SELECT s.entity_id, s.term_id, s.dept::text AS dept,
                   s.course_number, s.section_number, s.course_id,
                   string_agg(isy.instructor_id, ',' ORDER BY isy.instructor_id) AS inst_set
            FROM syllabi s
            JOIN instructors_syllabi isy ON isy.syllabus_id = s.entity_id
            WHERE {NOT_TEST}
            GROUP BY s.entity_id, s.term_id, s.dept, s.course_number,
                     s.section_number, s.course_id
        )
        SELECT term_id, dept, course_number, section_number, inst_set,
               COUNT(*) AS n, array_agg(course_id) AS crns,
               array_agg(entity_id) AS entity_ids
        FROM x
        GROUP BY term_id, dept, course_number, section_number, inst_set
        HAVING COUNT(*) > 1
    """,
    "duplicate_junction_rows": """
        SELECT syllabus_id, instructor_id, COUNT(*) AS n
        FROM instructors_syllabi
        GROUP BY syllabus_id, instructor_id
        HAVING COUNT(*) > 1
    """,
}


def main():
    load_dotenv()
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT COUNT(*) AS n FROM syllabi")
    total = cur.fetchone()["n"]
    print(f"Checked {total} syllabi\n")

    results = {}
    for name, sql in CHECKS.items():
        cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        results[name] = rows
        print(f"{name}: {len(rows)} group(s)")
        for r in rows:
            print("   ", r)

    with open("duplicate_syllabi.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nWrote duplicate_syllabi.json")
    conn.close()


if __name__ == "__main__":
    main()