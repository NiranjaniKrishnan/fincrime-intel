MODEL = "claude-haiku-5-5"
SCHEMA_VERSION = "v2.2"


def pick_list(*options):
    """A list field where every item must come from the given options."""
    return {"type": "array", "items": {"type": "string", "enum": list(options)}}


SCHEMA = {
    "type": "object",
    "properties": {
        "is_enforcement_action": {"type": "boolean"},
        "action_type": {
            "type": "string",
            "enum": ["indictment", "guilty plea", "conviction", "sentencing",
                     "settlement or consent order", "sanctions designation", "penalty", "other"],
        },
        "entity_name": {"type": "string"},
        "entity_type": {
            "type": "string",
            "enum": ["bank", "money services business", "crypto exchange", "casino",
                     "broker-dealer", "individual", "other"],
        },

        # ---- Layer 1: predicate offense ----
        "predicate_offenses": pick_list(
            "fraud", "drug trafficking", "human trafficking & migrant smuggling",
            "corruption & bribery", "cyber-enabled crime",
            "organized crime & racketeering", "other"),

        # ---- Layer 2: ML / TF overlay ----
        "money_laundering": {"type": "boolean"},
        "money_laundering_evidence": {"type": ["string", "null"]},
        "terrorist_financing": {"type": "boolean"},
        "terrorist_financing_evidence": {"type": ["string", "null"]},

        # ---- Layer 3: sanctions & regulatory violations ----
        "sanctions_regulatory_violations": pick_list(
            "sanctions violation", "AML program failure", "SAR reporting failure"),

        "control_failures": pick_list(
            "KYC/CDD", "transaction monitoring", "sanctions screening", "SAR filing",
            "governance & oversight", "training", "record keeping"),
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
    "additionalProperties": False,
}

# Every box must be filled, so "required" is simply every field name.
SCHEMA["required"] = list(SCHEMA["properties"].keys())

INSTRUCTIONS = """You are a financial crime compliance analyst extracting structured data
from U.S. government enforcement press releases. Each case is described in three layers:
(1) the predicate offense, (2) any money laundering or terrorist financing charge,
(3) any sanctions or regulatory violation.

General rules:
- is_enforcement_action: judge the release's MAIN PURPOSE. true only if it announces a
  specific case against a specific person or organization (charge, indictment, plea,
  conviction, sentence, settlement, penalty or sanctions designation). false for program,
  campaign, funding, task-force or award announcements, EVEN IF they mention example cases.
  If false, still fill the other fields as best you can, using "other", empty lists and nulls.
- Use ONLY information stated in the press release. Never guess or use outside knowledge.
- action_type: the stage this release announces. "conviction" = found guilty at trial;
  "guilty plea" = the defendant admitted guilt.
- entity_type: "broker-dealer" means a registered securities firm. A person is always
  "individual", whatever industry they work in.

Layer 1 - predicate_offenses:
- List the underlying crimes. ALL types of fraud (healthcare, securities, insider trading,
  investment, bank, mortgage, tax, pandemic, benefits, identity theft, scams) are "fraud".
- Classify by the underlying CONDUCT (the typology), not by the statute used.
  "corruption & bribery" means bribes, kickbacks or gifts to PUBLIC OFFICIALS or
  government employees (e.g. payments to military personnel, even if settled under
  the False Claims Act). Kickbacks between private parties, such as in healthcare
  billing schemes, are "fraud".
- Violent or property crimes such as robbery, assault or firearms offenses are "other".
  Do not label a crime "fraud" unless the release describes deception for financial gain.
- Use ["other"] ONLY when the crime is outside every listed category. Never combine "other"
  with another category.
- Do NOT list sanctions evasion here; it belongs in layer 3.
- Empty list if the case is only a sanctions or regulatory violation.

Layer 2 - money laundering and terrorist financing:
- money_laundering: true ONLY if the release states a money laundering CHARGE, GUILTY PLEA
  or CONVICTION (including conspiracy to commit money laundering). Describing how proceeds
  were spent or moved is NOT enough on its own.
- terrorist_financing: true ONLY if the release states a CHARGE, GUILTY PLEA or CONVICTION
  for financing terrorism or providing funds or material support to a terrorist organization.
- *_evidence: copy the exact sentence stating the charge, plea or conviction, word for word.
  Null when the flag is false.

Layer 3 - sanctions_regulatory_violations:
- "sanctions violation": any evasion or breach of U.S. sanctions or export controls,
  by a person OR an institution.
- "AML program failure" / "SAR reporting failure": failures by a regulated institution.
- Empty list if none.

Money and other fields:
- penalty_amount_usd: COUNT fines, civil money penalties and forfeiture ordered against the
  party, as a plain number. DO NOT COUNT restitution, special assessments or prison time.
  Null if nothing counts.
- penalty_evidence: the exact sentence stating the penalty, word for word. Null if none.
- control_failures: only failures the release explicitly describes. Individual criminal
  cases usually have none.
- detection_method: "unknown" unless the release says how the conduct was discovered.
- countries_involved: countries OTHER than the United States that are part of the conduct.
- summary: 2 sentences, plain English, for a compliance analyst."""