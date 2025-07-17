"""Enhanced xAI Grok-3 API service with comprehensive token usage tracking and raw content management."""

import json
import time
import hashlib
import uuid
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# Import official xAI SDK
from xai_sdk import Client
from xai_sdk.chat import user, system

from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from ..models.letter import Letter, LetterMetadata
from ..utils.logger import get_logger
from ..models.document import Document
from ..core.postgresql_database import PostgreSQLDatabase

logger = get_logger(__name__)


class LLMCallTracker:
    """Helper class for tracking LLM API calls with comprehensive metrics"""
    
    def __init__(self, db: PostgreSQLDatabase, prompts_config: Dict[str, Any]):
        self.db = db
        self.prompts_config = prompts_config
        
    def generate_call_id(self) -> str:
        """Generate unique call ID"""
        return str(uuid.uuid4())
    
    def hash_text(self, text: str) -> str:
        """Generate SHA-256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def get_git_commit_hash(self) -> Optional[str]:
        """Get current git commit hash for reproducibility"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'], 
                capture_output=True, text=True, cwd=Path.cwd()
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def get_prompt_version(self) -> str:
        """Get prompt version from prompts.yaml"""
        return self.prompts_config.get('version', 'unknown')
    
    def get_config_hash(self) -> str:
        """Generate hash of entire prompts configuration"""
        config_str = json.dumps(self.prompts_config, sort_keys=True)
        return self.hash_text(config_str)
    
    def track_api_call(
        self,
        call_id: str,
        letter_id: Optional[int],
        operation_type: str,
        model_name: str,
        base_url: str,
        system_prompt: str,
        user_prompt: str,
        prompt_template_name: str,
        document_name: str,
        document_size: int,
        start_time: float,
        end_time: float,
        response_success: bool,
        usage_data: Optional[Dict[str, Any]] = None,
        confidence_score: Optional[float] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0
    ) -> int:
        """Track API call with comprehensive metrics"""
        
        try:
            response_time_ms = (end_time - start_time) * 1000
            
            # Extract token usage from xAI SDK response
            prompt_tokens = usage_data.get('prompt_tokens') if usage_data else None
            completion_tokens = usage_data.get('completion_tokens') if usage_data else None
            total_tokens = usage_data.get('total_tokens') if usage_data else None
            
            # Calculate estimated cost (placeholder - update with actual xAI pricing)
            estimated_cost_usd = None
            if total_tokens:
                # Example pricing - update with actual xAI rates
                cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens (example)
                estimated_cost_usd = (total_tokens / 1000) * cost_per_1k_tokens
            
            # Insert tracking record
            sql = """
                INSERT INTO llm_api_calls (
                    call_id, letter_id, operation_type, api_provider, model_name, base_url,
                    system_prompt_hash, user_prompt_hash, prompt_version, prompt_template_name,
                    prompt_tokens, completion_tokens, total_tokens,
                    response_time_ms, request_timestamp, response_timestamp,
                    response_success, confidence_score,
                    error_type, error_message, retry_count,
                    git_commit_hash, pipeline_version, config_hash,
                    estimated_cost_usd, document_name, document_size_bytes,
                    input_char_count, output_char_count
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            params = (
                call_id, letter_id, operation_type, 'xai', model_name, base_url,
                self.hash_text(system_prompt), self.hash_text(user_prompt),
                self.get_prompt_version(), prompt_template_name,
                prompt_tokens, completion_tokens, total_tokens,
                response_time_ms, datetime.fromtimestamp(start_time), datetime.fromtimestamp(end_time),
                response_success, confidence_score,
                error_type, error_message, retry_count,
                self.get_git_commit_hash(), "2.2.1", self.get_config_hash(),
                estimated_cost_usd, document_name, document_size,
                len(system_prompt + user_prompt), 0  # Will be updated with response length
            )
            
            result = self.db.execute_query(sql, params, commit=True)
            if result:
                return result[0]['id']
            else:
                logger.error("Failed to insert LLM API call tracking record")
                return None
                
        except Exception as e:
            logger.error(f"Error tracking API call: {e}")
            return None


class RawContentManager:
    """Helper class for managing raw letter content with duplicate detection"""
    
    def __init__(self, db: PostgreSQLDatabase, prompts_config: Dict[str, Any]):
        self.db = db
        self.prompts_config = prompts_config
        self.call_tracker = LLMCallTracker(db, prompts_config)
    
    def generate_content_signature(self, content_hash: str, prompt_config_hash: str) -> str:
        """Generate unique signature for content + prompt version combination"""
        combined = f"{content_hash}::{prompt_config_hash}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def check_duplicate_processing(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Check if content has already been processed with current prompt version"""
        prompt_version = self.call_tracker.get_prompt_version()
        prompt_config_hash = self.call_tracker.get_config_hash()
        signature = self.generate_content_signature(content_hash, prompt_config_hash)
        
        sql = """
            SELECT * FROM letter_raw_content 
            WHERE content_prompt_signature = %s 
              AND prompt_version = %s 
              AND llm_processed = TRUE
            ORDER BY created_at DESC LIMIT 1
        """
        
        result = self.db.execute_query(sql, (signature, prompt_version))
        return result[0] if result else None
    
    def store_raw_content(
        self,
        letter_id: int,
        raw_text: str,
        extraction_method: str,
        source_file_path: str,
        source_file_size: int,
        mime_type: str,
        grok_response_id: Optional[int] = None,
        grok_metadata: Optional[Dict[str, Any]] = None,
        grok_confidence: Optional[float] = None,
        products_extracted: int = 0
    ) -> int:
        """Store raw content with comprehensive metadata"""
        
        try:
            content_hash = self.call_tracker.hash_text(raw_text)
            prompt_version = self.call_tracker.get_prompt_version()
            prompt_config_hash = self.call_tracker.get_config_hash()
            signature = self.generate_content_signature(content_hash, prompt_config_hash)
            
            # Analyze content quality
            word_count = len(raw_text.split())
            paragraph_count = raw_text.count('\n\n') + 1
            has_technical_content = any(term in raw_text.lower() for term in 
                ['voltage', 'current', 'power', 'frequency', 'circuit', 'breaker'])
            has_tables = 'table' in raw_text.lower() or '\t' in raw_text
            
            sql = """
                INSERT INTO letter_raw_content (
                    content_hash, letter_id, raw_text, raw_text_length, encoding,
                    extraction_method, source_file_path, source_file_size, source_file_mime_type,
                    prompt_version, system_prompt_hash, prompt_config_hash, content_prompt_signature,
                    processing_status, llm_processed, last_processed_at, processing_attempts,
                    content_quality_score, has_technical_content, has_tables, 
                    word_count, paragraph_count, grok_response_id, grok_metadata,
                    grok_confidence, products_extracted
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """
            
            # Calculate content quality score (0.0 - 1.0)
            quality_score = min(1.0, (len(raw_text) / 10000) * 0.7 + (word_count / 2000) * 0.3)
            
            params = (
                content_hash, letter_id, raw_text, len(raw_text), 'utf-8',
                extraction_method, source_file_path, source_file_size, mime_type,
                prompt_version, self.call_tracker.hash_text("system_prompt"), prompt_config_hash, signature,
                'processed' if grok_metadata else 'pending', bool(grok_metadata), 
                datetime.now() if grok_metadata else None, 1 if grok_metadata else 0,
                quality_score, has_technical_content, has_tables,
                word_count, paragraph_count, grok_response_id, 
                json.dumps(grok_metadata) if grok_metadata else None,
                grok_confidence, products_extracted
            )
            
            result = self.db.execute_query(sql, params, commit=True)
            if result:
                logger.info(f"Stored raw content with ID: {result[0]['id']}")
                return result[0]['id']
            else:
                logger.error("Failed to store raw content")
                return None
                
        except Exception as e:
            logger.error(f"Error storing raw content: {e}")
            return None


