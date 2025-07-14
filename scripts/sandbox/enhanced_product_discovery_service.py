#!/usr/bin/env python3
"""
Enhanced Product Discovery Service - SOTA Techniques
Intelligently expands search space using technical specifications for maximum accuracy

Features:
- Technical specification-based filtering
- Multi-dimensional search expansion
- Semantic similarity matching
- Range-aware product discovery
- Confidence scoring and ranking
- SOTA accuracy optimization

Version: 1.0.0
Author: SE Letters Team
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import duckdb
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from loguru import logger


class SearchStrategy(Enum):
    """Advanced search strategies"""
    EXACT_TECHNICAL_MATCH = "exact_technical_match"
    RANGE_EXPANSION = "range_expansion"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    HYBRID_MULTI_MODAL = "hybrid_multi_modal"
    SPECIFICATION_FUZZY = "specification_fuzzy"


@dataclass
class TechnicalSpecification:
    """Enhanced technical specification with normalization"""
    voltage_levels: List[str]
    current_ratings: List[str] 
    power_ratings: List[str]
    frequencies: List[str]
    raw_specs: Dict[str, Any]
    
    def normalize_voltage(self, voltage_str: str) -> Optional[Tuple[float, float]]:
        """Extract voltage range as (min, max) in kV"""
        if not voltage_str:
            return None
            
        # Handle ranges like "12 – 17.5kV", "6-24kV", "24kV"
        voltage_patterns = [
            r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)(?:kV|KV)',  # Range
            r'(\d+(?:\.\d+)?)(?:kV|KV)',  # Single value
            r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)',  # Range without unit
        ]
        
        for pattern in voltage_patterns:
            match = re.search(pattern, voltage_str, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    return (float(match.group(1)), float(match.group(2)))
                else:
                    val = float(match.group(1))
                    return (val, val)
        return None
    
    def normalize_current(self, current_str: str) -> Optional[float]:
        """Extract current rating in Amperes"""
        if not current_str:
            return None
            
        # Handle "up to 3150A", "1600A", "630-1250A"
        current_patterns = [
            r'up\s+to\s+(\d+(?:\.\d+)?)(?:A|a|Amp)',
            r'(\d+(?:\.\d+)?)(?:A|a|Amp)',
            r'(\d+(?:\.\d+)?)',  # Numbers only
        ]
        
        for pattern in current_patterns:
            match = re.search(pattern, current_str, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    def normalize_frequency(self, frequency_str: str) -> Optional[List[float]]:
        """Extract frequency values in Hz"""
        if not frequency_str:
            return None
            
        # Handle "50/60Hz", "50Hz", "60Hz"
        freq_pattern = r'(\d+)(?:/(\d+))?(?:Hz|hz)'
        match = re.search(freq_pattern, frequency_str, re.IGNORECASE)
        
        if match:
            freqs = [float(match.group(1))]
            if match.group(2):
                freqs.append(float(match.group(2)))
            return freqs
        return None


@dataclass
class ProductMatch:
    """Enhanced product match with detailed scoring"""
    product_id: str
    range_label: str
    subrange_label: str
    product_description: str
    technical_details: Dict[str, Any]
    match_confidence: float
    match_reasons: List[str]
    specification_match_score: float
    semantic_similarity_score: float
    range_match_score: float
    overall_score: float
    search_strategy: SearchStrategy


@dataclass
class DiscoveryResult:
    """Comprehensive discovery result"""
    primary_matches: List[ProductMatch]
    secondary_matches: List[ProductMatch] 
    total_products_found: int
    search_strategies_used: List[SearchStrategy]
    processing_time_ms: float
    confidence_distribution: Dict[str, int]
    technical_coverage: Dict[str, float]
    search_effectiveness: float


class EnhancedProductDiscoveryService:
    """State-of-the-art product discovery with technical specification intelligence"""
    
    def __init__(self, database_path: str = "../../data/IBcatalogue.duckdb"):
        """Initialize enhanced discovery service"""
        self.database_path = database_path
        
        # Initialize semantic model for advanced similarity
        logger.info("🧠 Loading semantic similarity model...")
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Technical specification weights
        self.spec_weights = {
            'voltage_match': 0.35,
            'current_match': 0.25, 
            'frequency_match': 0.15,
            'range_match': 0.25
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'high_confidence': 0.85,
            'medium_confidence': 0.70,
            'low_confidence': 0.50
        }
        
        logger.info(f"🔍 Enhanced Product Discovery Service initialized")
    
    def discover_products(
        self, 
        grok_metadata: Dict[str, Any],
        search_strategies: Optional[List[SearchStrategy]] = None
    ) -> DiscoveryResult:
        """
        Discover all products affected by obsolescence letter using SOTA techniques
        
        Args:
            grok_metadata: Complete Grok extraction metadata
            search_strategies: Specific strategies to use (default: all)
            
        Returns:
            Comprehensive discovery result with ranked products
        """
        start_time = time.time()
        
        if search_strategies is None:
            search_strategies = list(SearchStrategy)
        
        logger.info(f"🎯 Starting enhanced product discovery with {len(search_strategies)} strategies")
        
        # Extract and normalize technical specifications
        tech_specs = self._extract_technical_specifications(grok_metadata)
        
        # Extract product range information
        product_ranges = self._extract_product_ranges(grok_metadata)
        
        # Execute search strategies
        all_matches = []
        strategy_results = {}
        
        for strategy in search_strategies:
            logger.info(f"🔍 Executing strategy: {strategy.value}")
            matches = self._execute_search_strategy(strategy, tech_specs, product_ranges, grok_metadata)
            strategy_results[strategy] = matches
            all_matches.extend(matches)
        
        # Deduplicate and rank results
        deduplicated_matches = self._deduplicate_and_rank(all_matches)
        
        # Categorize matches by confidence
        primary_matches = [m for m in deduplicated_matches if m.overall_score >= self.confidence_thresholds['high_confidence']]
        secondary_matches = [m for m in deduplicated_matches if m.overall_score >= self.confidence_thresholds['medium_confidence'] and m.overall_score < self.confidence_thresholds['high_confidence']]
        
        # Calculate analytics
        processing_time_ms = (time.time() - start_time) * 1000
        confidence_distribution = self._calculate_confidence_distribution(deduplicated_matches)
        technical_coverage = self._calculate_technical_coverage(deduplicated_matches, tech_specs)
        search_effectiveness = self._calculate_search_effectiveness(strategy_results)
        
        result = DiscoveryResult(
            primary_matches=primary_matches,
            secondary_matches=secondary_matches,
            total_products_found=len(deduplicated_matches),
            search_strategies_used=search_strategies,
            processing_time_ms=processing_time_ms,
            confidence_distribution=confidence_distribution,
            technical_coverage=technical_coverage,
            search_effectiveness=search_effectiveness
        )
        
        logger.info(f"✅ Discovery completed: {len(primary_matches)} primary matches, {len(secondary_matches)} secondary matches")
        logger.info(f"⏱️ Processing time: {processing_time_ms:.2f}ms")
        
        return result
    
    def _extract_technical_specifications(self, grok_metadata: Dict[str, Any]) -> TechnicalSpecification:
        """Extract and normalize technical specifications"""
        tech_specs_raw = grok_metadata.get('technical_specifications', {})
        
        return TechnicalSpecification(
            voltage_levels=tech_specs_raw.get('voltage_levels', []),
            current_ratings=tech_specs_raw.get('current_ratings', []),
            power_ratings=tech_specs_raw.get('power_ratings', []),
            frequencies=tech_specs_raw.get('frequencies', []),
            raw_specs=tech_specs_raw
        )
    
    def _extract_product_ranges(self, grok_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product range information"""
        products = grok_metadata.get('products', [])
        ranges = []
        
        for product in products:
            ranges.append({
                'product_identifier': product.get('product_identifier', ''),
                'range_label': product.get('range_label', ''),
                'subrange_label': product.get('subrange_label', ''),
                'product_line': product.get('product_line', ''),
                'product_description': product.get('product_description', '')
            })
        
        return ranges
    
    def _execute_search_strategy(
        self,
        strategy: SearchStrategy,
        tech_specs: TechnicalSpecification,
        product_ranges: List[Dict[str, Any]],
        grok_metadata: Dict[str, Any]
    ) -> List[ProductMatch]:
        """Execute specific search strategy"""
        
        if strategy == SearchStrategy.EXACT_TECHNICAL_MATCH:
            return self._exact_technical_match(tech_specs, product_ranges)
        
        elif strategy == SearchStrategy.RANGE_EXPANSION:
            return self._range_expansion_search(product_ranges, tech_specs)
        
        elif strategy == SearchStrategy.SEMANTIC_SIMILARITY:
            return self._semantic_similarity_search(grok_metadata, tech_specs)
        
        elif strategy == SearchStrategy.HYBRID_MULTI_MODAL:
            return self._hybrid_multi_modal_search(tech_specs, product_ranges, grok_metadata)
        
        elif strategy == SearchStrategy.SPECIFICATION_FUZZY:
            return self._specification_fuzzy_search(tech_specs, product_ranges)
        
        else:
            logger.warning(f"⚠️ Unknown search strategy: {strategy}")
            return []
    
    def _exact_technical_match(self, tech_specs: TechnicalSpecification, product_ranges: List[Dict[str, Any]]) -> List[ProductMatch]:
        """Find products with exact technical specification matches"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                # Build technical specification filters
                voltage_conditions = []
                current_conditions = []
                frequency_conditions = []
                
                # Process voltage specifications
                for voltage_str in tech_specs.voltage_levels:
                    voltage_range = tech_specs.normalize_voltage(voltage_str)
                    if voltage_range:
                        min_v, max_v = voltage_range
                        voltage_conditions.append(f"(voltage_kv >= {min_v} AND voltage_kv <= {max_v})")
                
                # Process current specifications  
                for current_str in tech_specs.current_ratings:
                    current_val = tech_specs.normalize_current(current_str)
                    if current_val:
                        current_conditions.append(f"current_rating_a <= {current_val}")
                
                # Process frequency specifications
                for freq_str in tech_specs.frequencies:
                    freqs = tech_specs.normalize_frequency(freq_str)
                    if freqs:
                        freq_conditions = []
                        for freq in freqs:
                            freq_conditions.append(f"frequency_hz = {freq}")
                        frequency_conditions.append(f"({' OR '.join(freq_conditions)})")
                
                # Build main query with technical filters
                base_query = """
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label, 
                        product_description,
                        pl_services,
                        brand_label,
                        commercial_status,
                        COALESCE(voltage_kv, 0) as voltage_kv,
                        COALESCE(current_rating_a, 0) as current_rating_a,
                        COALESCE(frequency_hz, 0) as frequency_hz,
                        COALESCE(power_rating_kw, 0) as power_rating_kw
                    FROM products 
                    WHERE 1=1
                """
                
                # Add range filters
                if product_ranges:
                    range_filters = []
                    for range_info in product_ranges:
                        range_label = range_info.get('range_label', '')
                        if range_label:
                            range_filters.append(f"range_label ILIKE '%{range_label}%'")
                    
                    if range_filters:
                        base_query += f" AND ({' OR '.join(range_filters)})"
                
                # Add technical specification filters
                if voltage_conditions:
                    base_query += f" AND ({' OR '.join(voltage_conditions)})"
                
                if current_conditions:
                    base_query += f" AND ({' AND '.join(current_conditions)})"
                
                if frequency_conditions:
                    base_query += f" AND ({' OR '.join(frequency_conditions)})"
                
                # Execute query
                results = conn.execute(base_query).fetchall()
                columns = [desc[0] for desc in conn.description]
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    
                    # Calculate specification match score
                    spec_score = self._calculate_specification_score(product_data, tech_specs)
                    
                    match = ProductMatch(
                        product_id=product_data['product_identifier'],
                        range_label=product_data['range_label'],
                        subrange_label=product_data['subrange_label'],
                        product_description=product_data['product_description'],
                        technical_details=product_data,
                        match_confidence=spec_score,
                        match_reasons=['exact_technical_match'],
                        specification_match_score=spec_score,
                        semantic_similarity_score=0.0,
                        range_match_score=1.0,
                        overall_score=spec_score,
                        search_strategy=SearchStrategy.EXACT_TECHNICAL_MATCH
                    )
                    
                    matches.append(match)
                    
        except Exception as e:
            logger.error(f"❌ Exact technical match failed: {e}")
        
        logger.info(f"🎯 Exact technical match found {len(matches)} products")
        return matches
    
    def _range_expansion_search(self, product_ranges: List[Dict[str, Any]], tech_specs: TechnicalSpecification) -> List[ProductMatch]:
        """Expand search within product ranges using fuzzy matching"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                for range_info in product_ranges:
                    range_label = range_info.get('range_label', '')
                    product_line = range_info.get('product_line', '')
                    
                    # Build flexible range query
                    query = """
                        SELECT 
                            product_identifier,
                            range_label,
                            subrange_label,
                            product_description,
                            pl_services,
                            brand_label,
                            commercial_status,
                            COALESCE(voltage_kv, 0) as voltage_kv,
                            COALESCE(current_rating_a, 0) as current_rating_a,
                            COALESCE(frequency_hz, 0) as frequency_hz
                        FROM products 
                        WHERE (
                            range_label ILIKE ? OR
                            subrange_label ILIKE ? OR
                            product_description ILIKE ? OR
                            pl_services ILIKE ?
                        )
                    """
                    
                    # Create search patterns
                    patterns = [
                        f"%{range_label}%",
                        f"%{range_label}%", 
                        f"%{range_label}%",
                        f"%{product_line}%" if product_line else f"%{range_label}%"
                    ]
                    
                    results = conn.execute(query, patterns).fetchall()
                    columns = [desc[0] for desc in conn.description]
                    
                    for row in results:
                        product_data = dict(zip(columns, row))
                        
                        # Calculate range match score
                        range_score = self._calculate_range_similarity(product_data, range_info)
                        
                        # Calculate technical compatibility
                        tech_score = self._calculate_specification_score(product_data, tech_specs)
                        
                        # Combined score
                        overall_score = (range_score * 0.6) + (tech_score * 0.4)
                        
                        match = ProductMatch(
                            product_id=product_data['product_identifier'],
                            range_label=product_data['range_label'],
                            subrange_label=product_data['subrange_label'],
                            product_description=product_data['product_description'],
                            technical_details=product_data,
                            match_confidence=overall_score,
                            match_reasons=['range_expansion', 'fuzzy_range_match'],
                            specification_match_score=tech_score,
                            semantic_similarity_score=0.0,
                            range_match_score=range_score,
                            overall_score=overall_score,
                            search_strategy=SearchStrategy.RANGE_EXPANSION
                        )
                        
                        matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Range expansion search failed: {e}")
        
        logger.info(f"🔄 Range expansion found {len(matches)} products")
        return matches
    
    def _semantic_similarity_search(self, grok_metadata: Dict[str, Any], tech_specs: TechnicalSpecification) -> List[ProductMatch]:
        """Use semantic similarity for advanced product matching"""
        matches = []
        
        try:
            # Create semantic query from Grok metadata
            query_text = self._build_semantic_query(grok_metadata)
            query_embedding = self.semantic_model.encode([query_text])
            
            with duckdb.connect(self.database_path) as conn:
                # Get all products for semantic comparison
                results = conn.execute("""
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        pl_services,
                        brand_label,
                        COALESCE(voltage_kv, 0) as voltage_kv,
                        COALESCE(current_rating_a, 0) as current_rating_a,
                        COALESCE(frequency_hz, 0) as frequency_hz
                    FROM products 
                    WHERE product_description IS NOT NULL
                    LIMIT 5000  -- Limit for performance
                """).fetchall()
                
                columns = [desc[0] for desc in conn.description]
                
                # Build product embeddings
                product_texts = []
                product_data_list = []
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    product_text = f"{product_data['range_label']} {product_data['product_description']}"
                    product_texts.append(product_text)
                    product_data_list.append(product_data)
                
                if product_texts:
                    # Generate embeddings
                    product_embeddings = self.semantic_model.encode(product_texts)
                    
                    # Calculate similarities
                    similarities = cosine_similarity(query_embedding, product_embeddings)[0]
                    
                    # Create matches for high similarity products
                    for i, similarity in enumerate(similarities):
                        if similarity >= 0.3:  # Semantic similarity threshold
                            product_data = product_data_list[i]
                            
                            # Calculate technical compatibility
                            tech_score = self._calculate_specification_score(product_data, tech_specs)
                            
                            # Combined score
                            overall_score = (similarity * 0.5) + (tech_score * 0.5)
                            
                            match = ProductMatch(
                                product_id=product_data['product_identifier'],
                                range_label=product_data['range_label'],
                                subrange_label=product_data['subrange_label'],
                                product_description=product_data['product_description'],
                                technical_details=product_data,
                                match_confidence=overall_score,
                                match_reasons=['semantic_similarity', f'similarity_{similarity:.3f}'],
                                specification_match_score=tech_score,
                                semantic_similarity_score=similarity,
                                range_match_score=0.0,
                                overall_score=overall_score,
                                search_strategy=SearchStrategy.SEMANTIC_SIMILARITY
                            )
                            
                            matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Semantic similarity search failed: {e}")
        
        logger.info(f"🧠 Semantic similarity found {len(matches)} products")
        return matches
    
    def _hybrid_multi_modal_search(
        self,
        tech_specs: TechnicalSpecification,
        product_ranges: List[Dict[str, Any]],
        grok_metadata: Dict[str, Any]
    ) -> List[ProductMatch]:
        """Combine multiple search modalities for maximum coverage"""
        matches = []
        
        # Execute sub-strategies
        exact_matches = self._exact_technical_match(tech_specs, product_ranges)
        range_matches = self._range_expansion_search(product_ranges, tech_specs)
        semantic_matches = self._semantic_similarity_search(grok_metadata, tech_specs)
        
        # Combine and weight results
        all_matches = exact_matches + range_matches + semantic_matches
        
        # Re-score with hybrid approach
        for match in all_matches:
            # Hybrid scoring: technical + semantic + range
            hybrid_score = (
                match.specification_match_score * self.spec_weights['voltage_match'] +
                match.semantic_similarity_score * 0.3 +
                match.range_match_score * 0.3 +
                0.1  # Base boost for hybrid approach
            )
            
            match.overall_score = min(hybrid_score, 1.0)
            match.search_strategy = SearchStrategy.HYBRID_MULTI_MODAL
            match.match_reasons.append('hybrid_multi_modal')
            
            matches.append(match)
        
        logger.info(f"🔄 Hybrid multi-modal found {len(matches)} products")
        return matches
    
    def _specification_fuzzy_search(self, tech_specs: TechnicalSpecification, product_ranges: List[Dict[str, Any]]) -> List[ProductMatch]:
        """Fuzzy matching on technical specifications with tolerance"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                # Build fuzzy specification query with tolerance ranges
                voltage_conditions = []
                
                for voltage_str in tech_specs.voltage_levels:
                    voltage_range = tech_specs.normalize_voltage(voltage_str)
                    if voltage_range:
                        min_v, max_v = voltage_range
                        # Add 20% tolerance
                        tolerance = (max_v - min_v) * 0.2 if max_v > min_v else max_v * 0.2
                        fuzzy_min = max(0, min_v - tolerance)
                        fuzzy_max = max_v + tolerance
                        voltage_conditions.append(f"(voltage_kv >= {fuzzy_min} AND voltage_kv <= {fuzzy_max})")
                
                query = """
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        pl_services,
                        COALESCE(voltage_kv, 0) as voltage_kv,
                        COALESCE(current_rating_a, 0) as current_rating_a,
                        COALESCE(frequency_hz, 0) as frequency_hz
                    FROM products 
                    WHERE 1=1
                """
                
                if voltage_conditions:
                    query += f" AND ({' OR '.join(voltage_conditions)})"
                
                # Add range filters
                if product_ranges:
                    range_filters = []
                    for range_info in product_ranges:
                        range_label = range_info.get('range_label', '')
                        if range_label:
                            # Fuzzy range matching
                            range_filters.append(f"(range_label ILIKE '%{range_label[:3]}%' OR product_description ILIKE '%{range_label[:5]}%')")
                    
                    if range_filters:
                        query += f" AND ({' OR '.join(range_filters)})"
                
                results = conn.execute(query).fetchall()
                columns = [desc[0] for desc in conn.description]
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    
                    # Calculate fuzzy match score
                    fuzzy_score = self._calculate_fuzzy_specification_score(product_data, tech_specs)
                    
                    match = ProductMatch(
                        product_id=product_data['product_identifier'],
                        range_label=product_data['range_label'],
                        subrange_label=product_data['subrange_label'],
                        product_description=product_data['product_description'],
                        technical_details=product_data,
                        match_confidence=fuzzy_score,
                        match_reasons=['fuzzy_specification_match'],
                        specification_match_score=fuzzy_score,
                        semantic_similarity_score=0.0,
                        range_match_score=0.0,
                        overall_score=fuzzy_score,
                        search_strategy=SearchStrategy.SPECIFICATION_FUZZY
                    )
                    
                    matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Fuzzy specification search failed: {e}")
        
        logger.info(f"🔀 Fuzzy specification found {len(matches)} products")
        return matches
    
    def _calculate_specification_score(self, product_data: Dict[str, Any], tech_specs: TechnicalSpecification) -> float:
        """Calculate technical specification match score"""
        score = 0.0
        total_weight = 0.0
        
        # Voltage matching
        product_voltage = product_data.get('voltage_kv', 0)
        if product_voltage > 0:
            for voltage_str in tech_specs.voltage_levels:
                voltage_range = tech_specs.normalize_voltage(voltage_str)
                if voltage_range:
                    min_v, max_v = voltage_range
                    if min_v <= product_voltage <= max_v:
                        score += self.spec_weights['voltage_match']
                        break
            total_weight += self.spec_weights['voltage_match']
        
        # Current matching
        product_current = product_data.get('current_rating_a', 0)
        if product_current > 0:
            for current_str in tech_specs.current_ratings:
                current_val = tech_specs.normalize_current(current_str)
                if current_val and product_current <= current_val:
                    score += self.spec_weights['current_match']
                    break
            total_weight += self.spec_weights['current_match']
        
        # Frequency matching
        product_freq = product_data.get('frequency_hz', 0)
        if product_freq > 0:
            for freq_str in tech_specs.frequencies:
                freqs = tech_specs.normalize_frequency(freq_str)
                if freqs and product_freq in freqs:
                    score += self.spec_weights['frequency_match']
                    break
            total_weight += self.spec_weights['frequency_match']
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_fuzzy_specification_score(self, product_data: Dict[str, Any], tech_specs: TechnicalSpecification) -> float:
        """Calculate fuzzy specification match with tolerance"""
        score = 0.0
        total_weight = 0.0
        
        # Fuzzy voltage matching with tolerance
        product_voltage = product_data.get('voltage_kv', 0)
        if product_voltage > 0:
            for voltage_str in tech_specs.voltage_levels:
                voltage_range = tech_specs.normalize_voltage(voltage_str)
                if voltage_range:
                    min_v, max_v = voltage_range
                    tolerance = (max_v - min_v) * 0.2 if max_v > min_v else max_v * 0.2
                    fuzzy_min = max(0, min_v - tolerance)
                    fuzzy_max = max_v + tolerance
                    
                    if fuzzy_min <= product_voltage <= fuzzy_max:
                        # Calculate closeness score
                        center = (min_v + max_v) / 2
                        distance = abs(product_voltage - center)
                        max_distance = max(max_v - center, center - min_v)
                        closeness = 1 - (distance / max_distance) if max_distance > 0 else 1
                        score += self.spec_weights['voltage_match'] * closeness
                        break
            total_weight += self.spec_weights['voltage_match']
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_range_similarity(self, product_data: Dict[str, Any], range_info: Dict[str, Any]) -> float:
        """Calculate range name similarity"""
        product_range = product_data.get('range_label', '').lower()
        target_range = range_info.get('range_label', '').lower()
        
        if not product_range or not target_range:
            return 0.0
        
        # Simple similarity scoring
        if product_range == target_range:
            return 1.0
        elif target_range in product_range or product_range in target_range:
            return 0.8
        else:
            # Check word overlap
            product_words = set(product_range.split())
            target_words = set(target_range.split())
            overlap = len(product_words & target_words)
            total = len(product_words | target_words)
            return overlap / total if total > 0 else 0.0
    
    def _build_semantic_query(self, grok_metadata: Dict[str, Any]) -> str:
        """Build semantic query from Grok metadata"""
        query_parts = []
        
        # Document information
        doc_info = grok_metadata.get('document_information', {})
        if doc_info.get('document_title'):
            query_parts.append(doc_info['document_title'])
        
        # Product information
        products = grok_metadata.get('products', [])
        for product in products:
            if product.get('product_description'):
                query_parts.append(product['product_description'])
            if product.get('range_label'):
                query_parts.append(product['range_label'])
        
        # Technical specifications
        tech_specs = grok_metadata.get('technical_specifications', {})
        for spec_type, spec_values in tech_specs.items():
            if isinstance(spec_values, list):
                query_parts.extend(spec_values)
        
        return ' '.join(query_parts)
    
    def _deduplicate_and_rank(self, matches: List[ProductMatch]) -> List[ProductMatch]:
        """Remove duplicates and rank by overall score"""
        seen_products = set()
        unique_matches = []
        
        # Sort by overall score (descending)
        sorted_matches = sorted(matches, key=lambda x: x.overall_score, reverse=True)
        
        for match in sorted_matches:
            product_key = (match.product_id, match.range_label)
            if product_key not in seen_products:
                seen_products.add(product_key)
                unique_matches.append(match)
        
        return unique_matches
    
    def _calculate_confidence_distribution(self, matches: List[ProductMatch]) -> Dict[str, int]:
        """Calculate confidence score distribution"""
        distribution = {
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'very_low_confidence': 0
        }
        
        for match in matches:
            if match.overall_score >= self.confidence_thresholds['high_confidence']:
                distribution['high_confidence'] += 1
            elif match.overall_score >= self.confidence_thresholds['medium_confidence']:
                distribution['medium_confidence'] += 1
            elif match.overall_score >= self.confidence_thresholds['low_confidence']:
                distribution['low_confidence'] += 1
            else:
                distribution['very_low_confidence'] += 1
        
        return distribution
    
    def _calculate_technical_coverage(self, matches: List[ProductMatch], tech_specs: TechnicalSpecification) -> Dict[str, float]:
        """Calculate how well technical specifications are covered"""
        coverage = {
            'voltage_coverage': 0.0,
            'current_coverage': 0.0,
            'frequency_coverage': 0.0,
            'overall_coverage': 0.0
        }
        
        if not matches:
            return coverage
        
        # Calculate average specification match scores
        spec_scores = [m.specification_match_score for m in matches if m.specification_match_score > 0]
        
        if spec_scores:
            coverage['overall_coverage'] = sum(spec_scores) / len(spec_scores)
            coverage['voltage_coverage'] = coverage['overall_coverage']  # Simplified
            coverage['current_coverage'] = coverage['overall_coverage']
            coverage['frequency_coverage'] = coverage['overall_coverage']
        
        return coverage
    
    def _calculate_search_effectiveness(self, strategy_results: Dict[SearchStrategy, List[ProductMatch]]) -> float:
        """Calculate overall search effectiveness"""
        total_matches = sum(len(matches) for matches in strategy_results.values())
        unique_products = set()
        
        for matches in strategy_results.values():
            for match in matches:
                unique_products.add((match.product_id, match.range_label))
        
        # Effectiveness = unique products found / total search attempts
        effectiveness = len(unique_products) / max(len(strategy_results), 1)
        
        return min(effectiveness, 1.0)


def analyze_pix2b_discovery():
    """Analyze PIX2B using enhanced discovery service"""
    
    # Load PIX2B Grok metadata
    metadata_path = Path("../../data/output/json_outputs/PIX2B_Phase_out_Letter_22/20250714_213459/grok_metadata.json")
    
    if not metadata_path.exists():
        logger.error(f"❌ Metadata file not found: {metadata_path}")
        return
    
    with open(metadata_path) as f:
        grok_metadata = json.load(f)
    
    logger.info("🔍 Starting Enhanced Product Discovery Analysis for PIX2B")
    logger.info("="*80)
    
    # Initialize discovery service
    discovery_service = EnhancedProductDiscoveryService()
    
    # Perform comprehensive discovery
    result = discovery_service.discover_products(grok_metadata)
    
    # Display results
    logger.info(f"📊 DISCOVERY RESULTS SUMMARY")
    logger.info(f"💎 Primary matches (high confidence): {len(result.primary_matches)}")
    logger.info(f"🔸 Secondary matches (medium confidence): {len(result.secondary_matches)}")
    logger.info(f"📈 Total products found: {result.total_products_found}")
    logger.info(f"⏱️ Processing time: {result.processing_time_ms:.2f}ms")
    logger.info(f"🎯 Search effectiveness: {result.search_effectiveness:.2f}")
    
    # Show confidence distribution
    logger.info(f"\n📊 CONFIDENCE DISTRIBUTION:")
    for level, count in result.confidence_distribution.items():
        logger.info(f"  {level}: {count} products")
    
    # Show technical coverage
    logger.info(f"\n🔧 TECHNICAL COVERAGE:")
    for metric, score in result.technical_coverage.items():
        logger.info(f"  {metric}: {score:.2f}")
    
    # Show top primary matches
    logger.info(f"\n💎 TOP PRIMARY MATCHES:")
    for i, match in enumerate(result.primary_matches[:10], 1):
        logger.info(f"  {i}. {match.range_label} - {match.subrange_label}")
        logger.info(f"     ID: {match.product_id}")
        logger.info(f"     Score: {match.overall_score:.3f}")
        logger.info(f"     Strategy: {match.search_strategy.value}")
        logger.info(f"     Reasons: {', '.join(match.match_reasons)}")
        logger.info(f"     Tech Specs: V={match.technical_details.get('voltage_kv', 'N/A')}kV, " +
                   f"I={match.technical_details.get('current_rating_a', 'N/A')}A")
        logger.info("")
    
    # Save detailed results
    timestamp = int(time.time())
    results_file = f"pix2b_enhanced_discovery_{timestamp}.json"
    
    # Convert results to JSON-serializable format
    results_data = {
        'metadata': {
            'total_products_found': result.total_products_found,
            'processing_time_ms': result.processing_time_ms,
            'search_effectiveness': result.search_effectiveness,
            'confidence_distribution': result.confidence_distribution,
            'technical_coverage': result.technical_coverage,
            'strategies_used': [s.value for s in result.search_strategies_used]
        },
        'primary_matches': [
            {
                'product_id': m.product_id,
                'range_label': m.range_label,
                'subrange_label': m.subrange_label,
                'product_description': m.product_description,
                'overall_score': m.overall_score,
                'specification_match_score': m.specification_match_score,
                'semantic_similarity_score': m.semantic_similarity_score,
                'range_match_score': m.range_match_score,
                'search_strategy': m.search_strategy.value,
                'match_reasons': m.match_reasons,
                'technical_details': m.technical_details
            }
            for m in result.primary_matches
        ],
        'secondary_matches': [
            {
                'product_id': m.product_id,
                'range_label': m.range_label,
                'subrange_label': m.subrange_label,
                'overall_score': m.overall_score,
                'search_strategy': m.search_strategy.value,
                'technical_details': m.technical_details
            }
            for m in result.secondary_matches
        ]
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2, default=str)
    
    logger.info(f"💾 Detailed results saved to: {results_file}")
    
    return result


if __name__ == "__main__":
    # Run enhanced discovery analysis
    result = analyze_pix2b_discovery() 