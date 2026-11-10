"""
split into 3 stages
stage 0: pull dept / level filters + intent ("easy", "good", ...) out of the query
Stage 1: field-weighted BM25 over syllabus text, subtitle, course code
Stage 2: weighted sum of normalised BM25F + RMP rating + RMP difficulty + avg GPA

Usage
    python search_engine.py --demo # runs a small demo with fake data for testing
    python search_engine.py "easy 300 level csce course" # builds from Supabase (needs .env)
"""
import math
import os
import pickle
import re
import sys
from collections import Counter, defaultdict
from difflib import get_close_matches

 
# Tokenising
TOKEN_RE = re.compile(r"[a-z0-9]+")
CODE_RE = re.compile(r"\b([a-z]{3,4})[\s-]?(\d{3})\b")
STOP = {"a", "an", "and", "the", "of", "to", "in", "for", "on", "is", "with",
        "at", "by", "or", "this", "that", "be", "are", "as", "from", "will", "you"}

# Abbreviations
ABBREVIATIONS = {
    "info": "information",
    "intro": "introduction",
    "introductory": "introduction",
    "adv": "advanced",
    "fund": "fundamentals",
    "princ": "principles",
    "gen": "general",
    "appl": "application",
    "dev": "development",
    "intl": "international",
    "comp": "computer",
    "comput": "computing",
    "sys": "system",
    "syst": "system",
    "systs": "system",
    "db": "database",
    "dbms": "database",
    "netwk": "network",
    "netw": "network",
    "prog": "programming",
    "alg": "algorithm",
    "algo": "algorithm",
    "archit": "architecture",
    "tech": "technology",
    "technol": "technology",
    "engr": "engineering",
    "engrg": "engineering",
    "elec": "electrical",
    "elect": "electrical",
    "mech": "mechanical",
    "mfg": "manufacturing",
    "aero": "aerospace",
    "environ": "environmental",
    "mgmt": "management",
    "mgt": "management",
    "acct": "accounting",
    "fin": "financial",
    "admin": "administration",
    "econ": "economics",
    "orgnl": "organizational",
    "calc": "calculus",
    "geom": "geometry",
    "probab": "probability",
    "stats": "statistics",
    "stat": "statistics",
    "chem": "chemistry",
    "phys": "physics",
    "biol": "biology",
    "astro": "astronomy",
    "psych": "psychology",
    "sociol": "sociology",
    "hist": "history",
    "govt": "government",
    "lit": "literature",
    "philos": "philosophy",
    "educ": "education",
}

# light stemming on plurals
# queries varying by plurality shouldn't return significantly different results
# ex: "databases" vs "database"
def stem(tok):
    # don't touch very small tokens or class codes
    if len(tok) <= 3 or any(c.isdigit() for c in tok):
        return tok
    if tok.endswith("ies") and len(tok) > 4:
        return tok[:-3] + "y"
    if tok.endswith(("ss", "us", "is")):
        return tok
    if tok.endswith("zzes"):
        return tok[:-3] 
    if tok.endswith(("sses", "xes", "ches", "shes")):
        return tok[:-2] 
    if tok.endswith("s"):
        return tok[:-1] # databases, structures, algorithms
    return tok

def tokenize(text):
    """
    Lowercases, strips stop words, extracts regular tokens, and fuses course codes
    Returns:
        list of tokens
    """
    text = (text or "").lower()

    # Expand abbreviations before stemming
    toks = [stem(ABBREVIATIONS.get(t, t)) for t in TOKEN_RE.findall(text) if t not in STOP]

    toks += [m.group(1) + m.group(2) for m in CODE_RE.finditer(text)]  # "csce 221" -> "csce221"
    return toks


 
# BM25F: syllabus text, titles and descriptions are scored; dept/instructor/level are filters (change if needed)
FIELD_WEIGHTS = {
    "course_code":  3.0,        # Exact code match is a very strong signal
    "subtitle":     1.5,        # Course name is highly relevant
    "headings":     1.0,        # Structured text, medium weight
    "description":  2.0,        # Section headers
    "body":         1.0         # Full syllabus text, longest, most noise
    }

# Within the body sections, how much are each section weighted?
FIELD_B = {
    "course_code": 0.0,
    "subtitle": 0.3,
    "headings": 0.5,
    "description": 0.6,
    "body": 0.75
    }

