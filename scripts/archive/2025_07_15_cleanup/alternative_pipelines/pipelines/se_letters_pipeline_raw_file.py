#!/usr/bin/env python3
"""
SE Letters Pipeline - Raw File Processing with Grok
Production-ready pipeline that processes raw files directly with Grok without OCR preprocessing.
Includes comprehensive logging, debugging, and OCR as fallback/supplementary information.

Version: 2.2.1
Release Date: 2024-01-15
Status: Production Ready - Raw File Processing (Database Fixed)
Architecture: Direct Grok Processing Pipeline
Compatibility: Python 3.9+, DuckDB, xAI Grok API

Copyright (c) 2024 Schneider Electric SE Letters Team
Licensed under MIT License

Features:
- Direct raw file processing with Grok (PDF, DOC, DOCX)
- Bypasses OCR as first step - raw files sent directly to Grok
- OCR kept as fallback/supplementary information source
- Enhanced product line classification (SPIBS for UPS/Galaxy products)
- Comprehensive logging and debugging
- DuckDB integration for results storage (FIXED)
- Webapp-compatible JSON output format
- Real-time processing with detailed performance metrics

Dependencies:
- se_letters.core.config
- se_letters.services.raw_file_grok_service
- se_letters.services.enhanced_duckdb_service

Database Fixes:
- Fixed last_insert_rowid() -> lastval() for DuckDB compatibility
- Fixed auto-increment primary key constraints
- Fixed sequence usage and table creation

Changelog:
- v2.2.1 (2024-01-15): Fixed database storage issues
- v2.2.0 (2024-01-15): Raw file processing with Grok
- v2.1.0 (2024-01-15): Production release with webapp integration
- v2.0.0 (2024-01-13): SOTA pipeline implementation

Author: SE Letters Development Team
Repository: https://github.com/humananalog/se-letters
Documentation: docs/RAW_FILE_PROCESSING_ARCHITECTURE.md
"""

import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import duckdb

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('logs/pipeline/raw_file_pipeline.log')
    ]
)

# Set up specialized loggers
logger = logging.getLogger(__name__)
performance_logger = logging.getLogger(f"{__name__}.performance")
debug_logger = logging.getLogger(f"{__name__}.debug")
error_logger = logging.getLogger(f"{__name__}.error")

# Create logs directory if it doesn't exist
Path("logs/pipeline").mkdir(parents=True, exist_ok=True)

# Set up file handlers for specialized logging
performance_handler = logging.FileHandler('logs/pipeline/performance.log')
performance_handler.setLevel(logging.INFO)
performance_logger.addHandler(performance_handler)

