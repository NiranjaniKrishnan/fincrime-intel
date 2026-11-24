import duckdb

con = duckdb.connect("fincrime.duckdb", read_only=True)

# What did Claude find?
print(con.sql("""
    SELECT
        json_extract_string(extraction_json, '$.violation_type') AS violation_type,
        json_extract_string(extraction_json, '$.entity_type')    AS entity_type,
        count(*)                                                 AS stories
    FROM raw_extractions
    GROUP BY ALL
    ORDER BY stories DESC
"""))

# How much did it cost?
print(con.sql("""
    SELECT
        count(*)                                          AS stories,
        round(avg(input_tokens))                          AS avg_in,
        round(avg(output_tokens))                         AS avg_out,
        round(sum(input_tokens)  * 0.10 / 1e6
            + sum(output_tokens) * 0.50 / 1e6, 4)         AS total_cost_usd
    FROM raw_extractions
"""))

# Did the spot-check catch anything?
print(con.sql("""
    SELECT evidence_valid, count(*) AS stories
    FROM raw_extractions
    GROUP BY evidence_valid
"""))

print(con.sql("""
    SELECT
        json_extract_string(extraction_json, '$.is_enforcement_action') AS is_case,
        count(*) AS stories
    FROM raw_extractions
    GROUP BY 1
"""))