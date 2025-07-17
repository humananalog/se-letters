#!/usr/bin/env python3
"""
PostgreSQL Production Pipeline Service v2.3 - STAGE 1 Implementation
Enhanced document processing with intelligent duplicate detection,
token usage tracking, and raw content management
"""

import json
import time
import hashlib
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.enhanced_xai_service import EnhancedXAIService
from se_letters.services.document_processor import DocumentProcessor


@dataclass
class ProcessingDecision:
    """Result of document processing decision logic"""
    should_process: bool
    decision: str  # 'PROCESS', 'FORCE', 'SKIP', 'REJECT'
    reason: str
    existing_letter_id: Optional[int] = None
    existing_has_products: bool = False
    will_replace: bool = False


class DocumentProcessingLogic:
    """State-of-the-art document processing decision logic"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def determine_processing_action(
        self, 
        file_path: Path, 
        request_type: str,  # 'PROCESS' or 'FORCE'
    ) -> ProcessingDecision:
        """
        Determine processing action based on file existence and content
        
        Logic:
        A. EXISTS + NO_PRODUCTS + PROCESS → ACCEPT (hope Grok finds products)
        B. EXISTS + HAS_PRODUCTS + PROCESS → REJECT (already processed)
        C. NOT_EXISTS + PROCESS → ACCEPT (new document)
        D. EXISTS + FORCE → ACCEPT (replace existing)
        E. NOT_EXISTS + FORCE → ACCEPT (new document)
        """
        
        # Calculate file identification
        file_hash = self._calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        # Check database for existing document
        existing_letter = self._find_existing_document(
            file_hash, file_path.name, file_size
        )
        
        if existing_letter:
            existing_has_products = existing_letter['has_products']
            existing_letter_id = existing_letter['id']
            
            if request_type == 'PROCESS':
                if existing_has_products:
                    # Case B: Already processed successfully
                    return ProcessingDecision(
                        should_process=False,
                        decision='REJECT',
                        reason=(f"Document already processed successfully "
                                f"with {existing_letter['product_count']} "
                                f"products found"),
                        existing_letter_id=existing_letter_id,
                        existing_has_products=True
                    )
                else:
                    # Case A: Processed but no products found - try again
                    return ProcessingDecision(
                        should_process=True,
                        decision='PROCESS',
                        reason=("Document processed previously but no "
                                "products found - attempting reprocessing"),
                        existing_letter_id=existing_letter_id,
                        existing_has_products=False
                    )
            else:  # FORCE
                # Case D: Force reprocessing - will replace
                return ProcessingDecision(
                    should_process=True,
                    decision='FORCE',
                    reason=("Force reprocessing requested - "
                            "will replace existing content"),
                    existing_letter_id=existing_letter_id,
                    existing_has_products=existing_has_products,
                    will_replace=True
                )
        else:
            # Case C/E: New document
            return ProcessingDecision(
                should_process=True,
                decision=request_type,
                reason="New document - will process",
                existing_letter_id=None,
                existing_has_products=False
            )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _find_existing_document(
        self, file_hash: str, document_name: str, file_size: int
    ) -> Optional[Dict]:
        """Find existing document using multiple criteria"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    cur.execute("""
                        SELECT id, document_name, file_hash, file_size, 
                               has_products, product_count, processing_status, 
                               extraction_confidence
                        FROM letters 
                        WHERE file_hash = %s 
                           OR (document_name = %s AND file_size = %s)
                        ORDER BY created_at DESC
                        LIMIT 1
                    """, [file_hash, document_name, file_size])
                    
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error finding existing document: {e}")
            return None


class GrokIntegrationService:
    """Enhanced Grok integration with token usage tracking and raw content 
    management"""
    
    def __init__(
        self, 
        enhanced_xai_service: EnhancedXAIService, 
        document_processor: DocumentProcessor
    ):
        self.enhanced_xai_service = enhanced_xai_service
        self.document_processor = document_processor
    
    def process_document_with_grok(self, file_path: Path, letter_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process document with Grok and return structured output with comprehensive tracking
        
        Returns:
            Dict containing:
            - success: bool
            - grok_metadata: Complete Grok output
            - products: Extracted products
            - confidence: Overall confidence score
            - processing_time: Processing duration
            - tracking_metadata: Token usage and tracking information
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 Processing document with enhanced Grok integration: {file_path.name}")
            
            # Extract document content using DocumentProcessor
            document = self.document_processor.process_document(file_path)
            if not document or not document.text:
                return {
                    'success': False,
                    'error': 'Failed to extract document content',
                    'processing_time': (time.time() - start_time) * 1000
                }
            
            document_content = document.text
            logger.info(f"📄 Document content extracted: {len(document_content)} characters")
            
            # Determine extraction method
            extraction_method = self._determine_extraction_method(file_path)
            
            # Process with enhanced Grok service (includes token tracking and raw content storage)
            grok_result = self.enhanced_xai_service.extract_comprehensive_metadata_with_tracking(
                text=document_content,
                document_name=file_path.name,
                letter_id=letter_id,
                extraction_method=extraction_method,
                source_file_path=str(file_path.resolve()),
                source_file_size=file_path.stat().st_size
            )
            
            if not grok_result:
                return {
                    'success': False,
                    'error': 'Enhanced Grok processing returned no results',
                    'processing_time': (time.time() - start_time) * 1000
                }
            
            # Check if result is from cache
            from_cache = grok_result.get('from_cache', False)
            if from_cache:
                logger.info(f"🔄 Using cached result from content ID: {grok_result.get('cache_content_id')}")
            
            # Parse and validate Grok output
            parsed_result = self._parse_grok_output(grok_result)
            
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                'success': True,
                'grok_metadata': grok_result,
                'products': parsed_result['products'],
                'confidence': parsed_result['confidence'],
                'processing_time': processing_time,
                'document_info': parsed_result['document_info'],
                'from_cache': from_cache
            }
            
            # Add tracking metadata if available
            if 'tracking_metadata' in grok_result:
                result['tracking_metadata'] = grok_result['tracking_metadata']
                logger.info(f"📊 Token usage: {grok_result['tracking_metadata'].get('token_usage', {})}")
            
            logger.info(f"✅ Enhanced Grok processing completed: {len(parsed_result['products'])} products found")
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Enhanced Grok processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def _determine_extraction_method(self, file_path: Path) -> str:
        """Determine extraction method based on file extension"""
        suffix = file_path.suffix.lower()
        if suffix == '.pdf':
            return 'pdf_pymupdf'
        elif suffix in ['.docx', '.doc']:
            return 'docx_python'
        else:
            return 'unknown'
    
    def _parse_grok_output(self, grok_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate Grok output structure"""
        
        # Handle both new schema format and legacy format
        products = []
        
        # Try new schema format first (product_information)
        if 'product_information' in grok_result:
            for product in grok_result['product_information']:
                products.append({
                    'product_identifier': product.get('product_identifier'),
                    'range_label': product.get('range_label'),
                    'subrange_label': product.get('subrange_label'),
                    'product_line': product.get('product_line'),
                    'product_description': product.get('product_description'),
                    'obsolescence_status': product.get('commercial_information', {}).get('obsolescence_status'),
                    'end_of_service_date': product.get('commercial_information', {}).get('end_of_service_date'),
                    'replacement_suggestions': product.get('replacement_information', {}).get('replacement_suggestions', []),
                    'confidence_score': product.get('confidence_score', 0.0)
                })
        
        # Fall back to legacy format (products)
        elif 'products' in grok_result:
            for product in grok_result['products']:
                products.append({
                    'product_identifier': product.get('product_identifier'),
                    'range_label': product.get('range_label'),
                    'subrange_label': product.get('subrange_label'),
                    'product_line': product.get('product_line'),
                    'product_description': product.get('product_description'),
                    'obsolescence_status': product.get('obsolescence_status'),
                    'end_of_service_date': product.get('end_of_service_date'),
                    'replacement_suggestions': product.get('replacement_suggestions'),
                    'confidence_score': product.get('confidence_score', 0.0)
                })
        
        # Extract document information
        document_info = grok_result.get('document_information', {})
        
        # Calculate overall confidence
        confidence = grok_result.get('extraction_confidence', 0.0)
        if confidence == 0.0:
            confidence = grok_result.get('confidence_score', 0.0)
        
        return {
            'products': products,
            'confidence': confidence,
            'document_info': document_info
        }


