
"""
Match rmp.name with instructors.first_name + instructors.last_name.

If exactly one instructor matches:
    rmp.instructor_id = instructors.entity_id

If no match or multiple matches:
    Leave rmp.instructor_id as NULL.

Existing non-NULL instructor_id values are not modified.

Usage:
    python3 backend/add_instructor_id_rmp.py
"""

import os
import re
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv


def normalize_name(name):
    """Normalize names for case-insensitive matching."""

    if not name:
        return ""

    # Ignore capitalization and extra whitespace
    name = name.casefold()
    name = re.sub(r"\s+", " ", name)

    return name.strip()


def main():
    load_dotenv()

    DATABASE_URL = os.environ["DATABASE_URL"]

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # 1. Retrieve instructors
        cur.execute("""
            SELECT entity_id, first_name, last_name
            FROM instructors
        """)

        instructors = cur.fetchall()

        # 2. Build dictionary of instructor names -> IDs
        instructor_dict = defaultdict(list)

        for entity_id, first_name, last_name in instructors:
            full_name = f"{first_name or ''} {last_name or ''}"
            key = normalize_name(full_name)

            if key:
                instructor_dict[key].append(entity_id)

        # 3. Retrieve RMP professors
        cur.execute("""
            SELECT professor_id, name, instructor_id
            FROM rmp
        """)

        rmp_rows = cur.fetchall()

        matches = []

        matched = 0
        unmatched = 0
        ambiguous = 0
        already_linked = 0

        # 4. Match professors to instructors
        for professor_id, name, current_id in rmp_rows:

            # Do not overwrite existing instructor IDs
            if current_id is not None:
                already_linked += 1
                continue

            key = normalize_name(name)
            possible_matches = instructor_dict.get(key, [])

            if len(possible_matches) == 1:
                instructor_id = possible_matches[0]

                matches.append((instructor_id, professor_id))
                matched += 1

            elif len(possible_matches) == 0:
                unmatched += 1

            else:
                ambiguous += 1

        # 5. Update database
        total = len(matches)

        print(f"Updating {total} RMP professors...", flush=True)

        for i, (instructor_id, professor_id) in enumerate(matches, start=1):
            cur.execute("""
                UPDATE rmp
                SET instructor_id = %s
                WHERE professor_id = %s
                  AND instructor_id IS NULL
            """, (instructor_id, professor_id))

            if i % 100 == 0 or i == total:
                print(f"Updated {i}/{total} professors", flush=True)

        conn.commit()

        print("Database updated successfully!")

        # 6. Print summary
        print("\n===== RMP INSTRUCTOR MATCHING =====")
        print(f"Total RMP professors: {len(rmp_rows)}")
        print(f"Matched: {matched}")
        print(f"Unmatched: {unmatched}")
        print(f"Ambiguous: {ambiguous}")
        print(f"Already linked: {already_linked}")

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
