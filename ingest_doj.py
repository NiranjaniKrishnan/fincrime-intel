import json
import time

import duckdb
import requests

URL = "https://www.justice.gov/api/v1/press_releases.json"
DB_PATH = "fincrime.duckdb"

# ---- 1. Fetch (same as before) ----
releases = []
for page in range(5):
    params = {"sort": "date", "direction": "DESC", "page": page}
    response = requests.get(URL, params=params, timeout=30)
    response.raise_for_status()
    releases.extend(response.json()["results"])
    time.sleep(1)

print(f"Fetched {len(releases)} releases")

# ---- 2. Open the filing cabinet (creates the file if it doesn't exist) ----
con = duckdb.connect(DB_PATH)

con.execute("""
    CREATE TABLE IF NOT EXISTS raw_doj_press_releases (
        uuid        VARCHAR PRIMARY KEY,
        title       VARCHAR,
        body        VARCHAR,
        url         VARCHAR,
        date_epoch  BIGINT,
        raw_json    VARCHAR,
        fetched_at  TIMESTAMPTZ
    )
""")

# ---- 3. File each release (skip ones we already have) ----
count_before = con.execute("SELECT COUNT(*) FROM raw_doj_press_releases").fetchone()[0]

for r in releases:
    con.execute(
        """
        INSERT OR IGNORE INTO raw_doj_press_releases
        VALUES (?, ?, ?, ?, ?, ?, current_timestamp)
        """,
        [r["uuid"], r["title"], r["body"], r["url"], int(r["date"]), json.dumps(r)],
    )

count_after = con.execute("SELECT COUNT(*) FROM raw_doj_press_releases").fetchone()[0]

print(f"New releases saved: {count_after - count_before}")
print(f"Total in cabinet:   {count_after}")

con.close()