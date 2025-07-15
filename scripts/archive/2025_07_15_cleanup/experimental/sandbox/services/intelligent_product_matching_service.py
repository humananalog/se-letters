#!/usr/bin/env python3
"""
Intelligent Product Matching Service
Enhanced filtering layer that uses Grok to intelligently match products
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
from dataclasses import dataclass
from loguru import logger

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))

# Import services
from se_letters.core.config import get_config
from se_letters.services.xai_service import XAIService
from se_letters.services.sota_product_database_service import SOTAProductDatabaseService


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
    commercial_status: Optional[str]
    confidence_score: float
    source: str  # Which discovery strategy found this
    technical_specifications: Dict[str, Any]
    end_of_commercialisation: Optional[str] = None
    serviceable: Optional[str] = None


@dataclass
class IntelligentMatchResult:
    """Result of intelligent product matching"""
    letter_product_id: str
    matched_product_identifier: str
    confidence: float
    reason: str
    technical_match_score: float
    nomenclature_match_score: float
    product_line_match_score: float
    alternative_candidates: List[str]
    processing_time_ms: float
    grok_response: Dict[str, Any]


class IntelligentProductMatchingService:
    """
    Enhanced intelligent product matching service with comprehensive
    database integration
    """
    
    def __init__(self, debug_mode: bool = True):
        """Initialize the intelligent matching service with real database integration"""
        self.config = get_config()
        self.debug_mode = debug_mode
        
        # Initialize XAI service
        self.xai_service = XAIService(self.config)
        
        # Initialize SOTA database service for real data
        self.sota_db_service = SOTAProductDatabaseService()
        
        # Load prompt from prompts.yaml
        try:
            prompts_config = self._load_prompts_config()
            self.prompt = prompts_config.get('intelligent_product_matching', {
                'system_prompt': 'You are an expert system for Schneider Electric product matching.',
                'user_prompt': 'Match this product to the best candidate from the list.'
            })
        except Exception as e:
            logger.warning(f"Failed to load prompts config: {e}")
            self.prompt = {
                'system_prompt': 'You are an expert system for Schneider Electric product matching.',
                'user_prompt': 'Match this product to the best candidate from the list.'
            }
        
        logger.info("🧠 Intelligent Product Matching Service initialized")
        logger.info("🔍 Real database integration enabled")
        logger.info(f"🐛 Debug mode: {self.debug_mode}")
    
    def _get_api_key(self) -> str:
        """Get XAI API key from environment"""
        import os
        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            raise ValueError("XAI_API_KEY environment variable not set")
        return api_key
    
    def _load_prompts_config(self) -> Dict[str, Any]:
        """Load prompts configuration from YAML file"""
        prompts_path = Path("config/prompts.yaml")
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts config: {e}")
            raise
    
    def _get_real_discovered_candidates(self, letter_product: LetterProductInfo) -> List[ProductCandidate]:
        """
        Get REAL discovered product candidates from the database using comprehensive search
        """
        try:
            logger.info(f"🔍 Searching database for real candidates: {letter_product.product_identifier}")
            
            # Use SOTA database service to find real products
            search_result = self.sota_db_service.find_products_by_range(
                letter_product.range_label or letter_product.product_identifier,
                include_obsolete=True
            )
            
            candidates = []
            
            # Convert search results to ProductCandidate objects with comprehensive fields
            for product_match in search_result.products:
                # Get comprehensive fields from the product match
                candidate = ProductCandidate(
                    product_identifier=product_match.product_identifier,
                    product_type=getattr(product_match, 'product_type', ''),
                    product_description=getattr(product_match, 'product_description', ''),
                    brand_code=getattr(product_match, 'brand_code', ''),
                    brand_label=getattr(product_match, 'brand_label', ''),
                    range_code=getattr(product_match, 'range_code', ''),
                    range_label=product_match.range_label,
                    subrange_code=getattr(product_match, 'subrange_code', ''),
                    subrange_label=getattr(product_match, 'subrange_label', ''),
                    devicetype_label=getattr(product_match, 'devicetype_label', ''),
                    pl_services=getattr(product_match, 'pl_services', ''),
                    confidence_score=product_match.confidence_score,
                    technical_specifications=getattr(product_match, 'technical_specifications', {}),
                    commercial_status=getattr(product_match, 'commercial_status', ''),
                    end_of_commercialisation=getattr(product_match, 'end_of_commercialisation', ''),
                    serviceable=getattr(product_match, 'serviceable', ''),
                    source='database_range_search'
                )
                candidates.append(candidate)
            
            # If no results from range search, try semantic search with product identifier
            if not candidates and letter_product.product_identifier:
                logger.info(f"🔄 No range results, trying semantic search: {letter_product.product_identifier}")
                
                # Semantic search using product identifier
                search_result = self.sota_db_service.search_products_semantic(
                    letter_product.product_identifier,
                    limit=20
                )
                
                for product_match in search_result.products:
                    candidate = ProductCandidate(
                        product_identifier=product_match.product_identifier,
                        product_type=getattr(product_match, 'product_type', ''),
                        product_description=getattr(product_match, 'product_description', ''),
                        brand_code=getattr(product_match, 'brand_code', ''),
                        brand_label=getattr(product_match, 'brand_label', ''),
                        range_code=getattr(product_match, 'range_code', ''),
                        range_label=product_match.range_label,
                        subrange_code=getattr(product_match, 'subrange_code', ''),
                        subrange_label=getattr(product_match, 'subrange_label', ''),
                        devicetype_label=getattr(product_match, 'devicetype_label', ''),
                        pl_services=getattr(product_match, 'pl_services', ''),
                        confidence_score=product_match.confidence_score,
                        technical_specifications=getattr(product_match, 'technical_specifications', {}),
                        commercial_status=getattr(product_match, 'commercial_status', ''),
                        end_of_commercialisation=getattr(product_match, 'end_of_commercialisation', ''),
                        serviceable=getattr(product_match, 'serviceable', ''),
                        source='semantic_search'
                    )
                    candidates.append(candidate)
            
            # If still no results, try broader search with product description
            if not candidates and letter_product.product_description:
                logger.info(f"🔄 No direct results, trying broader search with description")
                
                # Semantic search using product description
                search_result = self.sota_db_service.search_products_semantic(
                    letter_product.product_description,
                    limit=20
                )
                
                for product_match in search_result.products:
                    candidate = ProductCandidate(
                        product_identifier=product_match.product_identifier,
                        product_type=getattr(product_match, 'product_type', ''),
                        product_description=getattr(product_match, 'product_description', ''),
                        brand_code=getattr(product_match, 'brand_code', ''),
                        brand_label=getattr(product_match, 'brand_label', ''),
                        range_code=getattr(product_match, 'range_code', ''),
                        range_label=product_match.range_label,
                        subrange_code=getattr(product_match, 'subrange_code', ''),
                        subrange_label=getattr(product_match, 'subrange_label', ''),
                        devicetype_label=getattr(product_match, 'devicetype_label', ''),
                        pl_services=getattr(product_match, 'pl_services', ''),
                        confidence_score=product_match.confidence_score,
                        technical_specifications=getattr(product_match, 'technical_specifications', {}),
                        commercial_status=getattr(product_match, 'commercial_status', ''),
                        end_of_commercialisation=getattr(product_match, 'end_of_commercialisation', ''),
                        serviceable=getattr(product_match, 'serviceable', ''),
                        source='semantic_description_search'
                    )
                    candidates.append(candidate)
            
            logger.info(f"✅ Found {len(candidates)} real candidates from database")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Error getting real candidates: {e}")
            return []
    
    def _format_letter_product_info(self, letter_product: LetterProductInfo) -> str:
        """Format letter product information for Grok"""
        
        info = {
            "product_identifier": letter_product.product_identifier,
            "range_label": letter_product.range_label,
            "subrange_label": letter_product.subrange_label,
            "product_line": letter_product.product_line,
            "product_description": letter_product.product_description,
            "technical_specifications": letter_product.technical_specifications,
            "obsolescence_status": letter_product.obsolescence_status,
            "end_of_service_date": letter_product.end_of_service_date,
            "replacement_suggestions": letter_product.replacement_suggestions
        }
        
        return json.dumps(info, indent=2)
    
    def _format_discovered_candidates(self, candidates: List[ProductCandidate]) -> str:
        """Format discovered candidates with comprehensive database fields"""
        if not candidates:
            return "No candidates found in database search."
        
        formatted_candidates = []
        
        for i, candidate in enumerate(candidates, 1):
            candidate_text = f"""
