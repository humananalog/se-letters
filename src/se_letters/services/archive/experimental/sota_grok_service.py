"""
SOTA Grok Service - Direct Raw Document Processing with grok-3-mini
Enhanced service for processing raw documents directly with Grok-3-mini model using centralized prompts.
"""

import json
import time
import base64
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import requests
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, validator
import duckdb

from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Unified Schema Models aligned with grok_simplified_unified_schema.json
class TechnicalSpecifications(BaseModel):
    """Enhanced technical specifications from unified schema"""
    voltage_level: Optional[str] = Field(default=None, description="Voltage level (e.g., 12-17.5kV)")
    current_rating: Optional[str] = Field(default=None, description="Current rating (e.g., up to 3150A)")
    power_rating: Optional[str] = Field(default=None, description="Power rating")
    frequency: Optional[str] = Field(default=None, description="Frequency (e.g., 50/60Hz)")
    short_circuit_rating: Optional[str] = Field(default=None, description="Short circuit rating (e.g., 31.5kA 3s)")
    protection_class: Optional[str] = Field(default=None, description="Protection class (e.g., IP54)")
    insulation_level: Optional[str] = Field(default=None, description="Insulation level")
    operating_temperature: Optional[str] = Field(default=None, description="Operating temperature range")
    dimensions: Optional[str] = Field(default=None, description="Physical dimensions")
    weight: Optional[str] = Field(default=None, description="Weight specifications")

class CommercialInformation(BaseModel):
    """Commercial information from unified schema"""
    part_number: Optional[str] = Field(default=None, description="Part number")
    obsolescence_status: Optional[str] = Field(default=None, description="Obsolescence status")
    last_order_date: Optional[str] = Field(default=None, description="Last order date")
    end_of_service_date: Optional[str] = Field(default=None, description="End of service date")

class ReplacementInformation(BaseModel):
    """Replacement information from unified schema"""
    replacement_suggestions: List[str] = Field(default_factory=list, description="Replacement suggestions")
    migration_path: Optional[str] = Field(default=None, description="Migration path")

class ProductInformation(BaseModel):
    """Product information from unified schema"""
    product_identifier: str = Field(description="Product identifier")
    range_label: str = Field(description="Range label")
    subrange_label: Optional[str] = Field(default=None, description="Subrange label")
    product_line: str = Field(description="Product line (PSIBS/DPIBS/SPIBS/PPIBS)")
    product_description: str = Field(description="Product description")
    technical_specifications: TechnicalSpecifications = Field(default_factory=TechnicalSpecifications)
    commercial_information: CommercialInformation = Field(default_factory=CommercialInformation)
    replacement_information: ReplacementInformation = Field(default_factory=ReplacementInformation)

class DocumentInformation(BaseModel):
    """Enhanced document information from unified schema"""
    document_type: str = Field(default="", description="Document type (obsolescence_letter, withdrawal_notice, etc.)")
    communication_type: Optional[str] = Field(default=None, description="Internal or External communication")
    language: Optional[str] = Field(default=None, description="Language (English, French, etc.)")
    document_number: Optional[str] = Field(default=None, description="Document number or reference")
    document_title: Optional[str] = Field(default=None, description="Document title")
    total_products: Optional[int] = Field(default=None, description="Total products mentioned")
    has_tables: Optional[bool] = Field(default=None, description="Contains tables")
    has_technical_specs: Optional[bool] = Field(default=None, description="Contains technical specifications")
    has_images: Optional[bool] = Field(default=None, description="Contains images or diagrams")
    extraction_complexity: Optional[str] = Field(default=None, description="Extraction complexity (Low/Medium/High)")
    page_count: Optional[int] = Field(default=None, description="Number of pages")
    word_count: Optional[int] = Field(default=None, description="Approximate word count")

class BusinessInformation(BaseModel):
    """Business information from unified schema"""
    affected_ranges: List[str] = Field(default_factory=list, description="Affected ranges")
    affected_countries: List[str] = Field(default_factory=list, description="Affected countries")
    customer_segments: List[str] = Field(default_factory=list, description="Customer segments")
    business_impact: Optional[str] = Field(default=None, description="Business impact")

