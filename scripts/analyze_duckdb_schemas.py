#!/usr/bin/env python3
"""
Analyze DuckDB Schemas: letters.duckdb and ibcatalogue.duckdb
Prints schema, indexes, and row counts for all tables in both databases.
Helps align PostgreSQL schema perfectly for migration.
"""
import duckdb
from pathlib import Path

DBS = {
    'letters': 'data/letters.duckdb',
    'ibcatalogue': 'data/backups/IBcatalogue_backup_20250716_085202.duckdb',
}

def print_schema(db_path, db_label):
    print(f"\n=== {db_label.upper()} ({db_path}) ===")
    if not Path(db_path).exists():
        print(f"  [ERROR] File not found: {db_path}")
        return
    conn = duckdb.connect(db_path)
    tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
    print(f"  Tables: {tables}")
    for table in tables:
        print(f"\n  -- Table: {table}")
        schema = conn.execute(f"DESCRIBE {table}").fetchall()
        print(f"    Columns:")
        for col in schema:
            print(f"      {col}")
        # Row count
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"    Row count: {count}")
    conn.close()

def main():
    for label, path in DBS.items():
        print_schema(path, label)

if __name__ == "__main__":
    main() 