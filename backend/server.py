from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from db_utils import get_db, get_dept_codes

from search_engine import tokenize, BM25FIndex, SyllySearch, demo_engine, parse_query, load_from_db




from dotenv import load_dotenv
import os

cache = "index.pkl"
eng = None
idx = None

load_dotenv()

def load_engine():
    if os.path.exists(cache):
        print("loading engine from cache")
        return SyllySearch.load(cache)

    else:
        print("generating engine index from database")
        engine = SyllySearch(*load_from_db(os.getenv("DATABASE_URL")))
        print("saving index to cache")
        engine.save(cache)
        return engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    global eng, idx
    eng = load_engine()
    idx = eng.index
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
def get_app_health(db = Depends(get_db)):
    return {"status": "ok"}

@app.get("/depts")
def get_depts(db = Depends(get_db)):
    """Gets department codes"""
    return get_dept_codes(db)

@app.get("/syllabi")
def get_num_syllabi(db = Depends(get_db)):
    """Returns the number of syllabi in the database"""
    cur = db.cursor()
    cur.execute("""SELECT COUNT(*) FROM syllabi""")
    count = cur.fetchone()[0]
    return count

@app.get("/index_stats")
def get_index_stats():
    num_docs = len(idx.docs)
    num_terms = len(idx.postings)
    avg_field_len = {k: round(v, 2) for k, v in idx.avg_len.items()}

    return {
        "docs": num_docs,
        "terms": num_terms,
        "avg_field_len": avg_field_len
    }

@app.get("/query")
def query(query_text: str):
    return eng.search(query_text)

if __name__ == "__main__":
    if not os.path.exists(cache):
        load_engine()
    uvicorn.run("server:app", port=8080, reload=True)