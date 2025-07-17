#!/usr/bin/env python3
"""
Intelligent Product Matching Service - Production Version
Enhanced filtering layer that uses Grok to intelligently match ALL products
based on technical specifications and comprehensive product metadata

Version: 2.2.0
Author: Alexandre Huther
Status: Production Ready
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any

from loguru import logger

from se_letters.core.config import get_config
from se_letters.services.xai_service import XAIService
from se_letters.models.product_matching import (
    LetterProductInfo,
    ProductCandidate,
    ProductMatch,
    IntelligentMatchResult
)


class IntelligentProductMatchingService:
    """Production service for intelligent product matching with multiple 
    results"""
    
    def __init__(self, debug_mode: bool = False):
        """Initialize the intelligent product matching service"""
        self.debug_mode = debug_mode
        self.config = get_config()
        self.xai_service = XAIService(self.config)
        
        # Load prompts from config
        self.prompts = self._load_prompts()
        
        logger.info("🧠 Intelligent Product Matching Service initialized "
                   "(Production Mode)")
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load intelligent product matching prompts from config"""
        try:
            config_path = (Path(__file__).parent.parent.parent.parent / 
                          "config" / "prompts.yaml")
            
            if not config_path.exists():
                logger.warning(f"⚠️ Prompts file not found: {config_path}")
                return self._get_default_prompts()
            
            import yaml
            with open(config_path, 'r') as f:
                prompts = yaml.safe_load(f)
            
            return prompts.get('intelligent_product_matching', 
                              self._get_default_prompts())
            
        except Exception as e:
            logger.error(f"❌ Error loading prompts: {e}")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default prompts if config file is not available"""
        return {
            'system': """You are an expert in Schneider Electric product identification and matching. Your task is to analyze obsolescence letter product information and match it against discovered product candidates from the IBcatalogue database.

**CRITICAL REQUIREMENTS:**
1. Find ALL products that match the obsolescence letter product, not just the best one
2. When letters mention ranges or series, identify ALL products in that range
3. Use confidence filtering (>= 0.5) to ensure quality matches
4. Provide detailed matching reasoning for each product

**MATCHING CRITERIA:**
- Technical specifications alignment
- Nomenclature and naming patterns
- Product line classification
- Brand and range associations
- Device type compatibility

**OUTPUT FORMAT:**
Return a JSON object with ALL matching products, each with detailed scoring.""",
            
            'user': """Analyze the following obsolescence letter product information and match it against the discovered product candidates.

**LETTER PRODUCT INFORMATION:**
{letter_product_info}

**DISCOVERED PRODUCT CANDIDATES:**
{discovered_candidates}

**TASK:**
Find ALL products that match the obsolescence letter product. Look for:
1. Exact product identifier matches
2. Range/series membership (if letter mentions a range, find ALL products in that range)
3. Technical specification compatibility
4. Brand and product line alignment

**CONFIDENCE THRESHOLD:** Only include matches with confidence >= 0.5

