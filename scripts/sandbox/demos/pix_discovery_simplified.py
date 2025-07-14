#!/usr/bin/env python3
"""
PIX Discovery Service - SOTA Simplified Version
Demonstrates enhanced product discovery using available database columns

Features:
- Technical specification-aware search
- Multi-strategy search expansion
- Semantic similarity matching
- Range-based product discovery
- Confidence scoring

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
    """Search strategies for product discovery"""
    EXACT_RANGE_MATCH = "exact_range_match"
    FUZZY_RANGE_EXPANSION = "fuzzy_range_expansion"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    TECHNICAL_SPEC_FILTER = "technical_spec_filter"
    COMPREHENSIVE_HYBRID = "comprehensive_hybrid"


@dataclass
class ProductMatch:
    """Product match with scoring details"""
    product_identifier: str
    range_label: str
    subrange_label: str
    product_description: str
    brand_label: str
    commercial_status: str
    match_confidence: float
    match_reasons: List[str]
    search_strategy: SearchStrategy
    technical_alignment: float = 0.0
    semantic_similarity: float = 0.0
    range_similarity: float = 0.0


@dataclass
class DiscoveryResult:
    """Comprehensive discovery result"""
    primary_matches: List[ProductMatch]
    secondary_matches: List[ProductMatch]
    total_products_found: int
    search_strategies_used: List[SearchStrategy]
    processing_time_ms: float
    confidence_stats: Dict[str, Any]
    grok_metadata_used: Dict[str, Any]


class PIXDiscoveryService:
    """Enhanced PIX product discovery using SOTA techniques"""
    
    def __init__(self, database_path: str = "../../data/IBcatalogue.duckdb"):
        """Initialize discovery service"""
        self.database_path = database_path
        
        # Load semantic model
        logger.info("🧠 Loading semantic similarity model...")
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'high': 0.80,
            'medium': 0.60,
            'low': 0.40
        }
        
        logger.info("🔍 PIX Discovery Service initialized")
    
    def discover_products(self, grok_metadata: Dict[str, Any]) -> DiscoveryResult:
        """
        Discover all products using multiple SOTA strategies
        
        Args:
            grok_metadata: Grok extraction metadata with technical specs
            
        Returns:
            Comprehensive discovery results
        """
        start_time = time.time()
        
        logger.info("🎯 Starting enhanced PIX product discovery")
        
        # Extract search criteria from Grok metadata
        search_criteria = self._extract_search_criteria(grok_metadata)
        logger.info(f"📋 Search criteria extracted: {search_criteria}")
        
        # Execute multiple search strategies
        all_matches = []
        strategies_used = []
        
        # Strategy 1: Exact Range Matching
        logger.info("🎯 Strategy 1: Exact Range Matching")
        exact_matches = self._exact_range_search(search_criteria)
        all_matches.extend(exact_matches)
        strategies_used.append(SearchStrategy.EXACT_RANGE_MATCH)
        logger.info(f"   Found {len(exact_matches)} exact matches")
        
        # Strategy 2: Fuzzy Range Expansion
        logger.info("🔄 Strategy 2: Fuzzy Range Expansion")
        fuzzy_matches = self._fuzzy_range_expansion(search_criteria)
        all_matches.extend(fuzzy_matches)
        strategies_used.append(SearchStrategy.FUZZY_RANGE_EXPANSION)
        logger.info(f"   Found {len(fuzzy_matches)} fuzzy matches")
        
        # Strategy 3: Semantic Similarity Search
        logger.info("🧠 Strategy 3: Semantic Similarity Search")
        semantic_matches = self._semantic_similarity_search(search_criteria, grok_metadata)
        all_matches.extend(semantic_matches)
        strategies_used.append(SearchStrategy.SEMANTIC_SIMILARITY)
        logger.info(f"   Found {len(semantic_matches)} semantic matches")
        
        # Strategy 4: Technical Specification Filter
        logger.info("🔧 Strategy 4: Technical Specification Filter")
        tech_matches = self._technical_specification_filter(search_criteria, grok_metadata)
        all_matches.extend(tech_matches)
        strategies_used.append(SearchStrategy.TECHNICAL_SPEC_FILTER)
        logger.info(f"   Found {len(tech_matches)} technical matches")
        
        # Strategy 5: Comprehensive Hybrid
        logger.info("⚡ Strategy 5: Comprehensive Hybrid")
        hybrid_matches = self._comprehensive_hybrid_search(search_criteria, grok_metadata)
        all_matches.extend(hybrid_matches)
        strategies_used.append(SearchStrategy.COMPREHENSIVE_HYBRID)
        logger.info(f"   Found {len(hybrid_matches)} hybrid matches")
        
        # Deduplicate and rank results
        unique_matches = self._deduplicate_and_rank(all_matches)
        
        # Categorize by confidence
        primary_matches = [m for m in unique_matches if m.match_confidence >= self.confidence_thresholds['high']]
        secondary_matches = [m for m in unique_matches if self.confidence_thresholds['medium'] <= m.match_confidence < self.confidence_thresholds['high']]
        
        # Calculate statistics
        processing_time_ms = (time.time() - start_time) * 1000
        confidence_stats = self._calculate_confidence_stats(unique_matches)
        
        result = DiscoveryResult(
            primary_matches=primary_matches,
            secondary_matches=secondary_matches,
            total_products_found=len(unique_matches),
            search_strategies_used=strategies_used,
            processing_time_ms=processing_time_ms,
            confidence_stats=confidence_stats,
            grok_metadata_used=search_criteria
        )
        
        logger.info(f"✅ Discovery completed: {len(primary_matches)} primary, {len(secondary_matches)} secondary matches")
        return result
    
    def _extract_search_criteria(self, grok_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract search criteria from Grok metadata"""
        criteria = {}
        
        # Extract product information
        products = grok_metadata.get('products', [])
        if products:
            product = products[0]  # Focus on first product
            criteria['product_identifier'] = product.get('product_identifier', '')
            criteria['range_label'] = product.get('range_label', '')
            criteria['subrange_label'] = product.get('subrange_label', '')
            criteria['product_line'] = product.get('product_line', '')
            criteria['product_description'] = product.get('product_description', '')
        
        # Extract technical specifications
        tech_specs = grok_metadata.get('technical_specifications', {})
        criteria['voltage_levels'] = tech_specs.get('voltage_levels', [])
        criteria['current_ratings'] = tech_specs.get('current_ratings', [])
        criteria['frequencies'] = tech_specs.get('frequencies', [])
        
        # Extract document context
        doc_info = grok_metadata.get('document_information', {})
        criteria['document_title'] = doc_info.get('document_title', '')
        
        return criteria
    
    def _exact_range_search(self, criteria: Dict[str, Any]) -> List[ProductMatch]:
        """Search for exact range matches"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                range_label = criteria.get('range_label', '')
                subrange_label = criteria.get('subrange_label', '')
                
                if not range_label:
                    return matches
                
                # Exact range query
                query = """
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        brand_label,
                        commercial_status
                    FROM products 
                    WHERE range_label ILIKE ?
                """
                
                params = [f"%{range_label}%"]
                
                # Add subrange filter if available
                if subrange_label:
                    query += " AND subrange_label ILIKE ?"
                    params.append(f"%{subrange_label}%")
                
                results = conn.execute(query, params).fetchall()
                columns = [desc[0] for desc in conn.description]
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    
                    # Calculate match confidence
                    confidence = self._calculate_range_confidence(product_data, criteria)
                    
                    match = ProductMatch(
                        product_identifier=product_data['product_identifier'],
                        range_label=product_data['range_label'],
                        subrange_label=product_data['subrange_label'] or '',
                        product_description=product_data['product_description'] or '',
                        brand_label=product_data['brand_label'] or '',
                        commercial_status=product_data['commercial_status'] or '',
                        match_confidence=confidence,
                        match_reasons=['exact_range_match'],
                        search_strategy=SearchStrategy.EXACT_RANGE_MATCH,
                        range_similarity=confidence
                    )
                    
                    matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Exact range search failed: {e}")
        
        return matches
    
    def _fuzzy_range_expansion(self, criteria: Dict[str, Any]) -> List[ProductMatch]:
        """Fuzzy expansion within product ranges"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                range_label = criteria.get('range_label', '')
                product_line = criteria.get('product_line', '')
                
                if not range_label:
                    return matches
                
                # Extract key terms for fuzzy matching
                range_keywords = self._extract_keywords(range_label)
                
                # Build fuzzy query
                query = """
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        brand_label,
                        commercial_status
                    FROM products 
                    WHERE (
                        range_label ILIKE ? OR
                        subrange_label ILIKE ? OR
                        product_description ILIKE ?
                    )
                """
                
                # Create fuzzy patterns
                fuzzy_pattern = f"%{range_keywords[0]}%" if range_keywords else f"%{range_label[:3]}%"
                params = [fuzzy_pattern, fuzzy_pattern, fuzzy_pattern]
                
                # Add product line filter if available
                if product_line and 'PSIBS' in product_line:
                    query += " AND (range_label ILIKE '%PIX%' OR range_label ILIKE '%PSI%' OR range_label ILIKE '%Medium%')"
                
                results = conn.execute(query, params).fetchall()
                columns = [desc[0] for desc in conn.description]
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    
                    # Calculate fuzzy confidence
                    confidence = self._calculate_fuzzy_confidence(product_data, criteria)
                    
                    match = ProductMatch(
                        product_identifier=product_data['product_identifier'],
                        range_label=product_data['range_label'],
                        subrange_label=product_data['subrange_label'] or '',
                        product_description=product_data['product_description'] or '',
                        brand_label=product_data['brand_label'] or '',
                        commercial_status=product_data['commercial_status'] or '',
                        match_confidence=confidence,
                        match_reasons=['fuzzy_range_expansion'],
                        search_strategy=SearchStrategy.FUZZY_RANGE_EXPANSION,
                        range_similarity=confidence
                    )
                    
                    matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Fuzzy range expansion failed: {e}")
        
        return matches
    
    def _semantic_similarity_search(self, criteria: Dict[str, Any], grok_metadata: Dict[str, Any]) -> List[ProductMatch]:
        """Semantic similarity-based search"""
        matches = []
        
        try:
            # Build semantic query
            query_text = self._build_semantic_query(criteria, grok_metadata)
            
            if not query_text.strip():
                return matches
            
            # Encode query
            query_embedding = self.semantic_model.encode([query_text])
            
            with duckdb.connect(self.database_path) as conn:
                # Get relevant products for comparison
                results = conn.execute("""
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        brand_label,
                        commercial_status
                    FROM products 
                    WHERE product_description IS NOT NULL
                    AND (
                        range_label ILIKE '%PIX%' OR
                        range_label ILIKE '%Bus%' OR
                        range_label ILIKE '%Medium%' OR
                        range_label ILIKE '%Voltage%' OR
                        product_description ILIKE '%switchgear%' OR
                        product_description ILIKE '%medium voltage%'
                    )
                    LIMIT 1000
                """).fetchall()
                
                columns = [desc[0] for desc in conn.description]
                
                if not results:
                    return matches
                
                # Build product texts and embeddings
                product_texts = []
                product_data_list = []
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    product_text = f"{product_data['range_label']} {product_data['subrange_label']} {product_data['product_description']}"
                    product_texts.append(product_text)
                    product_data_list.append(product_data)
                
                # Generate embeddings
                product_embeddings = self.semantic_model.encode(product_texts)
                
                # Calculate similarities
                similarities = cosine_similarity(query_embedding, product_embeddings)[0]
                
                # Create matches for high similarity products
                for i, similarity in enumerate(similarities):
                    if similarity >= 0.3:  # Similarity threshold
                        product_data = product_data_list[i]
                        
                        # Scale similarity to confidence
                        confidence = min(similarity * 1.2, 1.0)
                        
                        match = ProductMatch(
                            product_identifier=product_data['product_identifier'],
                            range_label=product_data['range_label'],
                            subrange_label=product_data['subrange_label'] or '',
                            product_description=product_data['product_description'] or '',
                            brand_label=product_data['brand_label'] or '',
                            commercial_status=product_data['commercial_status'] or '',
                            match_confidence=confidence,
                            match_reasons=['semantic_similarity', f'sim_{similarity:.3f}'],
                            search_strategy=SearchStrategy.SEMANTIC_SIMILARITY,
                            semantic_similarity=similarity
                        )
                        
                        matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Semantic similarity search failed: {e}")
        
        return matches
    
    def _technical_specification_filter(self, criteria: Dict[str, Any], grok_metadata: Dict[str, Any]) -> List[ProductMatch]:
        """Filter products by technical specifications"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                # Extract technical keywords
                voltage_keywords = self._extract_voltage_keywords(criteria.get('voltage_levels', []))
                current_keywords = self._extract_current_keywords(criteria.get('current_ratings', []))
                
                # Build technical filter query
                query = """
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        brand_label,
                        commercial_status
                    FROM products 
                    WHERE 1=1
                """
                
                conditions = []
                params = []
                
                # Add voltage filters
                if voltage_keywords:
                    voltage_conditions = []
                    for keyword in voltage_keywords:
                        voltage_conditions.append("product_description ILIKE ?")
                        params.append(f"%{keyword}%")
                    if voltage_conditions:
                        conditions.append(f"({' OR '.join(voltage_conditions)})")
                
                # Add current filters
                if current_keywords:
                    current_conditions = []
                    for keyword in current_keywords:
                        current_conditions.append("product_description ILIKE ?")
                        params.append(f"%{keyword}%")
                    if current_conditions:
                        conditions.append(f"({' OR '.join(current_conditions)})")
                
                # Add range context
                range_label = criteria.get('range_label', '')
                if range_label:
                    conditions.append("range_label ILIKE ?")
                    params.append(f"%{range_label[:3]}%")
                
                if conditions:
                    query += " AND " + " AND ".join(conditions)
                
                if not params:
                    return matches
                
                results = conn.execute(query, params).fetchall()
                columns = [desc[0] for desc in conn.description]
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    
                    # Calculate technical alignment
                    tech_score = self._calculate_technical_alignment(product_data, criteria)
                    
                    match = ProductMatch(
                        product_identifier=product_data['product_identifier'],
                        range_label=product_data['range_label'],
                        subrange_label=product_data['subrange_label'] or '',
                        product_description=product_data['product_description'] or '',
                        brand_label=product_data['brand_label'] or '',
                        commercial_status=product_data['commercial_status'] or '',
                        match_confidence=tech_score,
                        match_reasons=['technical_specification_filter'],
                        search_strategy=SearchStrategy.TECHNICAL_SPEC_FILTER,
                        technical_alignment=tech_score
                    )
                    
                    matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Technical specification filter failed: {e}")
        
        return matches
    
    def _comprehensive_hybrid_search(self, criteria: Dict[str, Any], grok_metadata: Dict[str, Any]) -> List[ProductMatch]:
        """Comprehensive hybrid search combining all techniques"""
        matches = []
        
        try:
            with duckdb.connect(self.database_path) as conn:
                # Comprehensive query combining range, semantic, and technical aspects
                query = """
                    SELECT 
                        product_identifier,
                        range_label,
                        subrange_label,
                        product_description,
                        brand_label,
                        commercial_status
                    FROM products 
                    WHERE (
                        -- Range-based matching
                        range_label ILIKE ? OR
                        subrange_label ILIKE ? OR
                        
                        -- Semantic matching  
                        product_description ILIKE ? OR
                        product_description ILIKE ? OR
                        
                        -- Technical matching
                        product_description ILIKE ? OR
                        product_description ILIKE ?
                    )
                """
                
                range_label = criteria.get('range_label', 'PIX')
                subrange_label = criteria.get('subrange_label', 'PIX')
                
                params = [
                    f"%{range_label}%",
                    f"%{subrange_label}%",
                    "%switchgear%",
                    "%medium voltage%",
                    "%kV%",
                    "%A%"
                ]
                
                results = conn.execute(query, params).fetchall()
                columns = [desc[0] for desc in conn.description]
                
                for row in results:
                    product_data = dict(zip(columns, row))
                    
                    # Calculate hybrid confidence
                    range_score = self._calculate_range_confidence(product_data, criteria)
                    tech_score = self._calculate_technical_alignment(product_data, criteria)
                    
                    # Weighted hybrid score
                    hybrid_confidence = (range_score * 0.5) + (tech_score * 0.3) + 0.2  # Base boost
                    hybrid_confidence = min(hybrid_confidence, 1.0)
                    
                    match = ProductMatch(
                        product_identifier=product_data['product_identifier'],
                        range_label=product_data['range_label'],
                        subrange_label=product_data['subrange_label'] or '',
                        product_description=product_data['product_description'] or '',
                        brand_label=product_data['brand_label'] or '',
                        commercial_status=product_data['commercial_status'] or '',
                        match_confidence=hybrid_confidence,
                        match_reasons=['comprehensive_hybrid', 'multi_modal'],
                        search_strategy=SearchStrategy.COMPREHENSIVE_HYBRID,
                        range_similarity=range_score,
                        technical_alignment=tech_score
                    )
                    
                    matches.append(match)
        
        except Exception as e:
            logger.error(f"❌ Comprehensive hybrid search failed: {e}")
        
        return matches
    
    def _calculate_range_confidence(self, product_data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate range matching confidence"""
        product_range = product_data.get('range_label', '').lower()
        target_range = criteria.get('range_label', '').lower()
        
        if not product_range or not target_range:
            return 0.1
        
        # Exact match
        if product_range == target_range:
            return 1.0
        
        # Substring match
        if target_range in product_range or product_range in target_range:
            return 0.8
        
        # Keyword overlap
        product_words = set(product_range.split())
        target_words = set(target_range.split())
        overlap = len(product_words & target_words)
        total = len(product_words | target_words)
        
        if total > 0:
            return (overlap / total) * 0.7
        
        return 0.1
    
    def _calculate_fuzzy_confidence(self, product_data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate fuzzy matching confidence"""
        # Base range confidence
        range_conf = self._calculate_range_confidence(product_data, criteria)
        
        # Description similarity
        product_desc = product_data.get('product_description', '').lower()
        target_desc = criteria.get('product_description', '').lower()
        
        desc_score = 0.0
        if product_desc and target_desc:
            # Simple word overlap
            product_words = set(product_desc.split())
            target_words = set(target_desc.split())
            overlap = len(product_words & target_words)
            total = len(product_words | target_words)
            desc_score = overlap / total if total > 0 else 0.0
        
        # Combined fuzzy score
        return (range_conf * 0.7) + (desc_score * 0.3)
    
    def _calculate_technical_alignment(self, product_data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate technical specification alignment"""
        product_desc = product_data.get('product_description', '').lower()
        
        if not product_desc:
            return 0.1
        
        score = 0.0
        factors = 0
        
        # Voltage alignment
        voltage_levels = criteria.get('voltage_levels', [])
        for voltage in voltage_levels:
            if any(v in product_desc for v in ['kv', 'voltage', '12', '17.5', 'medium']):
                score += 0.4
                break
        factors += 1
        
        # Current alignment
        current_ratings = criteria.get('current_ratings', [])
        for current in current_ratings:
            if any(c in product_desc for c in ['a', 'amp', 'current', '3150', 'rating']):
                score += 0.3
                break
        factors += 1
        
        # Equipment type alignment
        if any(t in product_desc for t in ['switchgear', 'bus', 'bar', 'medium', 'voltage']):
            score += 0.3
        factors += 1
        
        return score / factors if factors > 0 else 0.1
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from text"""
        if not text:
            return []
        
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 2 and w not in ['the', 'and', 'for', 'with']]
        return keywords[:5]  # Top 5 keywords
    
    def _extract_voltage_keywords(self, voltage_levels: List[str]) -> List[str]:
        """Extract voltage-related keywords"""
        keywords = []
        for voltage in voltage_levels:
            # Extract voltage values and units
            matches = re.findall(r'(\d+(?:\.\d+)?)\s*(kV|kv|V|v)', voltage, re.IGNORECASE)
            for match in matches:
                keywords.append(f"{match[0]}kV")
                keywords.append(match[0])
            
            # Add general voltage terms
            keywords.extend(['voltage', 'kV', 'medium voltage'])
        
        return list(set(keywords))
    
    def _extract_current_keywords(self, current_ratings: List[str]) -> List[str]:
        """Extract current-related keywords"""
        keywords = []
        for current in current_ratings:
            # Extract current values
            matches = re.findall(r'(\d+(?:\.\d+)?)\s*(A|a|amp)', current, re.IGNORECASE)
            for match in matches:
                keywords.append(f"{match[0]}A")
                keywords.append(match[0])
            
            # Add general current terms
            keywords.extend(['current', 'A', 'ampere', 'rating'])
        
        return list(set(keywords))
    
    def _build_semantic_query(self, criteria: Dict[str, Any], grok_metadata: Dict[str, Any]) -> str:
        """Build semantic query from criteria and metadata"""
        query_parts = []
        
        # Add range information
        if criteria.get('range_label'):
            query_parts.append(criteria['range_label'])
        
        # Add product description
        if criteria.get('product_description'):
            query_parts.append(criteria['product_description'])
        
        # Add document title
        if criteria.get('document_title'):
            query_parts.append(criteria['document_title'])
        
        # Add technical specifications
        for voltage in criteria.get('voltage_levels', []):
            query_parts.append(voltage)
        
        for current in criteria.get('current_ratings', []):
            query_parts.append(current)
        
        # Add business context
        business_info = grok_metadata.get('business_information', {})
        if business_info.get('customer_impact'):
            query_parts.append(business_info['customer_impact'][:100])  # First 100 chars
        
        return ' '.join(query_parts)
    
    def _deduplicate_and_rank(self, matches: List[ProductMatch]) -> List[ProductMatch]:
        """Remove duplicates and rank by confidence"""
        seen_products = set()
        unique_matches = []
        
        # Sort by confidence (descending)
        sorted_matches = sorted(matches, key=lambda x: x.match_confidence, reverse=True)
        
        for match in sorted_matches:
            product_key = match.product_identifier
            if product_key not in seen_products:
                seen_products.add(product_key)
                unique_matches.append(match)
        
        return unique_matches
    
    def _calculate_confidence_stats(self, matches: List[ProductMatch]) -> Dict[str, Any]:
        """Calculate confidence distribution statistics"""
        if not matches:
            return {'high': 0, 'medium': 0, 'low': 0, 'very_low': 0, 'avg_confidence': 0.0}
        
        high = sum(1 for m in matches if m.match_confidence >= self.confidence_thresholds['high'])
        medium = sum(1 for m in matches if self.confidence_thresholds['medium'] <= m.match_confidence < self.confidence_thresholds['high'])
        low = sum(1 for m in matches if self.confidence_thresholds['low'] <= m.match_confidence < self.confidence_thresholds['medium'])
        very_low = sum(1 for m in matches if m.match_confidence < self.confidence_thresholds['low'])
        
        avg_confidence = sum(m.match_confidence for m in matches) / len(matches)
        
        return {
            'high': high,
            'medium': medium, 
            'low': low,
            'very_low': very_low,
            'avg_confidence': avg_confidence
        }


def analyze_pix_discovery():
    """Analyze PIX2B using enhanced discovery service"""
    
    # Load PIX2B Grok metadata
    metadata_path = Path("../../data/output/json_outputs/PIX2B_Phase_out_Letter_22/20250714_213459/grok_metadata.json")
    
    if not metadata_path.exists():
        logger.error(f"❌ Metadata file not found: {metadata_path}")
        return
    
    with open(metadata_path) as f:
        grok_metadata = json.load(f)
    
    logger.info("🔍 PIX2B Enhanced Product Discovery Analysis")
    logger.info("="*60)
    
    # Show Grok metadata being used
    logger.info("📋 GROK METADATA INPUT:")
    logger.info(f"Document: {grok_metadata.get('document_information', {}).get('document_title', 'N/A')}")
    
    products = grok_metadata.get('products', [])
    if products:
        product = products[0]
        logger.info(f"Product ID: {product.get('product_identifier', 'N/A')}")
        logger.info(f"Range: {product.get('range_label', 'N/A')}")
        logger.info(f"Subrange: {product.get('subrange_label', 'N/A')}")
        logger.info(f"Description: {product.get('product_description', 'N/A')}")
    
    tech_specs = grok_metadata.get('technical_specifications', {})
    logger.info(f"Voltage: {tech_specs.get('voltage_levels', [])}")
    logger.info(f"Current: {tech_specs.get('current_ratings', [])}")
    logger.info(f"Frequency: {tech_specs.get('frequencies', [])}")
    logger.info("")
    
    # Initialize discovery service
    discovery_service = PIXDiscoveryService()
    
    # Perform discovery
    result = discovery_service.discover_products(grok_metadata)
    
    # Display comprehensive results
    logger.info("📊 DISCOVERY RESULTS SUMMARY")
    logger.info(f"💎 Primary matches (high confidence): {len(result.primary_matches)}")
    logger.info(f"🔸 Secondary matches (medium confidence): {len(result.secondary_matches)}")
    logger.info(f"📈 Total unique products found: {result.total_products_found}")
    logger.info(f"⏱️ Processing time: {result.processing_time_ms:.2f}ms")
    logger.info(f"🎯 Strategies used: {len(result.search_strategies_used)}")
    
    # Show confidence statistics
    stats = result.confidence_stats
    logger.info(f"\n📊 CONFIDENCE DISTRIBUTION:")
    logger.info(f"  High confidence (≥80%): {stats['high']} products")
    logger.info(f"  Medium confidence (60-80%): {stats['medium']} products")
    logger.info(f"  Low confidence (40-60%): {stats['low']} products")
    logger.info(f"  Very low confidence (<40%): {stats['very_low']} products")
    logger.info(f"  Average confidence: {stats['avg_confidence']:.2%}")
    
    # Show top primary matches
    logger.info(f"\n💎 TOP PRIMARY MATCHES:")
    for i, match in enumerate(result.primary_matches[:15], 1):
        logger.info(f"  {i}. {match.product_identifier}")
        logger.info(f"     Range: {match.range_label}")
        logger.info(f"     Subrange: {match.subrange_label}")
        logger.info(f"     Status: {match.commercial_status}")
        logger.info(f"     Confidence: {match.match_confidence:.1%}")
        logger.info(f"     Strategy: {match.search_strategy.value}")
        logger.info(f"     Reasons: {', '.join(match.match_reasons)}")
        if match.product_description:
            logger.info(f"     Description: {match.product_description[:100]}...")
        logger.info("")
    
    # Show secondary matches summary
    if result.secondary_matches:
        logger.info(f"\n🔸 TOP SECONDARY MATCHES:")
        for i, match in enumerate(result.secondary_matches[:10], 1):
            logger.info(f"  {i}. {match.product_identifier} - {match.range_label} ({match.match_confidence:.1%})")
    
    # Show strategy effectiveness
    logger.info(f"\n⚡ STRATEGY EFFECTIVENESS:")
    strategy_counts = {}
    for match in result.primary_matches + result.secondary_matches:
        strategy = match.search_strategy.value
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    for strategy, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {strategy}: {count} matches")
    
    # Save detailed results
    timestamp = int(time.time())
    results_file = f"pix_discovery_results_{timestamp}.json"
    
    # Convert to JSON-serializable format
    results_data = {
        'metadata': {
            'total_products_found': result.total_products_found,
            'processing_time_ms': result.processing_time_ms,
            'confidence_stats': result.confidence_stats,
            'strategies_used': [s.value for s in result.search_strategies_used],
            'grok_input': result.grok_metadata_used
        },
        'primary_matches': [
            {
                'product_identifier': m.product_identifier,
                'range_label': m.range_label,
                'subrange_label': m.subrange_label,
                'product_description': m.product_description,
                'brand_label': m.brand_label,
                'commercial_status': m.commercial_status,
                'match_confidence': m.match_confidence,
                'search_strategy': m.search_strategy.value,
                'match_reasons': m.match_reasons,
                'technical_alignment': m.technical_alignment,
                'semantic_similarity': m.semantic_similarity,
                'range_similarity': m.range_similarity
            }
            for m in result.primary_matches
        ],
        'secondary_matches': [
            {
                'product_identifier': m.product_identifier,
                'range_label': m.range_label,
                'match_confidence': m.match_confidence,
                'search_strategy': m.search_strategy.value
            }
            for m in result.secondary_matches
        ]
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    logger.info(f"\n💾 Detailed results saved to: {results_file}")
    
    # Key insights
    logger.info(f"\n🎯 KEY INSIGHTS:")
    logger.info(f"  • Found {result.total_products_found} total products vs 1 from original Grok extraction")
    logger.info(f"  • {len(result.primary_matches)} high-confidence matches show the range impact")
    logger.info(f"  • Technical specifications enabled {stats['high'] + stats['medium']} quality matches")
    logger.info(f"  • Multiple search strategies provide comprehensive coverage")
    logger.info(f"  • SOTA techniques expand single-product extraction into range-wide analysis")
    
    return result


if __name__ == "__main__":
    # Run PIX discovery analysis
    result = analyze_pix_discovery() 