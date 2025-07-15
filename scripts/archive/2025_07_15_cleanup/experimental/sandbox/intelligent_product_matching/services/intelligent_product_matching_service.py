#!/usr/bin/env python3
"""
Intelligent Product Matching Service - Multiple Matches Version
Enhanced filtering layer that uses Grok to intelligently match ALL products
based on technical specifications and comprehensive product metadata

Version: 2.0.0
Author: SE Letters Team
"""

import json
import time
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from loguru import logger

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))

# Import services
from se_letters.core.config import get_config
from se_letters.services.xai_service import XAIService
from se_letters.services.sota_product_database_service import (
    SOTAProductDatabaseService
)


@dataclass
class LetterProductInfo:
    """Letter product information from grok_metadata.json"""
    product_identifier: str
    range_label: str
    subrange_label: Optional[str]
    product_line: str
    product_description: str
    technical_specifications: Dict[str, Any]
    obsolescence_status: Optional[str] = None
    end_of_service_date: Optional[str] = None
    replacement_suggestions: Optional[str] = None


@dataclass
class ProductCandidate:
    """Discovered product candidate with comprehensive fields"""
    product_identifier: str
    product_type: Optional[str]
    product_description: Optional[str]
    brand_code: Optional[str]
    brand_label: Optional[str]
    range_code: Optional[str]
    range_label: Optional[str]
    subrange_code: Optional[str]
    subrange_label: Optional[str]
    devicetype_label: Optional[str]
    pl_services: Optional[str]


@dataclass
class ProductMatch:
    """Individual product match result"""
    product_identifier: str
    confidence: float
    reason: str
    technical_match_score: float
    nomenclature_match_score: float
    product_line_match_score: float
    match_type: str


@dataclass
class IntelligentMatchResult:
    """Complete intelligent matching result with multiple matches"""
    matching_products: List[ProductMatch]
    total_matches: int
    range_based_matching: bool
    excluded_low_confidence: int
    processing_time_ms: float
    letter_product_info: LetterProductInfo


