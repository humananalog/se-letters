#!/usr/bin/env python3
"""
SOTA Range Mapping Service
State-of-the-Art product range mapping for obsolescence letters

CRITICAL INSIGHT: Obsolescence letters refer to PRODUCT RANGES/SERIES that apply to 
MULTIPLE actual products in the IBcatalogue database.

Example: "Galaxy 6000" letter applies to:
- Galaxy 6000 250VA, 500VA, 1000VA
- Different voltage configurations  
- Various power ratings
- 3-phase and single-phase variants
- Multiple part numbers within the series

This service finds ALL products belonging to mentioned ranges with comprehensive analysis.

Version: 1.0.0
Author: SE Letters Team
"""

import pandas as pd
import numpy as np
import time
import json
import re
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
import threading
from fuzzywuzzy import fuzz
from loguru import logger


@dataclass
class ProductRecord:
    """Individual product record with full IBcatalogue details"""
    product_identifier: str
    product_type: str
    product_description: str
    brand_code: str
    brand_label: str
    range_code: str
    range_label: str
    subrange_code: str
    subrange_label: str
    devicetype_label: str
    pl_services: str
    confidence_score: float
    match_reason: str
    series_membership: str


@dataclass
class ProductRange:
    """Product range/series with all associated products"""
    range_identifier: str
    range_label: str
    subrange_label: str
    product_line: str
    total_products: int
    products: List[ProductRecord]
    range_confidence: float
    coverage_analysis: Dict[str, Any]
    business_impact: Dict[str, Any]


@dataclass
class RangeMappingResult:
    """Comprehensive range mapping result"""
    input_context: Dict[str, str]
    detected_ranges: List[ProductRange]
    total_products_found: int
    processing_time_ms: float
    search_strategy: str
    confidence_level: str
    business_analysis: Dict[str, Any]
    export_ready: bool


