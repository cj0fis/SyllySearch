
# SyllySearch: Checkpoint 2 (Core Algorithm Demo)


SyllySearch is a search engine for TAMU course syllabi. Given a natural language query such as
`easy 300 level csce course` or `best professor for csce 221`, it ranks course sections using syllabi content,
instructor ratings from RMP, and historical grade data from anex.us.

This release contains the core ranking algorithm and a demo.

- `search_engine.py`: the core algorithm: tokenizing, query parsing, BM25F indexing, reranking
- `test_index.py`: test script that checks the algorithm on a small fake dataset

## Setup

- Python 3.9 or newer
- No 3rd party dependencies


## The algorithm

First, query parsing is performed. It pulls structure out of the query, such as intent, course level, department, or an explicit course code.

Next, there is retrieval. The parsed filters help narrow down the candidate set. The remaining query text (after parsing) are scored against the candidate syllabi using BM25F. Several fields (course code, subtitle, heading, description, body) are included in the BM25F calculation, each with their own weight and length normalization.

Finally, there is the rerank. The BM25F score is combined in a weighted sum with instructor RMP signals (rating, difficulty) and the average GPA from grade distributions. The weights vary based on query intent. This process reranks the syllabi so that the overall ranking involves the BM25F performance, the instructor's general rating, and the average GPA of the course's grade distribution.


## How to run

1. Run the test:

```bash
python test_index.py
```

The script prints the result of each check (to a fake dataset) and finishes with `ALL PASSED`.

2. Run the pre-built demo:

```bash
python search_engine.py --demo
```

This runs a few sample queries against the same fake dataset and prints the ranked results, including the BM25F score, instructor rating, and GPA per result. 

Note that this release does not contain the database URL or a cached index. Attempting to run `search_engine.py` with arguments/query will fail.