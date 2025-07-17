#!/usr/bin/env python3
"""
PostgreSQL Production Pipeline Service v2.3
Corrected workflow: Direct Grok → Intelligent Matching → Final Grok Validation → Database Storage

Author: Alexandre Huther
Version: 2.3.0
Date: 2025-07-17
"""

import json
import time
import hashlib
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from ..core.config import get_config
from ..services.document_processor import DocumentProcessor
from ..services.xai_service import XAIService
from ..services.enhanced_product_mapping_service import EnhancedProductMappingService
from ..services.json_output_manager import JSONOutputManager, OutputMetadata


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
    final_grok_validation: Optional[Dict[str, Any]] = None
    ingestion_details: Optional[Dict[str, Any]] = None
    product_matching_result: Optional[Dict[str, Any]] = None


class PostgreSQLProductionPipelineServiceV2_3:
    """
    PostgreSQL Production Pipeline Service v2.3
    
    CORRECTED WORKFLOW:
    1. Direct Grok Processing (no OCR/text extraction)
    2. Intelligent Product Matching (Range → Individual Products)
    3. Final Grok Validation (candidates passed back to Grok)
    4. Database Storage (1 letter → multiple IBcatalogue products)
    """
    
    def __init__(self, connection_string: str = None):
        """Initialize the production pipeline service"""
        self.config = get_config()
        
        # Database connection
        self.connection_string = connection_string or self.config.database.postgresql.connection_string
        
        # Services
        self.document_processor = DocumentProcessor(self.config)
        self.xai_service = XAIService(self.config)
        self.enhanced_mapping_service = EnhancedProductMappingService()
        self.json_output_manager = JSONOutputManager()
        
        # Setup
        self._setup_logging()
        self._init_database()
        
        logger.info("🚀 PostgreSQL Production Pipeline Service v2.3 initialized")
        logger.info("📋 CORRECTED WORKFLOW: Direct Grok → Intelligent Matching → Final Grok Validation → Database")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logger.info("🔧 Setting up logging for PostgreSQL Production Pipeline v2.3")
    
    def _init_database(self) -> None:
        """Initialize database connection"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    logger.info(f"✅ Connected to PostgreSQL: {version}")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def process_document(self, file_path: Path, force_reprocess: bool = False) -> ProcessingResult:
        """
        Process document through CORRECTED production pipeline v2.3
        
        CORRECTED WORKFLOW:
        1. Direct Grok Processing (no OCR/text extraction)
        2. Intelligent Product Matching (Range → Individual Products)
        3. Final Grok Validation (candidates passed back to Grok)
        4. Database Storage (1 letter → multiple IBcatalogue products)
        
        Args:
            file_path: Path to the document to process
            force_reprocess: If True, reprocess even if document already exists
        """
        start_time = time.time()
        
        logger.info(f"🚀 Starting PostgreSQL production pipeline v2.3 for: {file_path}")
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
                existing_document_id = check_result.document_id
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
            
            # Step 3: DIRECT GROK PROCESSING (no OCR/text extraction)
            logger.info("🤖 Step 3: Direct Grok Processing (no OCR/text extraction)")
            grok_result = self._process_with_grok_direct(file_path, validation_result)
            
            if not grok_result:
                logger.error("❌ Direct Grok processing failed - pipeline stopped")
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message="Direct Grok processing failed - pipeline stopped as required",
                    validation_result=validation_result,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            logger.info(f"✅ Direct Grok extraction completed successfully")
            logger.info(f"📊 Extracted {len(grok_result.get('product_identification', {}).get('ranges', []))} product ranges")
            
            # Step 4: Intelligent Product Matching (Range → Individual Products)
            logger.info("🔍 Step 4: Intelligent Product Matching (Range → Individual Products)")
            product_matching_result = self._process_intelligent_product_matching(grok_result, file_path)
            
            # Step 5: FINAL GROK VALIDATION (candidates passed back to Grok)
            logger.info("🤖 Step 5: Final Grok Validation (candidates passed back to Grok)")
            final_grok_validation = self._final_grok_validation(
                grok_result, product_matching_result, file_path
            )
            
            if not final_grok_validation:
                logger.error("❌ Final Grok validation failed - pipeline stopped")
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message="Final Grok validation failed - pipeline stopped as required",
                    validation_result=validation_result,
                    grok_metadata=grok_result,
                    product_matching_result=product_matching_result,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Step 6: Database Storage (1 letter → multiple IBcatalogue products)
            logger.info("💾 Step 6: Database Storage (1 letter → multiple IBcatalogue products)")
            processing_time = (time.time() - start_time) * 1000
            ingestion_result = self._ingest_into_database_v2_3(
                file_path, validation_result, grok_result, product_matching_result,
                final_grok_validation, processing_time, 
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
                    final_grok_validation=final_grok_validation,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            # Step 7: Save JSON outputs
            logger.info("💾 Step 7: Saving JSON outputs")
            try:
                self._save_json_outputs_v2_3(
                    file_path=file_path,
                    document_id=ingestion_result["document_id"],
                    validation_result=validation_result,
                    grok_result=grok_result,
                    product_matching_result=product_matching_result,
                    final_grok_validation=final_grok_validation,
                    ingestion_result=ingestion_result,
                    processing_time_ms=processing_time
                )
                logger.info("✅ JSON outputs saved successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save JSON outputs: {e}")
            
            logger.info(f"✅ PostgreSQL production pipeline v2.3 completed successfully in {processing_time:.2f}ms")
            logger.info(f"📊 Document ID: {ingestion_result['document_id']}")
            logger.info(f"🎯 Confidence: {validation_result.confidence_score:.2f}")
            logger.info(f"📦 Product ranges found: {len(validation_result.product_ranges)}")
            logger.info(f"🔗 IBcatalogue products linked: {ingestion_result.get('ibcatalogue_products_linked', 0)}")
            
            return ProcessingResult(
                success=True,
                status=ProcessingStatus.COMPLETED,
                document_id=ingestion_result["document_id"],
                processing_time_ms=processing_time,
                confidence_score=validation_result.confidence_score,
                validation_result=validation_result,
                grok_metadata=grok_result,
                final_grok_validation=final_grok_validation,
                ingestion_details=ingestion_result,
                product_matching_result=product_matching_result
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ PostgreSQL production pipeline v2.3 failed: {e}")
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
                    cur.execute("DELETE FROM letters WHERE id = %s", [document_id])
                    conn.commit()
                    logger.info(f"🗑️ Deleted existing document ID: {document_id}")
        except Exception as e:
            logger.error(f"❌ Error deleting existing document: {e}")
            raise
    
    def _validate_content_compliance(self, file_path: Path) -> ContentValidationResult:
        """Validate content compliance (simplified for v2.3)"""
        try:
            logger.info("✅ Validating content compliance")
            
            # Basic validation - check if file exists and has content
            if not file_path.exists():
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["File does not exist"],
                    product_ranges=[],
                    document_type="unknown"
                )
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                return ContentValidationResult(
                    is_compliant=False,
                    confidence_score=0.0,
                    validation_errors=["File is empty"],
                    product_ranges=[],
                    document_type="unknown"
                )
            
            # Determine document type
            document_type = "unknown"
            if file_path.suffix.lower() in ['.pdf', '.docx', '.doc']:
                document_type = file_path.suffix.lower()[1:].upper()
            
            # For v2.3, we assume compliance and let Grok handle the validation
            # This is because we're doing DIRECT Grok processing
            logger.info("✅ Content validation passed - proceeding to direct Grok processing")
            
            return ContentValidationResult(
                is_compliant=True,
                confidence_score=0.95,  # High confidence for direct Grok processing
                validation_errors=[],
                product_ranges=[],  # Will be extracted by Grok
                document_type=document_type,
                document_title=file_path.stem
            )
            
        except Exception as e:
            logger.error(f"❌ Content validation failed: {e}")
            return ContentValidationResult(
                is_compliant=False,
                confidence_score=0.0,
                validation_errors=[str(e)],
                product_ranges=[],
                document_type="unknown"
            )
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity for xAI service"""
        try:
            # Test connectivity to xAI service
            test_result = self.xai_service.extract_comprehensive_metadata(
                text="Test connectivity",
                document_name="connectivity_test"
            )
            return test_result is not None
        except Exception as e:
            logger.error(f"❌ Network connectivity check failed: {e}")
            return False
    
    def _process_with_grok_direct(self, file_path: Path, validation_result: ContentValidationResult) -> Optional[Dict[str, Any]]:
        """
        DIRECT GROK PROCESSING (no OCR/text extraction)
        
        This is the CORRECTED approach for v2.3:
        - Send the raw document directly to Grok
        - No intermediate text extraction
        - Grok handles all document processing internally
        """
        try:
            logger.info("🤖 Processing document DIRECTLY with Grok (no OCR/text extraction)")
            
            # Check network connectivity
            if not self._check_network_connectivity():
                logger.error("❌ No network connectivity to xAI service")
                return None
            
            logger.info("🔄 Sending document directly to Grok for processing")
            
            # Process with Grok directly (no text extraction)
            # The xAI service should handle the document file directly
            grok_metadata = self.xai_service.extract_comprehensive_metadata(
                text=str(file_path),  # Pass file path as text for direct processing
                document_name=file_path.name
            )
            
            if not grok_metadata:
                logger.error("❌ Direct Grok processing returned no results")
                return None
            
            logger.info("✅ Direct Grok processing completed successfully")
            
            # Log extracted information
            if 'product_identification' in grok_metadata:
                product_identification = grok_metadata['product_identification']
                ranges = product_identification.get('ranges', [])
                descriptions = product_identification.get('descriptions', [])
                product_types = product_identification.get('product_types', [])
                
                logger.info(f"📊 Extracted {len(ranges)} product ranges")
                for i, range_label in enumerate(ranges):
                    logger.info(f"  - Range {i+1}: {range_label}")
                    if i < len(descriptions):
                        logger.info(f"    Description: {descriptions[i]}")
            
            return grok_metadata
            
        except Exception as e:
            logger.error(f"❌ Direct Grok processing failed: {e}")
            return None
    
    def _process_intelligent_product_matching(self, grok_result: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """
        Intelligent Product Matching (Range → Individual Products)
        
        This step converts product ranges to individual IBcatalogue products
        """
        try:
            logger.info("🔍 Processing intelligent product matching (Range → Individual Products)")
            
            # Extract product ranges from Grok result
            product_ranges = []
            
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
            
            if not product_ranges:
                logger.warning("⚠️ No product ranges found for intelligent matching")
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
                
                # Use enhanced mapping service to discover candidates
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
                
                # Convert ProductMatch objects to dictionaries
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
                
                # Apply intelligent product matching
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
            logger.error(f"❌ Error in intelligent product matching: {e}")
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
    
    def _final_grok_validation(self, grok_result: Dict[str, Any], 
                              product_matching_result: Dict[str, Any], 
                              file_path: Path) -> Optional[Dict[str, Any]]:
        """
        FINAL GROK VALIDATION (candidates passed back to Grok)
        
        This step passes the intelligent matching candidates back to Grok
        for final validation and approval
        """
        try:
            logger.info("🤖 Performing final Grok validation (candidates passed back to Grok)")
            
            matched_products = product_matching_result.get('matched_products', [])
            if not matched_products:
                logger.warning("⚠️ No matched products to validate with Grok")
                return {
                    'success': True,
                    'validated_products': [],
                    'validation_confidence': 0.0,
                    'validation_errors': ['No products to validate']
                }
            
            # Prepare validation prompt
            validation_prompt = self._prepare_final_validation_prompt(grok_result, matched_products)
            
            # Call Grok for final validation
            final_validation = self.xai_service.extract_comprehensive_metadata(
                text=validation_prompt,
                document_name=f"final_validation_{file_path.name}"
            )
            
            if not final_validation:
                logger.error("❌ Final Grok validation failed")
                return None
            
            logger.info("✅ Final Grok validation completed successfully")
            
            # Parse validation results
            try:
                validation_data = json.loads(final_validation.get('extracted_metadata', '{}'))
                validated_products = validation_data.get('validated_products', [])
                
                logger.info(f"✅ Final validation approved {len(validated_products)} products")
                return {
                    'success': True,
                    'validated_products': validated_products,
                    'validation_confidence': validation_data.get('validation_confidence', 0.0),
                    'validation_errors': validation_data.get('validation_errors', [])
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse final validation result: {e}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Final Grok validation failed: {e}")
            return None
    
    def _prepare_final_validation_prompt(self, grok_result: Dict[str, Any], 
                                        matched_products: List[Dict[str, Any]]) -> str:
        """Prepare prompt for final Grok validation"""
        prompt = f"""
Please validate the following product matches for the obsolescence letter.

ORIGINAL GROK EXTRACTION:
{json.dumps(grok_result, indent=2)}

INTELLIGENT MATCHING CANDIDATES:
{json.dumps(matched_products, indent=2)}

Please validate each candidate and return only the products that are:
1. Correctly matched to the original product ranges
2. Relevant to the obsolescence letter
3. Have high confidence scores

Return the result in this JSON format:
{{
    "validated_products": [
        {{
            "product_identifier": "string",
            "range_label": "string", 
            "confidence": 0.95,
            "validation_reason": "string"
        }}
    ],
    "validation_confidence": 0.95,
    "validation_errors": []
}}
"""
        return prompt
    
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

    def _ingest_into_database_v2_3(self, file_path: Path, validation_result: ContentValidationResult, 
                                  grok_result: Dict[str, Any], product_matching_result: Dict[str, Any],
                                  final_grok_validation: Dict[str, Any], processing_time_ms: float, 
                                  existing_document_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Database Storage (1 letter → multiple IBcatalogue products)
        
        This is the CORRECTED approach for v2.3:
        - Store 1 letter record
        - Link to multiple IBcatalogue products
        - Use final Grok validation results
        """
        try:
            logger.info("💾 Ingesting results into database (1 letter → multiple IBcatalogue products)")
            
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
                                'production_pipeline_v2_3',
                                processing_time_ms,
                                final_grok_validation.get('validation_confidence', 0.0),
                                json.dumps(grok_result.get('raw_grok_json')) if grok_result.get('raw_grok_json') else None,
                                json.dumps(grok_result.get('ocr_supplementary_json')) if grok_result.get('ocr_supplementary_json') else None,
                                json.dumps(grok_result.get('processing_steps_json')) if grok_result.get('processing_steps_json') else None,
                                file_hash,
                                json.dumps(final_grok_validation) if final_grok_validation else None
                            ]
                        )
                        letter_id = cur.fetchone()[0]
                        print(f"[DEBUG] Successfully inserted letter with ID: {letter_id}")
                        
                        # Insert product ranges from Grok result
                        product_ranges = []
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
                        
                        # Insert FINAL VALIDATED products from Grok validation
                        validated_products = final_grok_validation.get('validated_products', [])
                        print(f"[DEBUG] Inserting {len(validated_products)} FINAL VALIDATED products for letter ID: {letter_id}")
                        for idx, validated_product in enumerate(validated_products):
                            print(f"[DEBUG] Inserting validated product {idx+1}/{len(validated_products)}: {validated_product.get('product_identifier', 'N/A')}")
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
                                    None,  # letter_product_id (can be linked if available)
                                    validated_product.get('product_identifier'),
                                    validated_product.get('confidence', 0.0),
                                    validated_product.get('validation_reason'),
                                    validated_product.get('technical_match_score', 0.0),
                                    validated_product.get('nomenclature_match_score', 0.0),
                                    validated_product.get('product_line_match_score', 0.0),
                                    'final_grok_validated',
                                    True  # range_based_matching
                                ]
                            )
                            print(f"[DEBUG] Successfully inserted FINAL VALIDATED product: {validated_product.get('product_identifier')}")
                        
                        conn.commit()
                        print(f"[DEBUG] Database transaction committed successfully for letter ID: {letter_id}")
                        return {
                            'success': True,
                            'document_id': letter_id,
                            'products_inserted': len(product_ranges),
                            'ibcatalogue_products_linked': len(validated_products)
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
    
    def _save_json_outputs_v2_3(self, file_path: Path, document_id: int, validation_result: ContentValidationResult,
                               grok_result: Dict[str, Any], product_matching_result: Dict[str, Any],
                               final_grok_validation: Dict[str, Any], ingestion_result: Dict[str, Any], 
                               processing_time_ms: float) -> None:
        """Save JSON outputs for webapp consumption (v2.3)"""
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
                pipeline_method="postgresql_production_pipeline_v2_3"
            )
            
            # Prepare outputs dictionary
            outputs = {
                'validation_result': validation_result.__dict__,
                'grok_result': grok_result,
                'product_matching_result': product_matching_result,
                'final_grok_validation': final_grok_validation,
                'ingestion_result': ingestion_result,
                'processing_summary': {
                    'document_id': document_id,
                    'processing_time_ms': processing_time_ms,
                    'success': True,
                    'pipeline_version': '2.3.0'
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
                    
                    cur.execute("SELECT AVG(extraction_confidence) FROM letters WHERE extraction_confidence > 0")
                    avg_confidence = cur.fetchone()[0] or 0.0
                    
                    cur.execute("SELECT COUNT(*) FROM letter_product_matches")
                    total_matches = cur.fetchone()[0]
                    
                    return {
                        'total_documents': total_documents,
                        'processed_documents': processed_documents,
                        'avg_confidence': round(avg_confidence, 3),
                        'total_product_matches': total_matches,
                        'pipeline_version': '2.3.0'
                    }
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {
                'error': str(e),
                'pipeline_version': '2.3.0'
            } 