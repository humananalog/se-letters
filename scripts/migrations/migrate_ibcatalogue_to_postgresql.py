#!/usr/bin/env python3
"""
IBcatalogue Migration Script - Excel to PostgreSQL
Migrates IBcatalogue data from Excel to PostgreSQL products table

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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config


def create_products_table(connection_string: str):
    """Create the products table in PostgreSQL"""
    logger.info("🔧 Creating products table in PostgreSQL...")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        product_identifier TEXT,
        product_type TEXT,
        product_description TEXT,
        brand_code TEXT,
        brand_label TEXT,
        range_code TEXT,
        range_label TEXT,
        subrange_code TEXT,
        subrange_label TEXT,
        devicetype_code TEXT,
        devicetype_label TEXT,
        is_schneider_brand BOOLEAN,
        serviceable BOOLEAN,
        traceable BOOLEAN,
        commercial_status TEXT,
        end_of_production_date TEXT,
        end_of_commercialisation TEXT,
        service_obsolecense_date TEXT,
        end_of_service_date TEXT,
        average_life_duration_in_years TEXT,
        service_business_value TEXT,
        warranty_duration_in_months TEXT,
        include_installation_services BOOLEAN,
        relevant_for_ip_creation BOOLEAN,
        pl_services TEXT,
        connectable BOOLEAN,
        gdp TEXT,
        bu_pm0_node TEXT,
        bu_label TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
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
    """Load IBcatalogue data from Excel to PostgreSQL"""
    logger.info(f"📊 Loading IBcatalogue data from: {excel_path}")
    
    # Read Excel file
    logger.info("📖 Reading Excel file...")
    df = pd.read_excel(excel_path, sheet_name='OIC_out')
    logger.info(f"📊 Loaded {len(df)} products with {len(df.columns)} columns")
    
    # Display column names for reference
    logger.info(f"📋 Columns: {list(df.columns)}")
    
    # Map Excel columns to database columns (1:1)
    column_mapping = {
        'PRODUCT_IDENTIFIER': 'product_identifier',
        'PRODUCT_TYPE': 'product_type',
        'PRODUCT_DESCRIPTION': 'product_description',
        'BRAND_CODE': 'brand_code',
        'BRAND_LABEL': 'brand_label',
        'RANGE_CODE': 'range_code',
        'RANGE_LABEL': 'range_label',
        'SUBRANGE_CODE': 'subrange_code',
        'SUBRANGE_LABEL': 'subrange_label',
        'DEVICETYPE_CODE': 'devicetype_code',
        'DEVICETYPE_LABEL': 'devicetype_label',
        'IS_SCHNEIDER_BRAND': 'is_schneider_brand',
        'SERVICEABLE': 'serviceable',
        'TRACEABLE': 'traceable',
        'COMMERCIAL_STATUS': 'commercial_status',
        'END_OF_PRODUCTION_DATE': 'end_of_production_date',
        'END_OF_COMMERCIALISATION': 'end_of_commercialisation',
        'SERVICE_OBSOLECENSE_DATE': 'service_obsolecense_date',
        'END_OF_SERVICE_DATE': 'end_of_service_date',
        'AVERAGE_LIFE_DURATION_IN_YEARS': 'average_life_duration_in_years',
        'SERVICE_BUSINESS_VALUE': 'service_business_value',
        'WARRANTY_DURATION_IN_MONTHS': 'warranty_duration_in_months',
        'INCLUDE_INSTALLATION_SERVICES': 'include_installation_services',
        'RELEVANT_FOR_IP_CREATION': 'relevant_for_ip_creation',
        'PL_SERVICES': 'pl_services',
        'CONNECTABLE': 'connectable',
        'GDP': 'gdp',
        'BU_PM0_NODE': 'bu_pm0_node',
        'BU_LABEL': 'bu_label'
    }
    
    # Rename columns to match database schema
    df_renamed = df.rename(columns=column_mapping)
    db_columns = list(column_mapping.values())
    df_final = df_renamed[db_columns].copy()
    
    # Clean data
    logger.info("🧹 Cleaning data...")
    df_final = df_final.fillna('')
    
    # Convert boolean columns
    boolean_columns = ['is_schneider_brand', 'serviceable']
    for col in boolean_columns:
        if col in df_final.columns:
            df_final[col] = df_final[col].astype(str).str.lower().isin(['true', '1', 'yes', 'y'])
    
    # Insert data into PostgreSQL
    logger.info("💾 Inserting data into PostgreSQL...")
    start_time = time.time()
    
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Prepare insert statement
                columns = ', '.join(db_columns)
                placeholders = ', '.join(['%s'] * len(db_columns))
                insert_sql = f"INSERT INTO products ({columns}) VALUES ({placeholders})"
                
                # Convert DataFrame to list of tuples
                data_tuples = [tuple(row) for row in df_final.values]
                
                # Insert in batches
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


def verify_migration(connection_string: str):
    """Verify the migration was successful"""
    logger.info("🔍 Verifying migration...")
    
    try:
        with psycopg2.connect(connection_string) as conn:
            with conn.cursor() as cur:
                # Check total count
                cur.execute("SELECT COUNT(*) FROM products")
                total_products = cur.fetchone()[0]
                logger.info(f"📊 Total products in database: {total_products}")
                
                # Check for PIX products
                cur.execute("SELECT COUNT(*) FROM products WHERE range_label ILIKE '%PIX%'")
                pix_products = cur.fetchone()[0]
                logger.info(f"🎯 PIX products found: {pix_products}")
                
                # Check for PIX2B specifically
                cur.execute("SELECT COUNT(*) FROM products WHERE range_label ILIKE '%PIX2B%' OR product_identifier ILIKE '%PIX2B%'")
                pix2b_products = cur.fetchone()[0]
                logger.info(f"🎯 PIX2B products found: {pix2b_products}")
                
                # Show sample products
                cur.execute("SELECT product_identifier, range_label, brand_label FROM products WHERE range_label ILIKE '%PIX%' LIMIT 5")
                sample_products = cur.fetchall()
                logger.info("📋 Sample PIX products:")
                for product in sample_products:
                    logger.info(f"   - {product[0]} | {product[1]} | {product[2]}")
                
                if total_products > 0:
                    logger.success("✅ Migration verification successful!")
                    return True
                else:
                    logger.error("❌ No products found in database!")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def main():
    """Main migration function"""
    logger.info("🚀 Starting IBcatalogue migration to PostgreSQL...")
    
    # Get configuration
    config = get_config()
    connection_string = config.data.database.letter_database
    excel_path = "data/input/letters/IBcatalogue.xlsx"
    
    # Verify files exist
    if not Path(excel_path).exists():
        logger.error(f"❌ IBcatalogue Excel file not found: {excel_path}")
        return False
    
    try:
        # Step 1: Create products table
        create_products_table(connection_string)
        
        # Step 2: Load data
        load_ibcatalogue_data(excel_path, connection_string)
        
        # Step 3: Verify migration
        success = verify_migration(connection_string)
        
        if success:
            logger.success("🎉 IBcatalogue migration completed successfully!")
            return True
        else:
            logger.error("❌ Migration verification failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 