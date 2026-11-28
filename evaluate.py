import duckdb

con = duckdb.connect("fincrime.duckdb", read_only=True)


def as_list(column):
    """SQL to turn 'a; b' (or 'a, b') into a clean, sorted list. Blank becomes []."""
    return f"""coalesce(list_sort(list_transform(
                   string_split_regex({column}, '[;,]'),
                   lambda x: lower(trim(x)))), []::VARCHAR[])"""


def yes_no(column):
    """SQL to turn yes/no/true/false into 'true'/'false'."""
    return f"""CASE lower(trim({column}))
                   WHEN 'yes' THEN 'true' WHEN 'no' THEN 'false'
                   ELSE lower(trim({column})) END"""


def claude_list(field):
    """SQL to read a list field from Claude's v2.0 form."""
    return f"""list_sort(list_transform(
                   from_json(json_extract(extraction_json, '$.{field}'), '["VARCHAR"]'),
                   lambda x: lower(x)))"""


COMPARE = f"""
WITH labels AS (
    SELECT
        release_id,
        title,
        {yes_no('my_is_case')}                           AS my_is_case,
        lower(trim(my_action_type))                      AS my_action,
        lower(trim(my_entity_type))                      AS my_entity,
        nullif(trim(my_penalty_amount_usd), '0')         AS my_penalty,
        {as_list('my_predicates')}                       AS my_predicates,
        coalesce({yes_no('my_money_laundering')}, 'false') AS my_ml,
        {as_list('my_sanctions_regulatory')}             AS my_sanc
    FROM read_csv('labels.csv', header = true, all_varchar = true)
),
claude AS (
    SELECT
        release_id,
        schema_version,
        lower(json_extract_string(extraction_json, '$.is_enforcement_action')) AS c_is_case,
        lower(json_extract_string(extraction_json, '$.action_type'))           AS c_action,
        lower(json_extract_string(extraction_json, '$.entity_type'))           AS c_entity,
        json_extract_string(extraction_json, '$.penalty_amount_usd')           AS c_penalty,
        {claude_list('predicate_offenses')}                                    AS c_predicates,
        lower(json_extract_string(extraction_json, '$.money_laundering'))      AS c_ml,
        {claude_list('sanctions_regulatory_violations')}                       AS c_sanc
    FROM raw_extractions
),
compared AS (
    SELECT
        c.schema_version,
        l.title,
        l.my_is_case,    c.c_is_case,
        l.my_action,     c.c_action,
        l.my_entity,     c.c_entity,
        l.my_penalty,    c.c_penalty,
        l.my_predicates, c.c_predicates,
        l.my_ml,         c.c_ml,
        l.my_sanc,       c.c_sanc,

        l.my_is_case = c.c_is_case AS is_case_ok,
        CASE WHEN l.my_is_case = 'true' THEN l.my_action = c.c_action END AS action_ok,
        CASE WHEN l.my_is_case = 'true' THEN l.my_entity = c.c_entity END AS entity_ok,
        CASE WHEN l.my_is_case = 'true'
             THEN coalesce(try_cast(l.my_penalty AS DOUBLE), -1)
                = coalesce(try_cast(c.c_penalty  AS DOUBLE), -1) END AS penalty_ok,

        -- v2.0-only fields
        CASE WHEN l.my_is_case = 'true' AND starts_with(c.schema_version, 'v2.')
             THEN l.my_predicates = c.c_predicates END AS predicate_ok,
        CASE WHEN l.my_is_case = 'true' AND starts_with(c.schema_version, 'v2.')
             THEN l.my_ml = c.c_ml END AS ml_ok,
        CASE WHEN l.my_is_case = 'true' AND starts_with(c.schema_version, 'v2.')
             THEN l.my_sanc = c.c_sanc END AS sanc_ok
    FROM labels AS l
    JOIN claude AS c USING (release_id)
)
"""

# ---- Scorecard by version ----
con.sql(COMPARE + """
    SELECT
        schema_version,
        count(*)                               AS labeled,
        round(avg(is_case_ok::INT)    * 100)   AS is_case_pct,
        round(avg(action_ok::INT)     * 100)   AS action_pct,
        round(avg(entity_ok::INT)     * 100)   AS entity_pct,
        round(avg(penalty_ok::INT)    * 100)   AS penalty_pct,
        round(avg(predicate_ok::INT)  * 100)   AS predicate_pct,
        round(avg(ml_ok::INT)         * 100)   AS ml_pct,
        round(avg(sanc_ok::INT)       * 100)   AS sanc_pct
    FROM compared
    GROUP BY schema_version
    ORDER BY schema_version
""").show(max_width=400)

# ---- v2.0 disagreements ----
con.sql(COMPARE + """
    SELECT
        left(title, 40) AS story,
        my_is_case, c_is_case,
        my_predicates, c_predicates,
        my_ml, c_ml,
        my_sanc, c_sanc,
        my_action, c_action,
        my_penalty, c_penalty
    FROM compared
    WHERE schema_version = 'v2.2'
      AND (NOT is_case_ok
           OR NOT coalesce(action_ok, true)
           OR NOT coalesce(entity_ok, true)
           OR NOT coalesce(penalty_ok, true)
           OR NOT coalesce(predicate_ok, true)
           OR NOT coalesce(ml_ok, true)
           OR NOT coalesce(sanc_ok, true))
""").show(max_width=400)