class EnhancedXAIService:
    """Enhanced service for interacting with xAI Grok-3 API with comprehensive tracking."""

    def __init__(self, config: Config) -> None:
        """Initialize the enhanced xAI service.

        Args:
            config: Configuration instance.
        """
        self.config = config
        self.api_key = config.api.api_key
        self.base_url = config.api.base_url
        self.model = config.api.model
        self.timeout = config.api.timeout
        self.max_retries = getattr(config.api, "max_retries", 3)

        # Initialize database connection
        db_url = getattr(config.data.database, 'postgresql', 
                        'postgresql://ahuther@localhost:5432/se_letters')
        self.db = PostgreSQLDatabase(db_url)

        # Load prompts configuration
        self.prompts_config = self._load_prompts_config()
        
        # Initialize tracking services
        self.call_tracker = LLMCallTracker(self.db, self.prompts_config)
        self.content_manager = RawContentManager(self.db, self.prompts_config)

        # Debug console settings
        self.debug_enabled = getattr(config.api, "debug_enabled", False)
        self.debug_output_dir = Path("data/debug/xai")
        self.debug_output_dir.mkdir(parents=True, exist_ok=True)

        # Validate API key
        if not self.api_key:
            raise ValidationError("XAI API key is required")

        # Initialize xAI client using official SDK
        self.client = Client(api_host="api.x.ai", api_key=self.api_key)

        logger.info(f"Enhanced xAI client initialized with model: {self.model}")
        logger.info(f"Token usage tracking: ENABLED")
        logger.info(f"Raw content management: ENABLED")

    def _load_prompts_config(self) -> Dict[str, Any]:
        """Load prompts configuration from YAML file"""
        import yaml
        try:
            with open('config/prompts.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts config: {e}")
            return {'version': 'unknown'}

    def extract_comprehensive_metadata_with_tracking(
        self, 
        text: str, 
        document_name: str,
        letter_id: Optional[int] = None,
        extraction_method: str = "unknown",
        source_file_path: str = "",
        source_file_size: int = 0
    ) -> Dict[str, Any]:
        """
        Extract comprehensive metadata with full token usage tracking and raw content management.

        Args:
            text: Document text to analyze.
            document_name: Name of the document.
            letter_id: Optional letter ID for tracking.
            extraction_method: Method used to extract text (e.g., 'pdf_pymupdf', 'docx_python')
            source_file_path: Path to source file
            source_file_size: Size of source file in bytes

        Returns:
            Dictionary with comprehensive extracted metadata plus tracking information.
        """
        start_time = time.time()
        call_id = self.call_tracker.generate_call_id()

        try:
            logger.info(f"🔍 Starting enhanced extraction with tracking: {document_name}")
            logger.info(f"📊 Call ID: {call_id}")
            
            # Check for duplicate processing
            content_hash = self.call_tracker.hash_text(text)
            existing_content = self.content_manager.check_duplicate_processing(content_hash)
            
            if existing_content:
                logger.info(f"🔄 Found existing processed content with current prompt version")
                return {
                    "from_cache": True,
                    "cache_content_id": existing_content['id'],
                    **(existing_content['grok_metadata'] if existing_content['grok_metadata'] else {})
                }

            # Get prompts from configuration
            prompt_config = self.prompts_config['prompts']['unified_metadata_extraction']
            system_prompt = prompt_config['system_prompt']
            user_prompt_template = prompt_config['user_prompt_template']
            
            # Format user prompt
            user_prompt = user_prompt_template.format(
                document_name=document_name,
                document_content=text
            )

            logger.info(f"📝 Using prompt version: {self.call_tracker.get_prompt_version()}")
            logger.info(f"📝 Template: {prompt_config['name']}")

            # Make enhanced API call with tracking
            response_data = self._make_tracked_api_call(
                call_id=call_id,
                letter_id=letter_id,
                operation_type="metadata_extraction",
                prompt_template_name=prompt_config['name'],
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                document_name=document_name,
                document_size=len(text.encode('utf-8'))
            )

            processing_time = time.time() - start_time

            if not response_data['success']:
                logger.error(f"❌ API call failed: {response_data.get('error', 'Unknown error')}")
                return self._create_error_response(
                    response_data.get('error', 'API call failed'), 
                    processing_time, 
                    document_name
                )

            # Parse and validate response
            grok_result = response_data['parsed_response']
            
            # Extract confidence score
            confidence_score = self._extract_confidence_score(grok_result)
            
            # Store raw content with processing results
            raw_content_id = self.content_manager.store_raw_content(
                letter_id=letter_id or 0,  # Use 0 if no letter_id
                raw_text=text,
                extraction_method=extraction_method,
                source_file_path=source_file_path,
                source_file_size=source_file_size,
                mime_type="application/pdf",  # Default - could be detected
                grok_response_id=response_data['tracking_id'],
                grok_metadata=grok_result,
                grok_confidence=confidence_score,
                products_extracted=len(grok_result.get('product_information', []))
            )

            # Add tracking metadata to response
            grok_result.update({
                "tracking_metadata": {
                    "call_id": call_id,
                    "tracking_id": response_data['tracking_id'],
                    "raw_content_id": raw_content_id,
                    "prompt_version": self.call_tracker.get_prompt_version(),
                    "processing_time_ms": processing_time * 1000,
                    "token_usage": response_data.get('usage_data', {}),
                    "from_cache": False
                }
            })

            logger.info(f"✅ Enhanced extraction completed successfully")
            logger.info(f"📊 Token usage: {response_data.get('usage_data', {})}")
            logger.info(f"🎯 Confidence: {confidence_score:.2f}")

            return grok_result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Enhanced extraction failed: {e}")
            
            # Track failed API call
            self.call_tracker.track_api_call(
                call_id=call_id,
                letter_id=letter_id,
                operation_type="metadata_extraction",
                model_name=self.model,
                base_url=self.base_url,
                system_prompt="",
                user_prompt="",
                prompt_template_name="unified_metadata_extraction",
                document_name=document_name,
                document_size=len(text.encode('utf-8')),
                start_time=start_time,
                end_time=time.time(),
                response_success=False,
                error_type="extraction_error",
                error_message=str(e)
            )
            
            return self._create_error_response(str(e), processing_time, document_name)

    def _make_tracked_api_call(
        self,
        call_id: str,
        letter_id: Optional[int],
        operation_type: str,
        prompt_template_name: str,
        system_prompt: str,
        user_prompt: str,
        document_name: str,
        document_size: int
    ) -> Dict[str, Any]:
        """Make API call with comprehensive tracking"""
        
        for attempt in range(self.max_retries):
            request_start_time = time.time()
            
            try:
                logger.debug(f"🔄 Making tracked API call (attempt {attempt + 1}/{self.max_retries})")

                # Create chat using official SDK pattern
                chat = self.client.chat.create(
                    model=self.model, 
                    temperature=0.1
                )

                # Add system and user messages
                chat.append(system(system_prompt))
                chat.append(user(user_prompt))

                # Get response using official SDK pattern
                response = chat.sample()
                request_end_time = time.time()

                if not response or not response.content:
                    raise APIError("No content in API response")

                # Extract token usage from response
                usage_data = {}
                if hasattr(response, 'usage') and response.usage:
                    usage_data = {
                        'prompt_tokens': getattr(response.usage, 'prompt_tokens', None),
                        'completion_tokens': getattr(response.usage, 'completion_tokens', None),
                        'total_tokens': getattr(response.usage, 'total_tokens', None)
                    }
                    logger.info(f"📊 Token usage captured: {usage_data}")

                # Parse JSON response
                try:
                    parsed_content = json.loads(response.content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}")
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
                    if json_match:
                        try:
                            parsed_content = json.loads(json_match.group())
                        except json.JSONDecodeError:
                            raise APIError(f"Failed to parse JSON response: {e}")
                    else:
                        raise APIError(f"No valid JSON found in response: {e}")

                # Extract confidence score
                confidence_score = self._extract_confidence_score(parsed_content)

                # Track successful API call
                tracking_id = self.call_tracker.track_api_call(
                    call_id=call_id,
                    letter_id=letter_id,
                    operation_type=operation_type,
                    model_name=self.model,
                    base_url=self.base_url,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    prompt_template_name=prompt_template_name,
                    document_name=document_name,
                    document_size=document_size,
                    start_time=request_start_time,
                    end_time=request_end_time,
                    response_success=True,
                    usage_data=usage_data,
                    confidence_score=confidence_score,
                    retry_count=attempt
                )

                return {
                    'success': True,
                    'parsed_response': parsed_content,
                    'usage_data': usage_data,
                    'tracking_id': tracking_id,
                    'response_time_ms': (request_end_time - request_start_time) * 1000
                }

            except Exception as e:
                request_end_time = time.time()
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                
                # Track failed attempt
                if attempt == self.max_retries - 1:  # Last attempt
                    self.call_tracker.track_api_call(
                        call_id=call_id,
                        letter_id=letter_id,
                        operation_type=operation_type,
                        model_name=self.model,
                        base_url=self.base_url,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        prompt_template_name=prompt_template_name,
                        document_name=document_name,
                        document_size=document_size,
                        start_time=request_start_time,
                        end_time=request_end_time,
                        response_success=False,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        retry_count=attempt
                    )
                
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                
                return {
                    'success': False,
                    'error': str(e),
                    'tracking_id': None,
                    'response_time_ms': (request_end_time - request_start_time) * 1000
                }

        return {
            'success': False,
            'error': f"API call failed after {self.max_retries} attempts",
            'tracking_id': None,
            'response_time_ms': 0
        }

    def _extract_confidence_score(self, response: Dict[str, Any]) -> float:
        """Extract confidence score from response"""
        # Try different possible locations for confidence score
        if 'extraction_confidence' in response:
            return float(response['extraction_confidence'])
        elif 'confidence_score' in response:
            return float(response['confidence_score'])
        elif 'extraction_metadata' in response and 'confidence' in response['extraction_metadata']:
            return float(response['extraction_metadata']['confidence'])
        else:
            return 0.0

    def _create_error_response(
        self, error_msg: str, processing_time: float, document_name: str
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "document_information": {
                "document_type": "error",
                "document_title": document_name,
                "extraction_complexity": "error"
            },
            "product_information": [],
            "business_information": {
                "affected_ranges": [],
                "affected_countries": [],
                "customer_segments": [],
                "business_impact": None
            },
            "lifecycle_information": {
                "announcement_date": None,
                "effective_date": None,
                "lifecycle_stage": "error"
            },
            "contact_information": {
                "contact_details": None,
                "migration_guidance": None
            },
            "extraction_confidence": 0.0,
            "processing_timestamp": datetime.now().isoformat(),
            "source_file_path": document_name,
            "error": error_msg,
            "processing_time_ms": processing_time * 1000
        }

    # Legacy compatibility methods
    def extract_comprehensive_metadata(self, text: str, document_name: str) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        return self.extract_comprehensive_metadata_with_tracking(
            text=text,
            document_name=document_name,
            extraction_method="legacy"
        )

    def get_token_usage_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get token usage analytics for specified number of days"""
        sql = """
            SELECT 
                DATE(request_timestamp) as date,
                operation_type,
                COUNT(*) as total_calls,
                SUM(total_tokens) as total_tokens,
                AVG(total_tokens) as avg_tokens_per_call,
                SUM(estimated_cost_usd) as total_cost,
                AVG(confidence_score) as avg_confidence,
                COUNT(CASE WHEN response_success THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM llm_api_calls 
            WHERE request_timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(request_timestamp), operation_type
            ORDER BY date DESC, total_tokens DESC
        """
        
        result = self.db.execute_query(sql, (days,))
        return {"analytics": result, "period_days": days}

    def get_content_processing_summary(self) -> Dict[str, Any]:
        """Get summary of content processing status"""
        sql = """
            SELECT 
                prompt_version,
                COUNT(*) as total_content,
                COUNT(CASE WHEN llm_processed THEN 1 END) as processed_count,
                AVG(products_extracted) as avg_products,
                AVG(grok_confidence) as avg_confidence
            FROM letter_raw_content
            GROUP BY prompt_version
            ORDER BY prompt_version DESC
        """
        
        result = self.db.execute_query(sql)
        return {"content_summary": result} 