K1 = 1.2


class BM25FIndex:
    def __init__(self, weights=None, b=None, k1=K1):
        self.w = weights or FIELD_WEIGHTS
        self.b = b or FIELD_B
        self.k1 = k1
        self.postings = defaultdict(dict)  # term -> {doc_idx: {field: tf}}
        self.field_len, self.avg_len, self.docs = [], {}, []
        self.title_tokens = []
        self.lookup_vocab = set()

    def build(self, docs):
        """docs: list of dicts with the BM25F fields above plus any metadata."""
        totals = Counter()
        for idx, d in enumerate(docs):
            self.title_tokens.append(tokenize(d.get("subtitle", "")))
            self.docs.append(d)
            lens = {}
            for f in self.w:
                toks = tokenize(d.get(f, ""))
                lens[f] = len(toks)
                totals[f] += len(toks)
                for term, tf in Counter(toks).items():
                    self.postings[term].setdefault(idx, {})[f] = tf
                if f in ("subtitle", "description"):
                    self.lookup_vocab.update(toks)
            self.field_len.append(lens)
        n = max(len(docs), 1)
        self.avg_len = {f: (totals[f] / n) or 1.0 for f in self.w}
        return self

    def _idf(self, term):
        n, df = len(self.docs), len(self.postings.get(term, ()))
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query_text, candidates=None, k=250):
        """
        BM25F with typo recovery, query coverage,
        and course subtitle matching.
        """

        query_terms = list(dict.fromkeys(tokenize(query_text)))

        if not query_terms:
            return []

        expanded = []
        corrected = {}

        for term in query_terms:
            if term in self.postings:
                expanded.append((term, term, 1.0))
                corrected[term] = term

            elif len(term) >= 5:
                alternatives = get_close_matches(
                    str(term),
                    [str(word) for word in self.lookup_vocab],
                    n=1,
                    cutoff=0.86
                )

                if alternatives:
                    replacement = alternatives[0]
                    expanded.append((term, replacement, 0.65))
                    corrected[term] = replacement

        scores = defaultdict(float)
        hits = defaultdict(set)

        for original, indexed, factor in expanded:
            plist = self.postings.get(indexed)

            if not plist:
                continue

            idf = self._idf(indexed)

            for idx, tfs in plist.items():
                if candidates is not None and idx not in candidates:
                    continue

                tf_t = sum(
                    self.w[f] * tf / (
                        1 - self.b[f]
                        + self.b[f] * self.field_len[idx][f]
                        / self.avg_len[f]
                    )
                    for f, tf in tfs.items()
                )

                scores[idx] += (
                    factor * idf * tf_t / (self.k1 + tf_t)
                )

                hits[idx].add(original)

        n_terms = len(query_terms)

        for idx in scores:
            coverage = len(hits[idx]) / n_terms

            scores[idx] *= 0.70 + 0.30 * coverage

            title_tokens = self.title_tokens[idx]
            title_set = set(title_tokens)

            title_overlap = sum(
                corrected.get(term) in title_set
                for term in query_terms
            ) / n_terms

            scores[idx] *= 1.0 + 0.30 * title_overlap

            phrase = [
                corrected.get(term, term)
                for term in query_terms
            ]

            if n_terms >= 2 and any(
                title_tokens[pos:pos + n_terms] == phrase
                for pos in range(len(title_tokens) - n_terms + 1)
            ):
                scores[idx] *= 1.35

        ranked = sorted(
            scores.items(),
            key=lambda x: -x[1]
        )

        return ranked if k is None else ranked[:k]


#query parsing
INTENTS = {
    "easy": {"easy", "easiest", "easier", "gpa", "light", "chill", "simple"},
    "hard": {"hard", "hardest", "difficult", "challenging", "rigorous", "tough"},
    "good": {"good", "best", "great", "top", "recommended", "favorite", "amazing"},
}
NOISE = {"level", "course", "courses", "class", "classes", "professor", "prof", "with", "a", "an", "the"}

# bug in which a query would contain a word that: 1) is in STOP, 2) is not in NOISE, 3) isn't an intent, level, dept, course, and 4) no other terms left
# accidently queried "best professor for csce 221" and got nothing
QUERY_IGNORE = STOP | NOISE

