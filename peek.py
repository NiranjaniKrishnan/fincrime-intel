import duckdb

con = duckdb.connect("fincrime.duckdb")

print(con.sql("""
    SELECT release_date, title
    FROM stg_doj_press_releases
    WHERE is_fincrime_candidate
    ORDER BY release_date DESC
"""))