class KeyDates(BaseModel):
    """Enhanced key dates from unified schema with ISO format"""
    last_order_date: Optional[str] = Field(default=None, description="Last order date (ISO format: YYYY-MM-DD or YYYY)")
    end_of_service_date: Optional[str] = Field(default=None, description="End of service date (ISO format: YYYY-MM-DD or YYYY)")
    spare_parts_availability_date: Optional[str] = Field(default=None, description="Spare parts availability end date (ISO format)")
    spare_parts_availability_duration: Optional[str] = Field(default=None, description="Spare parts availability duration (e.g., '10 years')")
    commercialization_end_date: Optional[str] = Field(default=None, description="End of commercialization date (ISO format)")
    manufacturing_end_date: Optional[str] = Field(default=None, description="End of manufacturing date (ISO format)")
    repair_service_end_date: Optional[str] = Field(default=None, description="End of repair service date (ISO format)")

class LifecycleInformation(BaseModel):
    """Enhanced lifecycle information from unified schema with ISO dates"""
    announcement_date: Optional[str] = Field(default=None, description="Announcement date (ISO format: YYYY-MM-DD)")
    effective_date: Optional[str] = Field(default=None, description="Effective date (ISO format: YYYY-MM-DD)")
    publication_date: Optional[str] = Field(default=None, description="Document publication date (ISO format)")
    key_dates: KeyDates = Field(default_factory=KeyDates)
    lifecycle_stage: Optional[str] = Field(default=None, description="Current lifecycle stage (Active/Obsolete/Withdrawn/EOL)")
    transition_period: Optional[str] = Field(default=None, description="Transition period duration")

class ContactInformation(BaseModel):
    """Contact information from unified schema"""
    contact_details: Optional[str] = Field(default=None, description="Contact details")
    migration_guidance: Optional[str] = Field(default=None, description="Migration guidance")

class UnifiedMetadataSchema(BaseModel):
    """Unified metadata schema aligned with grok_simplified_unified_schema.json"""
    
    document_information: DocumentInformation = Field(default_factory=DocumentInformation)
    product_information: List[ProductInformation] = Field(default_factory=list)
    business_information: BusinessInformation = Field(default_factory=BusinessInformation)
    lifecycle_information: LifecycleInformation = Field(default_factory=LifecycleInformation)
    contact_information: ContactInformation = Field(default_factory=ContactInformation)
    
    # Processing metadata
    extraction_confidence: float = Field(default=0.0, description="Extraction confidence score")
    processing_timestamp: str = Field(default="", description="Processing timestamp")
    source_file_path: str = Field(default="", description="Source file path for traceability")

