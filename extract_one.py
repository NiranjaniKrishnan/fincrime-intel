import json

import duckdb
from anthropic import Anthropic
from dotenv import load_dotenv
from extraction_config import MODEL, SCHEMA, INSTRUCTIONS

load_dotenv()
client = Anthropic()

# ---------- 1. Take one story from the cabinet ----------
con = duckdb.connect("fincrime.duckdb", read_only=True)
release_id, release_date, title, body = con.execute("""
    SELECT release_id, release_date, title, body_text
    FROM int_doj_fincrime_candidates
    ORDER BY release_date DESC
    LIMIT 1
""").fetchone()
con.close()

# ---------- 2. Hand Claude the form and the story ----------
message = client.messages.create(
    model=MODEL,
    max_tokens=2000,
    system=INSTRUCTIONS,
    messages=[{"role": "user", "content": f"Title: {title}\n\n{body}"}],
    output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
)

# ---------- 3. Read the filled-in form ----------
reply = next(block.text for block in message.content if block.type == "text")
form = json.loads(reply)

# Attach the two fields we already knew
form["source"] = "DOJ"
form["action_date"] = str(release_date)
form["release_id"] = release_id

print("STORY:", title, "\n")
print(json.dumps(form, indent=2))

# ---------- 4. A first spot-check: is the evidence really in the story? ----------
if form["penalty_evidence"]:
    print("\nEvidence found in source text:", form["penalty_evidence"] in body)

print("\nTOKENS:", message.usage.input_tokens, "in /", message.usage.output_tokens, "out")