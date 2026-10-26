import psycopg2
from dotenv import load_dotenv
import os

from scrape_grade_dist import get_grade_dist

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


def get_dept_codes() -> list[str]:
    """
    Returns all department codes from the postgres database
    """
    cur.execute("""
        SELECT e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON e.enumtypid = t.oid
        WHERE t.typname = 'dept_code'
        ORDER BY e.enumsortorder
    """)

    dept_codes = [row[0] for row in cur.fetchall()]
    return dept_codes

def get_syllabi(dept_code: str, course_num: str) -> list[str]:
    """
    Given a course code and number (e.g. CSCE 221),
    Returns all rows that match that query
    """
    sql = """
        SELECT
                
                s.code,
                s.dept,
                s.course_number,
                s.section_number,
                s.subtitle,
                
                i.first_name,
                i.last_name,
                t.name
            FROM syllabi AS s
            LEFT JOIN instructors_syllabi AS isj
            ON isj.syllabus_id = s.entity_id
            LEFT JOIN instructors AS i
            ON i.entity_id = isj.instructor_id
            LEFT JOIN terms as t
            ON t.entity_id = s.term_id
            WHERE s.dept = %s
            AND s.course_number = %s
            ORDER BY s.section_number, s.entity_id, i.last_name;
    """
    cur.execute(sql, (dept_code, course_num))

    rows = cur.fetchall()
    # for row in rows:
    #     print(row)

    return rows
if __name__ == "__main__":
    # codes = get_dept_codes()
    # print(len(codes))

    dept = "CSCE"
    num = "221"
    syllabi = get_syllabi(dept, num)
    grade_dists = get_grade_dist(dept, num)

    # for s in syllabi:
    #     last_name = s[6].lower()
    #     section = s[3]
    #     print(s)
    #     for d in grade_dists: 
    #         if str(d["section"]) == section and d["last_name"].lower() == last_name:
    #             print(f"\tTERM: {d["semester"]} {d["year"]}  \t GPA: {d["gpa"]}")

    print("===== Available Syllabi =====\n")
    for s in syllabi:
        print(s)
    
    print("\n===== Available Grade Distributions =====\n")
    for g in grade_dists:
        print(g)
    