import json
import time

import psycopg2
from dotenv import load_dotenv
import os

import requests

load_dotenv()

session = requests.Session()
session.headers.update({
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest"
  })

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


GRADE_URL = "https://anex.us/grades/getData/"

def get_grade_dist(dept: str, num: str):
    """Gets the grade distributions for one class"""
    data = {
        "dept": dept,
        "number": num
    }
    try:
        r = session.post(GRADE_URL, data=data)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as e: 
        print(f"[WARN] ConnectionError on {dept} {num}, {e}")
        time.sleep(5)
        return []
    try:
        data = r.json()
    except:
        return []
    dist = []
    for c in data["classes"]:
        prof = c["prof"].split()
        #print(prof)
        cd = {
            "section" : c["section"],
            "last_name" : prof[0],
            "first_initial" : prof[1] if len(prof) > 1 else "",
            "year" : c["year"],
            "semester" : c["semester"],
            "gpa" : c["gpa"]
        }

        # print(f"({cd["section"]}, {cd["semester"]} {cd["year"]}, {cd["last_name"]} {cd["first_initial"]}, {cd["gpa"]})")
        dist.append(cd)

    return dist

def get_course_list():
    """Returns all unique pairs of (dept_code, course_number) found in the syllabi table"""

    cur.execute("""
        SELECT DISTINCT dept, course_number
        FROM syllabi
        ORDER BY dept, course_number;
    """)

    return cur.fetchall()

def print_grades(grade_dist: list[dict], dept_code, course_num):
    print("=====", dept_code, course_num, "=====")
    for g in grade_dist:
        name_width = 15
        full_name = (g["last_name"] + " " + g["first_initial"])[:name_width]
        full_name += " " * (name_width - len(full_name))

        term_width = 6
        full_term = (g["semester"])[:term_width]
        full_term += " " * (term_width - len(full_term))
        full_term += " " + g["year"]

        print(f"{g["section"]} {full_name} {full_term} {g["gpa"]}")

def save_grades(grade_dist: list[dict], dept_code, course_num):
    rows = [(
        dept_code,
        course_num,
        g["section"],
        g["last_name"],
        g["first_initial"],
        g["semester"],
        g["year"],
        g["gpa"]
        ) for g in grade_dist]
    cur.executemany("""
        INSERT INTO grade_distributions (dept, course_number, section_number, last_name, first_initial, semester, year, gpa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(dept, course_number, section_number, last_name, first_initial, semester, year) DO NOTHING
        """, rows)

    #conn.commit()
    print(f"[{dept_code} {course_num}] Saved {len(grade_dist)} grades")

if __name__ == "__main__":
    course_list = get_course_list()
    print(f"Found {len(course_list)} courses. Getting grades...")
    
    # limit = 1
    
    start = 100
    i = start
    uncommited = 0
    for dept, course_num in course_list[start:]:
        data = get_grade_dist(dept, course_num)
        print(i, end=' ')
        save_grades(data, dept, course_num)
        uncommited += len(data)

        if i % 20 == 0:
            conn.commit()
            print(f"Committed {uncommited} grades")
            uncommited = 0
            
        #print_grades(data, dept, course_num)
        # limit -= 1
        # if limit == 0:
        #     break
        i += 1