def parse_query(q, dept_codes=()):
    """'easy 300 level CSCE course' -> intent=easy, level=3, dept=CSCE, text=''
    'best csce 221 professor' -> intent=good, course=('CSCE', '221'), text=''"""
    ql = q.lower()
    dept_codes = {d.upper() for d in dept_codes}
    out = {"intent": None, "level": None, "dept": None, "course": None, "text": ""}

    # "300 level" always means a level filter (so "math 400 level" is dept=MATH, level=4)
    m = re.search(r"\b([1-6])00[\s-]?(?:level|lvl)\b", ql)
    if m:
        out["level"] = int(m.group(1))
        ql = ql[:m.start()] + " " + ql[m.end():]

    # a real course code ("csce 221") is an exact course filter, not just text
    for m in CODE_RE.finditer(ql):
        if m.group(1).upper() in dept_codes:
            out["course"] = (m.group(1).upper(), m.group(2))
            ql = ql[:m.start()] + " " + ql[m.end():]
            break

    # a leftover bare "300" with no dept in front of it is a level ("easy 300 csce")
    if out["level"] is None:
        m = re.search(r"\b([1-6])00\b", ql)
        if m:
            out["level"] = int(m.group(1))
            ql = ql[:m.start()] + " " + ql[m.end():]

    keep = []
    for t in TOKEN_RE.findall(ql):
        if out["dept"] is None and out["course"] is None and t.upper() in dept_codes:
            out["dept"] = t.upper()  # "csce" alone is a filter
            continue
        hit = next((name for name, words in INTENTS.items() if t in words), None)
        if hit:
            out["intent"] = out["intent"] or hit
            continue
        if t not in QUERY_IGNORE:
            keep.append(t)
    out["text"] = " ".join(keep)
    return out


 
#rerank (w_bm25, w_rating, w_difficulty_signal, w_gpa)
WEIGHTS = {
    "easy": (0.35, 0.10, 0.25, 0.30),
    "hard": (0.35, 0.10, 0.30, 0.25),
    "good": (0.35, 0.40, 0.00, 0.25),
    None:   (0.65, 0.175, 0.00, 0.175),
}
PRIOR_RATING, PRIOR_DIFF, SHRINK_M = 3.5, 3.0, 5  # shrink ratings with few reviews toward the mean


def _shrink(val, n, prior):
    return (n * val + SHRINK_M * prior) / (n + SHRINK_M)


def signals(doc, rmp, grades):
    """Return (rating 0-1, difficulty 0-1, gpa 0-1) averaged over instructors; 0.5 if unknown."""
    rs, ds, gs = [], [], []
    for ins in doc["instructors"]:
        r = rmp.get(ins["id"])
        if r and r["rating"] is not None:
            n = r["n"] or 0
            rs.append(_shrink(r["rating"], n, PRIOR_RATING) / 5)
            if r["difficulty"] is not None:
                ds.append(_shrink(r["difficulty"], n, PRIOR_DIFF) / 5)
        g = grades.get((doc["dept"], str(doc["course_number"]), ins["last"].lower(), ins["first"][:1].lower()))
        if g is None:  # fall back to course + last name
            g = grades.get((doc["dept"], str(doc["course_number"]), ins["last"].lower(), None))
        if g is not None:
            gs.append(g / 4)
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.5
    return mean(rs), mean(ds), mean(gs)


