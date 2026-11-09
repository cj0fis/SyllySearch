from search_engine import SyllySearch, debug_course

eng = SyllySearch.load("index.pkl")

debug_course(
    eng,
    query="information system",
    dept="CSCE",
    course_number="470"
)