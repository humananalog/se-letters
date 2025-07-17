#!/usr/bin/env python3
"""
IBcatalogue Clean Migration Script - Excel to PostgreSQL
Reads IBcatalogue.xlsx, maps and cleans all fields, converts dates to ISO, and loads into PostgreSQL.

Author: Alexandre Huther
Date: 2025-07-17
"""

import pandas as pd
import psycopg2
import psycopg2.extras
from pathlib import Path
from loguru import logger
import sys
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from se_letters.core.config import get_config

# Field mapping: Excel column -> (PostgreSQL column, type)
FIELD_MAP = [
    ("PRODUCT_IDENTIFIER", ("product_identifier", "TEXT")),
    ("PRODUCT_TYPE", ("product_type", "TEXT")),
    ("PRODUCT_DESCRIPTION", ("product_description", "TEXT")),
    ("BRAND_CODE", ("brand_code", "TEXT")),
    ("BRAND_LABEL", ("brand_label", "TEXT")),
    ("RANGE_CODE", ("range_code", "TEXT")),
    ("RANGE_LABEL", ("range_label", "TEXT")),
    ("SUBRANGE_CODE", ("subrange_code", "TEXT")),
    ("SUBRANGE_LABEL", ("subrange_label", "TEXT")),
    ("DEVICETYPE_CODE", ("devicetype_code", "TEXT")),
    ("DEVICETYPE_LABEL", ("devicetype_label", "TEXT")),
    ("IS_SCHNEIDER_BRAND", ("is_schneider_brand", "BOOLEAN")),
    ("SERVICEABLE", ("serviceable", "BOOLEAN")),
    ("TRACEABLE", ("traceable", "BOOLEAN")),
    ("COMMERCIAL_STATUS", ("commercial_status", "TEXT")),
    ("END_OF_PRODUCTION_DATE", ("end_of_production_date", "DATE")),
    ("END_OF_COMMERCIALISATION", ("end_of_commercialisation", "DATE")),
    ("SERVICE_OBSOLECENSE_DATE", ("service_obsolescence_date", "DATE")),
    ("END_OF_SERVICE_DATE", ("end_of_service_date", "DATE")),
    ("AVERAGE_LIFE_DURATION_IN_YEARS", ("average_life_years", "NUMERIC")),
    ("SERVICE_BUSINESS_VALUE", ("service_business_value", "TEXT")),
    ("WARRANTY_DURATION_IN_MONTHS", ("warranty_months", "NUMERIC")),
    ("INCLUDE_INSTALLATION_SERVICES", ("include_installation_services", "BOOLEAN")),
    ("RELEVANT_FOR_IP_CREATION", ("relevant_for_ip_creation", "BOOLEAN")),
    ("PL_SERVICES", ("pl_services", "TEXT")),
    ("CONNECTABLE", ("connectable", "BOOLEAN")),
    ("GDP", ("gdp", "TEXT")),
    ("BU_PM0_NODE", ("bu_pm0_node", "TEXT")),
    ("BU_LABEL", ("bu_label", "TEXT")),
]

# Helper for date conversion
def to_iso_date(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    if isinstance(val, datetime):
        return val.date().isoformat()
    try:
        # Try parsing as string
        return pd.to_datetime(str(val)).date().isoformat()
    except Exception:
        return None

# Helper for boolean conversion
def to_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ["true", "1", "yes", "y"]:
        return True
    if s in ["false", "0", "no", "n"]:
        return False
    return None

# Helper for numeric conversion
def to_numeric(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    try:
        return float(val)
    except Exception:
        return None

def create_products_table(connection_string: str):
    logger.info("🔧 Creating products table in PostgreSQL...")
    columns = []
    for _, (pg_col, pg_type) in FIELD_MAP:
        if pg_type == "BOOLEAN":
            columns.append(f"{pg_col} BOOLEAN")
        elif pg_type == "DATE":
            columns.append(f"{pg_col} DATE")
        elif pg_type == "NUMERIC":
            columns.append(f"{pg_col} NUMERIC")
        else:
            columns.append(f"{pg_col} TEXT")
    columns.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    create_table_sql = f"""
    DROP TABLE IF EXISTS products CASCADE;
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        {',\n        '.join(columns)}
    );
    """
    logger.info(f"🔧 Creating table with SQL:\n{create_table_sql}")
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                conn.commit()
                logger.success("✅ Products table created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create products table: {e}")
        raise

def load_ibcatalogue_data(excel_path: str, connection_string: str):
    logger.info(f"📊 Loading IBcatalogue data from: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name='OIC_out')
    logger.info(f"📊 Loaded {len(df)} products with {len(df.columns)} columns")
    logger.info(f"📋 Columns: {list(df.columns)}")
    # Build cleaned DataFrame
    cleaned = {}
    for excel_col, (pg_col, pg_type) in FIELD_MAP:
        if pg_type == "BOOLEAN":
            cleaned[pg_col] = df[excel_col].apply(to_bool)
        elif pg_type == "DATE":
            cleaned[pg_col] = df[excel_col].apply(to_iso_date)
        elif pg_type == "NUMERIC":
            cleaned[pg_col] = df[excel_col].apply(to_numeric)
        else:
            cleaned[pg_col] = df[excel_col].astype(str).replace('nan', '').replace('NaT', '')
    import_df = pd.DataFrame(cleaned)
    logger.info(f"🧹 Cleaned DataFrame shape: {import_df.shape}")
    logger.info(f"📋 DataFrame columns: {list(import_df.columns)}")
    # Insert into PostgreSQL
    logger.info("💾 Inserting data into PostgreSQL...")
    start_time = time.time()
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                columns = list(import_df.columns)
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO products ({', '.join(columns)}) VALUES ({placeholders})"
                data_tuples = [tuple(row) for row in import_df.values]
                batch_size = 1000
                total_inserted = 0
                for i in range(0, len(data_tuples), batch_size):
                    batch = data_tuples[i:i + batch_size]
                    psycopg2.extras.execute_batch(cur, insert_sql, batch)
                    total_inserted += len(batch)
                    if i % 10000 == 0:
                        logger.info(f"📊 Inserted {total_inserted}/{len(data_tuples)} products...")
                conn.commit()
                duration = time.time() - start_time
                logger.success(f"✅ Successfully inserted {total_inserted} products in {duration:.2f} seconds")
    except Exception as e:
        logger.error(f"❌ Failed to insert data: {e}")
        raise

def main():
    logger.info("🚀 Starting IBcatalogue clean migration to PostgreSQL...")
    config = get_config()
    connection_string = config.data.database.letter_database
    excel_path = "data/input/letters/IBcatalogue.xlsx"
    if not Path(excel_path).exists():
        logger.error(f"❌ IBcatalogue Excel file not found: {excel_path}")
        return False
    try:
        create_products_table(connection_string)
        load_ibcatalogue_data(excel_path, connection_string)
        logger.success("🎉 IBcatalogue clean migration completed successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 