Candidate {i}:
- Product Identifier: {candidate.product_identifier}
- Product Type: {candidate.product_type}
- Product Description: {candidate.product_description}
- Brand Code: {candidate.brand_code}
- Brand Label: {candidate.brand_label}
- Range Code: {candidate.range_code}
- Range Label: {candidate.range_label}
- Subrange Code: {candidate.subrange_code}
- Subrange Label: {candidate.subrange_label}
- Device Type Label: {candidate.devicetype_label}
- PL Services: {candidate.pl_services}
- Commercial Status: {candidate.commercial_status}
- End of Commercialisation: {candidate.end_of_commercialisation}
- Serviceable: {candidate.serviceable}
- Discovery Confidence: {candidate.confidence_score:.3f}
- Source: {candidate.source}
- Technical Specifications: {json.dumps(candidate.technical_specifications, indent=2)}
"""
            formatted_candidates.append(candidate_text.strip())
        
        return "\n\n".join(formatted_candidates)
    
    def _make_grok_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Make API call to Grok with full debugging"""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4096,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        if self.debug_mode:
            print("\n" + "="*100)
            print("🔍 GROK API CALL DEBUGGING")
            print("="*100)
            print(f"📤 MODEL: {self.model}")
            print(f"📤 SYSTEM PROMPT:")
            print("-" * 80)
            print(system_prompt)
            print("-" * 80)
            print(f"📤 USER PROMPT:")
            print("-" * 80)
            print(user_prompt)
            print("-" * 80)
            print(f"📤 PAYLOAD:")
            print(json.dumps(payload, indent=2))
            print("="*100)
        
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or not result['choices']:
                raise ValueError("No choices in API response")
            
            content = result['choices'][0]['message']['content']
            
            if self.debug_mode:
                print(f"📥 RAW GROK RESPONSE:")
                print("-" * 80)
                print(f"Full API Response: {json.dumps(result, indent=2)}")
                print("-" * 80)
                print(f"Content Only: {content}")
                print("="*100)
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Grok API call failed: {e}")
            if self.debug_mode:
                print(f"❌ API CALL FAILED: {e}")
                print("="*100)
            raise
    
    def match_products(self, letter_products: List[LetterProductInfo]) -> List[IntelligentMatchResult]:
        """
        Match letter products to database products using real data and intelligent AI reasoning
        """
        results = []
        
        for letter_product in letter_products:
            logger.info(f"🧠 Processing intelligent matching for: {letter_product.product_identifier}")
            
            # Get REAL discovered candidates from database
            discovered_candidates = self._get_real_discovered_candidates(letter_product)
            
            if not discovered_candidates:
                logger.warning(f"⚠️ No candidates found for {letter_product.product_identifier}")
                continue
            
            # Filter top candidates (limit to prevent prompt overflow)
            top_candidates = discovered_candidates[:10]  # Limit to top 10 candidates
            
            # Use Grok to intelligently match
            match_result = self._make_grok_call(letter_product, top_candidates)
            
            if match_result:
                results.append(match_result)
                logger.info(f"✅ Intelligent match completed for {letter_product.product_identifier}")
            else:
                logger.warning(f"⚠️ No intelligent match found for {letter_product.product_identifier}")
        
        return results
    
    def _make_grok_call(self, letter_product: LetterProductInfo, candidates: List[ProductCandidate]) -> Optional[IntelligentMatchResult]:
        """
        Make Grok API call to intelligently match letter product to candidates
        """
        start_time = time.time()
        
        try:
            # Format prompts
            system_prompt = self.prompt.get('system_prompt', '')
            
            # Format letter product info
            letter_info = self._format_letter_product_info(letter_product)
            
            # Format candidates
            candidates_info = self._format_discovered_candidates(candidates)
            
            # Build user prompt
            user_prompt = f"""
Please analyze the following obsolescence letter product and match it to the most likely product from the discovered candidates:

LETTER PRODUCT INFORMATION:
{letter_info}

DISCOVERED CANDIDATES FROM DATABASE:
{candidates_info}

Please provide a structured JSON response with your analysis and the best match.
"""
            
            # Make API call
            response = self._make_grok_api_call(system_prompt, user_prompt)
            
            # Parse response
            if response and 'product_identifier' in response:
                processing_time = (time.time() - start_time) * 1000
                
                return IntelligentMatchResult(
                    letter_product_id=letter_product.product_identifier,
                    matched_product_identifier=response.get('product_identifier'),
                    confidence=response.get('confidence', 0.0),
                    reason=response.get('reason', ''),
                    technical_match_score=response.get('technical_match_score', 0.0),
                    nomenclature_match_score=response.get('nomenclature_match_score', 0.0),
                    product_line_match_score=response.get('product_line_match_score', 0.0),
                    alternative_candidates=response.get('alternative_candidates', []),
                    processing_time_ms=processing_time,
                    grok_response=response
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Grok call failed: {e}")
            return None
    
    def _make_grok_api_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Make API call to Grok with full debugging"""
        
        try:
            # Combine system prompt with user prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.xai_service.generate_completion(
                prompt=full_prompt,
                document_content="",
                document_name="intelligent_matching"
            )
            
            if self.debug_mode:
                print("\n" + "="*100)
                print("🔍 GROK API CALL DEBUGGING")
                print("="*100)
                print(f"📤 SYSTEM PROMPT:")
                print("-" * 80)
                print(system_prompt)
                print("-" * 80)
                print(f"📤 USER PROMPT:")
                print("-" * 80)
                print(user_prompt)
                print("-" * 80)
                print(f"📥 RAW GROK RESPONSE:")
                print("-" * 80)
                print(f"Content: {response}")
                print("="*100)
            
            # Parse JSON response
            if isinstance(response, str):
                return json.loads(response)
            elif isinstance(response, dict):
                return response
            else:
                raise ValueError("Unexpected response format")
                
        except Exception as e:
            logger.error(f"Grok API call failed: {e}")
            if self.debug_mode:
                print(f"❌ API CALL FAILED: {e}")
                print("="*100)
            raise
    
    def process_pix2b_case(self) -> Dict[str, Any]:
        """Process PIX2B case using REAL data from database"""
        
        # Load grok_metadata.json
        grok_metadata_path = Path("data/output/json_outputs/PIX2B_Phase_out_Letter_22/latest/grok_metadata.json")
        
        try:
            with open(grok_metadata_path, 'r') as f:
                grok_metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load grok_metadata.json: {e}")
            return {"error": f"Failed to load grok_metadata.json: {e}"}
        
        # Extract letter products
        letter_products = []
        for product_data in grok_metadata.get('products', []):
            letter_product = LetterProductInfo(
                product_identifier=product_data.get('product_identifier', ''),
                range_label=product_data.get('range_label', ''),
                subrange_label=product_data.get('subrange_label'),
                product_line=product_data.get('product_line', ''),
                product_description=product_data.get('product_description', ''),
                technical_specifications=grok_metadata.get('technical_specifications', {}),
                obsolescence_status=product_data.get('obsolescence_status'),
                end_of_service_date=product_data.get('end_of_service_date'),
                replacement_suggestions=product_data.get('replacement_suggestions')
            )
            letter_products.append(letter_product)
        
        # Run intelligent matching using REAL database data
        results = self.match_products(letter_products)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'letter_product_id': result.letter_product_id,
                'matched_product_identifier': result.matched_product_identifier,
                'confidence': result.confidence,
                'reason': result.reason,
                'technical_match_score': result.technical_match_score,
                'nomenclature_match_score': result.nomenclature_match_score,
                'product_line_match_score': result.product_line_match_score,
                'alternative_candidates': result.alternative_candidates,
                'processing_time_ms': result.processing_time_ms
            })
        
        return {
            "letter_products_processed": len(letter_products),
            "matching_results": formatted_results,
            "total_processing_time_ms": sum(r.processing_time_ms for r in results),
            "average_confidence": sum(r.confidence for r in results) / len(results) if results else 0.0,
            "high_confidence_matches": len([r for r in results if r.confidence >= 0.8])
        }


def main():
    """Main function to test the intelligent product matching service"""
    
    logger.info("🚀 Testing Intelligent Product Matching Service")
    
    try:
        # Initialize service
        service = IntelligentProductMatchingService()
        
        # Process PIX2B case
        results = service.process_pix2b_case()
        
        # Display results
        print("\n" + "="*80)
        print("🤖 INTELLIGENT PRODUCT MATCHING RESULTS")
        print("="*80)
        
        print(f"📋 Letter Products Processed: {results.get('letter_products_processed', 0)}")
        print(f"⏱️  Total Processing Time: {results.get('total_processing_time_ms', 0):.2f}ms")
        print(f"🎯 Average Confidence: {results.get('average_confidence', 0):.2f}")
        print(f"🔥 High Confidence Matches: {results.get('high_confidence_matches', 0)}")
        
        print("\n📊 DETAILED MATCHING RESULTS:")
        for i, result in enumerate(results.get('matching_results', []), 1):
            print(f"\n{i}. Letter Product: {result['letter_product_id']}")
            print(f"   ✅ Matched Product: {result['matched_product_identifier']}")
            print(f"   🎯 Confidence: {result['confidence']:.3f}")
            print(f"   📝 Reason: {result['reason']}")
            print(f"   📈 Technical Match: {result['technical_match_score']:.3f}")
            print(f"   🏷️  Nomenclature Match: {result['nomenclature_match_score']:.3f}")
            print(f"   🔧 Product Line Match: {result['product_line_match_score']:.3f}")
            print(f"   🔄 Alternatives: {', '.join(result['alternative_candidates'])}")
            print(f"   ⏱️  Processing Time: {result['processing_time_ms']:.2f}ms")
        
        # Save results to file
        results_file = Path("scripts/sandbox/intelligent_matching_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 