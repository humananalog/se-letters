#!/usr/bin/env python3
"""
Document Metadata Service
Converts JSON metadata outputs to DuckDB table and provides query interface
"""

import json
import duckdb
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from se_letters.core.config import get_config


class DocumentMetadataService:
    """Service for managing document metadata in DuckDB"""
    
    def __init__(self, db_path: str = "data/document_metadata.duckdb"):
        """Initialize the service with DuckDB connection"""
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._create_tables()
        logger.info(f"✅ Document Metadata Service initialized with {db_path}")
    
    def _create_tables(self):
        """Create the document metadata tables"""
        
        # Main documents table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER,
                source_file_path VARCHAR,
                document_name VARCHAR,
                document_type VARCHAR,
                language VARCHAR,
                document_number VARCHAR,
                total_products INTEGER,
                has_tables BOOLEAN,
                has_technical_specs BOOLEAN,
                extraction_complexity VARCHAR,
                extraction_confidence FLOAT,
                processing_timestamp VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Products table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS document_products (
                id INTEGER,
                document_id INTEGER,
                product_identifier VARCHAR,
                range_label VARCHAR,
                subrange_label VARCHAR,
                product_line VARCHAR,
                product_description TEXT,
                voltage_level VARCHAR,
                current_rating VARCHAR,
                power_rating VARCHAR,
                frequency VARCHAR,
                part_number VARCHAR,
                obsolescence_status VARCHAR,
                last_order_date VARCHAR,
                end_of_service_date VARCHAR,
                replacement_suggestions TEXT,
                migration_path TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Business information table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS document_business_info (
                id INTEGER,
                document_id INTEGER,
                affected_ranges TEXT,
                affected_countries TEXT,
                customer_segments TEXT,
                business_impact TEXT,
                announcement_date VARCHAR,
                effective_date VARCHAR,
                last_order_date_key VARCHAR,
                end_of_service_date_key VARCHAR,
                spare_parts_availability VARCHAR,
                contact_details TEXT,
                migration_guidance TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        logger.info("✅ Document metadata tables created/verified")
    
    def import_json_metadata(self, json_file_path: str) -> int:
        """Import metadata from JSON file into DuckDB tables"""
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Extract document name from file path
            document_name = Path(json_file_path).stem.replace('enhanced_grok_output_', '').replace('_20250713_', '_')
            
            # Insert document record
            doc_info = metadata.get('document_information', {})
            
            self.conn.execute("""
                INSERT INTO documents (
                    source_file_path, document_name, document_type, language,
                    document_number, total_products, has_tables, has_technical_specs,
                    extraction_complexity, extraction_confidence, processing_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
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
            
            # Get the document ID
            doc_id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Insert product records
            products = metadata.get('product_information', [])
            for product in products:
                tech_specs = product.get('technical_specifications', {})
                commercial_info = product.get('commercial_information', {})
                replacement_info = product.get('replacement_information', {})
                
                self.conn.execute("""
                    INSERT INTO document_products (
                        document_id, product_identifier, range_label, subrange_label,
                        product_line, product_description, voltage_level, current_rating,
                        power_rating, frequency, part_number, obsolescence_status,
                        last_order_date, end_of_service_date, replacement_suggestions,
                        migration_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    doc_id,
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
            
            # Insert business information
            business_info = metadata.get('business_information', {})
            lifecycle_info = metadata.get('lifecycle_information', {})
            contact_info = metadata.get('contact_information', {})
            key_dates = lifecycle_info.get('key_dates', {})
            
            self.conn.execute("""
                INSERT INTO document_business_info (
                    document_id, affected_ranges, affected_countries, customer_segments,
                    business_impact, announcement_date, effective_date,
                    last_order_date_key, end_of_service_date_key, spare_parts_availability,
                    contact_details, migration_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                doc_id,
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
            
            logger.info(f"✅ Imported metadata for document ID {doc_id}: {document_name}")
            return doc_id
            
        except Exception as e:
            logger.error(f"❌ Failed to import JSON metadata: {e}")
            raise
    
    def import_all_json_files(self, json_directory: str = "data/test/debug") -> List[int]:
        """Import all JSON files from directory"""
        
        json_files = list(Path(json_directory).glob("enhanced_grok_output_*.json"))
        imported_ids = []
        
        logger.info(f"🔄 Importing {len(json_files)} JSON files from {json_directory}")
        
        for json_file in json_files:
            try:
                doc_id = self.import_json_metadata(str(json_file))
                imported_ids.append(doc_id)
            except Exception as e:
                logger.error(f"❌ Failed to import {json_file}: {e}")
        
        logger.info(f"✅ Successfully imported {len(imported_ids)} documents")
        return imported_ids
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents with summary information"""
        
        result = self.conn.execute("""
            SELECT 
                d.id,
                d.document_name,
                d.document_type,
                d.language,
                d.total_products,
                d.extraction_confidence,
                d.extraction_complexity,
                d.has_technical_specs,
                d.processing_timestamp,
                COUNT(p.id) as actual_products,
                STRING_AGG(DISTINCT p.product_line, ', ') as product_lines,
                ANY_VALUE(d.created_at) as created_at
            FROM documents d
            LEFT JOIN document_products p ON d.id = p.document_id
            GROUP BY d.id, d.document_name, d.document_type, d.language, 
                     d.total_products, d.extraction_confidence, d.extraction_complexity,
                     d.has_technical_specs, d.processing_timestamp
            ORDER BY created_at DESC
        """).fetchall()
        
        columns = [desc[0] for desc in self.conn.description]
        return [dict(zip(columns, row)) for row in result]
    
    def get_document_details(self, document_id: int) -> Dict[str, Any]:
        """Get complete details for a specific document"""
        
        # Get document info
        doc_result = self.conn.execute("""
            SELECT * FROM documents WHERE id = ?
        """, [document_id]).fetchone()
        
        if not doc_result:
            return {}
        
        doc_columns = [desc[0] for desc in self.conn.description]
        document = dict(zip(doc_columns, doc_result))
        
        # Get products
        products_result = self.conn.execute("""
            SELECT * FROM document_products WHERE document_id = ?
        """, [document_id]).fetchall()
        
        if products_result:
            product_columns = [desc[0] for desc in self.conn.description]
            document['products'] = [dict(zip(product_columns, row)) for row in products_result]
        else:
            document['products'] = []
        
        # Get business info
        business_result = self.conn.execute("""
            SELECT * FROM document_business_info WHERE document_id = ?
        """, [document_id]).fetchone()
        
        if business_result:
            business_columns = [desc[0] for desc in self.conn.description]
            document['business_info'] = dict(zip(business_columns, business_result))
        else:
            document['business_info'] = {}
        
        return document
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        
        stats = {}
        
        # Document counts
        stats['total_documents'] = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        stats['total_products'] = self.conn.execute("SELECT COUNT(*) FROM document_products").fetchone()[0]
        
        # Average confidence
        avg_confidence = self.conn.execute("SELECT AVG(extraction_confidence) FROM documents").fetchone()[0]
        stats['average_confidence'] = round(avg_confidence, 2) if avg_confidence else 0
        
        # Product line distribution
        product_lines = self.conn.execute("""
            SELECT product_line, COUNT(*) as count 
            FROM document_products 
            GROUP BY product_line 
            ORDER BY count DESC
        """).fetchall()
        stats['product_line_distribution'] = {pl: count for pl, count in product_lines}
        
        # Language distribution
        languages = self.conn.execute("""
            SELECT language, COUNT(*) as count 
            FROM documents 
            GROUP BY language 
            ORDER BY count DESC
        """).fetchall()
        stats['language_distribution'] = {lang: count for lang, count in languages}
        
        return stats
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("📝 Document Metadata Service closed")


def test_document_metadata_service():
    """Test the document metadata service"""
    
    service = DocumentMetadataService()
    
    # Import all JSON files
    imported_ids = service.import_all_json_files()
    print(f"✅ Imported {len(imported_ids)} documents")
    
    # Get statistics
    stats = service.get_statistics()
    print(f"📊 Statistics: {stats}")
    
    # Get all documents
    documents = service.get_all_documents()
    print(f"📄 Found {len(documents)} documents")
    
    for doc in documents:
        print(f"  - {doc['document_name']}: {doc['actual_products']} products, {doc['extraction_confidence']} confidence")
    
    service.close()


if __name__ == "__main__":
    test_document_metadata_service() 