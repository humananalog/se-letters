#!/usr/bin/env python3
"""
Product Mapping Service - CRITICAL NODE
Maps products from obsolescence letters to IBcatalogue database with smart search
Uses 3-level macro filters and hierarchical matching strategy

Author: SE Letters Team
Version: 1.0.0
Purpose: Critical node for accurate product identification
"""

import sys
from pathlib import Path
import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from fuzzywuzzy import fuzz
import re
from enum import Enum
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from se_letters.core.config import get_config
from loguru import logger


class MatchConfidence(Enum):
    """Match confidence levels"""
    EXACT = "exact"           # 95-100%
    HIGH = "high"            # 80-94%
    MEDIUM = "medium"        # 60-79%
    LOW = "low"              # 40-59%
    UNCERTAIN = "uncertain"   # 0-39%


@dataclass
class ProductCandidate:
    """A product candidate from IBcatalogue database"""
    product_identifier: str
    range_label: str
    subrange_label: Optional[str]
    product_description: str
    pl_services: str
    commercial_status: str
    brand_label: str
    bu_label: str
    
    # Matching details
    confidence_score: float
    confidence_level: MatchConfidence
    match_reasons: List[str]
    match_details: Dict[str, Any]
    
    # Additional fields
    end_of_commercialisation: Optional[str] = None
    end_of_service_date: Optional[str] = None
    devicetype_label: Optional[str] = None
    serviceable: Optional[str] = None


@dataclass
class LetterProduct:
    """Product from obsolescence letter"""
    letter_id: int
    product_identifier: str
    range_label: str
    subrange_label: Optional[str]
    product_line: str
    product_description: str
    obsolescence_status: Optional[str] = None
    end_of_service_date: Optional[str] = None


@dataclass
class MappingResult:
    """Result of product mapping operation"""
    letter_product: LetterProduct
    candidates: List[ProductCandidate]
    total_candidates: int
    best_match: Optional[ProductCandidate]
    mapping_success: bool
    mapping_time_ms: float
    search_strategy: str
    filters_applied: Dict[str, Any]


