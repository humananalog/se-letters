#!/usr/bin/env python3
"""
IBcatalogue Data Migration Script
Migrates 342,229 products from DuckDB to PostgreSQL
"""

import duckdb
import psycopg2
import time
from pathlib import Path
from loguru import logger

class IBcatalogueDataMigrator:
    """Handles IBcatalogue data migration from DuckDB to PostgreSQL"""
    
    def __init__(self, duckdb_path: str, pg_connection_string: str):
        self.duckdb_path = duckdb_path
        self.pg_connection_string = pg_connection_string
        
    def migrate_products(self):
        """Migrate all products from DuckDB to PostgreSQL"""
        logger.info("🚀 Starting IBcatalogue data migration...")
        
        # Connect to databases
        duck_conn = duckdb.connect(self.duckdb_path)
        pg_conn = psycopg2.connect(self.pg_connection_string)
        
        try:
            # Get total count
            total_products = duck_conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            logger.info(f"📊 Total products to migrate: {total_products:,}")
            
            # Get column names
            columns = [desc[0] for desc in duck_conn.execute("SELECT * FROM products LIMIT 1").description]
            logger.info(f"📋 Columns: {', '.join(columns)}")
            
            # Migrate in batches
            batch_size = 1000
            total_batches = (total_products + batch_size - 1) // batch_size
            
            start_time = time.time()
            migrated_count = 0
            
            for batch_num in range(total_batches):
                offset = batch_num * batch_size
                
                # Get batch from DuckDB
                batch_data = duck_conn.execute(f"""
                    SELECT * FROM products 
                    ORDER BY product_identifier 
                    LIMIT {batch_size} OFFSET {offset}
                """).fetchall()
                
                if not batch_data:
                    break
                
                # Insert batch into PostgreSQL
                self._insert_batch(pg_conn, batch_data, columns)
                
                migrated_count += len(batch_data)
                elapsed = time.time() - start_time
                rate = migrated_count / elapsed if elapsed > 0 else 0
                
                logger.info(f"📦 Batch {batch_num + 1}/{total_batches}: "
                           f"{migrated_count:,}/{total_products:,} products "
                           f"({rate:.0f} products/sec)")
            
            # Validate migration
            self._validate_migration(duck_conn, pg_conn, total_products)
            
            logger.success(f"✅ IBcatalogue migration completed: {migrated_count:,} products")
            
        finally:
            duck_conn.close()
            pg_conn.close()
    
    def _insert_batch(self, pg_conn, batch_data, columns):
        """Insert a batch of products into PostgreSQL"""
        cursor = pg_conn.cursor()
        
        try:
            # Clean data - convert empty strings to None for timestamp fields
            cleaned_data = []
            for row in batch_data:
                cleaned_row = list(row)
                # Convert empty strings to None for timestamp fields
                for i, col in enumerate(columns):
                    if ('date' in col.lower() or col in ['end_of_production_date', 'end_of_commercialisation', 'service_obsolescence_date', 'end_of_service_date']) and cleaned_row[i] == '':
                        cleaned_row[i] = None
                cleaned_data.append(tuple(cleaned_row))
            
            # Build INSERT statement
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO products ({','.join(columns)}) VALUES ({placeholders})"
            
            # Execute batch insert
            cursor.executemany(insert_sql, cleaned_data)
            pg_conn.commit()
            
        except Exception as e:
            pg_conn.rollback()
            logger.error(f"❌ Batch insert failed: {e}")
            raise
        finally:
            cursor.close()
    
    def _validate_migration(self, duck_conn, pg_conn, expected_count):
        """Validate the migration by comparing counts and sample data"""
        logger.info("🔍 Validating migration...")
        
        # Check count
        with pg_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM products")
            pg_count = cursor.fetchone()[0]
        
        if pg_count == expected_count:
            logger.success(f"✅ Record count matches: {pg_count:,}")
        else:
            logger.error(f"❌ Record count mismatch: DuckDB={expected_count:,}, PostgreSQL={pg_count:,}")
        
        # Check sample data
        sample_duck = duck_conn.execute("SELECT product_identifier, range_label FROM products LIMIT 5").fetchall()
        with pg_conn.cursor() as cursor:
            cursor.execute("SELECT product_identifier, range_label FROM products LIMIT 5")
            sample_pg = cursor.fetchall()
        
        if sample_duck == sample_pg:
            logger.success("✅ Sample data matches")
        else:
            logger.warning("⚠️ Sample data differs - checking individual records...")
            for i, (duck_row, pg_row) in enumerate(zip(sample_duck, sample_pg)):
                if duck_row != pg_row:
                    logger.error(f"❌ Row {i} mismatch: DuckDB={duck_row}, PostgreSQL={pg_row}")

def main():
    """Main migration function"""
    duckdb_path = "data/IBcatalogue.duckdb"
    pg_connection_string = "postgresql://alexandre@localhost:5432/se_letters_dev"
    
    if not Path(duckdb_path).exists():
        logger.error(f"❌ IBcatalogue DuckDB file not found: {duckdb_path}")
        return
    
    migrator = IBcatalogueDataMigrator(duckdb_path, pg_connection_string)
    migrator.migrate_products()

if __name__ == "__main__":
    main() 