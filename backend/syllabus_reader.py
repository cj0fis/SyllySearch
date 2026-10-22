import requests
import json

from bs4 import BeautifulSoup

EXCLUDED_SECTIONS = [
        "Late Work Policy",
        "AI Statement",
        "Technology Support",
        "University Policies",
        "Academic Integrity Statement and Policy",
        "University Attendance Policy",
        "Notice of Nondiscrimination",
        "Civil Rights, Free Speech, and Title IX Policies",
        "Americans with Disabilities Act (ADA) Policy",
        "Pregnancy Accommodations",
        "Statement on Mental Health and Wellness",
        "Statement on the Family Educational Rights and Privacy Act (FERPA)",
        "Free Speech and Civil Discourse",
        "College and Department Policies",
        "Special Course Designation",
    ]

def get_doc_data(code: str) -> dict:
    url = "https://tamu.simplesyllabus.com/api2/doc-full-page-get"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
    }
    resp = requests.get(url, headers=headers, params={"code": code})
    resp.raise_for_status()
    return resp.json()["items"][0]["doc_data"]

def parse_title(title: str):
    return {
        "dept_code": title[0:4],
        "course_num": title[5:8],
        "section_num": title[9:12]
    }

def process_term(term_data):
    """
    Reads the data from a term dict.
    checks if it is in the database, if not, this adds it.
    """
    pass

def process_editors(editor_list):
    """
    Reads an editor list.
    gets the instructors that are part of the course
    updates the instructors database if they aren't already part of it.
    """
    pass

def extract_section_from_component(component: dict):
    """
    Given one component dict from the components list, return a dict:
      {
        "name": section heading or None,
        "type": component_type,
        "text": plain text,
      }
    """
    html = component.get("html", "") or ""
    soup = BeautifulSoup(html, "html.parser")

    # Section name: <h2 class="component-name"> ... </h2>
    h2 = soup.select_one("h2.component-name")
    name = h2.get_text(strip=True) if h2 else None

    # Main editor body: <div class="fr-view" ...> ... </div>
    fr_view = soup.select_one("div.fr-view")
    if fr_view:
        text = fr_view.get_text(separator="\n", strip=True)
    else:
        # Fallback if no fr-view (rare)
        text = soup.get_text(separator="\n", strip=True)

    return {
        "name": name,
        "type": component.get("component_type"),
        "text": text,
    }

def process_html_components(html):
    
    sections = [extract_section_from_component(c) for c in html ]
    sections = [s for s in sections if (not s["name"] or s["name"] not in EXCLUDED_SECTIONS)]

    for s in sections:
        print("====", s["name"] or "(no name)", "====")
        print(s["text"][:500], "\n")

def extract_data(doc_data: dict):
    code = doc_data["code"]
    created = doc_data["created"]
    
    entity_id = doc_data["entity_id"]

    #TODO: save this to database
    title = doc_data["title"]
    dept_code = title[0:4]
    course_num = title[5:8]
    section_num = title[9:12]

    sub_title = doc_data["sub_title"]

    #TODO: parse and save this to database if it isn't already there
    term_data = doc_data["term"]
    process_term(term_data)

    term_id = doc_data["term_id"]
        # if term_id in database:
        #   set foreign key to term_id

    editor_list = doc_data["editors"]
    process_editors(editor_list)

    html_components = doc_data["components"]
    process_html_components(html_components)


    

if __name__ == "__main__":
    doc_data = get_doc_data("ldvj580dy")

    extract_data(doc_data)
    

    # print(json.dumps(doc_data,indent=2))
    # print()
    # print(doc_data["doc_data"].keys())
    