class DatabaseStorageService:
    """Enhanced database storage with transaction management and tracking integration"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def store_letter_processing_result(
        self, 
        file_path: Path,
        grok_result: Dict[str, Any],
        processing_decision: ProcessingDecision,
        request_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store letter processing result in database with enhanced tracking
        
        Args:
            file_path: Path to processed document
            grok_result: Complete Grok processing result with tracking
            processing_decision: Decision made by processing logic
            request_metadata: Frontend request metadata
        """
        
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    # Start transaction
                    cur.execute("BEGIN")
                    
                    # Handle existing document replacement
                    if processing_decision.will_replace and processing_decision.existing_letter_id:
                        self._replace_existing_document(cur, processing_decision.existing_letter_id)
                    
                    # Insert or update letter record
                    letter_id = self._store_letter_record(
                        cur, file_path, grok_result, processing_decision
                    )
                    
                    # Store products
                    products_stored = self._store_products(
                        cur, letter_id, grok_result.get('products', [])
                    )
                    
                    # Update letter with product count
                    self._update_letter_product_count(cur, letter_id, len(products_stored))
                    
                    # Store processing audit
                    self._store_processing_audit(
                        cur, letter_id, processing_decision, request_metadata, grok_result
                    )
                    
                    # Commit transaction
                    cur.execute("COMMIT")
                    
                    # Log tracking information if available
                    if 'tracking_metadata' in grok_result:
                        tracking = grok_result['tracking_metadata']
                        logger.info(f"📊 Processing tracked: Call ID {tracking.get('call_id')}")
                        logger.info(f"📊 Token usage: {tracking.get('token_usage', {})}")
                        logger.info(f"📊 Raw content ID: {tracking.get('raw_content_id')}")
                    
                    return {
                        'success': True,
                        'letter_id': letter_id,
                        'products_stored': len(products_stored),
                        'processing_decision': processing_decision.decision,
                        'from_cache': grok_result.get('from_cache', False),
                        'tracking_metadata': grok_result.get('tracking_metadata', {})
                    }
                    
        except Exception as e:
            logger.error(f"❌ Database storage failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'letter_id': None,
                'products_stored': 0
            }
    
    def _replace_existing_document(self, cur, existing_letter_id: int):
        """Replace existing document data"""
        # Delete existing products
        cur.execute("DELETE FROM letter_products WHERE letter_id = %s", [existing_letter_id])
        logger.info(f"🗑️ Removed existing products for letter ID: {existing_letter_id}")
    
    def _store_letter_record(self, cur, file_path: Path, grok_result: Dict[str, Any], 
                           processing_decision: ProcessingDecision) -> int:
        """Store letter record in database"""
        
        file_hash = self._calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        # Determine document type
        document_type = self._determine_document_type(file_path)
        
        # Extract document info from Grok
        document_info = grok_result.get('document_information', {})
        
        # Check if we're updating existing record
        if processing_decision.existing_letter_id and processing_decision.will_replace:
            # Update existing record
            cur.execute("""
                UPDATE letters SET
                    processing_method = %s,
                    extraction_confidence = %s,
                    grok_metadata = %s,
                    grok_confidence = %s,
                    grok_processing_timestamp = %s,
                    has_products = %s,
                    product_count = %s,
                    processing_status = %s,
                    processed_at = %s,
                    updated_at = %s
                WHERE id = %s
            """, [
                'production_pipeline_v2_3_stage1',
                grok_result.get('confidence', 0.0),
                json.dumps(grok_result),
                grok_result.get('confidence', 0.0),
                datetime.now(),
                len(grok_result.get('products', [])) > 0,
                len(grok_result.get('products', [])),
                'completed',
                datetime.now(),
                datetime.now(),
                processing_decision.existing_letter_id
            ])
            
            logger.info(f"📝 Updated existing letter record ID: {processing_decision.existing_letter_id}")
            return processing_decision.existing_letter_id
        else:
            # Insert new record
            cur.execute("""
                INSERT INTO letters (
                    document_name, document_type, document_title, source_file_path,
                    file_hash, file_size, processing_method, extraction_confidence,
                    grok_metadata, grok_confidence, grok_processing_timestamp,
                    has_products, product_count, processing_status, processed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                file_path.name,
                document_type,
                document_info.get('document_title'),
                str(file_path.resolve()),
                file_hash,
                file_size,
                'production_pipeline_v2_3_stage1',
                grok_result.get('confidence', 0.0),
                json.dumps(grok_result),
                grok_result.get('confidence', 0.0),
                datetime.now(),
                len(grok_result.get('products', [])) > 0,
                len(grok_result.get('products', [])),
                'completed',
                datetime.now()
            ])
            
            letter_id = cur.fetchone()[0]
            logger.info(f"📝 Created new letter record ID: {letter_id}")
            return letter_id
    
    def _store_products(self, cur, letter_id: int, products: List[Dict[str, Any]]) -> List[int]:
        """Store products for letter"""
        stored_product_ids = []
        
        for product in products:
            # Handle text fields that might be too long
            obsolescence_status = product.get('obsolescence_status')
            if obsolescence_status and len(obsolescence_status) > 100:
                # Store in TEXT field (product_description) if too long
                product_description = f"{product.get('product_description', '')} | Status: {obsolescence_status}"
                obsolescence_status = obsolescence_status[:100] + "..." if len(obsolescence_status) > 100 else obsolescence_status
            else:
                product_description = product.get('product_description')
            
            cur.execute("""
                INSERT INTO letter_products (
                    letter_id, product_identifier, range_label, subrange_label,
                    product_line, product_description, obsolescence_status,
                    end_of_service_date, replacement_suggestions, confidence_score,
                    grok_extraction_confidence
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                letter_id,
                product.get('product_identifier'),
                product.get('range_label'),
                product.get('subrange_label'),
                product.get('product_line'),
                product_description,
                obsolescence_status,
                product.get('end_of_service_date'),
                json.dumps(product.get('replacement_suggestions', [])) if product.get('replacement_suggestions') else None,
                product.get('confidence_score', 0.0),
                product.get('confidence_score', 0.0)
            ])
            
            stored_product_ids.append(cur.fetchone()[0])
        
        logger.info(f"📦 Stored {len(stored_product_ids)} products for letter ID: {letter_id}")
        return stored_product_ids
    
    def _update_letter_product_count(self, cur, letter_id: int, product_count: int):
        """Update letter with final product count"""
        cur.execute("""
            UPDATE letters SET 
                product_count = %s, 
                has_products = %s,
                updated_at = %s
            WHERE id = %s
        """, [product_count, product_count > 0, datetime.now(), letter_id])
        
        logger.info(f"📊 Updated letter ID {letter_id} with {product_count} products")
    
    def _store_processing_audit(self, cur, letter_id: int, processing_decision: ProcessingDecision,
                               request_metadata: Dict[str, Any], grok_result: Dict[str, Any]):
        """Store processing audit record"""
        
        cur.execute("""
            INSERT INTO processing_audit (
                letter_id, processing_decision, decision_reason, request_source,
                request_user, processing_success, processing_duration_ms,
                products_found
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            letter_id,
            processing_decision.decision,
            processing_decision.reason,
            request_metadata.get('source', 'frontend'),
            request_metadata.get('user', 'unknown'),
            grok_result.get('success', False),
            grok_result.get('processing_time', 0.0),
            len(grok_result.get('products', []))
        ])
        
        logger.info(f"📋 Stored processing audit for letter ID: {letter_id}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _determine_document_type(self, file_path: Path) -> str:
        """Determine document type from file extension"""
        suffix = file_path.suffix.lower()
        if suffix == '.pdf':
            return 'pdf'
        elif suffix == '.docx':
            return 'docx'
        elif suffix == '.doc':
            return 'doc'
        else:
            return 'unknown'


class PostgreSQLProductionPipelineServiceStage1:
    """
    STAGE 1 PostgreSQL Production Pipeline Service
    
    Features:
    - Intelligent duplicate detection based on filename, size, and content hash
    - Smart processing logic: PROCESS vs FORCE requests
    - Enhanced Grok integration with token usage tracking
    - Raw content storage with prompt version management
    - Comprehensive database management with proper transaction handling
    - Enhanced audit trail with tracking metadata
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Database connection
        self.connection_string = getattr(
            self.config.data.database, 
            'postgresql', 
            'postgresql://ahuther@localhost:5432/se_letters'
        )
        
        # Initialize services
        self.enhanced_xai_service = EnhancedXAIService(self.config)
        self.document_processor = DocumentProcessor(self.config)
        
        # Initialize components
        self.document_processing_logic = DocumentProcessingLogic(self.connection_string)
        self.grok_integration_service = GrokIntegrationService(
            self.enhanced_xai_service, 
            self.document_processor
        )
        self.database_storage_service = DatabaseStorageService(self.connection_string)
        
        logger.info("🏭 STAGE 1 PostgreSQL Production Pipeline Service initialized")
        logger.info(f"📊 Enhanced token tracking: ENABLED")
        logger.info(f"📦 Raw content management: ENABLED")
        logger.info(f"🗄️ Database: {self.connection_string}")
    
    def process_document(
        self, 
        file_path: Path, 
        request_type: str = "PROCESS",
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process document through STAGE 1 pipeline with comprehensive tracking
        
        Args:
            file_path: Path to document to process
            request_type: 'PROCESS' or 'FORCE'
            request_metadata: Additional request metadata (user, source, etc.)
        
        Returns:
            Dictionary with processing results and tracking metadata
        """
        start_time = time.time()
        
        if request_metadata is None:
            request_metadata = {"source": "api", "user": "unknown"}
        
        try:
            logger.info(f"🚀 Starting STAGE 1 processing: {file_path.name}")
            logger.info(f"📋 Request type: {request_type}")
            
            # Step 1: Document Processing Decision Logic
            logger.info("🔍 Step 1: Analyzing document for processing decision")
            processing_decision = self.document_processing_logic.determine_processing_action(
                file_path, request_type
            )
            
            logger.info(f"📋 Processing decision: {processing_decision.decision}")
            logger.info(f"📋 Reason: {processing_decision.reason}")
            
            if not processing_decision.should_process:
                # Document should not be processed
                processing_time = (time.time() - start_time) * 1000
                return {
                    'success': True,
                    'skipped': True,
                    'decision': processing_decision.decision,
                    'reason': processing_decision.reason,
                    'existing_letter_id': processing_decision.existing_letter_id,
                    'processing_time_ms': processing_time
                }
            
            # Step 2: Enhanced Grok Processing with Token Tracking
            logger.info("🤖 Step 2: Processing with enhanced Grok integration")
            grok_result = self.grok_integration_service.process_document_with_grok(
                file_path, processing_decision.existing_letter_id
            )
            
            if not grok_result['success']:
                logger.error(f"❌ Grok processing failed: {grok_result.get('error')}")
                processing_time = (time.time() - start_time) * 1000
                return {
                    'success': False,
                    'error': grok_result.get('error'),
                    'processing_time_ms': processing_time
                }
            
            # Step 3: Enhanced Database Storage
            logger.info("💾 Step 3: Storing results with enhanced tracking")
            storage_result = self.database_storage_service.store_letter_processing_result(
                file_path, grok_result, processing_decision, request_metadata
            )
            
            if not storage_result['success']:
                logger.error(f"❌ Database storage failed: {storage_result.get('error')}")
                processing_time = (time.time() - start_time) * 1000
                return {
                    'success': False,
                    'error': storage_result.get('error'),
                    'processing_time_ms': processing_time
                }
            
            # Success - compile comprehensive result
            processing_time = (time.time() - start_time) * 1000
            
            result = {
                'success': True,
                'letter_id': storage_result['letter_id'],
                'decision': processing_decision.decision,
                'products_found': storage_result['products_stored'],
                'confidence_score': grok_result.get('confidence', 0.0),
                'processing_time_ms': processing_time,
                'from_cache': grok_result.get('from_cache', False)
            }
            
            # Add enhanced tracking metadata
            if 'tracking_metadata' in grok_result:
                result['tracking_metadata'] = grok_result['tracking_metadata']
            
            logger.info(f"✅ STAGE 1 processing completed successfully")
            logger.info(f"📊 Letter ID: {result['letter_id']}")
            logger.info(f"📦 Products found: {result['products_found']}")
            logger.info(f"🎯 Confidence: {result['confidence_score']:.2f}")
            logger.info(f"⏱️ Processing time: {processing_time:.2f}ms")
            
            if 'tracking_metadata' in result:
                tracking = result['tracking_metadata']
                logger.info(f"📊 Token usage: {tracking.get('token_usage', {})}")
                logger.info(f"📋 Call ID: {tracking.get('call_id')}")
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ STAGE 1 processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': processing_time
            }
    
    def get_processing_analytics(self) -> Dict[str, Any]:
        """Get comprehensive processing analytics including token usage"""
        try:
            # Get token usage analytics from enhanced XAI service
            token_analytics = self.enhanced_xai_service.get_token_usage_analytics(days=7)
            
            # Get content processing summary
            content_analytics = self.enhanced_xai_service.get_content_processing_summary()
            
            # Get processing decision analytics
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            processing_decision,
                            COUNT(*) as decision_count,
                            AVG(products_found) as avg_products,
                            AVG(processing_duration_ms) as avg_duration_ms
                        FROM processing_audit 
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                        GROUP BY processing_decision
                        ORDER BY decision_count DESC
                    """)
                    
                    decision_analytics = [dict(row) for row in cur.fetchall()]
            
            return {
                'token_usage': token_analytics,
                'content_processing': content_analytics,
                'processing_decisions': decision_analytics,
                'analytics_period': '7 days'
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {'error': str(e)}
    
    def get_duplicate_detection_summary(self) -> Dict[str, Any]:
        """Get summary of duplicate detection performance"""
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_documents,
                            COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates_found,
                            COUNT(CASE WHEN has_products THEN 1 END) as documents_with_products,
                            AVG(extraction_confidence) as avg_confidence
                        FROM letters
                    """)
                    
                    summary = dict(cur.fetchone())
                    
                    # Calculate percentages
                    total = summary['total_documents']
                    if total > 0:
                        summary['duplicate_rate_percent'] = (summary['duplicates_found'] / total) * 100
                        summary['success_rate_percent'] = (summary['documents_with_products'] / total) * 100
                    else:
                        summary['duplicate_rate_percent'] = 0
                        summary['success_rate_percent'] = 0
                    
                    return summary
                    
        except Exception as e:
            logger.error(f"Error getting duplicate detection summary: {e}")
            return {'error': str(e)} 