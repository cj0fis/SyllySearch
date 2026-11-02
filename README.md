# SyllySearch


## How to create a virtual environment (DO THIS!)

Open the root directory in a terminal (vscode is fine)
run `python -m venv venv`
This will install a virtual environment into that folder. only run this once

To activate the venv:
run in the root directory: `venv/scripts/activate` on windows (there are a couple scripts in there, find one that works if you're not on windows).

Run this every time you start working on the project.

## How to install dependencies

run `pip install -r requirements.txt` from the root directory.

To save dependences if you end up installing more libraries, run `pip freeze > requirements.txt`. and then commit the file.

## .env file

this is not committed for obvious reasons. it contains the database url and password. msg me on discord for the .env file

## How to run the backend

run `python server.py` from backend

you can test this out at `localhost:8080/query?query_text=csce470`

replace "csce470" with whatever your query is.

## TODO

[x] get all syllabi codes

[x] Use the codes we have to parse all syllabi docs

[x] populate the following tables:

- instructors    (from editor list)
- syllabi_docs  (from syllabi reader)
  - this will be used for preprocessing. we will have an index later
- terms         (lots of redundant data in syllabus docs)
- department codes (or as an ENUM)
- class list (uses dept code and course_num from the title)

[x] Then, connect these with foreign keys.

[x] use instructor table to cross reference with RateMyProfessor

[x] cross reference term list, dept code, and class list with grade distribution data

[x] somehow get urls of all rmp pages for TAMU CSTAT

[x] parse those and save scores

[x] maybe save comment metadata for ranking. i.e. look for keywords like "easy" or "homework"

[x] once all course codes are retrieved, get grade distribution data