import duckdb

con = duckdb.connect("fincrime.duckdb", read_only=True)
con.sql("""
    SELECT
        left(s.title, 50) AS story,
        json_extract_string(e.extraction_json, '$.money_laundering_evidence') AS ml_quote,
        e.evidence_valid
    FROM raw_extractions AS e
    JOIN stg_doj_press_releases AS s USING (release_id)
    WHERE e.schema_version = 'v2.0'
      AND s.title ILIKE 'Long Island%'
""").show(max_width=400)