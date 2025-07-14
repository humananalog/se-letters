"""xAI Grok-3 API service for the SE Letters project."""

import json
import time
from typing import Dict, Any, List
from pathlib import Path

# Import official xAI SDK
from xai_sdk import Client
from xai_sdk.chat import user, system

from ..core.config import Config
from ..core.exceptions import APIError, ValidationError
from ..models.letter import Letter, LetterMetadata
from ..utils.logger import get_logger

logger = get_logger(__name__)


class XAIService:
    """Enhanced service for interacting with xAI Grok-3 API using official SDK."""

    def __init__(self, config: Config) -> None:
        """Initialize the xAI service.

        Args:
            config: Configuration instance.
        """
        self.config = config
        self.api_key = config.api.api_key
        self.base_url = config.api.base_url
        self.model = config.api.model
        self.timeout = config.api.timeout
        self.max_retries = getattr(config.api, "max_retries", 3)

        # Debug console settings
        self.debug_enabled = getattr(config.api, "debug_enabled", False)
        self.debug_output_dir = Path("data/debug/xai")
        self.debug_output_dir.mkdir(parents=True, exist_ok=True)

        # Validate API key
        if not self.api_key:
            raise ValidationError("XAI API key is required")

        # Initialize xAI client using official SDK
        self.client = Client(api_host="api.x.ai", api_key=self.api_key)

        logger.info(f"xAI client initialized with model: {self.model}")

        # Initialize structured JSON schema
        self.json_schema = self._build_structured_schema()

    def _build_structured_schema(self) -> Dict[str, Any]:
        """Build the structured JSON schema for comprehensive metadata extraction."""
        return {
            "type": "object",
            "properties": {
                "product_identification": {
                    "type": "object",
                    "properties": {
                        "ranges": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Product ranges/families mentioned (e.g., TeSys, PIX, Galaxy)",
                        },
                        "product_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific product codes/part numbers",
                        },
                        "product_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Product types/categories",
                        },
                        "descriptions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Product descriptions as stated",
                        },
                    },
                    "required": [
                        "ranges",
                        "product_codes",
                        "product_types",
                        "descriptions",
                    ],
                },
                "brand_business": {
                    "type": "object",
                    "properties": {
                        "brands": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Brand names mentioned",
                        },
                        "business_units": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Business units/divisions",
                        },
                        "geographic_regions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Geographic regions/markets",
                        },
                    },
                    "required": ["brands", "business_units", "geographic_regions"],
                },
                "commercial_lifecycle": {
                    "type": "object",
                    "properties": {
                        "commercial_status": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Commercial status information",
                        },
                        "dates": {
                            "type": "object",
                            "properties": {
                                "production_end": {"type": ["string", "null"]},
                                "commercialization_end": {"type": ["string", "null"]},
                                "service_end": {"type": ["string", "null"]},
                                "announcement_date": {"type": ["string", "null"]},
                                "other_dates": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                },
                            },
                        },
                        "timeline_info": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Timeline and schedule information",
                        },
                    },
                    "required": ["commercial_status", "dates", "timeline_info"],
                },
                "technical_specs": {
                    "type": "object",
                    "properties": {
                        "voltage_levels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Voltage levels mentioned",
                        },
                        "specifications": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Technical specifications",
                        },
                        "device_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Device types/categories",
                        },
                        "applications": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Applications/use cases",
                        },
                    },
                    "required": [
                        "voltage_levels",
                        "specifications",
                        "device_types",
                        "applications",
                    ],
                },
                "service_support": {
                    "type": "object",
                    "properties": {
                        "service_availability": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Service availability information",
                        },
                        "warranty_info": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Warranty/maintenance details",
                        },
                        "replacement_guidance": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Replacement/migration guidance",
                        },
                        "spare_parts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Spare parts information",
                        },
                    },
                    "required": [
                        "service_availability",
                        "warranty_info",
                        "replacement_guidance",
                        "spare_parts",
                    ],
                },
                "regulatory_compliance": {
                    "type": "object",
                    "properties": {
                        "standards": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Standards and certifications",
                        },
                        "compliance_info": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Compliance requirements",
                        },
                        "safety_info": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Safety information",
                        },
                    },
                    "required": ["standards", "compliance_info", "safety_info"],
                },
                "business_context": {
                    "type": "object",
                    "properties": {
                        "customer_impact": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Customer impact information",
                        },
                        "migration_recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Migration/replacement recommendations",
                        },
                        "contact_info": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Contact information",
                        },
                        "business_reasons": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Business reasons for changes",
                        },
                    },
                    "required": [
                        "customer_impact",
                        "migration_recommendations",
                        "contact_info",
                        "business_reasons",
                    ],
                },
                "extraction_metadata": {
                    "type": "object",
                    "properties": {
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Confidence score (0-1)",
                        },
                        "analysis_quality": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Quality of text analysis",
                        },
                        "text_length": {
                            "type": "integer",
                            "description": "Length of analyzed text",
                        },
                        "extraction_method": {
                            "type": "string",
                            "description": "Method used for extraction",
                        },
                        "limitations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Limitations or caveats",
                        },
                    },
                    "required": [
                        "confidence",
                        "analysis_quality",
                        "text_length",
                        "extraction_method",
                        "limitations",
                    ],
                },
            },
            "required": [
                "product_identification",
                "brand_business",
                "commercial_lifecycle",
                "technical_specs",
                "service_support",
                "regulatory_compliance",
                "business_context",
                "extraction_metadata",
            ],
        }

    def extract_ranges_from_text(self, text: str, document_name: str) -> Letter:
        """Extract product ranges from document text using Grok-3.

        Args:
            text: Document text to analyze.
            document_name: Name of the document.

        Returns:
            Letter object with extracted ranges and metadata.
        """
        start_time = time.time()

        try:
            logger.info(f"Extracting ranges from document: {document_name}")

            # Use comprehensive extraction
            comprehensive_metadata = self.extract_comprehensive_metadata(
                text, document_name
            )

            # Extract ranges from comprehensive metadata
            ranges = comprehensive_metadata.get("product_identification", {}).get(
                "ranges", []
            )

            processing_time = time.time() - start_time

            # Create Letter object
            letter = Letter(
                letter_id=document_name,
                ranges=ranges,
                metadata=LetterMetadata(
                    confidence_score=comprehensive_metadata.get(
                        "extraction_metadata", {}
                    ).get("confidence", 0.0),
                    processing_time=processing_time,
                    api_model=self.model,
                    extraction_method="xai_grok3_enhanced",
                    **comprehensive_metadata.get("extraction_metadata", {}),
                ),
            )

            # Debug console output
            if self.debug_enabled:
                self._write_debug_output(
                    document_name, text, comprehensive_metadata, "extract_ranges"
                )

            logger.info(
                f"Extracted {len(ranges)} ranges from {document_name} "
                f"in {processing_time:.2f}s"
            )

            return letter

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to extract ranges from {document_name} "
                f"after {processing_time:.2f}s: {e}"
            )

            # Return empty letter with error metadata
            return Letter(
                letter_id=document_name,
                ranges=[],
                metadata=LetterMetadata(
                    confidence_score=0.0,
                    processing_time=processing_time,
                    api_model=self.model,
                    extraction_method="xai_grok3_enhanced",
                    error=str(e),
                ),
            )

    def _build_enhanced_extraction_prompt(self, text: str, document_name: str) -> str:
        """Build enhanced extraction prompt with structured JSON schema.

        Args:
            text: Document text.
            document_name: Document name.

        Returns:
            Formatted prompt string.
        """
        prompt = f"""You are an expert AI system specialized in analyzing Schneider Electric technical documents with 95%+ accuracy.

Your task is to extract comprehensive metadata from the following obsolescence letter with EXTREME PRECISION.

CRITICAL ACCURACY REQUIREMENTS:
1. ONLY extract information that is EXPLICITLY stated in the document
2. NEVER create, infer, or hallucinate information
3. If information is not present, return empty arrays or null values
4. Be precise and accurate - false information is worse than no information
5. Focus on DISCOVERY - find whatever product ranges/families are actually mentioned
6. Maintain 95%+ accuracy by being conservative in extraction

DOCUMENT ANALYSIS:
Document: {document_name}
Text Length: {len(text)} characters

TEXT TO ANALYZE:
{text}

EXTRACTION REQUIREMENTS:
You must return a JSON object that strictly follows this schema:

{json.dumps(self.json_schema, indent=2)}

ACCURACY GUIDELINES:
- Product ranges: Only extract if clearly mentioned (e.g., "TeSys D", "PIX-DC", "Galaxy 6000")
- Dates: Only extract if explicitly stated with clear context
- Technical specs: Only extract if specifically mentioned with values
- Confidence: Calculate based on text clarity and information availability

RESPONSE FORMAT:
Return ONLY a valid JSON object. No additional text or explanation.

JSON Response:"""

        return prompt

    def _make_enhanced_api_call(self, prompt: str) -> Dict[str, Any]:
        """Make enhanced API call using official xAI SDK.

        Args:
            prompt: The prompt to send to the API.

        Returns:
            API response dictionary.
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Making API call (attempt {attempt + 1}/{self.max_retries})"
                )

                # Create chat using official SDK
                chat = self.client.chat.create(model=self.model, temperature=0.1)

                # Add system and user messages
                chat.append(
                    system(
                        "You are a precise technical document analyzer. Return only valid JSON."
                    )
                )
                chat.append(user(prompt))

                # Get response using official SDK
                response = chat.sample()

                if not response or not response.content:
                    raise APIError("No content in API response")

                # Parse JSON response
                try:
                    parsed_content = json.loads(response.content)
                    return parsed_content
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}")
                    # Try to extract JSON from response
                    import re

                    json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
                    if json_match:
                        try:
                            parsed_content = json.loads(json_match.group())
                            return parsed_content
                        except json.JSONDecodeError:
                            pass
                    raise APIError(f"Failed to parse JSON response: {e}")

            except Exception as e:
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise APIError(
                    f"API call failed after {self.max_retries} attempts: {e}"
                )

        raise APIError(f"API call failed after {self.max_retries} attempts")

    def generate_completion(
        self, prompt: str, document_content: str, document_name: str
    ) -> str:
        """Generate completion using the xAI API.

        Args:
            prompt: The prompt to send to the API.
            document_content: The document content to analyze.
            document_name: Name of the document.

        Returns:
            Generated completion text.
        """
        try:
            # Combine prompt with document content
            full_prompt = f"{prompt}\n\nDocument Content:\n{document_content}"

            # Create chat using official SDK
            chat = self.client.chat.create(model=self.model, temperature=0.1)

            # Add system and user messages
            chat.append(
                system(
                    "You are a precise technical document analyzer. Return only valid JSON."
                )
            )
            chat.append(user(full_prompt))

            # Get response using official SDK
            response = chat.sample()

            if not response or not response.content:
                logger.error("No content in API response")
                return ""

            return response.content

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return ""

    def extract_comprehensive_metadata(
        self, text: str, document_name: str
    ) -> Dict[str, Any]:
        """Extract comprehensive metadata with enhanced accuracy and debug capabilities.

        Args:
            text: Document text to analyze.
            document_name: Name of the document.

        Returns:
            Dictionary with comprehensive extracted metadata.
        """
        start_time = time.time()

        try:
            logger.info(f"Extracting comprehensive metadata from: {document_name}")

            # Build enhanced prompt
            prompt = self._build_enhanced_extraction_prompt(text, document_name)

            # Make enhanced API call
            response = self._make_enhanced_api_call(prompt)

            processing_time = time.time() - start_time

            # Validate and enhance response
            validated_response = self._validate_and_enhance_response(
                response, text, document_name
            )

            # Add processing metadata
            validated_response["extraction_metadata"].update(
                {
                    "processing_time": processing_time,
                    "api_model": self.model,
                    "extraction_method": "xai_grok3_enhanced",
                    "document_name": document_name,
                    "schema_version": "v2.0",
                }
            )

            # Debug console output
            if self.debug_enabled:
                self._write_debug_output(
                    document_name, text, validated_response, "comprehensive_extraction"
                )

            logger.info(
                f"Extracted comprehensive metadata from {document_name} "
                f"({len(validated_response['product_identification']['ranges'])} ranges) "
                f"in {processing_time:.2f}s"
            )

            return validated_response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to extract comprehensive metadata from {document_name} "
                f"after {processing_time:.2f}s: {e}"
            )

            # Return structured error response
            error_response = self._create_error_response(
                str(e), processing_time, document_name
            )

            if self.debug_enabled:
                self._write_debug_output(
                    document_name, text, error_response, "error_extraction"
                )

            return error_response

    def _validate_and_enhance_response(
        self, response: Dict[str, Any], text: str, document_name: str
    ) -> Dict[str, Any]:
        """Validate and enhance the API response for accuracy.

        Args:
            response: Raw API response.
            text: Original document text.
            document_name: Document name.

        Returns:
            Validated and enhanced response.
        """
        try:
            # Ensure all required fields exist
            validated = {}

            # Product identification
            product_id = response.get("product_identification", {})
            validated["product_identification"] = {
                "ranges": self._validate_ranges(product_id.get("ranges", []), text),
                "product_codes": product_id.get("product_codes", []),
                "product_types": product_id.get("product_types", []),
                "descriptions": product_id.get("descriptions", []),
            }

            # Brand business
            validated["brand_business"] = response.get(
                "brand_business",
                {"brands": [], "business_units": [], "geographic_regions": []},
            )

            # Commercial lifecycle
            validated["commercial_lifecycle"] = response.get(
                "commercial_lifecycle",
                {"commercial_status": [], "dates": {}, "timeline_info": []},
            )

            # Technical specs
            validated["technical_specs"] = response.get(
                "technical_specs",
                {
                    "voltage_levels": [],
                    "specifications": [],
                    "device_types": [],
                    "applications": [],
                },
            )

            # Service support
            validated["service_support"] = response.get(
                "service_support",
                {
                    "service_availability": [],
                    "warranty_info": [],
                    "replacement_guidance": [],
                    "spare_parts": [],
                },
            )

            # Regulatory compliance
            validated["regulatory_compliance"] = response.get(
                "regulatory_compliance",
                {"standards": [], "compliance_info": [], "safety_info": []},
            )

            # Business context
            validated["business_context"] = response.get(
                "business_context",
                {
                    "customer_impact": [],
                    "migration_recommendations": [],
                    "contact_info": [],
                    "business_reasons": [],
                },
            )

            # Extraction metadata
            extraction_meta = response.get("extraction_metadata", {})
            validated["extraction_metadata"] = {
                "confidence": self._calculate_confidence(validated, text),
                "analysis_quality": self._assess_analysis_quality(validated, text),
                "text_length": len(text),
                "extraction_method": "xai_grok3_enhanced",
                "limitations": extraction_meta.get("limitations", []),
            }

            return validated

        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return self._create_error_response(
                f"Validation failed: {e}", 0, document_name
            )

    def _validate_ranges(self, ranges: List[str], text: str) -> List[str]:
        """Validate extracted ranges against document text.

        Args:
            ranges: Extracted ranges.
            text: Document text.

        Returns:
            Validated ranges.
        """
        validated_ranges = []
        text_upper = text.upper()

        for range_name in ranges:
            if range_name and isinstance(range_name, str):
                range_upper = range_name.upper()

                # Check if range is actually mentioned in text
                if range_upper in text_upper:
                    validated_ranges.append(range_name.strip())
                else:
                    logger.warning(f"Range '{range_name}' not found in document text")

        return validated_ranges

    def _calculate_confidence(
        self, validated_response: Dict[str, Any], text: str
    ) -> float:
        """Calculate confidence score based on extraction quality.

        Args:
            validated_response: Validated response.
            text: Document text.

        Returns:
            Confidence score (0-1).
        """
        factors = []

        # Text length factor
        text_length = len(text)
        if text_length > 1000:
            factors.append(0.9)
        elif text_length > 500:
            factors.append(0.7)
        elif text_length > 100:
            factors.append(0.5)
        else:
            factors.append(0.3)

        # Content extraction factor
        total_items = 0
        for section in validated_response.values():
            if isinstance(section, dict):
                for key, value in section.items():
                    if isinstance(value, list):
                        total_items += len(value)
                    elif isinstance(value, dict):
                        total_items += len([v for v in value.values() if v])

        if total_items > 10:
            factors.append(0.9)
        elif total_items > 5:
            factors.append(0.7)
        elif total_items > 0:
            factors.append(0.5)
        else:
            factors.append(0.2)

        # Range validation factor
        ranges = validated_response.get("product_identification", {}).get("ranges", [])
        if ranges:
            factors.append(0.8)
        else:
            factors.append(0.4)

        return sum(factors) / len(factors)

    def _assess_analysis_quality(
        self, validated_response: Dict[str, Any], text: str
    ) -> str:
        """Assess the quality of analysis.

        Args:
            validated_response: Validated response.
            text: Document text.

        Returns:
            Quality assessment.
        """
        confidence = self._calculate_confidence(validated_response, text)

        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"

    def _create_error_response(
        self, error_msg: str, processing_time: float, document_name: str
    ) -> Dict[str, Any]:
        """Create structured error response.

        Args:
            error_msg: Error message.
            processing_time: Processing time.
            document_name: Document name.

        Returns:
            Structured error response.
        """
        return {
            "product_identification": {
                "ranges": [],
                "product_codes": [],
                "product_types": [],
                "descriptions": [],
            },
            "brand_business": {
                "brands": [],
                "business_units": [],
                "geographic_regions": [],
            },
            "commercial_lifecycle": {
                "commercial_status": [],
                "dates": {},
                "timeline_info": [],
            },
            "technical_specs": {
                "voltage_levels": [],
                "specifications": [],
                "device_types": [],
                "applications": [],
            },
            "service_support": {
                "service_availability": [],
                "warranty_info": [],
                "replacement_guidance": [],
                "spare_parts": [],
            },
            "regulatory_compliance": {
                "standards": [],
                "compliance_info": [],
                "safety_info": [],
            },
            "business_context": {
                "customer_impact": [],
                "migration_recommendations": [],
                "contact_info": [],
                "business_reasons": [],
            },
            "extraction_metadata": {
                "confidence": 0.0,
                "analysis_quality": "low",
                "text_length": 0,
                "extraction_method": "xai_grok3_enhanced",
                "limitations": [f"Processing failed: {error_msg}"],
                "processing_time": processing_time,
                "api_model": self.model,
                "document_name": document_name,
                "error": error_msg,
            },
        }

    def _write_debug_output(
        self, document_name: str, text: str, response: Dict[str, Any], operation: str
    ) -> None:
        """Write debug output to console and file.

        Args:
            document_name: Document name.
            text: Document text.
            response: API response.
            operation: Operation type.
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            debug_filename = f"{operation}_{document_name}_{timestamp}.json"
            debug_path = self.debug_output_dir / debug_filename

            debug_data = {
                "timestamp": timestamp,
                "operation": operation,
                "document_name": document_name,
                "text_length": len(text),
                "text_preview": text[:500] + "..." if len(text) > 500 else text,
                "response": response,
                "model": self.model,
                "api_base_url": self.base_url,
            }

            # Write to file
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False)

            # Console output
            print(f"\n🔍 DEBUG CONSOLE - {operation.upper()}")
            print(f"📄 Document: {document_name}")
            print(f"📊 Text Length: {len(text)} characters")
            print(
                f"🎯 Confidence: {response.get('extraction_metadata', {}).get('confidence', 0):.2f}"
            )
            print(
                f"📋 Ranges Found: {len(response.get('product_identification', {}).get('ranges', []))}"
            )
            print(f"💾 Debug File: {debug_path}")

            # Show raw JSON for debugging
            if response.get("extraction_metadata", {}).get("confidence", 0) < 0.7:
                print(f"⚠️  LOW CONFIDENCE - RAW JSON:")
                print(json.dumps(response, indent=2)[:1000] + "...")

        except Exception as e:
            logger.error(f"Debug output failed: {e}")

    def enable_debug_console(self) -> None:
        """Enable debug console output."""
        self.debug_enabled = True
        logger.info("Debug console enabled")

    def disable_debug_console(self) -> None:
        """Disable debug console output."""
        self.debug_enabled = False
        logger.info("Debug console disabled")

    def get_debug_files(self) -> List[Path]:
        """Get list of debug files.

        Returns:
            List of debug file paths.
        """
        return list(self.debug_output_dir.glob("*.json"))

    def clear_debug_files(self) -> int:
        """Clear all debug files.

        Returns:
            Number of files cleared.
        """
        debug_files = self.get_debug_files()
        count = 0
        for file_path in debug_files:
            try:
                file_path.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete debug file {file_path}: {e}")

        logger.info(f"Cleared {count} debug files")
        return count

    def validate_ranges(self, ranges: List[str]) -> Dict[str, Any]:
        """Validate extracted ranges against known patterns.

        Args:
            ranges: List of extracted ranges.

        Returns:
            Validation results.
        """
        validation_results = {
            "total_ranges": len(ranges),
            "valid_ranges": [],
            "suspicious_ranges": [],
            "validation_notes": [],
        }

        # Common Schneider Electric product range patterns
        known_patterns = [
            r"^[A-Z]{2,6}(-[A-Z0-9]+)*$",  # PIX-DC, HVX-C, etc.
            r"^[A-Z]+\d+[A-Z]*$",  # MCSet, N500, etc.
            r"^[A-Z]+\s+[A-Z0-9]+$",  # Evolis HP, etc.
        ]

        for range_name in ranges:
            is_valid = False

            # Check against known patterns
            import re

            for pattern in known_patterns:
                if re.match(pattern, range_name):
                    is_valid = True
                    break

            if is_valid:
                validation_results["valid_ranges"].append(range_name)
            else:
                validation_results["suspicious_ranges"].append(range_name)
                validation_results["validation_notes"].append(
                    f"Range '{range_name}' doesn't match known patterns"
                )

        return validation_results

    def get_api_status(self) -> Dict[str, Any]:
        """Check the status of the xAI API.

        Returns:
            API status information.
        """
        try:
            # Make a simple test request
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
            }

            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/chat/completions", json=test_payload, timeout=10
            )
            response_time = time.time() - start_time

            status = {
                "api_accessible": True,
                "response_time": response_time,
                "status_code": response.status_code,
                "model": self.model,
                "base_url": self.base_url,
            }

            if response.status_code == 200:
                status["api_working"] = True
                status["message"] = "API is working correctly"
            else:
                status["api_working"] = False
                status["message"] = f"API returned status {response.status_code}"

        except Exception as e:
            status = {
                "api_accessible": False,
                "api_working": False,
                "error": str(e),
                "model": self.model,
                "base_url": self.base_url,
            }

        return status