class ProductMappingService:
    """
    Critical service for mapping letter products to IBcatalogue database
    Uses intelligent 3-level macro filtering and hierarchical search
    """
    
    def __init__(self):
        """Initialize the product mapping service"""
        self.config = get_config()
        self.letter_db_path = "data/letters.duckdb"
        self.ibcatalogue_excel_path = "data/input/letters/IBcatalogue.xlsx"
        
        # Load IBcatalogue data (cached)
        self.ibcatalogue_df = None
        self._load_ibcatalogue()
        
        # Mapping configuration
        self.pl_services_mapping = {
            "SPIBS": "SPIBS",  # Secure Power
            "PPIBS": "PPIBS",  # Power Products  
            "DPIBS": "DPIBS",  # Digital Power
            "PSIBS": "PSIBS",  # Power Systems
            "IDIBS": "IDIBS",  # Industrial
            "IDPAS": "IDPAS"   # Industrial Process Automation
        }
        
        logger.info("🎯 Product Mapping Service initialized")
        logger.info(f"📊 IBcatalogue loaded: {len(self.ibcatalogue_df) if self.ibcatalogue_df is not None else 0} products")
    
    def _load_ibcatalogue(self):
        """Load IBcatalogue data into memory for fast searching"""
        try:
            logger.info("📂 Loading IBcatalogue database...")
            self.ibcatalogue_df = pd.read_excel(
                self.ibcatalogue_excel_path, 
                sheet_name='OIC_out'
            )
            
            # Clean and prepare data
            self.ibcatalogue_df = self.ibcatalogue_df.fillna('')
            
            # Create search-friendly columns
            self.ibcatalogue_df['search_text'] = (
                self.ibcatalogue_df['PRODUCT_IDENTIFIER'].astype(str) + ' ' +
                self.ibcatalogue_df['RANGE_LABEL'].astype(str) + ' ' +
                self.ibcatalogue_df['SUBRANGE_LABEL'].astype(str) + ' ' +
                self.ibcatalogue_df['PRODUCT_DESCRIPTION'].astype(str)
            ).str.upper()
            
            logger.info(f"✅ IBcatalogue loaded: {len(self.ibcatalogue_df)} products")
            
        except Exception as e:
            logger.error(f"❌ Failed to load IBcatalogue: {e}")
            self.ibcatalogue_df = None
    
    def map_letter_product_to_candidates(
        self, 
        letter_product: LetterProduct,
        max_candidates: int = 20
    ) -> MappingResult:
        """
        Map a letter product to IBcatalogue candidates using smart filtering
        
        Args:
            letter_product: Product from obsolescence letter
            max_candidates: Maximum candidates to return
            
        Returns:
            MappingResult with ranked candidates
        """
        import time
        start_time = time.time()
        
        if self.ibcatalogue_df is None:
            logger.error("❌ IBcatalogue not loaded")
            return MappingResult(
                letter_product=letter_product,
                candidates=[],
                total_candidates=0,
                best_match=None,
                mapping_success=False,
                mapping_time_ms=0,
                search_strategy="error",
                filters_applied={}
            )
        
        logger.info(f"🔍 Mapping product: {letter_product.product_identifier}")
        logger.info(f"📋 Letter details: {letter_product.range_label} | {letter_product.subrange_label} | {letter_product.product_line}")
        
        # Apply 3-level macro filtering strategy
        candidates_df = self._apply_macro_filters(letter_product)
        
        # Apply hierarchical search within filtered dataset
        scored_candidates = self._apply_hierarchical_search(
            letter_product, 
            candidates_df
        )
        
        # Rank and limit candidates
        final_candidates = self._rank_and_limit_candidates(
            scored_candidates, 
            max_candidates
        )
        
        # Determine best match
        best_match = final_candidates[0] if final_candidates else None
        mapping_success = best_match is not None and best_match.confidence_score >= 0.6
        
        mapping_time_ms = (time.time() - start_time) * 1000
        
        result = MappingResult(
            letter_product=letter_product,
            candidates=final_candidates,
            total_candidates=len(scored_candidates),
            best_match=best_match,
            mapping_success=mapping_success,
            mapping_time_ms=mapping_time_ms,
            search_strategy="3_level_macro_filter_hierarchical_search",
            filters_applied={
                "pl_services_filter": letter_product.product_line,
                "range_filter": letter_product.range_label,
                "subrange_filter": letter_product.subrange_label
            }
        )
        
        logger.info(f"✅ Mapping completed: {len(final_candidates)} candidates found")
        logger.info(f"⏱️ Processing time: {mapping_time_ms:.2f}ms")
        if best_match:
            logger.info(f"🎯 Best match: {best_match.product_identifier} (confidence: {best_match.confidence_score:.2f})")
        
        return result
    
    def _apply_macro_filters(self, letter_product: LetterProduct) -> pd.DataFrame:
        """
        Apply 3-level macro filtering strategy:
        1. PL_SERVICES filter (product line)
        2. RANGE_LABEL filter 
        3. SUBRANGE/identifier filter
        """
        df = self.ibcatalogue_df.copy()
        original_count = len(df)
        
        # Level 1: PL_SERVICES filter (macro filter)
        pl_services = self.pl_services_mapping.get(letter_product.product_line)
        if pl_services:
            df = df[df['PL_SERVICES'] == pl_services]
            logger.info(f"🔄 Level 1 - PL_SERVICES filter ({pl_services}): {len(df)}/{original_count} products")
        
        # Level 2: RANGE_LABEL filter (range matching)
        if letter_product.range_label:
            range_pattern = letter_product.range_label.upper()
            
            # Try exact match first
            exact_match = df[df['RANGE_LABEL'].str.upper() == range_pattern]
            if len(exact_match) > 0:
                df = exact_match
                logger.info(f"🔄 Level 2a - Exact range match ({range_pattern}): {len(df)} products")
            else:
                # Try contains match
                contains_match = df[df['RANGE_LABEL'].str.upper().str.contains(range_pattern, na=False)]
                if len(contains_match) > 0:
                    df = contains_match
                    logger.info(f"🔄 Level 2b - Range contains match ({range_pattern}): {len(df)} products")
                else:
                    # Try partial matching (remove common words)
                    clean_range = re.sub(r'\b(UPS|SYSTEM|POWER|ELECTRIC)\b', '', range_pattern).strip()
                    if clean_range:
                        partial_match = df[df['RANGE_LABEL'].str.upper().str.contains(clean_range, na=False)]
                        if len(partial_match) > 0:
                            df = partial_match
                            logger.info(f"🔄 Level 2c - Range partial match ({clean_range}): {len(df)} products")
        
        # Level 3: SUBRANGE/identifier filter (specific matching)
        if letter_product.subrange_label and len(df) > 50:  # Only if we have too many candidates
            subrange_pattern = letter_product.subrange_label.upper()
            
            # Try subrange match
            subrange_match = df[df['SUBRANGE_LABEL'].str.upper().str.contains(subrange_pattern, na=False)]
            if len(subrange_match) > 0:
                df = subrange_match
                logger.info(f"🔄 Level 3a - Subrange match ({subrange_pattern}): {len(df)} products")
            else:
                # Try identifier match
                identifier_match = df[df['PRODUCT_IDENTIFIER'].str.upper().str.contains(subrange_pattern, na=False)]
                if len(identifier_match) > 0:
                    df = identifier_match
                    logger.info(f"🔄 Level 3b - Identifier match ({subrange_pattern}): {len(df)} products")
                else:
                    # Try description match
                    desc_match = df[df['PRODUCT_DESCRIPTION'].str.upper().str.contains(subrange_pattern, na=False)]
                    if len(desc_match) > 0:
                        df = desc_match
                        logger.info(f"🔄 Level 3c - Description match ({subrange_pattern}): {len(df)} products")
        
        reduction_percentage = ((original_count - len(df)) / original_count) * 100
        logger.info(f"📊 Search space reduction: {reduction_percentage:.1f}% ({original_count} → {len(df)})")
        
        return df
    
    def _apply_hierarchical_search(
        self, 
        letter_product: LetterProduct, 
        candidates_df: pd.DataFrame
    ) -> List[ProductCandidate]:
        """
        Apply hierarchical search within filtered candidates
        """
        scored_candidates = []
        
        for _, row in candidates_df.iterrows():
            candidate = self._create_candidate_from_row(row)
            
            # Calculate confidence score using multiple factors
            confidence_score = self._calculate_confidence_score(
                letter_product, 
                candidate
            )
            
            # Get match reasons
            match_reasons = self._get_match_reasons(
                letter_product, 
                candidate, 
                confidence_score
            )
            
            # Set confidence level
            confidence_level = self._get_confidence_level(confidence_score)
            
            # Update candidate with scoring results
            candidate.confidence_score = confidence_score
            candidate.confidence_level = confidence_level
            candidate.match_reasons = match_reasons
            candidate.match_details = {
                "range_similarity": self._calculate_string_similarity(
                    letter_product.range_label, 
                    candidate.range_label
                ),
                "identifier_similarity": self._calculate_string_similarity(
                    letter_product.product_identifier, 
                    candidate.product_identifier
                ),
                "description_similarity": self._calculate_string_similarity(
                    letter_product.product_description, 
                    candidate.product_description
                )
            }
            
            scored_candidates.append(candidate)
        
        return scored_candidates
    
    def _create_candidate_from_row(self, row: pd.Series) -> ProductCandidate:
        """Create ProductCandidate from DataFrame row"""
        return ProductCandidate(
            product_identifier=str(row.get('PRODUCT_IDENTIFIER', '')),
            range_label=str(row.get('RANGE_LABEL', '')),
            subrange_label=str(row.get('SUBRANGE_LABEL', '')) if row.get('SUBRANGE_LABEL') else None,
            product_description=str(row.get('PRODUCT_DESCRIPTION', '')),
            pl_services=str(row.get('PL_SERVICES', '')),
            commercial_status=str(row.get('COMMERCIAL_STATUS', '')),
            brand_label=str(row.get('BRAND_LABEL', '')),
            bu_label=str(row.get('BU_LABEL', '')),
            end_of_commercialisation=str(row.get('END_OF_COMMERCIALISATION', '')) if row.get('END_OF_COMMERCIALISATION') else None,
            end_of_service_date=str(row.get('END_OF_SERVICE_DATE', '')) if row.get('END_OF_SERVICE_DATE') else None,
            devicetype_label=str(row.get('DEVICETYPE_LABEL', '')) if row.get('DEVICETYPE_LABEL') else None,
            serviceable=str(row.get('SERVICEABLE', '')) if row.get('SERVICEABLE') else None,
            confidence_score=0.0,
            confidence_level=MatchConfidence.UNCERTAIN,
            match_reasons=[],
            match_details={}
        )
    
    def _calculate_confidence_score(
        self, 
        letter_product: LetterProduct, 
        candidate: ProductCandidate
    ) -> float:
        """
        Calculate confidence score using weighted factors
        """
        factors = {}
        
        # 1. Range similarity (30% weight)
        range_sim = self._calculate_string_similarity(
            letter_product.range_label, 
            candidate.range_label
        )
        factors['range_similarity'] = range_sim * 0.30
        
        # 2. Identifier similarity (25% weight)
        identifier_sim = self._calculate_string_similarity(
            letter_product.product_identifier, 
            candidate.product_identifier
        )
        factors['identifier_similarity'] = identifier_sim * 0.25
        
        # 3. Subrange similarity (20% weight)
        if letter_product.subrange_label and candidate.subrange_label:
            subrange_sim = self._calculate_string_similarity(
                letter_product.subrange_label, 
                candidate.subrange_label
            )
        else:
            subrange_sim = 0.5  # Neutral score if missing
        factors['subrange_similarity'] = subrange_sim * 0.20
        
        # 4. Description similarity (15% weight)
        desc_sim = self._calculate_string_similarity(
            letter_product.product_description, 
            candidate.product_description
        )
        factors['description_similarity'] = desc_sim * 0.15
        
        # 5. Product line match (10% weight)
        pl_match = 1.0 if letter_product.product_line == candidate.pl_services else 0.0
        factors['product_line_match'] = pl_match * 0.10
        
        # Calculate final score
        confidence_score = sum(factors.values())
        
        # Apply bonuses for exact matches
        if letter_product.range_label.upper() == candidate.range_label.upper():
            confidence_score += 0.05  # Exact range bonus
        
        if letter_product.subrange_label and candidate.subrange_label:
            if letter_product.subrange_label.upper() == candidate.subrange_label.upper():
                confidence_score += 0.05  # Exact subrange bonus
        
        # Ensure score is between 0 and 1
        confidence_score = min(max(confidence_score, 0.0), 1.0)
        
        return confidence_score
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using fuzzy matching"""
        if not str1 or not str2:
            return 0.0
        
        # Use token sort ratio for better matching
        similarity = fuzz.token_sort_ratio(str1.upper(), str2.upper()) / 100.0
        return similarity
    
    def _get_confidence_level(self, score: float) -> MatchConfidence:
        """Get confidence level based on score"""
        if score >= 0.95:
            return MatchConfidence.EXACT
        elif score >= 0.80:
            return MatchConfidence.HIGH
        elif score >= 0.60:
            return MatchConfidence.MEDIUM
        elif score >= 0.40:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.UNCERTAIN
    
    def _get_match_reasons(
        self, 
        letter_product: LetterProduct, 
        candidate: ProductCandidate, 
        confidence_score: float
    ) -> List[str]:
        """Get human-readable match reasons"""
        reasons = []
        
        # Range matching
        range_sim = self._calculate_string_similarity(
            letter_product.range_label, 
            candidate.range_label
        )
        if range_sim >= 0.90:
            reasons.append(f"Exact range match: {letter_product.range_label} = {candidate.range_label}")
        elif range_sim >= 0.70:
            reasons.append(f"High range similarity: {letter_product.range_label} ~ {candidate.range_label}")
        
        # Subrange matching
        if letter_product.subrange_label and candidate.subrange_label:
            subrange_sim = self._calculate_string_similarity(
                letter_product.subrange_label, 
                candidate.subrange_label
            )
            if subrange_sim >= 0.90:
                reasons.append(f"Exact subrange match: {letter_product.subrange_label} = {candidate.subrange_label}")
        
        # Product line match
        if letter_product.product_line == candidate.pl_services:
            reasons.append(f"Product line match: {letter_product.product_line}")
        
        # Commercial status
        if candidate.commercial_status:
            if "commercialised" in candidate.commercial_status.lower():
                reasons.append("Currently commercialized")
            elif "end" in candidate.commercial_status.lower():
                reasons.append("End of commercialization")
        
        return reasons
    
    def _rank_and_limit_candidates(
        self, 
        candidates: List[ProductCandidate], 
        max_candidates: int
    ) -> List[ProductCandidate]:
        """Rank candidates by confidence score and limit results"""
        # Sort by confidence score (descending)
        ranked_candidates = sorted(
            candidates, 
            key=lambda x: x.confidence_score, 
            reverse=True
        )
        
        # Limit to max candidates
        limited_candidates = ranked_candidates[:max_candidates]
        
        return limited_candidates
    
    def get_letter_product_by_id(self, letter_id: int, product_id: int = None) -> Optional[LetterProduct]:
        """Get letter product from database"""
        try:
            with duckdb.connect(self.letter_db_path) as conn:
                if product_id:
                    # Get specific product
                    result = conn.execute("""
                        SELECT letter_id, product_identifier, range_label, subrange_label,
                               product_line, product_description, obsolescence_status,
                               end_of_service_date
                        FROM letter_products 
                        WHERE letter_id = ? AND id = ?
                    """, [letter_id, product_id]).fetchone()
                else:
                    # Get first product from letter
                    result = conn.execute("""
                        SELECT letter_id, product_identifier, range_label, subrange_label,
                               product_line, product_description, obsolescence_status,
                               end_of_service_date
                        FROM letter_products 
                        WHERE letter_id = ?
                        LIMIT 1
                    """, [letter_id]).fetchone()
                
                if result:
                    return LetterProduct(
                        letter_id=result[0],
                        product_identifier=result[1] or "",
                        range_label=result[2] or "",
                        subrange_label=result[3],
                        product_line=result[4] or "",
                        product_description=result[5] or "",
                        obsolescence_status=result[6],
                        end_of_service_date=result[7]
                    )
                
        except Exception as e:
            logger.error(f"❌ Error getting letter product: {e}")
        
        return None
    
    def export_mapping_result_to_json(self, result: MappingResult, output_path: str = None) -> str:
        """Export mapping result to JSON file"""
        if not output_path:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"scripts/sandbox/mapping_result_{timestamp}.json"
        
        # Convert result to dictionary
        result_dict = {
            "letter_product": asdict(result.letter_product),
            "candidates": [asdict(candidate) for candidate in result.candidates],
            "total_candidates": result.total_candidates,
            "best_match": asdict(result.best_match) if result.best_match else None,
            "mapping_success": result.mapping_success,
            "mapping_time_ms": result.mapping_time_ms,
            "search_strategy": result.search_strategy,
            "filters_applied": result.filters_applied
        }
        
        # Handle enum serialization
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif isinstance(obj, MatchConfidence):
                return obj.value
            return obj
        
        result_dict = convert_enums(result_dict)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Mapping result exported to: {output_path}")
        return output_path


def test_galaxy_6000_mapping():
    """Test the mapping service with Galaxy 6000 case"""
    logger.info("🧪 Testing Galaxy 6000 Product Mapping")
    
    # Initialize service
    mapping_service = ProductMappingService()
    
    # Get Galaxy 6000 letter product (ID=21 from exploration)
    letter_product = mapping_service.get_letter_product_by_id(21)
    
    if not letter_product:
        logger.error("❌ Could not find Galaxy 6000 letter product")
        return
    
    logger.info(f"📋 Testing with: {letter_product.product_identifier}")
    
    # Perform mapping
    result = mapping_service.map_letter_product_to_candidates(
        letter_product, 
        max_candidates=10
    )
    
    # Display results
    logger.info(f"\n🎯 MAPPING RESULTS:")
    logger.info(f"✅ Success: {result.mapping_success}")
    logger.info(f"📊 Total candidates: {result.total_candidates}")
    logger.info(f"⏱️ Processing time: {result.mapping_time_ms:.2f}ms")
    
    if result.best_match:
        logger.info(f"\n🏆 BEST MATCH:")
        logger.info(f"   Product: {result.best_match.product_identifier}")
        logger.info(f"   Range: {result.best_match.range_label}")
        logger.info(f"   Subrange: {result.best_match.subrange_label}")
        logger.info(f"   Description: {result.best_match.product_description}")
        logger.info(f"   Confidence: {result.best_match.confidence_score:.2f} ({result.best_match.confidence_level.value})")
        logger.info(f"   Status: {result.best_match.commercial_status}")
        logger.info(f"   Reasons: {', '.join(result.best_match.match_reasons)}")
    
    # Show top candidates
    logger.info(f"\n📋 TOP CANDIDATES:")
    for i, candidate in enumerate(result.candidates[:5], 1):
        logger.info(f"   {i}. {candidate.product_identifier} | "
                   f"{candidate.range_label} | "
                   f"Confidence: {candidate.confidence_score:.2f}")
    
    # Export results
    output_path = mapping_service.export_mapping_result_to_json(result)
    logger.info(f"📄 Results saved to: {output_path}")
    
    return result


if __name__ == "__main__":
    test_galaxy_6000_mapping() 