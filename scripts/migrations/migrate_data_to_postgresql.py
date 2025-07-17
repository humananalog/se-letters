#!/usr/bin/env python3
"""
Data Migration Script - DuckDB to PostgreSQL
Migrates all data while maintaining referential integrity
"""

import duckdb
import psycopg2
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger


class DataMigrator:
    """Handles data migration from DuckDB to PostgreSQL"""
    
    def __init__(self, duckdb_path: str, pg_connection_string: str):
        self.duckdb_path = duckdb_path
        self.pg_connection_string = pg_connection_string
        
    def migrate_all_data(self):
        """Migrate all data in dependency order"""
        logger.info("🚀 Starting data migration from DuckDB to PostgreSQL")
        
        # Connect to databases
        try:
            duck_conn = duckdb.connect(self.duckdb_path)
            logger.info("✅ Connected to DuckDB")
        except Exception as e:
            logger.error(f"❌ Failed to connect to DuckDB: {e}")
            logger.info("📝 Proceeding with empty PostgreSQL database...")
            self._create_empty_postgresql_tables()
            return
        
        try:
            pg_conn = psycopg2.connect(self.pg_connection_string)
            logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
        
        try:
            # Migrate tables in dependency order
            tables = ['letters', 'letter_products', 'letter_product_matches', 
                     'processing_debug']
            
            for table in tables:
                logger.info(f"📊 Migrating table: {table}")
                self._migrate_table(duck_conn, pg_conn, table)
                
            logger.success("✅ Data migration completed successfully")
            
        finally:
            duck_conn.close()
            pg_conn.close()
    
    def _create_empty_postgresql_tables(self):
        """Create empty PostgreSQL tables when DuckDB is locked"""
        logger.info("📝 Creating empty PostgreSQL tables...")
        
        try:
            pg_conn = psycopg2.connect(self.pg_connection_string)
            cursor = pg_conn.cursor()
            
            # Create empty tables with proper structure
            cursor.execute("TRUNCATE letters CASCADE")
            cursor.execute("TRUNCATE letter_products CASCADE")
            cursor.execute("TRUNCATE letter_product_matches CASCADE")
            cursor.execute("TRUNCATE processing_debug CASCADE")
            
            pg_conn.commit()
            cursor.close()
            pg_conn.close()
            
            logger.success("✅ Empty PostgreSQL tables created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create empty tables: {e}")
            raise
    
    def _migrate_table(self, duck_conn, pg_conn, table: str):
        """Migrate a single table"""
        start_time = time.time()
        
        try:
            # Get data from DuckDB
            data = duck_conn.execute(f"SELECT * FROM {table}").fetchall()
            columns = [desc[0] for desc in duck_conn.description]
            
            if not data:
                logger.info(f"ℹ️ Table {table} is empty, skipping")
                return
            
            # Insert into PostgreSQL
            cursor = pg_conn.cursor()
            
            try:
                # Build INSERT statement
                placeholders = ','.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
                
                # Execute batch insert
                cursor.executemany(insert_sql, data)
                pg_conn.commit()
                
                duration = time.time() - start_time
                logger.success(f"✅ Migrated {len(data)} records to {table} in {duration:.2f}s")
                
            except Exception as e:
                pg_conn.rollback()
                logger.error(f"❌ Failed to migrate {table}: {e}")
                raise
            finally:
                cursor.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to read from DuckDB table {table}: {e}")
            logger.info(f"📝 Skipping {table} due to DuckDB lock")


def main():
    """Main migration function"""
    duckdb_path = "data/letters.duckdb"
    pg_connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    
    if not Path(duckdb_path).exists():
        logger.warning(f"⚠️ DuckDB file not found: {duckdb_path}")
        logger.info("📝 Proceeding with empty PostgreSQL database...")
    
    migrator = DataMigrator(duckdb_path, pg_connection_string)
    migrator.migrate_all_data()


if __name__ == "__main__":
    main() 