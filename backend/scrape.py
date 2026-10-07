import math
import json
import time
import requests

from bs4 import BeautifulSoup

## this is just for the college of engineering
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

    return {
        "code": item["code"],
        "title": item["title"],
        "subtitle": item["sub_title"],
        #"term_name": item["term_name"],
        "editors": [e["full_name"] for e in item["editors"]],
    }

    return items

def fetch_all_codes():
    first = fetch_page(0)
    total = first["pagination"]["total"]
    page_size = first["pagination"]["page_size"]
    num_pages = math.ceil(total / page_size)

    codes = [i["code"] for i in first["items"]]

    for page in range(1, num_pages):
        data = fetch_page(page)
        codes.extend([i["code"] for i in data["items"]])
        print(f"Fetched page {page}, total items: {len(codes)}")
        time.sleep(0.2)

    with open("codes.json", "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)

def fetch_items(org_id: str, max_items: int = -1, max_pages: int = -1):
    first = fetch_page(0)
    total = first["pagination"]["total"]
    page_size = first["pagination"]["page_size"]
    num_pages = math.ceil(total / page_size)

    items = [clean_item(i) for i in first["items"]]
    print(f"Total syllabi: {total}, pages: {num_pages}")
    for page in range(1, num_pages):
        data = fetch_page(page)
        cleaned = [clean_item(i) for i in data["items"]]
        items.extend(cleaned)
        print(f"Fetched page {page}, total items: {len(items)}")
        time.sleep(0.2) # rate limiting

    with open("syllabus_index.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


# with open("syllabus_index.json", "r", encoding="utf-8") as f:
#     DOC_URL = ""
    
#     items = json.load(f)
#     for item in items:
#         code = item["code"]

def fetch_full_doc(code: str):
    params = {
        "code": code
    }
    r = session.get(DOC_URL, params=params)
    r.raise_for_status()
    return r.json()



if __name__ == "__main__":
    example_code = "h8cy5hqed"
    # data = fetch_full_doc(example_code)
    # print(json.dumps(data, indent=2))

    fetch_all_codes()