#!/usr/bin/env python3
"""
Enhanced DPIBS CORTEC Service
Advanced service for DPIBS protection relay mapping with CORTEC nomenclature 
understanding

Features:
- CORTEC code pattern recognition and parsing
- Enhanced MiCOM protection relay mapping
- Position-based component analysis
- Intelligent family grouping with CORTEC awareness
- Smart wildcard pattern matching for dashes/placeholders

Version: 4.0.0 - CORTEC Enhanced
Author: SE Letters Team
"""

import sys
from pathlib import Path
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time
from collections import defaultdict

import duckdb
from loguru import logger

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


@dataclass
class CORTECComponents:
    """CORTEC code components based on MiCOM nomenclature guide"""
    model: Optional[str] = None  # P441, P521, C264, etc.
    design_suffix: Optional[str] = None  # J, B, C, etc.
    input_config: Optional[str] = None  # 1, 2, 3, etc.
    hardware_config: Optional[str] = None  # A, C, E, M, etc.
    communication: Optional[str] = None  # 0, 1, 2, 3, etc.
    language: Optional[str] = None  # 0, 5, C, etc.
    mounting: Optional[str] = None  # M, P, etc.
    additional: Optional[str] = None  # Additional configuration


@dataclass
class ProtectionRelayMatch:
    """Enhanced protection relay match with CORTEC understanding"""
    product_identifier: str
    range_label: str
    subrange_label: str
    commercial_status: str
    product_description: str
    cortec_components: Optional[CORTECComponents] = None
    family_group: Optional[str] = None
    confidence_score: float = 0.0
    match_type: str = 'unknown'  # 'exact', 'cortec_family', 'pattern', 'semantic'


