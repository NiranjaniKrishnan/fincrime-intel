import json

import duckdb
from anthropic import Anthropic
from dotenv import load_dotenv

from extraction_config import MODEL, SCHEMA, INSTRUCTIONS, SCHEMA_VERSION

MAX_PER_RUN = 25   # safety cap: never more than 25 Claude calls per run

load_dotenv()
client = Anthropic()
con = duckdb.connect("fincrime.duckdb")

# ---------- 1. The drawer for filled-in forms ----------
con.execute("""
    CREATE TABLE IF NOT EXISTS raw_extractions (
        release_id      VARCHAR PRIMARY KEY,
        source          VARCHAR,
        action_date     DATE,
        extraction_json VARCHAR,
        evidence_valid  BOOLEAN,
        model           VARCHAR,
        schema_version  VARCHAR,
        input_tokens    INTEGER,
        output_tokens   INTEGER,
        extracted_at    TIMESTAMPTZ
    )
""")

# ---------- 2. Find stories we HAVEN'T extracted yet (the cache check) ----------
to_do = con.execute("""
    SELECT c.release_id, c.release_date, c.title, c.body_text
    FROM int_doj_fincrime_candidates AS c
    LEFT JOIN raw_extractions AS e
        ON c.release_id = e.release_id
    WHERE e.release_id IS NULL
    ORDER BY c.release_date DESC
    LIMIT ?
""", [MAX_PER_RUN]).fetchall()

print(f"Stories to extract: {len(to_do)}\n")


# ---------- 3. The supervisor's spot-check ----------
def squash(text):
    """Collapse all spaces, tabs and line breaks into single spaces."""
    return " ".join(text.split())


def check_evidence(form, body):
    if form["penalty_amount_usd"] is None:
        return None                       # no penalty → nothing to check
    if not form["penalty_evidence"]:
        return False                      # penalty claimed, but no evidence given
    return squash(form["penalty_evidence"]) in squash(body)


# ---------- 4. Extract each story, saving as we go ----------
done = 0
failed = 0

for release_id, release_date, title, body in to_do:
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=INSTRUCTIONS,
            messages=[{"role": "user", "content": f"Title: {title}\n\n{body}"}],
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        )
        reply = next(block.text for block in message.content if block.type == "text")
        form = json.loads(reply)

        con.execute(
            "INSERT INTO raw_extractions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp)",
            [release_id, "DOJ", release_date, json.dumps(form), check_evidence(form, body),
             MODEL, SCHEMA_VERSION, message.usage.input_tokens, message.usage.output_tokens],
        )
        done += 1
        print(f"  ✓ {title[:80]}")

    except Exception as error:
        failed += 1
        print(f"  ✗ {title[:80]}\n      ({error})")

con.close()
print(f"\nExtracted: {done}  |  Failed: {failed}")