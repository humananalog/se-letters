#!/usr/bin/env python3
"""
Schema Migration Script - DuckDB to PostgreSQL
Exports DuckDB schema and generates PostgreSQL-compatible DDL
"""

import duckdb
import psycopg2
from pathlib import Path
from loguru import logger



def create_postgresql_schema():
    """Create PostgreSQL schema"""
    
    # PostgreSQL connection
    pg_conn = psycopg2.connect(
        host="localhost",
        database="se_letters_dev",
        user="alexandre",
        password=""
    )
    
    cursor = pg_conn.cursor()
    
    try:
        # Create letters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letters (
                id SERIAL PRIMARY KEY,
                document_name TEXT NOT NULL,
                document_type TEXT,
                document_title TEXT,
                source_file_path TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                processing_method TEXT DEFAULT 'production_pipeline',
                processing_time_ms REAL,
                extraction_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processed',
                raw_grok_json JSONB,
                ocr_supplementary_json JSONB,
                processing_steps_json JSONB,
                validation_details_json JSONB
            )
        """)
        
        # Create letter_products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letter_products (
                id SERIAL PRIMARY KEY,
                letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
                product_identifier TEXT,
                range_label TEXT,
                subrange_label TEXT,
                product_line TEXT,
                product_description TEXT,
                obsolescence_status TEXT,
                end_of_service_date TEXT,
                replacement_suggestions TEXT,
                confidence_score REAL DEFAULT 0.0,
                validation_status TEXT DEFAULT 'validated'
            )
        """)
        
        # Create letter_product_matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letter_product_matches (
                id SERIAL PRIMARY KEY,
                letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
                letter_product_id INTEGER NOT NULL REFERENCES letter_products(id) ON DELETE CASCADE,
                ibcatalogue_product_identifier TEXT NOT NULL,
                match_confidence REAL NOT NULL,
                match_reason TEXT,
                technical_match_score REAL DEFAULT 0.0,
                nomenclature_match_score REAL DEFAULT 0.0,
                product_line_match_score REAL DEFAULT 0.0,
                match_type TEXT,
                range_based_matching BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create processing_debug table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_debug (
                id SERIAL PRIMARY KEY,
                letter_id INTEGER NOT NULL REFERENCES letters(id) ON DELETE CASCADE,
                processing_step TEXT NOT NULL,
                step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                step_duration_ms REAL,
                step_success BOOLEAN DEFAULT TRUE,
                step_details TEXT,
                error_message TEXT
            )
        """)
        
        # Create indexes
        create_indexes(cursor)
        
        pg_conn.commit()
        logger.success("✅ PostgreSQL schema created successfully")
        
    except Exception as e:
        pg_conn.rollback()
        logger.error(f"❌ Schema creation failed: {e}")
        raise
    finally:
        cursor.close()
        pg_conn.close()

def create_indexes(cursor):
    """Create performance indexes"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_letters_source_path ON letters(source_file_path)",
        "CREATE INDEX IF NOT EXISTS idx_letters_status ON letters(status)",
        "CREATE INDEX IF NOT EXISTS idx_letters_file_hash ON letters(file_hash)",
        "CREATE INDEX IF NOT EXISTS idx_letters_created_at ON letters(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_letters_document_name ON letters(document_name)",
        
        "CREATE INDEX IF NOT EXISTS idx_products_letter_id ON letter_products(letter_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_range_label ON letter_products(range_label)",
        "CREATE INDEX IF NOT EXISTS idx_products_product_identifier ON letter_products(product_identifier)",
        
        "CREATE INDEX IF NOT EXISTS idx_matches_letter_id ON letter_product_matches(letter_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_product_id ON letter_product_matches(letter_product_id)",
        "CREATE INDEX IF NOT EXISTS idx_matches_ibcatalogue_id ON letter_product_matches(ibcatalogue_product_identifier)",
        "CREATE INDEX IF NOT EXISTS idx_matches_confidence ON letter_product_matches(match_confidence)",
        
        "CREATE INDEX IF NOT EXISTS idx_debug_letter_id ON processing_debug(letter_id)",
        "CREATE INDEX IF NOT EXISTS idx_debug_timestamp ON processing_debug(step_timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_debug_step ON processing_debug(processing_step)",
        
        "CREATE INDEX IF NOT EXISTS idx_letters_raw_grok_gin ON letters USING GIN (raw_grok_json)",
        "CREATE INDEX IF NOT EXISTS idx_letters_validation_details_gin ON letters USING GIN (validation_details_json)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
        logger.info(f"✅ Created index: {index_sql.split('ON')[1].strip()}")