**RESPONSE FORMAT:**
{{
    "matching_products": [
        {{
            "product_identifier": "exact product identifier from candidates",
            "confidence": 0.0-1.0,
            "reason": "detailed explanation of why this product matches",
            "technical_match_score": 0.0-1.0,
            "nomenclature_match_score": 0.0-1.0,
            "product_line_match_score": 0.0-1.0,
            "match_type": "exact|range_member|variant|compatible"
        }}
    ],
    "total_matches": number,
    "range_based_matching": boolean,
    "excluded_low_confidence": number
}}"""
        }
    
    def match_products(self, letter_product_info: LetterProductInfo, 
                      product_candidates: List[ProductCandidate]) -> IntelligentMatchResult:
        """Match products using intelligent analysis"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Starting intelligent product matching for: "
                       f"{letter_product_info.product_identifier}")
            logger.info(f"📊 Processing {len(product_candidates)} "
                       f"product candidates")
            logger.info(f"[DEBUG] Matching {len(product_candidates)} candidates for product: {letter_product_info.product_identifier}")
            logger.info(f"[DEBUG] Candidate IDs: {[c.product_identifier for c in product_candidates]}")
            
            # Create matching prompt
            prompt = self._create_matching_prompt(letter_product_info, 
                                                product_candidates)
            
            # Make Grok API call
            logger.info("🤖 Calling Grok API for intelligent matching")
            raw_response = self._make_grok_call(prompt)
            
            if not raw_response:
                logger.error("❌ Empty response from Grok API")
                return self._create_empty_result(letter_product_info, 
                                               time.time() - start_time)
            
            # Parse response
            parsed_result = self._parse_grok_response(raw_response)
            
            # Create final result
            processing_time = (time.time() - start_time) * 1000
            
            result = IntelligentMatchResult(
                matching_products=parsed_result['matching_products'],
                total_matches=parsed_result['total_matches'],
                range_based_matching=parsed_result['range_based_matching'],
                excluded_low_confidence=parsed_result['excluded_low_confidence'],
                processing_time_ms=processing_time,
                letter_product_info=letter_product_info,
                raw_grok_request=prompt if self.debug_mode else None,
                raw_grok_response=raw_response if self.debug_mode else None
            )
            
            logger.info(f"✅ Product matching completed in "
                       f"{processing_time:.2f}ms")
            logger.info(f"📊 Found {result.total_matches} matching products")
            logger.info(f"🎯 Range-based matching: "
                       f"{result.range_based_matching}")
            logger.info(f"[DEBUG] Match confidence scores: {[m.confidence for m in result.matching_products]}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Product matching failed: {e}")
            return self._create_empty_result(letter_product_info, 
                                           time.time() - start_time)
    
    def _create_matching_prompt(self, letter_product_info: LetterProductInfo, 
                               product_candidates: List[ProductCandidate]) -> str:
        """Create intelligent matching prompt with database scoring"""
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
        
        # Format candidates with database scores
        candidates_formatted = []
        for i, candidate in enumerate(product_candidates[:50]):  # Limit to top 50 for LLM
            candidates_formatted.append(f"""
Candidate #{i+1}:
Product Identifier: {candidate.product_identifier}
Product Type: {candidate.product_type or 'N/A'}
Description: {candidate.product_description or 'N/A'}
Brand: {candidate.brand_code or 'N/A'} ({candidate.brand_label or 'N/A'})
Range: {candidate.range_label or 'N/A'}
Subrange: {candidate.subrange_label or 'N/A'}
Device Type: {candidate.devicetype_label or 'N/A'}
Product Line: {candidate.pl_services or 'N/A'}
Database Score: {candidate.match_score:.2f}/10.0 (Higher = better match)
""")
        
        candidates_text = "\n".join(candidates_formatted)
        
        # Enhanced prompt with scoring guidance
        prompt = self.prompts['user'].format(
            letter_product_info=letter_info,
            discovered_candidates=candidates_text
        )
        
        # Add scoring guidance
        prompt += f"""

**DATABASE SCORING CONTEXT:**
The candidates above are pre-scored by the database system (0.0-10.0 scale):
- 8.0-10.0: Excellent matches (exact identifiers, ranges, subranges)
- 5.0-7.9: Good matches (fuzzy similarity, product line alignment)
- 3.0-4.9: Moderate matches (partial alignment, brand matches)
- 0.0-2.9: Weak matches (minimal alignment)

**ENHANCED MATCHING INSTRUCTIONS:**
1. Consider database scores as a strong indicator of relevance
2. Products with high database scores (>=6.0) are likely good matches
3. Products with low database scores (<3.0) should only be included if you have strong technical reasoning
4. Combine database scoring with your technical analysis for final confidence
5. If letter mentions a specific range/subrange (e.g., "Galaxy 6000"), prioritize exact matches over broad range matches
6. Ensure all selected products have confidence >= 0.5 after your analysis

**FINAL CONFIDENCE CALCULATION:**
Consider both database score and your technical analysis:
- High database score (>=6.0) + good technical match = High confidence (0.8-1.0)
- Medium database score (3.0-5.9) + good technical match = Medium confidence (0.6-0.79)
- Low database score (<3.0) + excellent technical match = Low confidence (0.5-0.59)
- Low database score + poor technical match = Exclude (confidence <0.5)
"""
        
        return prompt
    
    def _make_grok_call(self, prompt: str) -> str:
        """Make API call to Grok"""
        try:
            response = self.xai_service.generate_completion(
                prompt=prompt,
                document_content="",
                document_name="intelligent_product_matching"
            )
            
            # Extract content from response
            if isinstance(response, dict):
                return response.get('content', '')
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"❌ Grok API call failed: {e}")
            return ""
    
    def _parse_grok_response(self, response: str) -> Dict[str, Any]:
        """Parse Grok response JSON"""
        try:
            # Clean response
            response_clean = response.strip()
            
            # Handle markdown formatting
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            # Parse JSON
            result = json.loads(response_clean)
            
            # Convert to ProductMatch objects
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
                'total_matches': result.get('total_matches', 
                                          len(matching_products)),
                'range_based_matching': result.get('range_based_matching', 
                                                  False),
                'excluded_low_confidence': result.get('excluded_low_confidence', 
                                                     0)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.error(f"Response was: {response}")
            return self._empty_match_result()
        except Exception as e:
            logger.error(f"❌ Response parsing failed: {e}")
            return self._empty_match_result()
    
    def _empty_match_result(self) -> Dict[str, Any]:
        """Return empty match result"""
        return {
            'matching_products': [],
            'total_matches': 0,
            'range_based_matching': False,
            'excluded_low_confidence': 0
        }
    
    def _create_empty_result(self, letter_product_info: LetterProductInfo, 
                           elapsed_time: float) -> IntelligentMatchResult:
        """Create empty result for error cases"""
        return IntelligentMatchResult(
            matching_products=[],
            total_matches=0,
            range_based_matching=False,
            excluded_low_confidence=0,
            processing_time_ms=elapsed_time * 1000,
            letter_product_info=letter_product_info
        )
    
    def create_letter_product_info_from_grok_metadata(self, 
                                                     grok_metadata: Dict[str, Any]) -> List[LetterProductInfo]:
        """Create LetterProductInfo objects from Grok metadata"""
        letter_products = []
        
        try:
            # Extract products from grok metadata
            products = grok_metadata.get('products', [])
            
            for product in products:
                letter_product = LetterProductInfo(
                    product_identifier=product.get('product_identifier', ''),
                    range_label=product.get('range_label', ''),
                    subrange_label=product.get('subrange_label'),
                    product_line=product.get('product_line', ''),
                    product_description=product.get('product_description', ''),
                    technical_specifications=grok_metadata.get('technical_specifications', {}),
                    obsolescence_status=product.get('obsolescence_status'),
                    end_of_service_date=product.get('end_of_service_date'),
                    replacement_suggestions=product.get('replacement_suggestions')
                )
                letter_products.append(letter_product)
            
            logger.info(f"📋 Created {len(letter_products)} LetterProductInfo "
                       f"objects from Grok metadata")
            
        except Exception as e:
            logger.error(f"❌ Error creating LetterProductInfo from Grok "
                        f"metadata: {e}")
        
        return letter_products
    
    def save_run_data(self, run_id: str, stage: str, 
                     data: Dict[str, Any]) -> None:
        """Save run data to JSON files"""
        try:
            # Create run directory
            run_dir = Path("data/runs") / run_id / stage
            run_dir.mkdir(parents=True, exist_ok=True)
            
            # Save data files
            for filename, content in data.items():
                file_path = run_dir / f"{filename}.json"
                with open(file_path, 'w') as f:
                    json.dump(content, f, indent=2, default=str)
            
            logger.info(f"💾 Saved run data to: {run_dir}")
            
        except Exception as e:
            logger.error(f"❌ Error saving run data: {e}") 