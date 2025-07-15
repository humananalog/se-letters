#!/usr/bin/env python3
import duckdb

with duckdb.connect("../../data/IBcatalogue.duckdb") as conn:
    schema = conn.execute("DESCRIBE products").fetchall()
    print("Database Schema:")
    for col in schema:
        print(f"  {col[0]}: {col[1]}") 