def rerank(scored, docs, intent, rmp, grades, include_full_doc: bool = False):
    if not scored:
        return []
    w_bm, w_r, w_d, w_g = WEIGHTS[intent]
    top = max(s for _, s in scored) or 1.0
    out = []
    for idx, s in scored:
        d = docs[idx]
        rating, diff, gpa = signals(d, rmp, grades)
        diff_sig = (1 - diff) if intent == "easy" else diff  # easy -> low difficulty, hard -> high
        final = w_bm * s / top + w_r * rating + w_d * diff_sig + w_g * (gpa if intent != "hard" else 1 - gpa)
        if not include_full_doc:
            slim = {k: v for k, v in d.items() if k not in ("headings", "body")}
            out.append({"doc": slim, "bm25f": s, "rating": rating, "difficulty": diff, "gpa": gpa, "score": final})
        else:
            out.append({"doc": d, "bm25f": s, "rating": rating, "difficulty": diff, "gpa": gpa, "score": final})
            
    out.sort(key=lambda r: -r["score"])
    seen, deduped = set(), []  # one row per (course, instructors) -- keep the best section/term
    for r in out:
        d = r["doc"]
        key = (d["dept"], str(d["course_number"]), tuple(sorted(i["id"] for i in d["instructors"])))
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


 
# Engine
class SyllySearch:
    def __init__(self, docs, rmp, grades, dept_codes):
        self.docs, self.rmp, self.grades, self.dept_codes = docs, rmp, grades, dept_codes
        self.index = BM25FIndex().build(docs)

    def search(self, query, k=10):
        p = parse_query(query, self.dept_codes)
        cands = {i for i, d in enumerate(self.docs)
                 if (p["course"] is None or (d["dept"], str(d["course_number"])) == p["course"])
                 and (p["dept"] is None or d["dept"] == p["dept"])
                 and (p["level"] is None or str(d["course_number"])[:1] == str(p["level"]))}
        if p["text"]:
            scored = self.index.search(p["text"], candidates=cands)
        else:  # pure filter/intent query like "easy 300 level csce": every filtered doc is a candidate
            scored = [(i, 1.0) for i in cands]
        return p, rerank(scored, self.docs, p["intent"], self.rmp, self.grades)[:k]

    def save(self, path):
        with open(path, "wb") as fh:
            pickle.dump(self, fh)

    @staticmethod
    def load(path):
        with open(path, "rb") as fh:
            return pickle.load(fh)


 
# Supabase loader
def load_from_db(database_url):
    import psycopg2  # imported lazily so --demo works without it
    conn = psycopg2.connect(database_url, options="-c statement_timeout=30000")
    cur = conn.cursor()
    print("loading from database")
    cur.execute("""
        SELECT s.entity_id, s.code, s.dept, s.course_number, s.section_number, s.subtitle, s.sections,
               t.name, i.entity_id, i.first_name, i.last_name
        FROM syllabi s
        LEFT JOIN instructors_syllabi isj ON isj.syllabus_id = s.entity_id
        LEFT JOIN instructors i ON i.entity_id = isj.instructor_id
        LEFT JOIN terms t ON t.entity_id = s.term_id
    """)

    by_id = {}
    for eid, code, dept, num, sec, sub, sections, term, iid, first, last in cur.fetchall():
        d = by_id.get(eid)
        if d is None:
            sections = sections or []  # NULL = not scraped yet; still searchable by code/subtitle
            desc = " ".join(s["text"] for s in sections if "description" in (s.get("name") or "").lower())
            d = by_id[eid] = {
                "id": eid, "code": code, "dept": dept, "course_number": str(num), "section": sec,
                "term": term, "subtitle": sub or "", "course_code": f"{dept} {num}",
                "headings": " ".join(s.get("name") or "" for s in sections),
                "description": desc,
                "body": " ".join(s.get("text") or "" for s in sections),
                "has_text": bool(sections), "instructors": [],
            }
        if iid:
            d["instructors"].append({"id": iid, "first": first or "", "last": last or ""})

    cur.execute("""SELECT instructor_id, professor_id, overall_rating, difficulty, num_ratings
                   FROM rmp WHERE instructor_id IS NOT NULL ORDER BY num_ratings NULLS FIRST""")
    rmp = {iid: {"prof_id": pid, "rating": r, "difficulty": df, "n": n}  # most-reviewed row wins
           for iid, pid, r, df, n in cur.fetchall()}

    cur.execute("""SELECT dept, course_number, lower(last_name), lower(left(first_initial, 1)), AVG(gpa::float)
                   FROM grade_distributions WHERE gpa IS NOT NULL
                   GROUP BY dept, course_number, lower(last_name), lower(left(first_initial, 1))""")
    grades = {(d, str(c), ln, fi or None): g for d, c, ln, fi, g in cur.fetchall()}
    cur.execute("""SELECT dept, course_number, lower(last_name), AVG(gpa::float)
                   FROM grade_distributions WHERE gpa IS NOT NULL GROUP BY dept, course_number, lower(last_name)""")
    for d, c, ln, g in cur.fetchall():
        grades.setdefault((d, str(c), ln, None), g)

    cur.execute("""SELECT e.enumlabel FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid
                   WHERE t.typname = 'dept_code'""")
    dept_codes = [r[0] for r in cur.fetchall()]
    conn.close()
    return list(by_id.values()), rmp, grades, dept_codes


 
