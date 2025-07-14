#!/usr/bin/env python3
"""
Enhanced Product Mapping Service v2 - CRITICAL NODE
Improved confidence scoring for better semantic matching
Maps products from obsolescence letters to IBcatalogue database

Author: SE Letters Team
Version: 2.0.0
Purpose: Enhanced semantic matching for product identification
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
    EXACT = "exact"           # 90-100%
    HIGH = "high"            # 75-89%
    MEDIUM = "medium"        # 60-74%
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


class EnhancedProductMappingService:
    """
    Enhanced product mapping service with improved semantic matching
    """
    
    def __init__(self):
        """Initialize the enhanced product mapping service"""
        self.config = get_config()
        self.letter_db_path = "data/letters.duckdb"
        self.ibcatalogue_excel_path = "data/input/letters/IBcatalogue.xlsx"
        
        # Load IBcatalogue data (cached)
        self.ibcatalogue_df = None
        self._load_ibcatalogue()
        
        # Enhanced mapping configuration
        self.pl_services_mapping = {
            "SPIBS": "SPIBS",  # Secure Power
            "PPIBS": "PPIBS",  # Power Products  
            "DPIBS": "DPIBS",  # Digital Power
            "PSIBS": "PSIBS",  # Power Systems
            "IDIBS": "IDIBS",  # Industrial
            "IDPAS": "IDPAS"   # Industrial Process Automation
        }
        
        # Semantic matching patterns
        self.semantic_patterns = {
            "galaxy": {
                "range_variants": ["galaxy", "mge galaxy", "mge galaxy 6000"],
                "identifier_patterns": [r"galaxy.*6000", r"6000.*galaxy", r"gala.*6000"],
                "description_patterns": [r"galaxy.*6000", r"mge.*galaxy.*6000"]
            },
            "sepam": {
                "range_variants": ["sepam", "micom", "powerlogic"],
                "identifier_patterns": [r"sepam.*\d+", r"micom.*\d+"],
                "description_patterns": [r"sepam.*\d+", r"protection.*relay"]
            }
        }
        
        logger.info("🚀 Enhanced Product Mapping Service v2 initialized")
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
            
            # Create enhanced search columns
            self.ibcatalogue_df['search_text'] = (
                self.ibcatalogue_df['PRODUCT_IDENTIFIER'].astype(str) + ' ' +
                self.ibcatalogue_df['RANGE_LABEL'].astype(str) + ' ' +
                self.ibcatalogue_df['SUBRANGE_LABEL'].astype(str) + ' ' +
                self.ibcatalogue_df['PRODUCT_DESCRIPTION'].astype(str)
            ).str.upper()
            
            # Create normalized columns for better matching
            self.ibcatalogue_df['normalized_range'] = self.ibcatalogue_df['RANGE_LABEL'].str.upper().str.strip()
            self.ibcatalogue_df['normalized_desc'] = self.ibcatalogue_df['PRODUCT_DESCRIPTION'].str.upper().str.strip()
            
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
        Enhanced mapping with improved semantic matching
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
        
        logger.info(f"🔍 Enhanced mapping for: {letter_product.product_identifier}")
        logger.info(f"📋 Letter details: {letter_product.range_label} | {letter_product.subrange_label} | {letter_product.product_line}")
        
        # Apply enhanced macro filtering
        candidates_df = self._apply_enhanced_macro_filters(letter_product)
        
        # Apply enhanced semantic search
        scored_candidates = self._apply_enhanced_semantic_search(
            letter_product, 
            candidates_df
        )
        
        # Rank with enhanced scoring
        final_candidates = self._rank_and_limit_candidates(
            scored_candidates, 
            max_candidates
        )
        
        # Determine best match with improved threshold
        best_match = final_candidates[0] if final_candidates else None
        mapping_success = best_match is not None and best_match.confidence_score >= 0.50  # Lowered threshold
        
        mapping_time_ms = (time.time() - start_time) * 1000
        
        result = MappingResult(
            letter_product=letter_product,
            candidates=final_candidates,
            total_candidates=len(scored_candidates),
            best_match=best_match,
            mapping_success=mapping_success,
            mapping_time_ms=mapping_time_ms,
            search_strategy="enhanced_semantic_matching_v2",
            filters_applied={
                "pl_services_filter": letter_product.product_line,
                "range_filter": letter_product.range_label,
                "subrange_filter": letter_product.subrange_label,
                "semantic_patterns_applied": True
            }
        )
        
        logger.info(f"✅ Enhanced mapping completed: {len(final_candidates)} candidates found")
        logger.info(f"⏱️ Processing time: {mapping_time_ms:.2f}ms")
        if best_match:
            logger.info(f"🎯 Best match: {best_match.product_identifier} (confidence: {best_match.confidence_score:.2f})")
        
        return result
    
    def _apply_enhanced_macro_filters(self, letter_product: LetterProduct) -> pd.DataFrame:
        """Enhanced macro filtering with better pattern matching"""
        df = self.ibcatalogue_df.copy()
        original_count = len(df)
        
        # Level 1: PL_SERVICES filter
        pl_services = self.pl_services_mapping.get(letter_product.product_line)
        if pl_services:
            df = df[df['PL_SERVICES'] == pl_services]
            logger.info(f"🔄 Level 1 - PL_SERVICES filter ({pl_services}): {len(df)}/{original_count} products")
        
        # Level 2: Enhanced range matching
        if letter_product.range_label:
            df = self._apply_enhanced_range_filter(df, letter_product.range_label)
        
        # Level 3: Enhanced subrange/identifier matching
        if letter_product.subrange_label and len(df) > 100:
            df = self._apply_enhanced_subrange_filter(df, letter_product)
        
        reduction_percentage = ((original_count - len(df)) / original_count) * 100
        logger.info(f"📊 Enhanced search space reduction: {reduction_percentage:.1f}% ({original_count} → {len(df)})")
        
        return df
    
    def _apply_enhanced_range_filter(self, df: pd.DataFrame, range_label: str) -> pd.DataFrame:
        """Enhanced range filtering with semantic patterns"""
        range_upper = range_label.upper().strip()
        
        # Check for known semantic patterns
        range_key = range_upper.lower()
        if range_key in self.semantic_patterns:
            patterns = self.semantic_patterns[range_key]
            
            # Try each range variant
            for variant in patterns["range_variants"]:
                variant_match = df[df['normalized_range'].str.contains(variant.upper(), na=False)]
                if len(variant_match) > 0:
                    logger.info(f"🔄 Level 2 - Semantic range match ({variant}): {len(variant_match)} products")
                    return variant_match
        
        # Fallback to standard matching
        # Try exact match
        exact_match = df[df['normalized_range'] == range_upper]
        if len(exact_match) > 0:
            logger.info(f"🔄 Level 2a - Exact range match ({range_upper}): {len(exact_match)} products")
            return exact_match
        
        # Try contains match
        contains_match = df[df['normalized_range'].str.contains(range_upper, na=False)]
        if len(contains_match) > 0:
            logger.info(f"🔄 Level 2b - Range contains match ({range_upper}): {len(contains_match)} products")
            return contains_match
        
        # Try partial matching
        clean_range = re.sub(r'\b(UPS|SYSTEM|POWER|ELECTRIC)\b', '', range_upper).strip()
        if clean_range and clean_range != range_upper:
            partial_match = df[df['normalized_range'].str.contains(clean_range, na=False)]
            if len(partial_match) > 0:
                logger.info(f"🔄 Level 2c - Range partial match ({clean_range}): {len(partial_match)} products")
                return partial_match
        
        return df
    
    def _apply_enhanced_subrange_filter(self, df: pd.DataFrame, letter_product: LetterProduct) -> pd.DataFrame:
        """Enhanced subrange filtering with semantic matching"""
        subrange_pattern = letter_product.subrange_label.upper()
        
        # Check for semantic patterns in descriptions
        range_key = letter_product.range_label.lower()
        if range_key in self.semantic_patterns:
            patterns = self.semantic_patterns[range_key]
            
            # Try description patterns
            for pattern in patterns["description_patterns"]:
                desc_match = df[df['normalized_desc'].str.contains(pattern, case=False, na=False)]
                if len(desc_match) > 0:
                    logger.info(f"🔄 Level 3a - Semantic description match ({pattern}): {len(desc_match)} products")
                    return desc_match
        
        # Standard subrange matching
        subrange_match = df[df['SUBRANGE_LABEL'].str.upper().str.contains(subrange_pattern, na=False)]
        if len(subrange_match) > 0:
            logger.info(f"🔄 Level 3b - Subrange match ({subrange_pattern}): {len(subrange_match)} products")
            return subrange_match
        
        # Try identifier match
        identifier_match = df[df['PRODUCT_IDENTIFIER'].str.upper().str.contains(subrange_pattern, na=False)]
        if len(identifier_match) > 0:
            logger.info(f"🔄 Level 3c - Identifier match ({subrange_pattern}): {len(identifier_match)} products")
            return identifier_match
        
        # Try description match
        desc_match = df[df['normalized_desc'].str.contains(subrange_pattern, na=False)]
        if len(desc_match) > 0:
            logger.info(f"🔄 Level 3d - Description match ({subrange_pattern}): {len(desc_match)} products")
            return desc_match
        
        return df
    
    def _apply_enhanced_semantic_search(
        self, 
        letter_product: LetterProduct, 
        candidates_df: pd.DataFrame
    ) -> List[ProductCandidate]:
        """Enhanced semantic search with improved scoring"""
        scored_candidates = []
        
        for _, row in candidates_df.iterrows():
            candidate = self._create_candidate_from_row(row)
            
            # Calculate enhanced confidence score
            confidence_score = self._calculate_enhanced_confidence_score(
                letter_product, 
                candidate
            )
            
            # Get enhanced match reasons
            match_reasons = self._get_enhanced_match_reasons(
                letter_product, 
                candidate, 
                confidence_score
            )
            
            # Set confidence level with adjusted thresholds
            confidence_level = self._get_enhanced_confidence_level(confidence_score)
            
            # Update candidate with enhanced scoring results
            candidate.confidence_score = confidence_score
            candidate.confidence_level = confidence_level
            candidate.match_reasons = match_reasons
            candidate.match_details = {
                "range_similarity": self._calculate_enhanced_string_similarity(
                    letter_product.range_label, 
                    candidate.range_label
                ),
                "identifier_similarity": self._calculate_enhanced_string_similarity(
                    letter_product.product_identifier, 
                    candidate.product_identifier
                ),
                "description_similarity": self._calculate_enhanced_string_similarity(
                    letter_product.product_description, 
                    candidate.product_description
                ),
                "semantic_match_score": self._calculate_semantic_match_score(
                    letter_product,
                    candidate
                )
            }
            
            scored_candidates.append(candidate)
        
        return scored_candidates
    
    def _calculate_enhanced_confidence_score(
        self, 
        letter_product: LetterProduct, 
        candidate: ProductCandidate
    ) -> float:
        """Enhanced confidence scoring with semantic awareness"""
        factors = {}
        
        # 1. Semantic range matching (35% weight - increased)
        semantic_range_score = self._calculate_semantic_range_score(
            letter_product.range_label,
            candidate.range_label
        )
        factors['semantic_range'] = semantic_range_score * 0.35
        
        # 2. Content similarity (30% weight - increased)
        content_score = self._calculate_content_similarity_score(
            letter_product,
            candidate
        )
        factors['content_similarity'] = content_score * 0.30
        
        # 3. Identifier matching (15% weight - decreased)
        identifier_sim = self._calculate_enhanced_string_similarity(
            letter_product.product_identifier, 
            candidate.product_identifier
        )
        factors['identifier_similarity'] = identifier_sim * 0.15
        
        # 4. Product line match (10% weight)
        pl_match = 1.0 if letter_product.product_line == candidate.pl_services else 0.0
        factors['product_line_match'] = pl_match * 0.10
        
        # 5. Subrange/model matching (10% weight)
        subrange_score = self._calculate_subrange_match_score(
            letter_product,
            candidate
        )
        factors['subrange_match'] = subrange_score * 0.10
        
        # Calculate base score
        confidence_score = sum(factors.values())
        
        # Apply semantic bonuses
        semantic_bonus = self._calculate_semantic_bonus(letter_product, candidate)
        confidence_score += semantic_bonus
        
        # Ensure score is between 0 and 1
        confidence_score = min(max(confidence_score, 0.0), 1.0)
        
        return confidence_score
    
    def _calculate_semantic_range_score(self, letter_range: str, candidate_range: str) -> float:
        """Calculate semantic range similarity"""
        letter_range_lower = letter_range.lower().strip()
        candidate_range_lower = candidate_range.lower().strip()
        
        # Check for known semantic equivalences
        if letter_range_lower == "galaxy":
            if "galaxy" in candidate_range_lower or "mge galaxy" in candidate_range_lower:
                return 1.0  # Perfect semantic match
        
        # Use enhanced string similarity
        return self._calculate_enhanced_string_similarity(letter_range, candidate_range)
    
    def _calculate_content_similarity_score(self, letter_product: LetterProduct, candidate: ProductCandidate) -> float:
        """Calculate content-based similarity"""
        scores = []
        
        # Check for key terms in descriptions
        letter_desc = letter_product.product_description.upper()
        candidate_desc = candidate.product_description.upper()
        
        # UPS systems
        if "UPS" in letter_desc or "UNINTERRUPTIBLE" in letter_desc:
            if "UPS" in candidate_desc or "GALAXY" in candidate_desc:
                scores.append(0.8)
        
        # Model numbers
        if letter_product.subrange_label:
            model_num = letter_product.subrange_label.upper()
            if model_num in candidate_desc or model_num in candidate.product_identifier.upper():
                scores.append(0.9)
        
        # Power ratings
        power_patterns = re.findall(r'\d+\s*k?[wva]', letter_desc.lower())
        if power_patterns:
            for pattern in power_patterns:
                if pattern in candidate_desc.lower():
                    scores.append(0.7)
        
        # Description similarity
        desc_sim = self._calculate_enhanced_string_similarity(letter_desc, candidate_desc)
        scores.append(desc_sim)
        
        return max(scores) if scores else 0.0
    
    def _calculate_subrange_match_score(self, letter_product: LetterProduct, candidate: ProductCandidate) -> float:
        """Calculate subrange/model matching score"""
        if not letter_product.subrange_label:
            return 0.5  # Neutral if no subrange
        
        subrange = letter_product.subrange_label.upper()
        
        # Check in candidate subrange
        if candidate.subrange_label and subrange in candidate.subrange_label.upper():
            return 1.0
        
        # Check in candidate identifier
        if subrange in candidate.product_identifier.upper():
            return 0.9
        
        # Check in candidate description
        if subrange in candidate.product_description.upper():
            return 0.8
        
        # Fuzzy match
        if candidate.subrange_label:
            sim = self._calculate_enhanced_string_similarity(subrange, candidate.subrange_label)
            return sim
        
        return 0.0
    
    def _calculate_semantic_bonus(self, letter_product: LetterProduct, candidate: ProductCandidate) -> float:
        """Calculate semantic bonus for known patterns"""
        bonus = 0.0
        
        # Galaxy 6000 specific bonus
        if (letter_product.range_label.lower() == "galaxy" and 
            letter_product.subrange_label == "6000"):
            
            if ("galaxy" in candidate.range_label.lower() and 
                "6000" in candidate.product_description):
                bonus += 0.15  # Strong semantic match bonus
        
        # UPS system bonus
        if "ups" in letter_product.product_description.lower():
            if ("ups" in candidate.product_description.lower() or 
                "galaxy" in candidate.range_label.lower()):
                bonus += 0.05
        
        return bonus
    
    def _calculate_semantic_match_score(self, letter_product: LetterProduct, candidate: ProductCandidate) -> float:
        """Calculate overall semantic match score"""
        semantic_indicators = []
        
        # Range semantic match
        range_semantic = self._calculate_semantic_range_score(
            letter_product.range_label,
            candidate.range_label
        )
        semantic_indicators.append(range_semantic)
        
        # Content semantic match
        content_semantic = self._calculate_content_similarity_score(letter_product, candidate)
        semantic_indicators.append(content_semantic)
        
        # Product line match
        pl_match = 1.0 if letter_product.product_line == candidate.pl_services else 0.0
        semantic_indicators.append(pl_match)
        
        return sum(semantic_indicators) / len(semantic_indicators)
    
    def _calculate_enhanced_string_similarity(self, str1: str, str2: str) -> float:
        """Enhanced string similarity calculation"""
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1 = str1.upper().strip()
        s2 = str2.upper().strip()
        
        # Use multiple similarity metrics and take the best
        similarities = [
            fuzz.ratio(s1, s2) / 100.0,
            fuzz.partial_ratio(s1, s2) / 100.0,
            fuzz.token_sort_ratio(s1, s2) / 100.0,
            fuzz.token_set_ratio(s1, s2) / 100.0
        ]
        
        return max(similarities)
    
    def _get_enhanced_confidence_level(self, score: float) -> MatchConfidence:
        """Enhanced confidence level determination"""
        if score >= 0.90:
            return MatchConfidence.EXACT
        elif score >= 0.75:
            return MatchConfidence.HIGH
        elif score >= 0.60:
            return MatchConfidence.MEDIUM
        elif score >= 0.40:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.UNCERTAIN
    
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
    
    def _get_enhanced_match_reasons(
        self, 
        letter_product: LetterProduct, 
        candidate: ProductCandidate, 
        confidence_score: float
    ) -> List[str]:
        """Get enhanced match reasons"""
        reasons = []
        
        # Semantic range matching
        if "galaxy" in letter_product.range_label.lower() and "galaxy" in candidate.range_label.lower():
            reasons.append(f"Semantic range match: {letter_product.range_label} ↔ {candidate.range_label}")
        
        # Model/subrange matching
        if (letter_product.subrange_label and 
            letter_product.subrange_label.upper() in candidate.product_description.upper()):
            reasons.append(f"Model number in description: {letter_product.subrange_label}")
        
        # Product line match
        if letter_product.product_line == candidate.pl_services:
            reasons.append(f"Product line match: {letter_product.product_line}")
        
        # Commercial status
        if candidate.commercial_status:
            if "commercialised" in candidate.commercial_status.lower():
                reasons.append("Currently commercialized")
            elif "end" in candidate.commercial_status.lower():
                reasons.append("End of commercialization")
        
        # High confidence indicator
        if confidence_score >= 0.75:
            reasons.append("High semantic confidence")
        
        return reasons
    
    def _rank_and_limit_candidates(
        self, 
        candidates: List[ProductCandidate], 
        max_candidates: int
    ) -> List[ProductCandidate]:
        """Rank candidates by enhanced confidence score"""
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
            output_path = f"scripts/sandbox/enhanced_mapping_result_{timestamp}.json"
        
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
        
        logger.info(f"📄 Enhanced mapping result exported to: {output_path}")
        return output_path


def test_enhanced_galaxy_6000_mapping():
    """Test the enhanced mapping service with Galaxy 6000 case"""
    logger.info("🧪 Testing Enhanced Galaxy 6000 Product Mapping v2")
    
    # Initialize enhanced service
    mapping_service = EnhancedProductMappingService()
    
    # Get Galaxy 6000 letter product (ID=21 from exploration)
    letter_product = mapping_service.get_letter_product_by_id(21)
    
    if not letter_product:
        logger.error("❌ Could not find Galaxy 6000 letter product")
        return
    
    logger.info(f"📋 Testing enhanced mapping with: {letter_product.product_identifier}")
    
    # Perform enhanced mapping
    result = mapping_service.map_letter_product_to_candidates(
        letter_product, 
        max_candidates=10
    )
    
    # Display enhanced results
    logger.info(f"\n🎯 ENHANCED MAPPING RESULTS:")
    logger.info(f"✅ Success: {result.mapping_success}")
    logger.info(f"📊 Total candidates: {result.total_candidates}")
    logger.info(f"⏱️ Processing time: {result.mapping_time_ms:.2f}ms")
    logger.info(f"🔍 Strategy: {result.search_strategy}")
    
    if result.best_match:
        logger.info(f"\n🏆 BEST MATCH (ENHANCED):")
        logger.info(f"   Product: {result.best_match.product_identifier}")
        logger.info(f"   Range: {result.best_match.range_label}")
        logger.info(f"   Subrange: {result.best_match.subrange_label}")
        logger.info(f"   Description: {result.best_match.product_description}")
        logger.info(f"   Confidence: {result.best_match.confidence_score:.2f} ({result.best_match.confidence_level.value})")
        logger.info(f"   Status: {result.best_match.commercial_status}")
        logger.info(f"   Brand: {result.best_match.brand_label}")
        logger.info(f"   Reasons: {', '.join(result.best_match.match_reasons)}")
        
        # Show enhanced match details
        details = result.best_match.match_details
        logger.info(f"\n📊 ENHANCED MATCH DETAILS:")
        logger.info(f"   Range similarity: {details.get('range_similarity', 0):.2f}")
        logger.info(f"   Identifier similarity: {details.get('identifier_similarity', 0):.2f}")
        logger.info(f"   Description similarity: {details.get('description_similarity', 0):.2f}")
        logger.info(f"   Semantic match score: {details.get('semantic_match_score', 0):.2f}")
    
    # Show top enhanced candidates
    logger.info(f"\n📋 TOP ENHANCED CANDIDATES:")
    for i, candidate in enumerate(result.candidates[:5], 1):
        logger.info(f"   {i}. {candidate.product_identifier} | "
                   f"{candidate.range_label} | "
                   f"Confidence: {candidate.confidence_score:.2f} ({candidate.confidence_level.value})")
        if candidate.product_description:
            logger.info(f"      → {candidate.product_description}")
    
    # Export enhanced results
    output_path = mapping_service.export_mapping_result_to_json(result)
    logger.info(f"📄 Enhanced results saved to: {output_path}")
    
    return result


if __name__ == "__main__":
    test_enhanced_galaxy_6000_mapping() 