class SOTARangeMappingService:
    """State-of-the-Art Range Mapping Service for Product Series"""
    
    def __init__(self, ibcatalogue_path: str = "../../data/input/letters/IBcatalogue.xlsx"):
        """Initialize SOTA Range Mapping Service"""
        self.ibcatalogue_path = ibcatalogue_path
        self.products_df = None
        self._lock = threading.RLock()
        
        # Range detection patterns
        self.range_patterns = {
            'galaxy_series': {
                'primary_patterns': ['galaxy', 'glxy'],
                'subrange_patterns': ['6000', '5000', '7000', '3000'],
                'variants': ['va', 'kva', 'tower', 'rack', '1ph', '3ph'],
                'brand_indicators': ['mge', 'schneider']
            },
            'sepam_series': {
                'primary_patterns': ['sepam'],
                'subrange_patterns': ['20', '40', '60', '80', '2040', '2030'],
                'variants': ['protection', 'relay', 'digital'],
                'brand_indicators': ['schneider']
            },
            'masterpact_series': {
                'primary_patterns': ['masterpact', 'mstpct'],
                'subrange_patterns': ['nt', 'nw', 'mt'],
                'variants': ['circuit breaker', 'switchgear', 'lv'],
                'brand_indicators': ['schneider']
            },
            'altivar_series': {
                'primary_patterns': ['altivar', 'atv'],
                'subrange_patterns': ['71', '61', '312', '32'],
                'variants': ['drive', 'vsd', 'variable speed'],
                'brand_indicators': ['schneider']
            },
            'modicon_series': {
                'primary_patterns': ['modicon'],
                'subrange_patterns': ['m580', 'm340', 'm241', 'm221'],
                'variants': ['plc', 'controller', 'automation'],
                'brand_indicators': ['schneider']
            }
        }
        
        # Range confidence thresholds
        self.confidence_thresholds = {
            'exact_range_match': 0.95,
            'strong_series_match': 0.85,
            'probable_range_match': 0.75,
            'possible_range_match': 0.65,
            'weak_correlation': 0.50
        }
        
        self._load_products()
        logger.info(f"🎯 SOTA Range Mapping Service initialized with {len(self.products_df)} products")
        logger.info(f"📊 Ready to map product ranges to series with comprehensive analysis")
    
    def _load_products(self) -> None:
        """Load IBcatalogue with range-focused optimization"""
        try:
            logger.info("📥 Loading IBcatalogue for range analysis...")
            
            self.products_df = pd.read_excel(
                self.ibcatalogue_path,
                sheet_name="OIC_out",
                usecols=[
                    'PRODUCT_IDENTIFIER', 'PRODUCT_TYPE', 'PRODUCT_DESCRIPTION',
                    'BRAND_CODE', 'BRAND_LABEL', 'RANGE_CODE', 'RANGE_LABEL',
                    'SUBRANGE_CODE', 'SUBRANGE_LABEL', 'DEVICETYPE_LABEL', 'PL_SERVICES'
                ]
            )
            
            # Clean and prepare for range analysis
            self.products_df = self.products_df.fillna('')
            
            # Create normalized columns for range matching
            self.products_df['range_norm'] = self.products_df['RANGE_LABEL'].str.lower().str.strip()
            self.products_df['subrange_norm'] = self.products_df['SUBRANGE_LABEL'].str.lower().str.strip()
            self.products_df['identifier_norm'] = self.products_df['PRODUCT_IDENTIFIER'].str.lower().str.strip()
            self.products_df['description_norm'] = self.products_df['PRODUCT_DESCRIPTION'].str.lower().str.strip()
            self.products_df['brand_norm'] = self.products_df['BRAND_LABEL'].str.lower().str.strip()
            
            # Create composite range keys for efficient grouping
            self.products_df['range_key'] = (
                self.products_df['range_norm'] + '|' + 
                self.products_df['subrange_norm'] + '|' + 
                self.products_df['PL_SERVICES']
            )
            
            # Pre-calculate range statistics
            self.range_stats = self._calculate_range_statistics()
            
            logger.info(f"✅ Loaded {len(self.products_df)} products with range optimization")
            logger.info(f"📊 Identified {len(self.range_stats)} unique product ranges")
            
        except Exception as e:
            logger.error(f"❌ Failed to load IBcatalogue: {e}")
            raise
    
    def _calculate_range_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Pre-calculate statistics for all product ranges"""
        range_stats = {}
        
        # Group by range and subrange
        grouped = self.products_df.groupby(['range_norm', 'subrange_norm', 'PL_SERVICES'])
        
        for (range_label, subrange_label, pl_services), group in grouped:
            if range_label:  # Only process non-empty ranges
                key = f"{range_label}|{subrange_label}|{pl_services}"
                range_stats[key] = {
                    'product_count': len(group),
                    'brand_distribution': group['BRAND_LABEL'].value_counts().to_dict(),
                    'device_types': group['DEVICETYPE_LABEL'].unique().tolist(),
                    'sample_identifiers': group['PRODUCT_IDENTIFIER'].head(5).tolist(),
                    'range_label': range_label,
                    'subrange_label': subrange_label,
                    'pl_services': pl_services
                }
        
        return range_stats
    
    def map_letter_to_product_ranges(
        self,
        product_identifier: str,
        range_label: str = "",
        subrange_label: str = "",
        product_line: str = "",
        context_description: str = "",
        include_similar_ranges: bool = True
    ) -> RangeMappingResult:
        """Map letter product to ALL associated product ranges and series"""
        
        start_time = time.time()
        
        try:
            with self._lock:
                logger.info(f"🎯 SOTA Range Mapping for: {product_identifier}")
                logger.info(f"📋 Context: Range={range_label}, Subrange={subrange_label}, PL={product_line}")
                
                # Step 1: Detect target ranges from input
                detected_ranges = self._detect_target_ranges(
                    product_identifier, range_label, subrange_label, context_description
                )
                
                # Step 2: Find all products for each detected range
                range_results = []
                total_products = 0
                
                for range_info in detected_ranges:
                    products = self._find_all_products_in_range(
                        range_info, product_line, include_similar_ranges
                    )
                    
                    if products:
                        product_range = self._create_product_range(range_info, products)
                        range_results.append(product_range)
                        total_products += len(products)
                
                # Step 3: Business impact analysis
                business_analysis = self._analyze_business_impact(range_results, total_products)
                
                # Step 4: Determine overall confidence
                confidence_level = self._determine_confidence_level(range_results)
                
                processing_time_ms = (time.time() - start_time) * 1000
                
                result = RangeMappingResult(
                    input_context={
                        'product_identifier': product_identifier,
                        'range_label': range_label,
                        'subrange_label': subrange_label,
                        'product_line': product_line,
                        'context_description': context_description
                    },
                    detected_ranges=range_results,
                    total_products_found=total_products,
                    processing_time_ms=processing_time_ms,
                    search_strategy="sota_range_mapping",
                    confidence_level=confidence_level,
                    business_analysis=business_analysis,
                    export_ready=True
                )
                
                logger.info(f"✅ Range mapping completed in {processing_time_ms:.1f}ms")
                logger.info(f"📊 Found {len(range_results)} ranges with {total_products} total products")
                logger.info(f"🎯 Confidence Level: {confidence_level}")
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Range mapping failed: {e}")
            raise
    
    def _detect_target_ranges(
        self, 
        product_identifier: str, 
        range_label: str, 
        subrange_label: str, 
        context_description: str
    ) -> List[Dict[str, Any]]:
        """Detect target ranges from input using pattern recognition"""
        
        detected_ranges = []
        input_text = f"{product_identifier} {range_label} {subrange_label} {context_description}".lower()
        
        # Primary range detection
        primary_range = {
            'range_label': range_label.lower() if range_label else '',
            'subrange_label': subrange_label.lower() if subrange_label else '',
            'confidence': 0.0,
            'detection_method': 'direct_input',
            'patterns_matched': []
        }
        
        # Calculate confidence based on input quality
        if range_label and subrange_label:
            primary_range['confidence'] = 0.95
        elif range_label:
            primary_range['confidence'] = 0.85
        else:
            primary_range['confidence'] = 0.70
        
        detected_ranges.append(primary_range)
        
        # Pattern-based detection for additional ranges
        for series_name, patterns in self.range_patterns.items():
            range_match = self._match_range_patterns(input_text, patterns)
            if range_match['confidence'] > 0.70:
                range_match['detection_method'] = 'pattern_recognition'
                range_match['series_family'] = series_name
                detected_ranges.append(range_match)
        
        # Remove duplicates and sort by confidence
        unique_ranges = []
        seen_ranges = set()
        
        for range_info in sorted(detected_ranges, key=lambda x: x['confidence'], reverse=True):
            range_key = f"{range_info['range_label']}|{range_info['subrange_label']}"
            if range_key not in seen_ranges:
                unique_ranges.append(range_info)
                seen_ranges.add(range_key)
        
        logger.info(f"🔍 Detected {len(unique_ranges)} target ranges")
        for i, range_info in enumerate(unique_ranges, 1):
            logger.info(f"  {i}. {range_info['range_label']} / {range_info['subrange_label']} (confidence: {range_info['confidence']:.3f})")
        
        return unique_ranges
    
    def _match_range_patterns(self, input_text: str, patterns: Dict[str, List[str]]) -> Dict[str, Any]:
        """Match input against range patterns"""
        
        match_result = {
            'range_label': '',
            'subrange_label': '',
            'confidence': 0.0,
            'patterns_matched': []
        }
        
        confidence_score = 0.0
        matched_patterns = []
        
        # Check primary patterns
        for pattern in patterns['primary_patterns']:
            if pattern in input_text:
                match_result['range_label'] = pattern
                confidence_score += 0.4
                matched_patterns.append(f"primary:{pattern}")
        
        # Check subrange patterns
        for pattern in patterns['subrange_patterns']:
            if pattern in input_text:
                match_result['subrange_label'] = pattern
                confidence_score += 0.3
                matched_patterns.append(f"subrange:{pattern}")
        
        # Check variant patterns
        for pattern in patterns['variants']:
            if pattern in input_text:
                confidence_score += 0.2
                matched_patterns.append(f"variant:{pattern}")
        
        # Check brand indicators
        for pattern in patterns['brand_indicators']:
            if pattern in input_text:
                confidence_score += 0.1
                matched_patterns.append(f"brand:{pattern}")
        
        match_result['confidence'] = min(confidence_score, 1.0)
        match_result['patterns_matched'] = matched_patterns
        
        return match_result
    
    def _find_all_products_in_range(
        self, 
        range_info: Dict[str, Any], 
        product_line: str,
        include_similar: bool = True
    ) -> List[ProductRecord]:
        """Find ALL products belonging to the specified range"""
        
        products = []
        
        # Apply PL_SERVICES filter if specified
        if product_line:
            pl_mappings = {'spibs': 'SPIBS', 'dpibs': 'DPIBS', 'ppibs': 'PPIBS', 'psibs': 'PSIBS'}
            mapped_pl = pl_mappings.get(product_line.lower(), product_line.upper())
            candidates_df = self.products_df[self.products_df['PL_SERVICES'] == mapped_pl].copy()
        else:
            candidates_df = self.products_df.copy()
        
        # Exact range matches
        exact_matches = self._find_exact_range_matches(candidates_df, range_info)
        products.extend(exact_matches)
        
        # Similar range matches if enabled
        if include_similar:
            similar_matches = self._find_similar_range_matches(candidates_df, range_info, exact_matches)
            products.extend(similar_matches)
        
        logger.info(f"📦 Found {len(products)} products for range: {range_info['range_label']} / {range_info['subrange_label']}")
        
        return products
    
    def _find_exact_range_matches(self, df: pd.DataFrame, range_info: Dict[str, Any]) -> List[ProductRecord]:
        """Find exact matches for the range"""
        
        products = []
        range_label = range_info['range_label']
        subrange_label = range_info['subrange_label']
        
        # Exact range and subrange match
        if range_label and subrange_label:
            matches = df[
                (df['range_norm'].str.contains(range_label, na=False)) &
                (df['subrange_norm'].str.contains(subrange_label, na=False))
            ]
        elif range_label:
            matches = df[df['range_norm'].str.contains(range_label, na=False)]
        else:
            matches = pd.DataFrame()  # No valid range to match
        
        for _, row in matches.iterrows():
            product = ProductRecord(
                product_identifier=row['PRODUCT_IDENTIFIER'],
                product_type=row['PRODUCT_TYPE'],
                product_description=row['PRODUCT_DESCRIPTION'],
                brand_code=row['BRAND_CODE'],
                brand_label=row['BRAND_LABEL'],
                range_code=row['RANGE_CODE'],
                range_label=row['RANGE_LABEL'],
                subrange_code=row['SUBRANGE_CODE'],
                subrange_label=row['SUBRANGE_LABEL'],
                devicetype_label=row['DEVICETYPE_LABEL'],
                pl_services=row['PL_SERVICES'],
                confidence_score=0.95,  # High confidence for exact matches
                match_reason="exact_range_match",
                series_membership="primary"
            )
            products.append(product)
        
        return products
    
    def _find_similar_range_matches(
        self, 
        df: pd.DataFrame, 
        range_info: Dict[str, Any], 
        exclude_products: List[ProductRecord]
    ) -> List[ProductRecord]:
        """Find similar ranges that might be related"""
        
        products = []
        range_label = range_info['range_label']
        
        if not range_label:
            return products
        
        # Get identifiers to exclude
        exclude_ids = {p.product_identifier for p in exclude_products}
        
        # Fuzzy matching for similar ranges
        similar_ranges = df[
            df['range_norm'].apply(lambda x: fuzz.ratio(range_label, x) > 70 if x else False)
        ]
        
        for _, row in similar_ranges.iterrows():
            if row['PRODUCT_IDENTIFIER'] not in exclude_ids:
                # Calculate similarity confidence
                similarity = fuzz.ratio(range_label, row['range_norm']) / 100.0
                
                product = ProductRecord(
                    product_identifier=row['PRODUCT_IDENTIFIER'],
                    product_type=row['PRODUCT_TYPE'],
                    product_description=row['PRODUCT_DESCRIPTION'],
                    brand_code=row['BRAND_CODE'],
                    brand_label=row['BRAND_LABEL'],
                    range_code=row['RANGE_CODE'],
                    range_label=row['RANGE_LABEL'],
                    subrange_code=row['SUBRANGE_CODE'],
                    subrange_label=row['SUBRANGE_LABEL'],
                    devicetype_label=row['DEVICETYPE_LABEL'],
                    pl_services=row['PL_SERVICES'],
                    confidence_score=similarity * 0.8,  # Reduced confidence for similar matches
                    match_reason="similar_range_match",
                    series_membership="related"
                )
                products.append(product)
        
        return products[:10]  # Limit similar matches to prevent overwhelming results
    
    def _create_product_range(self, range_info: Dict[str, Any], products: List[ProductRecord]) -> ProductRange:
        """Create a ProductRange object with comprehensive analysis"""
        
        # Coverage analysis
        coverage_analysis = {
            'total_products': len(products),
            'confidence_distribution': self._analyze_confidence_distribution(products),
            'brand_coverage': self._analyze_brand_coverage(products),
            'device_type_coverage': self._analyze_device_type_coverage(products),
            'subrange_coverage': self._analyze_subrange_coverage(products)
        }
        
        # Business impact analysis
        business_impact = {
            'affected_product_count': len(products),
            'primary_brands': list(coverage_analysis['brand_coverage'].keys())[:3],
            'device_categories': list(coverage_analysis['device_type_coverage'].keys())[:5],
            'complexity_assessment': self._assess_range_complexity(products)
        }
        
        # Calculate overall range confidence
        if products:
            range_confidence = sum(p.confidence_score for p in products) / len(products)
        else:
            range_confidence = 0.0
        
        return ProductRange(
            range_identifier=f"{range_info['range_label']}_{range_info.get('subrange_label', '')}",
            range_label=range_info['range_label'],
            subrange_label=range_info.get('subrange_label', ''),
            product_line=products[0].pl_services if products else '',
            total_products=len(products),
            products=products,
            range_confidence=range_confidence,
            coverage_analysis=coverage_analysis,
            business_impact=business_impact
        )
    
    def _analyze_confidence_distribution(self, products: List[ProductRecord]) -> Dict[str, int]:
        """Analyze confidence score distribution"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for product in products:
            if product.confidence_score >= 0.80:
                distribution['high'] += 1
            elif product.confidence_score >= 0.60:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution
    
    def _analyze_brand_coverage(self, products: List[ProductRecord]) -> Dict[str, int]:
        """Analyze brand distribution"""
        brand_count = defaultdict(int)
        for product in products:
            brand_count[product.brand_label] += 1
        return dict(brand_count)
    
    def _analyze_device_type_coverage(self, products: List[ProductRecord]) -> Dict[str, int]:
        """Analyze device type distribution"""
        device_count = defaultdict(int)
        for product in products:
            device_count[product.devicetype_label] += 1
        return dict(device_count)
    
    def _analyze_subrange_coverage(self, products: List[ProductRecord]) -> Dict[str, int]:
        """Analyze subrange distribution"""
        subrange_count = defaultdict(int)
        for product in products:
            if product.subrange_label:
                subrange_count[product.subrange_label] += 1
        return dict(subrange_count)
    
    def _assess_range_complexity(self, products: List[ProductRecord]) -> str:
        """Assess the complexity of the product range"""
        if len(products) > 50:
            return "high_complexity"
        elif len(products) > 20:
            return "medium_complexity"
        elif len(products) > 5:
            return "low_complexity"
        else:
            return "simple_range"
    
    def _analyze_business_impact(self, ranges: List[ProductRange], total_products: int) -> Dict[str, Any]:
        """Analyze overall business impact"""
        
        all_brands = set()
        all_device_types = set()
        complexity_levels = []
        
        for range_obj in ranges:
            all_brands.update(range_obj.coverage_analysis['brand_coverage'].keys())
            all_device_types.update(range_obj.coverage_analysis['device_type_coverage'].keys())
            complexity_levels.append(range_obj.business_impact['complexity_assessment'])
        
        return {
            'total_affected_products': total_products,
            'affected_brands': list(all_brands),
            'affected_device_types': list(all_device_types),
            'range_complexity_distribution': {level: complexity_levels.count(level) for level in set(complexity_levels)},
            'business_criticality': self._assess_business_criticality(total_products, len(all_brands)),
            'modernization_scope': self._assess_modernization_scope(ranges)
        }
    
    def _assess_business_criticality(self, product_count: int, brand_count: int) -> str:
        """Assess business criticality based on scope"""
        if product_count > 100 or brand_count > 3:
            return "critical"
        elif product_count > 50 or brand_count > 2:
            return "high"
        elif product_count > 20:
            return "medium"
        else:
            return "low"
    
    def _assess_modernization_scope(self, ranges: List[ProductRange]) -> str:
        """Assess modernization scope requirements"""
        total_ranges = len(ranges)
        total_products = sum(r.total_products for r in ranges)
        
        if total_ranges > 3 and total_products > 100:
            return "comprehensive_program"
        elif total_ranges > 2 or total_products > 50:
            return "major_initiative"
        elif total_products > 20:
            return "focused_project"
        else:
            return "targeted_replacement"
    
    def _determine_confidence_level(self, ranges: List[ProductRange]) -> str:
        """Determine overall confidence level"""
        if not ranges:
            return "NO_MATCH"
        
        avg_confidence = sum(r.range_confidence for r in ranges) / len(ranges)
        
        if avg_confidence >= 0.90:
            return "EXACT"
        elif avg_confidence >= 0.75:
            return "HIGH"
        elif avg_confidence >= 0.60:
            return "MEDIUM"
        elif avg_confidence >= 0.40:
            return "LOW"
        else:
            return "UNCERTAIN"
    
    def export_comprehensive_results(
        self, 
        result: RangeMappingResult, 
        export_format: str = "json",
        include_details: bool = True
    ) -> str:
        """Export comprehensive range mapping results"""
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if export_format == "json":
            export_data = {
                "sota_range_mapping_analysis": {
                    "metadata": {
                        "timestamp": timestamp,
                        "input_context": result.input_context,
                        "processing_time_ms": result.processing_time_ms,
                        "search_strategy": result.search_strategy,
                        "confidence_level": result.confidence_level
                    },
                    "summary": {
                        "total_ranges_detected": len(result.detected_ranges),
                        "total_products_found": result.total_products_found,
                        "business_impact": result.business_analysis
                    },
                    "detected_ranges": []
                }
            }
            
            # Add detailed range information
            for range_obj in result.detected_ranges:
                range_data = {
                    "range_identifier": range_obj.range_identifier,
                    "range_label": range_obj.range_label,
                    "subrange_label": range_obj.subrange_label,
                    "product_line": range_obj.product_line,
                    "total_products": range_obj.total_products,
                    "range_confidence": range_obj.range_confidence,
                    "coverage_analysis": range_obj.coverage_analysis,
                    "business_impact": range_obj.business_impact
                }
                
                if include_details:
                    range_data["products"] = [
                        {
                            "product_identifier": p.product_identifier,
                            "product_type": p.product_type,
                            "product_description": p.product_description,
                            "brand_label": p.brand_label,
                            "range_label": p.range_label,
                            "subrange_label": p.subrange_label,
                            "devicetype_label": p.devicetype_label,
                            "confidence_score": p.confidence_score,
                            "match_reason": p.match_reason,
                            "series_membership": p.series_membership
                        }
                        for p in range_obj.products
                    ]
                
                export_data["sota_range_mapping_analysis"]["detected_ranges"].append(range_data)
            
            output_file = f"sota_range_mapping_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"📤 SOTA range mapping results exported to {output_file}")
            return output_file
        
        else:
            raise ValueError(f"Unsupported export format: {export_format}")