# Demo data for testing
def demo_engine():
    def mk(i, dept, num, sub, body, ins, desc=""):
        return {"id": i, "dept": dept, "course_number": num, "subtitle": sub, "course_code": f"{dept} {num}",
                "headings": "Course Description Grading", "description": desc, "body": body,
                "instructors": [{"id": ins[0], "first": ins[1], "last": ins[2]}], "term": "Spring 2027", "section": "500"}
    docs = [
        mk(1, "CSCE", "221", "DATA STRUCTURES", "linked lists trees graphs sorting exams", ("a", "John", "Smith"), "data structures"),
        mk(2, "CSCE", "221", "DATA STRUCTURES", "linked lists trees graphs weekly quizzes", ("b", "Jane", "Doe"), "data structures"),
        mk(3, "CSCE", "314", "PROGRAMMING LANGUAGES", "functional programming haskell exams", ("c", "Sam", "Lee")),
        mk(4, "CSCE", "121", "INTRO PROGRAM DESIGN", "python loops functions projects", ("b", "Jane", "Doe")),
        mk(5, "MATH", "251", "ENGINEERING MATH III", "vector calculus homework exams", ("d", "Ann", "Wu")),
        mk(6, "CSCE", "315", "PROGRAMMING STUDIO", "software design team projects", ("a", "John", "Smith")),
    ]
    rmp = {"a": {"rating": 2.8, "difficulty": 4.2, "n": 60}, "b": {"rating": 4.8, "difficulty": 2.1, "n": 80},
           "c": {"rating": 4.0, "difficulty": 3.5, "n": 30}, "d": {"rating": 3.5, "difficulty": 3.0, "n": 10}}
    grades = {("CSCE", "221", "smith", "j"): 2.9, ("CSCE", "221", "doe", "j"): 3.7, ("CSCE", "314", "lee", "s"): 3.3,
              ("CSCE", "121", "doe", "j"): 3.8, ("CSCE", "315", "smith", "j"): 3.0}
    return SyllySearch(docs, rmp, grades, ["CSCE", "MATH", "ENGL"])


def show(engine, q):
    p, res = engine.search(q)
    print(f"\n> {q}\n  parsed: {p}")
    for r in res:
        d, i = r["doc"], r["doc"]["instructors"][0]
        print(f"  {d['course_code']:9} {d['subtitle'][:24]:24} {i['first'][:1]}. {i['last']:6} "
              f"score={r['score']:.3f} bm25f={r['bm25f']:.2f} rate={r['rating']:.2f} gpa={r['gpa']:.2f}")


def debug_course(engine, query, dept, course_number):
    parsed, results = engine.search(query, k=len(engine.docs))

    print(f"\nQuery: {query}")
    print(f"Parsed: {parsed}")
    print(f"Retrived ranked results count: {len(results)}")

    print(f"\n===== {dept} {course_number} FINAL RANK =====")

    found = False

    for rank, result in enumerate(results, start=1):
        doc = result["doc"]

        if (
            str(doc["dept"]).upper() == str(dept).upper()
            and str(doc["course_number"]) == str(course_number)
        ):
            found = True

            print(f"Course: {doc['course_code']}")
            print(f"Subtitle: {doc['subtitle']}")
            print(f"Final Rank: {rank}")
            print(f"Final Score: {result['score']:.6f}")
            print(f"BM25F Score: {result['bm25f']:.6f}")
            print(f"Professor Rating: {result['rating']:.6f}")
            print(f"GPA: {result['gpa']:.6f}")

    if not found:
        print("Course not found in retrived ranked results.")

    print("\n===== TOP 10 SEARCH RESULTS =====")

    for rank, result in enumerate(results[:10], start=1):
        doc = result["doc"]

        print(
            f"{rank}. {doc['course_code']} - "
            f"{doc['subtitle']} "
            f"(Score: {result['score']:.6f})"
        )


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--demo":
        eng = demo_engine()
        for q in ["easy 300 level csce course", "best csce 221 professor", "hard csce", "data structures"]:
            show(eng, q)
    else:
        
        cache = "index.pkl"
        if os.path.exists(cache):
            eng = SyllySearch.load(cache)
        else:
            from dotenv import load_dotenv
            load_dotenv()
            eng = SyllySearch(*load_from_db(os.getenv("DATABASE_URL")))
            eng.save(cache) 
        show(eng, " ".join(args))