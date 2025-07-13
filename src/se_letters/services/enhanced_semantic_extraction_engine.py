#!/usr/bin/env python3
"""
Enhanced Semantic Extraction Engine.

Multi-dimensional database-driven extraction using subrange, device type,
brand, and PL services.
"""

import re
import time
from typing import Dict, List, Any
from dataclasses import dataclass
import duckdb
from loguru import logger


@dataclass
class SemanticMatch:
    """Represents a semantic match with confidence scoring."""

    field_type: str  # 'range', 'subrange', 'device_type', 'brand', 'pl_service'
    matched_value: str
    confidence: float
    extraction_method: str
    context: str = ""


@dataclass
class EnhancedExtractionResult:
    """Enhanced extraction result with multi-dimensional matches."""

    ranges: List[str]
    subranges: List[str]
    device_types: List[str]
    brands: List[str]
    pl_services: List[str]
    technical_specs: List[str]
    semantic_matches: List[SemanticMatch]
    extraction_confidence: float
    processing_time_ms: float
    extraction_method: str
    ai_metadata: Dict[str, Any]


class EnhancedSemanticExtractionEngine:
    """Enhanced semantic extraction with multi-dimensional database matching."""

    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.conn = duckdb.connect(db_path)
        self._load_semantic_dictionaries()
        logger.info(
            f"Enhanced semantic engine initialized with {len(self.ranges)} "
            f"ranges, {len(self.subranges)} subranges, "
            f"{len(self.device_types)} device types"
        )
    
    def _load_semantic_dictionaries(self):
        """Load all semantic dictionaries from database"""
        start_time = time.time()
        
        # Load ranges
        result = self.conn.execute("SELECT DISTINCT RANGE_LABEL FROM products WHERE RANGE_LABEL IS NOT NULL").fetchall()
        self.ranges = set(r[0] for r in result)
        
        # Load subranges
        result = self.conn.execute("SELECT DISTINCT SUBRANGE_LABEL FROM products WHERE SUBRANGE_LABEL IS NOT NULL").fetchall()
        self.subranges = set(r[0] for r in result)
        
        # Load device types
        result = self.conn.execute("SELECT DISTINCT DEVICETYPE_LABEL FROM products WHERE DEVICETYPE_LABEL IS NOT NULL").fetchall()
        self.device_types = set(r[0] for r in result)
        
        # Load brands
        result = self.conn.execute("SELECT DISTINCT BRAND_LABEL FROM products WHERE BRAND_LABEL IS NOT NULL").fetchall()
        self.brands = set(r[0] for r in result)
        
        # Load PL services
        result = self.conn.execute("SELECT DISTINCT PL_SERVICES FROM products WHERE PL_SERVICES IS NOT NULL").fetchall()
        self.pl_services = set(r[0] for r in result)
        
        # Create semantic patterns for enhanced matching
        self._create_semantic_patterns()
        
        load_time = (time.time() - start_time) * 1000
        logger.info(f"Loaded semantic dictionaries in {load_time:.1f}ms")
    
    def _create_semantic_patterns(self):
        """Create semantic patterns for advanced matching"""
        # Device type patterns
        self.device_patterns = {
            'circuit_breaker': ['breaker', 'circuit breaker', 'CB', 'MCB', 'MCCB', 'ACB'],
            'contactor': ['contactor', 'magnetic contactor', 'starter'],
            'relay': ['relay', 'protection relay', 'monitoring relay'],
            'drive': ['drive', 'VSD', 'variable speed drive', 'frequency converter'],
            'transformer': ['transformer', 'TX', 'isolation transformer'],
            'switch': ['switch', 'disconnector', 'isolator', 'load break switch'],
            'protection': ['protection', 'overcurrent', 'differential', 'distance'],
            'measurement': ['measurement', 'meter', 'monitoring', 'measuring'],
            'busway': ['busway', 'bus duct', 'power distribution'],
            'capacitor': ['capacitor', 'power factor correction', 'PFC']
        }
        
        # Brand patterns (including historical brands)
        self.brand_patterns = {
            'schneider': ['schneider', 'schneider electric', 'SE'],
            'square_d': ['square d', 'squared', 'sq d'],
            'telemecanique': ['telemecanique', 'tele', 'télémécanique'],
            'merlin_gerin': ['merlin gerin', 'merlin-gerin', 'MG'],
            'apc': ['apc', 'american power conversion'],
            'mge': ['mge', 'mge ups'],
            'himel': ['himel']
        }
        
        # Technical specification patterns
        self.technical_patterns = {
            'voltage': [r'(\d+)\s*kV', r'(\d+)\s*V', r'(\d+)\s*volt'],
            'current': [r'(\d+)\s*A', r'(\d+)\s*amp', r'(\d+)\s*ampere'],
            'power': [r'(\d+)\s*kW', r'(\d+)\s*MW', r'(\d+)\s*HP'],
            'frequency': [r'(\d+)\s*Hz', r'(\d+)\s*hertz']
        }
    
    def extract_enhanced_semantics(self, text: str, context: Dict[str, Any] = None) -> EnhancedExtractionResult:
        """Extract enhanced semantics using multi-dimensional matching"""
        start_time = time.time()
        
        if not text or not text.strip():
            return self._create_empty_result()
        
        text_upper = text.upper()
        semantic_matches = []
        
        # Extract ranges (existing logic)
        ranges = self._extract_ranges(text, text_upper, semantic_matches)
        
        # Extract subranges (new)
        subranges = self._extract_subranges(text, text_upper, semantic_matches)
        
        # Extract device types (new)
        device_types = self._extract_device_types(text, text_upper, semantic_matches)
        
        # Extract brands (new)
        brands = self._extract_brands(text, text_upper, semantic_matches)
        
        # Extract PL services (new)
        pl_services = self._extract_pl_services(text, text_upper, semantic_matches)
        
        # Extract technical specifications (new)
        technical_specs = self._extract_technical_specs(text, semantic_matches)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(semantic_matches, len(text))
        
        return EnhancedExtractionResult(
            ranges=ranges,
            subranges=subranges,
            device_types=device_types,
            brands=brands,
            pl_services=pl_services,
            technical_specs=technical_specs,
            semantic_matches=semantic_matches,
            extraction_confidence=confidence,
            processing_time_ms=processing_time,
            extraction_method="enhanced_multi_dimensional",
            ai_metadata={
                'total_matches': len(semantic_matches),
                'range_matches': len(ranges),
                'subrange_matches': len(subranges),
                'device_type_matches': len(device_types),
                'brand_matches': len(brands),
                'pl_service_matches': len(pl_services),
                'technical_spec_matches': len(technical_specs),
                'text_length': len(text),
                'processing_time_ms': processing_time
            }
        )
    
    def _extract_ranges(self, text: str, text_upper: str, semantic_matches: List[SemanticMatch]) -> List[str]:
        """Extract product ranges"""
        found_ranges = []
        
        # Exact matches
        for range_name in self.ranges:
            if range_name.upper() in text_upper:
                found_ranges.append(range_name)
                semantic_matches.append(SemanticMatch(
                    field_type='range',
                    matched_value=range_name,
                    confidence=0.95,
                    extraction_method='exact_match',
                    context=f"Found '{range_name}' in text"
                ))
        
        return list(set(found_ranges))
    
    def _extract_subranges(self, text: str, text_upper: str, semantic_matches: List[SemanticMatch]) -> List[str]:
        """Extract product subranges for granular matching"""
        found_subranges = []
        
        # Exact matches
        for subrange in self.subranges:
            if subrange.upper() in text_upper:
                found_subranges.append(subrange)
                semantic_matches.append(SemanticMatch(
                    field_type='subrange',
                    matched_value=subrange,
                    confidence=0.90,
                    extraction_method='exact_match',
                    context=f"Found subrange '{subrange}' in text"
                ))
        
        # Pattern-based matching for common subrange patterns
        subrange_patterns = [
            r'NSX\d+',  # NSX100, NSX250, etc.
            r'ATV\d+',  # ATV900, ATV600, etc.
            r'CVS\d+',  # CVS100, CVS250, etc.
            r'RM6\s*\d+',  # RM6 2, RM6 3, etc.
        ]
        
        for pattern in subrange_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                # Check if this pattern exists in our subranges
                matching_subranges = [sr for sr in self.subranges if match in sr.upper()]
                for subrange in matching_subranges:
                    if subrange not in found_subranges:
                        found_subranges.append(subrange)
                        semantic_matches.append(SemanticMatch(
                            field_type='subrange',
                            matched_value=subrange,
                            confidence=0.85,
                            extraction_method='pattern_match',
                            context=f"Pattern '{pattern}' matched '{subrange}'"
                        ))
        
        return list(set(found_subranges))
    
    def _extract_device_types(self, text: str, text_upper: str, semantic_matches: List[SemanticMatch]) -> List[str]:
        """Extract device types using semantic patterns"""
        found_device_types = []
        
        # Exact matches
        for device_type in self.device_types:
            if device_type.upper() in text_upper:
                found_device_types.append(device_type)
                semantic_matches.append(SemanticMatch(
                    field_type='device_type',
                    matched_value=device_type,
                    confidence=0.95,
                    extraction_method='exact_match',
                    context=f"Found device type '{device_type}' in text"
                ))
        
        # Pattern-based semantic matching
        for category, patterns in self.device_patterns.items():
            for pattern in patterns:
                if pattern.upper() in text_upper:
                    # Find matching device types in database
                    matching_types = [dt for dt in self.device_types if any(p.upper() in dt.upper() for p in patterns)]
                    for device_type in matching_types:
                        if device_type not in found_device_types:
                            found_device_types.append(device_type)
                            semantic_matches.append(SemanticMatch(
                                field_type='device_type',
                                matched_value=device_type,
                                confidence=0.80,
                                extraction_method='semantic_pattern',
                                context=f"Pattern '{pattern}' suggests '{device_type}'"
                            ))
        
        return list(set(found_device_types))
    
    def _extract_brands(self, text: str, text_upper: str, semantic_matches: List[SemanticMatch]) -> List[str]:
        """Extract brands including historical brands"""
        found_brands = []
        
        # Exact matches
        for brand in self.brands:
            if brand.upper() in text_upper:
                found_brands.append(brand)
                semantic_matches.append(SemanticMatch(
                    field_type='brand',
                    matched_value=brand,
                    confidence=0.95,
                    extraction_method='exact_match',
                    context=f"Found brand '{brand}' in text"
                ))
        
        # Pattern-based brand matching
        for brand_key, patterns in self.brand_patterns.items():
            for pattern in patterns:
                if pattern.upper() in text_upper:
                    # Find matching brands in database
                    matching_brands = [b for b in self.brands if any(p.upper() in b.upper() for p in patterns)]
                    for brand in matching_brands:
                        if brand not in found_brands:
                            found_brands.append(brand)
                            semantic_matches.append(SemanticMatch(
                                field_type='brand',
                                matched_value=brand,
                                confidence=0.85,
                                extraction_method='pattern_match',
                                context=f"Pattern '{pattern}' matched brand '{brand}'"
                            ))
        
        return list(set(found_brands))
    
    def _extract_pl_services(self, text: str, text_upper: str, semantic_matches: List[SemanticMatch]) -> List[str]:
        """Extract PL services for business context"""
        found_pl_services = []
        
        # Direct matches
        for pl_service in self.pl_services:
            if pl_service.upper() in text_upper:
                found_pl_services.append(pl_service)
                semantic_matches.append(SemanticMatch(
                    field_type='pl_service',
                    matched_value=pl_service,
                    confidence=0.90,
                    extraction_method='exact_match',
                    context=f"Found PL service '{pl_service}' in text"
                ))
        
        # Context-based PL service inference
        pl_context_patterns = {
            'PPIBS': ['power', 'distribution', 'panel', 'switchboard'],
            'IDPAS': ['industrial', 'automation', 'control'],
            'DPIBS': ['data center', 'UPS', 'critical power'],
            'SPIBS': ['solar', 'renewable', 'photovoltaic'],
            'PSIBS': ['power system', 'transmission', 'substation'],
            'IDIBS': ['industrial', 'building', 'infrastructure'],
            'DBIBS': ['distribution', 'building', 'commercial']
        }
        
        for pl_service, patterns in pl_context_patterns.items():
            if any(pattern.upper() in text_upper for pattern in patterns):
                if pl_service not in found_pl_services:
                    found_pl_services.append(pl_service)
                    semantic_matches.append(SemanticMatch(
                        field_type='pl_service',
                        matched_value=pl_service,
                        confidence=0.70,
                        extraction_method='context_inference',
                        context=f"Context patterns suggest '{pl_service}'"
                    ))
        
        return list(set(found_pl_services))
    
    def _extract_technical_specs(self, text: str, semantic_matches: List[SemanticMatch]) -> List[str]:
        """Extract technical specifications"""
        found_specs = []
        
        for spec_type, patterns in self.technical_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    spec_value = f"{spec_type}: {match}"
                    found_specs.append(spec_value)
                    semantic_matches.append(SemanticMatch(
                        field_type='technical_spec',
                        matched_value=spec_value,
                        confidence=0.95,
                        extraction_method='regex_pattern',
                        context=f"Extracted {spec_type} specification: {match}"
                    ))
        
        return list(set(found_specs))
    
    def _calculate_confidence(self, semantic_matches: List[SemanticMatch], text_length: int) -> float:
        """Calculate overall extraction confidence"""
        if not semantic_matches:
            return 0.0
        
        # Weight by match type and confidence
        weighted_score = 0.0
        total_weight = 0.0
        
        type_weights = {
            'range': 1.0,
            'subrange': 0.9,
            'device_type': 0.8,
            'brand': 0.7,
            'pl_service': 0.6,
            'technical_spec': 0.5
        }
        
        for match in semantic_matches:
            weight = type_weights.get(match.field_type, 0.5)
            weighted_score += match.confidence * weight
            total_weight += weight
        
        base_confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Adjust for text length (longer text = more reliable)
        length_factor = min(1.0, text_length / 500)  # Normalize around 500 chars
        
        return min(0.95, base_confidence * (0.7 + 0.3 * length_factor))
    
    def _create_empty_result(self) -> EnhancedExtractionResult:
        """Create empty result for failed extraction"""
        return EnhancedExtractionResult(
            ranges=[],
            subranges=[],
            device_types=[],
            brands=[],
            pl_services=[],
            technical_specs=[],
            semantic_matches=[],
            extraction_confidence=0.0,
            processing_time_ms=0.0,
            extraction_method="failed",
            ai_metadata={}
        )
    
    def get_refined_search_space(self, extraction_result: EnhancedExtractionResult) -> Dict[str, Any]:
        """Get refined search space based on multi-dimensional extraction"""
        search_criteria = {}
        
        # Add range criteria
        if extraction_result.ranges:
            search_criteria['ranges'] = extraction_result.ranges
        
        # Add subrange criteria for granular matching
        if extraction_result.subranges:
            search_criteria['subranges'] = extraction_result.subranges
        
        # Add device type criteria
        if extraction_result.device_types:
            search_criteria['device_types'] = extraction_result.device_types
        
        # Add brand criteria
        if extraction_result.brands:
            search_criteria['brands'] = extraction_result.brands
        
        # Add PL service criteria
        if extraction_result.pl_services:
            search_criteria['pl_services'] = extraction_result.pl_services
        
        # Add technical specification criteria
        if extraction_result.technical_specs:
            search_criteria['technical_specs'] = extraction_result.technical_specs
        
        return search_criteria
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close() 