debug_handler = logging.FileHandler('logs/pipeline/debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_logger.addHandler(debug_handler)

error_handler = logging.FileHandler('logs/pipeline/errors.log')
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

# Try to import services
SERVICES_AVAILABLE = True
try:
    from se_letters.core.config import get_config
    from se_letters.services.raw_file_grok_service import RawFileGrokService
    from se_letters.services.enhanced_duckdb_service import EnhancedDuckDBService
    
    logger.info("✅ All services imported successfully")
    
except ImportError as e:
    logger.warning(f"⚠️ Service import failed: {e}")
    SERVICES_AVAILABLE = False
    
    # Fallback implementations
    class RawFileGrokService:
        def __init__(self, config):
            logger.warning("Using fallback RawFileGrokService")
        
        def process_raw_document(self, file_path, include_ocr_fallback=True):
            return {"error": "Service not available"}
        
        def close(self):
            pass
    
    class EnhancedDuckDBService:
        def __init__(self):
            logger.warning("Using fallback EnhancedDuckDBService")
        
        def close(self):
            pass
    
    def get_config():
        class MockConfig:
            def __init__(self):
                self.api = type('', (), {
                    'api_key': 'mock_key',
                    'base_url': 'https://api.x.ai/v1',
                    'timeout': 30
                })()
        return MockConfig()

@dataclass
class RawFileProcessingResult:
    """Enhanced processing result for raw file processing"""
    success: bool
    file_name: str
    file_path: str
    file_size: int
    processing_method: str
    
    # Raw Grok metadata
    grok_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # OCR supplementary info
    ocr_supplementary: Optional[Dict[str, Any]] = None
    
    # Legacy compatibility fields
    extracted_ranges: List[str] = field(default_factory=list)
    valid_ranges: List[str] = field(default_factory=list)
    invalid_ranges: List[str] = field(default_factory=list)
    
    # Product results
    obsolete_products: List[Dict[str, Any]] = field(default_factory=list)
    replacement_products: List[Dict[str, Any]] = field(default_factory=list)
    obsolete_count: int = 0
    replacement_count: int = 0
    
    # Performance metrics
    processing_time_ms: float = 0.0
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    extraction_confidence: float = 0.0
    
    # Error handling
    error: str = ""
    warnings: List[str] = field(default_factory=list)
    
    # Database tracking
    letter_id: int = 0

class RawFileLetterDatabaseService:
    """Database service for storing raw file processing results"""
    
    def __init__(self, db_path: str = "data/letters.duckdb"):
        self.db_path = db_path
        self.conn = None
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables for raw file processing"""
        try:
            self.conn = duckdb.connect(self.db_path)
            
            # Create sequences for auto-increment (DuckDB compatible)
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS letters_id_seq START 1")
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS products_id_seq START 1")
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS debug_id_seq START 1")
            
            # Create enhanced letters table with proper auto-increment
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS letters (
                    id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
                    document_name TEXT NOT NULL,
                    document_type TEXT,
                    document_title TEXT,
                    source_file_path TEXT NOT NULL,
                    file_size INTEGER,
                    processing_method TEXT DEFAULT 'raw_file_grok',
                    processing_time_ms REAL,
                    extraction_confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'processed',
                    raw_grok_json TEXT,
                    ocr_supplementary_json TEXT,
                    processing_steps_json TEXT
                )
            """)
            
            # Create products table with proper auto-increment
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS letter_products (
                    id INTEGER PRIMARY KEY DEFAULT nextval('products_id_seq'),
                    letter_id INTEGER NOT NULL,
                    product_identifier TEXT,
                    range_label TEXT,
                    subrange_label TEXT,
                    product_line TEXT,
                    product_description TEXT,
                    obsolescence_status TEXT,
                    end_of_service_date TEXT,
                    replacement_suggestions TEXT,
                    FOREIGN KEY (letter_id) REFERENCES letters(id)
                )
            """)
            
            # Create processing debug table with proper auto-increment
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_debug (
                    id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
                    letter_id INTEGER NOT NULL,
                    processing_step TEXT NOT NULL,
                    step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    step_duration_ms REAL,
                    step_success BOOLEAN DEFAULT TRUE,
                    step_details TEXT,
                    FOREIGN KEY (letter_id) REFERENCES letters(id)
                )
            """)
            
            logger.info("Raw file processing database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def store_processing_result(self, result: RawFileProcessingResult) -> int:
        """Store raw file processing result in database"""
        try:
            # Insert letter record
            self.conn.execute("""
                INSERT INTO letters (
                    document_name, document_type, document_title, source_file_path,
                    file_size, processing_method, processing_time_ms, extraction_confidence,
                    status, raw_grok_json, ocr_supplementary_json, processing_steps_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                result.file_name,
                result.grok_metadata.get('document_information', {}).get('document_type'),
                result.grok_metadata.get('document_information', {}).get('document_title'),
                result.file_path,
                result.file_size,
                result.processing_method,
                result.processing_time_ms,
                result.extraction_confidence,
                'processed' if result.success else 'failed',
                json.dumps(result.grok_metadata, indent=2),
                json.dumps(result.ocr_supplementary, indent=2) if result.ocr_supplementary else None,
                json.dumps(result.processing_steps, indent=2)
            ])
            
            # Get letter ID using DuckDB's currval() function
            letter_id = self.conn.execute("SELECT currval('letters_id_seq')").fetchone()[0]
            
            # Store product information
            product_info = result.grok_metadata.get('product_information', [])
            for product in product_info:
                self.conn.execute("""
                    INSERT INTO letter_products (
                        letter_id, product_identifier, range_label, subrange_label,
                        product_line, product_description, obsolescence_status,
                        end_of_service_date, replacement_suggestions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    letter_id,
                    product.get('product_identifier'),
                    product.get('range_label'),
                    product.get('subrange_label'),
                    product.get('product_line'),
                    product.get('product_description'),
                    product.get('commercial_information', {}).get('obsolescence_status'),
                    product.get('commercial_information', {}).get('end_of_service_date'),
                    json.dumps(product.get('replacement_information', {}).get('replacement_suggestions', []))
                ])
            
            # Store processing steps for debugging
            for step in result.processing_steps:
                self.conn.execute("""
                    INSERT INTO processing_debug (
                        letter_id, processing_step, step_duration_ms, 
                        step_success, step_details
                    ) VALUES (?, ?, ?, ?, ?)
                """, [
                    letter_id,
                    step.get('step'),
                    step.get('duration_ms'),
                    step.get('success'),
                    json.dumps(step, indent=2)
                ])
            
            logger.info(f"Stored processing result for letter ID: {letter_id}")
            return letter_id
            
        except Exception as e:
            logger.error(f"Failed to store processing result: {e}")
            raise
    
    def get_processed_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Check if document has already been processed"""
        try:
            result = self.conn.execute("""
                SELECT id, document_name, processing_time_ms, extraction_confidence,
                       created_at, status, raw_grok_json
                FROM letters 
                WHERE source_file_path = ? OR document_name = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, [file_path, Path(file_path).name]).fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "document_name": result[1],
                    "processing_time_ms": result[2],
                    "extraction_confidence": result[3],
                    "created_at": result[4],
                    "status": result[5],
                    "raw_grok_json": json.loads(result[6]) if result[6] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to check processed document: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class RawFileProductionPipeline:
    """Production pipeline for raw file processing"""
    
    def __init__(self):
        """Initialize the raw file processing pipeline"""
        logger.info("🚀 Initializing Raw File Production Pipeline")
        
        # Load configuration
        self.config = get_config()
        
        # Initialize services
        self.raw_grok_service = RawFileGrokService(self.config)
        self.db_service = RawFileLetterDatabaseService()
        
        # Initialize product database service if available
        if SERVICES_AVAILABLE:
            self.product_db_service = EnhancedDuckDBService()
        else:
            self.product_db_service = None
        
        logger.info("✅ Raw File Production Pipeline initialized successfully")
    
    def process_single_document(self, document_path: str) -> Dict[str, Any]:
        """Process a single document using raw file processing
        
        Args:
            document_path: Path to the document to process
            
        Returns:
            Dictionary containing processing results
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔄 Processing document: {document_path}")
            performance_logger.info(f"Started processing: {document_path}")
            
            # Check if document already processed
            existing_result = self.db_service.get_processed_document(document_path)
            if existing_result:
                logger.info(f"📋 Document already processed: {document_path}")
                return {
                    "success": True,
                    "already_processed": True,
                    "file_name": existing_result["document_name"],
                    "processing_time_ms": existing_result["processing_time_ms"],
                    "extraction_confidence": existing_result["extraction_confidence"],
                    "grok_metadata": existing_result["raw_grok_json"]
                }
            
            # Initialize result
            result = RawFileProcessingResult(
                success=False,
                file_name=Path(document_path).name,
                file_path=document_path,
                file_size=Path(document_path).stat().st_size if Path(document_path).exists() else 0,
                processing_method="raw_file_grok"
            )
            
            # Process with raw file Grok service
            grok_result = self.raw_grok_service.process_raw_document(
                Path(document_path), 
                include_ocr_fallback=True
            )
            
            # Update result with Grok metadata
            result.grok_metadata = grok_result
            result.extraction_confidence = grok_result.get('extraction_confidence', 0.0)
            result.processing_steps = grok_result.get('processing_steps', [])
            
            # Check for processing success
            if grok_result.get('error'):
                result.error = grok_result['error']
                result.success = False
            else:
                result.success = True
            
            # Extract ranges for legacy compatibility
            product_info = grok_result.get('product_information', [])
            result.extracted_ranges = [p.get('range_label', '') for p in product_info if p.get('range_label')]
            result.valid_ranges = result.extracted_ranges  # All ranges are considered valid from Grok
            
            # Validate ranges against product database if available
            if self.product_db_service:
                try:
                    valid_ranges, invalid_ranges = self.product_db_service.validate_ranges(result.extracted_ranges)
                    result.valid_ranges = valid_ranges
                    result.invalid_ranges = invalid_ranges
                    
                    # Find obsolete and replacement products
                    if valid_ranges:
                        result.obsolete_products = self.product_db_service.find_obsolete_products(valid_ranges)
                        result.replacement_products = self.product_db_service.find_replacement_products(valid_ranges)
                        result.obsolete_count = len(result.obsolete_products)
                        result.replacement_count = len(result.replacement_products)
                        
                        debug_logger.debug(f"Found {result.obsolete_count} obsolete and {result.replacement_count} replacement products")
                        
                except Exception as e:
                    logger.warning(f"Product database validation failed: {e}")
                    result.warnings.append(f"Product database validation failed: {e}")
            
            # Calculate total processing time
            total_time = (time.time() - start_time) * 1000
            result.processing_time_ms = total_time
            
            # Store in database
            try:
                result.letter_id = self.db_service.store_processing_result(result)
                logger.info(f"📊 Stored processing result with letter ID: {result.letter_id}")
            except Exception as e:
                logger.error(f"Failed to store processing result: {e}")
                result.warnings.append(f"Database storage failed: {e}")
            
            # Log performance metrics
            performance_logger.info(f"Processing completed: {document_path} in {total_time:.2f}ms")
            
            # Convert to dictionary format for webapp compatibility
            return self._result_to_dict(result)
            
        except Exception as e:
            error_logger.error(f"Failed to process document {document_path}: {e}")
            
            # Return error result
            total_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "file_name": Path(document_path).name,
                "processing_time_ms": total_time,
                "extraction_confidence": 0.0,
                "grok_metadata": {},
                "extracted_ranges": [],
                "valid_ranges": [],
                "obsolete_products": [],
                "replacement_products": [],
                "obsolete_count": 0,
                "replacement_count": 0
            }
    
    def _result_to_dict(self, result: RawFileProcessingResult) -> Dict[str, Any]:
        """Convert processing result to dictionary format"""
        return {
            "success": result.success,
            "file_name": result.file_name,
            "file_path": result.file_path,
            "file_size": result.file_size,
            "processing_method": result.processing_method,
            "processing_time_ms": result.processing_time_ms,
            "extraction_confidence": result.extraction_confidence,
            "grok_metadata": result.grok_metadata,
            "ocr_supplementary": result.ocr_supplementary,
            "extracted_ranges": result.extracted_ranges,
            "valid_ranges": result.valid_ranges,
            "invalid_ranges": result.invalid_ranges,
            "obsolete_products": result.obsolete_products,
            "replacement_products": result.replacement_products,
            "obsolete_count": result.obsolete_count,
            "replacement_count": result.replacement_count,
            "processing_steps": result.processing_steps,
            "error": result.error,
            "warnings": result.warnings,
            "letter_id": result.letter_id
        }
    
    def process_multiple_documents(self, document_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple documents"""
        results = []
        
        for doc_path in document_paths:
            result = self.process_single_document(doc_path)
            results.append(result)
        
        return results
    
    def close(self):
        """Close all service connections"""
        if self.raw_grok_service:
            self.raw_grok_service.close()
        if self.db_service:
            self.db_service.close()
        if self.product_db_service:
            self.product_db_service.close()

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Raw File Processing Pipeline')
    parser.add_argument('document_path', help='Path to document to process')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = RawFileProductionPipeline()
    
    try:
        # Process document
        result = pipeline.process_single_document(args.document_path)
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        exit_code = 0 if result['success'] else 1
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        print(f"Error: {e}")
        exit_code = 1
    
    finally:
        pipeline.close()
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 