def export_duckdb_schema():
    """Export DuckDB schema and generate PostgreSQL DDL"""
    duckdb_path = "data/letters.duckdb"
    
    if not Path(duckdb_path).exists():
        logger.warning(f"⚠️ DuckDB file not found: {duckdb_path}")
        return
    
    duck_conn = duckdb.connect(duckdb_path)
    
    # Get table schemas
    tables = duck_conn.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'main'
    """).fetchall()
    
    logger.info(f"📊 Found {len(tables)} tables in DuckDB")
    
    for table in tables:
        table_name = table[0]
        logger.info(f"Processing table: {table_name}")
        
        # Get column information
        columns = duck_conn.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """).fetchall()
        
        # Generate PostgreSQL DDL
        generate_postgresql_ddl(table_name, columns)
    
    duck_conn.close()

def generate_postgresql_ddl(table_name: str, columns: list):
    """Generate PostgreSQL DDL for a table"""
    ddl = f"CREATE TABLE {table_name} (\n"
    
    for column in columns:
        col_name, data_type, is_nullable, default = column
        
        # Map DuckDB types to PostgreSQL
        pg_type = map_data_type(data_type)
        
        ddl += f"    {col_name} {pg_type}"
        
        if default and default != "NULL":
            ddl += f" DEFAULT {default}"
        
        if is_nullable == "NO":
            ddl += " NOT NULL"
        
        ddl += ",\n"
    
    ddl = ddl.rstrip(",\n") + "\n);"
    
    logger.info(f"Generated DDL for {table_name}:")
    logger.info(ddl)

def map_data_type(duckdb_type: str) -> str:
    """Map DuckDB data types to PostgreSQL"""
    type_mapping = {
        "INTEGER": "INTEGER",
        "BIGINT": "BIGINT", 
        "TEXT": "TEXT",
        "VARCHAR": "VARCHAR",
        "REAL": "REAL",
        "DOUBLE": "DOUBLE PRECISION",
        "BOOLEAN": "BOOLEAN",
        "TIMESTAMP": "TIMESTAMP",
        "DATE": "DATE",
        "JSON": "JSONB"
    }
    return type_mapping.get(duckdb_type.upper(), "TEXT")

#!/usr/bin/env python3
"""
Schema Migration Script - IBcatalogue to PostgreSQL
Creates the PostgreSQL schema for the IBcatalogue products table
"""

import psycopg2

def create_ibcatalogue_schema():
    """Create PostgreSQL schema for IBcatalogue products table"""
    pg_conn = psycopg2.connect(
        host="localhost",
        database="se_letters_dev",
        user="alexandre"
    )
    cursor = pg_conn.cursor()
    try:
        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_identifier VARCHAR PRIMARY KEY,
                product_type VARCHAR,
                product_description VARCHAR,
                brand_code VARCHAR,
                brand_label VARCHAR,
                range_code VARCHAR,
                range_label VARCHAR,
                subrange_code VARCHAR,
                subrange_label VARCHAR,
                devicetype_code VARCHAR,
                devicetype_label VARCHAR,
                is_schneider_brand BOOLEAN,
                serviceable BOOLEAN,
                traceable BOOLEAN,
                commercial_status VARCHAR,
                end_of_production_date TIMESTAMP,
                end_of_commercialisation TIMESTAMP,
                service_obsolescence_date TIMESTAMP,
                end_of_service_date TIMESTAMP,
                average_life_duration_years INTEGER,
                service_business_value VARCHAR,
                warranty_duration_months INTEGER,
                include_installation_services BOOLEAN,
                relevant_for_ip_creation BOOLEAN,
                pl_services VARCHAR,
                connectable BOOLEAN,
                gdp VARCHAR,
                bu_pm0_node VARCHAR,
                bu_label VARCHAR,
                range_label_norm VARCHAR,
                brand_label_norm VARCHAR,
                product_description_norm VARCHAR,
                created_at TIMESTAMP,
                database_version VARCHAR
            )
        """)
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_range_label ON products(range_label)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_brand_label ON products(brand_label)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_pl_services ON products(pl_services)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_commercial_status ON products(commercial_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_product_description ON products(product_description)")
        pg_conn.commit()
        print("✅ IBcatalogue products table and indexes created successfully")
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Schema creation failed: {e}")
        raise
    finally:
        cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    create_ibcatalogue_schema()

if __name__ == "__main__":
    logger.info("🚀 Starting PostgreSQL schema migration...")
    
    try:
        # Try to export DuckDB schema for reference (may fail due to locks)
        try:
            export_duckdb_schema()
        except Exception as e:
            logger.warning(f"⚠️ Could not export DuckDB schema (likely locked): {e}")
            logger.info("📝 Proceeding with PostgreSQL schema creation...")
        
        # Create PostgreSQL schema
        create_postgresql_schema()
        
        logger.success("🎉 Schema migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Schema migration failed: {e}")
        raise 