class IntelligentProductMatchingService:
    """Service for intelligent product matching with multiple results"""
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the intelligent product matching service"""
        self.debug_mode = debug_mode
        self.config = get_config()
        self.xai_service = XAIService(self.config)
        self.product_db_service = SOTAProductDatabaseService()
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        logger.info("🧠 Intelligent Product Matching Service initialized (Multiple Matches Mode)")
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from config file"""
        try:
            config_path = Path("config/prompts.yaml")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('prompts', {})
        except Exception as e:
            logger.error(f"❌ Failed to load prompts: {e}")
            return {}
    
    def match_products(self, letter_product_info: LetterProductInfo,
                       discovered_candidates: List[ProductCandidate]
                       ) -> IntelligentMatchResult:
        """Match products using intelligent filtering with multiple results"""
        start_time = time.time()
        
        try:
            logger.info(f"🧠 Starting intelligent product matching for: "
                        f"{letter_product_info.product_identifier}")
            logger.info(f"📋 Analyzing {len(discovered_candidates)} discovered candidates")
            
            # Format candidates for prompt
            candidates_formatted = self._format_discovered_candidates(discovered_candidates)
            
            # Create prompt
            prompt = self._create_matching_prompt(letter_product_info, candidates_formatted)
            
            if self.debug_mode:
                logger.info("🔍 DEBUG: Full prompt sent to Grok:")
                logger.info(prompt)
            
            # Make Grok call
            response = self._make_grok_call(prompt)
            
            if self.debug_mode:
                logger.info("📤 DEBUG: Full raw response from Grok:")
                logger.info(response)
            
            # Parse response
            match_results = self._parse_grok_response(response)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Create result
            result = IntelligentMatchResult(
                matching_products=match_results.get('matching_products', []),
                total_matches=match_results.get('total_matches', 0),
                range_based_matching=match_results.get('range_based_matching', False),
                excluded_low_confidence=match_results.get('excluded_low_confidence', 0),
                processing_time_ms=processing_time_ms,
                letter_product_info=letter_product_info
            )
            
            logger.info(f"✅ Intelligent matching completed: {result.total_matches} matches found")
            logger.info(f"⏱️ Processing time: {processing_time_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Intelligent matching failed: {e}")
            return IntelligentMatchResult(
                matching_products=[],
                total_matches=0,
                range_based_matching=False,
                excluded_low_confidence=0,
                processing_time_ms=(time.time() - start_time) * 1000,
                letter_product_info=letter_product_info
            )
    
    def _format_discovered_candidates(self, candidates: List[ProductCandidate]) -> str:
        """Format discovered candidates for prompt"""
        formatted_candidates = []
        
        for i, candidate in enumerate(candidates, 1):
            candidate_info = f"""
Candidate {i}:
- Product Identifier: {candidate.product_identifier}
- Product Type: {candidate.product_type or 'Not specified'}
- Product Description: {candidate.product_description or 'Not specified'}
- Brand: {candidate.brand_label or 'Not specified'} ({candidate.brand_code or 'N/A'})
- Range: {candidate.range_label or 'Not specified'} ({candidate.range_code or 'N/A'})
- Subrange: {candidate.subrange_label or 'Not specified'} ({candidate.subrange_code or 'N/A'})
- Device Type: {candidate.devicetype_label or 'Not specified'}
- PL Services: {candidate.pl_services or 'Not specified'}
"""
            formatted_candidates.append(candidate_info)
        
        return "\n".join(formatted_candidates)
    
    def _create_matching_prompt(self, letter_product_info: LetterProductInfo, 
                               candidates_formatted: str) -> str:
        """Create the matching prompt"""
        prompt_config = self.prompts.get('intelligent_product_matching', {})
        system_prompt = prompt_config.get('system_prompt', '')
        user_template = prompt_config.get('user_prompt_template', '')
        
        # Format letter product info
        letter_info = f"""
Product Identifier: {letter_product_info.product_identifier}
Range Label: {letter_product_info.range_label}
Subrange Label: {letter_product_info.subrange_label or 'Not specified'}
Product Line: {letter_product_info.product_line}
Product Description: {letter_product_info.product_description}
Technical Specifications: {json.dumps(letter_product_info.technical_specifications, indent=2)}
Obsolescence Status: {letter_product_info.obsolescence_status or 'Not specified'}
End of Service Date: {letter_product_info.end_of_service_date or 'Not specified'}
Replacement Suggestions: {letter_product_info.replacement_suggestions or 'Not specified'}
"""
        
        # Create user prompt
        user_prompt = user_template.format(
            letter_product_info=letter_info,
            discovered_candidates=candidates_formatted
        )
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def _make_grok_call(self, prompt: str) -> str:
        """Make API call to Grok"""
        try:
            response = self.xai_service.generate_completion(
                prompt=prompt,
                document_content="",
                document_name="intelligent_product_matching"
            )
            return response.get('content', '')
        except Exception as e:
            logger.error(f"❌ Grok API call failed: {e}")
            return ""
    
    def _parse_grok_response(self, response: str) -> Dict[str, Any]:
        """Parse Grok response JSON"""
        try:
            # Extract JSON from response
            response_clean = response.strip()
            
            # Handle case where response might have markdown formatting
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            # Parse JSON
            result = json.loads(response_clean)
            
            # Convert matching_products to ProductMatch objects
            matching_products = []
            for match_data in result.get('matching_products', []):
                product_match = ProductMatch(
                    product_identifier=match_data.get('product_identifier', ''),
                    confidence=match_data.get('confidence', 0.0),
                    reason=match_data.get('reason', ''),
                    technical_match_score=match_data.get('technical_match_score', 0.0),
                    nomenclature_match_score=match_data.get('nomenclature_match_score', 0.0),
                    product_line_match_score=match_data.get('product_line_match_score', 0.0),
                    match_type=match_data.get('match_type', 'unknown')
                )
                matching_products.append(product_match)
            
            return {
                'matching_products': matching_products,
                'total_matches': result.get('total_matches', len(matching_products)),
                'range_based_matching': result.get('range_based_matching', False),
                'excluded_low_confidence': result.get('excluded_low_confidence', 0)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.error(f"Response was: {response}")
            return {
                'matching_products': [],
                'total_matches': 0,
                'range_based_matching': False,
                'excluded_low_confidence': 0
            }
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {e}")
            return {
                'matching_products': [],
                'total_matches': 0,
                'range_based_matching': False,
                'excluded_low_confidence': 0
            }
    
    def save_results(self, result: IntelligentMatchResult, output_dir: Path) -> Path:
        """Save intelligent matching results to file"""
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = int(time.time())
            filename = f"intelligent_matching_results_{timestamp}.json"
            output_path = output_dir / filename
            
            # Prepare result data
            result_data = {
                'letter_product_info': asdict(result.letter_product_info),
                'matching_results': {
                    'matching_products': [asdict(match) for match in result.matching_products],
                    'total_matches': result.total_matches,
                    'range_based_matching': result.range_based_matching,
                    'excluded_low_confidence': result.excluded_low_confidence
                },
                'processing_metadata': {
                    'processing_time_ms': result.processing_time_ms,
                    'timestamp': timestamp,
                    'service_version': '2.0.0'
                }
            }
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            logger.info(f"💾 Results saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
            return None


def main():
    """Main function for testing"""
    # Test the service with mock data
    service = IntelligentProductMatchingService(debug_mode=True)
    
    # Mock letter product info
    letter_product = LetterProductInfo(
        product_identifier="PIX 2B",
        range_label="PIX Double Bus Bar",
        subrange_label="PIX 2B",
        product_line="PSIBS (Power Systems)",
        product_description="Medium Voltage equipment with double bus bar configuration",
        technical_specifications={
            "voltage_levels": ["12 – 17.5kV"],
            "current_ratings": ["up to 3150A"],
            "frequencies": ["50/60Hz"]
        },
        obsolescence_status="Withdrawn"
    )
    
    # Mock discovered candidates
    candidates = [
        ProductCandidate(
            product_identifier="PIX2B-HV-3150",
            product_type="Switchgear",
            product_description="High Voltage Double Bus Bar Switchgear",
            brand_label="Schneider Electric",
            range_label="PIX Double Bus Bar",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX2B-MV-2500",
            product_type="Switchgear",
            product_description="Medium Voltage Double Bus Bar Switchgear",
            brand_label="Schneider Electric",
            range_label="PIX Double Bus Bar",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        ),
        ProductCandidate(
            product_identifier="PIX2B-LV-1600",
            product_type="Switchgear",
            product_description="Low Voltage Double Bus Bar Switchgear",
            brand_label="Schneider Electric",
            range_label="PIX Double Bus Bar",
            subrange_label="PIX 2B",
            devicetype_label="Medium Voltage Equipment",
            pl_services="PSIBS"
        )
    ]
    
    # Process matching
    result = service.match_products(letter_product, candidates)
    
    # Save results
    output_dir = Path("scripts/sandbox/intelligent_product_matching/results")
    service.save_results(result, output_dir)
    
    # Print summary
    print(f"\n{'='*50}")
    print("INTELLIGENT PRODUCT MATCHING RESULTS")
    print(f"{'='*50}")
    print(f"Letter Product: {letter_product.product_identifier}")
    print(f"Total Matches Found: {result.total_matches}")
    print(f"Range-based Matching: {result.range_based_matching}")
    print(f"Processing Time: {result.processing_time_ms:.2f}ms")
    print(f"{'='*50}")
    
    for i, match in enumerate(result.matching_products, 1):
        print(f"\nMatch {i}:")
        print(f"  Product: {match.product_identifier}")
        print(f"  Confidence: {match.confidence:.2f}")
        print(f"  Match Type: {match.match_type}")
        print(f"  Technical Score: {match.technical_match_score:.2f}")
        print(f"  Nomenclature Score: {match.nomenclature_match_score:.2f}")
        print(f"  Product Line Score: {match.product_line_match_score:.2f}")
        print(f"  Reason: {match.reason}")


if __name__ == "__main__":
    main() 