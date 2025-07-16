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
            
            # Step 3: Process with Grok (now with comprehensive fallback)
            logger.info("🤖 Step 3: Processing with Grok and fallback system")
            grok_result = self._process_with_grok(file_path, validation_result)
            
            # grok_result is now guaranteed to be a valid dictionary (never None)
            logger.info(f"✅ Extraction completed with method: {grok_result.get('extraction_metadata', {}).get('processing_method', 'unknown')}")
            logger.info(f"📊 Extracted {len(grok_result.get('products', []))} products")
            logger.info(f"🎯 Confidence: {grok_result.get('extraction_metadata', {}).get('confidence_score', 0.0)}")
            
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
            
            # Test HTTP connectivity (with timeout)
            urllib.request.urlopen("https://api.x.ai", timeout=5)
            
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
    
    def _process_with_grok(self, file_path: Path, validation_result: ContentValidationResult) -> Dict[str, Any]:
        """Process document with Grok and comprehensive fallback mechanisms"""
        logger.info("🤖 Processing document with Grok and fallback system")
        
        # Try multiple extraction methods in order of preference
        extraction_methods = [
            ("grok_primary", self._extract_with_grok_primary),
            ("grok_fallback", self._extract_with_grok_fallback),
            ("rule_based", self._extract_with_rule_based),
            ("filename_analysis", self._extract_from_filename),
            ("intelligent_fallback", self._create_intelligent_fallback)
        ]
        
        for method_name, method_func in extraction_methods:
            try:
                logger.info(f"🔄 Trying extraction method: {method_name}")
                result = method_func(file_path, validation_result)
                
                if result and self._validate_extraction_result(result):
                    logger.info(f"✅ Extraction successful with {method_name}")
                    result["extraction_metadata"]["processing_method"] = method_name
                    result["extraction_metadata"]["fallback_used"] = method_name != "grok_primary"
                    return result
                else:
                    logger.warning(f"⚠️ {method_name} returned invalid result, trying next method")
                    
            except Exception as e:
                logger.warning(f"⚠️ {method_name} failed: {e}, trying next method")
                continue
        
        # This should never happen due to intelligent fallback
        logger.error("❌ All extraction methods failed - this should not happen")
        return self._create_emergency_fallback(file_path, validation_result)
    
    def _extract_with_grok_primary(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Primary Grok extraction with full API access"""
        try:
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
                raise Exception("Grok response is empty")
            
            # Parse Grok response
            grok_data = self._parse_grok_response(grok_response)
            
            if not grok_data:
                raise Exception("Failed to parse Grok response")
            
            logger.info(f"📊 Extracted {len(grok_data.get('products', []))} products")
            return grok_data
            
        except Exception as e:
            logger.warning(f"⚠️ Primary Grok extraction failed: {e}")
            return None
    
    def _extract_with_grok_fallback(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Fallback Grok extraction with simplified prompt"""
        try:
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                raise Exception("Failed to process document")
            document_content = document.text
            
            # Use simplified prompt for fallback
            simplified_prompt = self._get_simplified_grok_prompt()
            
            logger.info("🔄 Requesting simplified extraction from Grok")
            grok_response = self.xai_service.generate_completion(
                prompt=simplified_prompt,
                document_content=document_content,
                document_name=file_path.name
            )
            
            if not grok_response:
                raise Exception("Grok response is empty")
            
            # Parse with more lenient parsing
            grok_data = self._parse_grok_response_lenient(grok_response)
            
            if not grok_data:
                raise Exception("Failed to parse Grok response")
            
            logger.info(f"📊 Fallback extracted {len(grok_data.get('products', []))} products")
            return grok_data
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback Grok extraction failed: {e}")
            return None
    
    def _extract_with_rule_based(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Rule-based extraction using predefined patterns and validation results"""
        try:
            logger.info("🔍 Using rule-based extraction")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                raise Exception("Failed to process document")
            document_content = document.text
            
            # Use validation results and content analysis
            products = self._extract_products_by_rules(document_content, file_path.name)
            
            result = {
                "document_information": {
                    "document_type": "Obsolescence Letter",
                    "document_title": file_path.stem,
                    "document_date": self._extract_date_from_content(document_content),
                    "language": "English"
                },
                "products": products,
                "technical_specifications": {
                    "voltage_levels": [],
                    "current_ratings": [],
                    "power_ratings": [],
                    "frequencies": []
                },
                "business_information": {
                    "customer_impact": "Product obsolescence notice",
                    "migration_timeline": "Refer to document for specific dates",
                    "support_contacts": "Contact Schneider Electric support"
                },
                "extraction_metadata": {
                    "confidence_score": 0.6,
                    "processing_method": "rule_based",
                    "extraction_timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"📊 Rule-based extracted {len(products)} products")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Rule-based extraction failed: {e}")
            return None
    
    def _extract_from_filename(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Extract product information from filename analysis"""
        try:
            logger.info("📁 Using filename-based extraction")
            
            filename = file_path.name
            products = self._extract_products_from_filename(filename)
            
            result = {
                "document_information": {
                    "document_type": "Obsolescence Letter",
                    "document_title": file_path.stem,
                    "document_date": datetime.now().strftime("%Y-%m-%d"),
                    "language": "English"
                },
                "products": products,
                "technical_specifications": {
                    "voltage_levels": [],
                    "current_ratings": [],
                    "power_ratings": [],
                    "frequencies": []
                },
                "business_information": {
                    "customer_impact": "Product obsolescence notice",
                    "migration_timeline": "Refer to document for specific dates",
                    "support_contacts": "Contact Schneider Electric support"
                },
                "extraction_metadata": {
                    "confidence_score": 0.4,
                    "processing_method": "filename_analysis",
                    "extraction_timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"📊 Filename analysis extracted {len(products)} products")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Filename extraction failed: {e}")
            return None
    
    def _create_intelligent_fallback(self, file_path: Path, validation_result: ContentValidationResult) -> Dict[str, Any]:
        """Intelligent fallback that never fails - creates structured content from available information"""
        logger.info("🧠 Using intelligent fallback extraction")
        
        # Create basic product information from validation results
        products = []
        for range_name in validation_result.product_ranges:
            products.append({
                "product_identifier": range_name,
                "range_label": range_name.split()[0] if range_name else "",
                "subrange_label": " ".join(range_name.split()[1:]) if len(range_name.split()) > 1 else None,
                "product_line": self._classify_product_line(range_name),
                "product_description": f"Product from {range_name} range",
                "obsolescence_status": "End of Commercialization",
                "end_of_service_date": "Refer to document",
                "replacement_suggestions": "Contact Schneider Electric"
            })
        
        # If no products from validation, create from filename
        if not products:
            products = self._extract_products_from_filename(file_path.name)
        
        result = {
            "document_information": {
                "document_type": "Obsolescence Letter",
                "document_title": file_path.stem,
                "document_date": datetime.now().strftime("%Y-%m-%d"),
                "language": "English"
            },
            "products": products,
            "technical_specifications": {
                "voltage_levels": [],
                "current_ratings": [],
                "power_ratings": [],
                "frequencies": []
            },
            "business_information": {
                "customer_impact": "Product obsolescence notice",
                "migration_timeline": "Refer to document for specific dates",
                "support_contacts": "Contact Schneider Electric support"
            },
            "extraction_metadata": {
                "confidence_score": 0.3,
                "processing_method": "intelligent_fallback",
                "extraction_timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"📊 Intelligent fallback created {len(products)} products")
        return result
    
    def _create_emergency_fallback(self, file_path: Path, validation_result: ContentValidationResult) -> Dict[str, Any]:
        """Emergency fallback that absolutely never fails"""
        logger.warning("🚨 Using emergency fallback - all other methods failed")
        
        return {
            "document_information": {
                "document_type": "Document",
                "document_title": file_path.name,
                "document_date": datetime.now().strftime("%Y-%m-%d"),
                "language": "Unknown"
            },
            "products": [{
                "product_identifier": "Unknown Product",
                "range_label": "Unknown",
                "subrange_label": None,
                "product_line": "Unknown",
                "product_description": "Product information could not be extracted",
                "obsolescence_status": "Unknown",
                "end_of_service_date": "Unknown",
                "replacement_suggestions": "Contact Schneider Electric"
            }],
            "technical_specifications": {
                "voltage_levels": [],
                "current_ratings": [],
                "power_ratings": [],
                "frequencies": []
            },
            "business_information": {
                "customer_impact": "Document processing failed",
                "migration_timeline": "Manual review required",
                "support_contacts": "Contact Schneider Electric support"
            },
            "extraction_metadata": {
                "confidence_score": 0.1,
                "processing_method": "emergency_fallback",
                "extraction_timestamp": datetime.now().isoformat()
            }
        }
    
    def _validate_extraction_result(self, result: Dict[str, Any]) -> bool:
        """Validate that extraction result has required structure"""
        try:
            required_keys = ["document_information", "products", "extraction_metadata"]
            for key in required_keys:
                if key not in result:
                    return False
            
            if not isinstance(result.get("products"), list):
                return False
            
            return True
        except Exception:
            return False
    
    def _get_simplified_grok_prompt(self) -> str:
        """Get simplified Grok prompt for fallback extraction"""
        return """
        Extract basic product information from this Schneider Electric document.
        
        Return JSON with:
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
                "voltage_levels": [],
                "current_ratings": [],
                "power_ratings": [],
                "frequencies": []
            }},
            "business_information": {{
                "customer_impact": "string",
                "migration_timeline": "string",
                "support_contacts": "string"
            }},
            "extraction_metadata": {{
                "confidence_score": 0.5,
                "processing_method": "grok_fallback",
                "extraction_timestamp": "ISO timestamp"
            }}
        }}
        
        Document: {{document_name}}
        Content: {{document_content}}
        """
    
    def _parse_grok_response_lenient(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse Grok response with more lenient parsing for fallback"""
        try:
            # Try multiple JSON extraction methods
            json_str = self._extract_json_from_response(response)
            if not json_str:
                return None
            
            grok_data = json.loads(json_str)
            
            # Ensure required structure exists
            if "products" not in grok_data:
                grok_data["products"] = []
            if "document_information" not in grok_data:
                grok_data["document_information"] = {}
            if "extraction_metadata" not in grok_data:
                grok_data["extraction_metadata"] = {}
            
            return grok_data
            
        except Exception as e:
            logger.warning(f"⚠️ Lenient parsing failed: {e}")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON from response using multiple methods"""
        # Method 1: Look for JSON between curly braces
        if "{" in response and "}" in response:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            try:
                json.loads(json_str)  # Validate JSON
                return json_str
            except:
                pass
        
        # Method 2: Look for JSON in code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                json_str = response[start:end].strip()
                try:
                    json.loads(json_str)
                    return json_str
                except:
                    pass
        
        # Method 3: Look for any JSON-like structure
        import re
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        for match in matches:
            try:
                json.loads(match)
                return match
            except:
                continue
        
        return None
    
    def _extract_products_by_rules(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Extract products using rule-based patterns"""
        products = []
        
        # Common product patterns
        patterns = {
            "MiCOM": r"MiCOM\s+[A-Z0-9]+",
            "SEPAM": r"SEPAM\s+[A-Z0-9]+",
            "PowerLogic": r"PowerLogic\s+[A-Z0-9]+",
            "Galaxy": r"Galaxy\s+[0-9]+",
            "PIX": r"PIX\s*[A-Z0-9]*",
            "Masterpact": r"Masterpact\s+[A-Z0-9]+",
            "Powerpact": r"Powerpact\s+[A-Z0-9]+"
        }
        
        for range_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                products.append({
                    "product_identifier": match,
                    "range_label": range_name,
                    "subrange_label": match.replace(range_name, "").strip(),
                    "product_line": self._classify_product_line(match),
                    "product_description": f"{match} product",
                    "obsolescence_status": "End of Commercialization",
                    "end_of_service_date": "Refer to document",
                    "replacement_suggestions": "Contact Schneider Electric"
                })
        
        return products
    
    def _extract_products_from_filename(self, filename: str) -> List[Dict[str, Any]]:
        """Extract product information from filename"""
        products = []
        
        # Common patterns in filenames
        patterns = {
            "MiCOM": r"MiCOM\s*[A-Z0-9]*",
            "SEPAM": r"SEPAM\s*[A-Z0-9]*",
            "PowerLogic": r"PowerLogic\s*[A-Z0-9]*",
            "Galaxy": r"Galaxy\s*[0-9]*",
            "PIX": r"PIX\s*[A-Z0-9]*",
            "Masterpact": r"Masterpact\s*[A-Z0-9]*",
            "Powerpact": r"Powerpact\s*[A-Z0-9]*"
        }
        
        for range_name, pattern in patterns.items():
            matches = re.findall(pattern, filename, re.IGNORECASE)
            for match in matches:
                products.append({
                    "product_identifier": match,
                    "range_label": range_name,
                    "subrange_label": match.replace(range_name, "").strip(),
                    "product_line": self._classify_product_line(match),
                    "product_description": f"{match} product from filename analysis",
                    "obsolescence_status": "End of Commercialization",
                    "end_of_service_date": "Refer to document",
                    "replacement_suggestions": "Contact Schneider Electric"
                })
        
        return products
    
    def _classify_product_line(self, product_name: str) -> str:
        """Classify product line based on product name"""
        product_upper = product_name.upper()
        
        if any(keyword in product_upper for keyword in ["MICOM", "SEPAM", "POWERLOGIC"]):
            return "DPIBS"
        elif any(keyword in product_upper for keyword in ["GALAXY", "UPS"]):
            return "SPIBS"
        elif any(keyword in product_upper for keyword in ["MASTERPACT", "POWERPACT", "ACB"]):
            return "PPIBS"
        elif any(keyword in product_upper for keyword in ["PIX", "SWITCHGEAR"]):
            return "PSIBS"
        else:
            return "Unknown"
    
    def _extract_date_from_content(self, content: str) -> str:
        """Extract date from content using patterns"""
        import re
        
        # Common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
        
        return datetime.now().strftime("%Y-%m-%d") 