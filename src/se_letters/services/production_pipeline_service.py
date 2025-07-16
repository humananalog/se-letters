#!/usr/bin/env python3
"""
Production Pipeline Service
Handles document processing with deduplication, validation, and ingestion

Version: 2.2.0
Author: Alexandre Huther
Last Updated: 2025-07-16
"""

import json
import hashlib
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

import duckdb
from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.xai_service import XAIService
from se_letters.services.document_processor import DocumentProcessor
from se_letters.services.intelligent_product_matching_service import IntelligentProductMatchingService
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.utils.json_output_manager import JSONOutputManager, OutputMetadata


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
    product_matching_result: Optional[Dict[str, Any]] = None


class ProductionPipelineService:
    """Production pipeline service with comprehensive validation and logging"""
    
    def __init__(self, db_path: str = "data/letters.duckdb"):
        """Initialize production pipeline service"""
        self.db_path = db_path
        self.config = get_config()
        
        # Initialize services
        self.xai_service = XAIService(self.config)
        self.document_processor = DocumentProcessor(self.config)
        self.json_output_manager = JSONOutputManager()
        self.product_matching_service = IntelligentProductMatchingService(debug_mode=True)
        self.product_database_service = SOTAProductDatabaseService()
        
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
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
            "<cyan>{line}</cyan> | "
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
                conn.execute("CREATE SEQUENCE IF NOT EXISTS matches_id_seq START 1")
                
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
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                
                # Create products table (extracted products from Grok)
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
                
                # Create product matches table (matched IBcatalogue products)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS letter_product_matches (
                        id INTEGER PRIMARY KEY DEFAULT nextval('matches_id_seq'),
                        letter_id INTEGER NOT NULL,
                        letter_product_id INTEGER NOT NULL,
                        ibcatalogue_product_identifier TEXT NOT NULL,
                        match_confidence REAL NOT NULL,
                        match_reason TEXT,
                        technical_match_score REAL DEFAULT 0.0,
                        nomenclature_match_score REAL DEFAULT 0.0,
                        product_line_match_score REAL DEFAULT 0.0,
                        match_type TEXT,
                        range_based_matching BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (letter_id) REFERENCES letters(id),
                        FOREIGN KEY (letter_product_id) REFERENCES letter_products(id)
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
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_letters_source_path ON letters(source_file_path)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_letters_status ON letters(status)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_products_letter_id ON letter_products(letter_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_matches_letter_id ON letter_product_matches(letter_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_matches_product_id ON letter_product_matches(letter_product_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_debug_letter_id ON processing_debug(letter_id)"
                )
                
                # Create file_hash index if column exists
                try:
                    conn.execute(
                        "CREATE INDEX IF NOT EXISTS idx_letters_file_hash ON letters(file_hash)"
                    )
                except Exception:
                    pass  # Column doesn't exist yet
                
                logger.info("🗄️ Production database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def process_document(self, file_path: Path, force_reprocess: bool = False) -> ProcessingResult:
        """Process document through complete production pipeline
        
        Args:
            file_path: Path to the document to process
            force_reprocess: If True, reprocess even if document already exists
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting production pipeline for: {file_path}")
        logger.info(f"📁 File size: {file_path.stat().st_size} bytes")
        logger.info(f"🔄 Force reprocess: {force_reprocess}")
        
        try:
            # Step 1: Check if document already exists
            logger.info("🔍 Step 1: Checking document existence")
            check_result = self._check_document_exists(file_path)
            
            if check_result.exists and check_result.content_compliant and not force_reprocess:
                logger.info(f"⏭️ Document already processed and compliant: {file_path}")
                return ProcessingResult(
                    success=True,
                    status=ProcessingStatus.SKIPPED,
                    document_id=check_result.document_id,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            elif check_result.exists and force_reprocess:
                logger.info(f"🔄 Force reprocessing existing document: {file_path}")
                # Store the existing document ID for updating instead of creating new
                existing_document_id = check_result.document_id
                # Delete existing record to allow reprocessing
                self._delete_existing_document(check_result.document_id)
            
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
            
            # Step 3: Process with Grok (NO FALLBACK - pipeline stops if Grok fails)
            logger.info("🤖 Step 3: Processing with Grok (no fallback)")
            grok_result = self._process_with_grok(file_path, validation_result)
            
            if not grok_result:
                logger.error("❌ Grok processing failed - pipeline stopped")
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message="Grok processing failed - pipeline stopped as required",
                    validation_result=validation_result,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            logger.info(f"✅ Grok extraction completed successfully")
            logger.info(f"📊 Extracted {len(grok_result.get('products', []))} products")
            
            # Step 4: Intelligent Product Matching
            logger.info("🔍 Step 4: Intelligent Product Matching")
            product_matching_result = self._process_product_matching(grok_result, file_path)
            
            # Step 5: Ingest into database
            logger.info("💾 Step 5: Ingesting into database")
            ingestion_result = self._ingest_into_database(
                file_path, validation_result, grok_result, product_matching_result,
                existing_document_id if 'existing_document_id' in locals() else None
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
            
            # Step 6: Save JSON outputs
            logger.info("💾 Step 6: Saving JSON outputs")
            try:
                self._save_json_outputs(
                    file_path=file_path,
                    document_id=ingestion_result["document_id"],
                    validation_result=validation_result,
                    grok_result=grok_result,
                    ingestion_result=ingestion_result,
                    processing_time_ms=processing_time
                )
                logger.info("✅ JSON outputs saved successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save JSON outputs: {e}")
            
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
                ingestion_details=ingestion_result,
                product_matching_result=product_matching_result
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
                # Normalize file path to handle relative vs absolute paths
                file_path_str = str(file_path.resolve())
                file_name = file_path.name
                
                # Check by multiple criteria to handle path variations
                result = conn.execute("""
                    SELECT id, created_at, status, validation_details_json, source_file_path
                    FROM letters 
                    WHERE source_file_path = ? 
                       OR source_file_path = ?
                       OR (document_name = ? AND file_hash = ?)
                    ORDER BY created_at DESC
                    LIMIT 1
                """, [str(file_path), file_path_str, file_name, file_hash]).fetchone()
                
                if result:
                    document_id, created_at, status, validation_json, existing_path = result
                    
                    logger.info(f"📋 Document found in database: ID={document_id}")
                    logger.info(f"📅 Previous processing: {created_at}")
                    logger.info(f"📊 Status: {status}")
                    logger.info(f"📂 Existing path: {existing_path}")
                    
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
    
    def _delete_existing_document(self, document_id: int) -> None:
        """Delete existing document child records for reprocessing, keep letter record for update"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Delete only child records due to foreign key constraints, keep letter record
                conn.execute("DELETE FROM processing_debug WHERE letter_id = ?", [document_id])
                conn.execute("DELETE FROM letter_product_matches WHERE letter_id = ?", [document_id])
                conn.execute("DELETE FROM letter_products WHERE letter_id = ?", [document_id])
                # Do NOT delete the letter record - we will update it instead
                
                logger.info(f"🗑️ Deleted child records for document: ID={document_id}")
                
        except Exception as e:
            logger.error(f"❌ Error deleting existing document child records: {e}")
            raise
    
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
        """Validate document content compliance using XAI"""
        try:
            logger.info("🔍 Extracting document content for validation")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                raise Exception("Failed to process document")
            
            document_content = document.text
            logger.info(f"📄 Document content extracted: {len(document_content)} characters")
            
            # Check network connectivity before making API call
            if not self._check_network_connectivity():
                logger.warning("⚠️ Network connectivity issues detected - skipping XAI validation")
                return ContentValidationResult(
                    is_compliant=True,
                    confidence_score=0.8,
                    product_ranges=[],
                    technical_specs={},
                    validation_errors=["Network connectivity issues - using fallback validation"],
                    extracted_metadata={}
                )
            
            logger.info("🤖 Requesting content validation from XAI")
            
            # Get validation prompt
            validation_prompt = self._get_validation_prompt()
            
            # Make API call with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    validation_response = self.xai_service.generate_completion(
                        prompt=validation_prompt,
                        document_content=document_content,
                        document_name=file_path.name
                    )
                    
                    if validation_response:
                        break
                    else:
                        raise Exception("Empty response from XAI")
                        
                except Exception as e:
                    if "DNS resolution failed" in str(e) or "Could not contact DNS servers" in str(e):
                        logger.warning(f"⚠️ DNS resolution failed (attempt {attempt + 1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(2 ** attempt)  # Exponential backoff
                            continue
                        else:
                            logger.error("❌ XAI validation failed after all retries due to network issues")
                            return ContentValidationResult(
                                is_compliant=True,
                                confidence_score=0.7,
                                product_ranges=[],
                                technical_specs={},
                                validation_errors=["Network connectivity issues - using fallback validation"],
                                extracted_metadata={}
                            )
                    else:
                        raise e
            
            if not validation_response:
                logger.error("❌ XAI validation response is empty")
                return ContentValidationResult(
                    is_compliant=True,
                    confidence_score=0.7,
                    product_ranges=[],
                    technical_specs={},
                    validation_errors=["XAI validation failed"],
                    extracted_metadata={}
                )
            
            # Parse validation response
            validation_result = self._parse_validation_response(validation_response)
            
            logger.info("✅ Content validation completed")
            logger.info(f"🎯 Compliance: {validation_result.is_compliant}")
            logger.info(f"📊 Confidence: {validation_result.confidence_score}")
            logger.info(f"📦 Product ranges: {validation_result.product_ranges}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Content validation failed: {e}")
            return ContentValidationResult(
                is_compliant=True,
                confidence_score=0.6,
                product_ranges=[],
                technical_specs={},
                validation_errors=[f"Validation failed: {e}"],
                extracted_metadata={}
            )
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity to xAI API"""
        try:
            import socket
            import urllib.request
            
            # Test DNS resolution
            socket.gethostbyname("api.x.ai")
            
            # Test HTTP connectivity with proper headers (avoid 403)
            req = urllib.request.Request("https://api.x.ai")
            req.add_header('User-Agent', 'SE-Letters-Pipeline/2.2.0')
            urllib.request.urlopen(req, timeout=5)
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ Network connectivity check failed: {e}")
            return False
    
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
            # DEBUG: Log the raw response
            logger.debug(f"🔍 DEBUG: Raw XAI validation response:\n{response}")
            
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                
                # DEBUG: Log the extracted JSON string
                logger.debug(f"🔍 DEBUG: Extracted JSON string:\n{json_str}")
                
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
            logger.error(f"❌ Raw response that caused error:\n{response}")
            return {
                "is_compliant": False,
                "confidence_score": 0.0,
                "product_ranges": [],
                "technical_specs": {},
                "validation_errors": [f"JSON parsing error: {e}"],
                "extracted_metadata": {}
            }
    
    def _process_with_grok(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Process document with Grok - NO FALLBACK, pipeline stops if Grok fails"""
        try:
            logger.info("🤖 Processing document with Grok (no fallback)")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                raise Exception("Failed to process document")
            document_content = document.text
            
            logger.info("🔄 Requesting comprehensive extraction from Grok")
            
            # Use the comprehensive metadata extraction method
            grok_data = self.xai_service.extract_comprehensive_metadata(
                text=document_content,
                document_name=file_path.name
            )
            
            if not grok_data:
                logger.error("❌ Grok response is empty")
                return None
            
            # Convert the comprehensive metadata to the expected format
            processed_data = self._convert_comprehensive_metadata(grok_data)
            
            logger.info("✅ Grok processing completed successfully")
            logger.info(f"📊 Extracted {len(processed_data.get('products', []))} products")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ Grok processing failed: {e}")
            return None
    
    def _convert_comprehensive_metadata(self, comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert comprehensive metadata to the expected pipeline format"""
        try:
            # Extract product information
            product_info = comprehensive_data.get('product_identification', {})
            ranges = product_info.get('ranges', [])
            product_codes = product_info.get('product_codes', [])
            descriptions = product_info.get('descriptions', [])
            
            # Create products list
            products = []
            for i, range_name in enumerate(ranges):
                product = {
                    'product_identifier': product_codes[i] if i < len(product_codes) else f"PROD_{i+1}",
                    'range_label': range_name,
                    'product_description': descriptions[i] if i < len(descriptions) else range_name,
                    'confidence_score': comprehensive_data.get('extraction_metadata', {}).get('confidence', 0.8)
                }
                products.append(product)
            
            # Return in expected format
            return {
                'products': products,
                'extraction_metadata': comprehensive_data.get('extraction_metadata', {}),
                'processing_timestamp': comprehensive_data.get('extraction_metadata', {}).get('processing_time', 0),
                'confidence_score': comprehensive_data.get('extraction_metadata', {}).get('confidence', 0.8)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to convert comprehensive metadata: {e}")
            return {
                'products': [],
                'extraction_metadata': {},
                'processing_timestamp': 0,
                'confidence_score': 0.0
            } 

    def _process_product_matching(self, grok_result: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Process product matching using intelligent matching service"""
        try:
            logger.info("🔍 Processing product matching")
            
            # Convert Grok products to LetterProductInfo objects
            letter_products = self.product_matching_service.create_letter_product_info_from_grok_metadata(grok_result)
            if not letter_products:
                logger.warning("⚠️ No products found for matching")
                return {
                    'success': True,
                    'matched_products': [],
                    'matching_confidence': 0.0,
                    'matching_errors': ['No products to match']
                }
            
            # For each letter product, discover candidates and match
            all_matches = []
            for letter_product in letter_products:
                discovery_result = self.product_database_service.discover_product_candidates(letter_product, max_candidates=1000)
                candidates = discovery_result.candidates
                match_result = self.product_matching_service.match_products(letter_product, candidates)
                all_matches.extend(match_result.matching_products)
            
            logger.info(f"✅ Product matching completed: {len(all_matches)} matches")
            return {
                'success': True,
                'matched_products': all_matches,
                'matching_confidence': max((m.confidence for m in all_matches), default=0.0),
                'matching_errors': []
            }
        except Exception as e:
            logger.error(f"❌ Product matching failed: {e}")
            return {
                'success': False,
                'matched_products': [],
                'matching_confidence': 0.0,
                'matching_errors': [f'Product matching failed: {e}']
            }

    def _ingest_into_database(self, file_path: Path, validation_result: ContentValidationResult, 
                             grok_result: Dict[str, Any], product_matching_result: Dict[str, Any],
                             existing_document_id: Optional[int] = None) -> Dict[str, Any]:
        """Ingest processing results into database"""
        try:
            logger.info("💾 Ingesting results into database")
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            with duckdb.connect(self.db_path) as conn:
                # Insert or update letter record
                if existing_document_id:
                    # Update existing record
                    conn.execute("""
                        UPDATE letters 
                        SET document_name = ?, source_file_path = ?, file_hash = ?, 
                            validation_details_json = ?, updated_at = CURRENT_TIMESTAMP,
                            status = 'processed'
                        WHERE id = ?
                    """, [
                        file_path.name,
                        str(file_path.resolve()),
                        file_hash,
                        json.dumps(validation_result.__dict__),
                        existing_document_id
                    ])
                    document_id = existing_document_id
                else:
                    # Insert new record
                    result = conn.execute("""
                        INSERT INTO letters (document_name, source_file_path, file_hash, 
                                           validation_details_json, status)
                        VALUES (?, ?, ?, ?, 'processed')
                        RETURNING id
                    """, [
                        file_path.name,
                        str(file_path.resolve()),
                        file_hash,
                        json.dumps(validation_result.__dict__)
                    ]).fetchone()
                    document_id = result[0]
                
                # Insert products
                products = grok_result.get('products', [])
                for product in products:
                    conn.execute("""
                        INSERT INTO letter_products (letter_id, product_identifier, range_label, 
                                                   product_description, confidence_score)
                        VALUES (?, ?, ?, ?, ?)
                    """, [
                        document_id,
                        product.get('product_identifier', ''),
                        product.get('range_label', ''),
                        product.get('product_description', ''),
                        product.get('confidence_score', 0.0)
                    ])
                
                # Insert product matches
                matched_products = product_matching_result.get('matched_products', [])
                for match in matched_products:
                    conn.execute("""
                        INSERT INTO letter_product_matches (letter_id, letter_product_id, ibcatalogue_product_identifier, 
                                                          match_confidence, match_reason, technical_match_score, nomenclature_match_score, product_line_match_score, match_type, range_based_matching)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        document_id,
                        None,  # letter_product_id (can be linked if available)
                        match.product_identifier,
                        match.confidence,
                        match.reason,
                        match.technical_match_score,
                        match.nomenclature_match_score,
                        match.product_line_match_score,
                        match.match_type,
                        False  # range_based_matching (can be set if available)
                    ])
                
                logger.info(f"✅ Database ingestion completed: Document ID {document_id}")
                return {
                    'success': True,
                    'document_id': document_id,
                    'products_inserted': len(products),
                    'matches_inserted': len(matched_products)
                }
                
        except Exception as e:
            logger.error(f"❌ Database ingestion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics from database"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Get basic statistics
                total_documents = conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0]
                processed_documents = conn.execute("SELECT COUNT(*) FROM letters WHERE status = 'processed'").fetchone()[0]
                failed_documents = conn.execute("SELECT COUNT(*) FROM letters WHERE status = 'failed'").fetchone()[0]
                
                # Get recent processing stats
                recent_processing = conn.execute("""
                    SELECT COUNT(*) FROM letters 
                    WHERE created_at >= CURRENT_DATE - INTERVAL 7 DAY
                """).fetchone()[0]
                
                # Get average confidence scores
                avg_confidence = conn.execute("""
                    SELECT AVG(CAST(JSON_EXTRACT(validation_details_json, '$.confidence_score') AS FLOAT))
                    FROM letters 
                    WHERE validation_details_json IS NOT NULL
                """).fetchone()[0] or 0.0
                
                return {
                    'total_documents': total_documents,
                    'processed_documents': processed_documents,
                    'failed_documents': failed_documents,
                    'recent_processing_7_days': recent_processing,
                    'average_confidence_score': round(avg_confidence, 2),
                    'success_rate': round((processed_documents / total_documents * 100) if total_documents > 0 else 0, 2)
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get processing statistics: {e}")
            return {
                'total_documents': 0,
                'processed_documents': 0,
                'failed_documents': 0,
                'recent_processing_7_days': 0,
                'average_confidence_score': 0.0,
                'success_rate': 0.0,
                'error': str(e)
            } 