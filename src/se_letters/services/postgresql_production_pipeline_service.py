#!/usr/bin/env python3
"""
PostgreSQL Production Pipeline Service
Handles document processing with deduplication, validation, and ingestion using PostgreSQL

Version: 2.2.0
Author: Alexandre Huther
Last Updated: 2025-07-17
"""

import json
import hashlib
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import psycopg2
import psycopg2.extras
from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.xai_service import XAIService
from se_letters.services.document_processor import DocumentProcessor
from se_letters.services.intelligent_product_matching_service import IntelligentProductMatchingService
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService
from se_letters.services.enhanced_product_mapping_service_v3 import EnhancedProductMappingServiceV3
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
    content_compliant: bool = False
    file_hash: Optional[str] = None
    processing_time_ms: Optional[float] = None
    confidence_score: Optional[float] = None


@dataclass
class ContentValidationResult:
    """Result of content validation"""
    is_compliant: bool
    confidence_score: float
    validation_errors: List[str]
    product_ranges: List[str]
    document_type: str
    document_title: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of document processing"""
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


class PostgreSQLProductionPipelineService:
    """PostgreSQL production pipeline service with comprehensive validation and logging"""
    
    def __init__(self, connection_string: str = None):
        """Initialize production pipeline service"""
        if connection_string is None:
            connection_string = os.getenv('DATABASE_URL', "postgresql://ahuther:bender1980@localhost:5432/se_letters_dev")
        self.connection_string = connection_string
        self.config = get_config()
        
        # Initialize services
        self.xai_service = XAIService(self.config)
        self.document_processor = DocumentProcessor(self.config)
        self.json_output_manager = JSONOutputManager()
        self.product_matching_service = IntelligentProductMatchingService(debug_mode=True)
        self.product_database_service = SOTAProductDatabaseService()
        self.enhanced_mapping_service = EnhancedProductMappingServiceV3(self.connection_string)
        
        # Initialize database
        self._init_database()
        
        # Setup logging
        self._setup_logging()
        
        logger.info("🏭 PostgreSQL Production Pipeline Service initialized")
        logger.info(f"📊 Database: {self.connection_string}")
        logger.info(f"🔧 Configuration loaded: {self.config.api.model}")
    
    def _setup_logging(self) -> None:
        """Setup comprehensive logging"""
        import sys
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.configure(
            handlers=[
                {
                    "sink": sys.stdout,
                    "format": log_format,
                    "level": "INFO"
                },
                {
                    "sink": "logs/postgresql_pipeline.log",
                    "format": log_format,
                    "level": "DEBUG",
                    "rotation": "10 MB",
                    "retention": "7 days"
                }
            ]
        )
    
    def _init_database(self) -> None:
        """Initialize production database with comprehensive schema"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Create letters table
                    cur.execute("""
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
                    
                    # Create products table (extracted products from Grok)
                    cur.execute("""
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
                    
                    # Create product matches table (matched IBcatalogue products)
                    cur.execute("""
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
                    
                    # Create processing debug table
                    cur.execute("""
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
                    
                    # Create indexes for performance
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_source_path ON letters(source_file_path)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_status ON letters(status)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_file_hash ON letters(file_hash)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_created_at ON letters(created_at)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_document_name ON letters(document_name)")
                    
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_letter_id ON letter_products(letter_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_range_label ON letter_products(range_label)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_products_product_identifier ON letter_products(product_identifier)")
                    
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_letter_id ON letter_product_matches(letter_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_product_id ON letter_product_matches(letter_product_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_ibcatalogue_id ON letter_product_matches(ibcatalogue_product_identifier)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_confidence ON letter_product_matches(match_confidence)")
                    
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_debug_letter_id ON processing_debug(letter_id)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_debug_timestamp ON processing_debug(step_timestamp)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_debug_step ON processing_debug(processing_step)")
                    
                    # Create JSONB indexes for better performance
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_raw_grok_gin ON letters USING GIN (raw_grok_json)")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_letters_validation_details_gin ON letters USING GIN (validation_details_json)")
                    
                    conn.commit()
                    logger.info("🗄️ PostgreSQL production database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize PostgreSQL database: {e}")
            raise
    
    def process_document(self, file_path: Path, force_reprocess: bool = False) -> ProcessingResult:
        """Process document through complete production pipeline
        
        Args:
            file_path: Path to the document to process
            force_reprocess: If True, reprocess even if document already exists
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting PostgreSQL production pipeline for: {file_path}")
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
            
            # Add debug logging for grok_result and products
            logger.info(f"[DEBUG] grok_result keys: {list(grok_result.keys()) if grok_result else 'None'}")
            if grok_result:
                logger.info(f"[DEBUG] Products count: {len(grok_result.get('products', []))}")
                logger.info(f"[DEBUG] Products sample: {grok_result.get('products', [])[:2]}")
            else:
                logger.warning("[DEBUG] grok_result is None after Grok extraction!")
            
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
            processing_time = (time.time() - start_time) * 1000
            ingestion_result = self._ingest_into_database(
                file_path, validation_result, grok_result, product_matching_result,
                processing_time, existing_document_id if 'existing_document_id' in locals() else None
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
            
            logger.info(f"✅ PostgreSQL production pipeline completed successfully in {processing_time:.2f}ms")
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
            logger.error(f"❌ PostgreSQL production pipeline failed: {e}")
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
            file_hash = self._calculate_file_hash(file_path)
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Check by file hash first (most reliable)
                    cur.execute("""
                        SELECT id, document_name, source_file_path, processing_time_ms, 
                               extraction_confidence, status, validation_details_json
                        FROM letters 
                        WHERE file_hash = %s OR source_file_path = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, [file_hash, str(file_path.resolve())])
                    
                    result = cur.fetchone()
                    
                    if result:
                        # Parse validation details to check compliance
                        validation_details = result.get('validation_details_json', {})
                        if isinstance(validation_details, str):
                            try:
                                validation_details = json.loads(validation_details)
                            except:
                                validation_details = {}
                        
                        confidence_score = validation_details.get('confidence_score', 0.0)
                        is_compliant = confidence_score >= 0.95
                        
                        logger.info(f"📋 Document found in database: ID={result['id']}")
                        logger.info(f"📅 Previous processing: {result.get('created_at')}")
                        logger.info(f"📊 Status: {result['status']}")
                        logger.info(f"📂 Existing path: {result['source_file_path']}")
                        
                        return DocumentCheckResult(
                            exists=True,
                            document_id=result['id'],
                            content_compliant=is_compliant,
                            file_hash=file_hash,
                            processing_time_ms=result.get('processing_time_ms'),
                            confidence_score=confidence_score
                        )
                    
                    return DocumentCheckResult(exists=False, file_hash=file_hash)
                    
        except Exception as e:
            logger.error(f"❌ Error checking document existence: {e}")
            return DocumentCheckResult(exists=False)
    
    def _delete_existing_document(self, document_id: int) -> None:
        """Delete existing document and all related records"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Delete child records first (CASCADE will handle this automatically)
                    cur.execute("DELETE FROM letters WHERE id = %s", [document_id])
                    conn.commit()
                    logger.info(f"🗑️ Deleted child records for document: ID={document_id}")
                    
        except Exception as e:
            logger.error(f"❌ Error deleting existing document: {e}")
            raise
    
    def _validate_content_compliance(self, file_path: Path) -> ContentValidationResult:
        """Validate document content compliance"""
        try:
            logger.info("🔍 Extracting document content for validation")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                logger.error("❌ Document processing failed")
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["Document processing failed"],
                    product_ranges=[],
                    document_type="unknown"
                )
            document_content = document.text
            
            if not document_content:
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["No content extracted from document"],
                    product_ranges=[],
                    document_type="unknown"
                )
            
            logger.info(f"📄 Document content extracted: {len(document_content)} characters")
            
            # Check network connectivity for XAI validation
            if not self._check_network_connectivity():
                logger.error("❌ Network connectivity issues detected - XAI validation required but unavailable")
                # CRITICAL: Don't proceed without XAI validation
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["XAI validation required but network connectivity failed"],
                    product_ranges=[],
                    document_type="unknown"
                )
            
            # Validate with XAI service
            validation_prompt = f"""
            Analyze this document content and determine if it's a Schneider Electric obsolescence letter.
            
            Document: {file_path.name}
            Content: {document_content[:2000]}...
            
            Return a JSON response with:
            - is_compliant: boolean (true if it's a valid SE obsolescence letter)
            - confidence_score: float (0.0-1.0)
            - validation_errors: array of error messages (empty if compliant)
            - product_ranges: array of product ranges mentioned
            - document_type: string (pdf, docx, etc.)
            - document_title: string (extracted title)
            """
            
            validation_response = self.xai_service.generate_completion(
                prompt=validation_prompt,
                document_content=document_content,
                document_name=file_path.name
            )
            
            if not validation_response:
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["XAI validation failed"],
                    product_ranges=[],
                    document_type="unknown"
                )
            
            # Parse validation response
            try:
                validation_data = json.loads(validation_response)
                return ContentValidationResult(
                    is_compliant=validation_data.get('is_compliant', False),
                    confidence_score=validation_data.get('confidence_score', 0.0),
                    validation_errors=validation_data.get('validation_errors', []),
                    product_ranges=validation_data.get('product_ranges', []),
                    document_type=validation_data.get('document_type', 'unknown'),
                    document_title=validation_data.get('document_title')
                )
            except json.JSONDecodeError:
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["Invalid XAI validation response"],
                    product_ranges=[],
                    document_type="unknown"
                )
                
        except Exception as e:
            logger.error(f"❌ Content validation failed: {e}")
            return ContentValidationResult(
                is_compliant=False,
                confidence_score=0.0,
                validation_errors=[f"Validation error: {e}"],
                product_ranges=[],
                document_type="unknown"
            )
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity for XAI API"""
        try:
            import socket
            import urllib.request
            import os
            
            # Test DNS resolution for api.x.ai
            socket.gethostbyname("api.x.ai")
            
            # Test connectivity with proper authentication
            api_key = os.getenv('XAI_API_KEY')
            if not api_key:
                logger.error("❌ XAI_API_KEY environment variable not set")
                return False
            
            # Test with a simple authenticated request
            req = urllib.request.Request(
                'https://api.x.ai/v1/models',
                headers={
                    'User-Agent': 'SE-Letters-Pipeline/2.2.0',
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            )
            urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            logger.warning(f"⚠️ Network connectivity check failed: {e}")
            return False
    
    def _process_with_grok(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """Process document with Grok (no fallback)"""
        try:
            logger.info("🤖 Processing document with Grok (no fallback)")
            
            # Extract document content
            document = self.document_processor.process_document(file_path)
            if not document:
                logger.error("❌ Document processing failed")
                return None
            document_content = document.text
            
            if not document_content:
                logger.error("❌ No content extracted for Grok processing")
                return None
            
            logger.info("🔄 Requesting comprehensive extraction from Grok")
            
            # Process with Grok
            grok_metadata = self.xai_service.extract_comprehensive_metadata(
                text=document_content,
                document_name=file_path.name
            )
            
            if not grok_metadata:
                logger.error("❌ Grok processing returned no results")
                return None
            
            logger.info("✅ Grok processing completed successfully")
            logger.info(f"📊 Extracted {len(grok_metadata.get('products', []))} products")
            
            return grok_metadata
            
        except Exception as e:
            logger.error(f"❌ Grok processing failed: {e}")
            return None
    
    def _process_product_matching(self, grok_result: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Process product matching using intelligent matching with prompts.yaml"""
        try:
            logger.info("🔍 Processing product matching with intelligent matching")
            
            # Extract product ranges from Grok result (new unified schema)
            product_ranges = []
            
            # Check for new unified schema structure
            if 'product_identification' in grok_result:
                product_identification = grok_result['product_identification']
                ranges = product_identification.get('ranges', [])
                descriptions = product_identification.get('descriptions', [])
                product_types = product_identification.get('product_types', [])
                
                for i, range_label in enumerate(ranges):
                    product_ranges.append({
                        'range_label': range_label,
                        'subrange_label': None,
                        'product_description': descriptions[i] if i < len(descriptions) else '',
                        'technical_specifications': {},
                        'product_line': self._determine_product_line(range_label, product_types)
                    })
            
            # Fallback to old structure if needed
            elif 'product_information' in grok_result:
                for product in grok_result['product_information']:
                    if 'range_label' in product and product['range_label']:
                        product_ranges.append({
                            'range_label': product['range_label'],
                            'subrange_label': product.get('subrange_label'),
                            'product_description': product.get('product_description', ''),
                            'technical_specifications': product.get('technical_specifications', {}),
                            'product_line': product.get('product_line', '')
                        })
            
            if not product_ranges:
                logger.warning("⚠️ No product ranges found for matching")
                return {
                    'success': True,
                    'matched_products': [],
                    'matching_confidence': 0.0,
                    'matching_errors': ['No product ranges to match']
                }
            
            # Use enhanced mapping service to discover product candidates
            all_matched_products = []
            total_confidence = 0.0
            
            for product_range in product_ranges:
                logger.info(f"🔍 Processing range: {product_range['range_label']}")
                
                # Step 1: Use enhanced mapping service to discover candidates
                mapping_result = self.enhanced_mapping_service.process_product_mapping(
                    product_identifier=product_range['range_label'],
                    range_label=product_range['range_label'],
                    subrange_label=product_range.get('subrange_label'),
                    product_line=product_range.get('product_line', ''),
                    additional_context={'product_description': product_range.get('product_description', '')}
                )
                
                if not mapping_result.modernization_candidates:
                    logger.warning(f"⚠️ No candidates found for range {product_range['range_label']}")
                    continue
                
                # Step 2: Use intelligent product matching prompt to convert ranges to individual products
                # Convert ProductMatch objects to dictionaries for the intelligent matching
                candidates_dict = []
                for candidate in mapping_result.modernization_candidates:
                    candidates_dict.append({
                        'product_identifier': candidate.product_identifier,
                        'range_label': candidate.range_label,
                        'subrange_label': candidate.subrange_label,
                        'product_description': candidate.product_description,
                        'brand_label': candidate.brand_label,
                        'pl_services': candidate.pl_services,
                        'devicetype_label': candidate.devicetype_label,
                        'commercial_status': candidate.commercial_status,
                        'confidence_score': candidate.confidence_score,
                        'match_reason': candidate.match_reason
                    })
                
                intelligent_matches = self._apply_intelligent_product_matching(
                    product_range, candidates_dict
                )
                
                if intelligent_matches:
                    all_matched_products.extend(intelligent_matches)
                    total_confidence += sum(match.get('confidence', 0.0) for match in intelligent_matches)
                    logger.info(f"✅ Found {len(intelligent_matches)} intelligent matches for range {product_range['range_label']}")
                else:
                    logger.warning(f"⚠️ No intelligent matches for range {product_range['range_label']}")
            
            # Calculate average confidence
            avg_confidence = total_confidence / len(all_matched_products) if all_matched_products else 0.0
            
            return {
                'success': True,
                'matched_products': all_matched_products,
                'matching_confidence': avg_confidence,
                'matching_errors': [],
                'total_ranges_processed': len(product_ranges),
                'total_products_found': len(all_matched_products)
            }
            
        except Exception as e:
            logger.error(f"❌ Error in product matching: {e}")
            return {
                'success': False,
                'matched_products': [],
                'matching_confidence': 0.0,
                'matching_errors': [str(e)]
            }
    
    def _apply_intelligent_product_matching(self, product_range: Dict[str, Any], 
                                           discovered_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply intelligent product matching using prompts.yaml"""
        try:
            logger.info(f"🧠 Applying intelligent product matching for range: {product_range['range_label']}")
            
            # Load prompts from config
            import yaml
            with open('config/prompts.yaml', 'r') as f:
                prompts_config = yaml.safe_load(f)
            
            # Get the intelligent product matching prompt
            prompt_config = prompts_config['prompts']['intelligent_product_matching']
            system_prompt = prompt_config['system_prompt']
            user_prompt_template = prompt_config['user_prompt_template']
            
            # Prepare letter product info
            letter_product_info = {
                'range_label': product_range['range_label'],
                'subrange_label': product_range.get('subrange_label'),
                'product_description': product_range.get('product_description', ''),
                'technical_specifications': product_range.get('technical_specifications', {}),
                'product_line': product_range.get('product_line', '')
            }
            
            # Format the user prompt
            user_prompt = user_prompt_template.format(
                letter_product_info=json.dumps(letter_product_info, indent=2),
                discovered_candidates=json.dumps(discovered_candidates, indent=2)
            )
            
            # Concatenate system and user prompt
            full_prompt = system_prompt + "\n\n" + user_prompt
            
            # Call xAI service with the intelligent matching prompt
            intelligent_result = self.xai_service.extract_comprehensive_metadata(
                text=full_prompt,
                document_name=f"intelligent_matching_{product_range['range_label']}"
            )
            
            if not intelligent_result or not intelligent_result.get('success'):
                logger.warning(f"⚠️ Intelligent matching failed for range {product_range['range_label']}")
                return []
            
            # Parse the intelligent matching result
            try:
                matching_data = json.loads(intelligent_result.get('extracted_metadata', '{}'))
                matching_products = matching_data.get('matching_products', [])
                
                logger.info(f"✅ Intelligent matching found {len(matching_products)} products")
                return matching_products
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse intelligent matching result: {e}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error in intelligent product matching: {e}")
            return []
    
    def _determine_product_line(self, range_label: str, product_types: List[str]) -> str:
        """Determine product line based on range label and product types"""
        range_lower = range_label.lower()
        types_lower = [pt.lower() for pt in product_types]
        
        # Check for product line indicators
        if any(keyword in range_lower for keyword in ['ups', 'galaxy', 'uninterruptible', 'backup']):
            return 'SPIBS'
        elif any(keyword in range_lower for keyword in ['acb', 'masterpact', 'powerpact', 'easypact']):
            return 'PPIBS'
        elif any(keyword in range_lower for keyword in ['plc', 'automation', 'control']):
            return 'DPIBS'
        elif any(keyword in range_lower for keyword in ['power', 'distribution', 'transformer']):
            return 'PSIBS'
        
        # Check product types
        if any('medium voltage' in pt for pt in types_lower):
            return 'PSIBS'
        elif any('low voltage' in pt for pt in types_lower):
            return 'PPIBS'
        
        # Default to PSIBS for power systems
        return 'PSIBS'

    def _ingest_into_database(self, file_path: Path, validation_result: ContentValidationResult, 
                             grok_result: Dict[str, Any], product_matching_result: Dict[str, Any],
                             processing_time_ms: float, existing_document_id: Optional[int] = None) -> Dict[str, Any]:
        """Ingest processing results into PostgreSQL database"""
        try:
            logger.info("💾 Ingesting results into database")
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            print(f"[DEBUG] Attempting to insert letter: document_name={file_path.name}, file_hash={file_hash}")
            
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    try:
                        print("[DEBUG] Executing letter insert...")
                        cur.execute(
                            """
                            INSERT INTO letters (
                                document_name, document_type, document_title, source_file_path,
                                file_size, processing_method, processing_time_ms, extraction_confidence,
                                raw_grok_json, ocr_supplementary_json, processing_steps_json,
                                file_hash, validation_details_json
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                            """, [
                                file_path.name,
                                grok_result.get('document_type', 'unknown'),
                                grok_result.get('document_title'),
                                str(file_path),
                                file_path.stat().st_size if file_path.exists() else None,
                                'production_pipeline',
                                processing_time_ms,
                                grok_result.get('extraction_metadata', {}).get('confidence', 0.0),
                                json.dumps(grok_result.get('raw_grok_json')) if grok_result.get('raw_grok_json') else None,
                                json.dumps(grok_result.get('ocr_supplementary_json')) if grok_result.get('ocr_supplementary_json') else None,
                                json.dumps(grok_result.get('processing_steps_json')) if grok_result.get('processing_steps_json') else None,
                                file_hash,
                                json.dumps(grok_result.get('validation_details_json')) if grok_result.get('validation_details_json') else None
                            ]
                        )
                        letter_id = cur.fetchone()[0]
                        print(f"[DEBUG] Successfully inserted letter with ID: {letter_id}")
                        
                        # Insert product ranges from Grok result (new unified schema)
                        product_ranges = []
                        
                        # Handle new unified schema structure
                        if 'product_identification' in grok_result:
                            product_identification = grok_result['product_identification']
                            ranges = product_identification.get('ranges', [])
                            descriptions = product_identification.get('descriptions', [])
                            product_types = product_identification.get('product_types', [])
                            
                            for i, range_label in enumerate(ranges):
                                product_ranges.append({
                                    'range_label': range_label,
                                    'product_description': descriptions[i] if i < len(descriptions) else '',
                                    'product_line': self._determine_product_line(range_label, product_types)
                                })
                        
                        # Fallback to old structure
                        elif 'product_information' in grok_result:
                            product_ranges = grok_result.get('product_information', [])
                        
                        print(f"[DEBUG] Inserting {len(product_ranges)} product ranges for letter ID: {letter_id}")
                        for idx, product_range in enumerate(product_ranges):
                            print(f"[DEBUG] Inserting product range {idx+1}/{len(product_ranges)}: {product_range.get('range_label', 'N/A')}")
                            cur.execute(
                                """
                                INSERT INTO letter_products (
                                    letter_id, product_identifier, range_label, subrange_label,
                                    product_line, product_description, obsolescence_status,
                                    end_of_service_date, replacement_suggestions, confidence_score
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING id
                                """, [
                                    letter_id,
                                    product_range.get('product_identifier'),
                                    product_range.get('range_label'),
                                    product_range.get('subrange_label'),
                                    product_range.get('product_line'),
                                    product_range.get('product_description'),
                                    product_range.get('obsolescence_status'),
                                    product_range.get('end_of_service_date'),
                                    product_range.get('replacement_suggestions'),
                                    product_range.get('confidence_score', 0.0)
                                ]
                            )
                            product_id = cur.fetchone()[0]
                            print(f"[DEBUG] Successfully inserted product range with ID: {product_id}")
                        
                        # Insert matched products from intelligent matching
                        matched_products = product_matching_result.get('matched_products', [])
                        print(f"[DEBUG] Inserting {len(matched_products)} matched products for letter ID: {letter_id}")
                        for idx, match in enumerate(matched_products):
                            print(f"[DEBUG] Inserting match {idx+1}/{len(matched_products)}: {match.get('product_identifier', 'N/A')}")
                            cur.execute(
                                """
                                INSERT INTO letter_product_matches (
                                    letter_id, letter_product_id, ibcatalogue_product_identifier,
                                    match_confidence, match_reason, technical_match_score,
                                    nomenclature_match_score, product_line_match_score,
                                    match_type, range_based_matching
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, [
                                    letter_id,
                                    None, # letter_product_id (can be linked if available)
                                    match.get('product_identifier'),
                                    match.get('confidence', 0.0),
                                    match.get('reason'),
                                    match.get('technical_match_score', 0.0),
                                    match.get('nomenclature_match_score', 0.0),
                                    match.get('product_line_match_score', 0.0),
                                    match.get('match_type'),
                                    match.get('range_based_matching', False)
                                ]
                            )
                            print(f"[DEBUG] Successfully inserted match for product: {match.get('product_identifier')}")
                        
                        conn.commit()
                        print(f"[DEBUG] Database transaction committed successfully for letter ID: {letter_id}")
                        return {
                            'success': True,
                            'document_id': letter_id,
                            'products_inserted': len(product_ranges),
                            'matches_inserted': len(matched_products)
                        }
                    except Exception as e:
                        conn.rollback()
                        print(f"[DEBUG] Database transaction failed and rolled back: {e}")
                        raise
                    
        except Exception as e:
            logger.error(f"❌ Database ingestion failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _save_json_outputs(self, file_path: Path, document_id: int, validation_result: ContentValidationResult,
                          grok_result: Dict[str, Any], ingestion_result: Dict[str, Any], processing_time_ms: float) -> None:
        """Save JSON outputs for webapp consumption"""
        try:
            # Create output metadata
            output_metadata = OutputMetadata(
                document_id=str(document_id),
                document_name=file_path.name,
                source_file_path=str(file_path.resolve()),
                processing_timestamp=datetime.now().isoformat(),
                processing_duration_ms=processing_time_ms,
                confidence_score=validation_result.confidence_score,
                success=True,
                pipeline_method="postgresql_production_pipeline"
            )
            
            # Prepare outputs dictionary
            outputs = {
                'validation_result': validation_result.__dict__,
                'grok_result': grok_result,
                'ingestion_result': ingestion_result,
                'processing_summary': {
                    'document_id': document_id,
                    'processing_time_ms': processing_time_ms,
                    'success': True
                }
            }
            
            # Save outputs
            self.json_output_manager.save_document_outputs(
                document_id=str(document_id),
                document_name=file_path.name,
                source_file_path=str(file_path.resolve()),
                outputs=outputs,
                metadata=output_metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to save JSON outputs: {e}")
            raise
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics from PostgreSQL database"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Get basic statistics
                    cur.execute("SELECT COUNT(*) FROM letters")
                    total_documents = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM letters WHERE status = 'processed'")
                    processed_documents = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM letters WHERE status = 'failed'")
                    failed_documents = cur.fetchone()[0]
                    
                    # Get recent processing stats
                    cur.execute("""
                        SELECT COUNT(*) FROM letters 
                        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    """)
                    recent_processing = cur.fetchone()[0]
                    
                    # Get average confidence scores
                    cur.execute("""
                        SELECT AVG(CAST(validation_details_json->>'confidence_score' AS FLOAT))
                        FROM letters 
                        WHERE validation_details_json IS NOT NULL
                    """)
                    avg_confidence = cur.fetchone()[0] or 0.0
                    
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
                'success_rate': 0.0
            } 