def main():
    """Demonstration of SOTA Range Mapping Service"""
    
    logger.info("🚀 SOTA Range Mapping Service - Comprehensive Demo")
    logger.info("🎯 Finding ALL products in ranges/series mentioned in obsolescence letters")
    
    # Initialize SOTA service
    mapping_service = SOTARangeMappingService()
    
    # Comprehensive test scenarios
    test_scenarios = [
        {
            "name": "Galaxy 6000 Series - Complete Range Analysis",
            "description": "Finding ALL Galaxy 6000 series products",
            "product_identifier": "Galaxy 6000",
            "range_label": "Galaxy",
            "subrange_label": "6000",
            "product_line": "SPIBS",
            "context_description": "MGE Galaxy UPS series 6000 range uninterruptible power supply",
            "expected_products": "Multiple variants: 250VA, 500VA, 1000VA, 3-phase, single-phase"
        },
        {
            "name": "SEPAM Protection Range - Complete Family",
            "description": "Finding ALL SEPAM protection relay products",
            "product_identifier": "SEPAM 2040",
            "range_label": "SEPAM",
            "subrange_label": "40",
            "product_line": "DPIBS",
            "context_description": "SEPAM protection relay series 40 range digital protection",
            "expected_products": "Multiple protection relay variants and configurations"
        },
        {
            "name": "Masterpact NT Series - Switchgear Range",
            "description": "Finding ALL Masterpact NT switchgear products",
            "product_identifier": "Masterpact NT",
            "range_label": "Masterpact",
            "subrange_label": "NT",
            "product_line": "PPIBS",
            "context_description": "Masterpact NT circuit breaker series low voltage switchgear range",
            "expected_products": "Multiple current ratings and configurations"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n{'='*100}")
        logger.info(f"🧪 Test Scenario {i}: {scenario['name']}")
        logger.info(f"📝 Description: {scenario['description']}")
        logger.info(f"🎯 Expected: {scenario['expected_products']}")
        logger.info(f"{'='*100}")
        
        # Execute SOTA range mapping
        result = mapping_service.map_letter_to_product_ranges(
            product_identifier=scenario["product_identifier"],
            range_label=scenario["range_label"],
            subrange_label=scenario["subrange_label"],
            product_line=scenario["product_line"],
            context_description=scenario["context_description"],
            include_similar_ranges=True
        )
        
        # Display comprehensive results
        logger.info(f"⏱️ Processing Time: {result.processing_time_ms:.1f}ms")
        logger.info(f"🎯 Confidence Level: {result.confidence_level}")
        logger.info(f"📊 Total Ranges Found: {len(result.detected_ranges)}")
        logger.info(f"📦 Total Products Found: {result.total_products_found}")
        
        # Business impact analysis
        business = result.business_analysis
        logger.info(f"\n💼 Business Impact Analysis:")
        logger.info(f"  🏭 Affected Brands: {', '.join(business['affected_brands'][:5])}")
        logger.info(f"  🔧 Device Categories: {', '.join(business['affected_device_types'][:5])}")
        logger.info(f"  ⚠️ Business Criticality: {business['business_criticality']}")
        logger.info(f"  🔄 Modernization Scope: {business['modernization_scope']}")
        
        # Detailed range analysis
        logger.info(f"\n📋 Detailed Range Analysis:")
        for j, range_obj in enumerate(result.detected_ranges, 1):
            logger.info(f"\n  📦 Range {j}: {range_obj.range_label} / {range_obj.subrange_label}")
            logger.info(f"    🔢 Products: {range_obj.total_products}")
            logger.info(f"    🎯 Confidence: {range_obj.range_confidence:.3f}")
            logger.info(f"    💼 PL Services: {range_obj.product_line}")
            logger.info(f"    🏭 Brands: {', '.join(range_obj.coverage_analysis['brand_coverage'].keys())}")
            logger.info(f"    🔧 Device Types: {len(range_obj.coverage_analysis['device_type_coverage'])} types")
            logger.info(f"    📊 Complexity: {range_obj.business_impact['complexity_assessment']}")
            
            # Show sample products
            logger.info(f"    📋 Sample Products:")
            for k, product in enumerate(range_obj.products[:5], 1):
                logger.info(f"      {k}. {product.product_identifier} - {product.product_type}")
                logger.info(f"         {product.brand_label} | {product.devicetype_label}")
                logger.info(f"         Confidence: {product.confidence_score:.3f} | {product.match_reason}")
            
            if range_obj.total_products > 5:
                logger.info(f"      ... and {range_obj.total_products - 5} more products")
        
        # Export results
        output_file = mapping_service.export_comprehensive_results(result, "json", include_details=True)
        logger.info(f"\n📁 Comprehensive results exported to: {output_file}")


if __name__ == "__main__":
    main() 