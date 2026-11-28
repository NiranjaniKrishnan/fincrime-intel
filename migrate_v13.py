import duckdb

con = duckdb.connect("fincrime.duckdb")

con.begin()   # start a transaction: all steps succeed, or none happen

con.execute("""
    CREATE TABLE raw_extractions_new (
        release_id      VARCHAR,
        source          VARCHAR,
        action_date     DATE,
        extraction_json VARCHAR,
        evidence_valid  BOOLEAN,
        model           VARCHAR,
        schema_version  VARCHAR,
        input_tokens    INTEGER,
        output_tokens   INTEGER,
        extracted_at    TIMESTAMPTZ,
        PRIMARY KEY (release_id, schema_version)
    )
""")
con.execute("INSERT INTO raw_extractions_new SELECT * FROM raw_extractions")
con.execute("DROP TABLE raw_extractions")
con.execute("ALTER TABLE raw_extractions_new RENAME TO raw_extractions")

con.commit()  # make it permanent

print(con.sql("SELECT schema_version, count(*) AS forms FROM raw_extractions GROUP BY 1"))
con.close()