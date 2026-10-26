# to generate visualizations of existing data in Supabase db
# visualize the total records collected so far
# visualize the grade distribution of course sections
# for Checkpoint 1
import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not found."
    )

OUTPUT_DIR = "figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# count number of records per table (grade_distributions, instructors, rmp, syllabi)
def save_dataset_size_chart(conn):
    tables = [
        "grade_distributions",
        "instructors",
        "rmp",
        "syllabi",
    ]

    counts = {}
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM public."{table}"')
            counts[table] = cur.fetchone()[0]

    plt.figure(figsize = (6, 6))
    bars = plt.bar(counts.keys(), counts.values())
    plt.bar_label(bars, padding = 5)
    plt.title("Dataset Size by Table")
    plt.ylabel("Number of Records")
    plt.xticks()
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, "dataset_size.png"),
        bbox_inches = "tight",
    )
    plt.close()

    print("\nRecord counts:")
    for table, count in counts.items():
        print(f"{table}: {count}")
    print(f"Total: {sum(counts.values())}")

# avg gpa per course section (grade_distributions)
def save_gpa_chart(conn):
    # there will be warning bc psycopg2 connection in pandas is not recommended
    # but it should still work despite the warning
    df = pd.read_sql_query(
        """
        SELECT gpa
        FROM public.grade_distributions
        WHERE gpa IS NOT NULL
        """,
        conn,
    )

    gpas = df["gpa"].dropna()

    

    if not gpas.empty:
        plt.figure(figsize = (6, 6))
        plt.hist(gpas, bins = 15, edgecolor = "black")

        mean_gpa = gpas.mean()
        median_gpa = gpas.median()

        plt.axvline(
            mean_gpa,
            linestyle = "--",
            color = "red",
            label = f"Mean = {mean_gpa:.2f}",
        )
        plt.axvline(
            median_gpa,
            linestyle = ":",
            color = "red",
            label = f"Median = {median_gpa:.2f}",
        )
        plt.legend()

        print("\nCourse-section GPA values:")
        print(f"Sections with GPA data: {len(gpas)}")
        print(f"Mean GPA: {mean_gpa:.2f}")
        print(f"Median GPA: {median_gpa:.2f}")
        print(f"Minimum GPA: {gpas.min():.2f}")
        print(f"Maximum GPA: {gpas.max():.2f}")
    else:
        print("No GPA data?")

    plt.title("Distribution of Average GPA by Course Section")
    plt.xlabel("Average GPA (4-point scale)")
    plt.ylabel("Number of Course Sections")
    plt.tight_layout()
    plt.savefig(
        os.path.join(OUTPUT_DIR, "gpa_distribution.png"),
        bbox_inches = "tight",
    )
    plt.close()


def main():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Connected to DB")

        save_dataset_size_chart(conn)
        save_gpa_chart(conn)

        print(f"\nFigures saved in the '{OUTPUT_DIR}' folder.")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
