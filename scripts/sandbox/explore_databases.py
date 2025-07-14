#!/usr/bin/env python3
"""
Database Exploration Script for Product Mapping
Explores letter database and IBcatalogue database to understand data structures
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from se_letters.core.config import get_config
from loguru import logger


class DatabaseExplorer:
    """Explores both letter database and IBcatalogue database"""
    
    def __init__(self):
        """Initialize database explorer"""
        self.config = get_config()
        self.letter_db_path = "data/letters.duckdb"
        self.ibcatalogue_db_path = "data/IBcatalogue.duckdb"
        self.ibcatalogue_excel_path = "data/input/letters/IBcatalogue.xlsx"
        
        logger.info("🔍 Database Explorer initialized")
    
    def explore_letter_database(self):
        """Explore the letter database structure and Galaxy 6000 data"""
        logger.info("📊 Exploring Letter Database")
        
        try:
            with duckdb.connect(self.letter_db_path) as conn:
                # 1. Show database structure
                logger.info("=== LETTER DATABASE STRUCTURE ===")
                
                tables = conn.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'main'
                """).fetchall()
                
                for table in tables:
                    table_name = table[0]
                    logger.info(f"\n📋 Table: {table_name}")
                    
                    # Show columns
                    columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    for col in columns:
                        logger.info(f"  - {col[0]}: {col[1]}")
                    
                    # Show count
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    logger.info(f"  📊 Records: {count}")
                
                # 2. Find Galaxy 6000 data
                logger.info("\n=== GALAXY 6000 DATA ===")
                
                # Search for Galaxy letters
                galaxy_letters = conn.execute("""
                    SELECT id, document_name, document_title, status, 
                           extraction_confidence, created_at
                    FROM letters 
                    WHERE document_name ILIKE '%galaxy%' 
                       OR document_title ILIKE '%galaxy%'
                    ORDER BY created_at DESC
                """).fetchall()
                
                logger.info(f"Found {len(galaxy_letters)} Galaxy letters:")
                for letter in galaxy_letters:
                    logger.info(f"  ID: {letter[0]}, Name: {letter[1]}, "
                               f"Title: {letter[2]}")
                
                # Get Galaxy products from letter database
                if galaxy_letters:
                    galaxy_letter_id = galaxy_letters[0][0]  # Most recent
                    logger.info(f"\n📦 Products from Galaxy Letter "
                               f"ID={galaxy_letter_id}:")
                    
                    galaxy_products = conn.execute("""
                        SELECT 
                            product_identifier, range_label, subrange_label, 
                            product_line, product_description, 
                            obsolescence_status, end_of_service_date,
                            confidence_score
                        FROM letter_products 
                        WHERE letter_id = ?
                    """, [galaxy_letter_id]).fetchall()
                    
                    for product in galaxy_products:
                        logger.info(f"  🔧 {product[0]} | {product[1]} | "
                                   f"{product[2]} | {product[3]}")
                        logger.info(f"     Description: {product[4]}")
                        logger.info(f"     Status: {product[5]} | End: "
                                   f"{product[6]} | Confidence: {product[7]}")
                
        except Exception as e:
            logger.error(f"❌ Error exploring letter database: {e}")
    
    def explore_ibcatalogue_database(self):
        """Explore the IBcatalogue database structure and Galaxy products"""
        logger.info("\n📊 Exploring IBcatalogue Database")
        
        # First try DuckDB, then Excel if DuckDB doesn't exist
        ibcatalogue_data = None
        
        if Path(self.ibcatalogue_db_path).exists():
            logger.info(f"Using DuckDB: {self.ibcatalogue_db_path}")
            try:
                with duckdb.connect(self.ibcatalogue_db_path) as conn:
                    # Show structure
                    tables = conn.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'main'
                    """).fetchall()
                    
                    logger.info("=== IBCATALOGUE DATABASE STRUCTURE ===")
                    for table in tables:
                        table_name = table[0]
                        logger.info(f"\n📋 Table: {table_name}")
                        
                        columns = conn.execute(f"DESCRIBE {table_name}").fetchall()
                        for col in columns:
                            logger.info(f"  - {col[0]}: {col[1]}")
                        
                        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        logger.info(f"  📊 Records: {count}")
                    
                    # Search for Galaxy products
                    self._search_galaxy_products_duckdb(conn)
                    
            except Exception as e:
                logger.error(f"❌ Error with DuckDB: {e}")
                ibcatalogue_data = None
        
        # Fallback to Excel
        if ibcatalogue_data is None and Path(self.ibcatalogue_excel_path).exists():
            logger.info(f"Using Excel: {self.ibcatalogue_excel_path}")
            self._search_galaxy_products_excel()
    
    def _search_galaxy_products_duckdb(self, conn):
        """Search for Galaxy products in DuckDB"""
        logger.info("\n=== GALAXY PRODUCTS IN IBCATALOGUE (DuckDB) ===")
        
        # Search for Galaxy products
        galaxy_products = conn.execute("""
            SELECT 
                PRODUCT_IDENTIFIER, RANGE_LABEL, SUBRANGE_LABEL,
                PRODUCT_DESCRIPTION, PL_SERVICES, COMMERCIAL_STATUS,
                BRAND_LABEL, BU_LABEL
            FROM products
            WHERE RANGE_LABEL ILIKE '%galaxy%' 
               OR PRODUCT_DESCRIPTION ILIKE '%galaxy%'
               OR PRODUCT_IDENTIFIER ILIKE '%galaxy%'
            ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER
            LIMIT 20
        """).fetchall()
        
        logger.info(f"Found {len(galaxy_products)} Galaxy products in IBcatalogue:")
        for product in galaxy_products:
            logger.info(f"  🔧 {product[0]} | {product[1]} | {product[2]}")
            logger.info(f"     Description: {product[3]}")
            logger.info(f"     PL_SERVICES: {product[4]} | Status: {product[5]}")
            logger.info(f"     Brand: {product[6]} | BU: {product[7]}")
            logger.info("     ---")
        
        # Check SPIBS products (Galaxy is SPIBS)
        logger.info("\n=== SPIBS PRODUCTS SAMPLE ===")
        spibs_products = conn.execute("""
            SELECT 
                PRODUCT_IDENTIFIER, RANGE_LABEL, SUBRANGE_LABEL,
                PRODUCT_DESCRIPTION, COMMERCIAL_STATUS
            FROM products
            WHERE PL_SERVICES = 'SPIBS'
            ORDER BY RANGE_LABEL
            LIMIT 10
        """).fetchall()
        
        for product in spibs_products:
            logger.info(f"  🔧 {product[0]} | {product[1]} | {product[2]}")
            logger.info(f"     Description: {product[3]} | Status: {product[4]}")
    
    def _search_galaxy_products_excel(self):
        """Search for Galaxy products in Excel file"""
        logger.info("\n=== GALAXY PRODUCTS IN IBCATALOGUE (Excel) ===")
        
        try:
            # Load Excel data
            df = pd.read_excel(self.ibcatalogue_excel_path, sheet_name='OIC_out')
            logger.info(f"Loaded {len(df)} products from Excel")
            
            # Show columns
            logger.info("Available columns:")
            for col in df.columns:
                logger.info(f"  - {col}")
            
            # Search for Galaxy products
            galaxy_mask = (
                df['RANGE_LABEL'].str.contains('Galaxy', case=False, na=False) |
                df['PRODUCT_DESCRIPTION'].str.contains('Galaxy', case=False, na=False) |
                df['PRODUCT_IDENTIFIER'].str.contains('Galaxy', case=False, na=False)
            )
            
            galaxy_products = df[galaxy_mask].head(20)
            logger.info(f"\nFound {len(galaxy_products)} Galaxy products:")
            
            for _, product in galaxy_products.iterrows():
                logger.info(f"  🔧 {product['PRODUCT_IDENTIFIER']} | "
                           f"{product['RANGE_LABEL']} | "
                           f"{product.get('SUBRANGE_LABEL', 'N/A')}")
                logger.info(f"     Description: {product['PRODUCT_DESCRIPTION']}")
                logger.info(f"     PL_SERVICES: {product.get('PL_SERVICES', 'N/A')} | "
                           f"Status: {product.get('COMMERCIAL_STATUS', 'N/A')}")
                logger.info("     ---")
            
            # Check SPIBS products
            logger.info("\n=== SPIBS PRODUCTS SAMPLE ===")
            spibs_mask = df['PL_SERVICES'] == 'SPIBS'
            spibs_products = df[spibs_mask].head(10)
            
            for _, product in spibs_products.iterrows():
                logger.info(f"  🔧 {product['PRODUCT_IDENTIFIER']} | "
                           f"{product['RANGE_LABEL']} | "
                           f"{product.get('SUBRANGE_LABEL', 'N/A')}")
                logger.info(f"     Description: {product['PRODUCT_DESCRIPTION']}")
                
        except Exception as e:
            logger.error(f"❌ Error reading Excel: {e}")
    
    def analyze_mapping_challenge(self):
        """Analyze the mapping challenge between letter and IBcatalogue"""
        logger.info("\n🧩 MAPPING CHALLENGE ANALYSIS")
        
        logger.info("From Galaxy 6000 example:")
        logger.info("  Letter DB: product_identifier='Galaxy 6000', "
                   "range_label='Galaxy', subrange_label='6000', "
                   "product_line='SPIBS'")
        logger.info("  Challenge: Find matching products in IBcatalogue "
                   "with 342,229 products")
        logger.info("  Strategy needed:")
        logger.info("    1. Filter by PL_SERVICES = 'SPIBS' (macro filter)")
        logger.info("    2. Filter by RANGE_LABEL containing 'Galaxy'")
        logger.info("    3. Filter by SUBRANGE_LABEL or identifier containing '6000'")
        logger.info("    4. Use fuzzy matching for product descriptions")
        logger.info("    5. Score and rank candidates by confidence")
    
    def run_exploration(self):
        """Run complete database exploration"""
        logger.info("🚀 Starting Database Exploration for Product Mapping")
        
        self.explore_letter_database()
        self.explore_ibcatalogue_database()
        self.analyze_mapping_challenge()
        
        logger.info("✅ Database exploration completed")


if __name__ == "__main__":
    explorer = DatabaseExplorer()
    explorer.run_exploration() 