#!/usr/bin/env python3
"""
Simple script to convert JSON metadata to DuckDB tables
"""

import json
import duckdb
from pathlib import Path
from loguru import logger


def convert_json_to_duckdb():
    """Convert JSON metadata files to DuckDB tables"""
    
    # Connect to DuckDB
    conn = duckdb.connect('data/document_metadata.duckdb')
    
    # Drop existing tables if they exist
    conn.execute("DROP TABLE IF EXISTS document_business_info")
    conn.execute("DROP TABLE IF EXISTS document_products")
    conn.execute("DROP TABLE IF EXISTS documents")
    
    # Create simple tables
    conn.execute("""
        CREATE TABLE documents (
            id INTEGER,
            source_file_path TEXT,
            document_name TEXT,
            document_type TEXT,
            language TEXT,
            document_number TEXT,
            total_products INTEGER,
            has_tables BOOLEAN,
            has_technical_specs BOOLEAN,
            extraction_complexity TEXT,
            extraction_confidence REAL,
            processing_timestamp TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE document_products (
            document_id INTEGER,
            product_identifier TEXT,
            range_label TEXT,
            subrange_label TEXT,
            product_line TEXT,
            product_description TEXT,
            voltage_level TEXT,
            current_rating TEXT,
            power_rating TEXT,
            frequency TEXT,
            part_number TEXT,
            obsolescence_status TEXT,
            last_order_date TEXT,
            end_of_service_date TEXT,
            replacement_suggestions TEXT,
            migration_path TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE document_business_info (
            document_id INTEGER,
            affected_ranges TEXT,
            affected_countries TEXT,
            customer_segments TEXT,
            business_impact TEXT,
            announcement_date TEXT,
            effective_date TEXT,
            last_order_date_key TEXT,
            end_of_service_date_key TEXT,
            spare_parts_availability TEXT,
            contact_details TEXT,
            migration_guidance TEXT
        )
    """)
    
    logger.info("✅ Created DuckDB tables")
    
    # Find JSON files
    json_files = list(Path("data/test/debug").glob("enhanced_grok_output_*.json"))
    logger.info(f"🔄 Found {len(json_files)} JSON files to process")
    
    document_id = 1
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Extract document name
            document_name = json_file.stem.replace('enhanced_grok_output_', '').split('_20250713_')[0]
            
            # Insert document
            doc_info = metadata.get('document_information', {})
            conn.execute("""
                INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                document_id,
                metadata.get('source_file_path'),
                document_name,
                doc_info.get('document_type'),
                doc_info.get('language'),
                doc_info.get('document_number'),
                doc_info.get('total_products'),
                doc_info.get('has_tables'),
                doc_info.get('has_technical_specs'),
                doc_info.get('extraction_complexity'),
                metadata.get('extraction_confidence'),
                metadata.get('processing_timestamp')
            ])
            
            # Insert products
            products = metadata.get('product_information', [])
            for product in products:
                tech_specs = product.get('technical_specifications', {})
                commercial_info = product.get('commercial_information', {})
                replacement_info = product.get('replacement_information', {})
                
                conn.execute("""
                    INSERT INTO document_products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    document_id,
                    product.get('product_identifier'),
                    product.get('range_label'),
                    product.get('subrange_label'),
                    product.get('product_line'),
                    product.get('product_description'),
                    tech_specs.get('voltage_level'),
                    tech_specs.get('current_rating'),
                    tech_specs.get('power_rating'),
                    tech_specs.get('frequency'),
                    commercial_info.get('part_number'),
                    commercial_info.get('obsolescence_status'),
                    commercial_info.get('last_order_date'),
                    commercial_info.get('end_of_service_date'),
                    json.dumps(replacement_info.get('replacement_suggestions', [])),
                    replacement_info.get('migration_path')
                ])
            
            # Insert business info
            business_info = metadata.get('business_information', {})
            lifecycle_info = metadata.get('lifecycle_information', {})
            contact_info = metadata.get('contact_information', {})
            key_dates = lifecycle_info.get('key_dates', {})
            
            conn.execute("""
                INSERT INTO document_business_info VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                document_id,
                json.dumps(business_info.get('affected_ranges', [])),
                json.dumps(business_info.get('affected_countries', [])),
                json.dumps(business_info.get('customer_segments', [])),
                business_info.get('business_impact'),
                lifecycle_info.get('announcement_date'),
                lifecycle_info.get('effective_date'),
                key_dates.get('last_order_date'),
                key_dates.get('end_of_service_date'),
                key_dates.get('spare_parts_availability_duration'),
                contact_info.get('contact_details'),
                contact_info.get('migration_guidance')
            ])
            
            logger.info(f"✅ Imported document {document_id}: {document_name}")
            document_id += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to import {json_file}: {e}")
    
    # Show statistics
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    product_count = conn.execute("SELECT COUNT(*) FROM document_products").fetchone()[0]
    avg_confidence = conn.execute("SELECT AVG(extraction_confidence) FROM documents").fetchone()[0]
    
    logger.info(f"📊 Import complete: {doc_count} documents, {product_count} products, {avg_confidence:.2f} avg confidence")
    
    # Show sample data
    print("\n📄 Documents:")
    documents = conn.execute("""
        SELECT id, document_name, total_products, extraction_confidence, product_line_summary
        FROM (
            SELECT 
                d.id,
                d.document_name,
                d.total_products,
                d.extraction_confidence,
                STRING_AGG(DISTINCT p.product_line, ', ') as product_line_summary
            FROM documents d
            LEFT JOIN document_products p ON d.id = p.document_id
            GROUP BY d.id, d.document_name, d.total_products, d.extraction_confidence
        )
    """).fetchall()
    
    for doc in documents:
        print(f"  {doc[0]}: {doc[1]} - {doc[2]} products, {doc[3]:.2f} confidence, {doc[4]} lines")
    
    conn.close()


if __name__ == "__main__":
    convert_json_to_duckdb() 