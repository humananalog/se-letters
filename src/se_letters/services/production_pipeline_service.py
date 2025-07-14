#!/usr/bin/env python3
"""
Production Pipeline Service
Handles document processing with deduplication, validation, and ingestion

Version: 2.1.0
Last Updated: 2025-01-27
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import duckdb
from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.xai_service import XAIService
from se_letters.services.document_processor import DocumentProcessor


class ProcessingStatus(Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    DUPLICATE = "duplicate"


@dataclass
class DocumentCheckResult:
    """Result of document existence check"""
    exists: bool
    document_id: Optional[int] = None
    file_hash: Optional[str] = None
    processing_date: Optional[str] = None
    content_compliant: bool = False
    compliance_details: Optional[Dict[str, Any]] = None


@dataclass
class ContentValidationResult:
    """Result of content compliance validation"""
    is_compliant: bool
    confidence_score: float
    product_ranges: List[str]
    technical_specs: Dict[str, Any]
    validation_errors: List[str]
    extracted_metadata: Dict[str, Any]


@dataclass
class ProcessingResult:
    """Complete processing result"""
    success: bool
    status: ProcessingStatus
    document_id: Optional[int] = None
    processing_time_ms: float = 0.0
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    validation_result: Optional[ContentValidationResult] = None
    grok_metadata: Optional[Dict[str, Any]] = None
    ingestion_details: Optional[Dict[str, Any]] = None


class ProductionPipelineService:
    """Production pipeline service with comprehensive validation and logging"""
    
    def __init__(self, db_path: str = "data/letters.duckdb"):
        """Initialize production pipeline service"""
        self.db_path = db_path
        self.config = get_config()
        
        # Initialize services
        self.xai_service = XAIService(self.config)
        self.document_processor = DocumentProcessor(self.config)
        
        # Initialize database
        self._init_database()
        
        # Setup logging
        self._setup_logging()
        
        logger.info("🏭 Production Pipeline Service initialized")
        logger.info(f"📊 Database: {self.db_path}")
        logger.info(f"🔧 Configuration loaded: {self.config.api.model}")
    
    def _setup_logging(self) -> None:
        """Setup comprehensive logging for production pipeline"""
        # Configure structured logging
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.configure(
            handlers=[
                {
                    "sink": "logs/production_pipeline.log",
                    "format": log_format,
                    "level": "INFO",
                    "rotation": "10 MB",
                    "retention": "7 days"
                },
                {
                    "sink": "logs/production_errors.log",
                    "format": log_format,
                    "level": "ERROR",
                    "rotation": "10 MB",
                    "retention": "30 days"
                }
            ]
        )
        
        logger.info("📝 Production logging configured")
    
    def _init_database(self) -> None:
        """Initialize production database with comprehensive schema"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Create sequences
                conn.execute("CREATE SEQUENCE IF NOT EXISTS letters_id_seq START 1")
                conn.execute("CREATE SEQUENCE IF NOT EXISTS products_id_seq START 1")
                conn.execute("CREATE SEQUENCE IF NOT EXISTS debug_id_seq START 1")
                
                # Create letters table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS letters (
                        id INTEGER PRIMARY KEY DEFAULT nextval('letters_id_seq'),
                        document_name TEXT NOT NULL,
                        document_type TEXT,
                        document_title TEXT,
                        source_file_path TEXT NOT NULL,
                        file_size INTEGER,
                        processing_method TEXT DEFAULT 'production_pipeline',
                        processing_time_ms REAL,
                        extraction_confidence REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'processed',
                        raw_grok_json TEXT,
                        ocr_supplementary_json TEXT,
                        processing_steps_json TEXT
                    )
                """)
                
                # Add new columns if they don't exist
                try:
                    conn.execute("ALTER TABLE letters ADD COLUMN file_hash TEXT")
                except Exception:
                    pass  # Column already exists
                
                try:
                    conn.execute("ALTER TABLE letters ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                except Exception:
                    pass  # Column already exists
                
                try:
                    conn.execute("ALTER TABLE letters ADD COLUMN validation_details_json TEXT")
                except Exception:
                    pass  # Column already exists
                
                # Create products table
                conn.execute("""
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
                        confidence_score REAL DEFAULT 0.0,
                        validation_status TEXT DEFAULT 'validated',
                        FOREIGN KEY (letter_id) REFERENCES letters(id)
                    )
                """)
                
                # Create processing debug table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processing_debug (
                        id INTEGER PRIMARY KEY DEFAULT nextval('debug_id_seq'),
                        letter_id INTEGER NOT NULL,
                        processing_step TEXT NOT NULL,
                        step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        step_duration_ms REAL,
                        step_success BOOLEAN DEFAULT TRUE,
                        step_details TEXT,
                        error_message TEXT,
                        FOREIGN KEY (letter_id) REFERENCES letters(id)
                    )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_letters_source_path ON letters(source_file_path)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_letters_status ON letters(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_products_letter_id ON letter_products(letter_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_debug_letter_id ON processing_debug(letter_id)")
                
                # Create file_hash index if column exists
                try:
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_letters_file_hash ON letters(file_hash)")
                except Exception:
                    pass  # Column doesn't exist yet
                
                logger.info("🗄️ Production database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def process_document(self, file_path: Path) -> ProcessingResult:
        """Process document through complete production pipeline"""
        start_time = time.time()
        
        logger.info(f"🚀 Starting production pipeline for: {file_path}")
        logger.info(f"📁 File size: {file_path.stat().st_size} bytes")
        
        try:
            # Step 1: Check if document already exists
            logger.info("🔍 Step 1: Checking document existence")
            check_result = self._check_document_exists(file_path)
            
            if check_result.exists and check_result.content_compliant:
                logger.info(f"⏭️ Document already processed and compliant: {file_path}")
                return ProcessingResult(
                    success=True,
                    status=ProcessingStatus.SKIPPED,
                    document_id=check_result.document_id,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Step 2: Validate content compliance
            logger.info("✅ Step 2: Validating content compliance")
            validation_result = self._validate_content_compliance(file_path)
            
            if not validation_result.is_compliant:
                logger.warning(f"⚠️ Content validation failed: {validation_result.validation_errors}")
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message=f"Content validation failed: {validation_result.validation_errors}",
                    validation_result=validation_result,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Step 3: Process with Grok
            logger.info("🤖 Step 3: Processing with Grok")
            grok_result = self._process_with_grok(file_path, validation_result)
            
            if not grok_result:
                logger.error("❌ Grok processing failed")
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message="Grok processing failed",
                    validation_result=validation_result,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Step 4: Ingest into database
            logger.info("💾 Step 4: Ingesting into database")
            ingestion_result = self._ingest_into_database(
                file_path, validation_result, grok_result
            )
            
            if not ingestion_result["success"]:
                logger.error(f"❌ Database ingestion failed: {ingestion_result['error']}")
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message=f"Database ingestion failed: {ingestion_result['error']}",
                    validation_result=validation_result,
                    grok_metadata=grok_result,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Production pipeline completed successfully in {processing_time:.2f}ms")
            logger.info(f"📊 Document ID: {ingestion_result['document_id']}")
            logger.info(f"🎯 Confidence: {validation_result.confidence_score:.2f}")
            logger.info(f"📦 Products found: {len(validation_result.product_ranges)}")
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                document_id=ingestion_result["document_id"],
                processing_time_ms=processing_time,
                confidence_score=validation_result.confidence_score,
                validation_result=validation_result,
                grok_metadata=grok_result,
                ingestion_details=ingestion_result
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Production pipeline failed: {e}")
            logger.error(f"⏱️ Failed after {processing_time:.2f}ms")
            
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
                processing_time_ms=processing_time
            )
    
    def _check_document_exists(self, file_path: Path) -> DocumentCheckResult:
        """Check if document already exists in database"""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            with duckdb.connect(self.db_path) as conn:
                # Check by file path first
                result = conn.execute("""
                    SELECT id, created_at, status, validation_details_json
                    FROM letters 
                    WHERE source_file_path = ?
                """, [str(file_path)]).fetchone()
                
                # If not found by path, try by hash if column exists
                if not result:
                    try:
                        result = conn.execute("""
                            SELECT id, created_at, status, validation_details_json
                            FROM letters 
                            WHERE file_hash = ?
                        """, [file_hash]).fetchone()
                    except Exception:
                        pass  # file_hash column doesn't exist
                
                if result:
                    document_id, created_at, status, validation_json = result
                    
                    logger.info(f"📋 Document found in database: ID={document_id}")
                    logger.info(f"📅 Previous processing: {created_at}")
                    logger.info(f"📊 Status: {status}")
                    
                    # Check content compliance from previous processing
                    content_compliant = False
                    compliance_details = None
                    
                    if validation_json:
                        try:
                            validation_data = json.loads(validation_json)
                            content_compliant = validation_data.get("is_compliant", False)
                            compliance_details = validation_data
                        except json.JSONDecodeError:
                            logger.warning("⚠️ Invalid validation JSON in database")
                    
                    return DocumentCheckResult(
                        exists=True,
                        document_id=document_id,
                        file_hash=file_hash,
                        processing_date=str(created_at),
                        content_compliant=content_compliant,
                        compliance_details=compliance_details
                    )
                
                logger.info("🆕 Document not found in database - new processing required")
                return DocumentCheckResult(
                    exists=False,
                    file_hash=file_hash
                )
                
        except Exception as e:
            logger.error(f"❌ Error checking document existence: {e}")
            return DocumentCheckResult(exists=False)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            file_hash = hash_sha256.hexdigest()
            logger.debug(f"🔐 File hash calculated: {file_hash[:16]}...")
            return file_hash
            
        except Exception as e:
            logger.error(f"❌ Error calculating file hash: {e}")
            raise
    
    def _validate_content_compliance(self, file_path: Path) -> ContentValidationResult:
        """Validate content compliance for basic product information"""
        try:
            logger.info("🔍 Extracting document content for validation")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                raise Exception("Failed to process document")
            document_content = document.text
            
            if not document_content or len(document_content.strip()) < 100:
                logger.warning("⚠️ Document content too short or empty")
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    product_ranges=[],
                    technical_specs={},
                    validation_errors=["Document content too short or empty"],
                    extracted_metadata={}
                )
            
            logger.info(f"📄 Document content extracted: {len(document_content)} characters")
            
            # Use XAI service for basic validation
            validation_prompt = self._get_validation_prompt()
            
            logger.info("🤖 Requesting content validation from XAI")
            validation_response = self.xai_service.generate_completion(
                prompt=validation_prompt,
                document_content=document_content,
                document_name=file_path.name
            )
            
            if not validation_response:
                logger.error("❌ XAI validation response is empty")
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    product_ranges=[],
                    technical_specs={},
                    validation_errors=["XAI validation failed"],
                    extracted_metadata={}
                )
            
            # Parse validation response
            validation_data = self._parse_validation_response(validation_response)
            
            logger.info(f"✅ Content validation completed")
            logger.info(f"🎯 Compliance: {validation_data['is_compliant']}")
            logger.info(f"📊 Confidence: {validation_data['confidence_score']:.2f}")
            logger.info(f"📦 Product ranges: {validation_data['product_ranges']}")
            
            return ContentValidationResult(**validation_data)
            
        except Exception as e:
            logger.error(f"❌ Content validation error: {e}")
            return ContentValidationResult(
                is_compliant=False,
                confidence_score=0.0,
                product_ranges=[],
                technical_specs={},
                validation_errors=[str(e)],
                extracted_metadata={}
            )
    
    def _get_validation_prompt(self) -> str:
        """Get content validation prompt"""
        return """
        Analyze this document and determine if it contains valid Schneider Electric product information.
        
        Check for:
        1. Product ranges (e.g., TeSys, Modicon, Acti9, etc.)
        2. Product codes or identifiers
        3. Technical specifications
        4. Obsolescence or end-of-life information
        
        Return JSON with:
        {
            "is_compliant": boolean,
            "confidence_score": float (0.0-1.0),
            "product_ranges": [list of detected ranges],
            "technical_specs": {key: value pairs},
            "validation_errors": [list of issues],
            "extracted_metadata": {additional metadata}
        }
        
        Document: {document_name}
        Content: {document_content}
        """
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response from XAI"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                
                validation_data = json.loads(json_str)
                
                # Ensure required fields
                return {
                    "is_compliant": validation_data.get("is_compliant", False),
                    "confidence_score": float(validation_data.get("confidence_score", 0.0)),
                    "product_ranges": validation_data.get("product_ranges", []),
                    "technical_specs": validation_data.get("technical_specs", {}),
                    "validation_errors": validation_data.get("validation_errors", []),
                    "extracted_metadata": validation_data.get("extracted_metadata", {})
                }
            
            logger.warning("⚠️ No valid JSON found in validation response")
            return {
                "is_compliant": False,
                "confidence_score": 0.0,
                "product_ranges": [],
                "technical_specs": {},
                "validation_errors": ["Invalid response format"],
                "extracted_metadata": {}
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
            return {
                "is_compliant": False,
                "confidence_score": 0.0,
                "product_ranges": [],
                "technical_specs": {},
                "validation_errors": [f"JSON parsing error: {e}"],
                "extracted_metadata": {}
            }
    
    def _process_with_grok(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Process document with Grok to produce structured JSON"""
        try:
            logger.info("🤖 Processing document with Grok")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                raise Exception("Failed to process document")
            document_content = document.text
            
            # Get comprehensive extraction prompt
            grok_prompt = self._get_grok_prompt(validation_result)
            
            logger.info("🔄 Requesting comprehensive extraction from Grok")
            grok_response = self.xai_service.generate_completion(
                prompt=grok_prompt,
                document_content=document_content,
                document_name=file_path.name
            )
            
            if not grok_response:
                logger.error("❌ Grok response is empty")
                return None
            
            # Parse Grok response
            grok_data = self._parse_grok_response(grok_response)
            
            if not grok_data:
                logger.error("❌ Failed to parse Grok response")
                return None
            
            logger.info("✅ Grok processing completed successfully")
            logger.info(f"📊 Extracted {len(grok_data.get('products', []))} products")
            
            return grok_data
            
        except Exception as e:
            logger.error(f"❌ Grok processing error: {e}")
            return None
    
    def _get_grok_prompt(self, validation_result: ContentValidationResult) -> str:
        """Get comprehensive Grok extraction prompt"""
        return """
        Extract comprehensive product information from this Schneider Electric document.
        
        Based on validation results:
        - Product ranges detected: {product_ranges}
        - Technical specs: {technical_specs}
        
        Extract and return JSON with:
        {{
            "document_information": {{
                "document_type": "string",
                "document_title": "string",
                "document_date": "string",
                "language": "string"
            }},
            "products": [
                {{
                    "product_identifier": "string",
                    "range_label": "string",
                    "subrange_label": "string",
                    "product_line": "string",
                    "product_description": "string",
                    "obsolescence_status": "string",
                    "end_of_service_date": "string",
                    "replacement_suggestions": "string"
                }}
            ],
            "technical_specifications": {{
                "voltage_levels": ["list"],
                "current_ratings": ["list"],
                "power_ratings": ["list"],
                "frequencies": ["list"]
            }},
            "business_information": {{
                "customer_impact": "string",
                "migration_timeline": "string",
                "support_contacts": "string"
            }},
            "extraction_metadata": {{
                "confidence_score": float,
                "processing_method": "grok_production",
                "extraction_timestamp": "ISO timestamp"
            }}
        }}
        
        Document: {{document_name}}
        Content: {{document_content}}
        """.format(
            product_ranges=validation_result.product_ranges,
            technical_specs=validation_result.technical_specs
        )
    
    def _parse_grok_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse Grok response into structured data"""
        try:
            # Extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                
                grok_data = json.loads(json_str)
                
                # Validate required structure
                if not isinstance(grok_data.get("products"), list):
                    logger.warning("⚠️ No products list in Grok response")
                    grok_data["products"] = []
                
                return grok_data
            
            logger.warning("⚠️ No valid JSON found in Grok response")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Grok JSON parsing error: {e}")
            return None
    
    def _ingest_into_database(self, file_path: Path, validation_result: ContentValidationResult, grok_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest processed data into database with comprehensive validation"""
        try:
            logger.info("💾 Starting database ingestion")
            
            with duckdb.connect(self.db_path) as conn:
                # Insert letter record
                file_hash = self._calculate_file_hash(file_path)
                file_size = file_path.stat().st_size
                
                conn.execute("""
                    INSERT INTO letters (
                        document_name, document_type, document_title, source_file_path,
                        file_hash, file_size, processing_method, extraction_confidence,
                        status, raw_grok_json, validation_details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    file_path.name,
                    grok_data.get("document_information", {}).get("document_type"),
                    grok_data.get("document_information", {}).get("document_title"),
                    str(file_path),
                    file_hash,
                    file_size,
                    "production_pipeline",
                    validation_result.confidence_score,
                    "processed",
                    json.dumps(grok_data, indent=2),
                    json.dumps(asdict(validation_result), indent=2)
                ])
                
                # Get letter ID
                letter_id = conn.execute("SELECT currval('letters_id_seq')").fetchone()[0]
                
                logger.info(f"📝 Letter record created: ID={letter_id}")
                
                # Insert product records
                products_inserted = 0
                for product in grok_data.get("products", []):
                    conn.execute("""
                        INSERT INTO letter_products (
                            letter_id, product_identifier, range_label, subrange_label,
                            product_line, product_description, obsolescence_status,
                            end_of_service_date, replacement_suggestions, confidence_score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        letter_id,
                        product.get("product_identifier"),
                        product.get("range_label"),
                        product.get("subrange_label"),
                        product.get("product_line"),
                        product.get("product_description"),
                        product.get("obsolescence_status"),
                        product.get("end_of_service_date"),
                        product.get("replacement_suggestions"),
                        validation_result.confidence_score
                    ])
                    products_inserted += 1
                
                logger.info(f"📦 Products inserted: {products_inserted}")
                
                # Log processing step
                self._log_processing_step(
                    conn, letter_id, "database_ingestion", 
                    True, f"Successfully ingested {products_inserted} products"
                )
                
                logger.info("✅ Database ingestion completed successfully")
                
                return {
                    "success": True,
                    "document_id": letter_id,
                    "products_inserted": products_inserted,
                    "file_hash": file_hash
                }
                
        except Exception as e:
            logger.error(f"❌ Database ingestion error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_processing_step(self, conn, letter_id: int, step_name: str, success: bool, details: str, duration_ms: float = 0.0) -> None:
        """Log processing step to debug table"""
        try:
            conn.execute("""
                INSERT INTO processing_debug (
                    letter_id, processing_step, step_duration_ms, step_success, step_details
                ) VALUES (?, ?, ?, ?, ?)
            """, [letter_id, step_name, duration_ms, success, details])
            
        except Exception as e:
            logger.error(f"❌ Failed to log processing step: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics from database"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Get basic statistics
                stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(CASE WHEN status = 'processed' THEN 1 END) as processed_count,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                        AVG(extraction_confidence) as avg_confidence,
                        AVG(processing_time_ms) as avg_processing_time
                    FROM letters
                """).fetchone()
                
                # Get product statistics
                product_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_products,
                        COUNT(DISTINCT range_label) as unique_ranges
                    FROM letter_products
                """).fetchone()
                
                return {
                    "total_documents": stats[0] if stats else 0,
                    "processed_count": stats[1] if stats else 0,
                    "failed_count": stats[2] if stats else 0,
                    "avg_confidence": float(stats[3]) if stats and stats[3] else 0.0,
                    "avg_processing_time": float(stats[4]) if stats and stats[4] else 0.0,
                    "total_products": product_stats[0] if product_stats else 0,
                    "unique_ranges": product_stats[1] if product_stats else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {} 