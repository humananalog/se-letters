#!/usr/bin/env python3
"""
Raw File Grok Service - Direct Document Processing without OCR preprocessing
Processes raw documents directly with Grok API for enhanced product identification.

This service bypasses OCR as the first step and sends raw files directly to Grok,
keeping OCR as fallback/supplementary information source.

Key Features:
- Direct raw file processing with Grok (PDF, DOC, DOCX)
- Base64 encoding for file transmission
- Comprehensive logging and debugging
- DuckDB staging tables for processing results
- OCR service integration as fallback
- Enhanced error handling and validation

Database Fixes:
- Fixed last_insert_rowid() -> lastval() for DuckDB compatibility
- Fixed auto-increment primary key constraints
- Fixed sequence usage and table creation

Version: 2.2.1
Author: SE Letters Development Team
"""

import json
import time
import base64
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import requests
import duckdb

from ..core.config import Config
from ..core.exceptions import ValidationError, ProcessingError

# Set up logging
logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")
performance_logger = logging.getLogger(f"{__name__}.performance")

class RawFileGrokService:
    """Raw File Grok Service for direct document processing without OCR preprocessing"""
    
    def __init__(self, config: Config) -> None:
        """Initialize the Raw File Grok service"""
        self.config = config
        self.api_key = config.api.api_key
        self.base_url = config.api.base_url
        self.model = "grok-3-latest"  # Use working model
        self.timeout = config.api.timeout
        self.max_retries = getattr(config.api, 'max_retries', 3)
        
        # Load prompts from YAML file
        self.prompts_config = self._load_prompts_config()
        
        # Validate API key
        if not self.api_key:
            raise ValidationError("XAI API key is required")
        
        # Set up session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        
        # Initialize DuckDB connection for staging
        self.db_path = "data/raw_document_processing.duckdb"
        self._init_staging_tables()
        
        # Initialize OCR service for fallback
        self.ocr_service = None
        try:
            from .document_processor import DocumentProcessor
            self.ocr_service = DocumentProcessor(config)
            logger.info("OCR service initialized for fallback/supplementary processing")
        except ImportError:
            logger.warning("OCR service not available - raw processing only")
        
        logger.info(f"Raw File Grok Service initialized with {self.model}")
        debug_logger.info(f"Service initialized with config: {self.config}")
    
    def _load_prompts_config(self) -> Dict[str, Any]:
        """Load prompts configuration from YAML file"""
        import yaml
        
        try:
            prompts_path = Path("config/prompts.yaml")
            if not prompts_path.exists():
                raise FileNotFoundError(f"Prompts configuration not found: {prompts_path}")
            
            with open(prompts_path, 'r') as f:
                prompts_config = yaml.safe_load(f)
            
            logger.info("Prompts configuration loaded successfully")
            debug_logger.debug(f"Loaded prompts config: {prompts_config.keys()}")
            
            return prompts_config
            
        except Exception as e:
            logger.error(f"Failed to load prompts configuration: {e}")
            raise ProcessingError(f"Prompts configuration error: {e}")
    
    def _init_staging_tables(self) -> None:
        """Initialize staging tables for raw document processing"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Create sequences for auto-increment (DuckDB compatible)
                conn.execute("CREATE SEQUENCE IF NOT EXISTS raw_staging_id_seq START 1")
                conn.execute("CREATE SEQUENCE IF NOT EXISTS raw_debug_id_seq START 1")
                
                # Create staging table for raw processing results
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS raw_processing_staging (
                        id INTEGER PRIMARY KEY DEFAULT nextval('raw_staging_id_seq'),
                        source_file_path TEXT NOT NULL,
                        document_name TEXT NOT NULL,
                        file_size INTEGER,
                        file_type TEXT,
                        processing_method TEXT,
                        raw_grok_json TEXT NOT NULL,
                        ocr_text TEXT,
                        processing_confidence REAL DEFAULT 0.0,
                        processing_time_ms REAL,
                        model_used TEXT DEFAULT 'grok-3-latest',
                        prompt_version TEXT DEFAULT '2.0.0',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT
                    )
                """)
                
                # Create index for faster lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_raw_staging_source_path 
                    ON raw_processing_staging(source_file_path)
                """)
                
                # Create debug table for detailed logging
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS raw_processing_debug (
                        id INTEGER PRIMARY KEY DEFAULT nextval('raw_debug_id_seq'),
                        source_file_path TEXT NOT NULL,
                        processing_step TEXT NOT NULL,
                        step_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        step_data TEXT,
                        step_duration_ms REAL,
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT
                    )
                """)
                
                logger.info("Raw processing staging tables initialized successfully")
                debug_logger.debug("Database tables created/verified")
                
        except Exception as e:
            logger.error(f"Failed to initialize staging tables: {e}")
            debug_logger.error(f"Database initialization error: {e}")
            raise
    
    def process_raw_document(self, file_path: Path, include_ocr_fallback: bool = True) -> Dict[str, Any]:
        """Process raw document directly with Grok without OCR preprocessing
        
        Args:
            file_path: Path to the document file
            include_ocr_fallback: Whether to include OCR as supplementary information
            
        Returns:
            Dictionary containing extracted metadata and processing details
        """
        start_time = time.time()
        processing_steps = []
        
        try:
            logger.info(f"🔄 Processing raw document: {file_path.name}")
            debug_logger.debug(f"Starting raw document processing: {file_path}")
            
            # Step 1: Prepare raw document for Grok
            step_start = time.time()
            raw_content = self._prepare_raw_document_for_grok(file_path)
            step_duration = (time.time() - step_start) * 1000
            processing_steps.append({
                "step": "raw_document_preparation",
                "duration_ms": step_duration,
                "success": True,
                "details": f"Prepared {len(raw_content)} bytes for Grok processing"
            })
            
            # Step 2: Process with Grok directly
            step_start = time.time()
            grok_metadata = self._process_with_grok_direct(raw_content, file_path)
            step_duration = (time.time() - step_start) * 1000
            processing_steps.append({
                "step": "grok_direct_processing",
                "duration_ms": step_duration,
                "success": True,
                "details": f"Grok processing completed with confidence {grok_metadata.get('extraction_confidence', 0.0)}"
            })
            
            # Step 3: OCR supplementary processing (if enabled)
            ocr_text = None
            if include_ocr_fallback and self.ocr_service:
                step_start = time.time()
                try:
                    ocr_result = self.ocr_service.process_document(file_path)
                    ocr_text = ocr_result.get('extracted_text', '')
                    step_duration = (time.time() - step_start) * 1000
                    processing_steps.append({
                        "step": "ocr_supplementary_processing",
                        "duration_ms": step_duration,
                        "success": True,
                        "details": f"OCR extracted {len(ocr_text)} characters as supplementary info"
                    })
                except Exception as e:
                    step_duration = (time.time() - step_start) * 1000
                    processing_steps.append({
                        "step": "ocr_supplementary_processing",
                        "duration_ms": step_duration,
                        "success": False,
                        "error_message": str(e),
                        "details": "OCR supplementary processing failed"
                    })
                    logger.warning(f"OCR supplementary processing failed: {e}")
            
            # Step 4: Enhance metadata with processing details
            step_start = time.time()
            enhanced_metadata = self._enhance_metadata_with_processing_details(
                grok_metadata, file_path, processing_steps, ocr_text
            )
            step_duration = (time.time() - step_start) * 1000
            processing_steps.append({
                "step": "metadata_enhancement",
                "duration_ms": step_duration,
                "success": True,
                "details": "Added processing details and OCR supplementary info"
            })
            
            # Step 5: Store in staging database
            step_start = time.time()
            self._store_in_staging(file_path, enhanced_metadata, processing_steps, ocr_text)
            step_duration = (time.time() - step_start) * 1000
            processing_steps.append({
                "step": "database_storage",
                "duration_ms": step_duration,
                "success": True,
                "details": "Stored in staging database"
            })
            
            # Calculate total processing time
            total_processing_time = (time.time() - start_time) * 1000
            enhanced_metadata['processing_time_ms'] = total_processing_time
            enhanced_metadata['processing_steps'] = processing_steps
            
            logger.info(f"✅ Raw document processed successfully in {total_processing_time:.2f}ms")
            debug_logger.info(f"Complete processing result: {enhanced_metadata}")
            
            return enhanced_metadata
            
        except Exception as e:
            # Calculate processing time for error
            error_processing_time = (time.time() - start_time) * 1000
            
            # Add error step
            processing_steps.append({
                "step": "error_handling",
                "duration_ms": 0,
                "success": False,
                "error_message": str(e),
                "details": f"Processing failed: {e}"
            })
            
            # Store error in staging
            self._store_error_in_staging(file_path, str(e), processing_steps, error_processing_time)
            
            logger.error(f"❌ Raw document processing failed: {e}")
            debug_logger.error(f"Processing error details: {e}", exc_info=True)
            
            return self._create_error_response(str(e), file_path, error_processing_time)
    
    def _prepare_raw_document_for_grok(self, file_path: Path) -> str:
        """Prepare raw document for Grok processing by encoding to base64"""
        try:
            logger.info(f"📄 Preparing raw document for Grok: {file_path.name}")
            
            # Read file as binary
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Encode to base64
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            debug_logger.debug(f"Document encoded to base64: {len(base64_content)} characters")
            
            return base64_content
            
        except Exception as e:
            logger.error(f"Failed to prepare document for Grok: {e}")
            raise ProcessingError(f"Document preparation failed: {e}")
    
    def _process_with_grok_direct(self, raw_content: str, file_path: Path) -> Dict[str, Any]:
        """Process raw document content directly with Grok API"""
        try:
            logger.info(f"🤖 Processing with Grok: {file_path.name}")
            
            # Get prompts from configuration
            system_prompt = self.prompts_config['prompts']['unified_metadata_extraction']['system_prompt']
            user_prompt_template = self.prompts_config['prompts']['unified_metadata_extraction']['user_prompt_template']
            
            # Format user prompt with document info
            user_prompt = user_prompt_template.format(
                document_name=file_path.name,
                file_type=file_path.suffix.lower(),
                raw_content=raw_content[:50000]  # Limit content size for API
            )
            
            # Make API call to Grok
            response = self._make_grok_api_call(system_prompt, user_prompt)
            
            # Validate and structure response
            structured_response = self._validate_and_structure_response(response, file_path)
            
            # Calculate confidence
            confidence = self._calculate_confidence(structured_response)
            structured_response['extraction_confidence'] = confidence
            
            logger.info(f"✅ Grok processing completed with confidence: {confidence:.2f}")
            debug_logger.debug(f"Grok response: {structured_response}")
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Grok processing failed: {e}")
            raise ProcessingError(f"Grok processing error: {e}")
    
    def _make_grok_api_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Make API call to Grok with retry logic"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4000,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making Grok API call (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                response_data = response.json()
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0]['message']['content']
                    
                    # Try to parse as JSON
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        # If not JSON, wrap in error structure
                        return {"error": "Invalid JSON response", "raw_content": content}
                else:
                    raise ProcessingError("No choices in API response")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise ProcessingError(f"API call failed after {self.max_retries} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise ProcessingError("API call failed after all retries")
    
    def _validate_and_structure_response(self, response: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Validate and structure the Grok response"""
        
        if 'error' in response:
            logger.warning(f"Grok returned error: {response['error']}")
            return self._create_error_response(response['error'], file_path, 0)
        
        # Ensure required structure exists
        structured_response = {
            "document_information": response.get("document_information", {}),
            "product_information": response.get("product_information", []),
            "commercial_information": response.get("commercial_information", {}),
            "replacement_information": response.get("replacement_information", {}),
            "business_context": response.get("business_context", {}),
            "technical_specifications": response.get("technical_specifications", {}),
            "processing_metadata": {
                "source_file_path": str(file_path.absolute()),
                "document_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "file_type": file_path.suffix.lower(),
                "processing_method": "raw_file_direct_grok",
                "model_used": self.model,
                "prompt_version": self.prompts_config.get('version', '2.0.0')
            }
        }
        
        return structured_response
    
    def _calculate_confidence(self, response: Dict[str, Any]) -> float:
        """Calculate extraction confidence based on response completeness"""
        
        confidence_factors = []
        
        # Document information completeness
        doc_info = response.get("document_information", {})
        if doc_info.get("document_type"):
            confidence_factors.append(0.2)
        if doc_info.get("document_title"):
            confidence_factors.append(0.1)
        if doc_info.get("document_date"):
            confidence_factors.append(0.1)
        
        # Product information completeness
        product_info = response.get("product_information", [])
        if product_info:
            confidence_factors.append(0.3)
            for product in product_info:
                if product.get("product_identifier"):
                    confidence_factors.append(0.1)
                if product.get("range_label"):
                    confidence_factors.append(0.1)
                if product.get("product_line"):
                    confidence_factors.append(0.1)
        
        # Commercial information completeness
        commercial_info = response.get("commercial_information", {})
        if commercial_info.get("obsolescence_status"):
            confidence_factors.append(0.1)
        if commercial_info.get("end_of_service_date"):
            confidence_factors.append(0.1)
        
        # Calculate final confidence
        confidence = min(sum(confidence_factors), 1.0)
        
        return confidence
    
    def _enhance_metadata_with_processing_details(
        self, 
        grok_metadata: Dict[str, Any], 
        file_path: Path, 
        processing_steps: List[Dict[str, Any]], 
        ocr_text: Optional[str]
    ) -> Dict[str, Any]:
        """Enhance metadata with processing details and OCR supplementary info"""
        
        enhanced_metadata = grok_metadata.copy()
        
        # Add processing details
        enhanced_metadata['processing_metadata']['processing_steps'] = processing_steps
        enhanced_metadata['processing_metadata']['total_steps'] = len(processing_steps)
        enhanced_metadata['processing_metadata']['successful_steps'] = len([s for s in processing_steps if s['success']])
        
        # Add OCR supplementary information
        if ocr_text:
            enhanced_metadata['ocr_supplementary'] = {
                "extracted_text": ocr_text,
                "text_length": len(ocr_text),
                "purpose": "supplementary_information"
            }
        
        debug_logger.debug(f"Enhanced metadata with processing details")
        
        return enhanced_metadata
    
    def _store_in_staging(
        self, 
        file_path: Path, 
        metadata: Dict[str, Any], 
        processing_steps: List[Dict[str, Any]], 
        ocr_text: Optional[str]
    ) -> None:
        """Store processed metadata in staging database"""
        
        try:
            with duckdb.connect(self.db_path) as conn:
                # Store main result
                conn.execute("""
                    INSERT INTO raw_processing_staging 
                    (source_file_path, document_name, file_size, file_type, processing_method,
                     raw_grok_json, ocr_text, processing_confidence, processing_time_ms, 
                     model_used, prompt_version, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    str(file_path.absolute()),
                    file_path.name,
                    file_path.stat().st_size,
                    file_path.suffix.lower(),
                    'raw_file_direct_grok',
                    json.dumps(metadata, indent=2),
                    ocr_text,
                    metadata.get('extraction_confidence', 0.0),
                    metadata.get('processing_time_ms', 0.0),
                    self.model,
                    self.prompts_config.get('version', '2.0.0'),
                    True
                ])
                
                # Store processing steps for debugging
                for step in processing_steps:
                    conn.execute("""
                        INSERT INTO raw_processing_debug 
                        (source_file_path, processing_step, step_data, 
                         step_duration_ms, success, error_message)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, [
                        str(file_path.absolute()),
                        step['step'],
                        json.dumps(step, indent=2),
                        step['duration_ms'],
                        step['success'],
                        step.get('error_message')
                    ])
                
                debug_logger.debug(f"Stored processing results in staging database")
                
        except Exception as e:
            debug_logger.error(f"Failed to store in staging database: {e}")
            raise
    
    def _store_error_in_staging(
        self, 
        file_path: Path, 
        error_msg: str, 
        processing_steps: List[Dict[str, Any]], 
        processing_time_ms: float
    ) -> None:
        """Store error information in staging database"""
        
        try:
            with duckdb.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO raw_processing_staging 
                    (source_file_path, document_name, file_size, file_type, processing_method,
                     raw_grok_json, processing_time_ms, model_used, prompt_version, 
                     success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    str(file_path.absolute()),
                    file_path.name,
                    file_path.stat().st_size if file_path.exists() else 0,
                    file_path.suffix.lower(),
                    'raw_file_direct_grok',
                    json.dumps({"error": error_msg}, indent=2),
                    processing_time_ms,
                    self.model,
                    self.prompts_config.get('version', '2.0.0'),
                    False,
                    error_msg
                ])
                
        except Exception as e:
            debug_logger.error(f"Failed to store error in staging: {e}")
    
    def _create_error_response(self, error_msg: str, file_path: Path, processing_time_ms: float) -> Dict[str, Any]:
        """Create error response using template"""
        
        error_template = self.prompts_config['error_templates']['api_error']['template']
        
        return {
            "document_type": "error",
            "document_title": file_path.name,
            "source_file_path": str(file_path.absolute()),
            "error": error_msg,
            "processing_time_ms": processing_time_ms,
            "extraction_confidence": 0.0,
            "processing_method": "raw_file_direct_grok",
            "model_used": self.model,
            "prompt_version": self.prompts_config.get('version', '2.0.0'),
            "document_information": {
                "document_type": "error",
                "document_title": file_path.name,
                "language": "unknown",
                "document_date": "unknown"
            },
            "product_information": [],
            "commercial_information": {},
            "replacement_information": {},
            "business_context": {},
            "technical_specifications": {}
        }
    
    def close(self) -> None:
        """Close service and cleanup resources"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            
            if hasattr(self, 'ocr_service') and self.ocr_service:
                self.ocr_service.close()
                
            logger.info("Raw File Grok Service closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing Raw File Grok Service: {e}") 