class SOTAGrokService:
    """SOTA Grok Service for direct raw document processing with grok-3-mini"""
    
    def __init__(self, config: Config) -> None:
        """Initialize the SOTA Grok service"""
        self.config = config
        self.api_key = config.api.api_key
        self.base_url = config.api.base_url
        self.model = "grok-3-latest"  # Use working model found by testing
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
        self.db_path = "data/document_metadata.duckdb"
        self._init_staging_tables()
        
        logger.info(f"SOTA Grok Service initialized with {self.model}")
    
    def _load_prompts_config(self) -> Dict[str, Any]:
        """Load prompts configuration from YAML file"""
        prompts_path = Path("config/prompts.yaml")
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompts_config = yaml.safe_load(f)
            
            logger.info(f"Loaded prompts configuration v{prompts_config.get('version', 'unknown')}")
            return prompts_config
            
        except FileNotFoundError:
            logger.error(f"Prompts configuration file not found: {prompts_path}")
            raise ValidationError(f"Prompts configuration file not found: {prompts_path}")
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in prompts configuration: {e}")
            raise ValidationError(f"Invalid YAML in prompts configuration: {e}")
    
    def _init_staging_tables(self) -> None:
        """Initialize staging tables for document metadata"""
        try:
            with duckdb.connect(self.db_path) as conn:
                # Create staging table for raw JSON outputs
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS document_staging (
                        source_file_path TEXT NOT NULL,
                        document_name TEXT NOT NULL,
                        raw_json TEXT NOT NULL,
                        metadata_extracted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processing_confidence REAL DEFAULT 0.0,
                        model_used TEXT DEFAULT 'grok-3-latest'
                    )
                """)
                
                # Add prompt_version column if it doesn't exist (migration)
                try:
                    conn.execute("""
                        ALTER TABLE document_staging 
                        ADD COLUMN prompt_version TEXT DEFAULT '2.0.0'
                    """)
                except Exception:
                    # Column already exists, ignore
                    pass
                
                # Create index for faster lookups
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_staging_source_path 
                    ON document_staging(source_file_path)
                """)
                
                logger.info("Staging tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize staging tables: {e}")
    
    def process_raw_document(self, file_path: Path, document_content: str = None) -> Dict[str, Any]:
        """Process raw document directly with grok-3-mini using centralized prompts
        
        Args:
            file_path: Path to the document file
            document_content: Optional pre-extracted content (if None, will read file)
            
        Returns:
            Dictionary containing extracted metadata aligned with unified schema
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing raw document with {self.model}: {file_path}")
            
            # Read document content if not provided
            if document_content is None:
                document_content = self._read_raw_document(file_path)
            
            # Extract metadata using grok-3-mini with centralized prompts
            metadata = self._extract_metadata_with_grok(document_content, file_path)
            
            # Add source file path for traceability
            metadata['source_file_path'] = str(file_path.absolute())
            
            # Store in staging table
            self._store_in_staging(file_path, metadata)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            metadata['processing_time_ms'] = processing_time
            
            logger.info(f"Document processed successfully in {processing_time:.2f}ms")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {e}")
            return self._create_error_response(str(e), file_path)
    
    def _read_raw_document(self, file_path: Path) -> str:
        """Read raw document content without OCR processing
        
        Args:
            file_path: Path to the document
            
        Returns:
            Raw document content as string
        """
        try:
            if file_path.suffix.lower() == '.pdf':
                # For PDF, read as binary and encode as base64 for Grok
                with open(file_path, 'rb') as f:
                    pdf_content = f.read()
                    return base64.b64encode(pdf_content).decode('utf-8')
            
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                # For Word documents, try to read as binary first
                with open(file_path, 'rb') as f:
                    doc_content = f.read()
                    return base64.b64encode(doc_content).decode('utf-8')
            
            elif file_path.suffix.lower() == '.txt':
                # For text files, read directly
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            else:
                # For other formats, try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Failed to read raw document {file_path}: {e}")
            raise
    
    def _extract_metadata_with_grok(self, document_content: str, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using grok-3-mini model with centralized prompts
        
        Args:
            document_content: Raw document content
            file_path: Path to the document
            
        Returns:
            Extracted metadata dictionary aligned with unified schema
        """
        try:
            # Get primary extraction prompt from config
            prompt_config = self.prompts_config['prompts']['unified_metadata_extraction']
            
            # Build prompt using template
            system_prompt = prompt_config['system_prompt']
            user_prompt = prompt_config['user_prompt_template'].format(
                document_name=file_path.name,
                document_content=document_content[:self.prompts_config['processing']['max_content_length']]
            )
            
            # Make API call to grok-3-mini
            response = self._make_api_call(system_prompt, user_prompt)
            
            # Validate and structure response
            metadata = self._validate_and_structure_response(response, file_path)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata with Grok: {e}")
            raise
    
    def _make_api_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Make API call to grok-3-mini model"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ],
            "max_tokens": self.prompts_config['processing']['max_tokens'],
            "temperature": self.prompts_config['processing']['temperature'],
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.prompts_config['processing']['timeout_seconds']
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise APIError("No choices in API response")
            
            content = result['choices'][0]['message']['content']
            
            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {content}")
                raise APIError(f"Invalid JSON response: {e}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"API request failed: {e}")
    
    def _validate_and_structure_response(self, response: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Validate and structure the API response according to unified schema"""
        
        try:
            # Add processing metadata
            response['processing_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            response['source_file_path'] = str(file_path.absolute())
            
            # Calculate confidence score
            if 'extraction_confidence' not in response:
                response['extraction_confidence'] = self._calculate_confidence(response)
            
            # Validate against unified schema
            try:
                metadata = UnifiedMetadataSchema(**response)
                return response  # Return raw response if validation passes
            except Exception as validation_error:
                logger.warning(f"Schema validation failed: {validation_error}")
                # Return response with validation warning but don't fail
                response['schema_validation_warning'] = str(validation_error)
                return response
            
        except Exception as e:
            logger.error(f"Failed to validate response: {e}")
            # Return error response using template
            return self._create_error_response(str(e), file_path)
    
    def _calculate_confidence(self, response: Dict[str, Any]) -> float:
        """Calculate confidence score based on response completeness using rules from prompts config"""
        
        confidence_rules = self.prompts_config.get('confidence_scoring', {})
        
        # Count populated fields
        total_fields = 0
        populated_fields = 0
        
        def count_fields(obj, path=""):
            nonlocal total_fields, populated_fields
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, (dict, list)):
                        count_fields(value, f"{path}.{key}")
                    else:
                        total_fields += 1
                        if value and str(value).strip():
                            populated_fields += 1
            elif isinstance(obj, list):
                total_fields += 1
                if obj:
                    populated_fields += 1
        
        count_fields(response)
        
        if total_fields == 0:
            return 0.0
        
        base_confidence = min(populated_fields / total_fields, 1.0)
        
        # Apply confidence rules
        if base_confidence >= confidence_rules.get('high_confidence', {}).get('threshold', 0.8):
            return min(base_confidence * 1.1, 1.0)  # Boost high confidence
        elif base_confidence >= confidence_rules.get('medium_confidence', {}).get('threshold', 0.5):
            return base_confidence
        else:
            return max(base_confidence * 0.9, 0.1)  # Reduce low confidence
    
    def _store_in_staging(self, file_path: Path, metadata: Dict[str, Any]) -> None:
        """Store extracted metadata in staging table"""
        
        try:
            with duckdb.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO document_staging 
                    (source_file_path, document_name, raw_json, processing_confidence, model_used, prompt_version)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    str(file_path.absolute()),
                    file_path.name,
                    json.dumps(metadata, indent=2),
                    metadata.get('extraction_confidence', 0.0),
                    self.model,
                    self.prompts_config.get('version', '2.0.0')
                ])
                
                logger.info(f"Metadata stored in staging for {file_path.name}")
                
        except Exception as e:
            logger.error(f"Failed to store metadata in staging: {e}")
    
    def _create_error_response(self, error_msg: str, file_path: Path) -> Dict[str, Any]:
        """Create error response structure using template from prompts config"""
        
        error_template = self.prompts_config.get('error_templates', {}).get('api_error', {}).get('template', '')
        
        if error_template:
            try:
                # Use template from config
                error_json = error_template.format(
                    document_name=file_path.name,
                    file_path=str(file_path.absolute()),
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    error_message=error_msg
                )
                return json.loads(error_json)
            except Exception as template_error:
                logger.error(f"Failed to use error template: {template_error}")
        
        # Fallback error response
        return {
            'document_type': 'error',
            'document_title': file_path.name,
            'source_file_path': str(file_path.absolute()),
            'processing_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'extraction_confidence': 0.0,
            'error': error_msg,
            'processing_time_ms': 0.0
        }
    
    def get_staging_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get records from staging table"""
        
        try:
            with duckdb.connect(self.db_path) as conn:
                result = conn.execute("""
                    SELECT * FROM document_staging 
                    ORDER BY metadata_extracted DESC 
                    LIMIT ?
                """, [limit]).fetchall()
                
                columns = [desc[0] for desc in conn.description]
                return [dict(zip(columns, row)) for row in result]
                
        except Exception as e:
            logger.error(f"Failed to get staging records: {e}")
            return []
    
    def get_prompts_info(self) -> Dict[str, Any]:
        """Get information about loaded prompts configuration"""
        return {
            'version': self.prompts_config.get('version', 'unknown'),
            'last_updated': self.prompts_config.get('last_updated', 'unknown'),
            'schema_version': self.prompts_config.get('schema', {}).get('version', 'unknown'),
            'available_prompts': list(self.prompts_config.get('prompts', {}).keys()),
            'model': self.model
        }
    
    def close(self) -> None:
        """Close service connections"""
        if hasattr(self, 'session'):
            self.session.close()
        logger.info("SOTA Grok Service closed") 