MODEL = "claude-haiku-5-5"
SCHEMA_VERSION = "v1.2"
SCHEMA = {
    "type": "object",
    "properties": {
        "is_enforcement_action": {"type": "boolean"},
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
    "required": ["is_enforcement_action", "action_type", "entity_name", "entity_type", "violation_type", "control_failures",
                 "detection_method", "penalty_amount_usd", "penalty_evidence",
                 "remediation_mentioned", "remediation_summary", "countries_involved", "summary"],
    "additionalProperties": False,
}

INSTRUCTIONS = """You are a financial crime compliance analyst extracting structured data
from U.S. government enforcement press releases.

Rules:
- is_enforcement_action: true ONLY if the release announces a specific case against a
  specific person or organization (charge, indictment, plea, conviction, sentence,
  settlement, penalty or sanctions designation). false for program or funding
  announcements, awards, task forces, campaigns or general fraud-awareness releases.
  If false, still fill the other fields as best you can, using "other" and nulls.
- Use ONLY information stated in the press release. Never guess or use outside knowledge.
- If a field is not stated, use null (or an empty list, or "unknown" for detection_method).
- penalty_amount_usd: fines, civil money penalties or forfeiture ordered against the party,
  as a plain number (e.g. 50000000). Prison sentences and restitution are not penalties.
- penalty_evidence: copy the exact sentence from the press release that states the penalty,
  word for word. Null if there is no penalty.
- control_failures: only list failures the press release explicitly describes.
  Individual criminal cases usually have none, so return an empty list.
- countries_involved: list countries OTHER than the United States that are part of the
  conduct (e.g. where funds were sent, where sanctioned parties are). Empty list if none.
- summary: 2 sentences, plain English, for a compliance analyst."""