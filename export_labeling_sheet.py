import duckdb

con = duckdb.connect("fincrime.duckdb", read_only=True)

con.sql("""
    SELECT
        e.release_id,
        s.title,
        s.url,
        NULL AS my_is_case,
        NULL AS my_action_type,
        NULL AS my_entity_type,
        NULL AS my_violation_type,
        NULL AS my_penalty_amount_usd
    FROM raw_extractions AS e
    JOIN stg_doj_press_releases AS s
        ON e.release_id = s.release_id
    ORDER BY hash(e.release_id)
    LIMIT 20
""").write_csv("labels.csv")

print("Created labels.csv with 20 stories to label")