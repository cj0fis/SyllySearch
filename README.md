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