class EnhancedDPIBSCORTECService:
    """Enhanced DPIBS service with CORTEC nomenclature understanding"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        """Initialize the enhanced DPIBS CORTEC service"""
        self.db_path = db_path
        
        # CORTEC pattern definitions based on analysis
        self.cortec_patterns = {
            # P-series protection relays (P441, P521, etc.)
            'p_series': re.compile(
                r'P(\d{2,3})([A-Z]?)(\d?)([A-Z]?)(\d?)([A-Z]?)(\d?)', 
                re.IGNORECASE
            ),
            
            # C-series control relays (C264, etc.)
            'c_series': re.compile(
                r'C(\d{3})([A-Z])(\d+)(-+)(\d+)(-+)', 
                re.IGNORECASE
            ),
            
            # E-series enhanced relays (E521, etc.)
            'e_series': re.compile(
                r'E(\d{3})([A-Z]\d)([A-Z]{2})(\d{3})([A-Z]{2})(\d)', 
                re.IGNORECASE
            ),
            
            # General CORTEC-like patterns
            'general': re.compile(
                r'([A-Z]+\d+)([A-Z]+)?(\d+)?([A-Z]+)?(\d+)?', 
                re.IGNORECASE
            )
        }
        
        # Protection relay families based on discovered patterns
        self.protection_families = {
            'MiCOM_P20': ['P20', 'P21', 'P22', 'P23'],
            'MiCOM_P120': ['P120', 'P121', 'P122', 'P123'],
            'MiCOM_P125': ['P125', 'P126', 'P127'],
            'MiCOM_P220': ['P220', 'P221', 'P222', 'P225'],
            'MiCOM_P441': ['P441', 'P442', 'P444'],
            'MiCOM_P521': ['P521', 'P522', 'P523'],
            'MiCOM_P632': ['P632', 'P633', 'P634'],
            'MiCOM_P921': ['P921', 'P922', 'P923'],
            'MiCOM_C264': ['C264'],
            'SEPAM_20': ['SEPAM20', 'SEPAM 20', 'SEPAM-20'],
            'SEPAM_40': ['SEPAM40', 'SEPAM 40', 'SEPAM-40'],
            'PowerLogic_P5L': ['P5L', 'PowerLogic P5L']
        }
        
        logger.info("🔧 Enhanced DPIBS CORTEC Service initialized")
        logger.info(f"📊 Database: {self.db_path}")
        logger.info(f"🎯 Protection families: {len(self.protection_families)}")
    
    def parse_cortec_code(self, product_identifier: str) -> Optional[CORTECComponents]:
        """Parse CORTEC code components from product identifier"""
        if not product_identifier:
            return None
        
        # Try P-series pattern (P441J1M0, P521, etc.)
        if match := self.cortec_patterns['p_series'].search(product_identifier):
            return CORTECComponents(
                model=f"P{match.group(1)}",
                design_suffix=match.group(2) if match.group(2) else None,
                input_config=match.group(3) if match.group(3) else None,
                hardware_config=match.group(4) if match.group(4) else None,
                communication=match.group(5) if match.group(5) else None,
                language=match.group(6) if match.group(6) else None,
                mounting=match.group(7) if match.group(7) else None
            )
        
        # Try C-series pattern (C264C0-------0----)
        if match := self.cortec_patterns['c_series'].search(product_identifier):
            return CORTECComponents(
                model=f"C{match.group(1)}",
                design_suffix=match.group(2),
                input_config=match.group(3),
                hardware_config=match.group(4).replace('-', 'X'),  # Placeholder
                communication=match.group(5),
                additional=match.group(6).replace('-', 'X')
            )
        
        # Try E-series pattern (E521A0BZ112DB0)
        if match := self.cortec_patterns['e_series'].search(product_identifier):
            return CORTECComponents(
                model=f"E{match.group(1)}",
                design_suffix=match.group(2),
                input_config=match.group(3),
                hardware_config=match.group(4),
                communication=match.group(5),
                mounting=match.group(6)
            )
        
        return None
    
    def identify_protection_family(self, product_identifier: str, 
                                 range_label: str) -> Optional[str]:
        """Identify protection relay family from identifier and range"""
        identifier_upper = product_identifier.upper()
        range_upper = range_label.upper()
        
        # Check each family
        for family_name, patterns in self.protection_families.items():
            for pattern in patterns:
                pattern_upper = pattern.upper()
                if (pattern_upper in identifier_upper or 
                    pattern_upper in range_upper or
                    pattern_upper.replace(' ', '') in 
                    identifier_upper.replace(' ', '')):
                    return family_name
        
        return None
    
    def enhanced_dpibs_product_search(
        self, 
        target_products: List[Dict[str, Any]],
        include_active_filter: bool = True
    ) -> List[ProtectionRelayMatch]:
        """Enhanced DPIBS product search with CORTEC understanding"""
        start_time = time.time()
        
        logger.info("🔍 Enhanced DPIBS Product Search with CORTEC Analysis")
        logger.info(f"🎯 Target products: {len(target_products)}")
        
        matches = []
        
        try:
            with duckdb.connect(self.db_path) as conn:
                for target_product in target_products:
                    product_identifier = target_product.get(
                        'product_identifier', ''
                    )
                    range_label = target_product.get('range_label', '')
                    product_line = target_product.get('product_line', '')
                    obsolescence_status = target_product.get(
                        'obsolescence_status', ''
                    )
                    
                    logger.info(f"\n🔎 Searching for: {product_identifier} "
                               f"({range_label})")
                    
                    # Skip active products if filter enabled
                    if (include_active_filter and 
                            obsolescence_status.upper() == 'ACTIVE'):
                        logger.info(f"   ⏭️ Skipping active product: "
                                   f"{product_identifier}")
                        continue
                    
                    # Build enhanced search strategy
                    search_results = self._perform_enhanced_cortec_search(
                        conn, product_identifier, range_label
                    )
                    
                    # Process and enhance results
                    for result in search_results:
                        cortec_components = self.parse_cortec_code(
                            result['PRODUCT_IDENTIFIER']
                        )
                        family_group = self.identify_protection_family(
                            result['PRODUCT_IDENTIFIER'], 
                            result['RANGE_LABEL']
                        )
                        
                        match = ProtectionRelayMatch(
                            product_identifier=result['PRODUCT_IDENTIFIER'],
                            range_label=result['RANGE_LABEL'],
                            subrange_label=result.get('SUBRANGE_LABEL', ''),
                            commercial_status=result['COMMERCIAL_STATUS'],
                            product_description=result['PRODUCT_DESCRIPTION'],
                            cortec_components=cortec_components,
                            family_group=family_group,
                            confidence_score=self._calculate_match_confidence(
                                target_product, result, cortec_components, 
                                family_group
                            ),
                            match_type=self._determine_match_type(
                                target_product, result, cortec_components
                            )
                        )
                        
                        matches.append(match)
                        
                        logger.info(f"   ✅ Found: {match.product_identifier}")
                        logger.info(f"      Family: {match.family_group}")
                        logger.info(f"      CORTEC: "
                                   f"{cortec_components is not None}")
                        logger.info(f"      Confidence: "
                                   f"{match.confidence_score:.2f}")
                        logger.info(f"      Status: {match.commercial_status}")
        
        except Exception as e:
            logger.error(f"❌ Enhanced DPIBS search failed: {e}")
            return []
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        search_time = (time.time() - start_time) * 1000
        logger.info(f"\n📊 Enhanced DPIBS Search Results:")
        logger.info(f"   🎯 Total matches: {len(matches)}")
        logger.info(f"   ⏱️ Search time: {search_time:.2f}ms")
        
        return matches
    
    def _perform_enhanced_cortec_search(
        self, 
        conn: duckdb.DuckDBPyConnection, 
        product_identifier: str, 
        range_label: str
    ) -> List[Dict[str, Any]]:
        """Perform enhanced CORTEC-aware database search"""
        
        # Strategy 1: Exact identifier match
        exact_results = self._search_exact_identifier(conn, product_identifier)
        if exact_results:
            logger.info(f"   🎯 Exact identifier matches: {len(exact_results)}")
            return exact_results
        
        # Strategy 2: CORTEC family search
        cortec_results = self._search_cortec_family(conn, product_identifier)
        if cortec_results:
            logger.info(f"   🎯 CORTEC family matches: {len(cortec_results)}")
            return cortec_results
        
        # Strategy 3: Range-based search
        range_results = self._search_range_patterns(conn, range_label)
        if range_results:
            logger.info(f"   🎯 Range pattern matches: {len(range_results)}")
            return range_results
        
        # Strategy 4: Semantic search
        semantic_results = self._search_semantic_patterns(
            conn, product_identifier, range_label
        )
        logger.info(f"   🎯 Semantic matches: {len(semantic_results)}")
        return semantic_results
    
    def _search_exact_identifier(self, conn: duckdb.DuckDBPyConnection, 
                                identifier: str) -> List[Dict[str, Any]]:
        """Search for exact product identifier matches"""
        query = """
            SELECT PRODUCT_IDENTIFIER, RANGE_LABEL, SUBRANGE_LABEL, 
                   COMMERCIAL_STATUS, PRODUCT_DESCRIPTION
            FROM products 
            WHERE PL_SERVICES = 'DPIBS' 
            AND UPPER(PRODUCT_IDENTIFIER) = UPPER(?)
            ORDER BY PRODUCT_IDENTIFIER
            LIMIT 20
        """
        
        result = conn.execute(query, [identifier]).fetchall()
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in result]
    
    def _search_cortec_family(self, conn: duckdb.DuckDBPyConnection, 
                             identifier: str) -> List[Dict[str, Any]]:
        """Search for CORTEC family matches"""
        
        # Extract model from identifier
        cortec_components = self.parse_cortec_code(identifier)
        if not cortec_components or not cortec_components.model:
            return []
        
        # Search for same model family
        model_pattern = f"%{cortec_components.model}%"
        
        query = """
            SELECT PRODUCT_IDENTIFIER, RANGE_LABEL, SUBRANGE_LABEL, 
                   COMMERCIAL_STATUS, PRODUCT_DESCRIPTION
            FROM products 
            WHERE PL_SERVICES = 'DPIBS' 
            AND (UPPER(PRODUCT_IDENTIFIER) LIKE UPPER(?) OR
                 UPPER(RANGE_LABEL) LIKE UPPER(?))
            ORDER BY PRODUCT_IDENTIFIER
            LIMIT 50
        """
        
        result = conn.execute(query, [model_pattern, model_pattern]).fetchall()
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in result]
    
    def _search_range_patterns(self, conn: duckdb.DuckDBPyConnection, 
                              range_label: str) -> List[Dict[str, Any]]:
        """Search for range pattern matches"""
        if not range_label:
            return []
        
        # Clean and prepare range search terms
        range_terms = []
        range_terms.append(range_label)
        
        # Add variations
        if ' ' in range_label:
            range_terms.append(range_label.replace(' ', ''))
        
        # Extract key terms (MiCOM, SEPAM, PowerLogic, etc.)
        for term in ['MiCOM', 'SEPAM', 'PowerLogic']:
            if term.upper() in range_label.upper():
                range_terms.append(term)
        
        # Build search patterns
        search_patterns = []
        params = []
        
        for term in range_terms:
            search_patterns.extend([
                "UPPER(RANGE_LABEL) LIKE UPPER(?)",
                "UPPER(PRODUCT_IDENTIFIER) LIKE UPPER(?)",
                "UPPER(PRODUCT_DESCRIPTION) LIKE UPPER(?)"
            ])
            pattern = f"%{term}%"
            params.extend([pattern, pattern, pattern])
        
        if not search_patterns:
            return []
        
        query = f"""
            SELECT PRODUCT_IDENTIFIER, RANGE_LABEL, SUBRANGE_LABEL, 
                   COMMERCIAL_STATUS, PRODUCT_DESCRIPTION
            FROM products 
            WHERE PL_SERVICES = 'DPIBS' 
            AND ({' OR '.join(search_patterns)})
            ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER
            LIMIT 100
        """
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in result]
    
    def _search_semantic_patterns(self, conn: duckdb.DuckDBPyConnection, 
                                 identifier: str, 
                                 range_label: str) -> List[Dict[str, Any]]:
        """Search for semantic pattern matches"""
        
        # Extract semantic keywords
        keywords = []
        
        # From identifier
        if identifier:
            if any(x in identifier.upper() for x in ['P20', 'P521', 'SEPAM', 'MICOM']):
                keywords.extend(['protection', 'relay', 'digital', 'power'])
        
        # From range
        if range_label:
            if 'MiCOM' in range_label:
                keywords.extend(['MiCOM', 'protection', 'relay'])
            if 'SEPAM' in range_label:
                keywords.extend(['SEPAM', 'protection', 'relay'])
            if 'PowerLogic' in range_label:
                keywords.extend(['PowerLogic', 'power', 'monitoring'])
        
        if not keywords:
            keywords = ['protection', 'relay']  # Default DPIBS keywords
        
        # Build semantic search
        search_patterns = []
        params = []
        
        for keyword in keywords[:5]:  # Limit to top 5 keywords
            search_patterns.extend([
                "UPPER(PRODUCT_DESCRIPTION) LIKE UPPER(?)",
                "UPPER(RANGE_LABEL) LIKE UPPER(?)"
            ])
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern])
        
        query = f"""
            SELECT PRODUCT_IDENTIFIER, RANGE_LABEL, SUBRANGE_LABEL, 
                   COMMERCIAL_STATUS, PRODUCT_DESCRIPTION
            FROM products 
            WHERE PL_SERVICES = 'DPIBS' 
            AND ({' OR '.join(search_patterns)})
            ORDER BY RANGE_LABEL, PRODUCT_IDENTIFIER
            LIMIT 50
        """
        
        result = conn.execute(query, params).fetchall()
        columns = [desc[0] for desc in conn.description]
        return [dict(zip(columns, row)) for row in result]
    
    def _calculate_match_confidence(
        self, 
        target: Dict[str, Any], 
        result: Dict[str, Any],
        cortec_components: Optional[CORTECComponents],
        family_group: Optional[str]
    ) -> float:
        """Calculate match confidence score"""
        confidence = 0.0
        
        target_id = target.get('product_identifier', '').upper()
        result_id = result['PRODUCT_IDENTIFIER'].upper()
        target_range = target.get('range_label', '').upper()
        result_range = result['RANGE_LABEL'].upper()
        
        # Exact identifier match
        if target_id == result_id:
            confidence += 0.5
        
        # Range match
        if target_range in result_range or result_range in target_range:
            confidence += 0.3
        
        # CORTEC family bonus
        if cortec_components:
            confidence += 0.1
        
        # Family group bonus
        if family_group:
            confidence += 0.1
        
        # Commercial status consideration
        status = result['COMMERCIAL_STATUS'].upper()
        if 'COMMERCIALIS' in status:
            confidence += 0.0  # Neutral for obsolete products
        elif 'END' in status or 'OBSOLETE' in status:
            confidence += 0.0  # Expected for obsolescence letters
        
        return min(confidence, 1.0)
    
    def _determine_match_type(
        self, 
        target: Dict[str, Any], 
        result: Dict[str, Any],
        cortec_components: Optional[CORTECComponents]
    ) -> str:
        """Determine the type of match"""
        target_id = target.get('product_identifier', '').upper()
        result_id = result['PRODUCT_IDENTIFIER'].upper()
        
        if target_id == result_id:
            return 'exact'
        elif cortec_components:
            return 'cortec_family'
        elif any(term in result_id for term in target_id.split()[:2]):
            return 'pattern'
        else:
            return 'semantic'


def test_enhanced_dpibs_cortec_service():
    """Test the enhanced DPIBS CORTEC service"""
    
    # Test data from grok_metadata.json
    test_products = [
        {
            "product_identifier": "MiCOM P20",
            "range_label": "MiCOM",
            "subrange_label": "P20",
            "product_line": "DPIBS",
            "obsolescence_status": "End of Commercialization"
        },
        {
            "product_identifier": "SEPAM 20",
            "range_label": "SEPAM",
            "subrange_label": "20",
            "product_line": "DPIBS",
            "obsolescence_status": "End of Commercialization"
        },
        {
            "product_identifier": "SEPAM 40",
            "range_label": "SEPAM",
            "subrange_label": "40",
            "product_line": "DPIBS",
            "obsolescence_status": "End of Commercialization"
        },
        {
            "product_identifier": "MiCOM P521",
            "range_label": "MiCOM",
            "subrange_label": "P521",
            "product_line": "DPIBS",
            "obsolescence_status": "End of Commercialization"
        },
        {
            "product_identifier": "PowerLogic P5L",
            "range_label": "PowerLogic",
            "subrange_label": "P5L",
            "product_line": "DPIBS",
            "obsolescence_status": "Active"  # This should be filtered out
        }
    ]
    
    # Initialize service
    service = EnhancedDPIBSCORTECService()
    
    # Test CORTEC parsing
    logger.info("\n🧪 Testing CORTEC Code Parsing:")
    test_codes = [
        "P441J1M0",  # Standard CORTEC
        "C264C0-------0----",  # C-series with placeholders
        "E521A0BZ112DB0",  # E-series
        "MiCOM P20",  # Simple identifier
        "SEPAM 40"  # Simple identifier
    ]
    
    for code in test_codes:
        cortec = service.parse_cortec_code(code)
        logger.info(f"   {code}: {cortec}")
    
    # Test enhanced search
    logger.info("\n🔍 Testing Enhanced DPIBS Search:")
    matches = service.enhanced_dpibs_product_search(test_products)
    
    # Display results
    logger.info(f"\n📊 ENHANCED DPIBS SEARCH RESULTS:")
    logger.info(f"   🎯 Total matches found: {len(matches)}")
    
    # Group by family
    families = defaultdict(list)
    for match in matches:
        family = match.family_group or 'Unknown'
        families[family].append(match)
    
    for family, family_matches in families.items():
        logger.info(f"\n📦 {family} Family ({len(family_matches)} products):")
        for match in family_matches[:5]:  # Show top 5 per family
            logger.info(f"   ✅ {match.product_identifier}")
            logger.info(f"      Range: {match.range_label}")
            logger.info(f"      Status: {match.commercial_status}")
            logger.info(f"      Confidence: {match.confidence_score:.3f}")
            logger.info(f"      Match Type: {match.match_type}")
            if match.cortec_components:
                logger.info(f"      CORTEC: {match.cortec_components.model}")
            logger.info("      ---")


if __name__ == "__main__":
    test_enhanced_dpibs_cortec_service() 