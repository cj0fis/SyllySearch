import json

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
    data = {
        "dept": dept,
        "number": num
    }
    r = session.post(GRADE_URL, data=data)
    r.raise_for_status()
    data = r.json()

    dist = []
    for c in data["classes"]:
        prof = c["prof"].split()
        cd = {
            "section" : c["section"],
            "last_name" : prof[0],
            "first_initial" : prof[1],
            "year" : c["year"],
            "semester" : c["semester"],
            "gpa" : c["gpa"]
        }

        # print(f"({cd["section"]}, {cd["semester"]} {cd["year"]}, {cd["last_name"]} {cd["first_initial"]}, {cd["gpa"]})")
        dist.append(cd)

    return dist

if __name__ == "__main__":
    data = get_grade_dist("CSCE", "470")
    #print(json.dumps(data, indent=2))