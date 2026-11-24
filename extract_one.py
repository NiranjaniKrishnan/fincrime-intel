import json

import duckdb
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

# ---------- 1. The blank form (your 13-field schema, minus the 2 we already know) ----------
SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {
            "type": "string",
            "enum": ["indictment", "guilty plea", "sentencing", "settlement or consent order",
                     "sanctions designation", "penalty", "other"],
        },
        "entity_name": {"type": "string"},
        "entity_type": {
            "type": "string",
            "enum": ["bank", "money services business", "crypto exchange", "casino",
                     "broker-dealer", "individual", "other"],
        },
        "violation_type": {
            "type": "string",
            "enum": ["sanctions violation", "AML program failure", "SAR reporting failure",
                     "fraud", "money laundering", "other"],
        },
        "control_failures": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["KYC/CDD", "transaction monitoring", "sanctions screening", "SAR filing",
                         "governance & oversight", "training", "record keeping"],
            },
        },
        "detection_method": {
            "type": "string",
            "enum": ["self-disclosed", "regulator exam", "whistleblower", "law enforcement", "unknown"],
        },
        "penalty_amount_usd": {"type": ["number", "null"]},
        "penalty_evidence": {"type": ["string", "null"]},
        "remediation_mentioned": {"type": "boolean"},
        "remediation_summary": {"type": ["string", "null"]},
        "countries_involved": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["action_type", "entity_name", "entity_type", "violation_type", "control_failures",
                 "detection_method", "penalty_amount_usd", "penalty_evidence",
                 "remediation_mentioned", "remediation_summary", "countries_involved", "summary"],
    "additionalProperties": False,
}

# ---------- 2. The job description for the reader ----------
INSTRUCTIONS = """You are a financial crime compliance analyst extracting structured data
from U.S. government enforcement press releases.

Rules:
- Use ONLY information stated in the press release. Never guess or use outside knowledge.
- If a field is not stated, use null (or an empty list, or "unknown" for detection_method).
- penalty_amount_usd: fines, civil money penalties or forfeiture ordered against the party,
  as a plain number (e.g. 50000000). Prison sentences are not penalties.
- penalty_evidence: copy the exact sentence from the press release that states the penalty,
  word for word. Null if there is no penalty.
- control_failures: only list failures the press release explicitly describes.
  Individual criminal cases usually have none, so return an empty list.
- summary: 2 sentences, plain English, for a compliance analyst."""

# ---------- 3. Take one story from the cabinet ----------
con = duckdb.connect("fincrime.duckdb", read_only=True)
release_id, release_date, title, body = con.execute("""
    SELECT release_id, release_date, title, body_text
    FROM int_doj_fincrime_candidates
    ORDER BY release_date DESC
    LIMIT 1
""").fetchone()
con.close()

# ---------- 4. Hand Claude the form and the story ----------
message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=2000,
    system=INSTRUCTIONS,
    messages=[{"role": "user", "content": f"Title: {title}\n\n{body}"}],
    output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
)

# ---------- 5. Read the filled-in form ----------
reply = next(block.text for block in message.content if block.type == "text")
form = json.loads(reply)

# Attach the two fields we already knew
form["source"] = "DOJ"
form["action_date"] = str(release_date)
form["release_id"] = release_id

print("STORY:", title, "\n")
print(json.dumps(form, indent=2))

# ---------- 6. A first spot-check: is the evidence really in the story? ----------
if form["penalty_evidence"]:
    print("\nEvidence found in source text:", form["penalty_evidence"] in body)

print("\nTOKENS:", message.usage.input_tokens, "in /", message.usage.output_tokens, "out")