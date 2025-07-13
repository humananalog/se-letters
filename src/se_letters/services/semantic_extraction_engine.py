#!/usr/bin/env python3
"""
Semantic Extraction Engine
Creates embeddings from DuckDB database to enable intelligent product range detection
Eliminates hardcoded values and provides true semantic understanding
"""

import sys
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import numpy as np
import pandas as pd
import duckdb
from sentence_transformers import SentenceTransformer
import faiss
from collections import Counter, defaultdict

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from se_letters.core.config import get_config
from se_letters.core.exceptions import ProcessingError
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SemanticMatch:
    """Semantic match result with confidence and context"""
    range_label: str
    similarity_score: float
    match_type: str  # 'exact', 'partial', 'semantic'
    context: str
    product_count: int
    commercial_status: str
    confidence: float
    evidence: List[str]


@dataclass
class ExtractionResult:
    """Complete extraction result with semantic analysis"""
    detected_ranges: List[str]
    semantic_matches: List[SemanticMatch]
    confidence_score: float
    extraction_method: str
    processing_time_ms: float
    evidence_text: List[str]
    missed_opportunities: List[str]
    quality_assessment: Dict[str, Any]


class SemanticExtractionEngine:
    """Semantic extraction engine using DuckDB embeddings for intelligent range detection"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize semantic extraction engine"""
        self.config = config or get_config()
        self.db_path = "data/IBcatalogue.duckdb"
        self.conn = None
        
        # Embedding components
        self.embedding_model = None
        self.range_embeddings = None
        self.range_index = None
        self.range_metadata = {}
        
        # Semantic dictionaries built from database
        self.range_dictionary = {}
        self.product_patterns = {}
        self.obsolescence_patterns = {}
        self.brand_patterns = {}
        
        # Performance tracking
        self.extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'avg_confidence': 0.0,
            'avg_processing_time': 0.0
        }
        
        logger.info("Semantic Extraction Engine initialized")
    
    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Semantic Extraction Engine components")
        
        # 1. Connect to database
        self._connect_database()
        
        # 2. Initialize embedding model
        self._initialize_embedding_model()
        
        # 3. Build semantic dictionaries from database
        self._build_semantic_dictionaries()
        
        # 4. Create range embeddings
        self._create_range_embeddings()
        
        logger.info("Semantic Extraction Engine fully initialized")
    
    def _connect_database(self):
        """Connect to DuckDB database"""
        if not Path(self.db_path).exists():
            raise ProcessingError(f"Database not found: {self.db_path}")
        
        self.conn = duckdb.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer for semantic matching"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise ProcessingError(f"Embedding model initialization failed: {e}")
    
    def _build_semantic_dictionaries(self):
        """Build semantic dictionaries from DuckDB database content"""
        logger.info("Building semantic dictionaries from database")
        
        # 1. Build range dictionary with variants and patterns
        range_query = """
            SELECT 
                RANGE_LABEL,
                COUNT(*) as product_count,
                COUNT(CASE WHEN COMMERCIAL_STATUS IN ('18-End of commercialisation', '19-end of commercialization block') THEN 1 END) as obsolete_count,
                STRING_AGG(DISTINCT BRAND_LABEL, '|') as brands,
                STRING_AGG(DISTINCT DEVICETYPE_LABEL, '|') as device_types,
                STRING_AGG(DISTINCT SUBRANGE_LABEL, '|') as subranges
            FROM products 
            WHERE RANGE_LABEL IS NOT NULL 
            GROUP BY RANGE_LABEL
            ORDER BY product_count DESC
        """
        
        range_data = self.conn.execute(range_query).fetchall()
        
        for range_label, prod_count, obs_count, brands, device_types, subranges in range_data:
            # Generate range variants and patterns
            variants = self._generate_range_variants(range_label)
            
            self.range_dictionary[range_label] = {
                'variants': variants,
                'product_count': prod_count,
                'obsolete_count': obs_count,
                'obsolescence_rate': (obs_count / prod_count) * 100 if prod_count > 0 else 0,
                'brands': brands.split('|') if brands else [],
                'device_types': device_types.split('|') if device_types else [],
                'subranges': subranges.split('|') if subranges and subranges != 'None' else [],
                'priority_score': self._calculate_range_priority(prod_count, obs_count)
            }
        
        # 2. Build product identifier patterns
        self._build_product_patterns()
        
        # 3. Build obsolescence language patterns
        self._build_obsolescence_patterns()
        
        logger.info(f"Built semantic dictionaries: {len(self.range_dictionary)} ranges")
    
    def _generate_range_variants(self, range_label: str) -> List[str]:
        """Generate variants of a range label for better matching"""
        variants = [range_label]
        
        # Common variations
        variants.extend([
            range_label.upper(),
            range_label.lower(),
            range_label.replace(' ', ''),
            range_label.replace('-', ' '),
            range_label.replace('_', ' '),
        ])
        
        # Handle specific patterns
        if 'TeSys' in range_label:
            variants.extend(['TESYS', 'Te Sys', range_label.replace('TeSys', 'TESYS')])
        
        if 'PowerPact' in range_label:
            variants.extend(['POWERPACT', 'Power Pact', range_label.replace('PowerPact', 'POWERPACT')])
        
        if 'ComPacT' in range_label or 'Compact' in range_label:
            variants.extend(['COMPACT', 'ComPacT', 'Compact'])
        
        # Remove duplicates and empty strings
        return list(set([v for v in variants if v.strip()]))
    
    def _build_product_patterns(self):
        """Build product identifier patterns from database"""
        pattern_query = """
            SELECT 
                SUBSTR(PRODUCT_IDENTIFIER, 1, 2) as prefix_2,
                SUBSTR(PRODUCT_IDENTIFIER, 1, 3) as prefix_3,
                SUBSTR(PRODUCT_IDENTIFIER, 1, 4) as prefix_4,
                RANGE_LABEL,
                COUNT(*) as count
            FROM products 
            WHERE PRODUCT_IDENTIFIER IS NOT NULL AND RANGE_LABEL IS NOT NULL
            GROUP BY prefix_2, prefix_3, prefix_4, RANGE_LABEL
            HAVING count > 10
            ORDER BY count DESC
            LIMIT 1000
        """
        
        pattern_data = self.conn.execute(pattern_query).fetchall()
        
        for prefix_2, prefix_3, prefix_4, range_label, count in pattern_data:
            if range_label not in self.product_patterns:
                self.product_patterns[range_label] = {
                    'prefixes_2': [],
                    'prefixes_3': [],
                    'prefixes_4': []
                }
            
            self.product_patterns[range_label]['prefixes_2'].append(prefix_2)
            self.product_patterns[range_label]['prefixes_3'].append(prefix_3)
            self.product_patterns[range_label]['prefixes_4'].append(prefix_4)
        
        logger.info(f"Built product patterns for {len(self.product_patterns)} ranges")
    
    def _build_obsolescence_patterns(self):
        """Build obsolescence language patterns"""
        self.obsolescence_patterns = {
            'strong_indicators': [
                'obsolete', 'obsolescence', 'end of life', 'end-of-life', 'eol',
                'discontinued', 'withdrawal', 'end of commercialization',
                'end of production', 'no longer available', 'phased out'
            ],
            'weak_indicators': [
                'replacement', 'superseded', 'upgrade', 'modernization',
                'migration', 'transition', 'alternative'
            ],
            'temporal_indicators': [
                'as of', 'effective', 'from', 'since', 'until', 'by'
            ]
        }
    
    def _calculate_range_priority(self, product_count: int, obsolete_count: int) -> float:
        """Calculate priority score for a range"""
        size_factor = min(product_count / 1000, 10)
        obsolescence_factor = (obsolete_count / product_count) * 5 if product_count > 0 else 0
        return size_factor + obsolescence_factor
    
    def _create_range_embeddings(self):
        """Create embeddings for all ranges"""
        logger.info("Creating range embeddings for semantic matching")
        
        # Prepare range texts for embedding
        range_texts = []
        range_labels = []
        
        for range_label, data in self.range_dictionary.items():
            # Create rich text representation
            text_parts = [range_label]
            
            # Add variants
            text_parts.extend(data['variants'][:3])  # Top 3 variants
            
            # Add device types
            if data['device_types']:
                text_parts.extend(data['device_types'][:2])  # Top 2 device types
            
            # Add brands
            if data['brands']:
                text_parts.append(data['brands'][0])  # Primary brand
            
            range_text = ' '.join(text_parts)
            range_texts.append(range_text)
            range_labels.append(range_label)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(range_texts, show_progress_bar=True)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.range_index = faiss.IndexFlatIP(dimension)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        self.range_index.add(embeddings.astype(np.float32))
        
        # Store metadata
        self.range_metadata = {
            'labels': range_labels,
            'texts': range_texts,
            'embeddings': embeddings
        }
        
        logger.info(f"Created embeddings for {len(range_labels)} ranges")
    
    def extract_ranges_semantic(self, document_text: str, document_name: str = "") -> ExtractionResult:
        """Extract product ranges using semantic analysis"""
        start_time = time.time()
        
        logger.info(f"Starting semantic extraction for document: {document_name}")
        
        # 1. Preprocess text
        processed_text = self._preprocess_text(document_text)
        
        # 2. Multi-strategy extraction
        extraction_strategies = [
            self._extract_exact_matches,
            self._extract_semantic_matches,
            self._extract_pattern_matches,
            self._extract_context_clues
        ]
        
        all_matches = []
        evidence_texts = []
        
        for strategy in extraction_strategies:
            try:
                matches, evidence = strategy(processed_text, document_name)
                all_matches.extend(matches)
                evidence_texts.extend(evidence)
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
        
        # 3. Consolidate and rank results
        final_ranges, semantic_matches = self._consolidate_matches(all_matches)
        
        # 4. Calculate confidence and quality
        confidence = self._calculate_extraction_confidence(semantic_matches, processed_text)
        quality = self._assess_extraction_quality(semantic_matches, processed_text)
        
        # 5. Identify missed opportunities
        missed_opportunities = self._identify_missed_opportunities(processed_text, final_ranges)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Update stats
        self.extraction_stats['total_extractions'] += 1
        if final_ranges:
            self.extraction_stats['successful_extractions'] += 1
        
        result = ExtractionResult(
            detected_ranges=final_ranges,
            semantic_matches=semantic_matches,
            confidence_score=confidence,
            extraction_method="semantic_multi_strategy",
            processing_time_ms=processing_time,
            evidence_text=evidence_texts,
            missed_opportunities=missed_opportunities,
            quality_assessment=quality
        )
        
        logger.info(f"Semantic extraction complete: {len(final_ranges)} ranges, confidence: {confidence:.2f}")
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better extraction"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common abbreviations
        text = text.replace('&', 'and')
        text = re.sub(r'\b(CB|MCB|MCCB|ACB)\b', lambda m: f"circuit breaker {m.group()}", text)
        
        return text.strip()
    
    def _extract_exact_matches(self, text: str, doc_name: str) -> Tuple[List[SemanticMatch], List[str]]:
        """Extract exact range matches"""
        matches = []
        evidence = []
        
        text_upper = text.upper()
        
        for range_label, data in self.range_dictionary.items():
            for variant in data['variants']:
                if variant.upper() in text_upper:
                    # Find context around the match
                    context = self._extract_context(text, variant, window=50)
                    
                    match = SemanticMatch(
                        range_label=range_label,
                        similarity_score=1.0,
                        match_type='exact',
                        context=context,
                        product_count=data['product_count'],
                        commercial_status='unknown',
                        confidence=0.95,
                        evidence=[f"Exact match: '{variant}' in text"]
                    )
                    matches.append(match)
                    evidence.append(f"Exact match found: {variant} -> {range_label}")
        
        return matches, evidence
    
    def _extract_semantic_matches(self, text: str, doc_name: str) -> Tuple[List[SemanticMatch], List[str]]:
        """Extract semantic matches using embeddings"""
        matches = []
        evidence = []
        
        if not self.range_index:
            return matches, evidence
        
        # Create embedding for document text (use first 500 chars for efficiency)
        text_sample = text[:500]
        text_embedding = self.embedding_model.encode([text_sample])
        faiss.normalize_L2(text_embedding)
        
        # Search for similar ranges
        similarities, indices = self.range_index.search(text_embedding.astype(np.float32), k=10)
        
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity > 0.3:  # Threshold for semantic similarity
                range_label = self.range_metadata['labels'][idx]
                range_data = self.range_dictionary[range_label]
                
                match = SemanticMatch(
                    range_label=range_label,
                    similarity_score=float(similarity),
                    match_type='semantic',
                    context=text_sample,
                    product_count=range_data['product_count'],
                    commercial_status='unknown',
                    confidence=float(similarity) * 0.8,  # Reduce confidence for semantic matches
                    evidence=[f"Semantic similarity: {similarity:.3f}"]
                )
                matches.append(match)
                evidence.append(f"Semantic match: {range_label} (similarity: {similarity:.3f})")
        
        return matches, evidence
    
    def _extract_pattern_matches(self, text: str, doc_name: str) -> Tuple[List[SemanticMatch], List[str]]:
        """Extract matches based on product identifier patterns"""
        matches = []
        evidence = []
        
        # Look for product identifier patterns
        product_patterns = re.findall(r'\b[A-Z]{2,4}\d{2,6}[A-Z]*\b', text)
        
        for pattern in product_patterns:
            # Check against known product patterns
            for range_label, data in self.product_patterns.items():
                prefix_2 = pattern[:2]
                prefix_3 = pattern[:3]
                prefix_4 = pattern[:4]
                
                if (prefix_2 in data['prefixes_2'] or 
                    prefix_3 in data['prefixes_3'] or 
                    prefix_4 in data['prefixes_4']):
                    
                    context = self._extract_context(text, pattern, window=30)
                    range_data = self.range_dictionary.get(range_label, {})
                    
                    match = SemanticMatch(
                        range_label=range_label,
                        similarity_score=0.8,
                        match_type='pattern',
                        context=context,
                        product_count=range_data.get('product_count', 0),
                        commercial_status='unknown',
                        confidence=0.7,
                        evidence=[f"Product pattern match: {pattern}"]
                    )
                    matches.append(match)
                    evidence.append(f"Pattern match: {pattern} -> {range_label}")
        
        return matches, evidence
    
    def _extract_context_clues(self, text: str, doc_name: str) -> Tuple[List[SemanticMatch], List[str]]:
        """Extract ranges based on context clues and obsolescence indicators"""
        matches = []
        evidence = []
        
        # Look for obsolescence context
        text_lower = text.lower()
        
        for indicator in self.obsolescence_patterns['strong_indicators']:
            if indicator in text_lower:
                # Extract sentences containing obsolescence indicators
                sentences = re.split(r'[.!?]', text)
                
                for sentence in sentences:
                    if indicator in sentence.lower():
                        # Look for potential range names in this sentence
                        words = sentence.split()
                        
                        for i, word in enumerate(words):
                            # Check if word could be a range name
                            if len(word) > 2 and any(c.isupper() for c in word):
                                # Check against our range dictionary
                                for range_label, data in self.range_dictionary.items():
                                    if word.upper() in [v.upper() for v in data['variants']]:
                                        match = SemanticMatch(
                                            range_label=range_label,
                                            similarity_score=0.6,
                                            match_type='context',
                                            context=sentence.strip(),
                                            product_count=data['product_count'],
                                            commercial_status='likely_obsolete',
                                            confidence=0.6,
                                            evidence=[f"Context clue: '{indicator}' near '{word}'"]
                                        )
                                        matches.append(match)
                                        evidence.append(f"Context match: {word} -> {range_label} (obsolescence context)")
        
        return matches, evidence
    
    def _extract_context(self, text: str, match: str, window: int = 50) -> str:
        """Extract context around a match"""
        try:
            start = max(0, text.find(match) - window)
            end = min(len(text), text.find(match) + len(match) + window)
            return text[start:end].strip()
        except:
            return match
    
    def _consolidate_matches(self, all_matches: List[SemanticMatch]) -> Tuple[List[str], List[SemanticMatch]]:
        """Consolidate and rank matches"""
        # Group matches by range
        range_groups = defaultdict(list)
        for match in all_matches:
            range_groups[match.range_label].append(match)
        
        # Select best match for each range
        final_matches = []
        for range_label, matches in range_groups.items():
            # Sort by confidence and similarity
            best_match = max(matches, key=lambda m: (m.confidence, m.similarity_score))
            final_matches.append(best_match)
        
        # Sort by confidence
        final_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        # Extract range labels
        final_ranges = [match.range_label for match in final_matches]
        
        return final_ranges, final_matches
    
    def _calculate_extraction_confidence(self, matches: List[SemanticMatch], text: str) -> float:
        """Calculate overall extraction confidence"""
        if not matches:
            return 0.0
        
        # Factors affecting confidence
        match_confidence = np.mean([m.confidence for m in matches])
        match_diversity = len(set(m.match_type for m in matches)) / 4  # 4 possible types
        text_length_factor = min(len(text) / 1000, 1.0)  # Longer text = more confidence
        
        overall_confidence = (match_confidence * 0.6 + 
                            match_diversity * 0.2 + 
                            text_length_factor * 0.2)
        
        return min(overall_confidence, 1.0)
    
    def _assess_extraction_quality(self, matches: List[SemanticMatch], text: str) -> Dict[str, Any]:
        """Assess quality of extraction"""
        return {
            'total_matches': len(matches),
            'match_types': list(set(m.match_type for m in matches)),
            'avg_confidence': np.mean([m.confidence for m in matches]) if matches else 0.0,
            'has_exact_matches': any(m.match_type == 'exact' for m in matches),
            'has_semantic_matches': any(m.match_type == 'semantic' for m in matches),
            'text_length': len(text),
            'obsolescence_detected': any('obsolet' in text.lower() for _ in [1])
        }
    
    def _identify_missed_opportunities(self, text: str, detected_ranges: List[str]) -> List[str]:
        """Identify potential ranges that might have been missed"""
        missed = []
        
        # Look for capitalized words that might be ranges
        potential_ranges = re.findall(r'\b[A-Z][A-Za-z]*[A-Z][A-Za-z]*\b', text)
        
        for potential in potential_ranges:
            if potential not in detected_ranges and len(potential) > 3:
                # Check if it's similar to any known range
                for range_label in self.range_dictionary.keys():
                    if potential.upper() in range_label.upper() or range_label.upper() in potential.upper():
                        if range_label not in detected_ranges:
                            missed.append(f"Potential missed range: {potential} (similar to {range_label})")
        
        return missed[:5]  # Limit to 5 suggestions
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        success_rate = (self.extraction_stats['successful_extractions'] / 
                       max(self.extraction_stats['total_extractions'], 1)) * 100
        
        return {
            **self.extraction_stats,
            'success_rate': success_rate,
            'range_dictionary_size': len(self.range_dictionary),
            'embedding_model_ready': self.range_index is not None
        }


def main():
    """Test the semantic extraction engine"""
    engine = SemanticExtractionEngine()
    
    try:
        engine.initialize()
        
        # Test with the DA example
        test_text = """
        DA series End of Life and associated risks
        
        The DA circuit breaker range was sold primarily to OEM equipment builders in the late 1960's up to late 1980's and the circuit breaker applications were primarily used in paralleling switchgear, generator switching and UPS output breakers.
        
        The obsolescence of the DA breaker was planned in 1986 and during a certain period, Schneider Electric has committed to providing breaker support and parts availability. Those commitments have ended as from January 2009.
        
        In addition to the availability of the new range of Masterpact NW circuit breakers to replace your current DA breaker, we have a retrofit solution at your disposal which enables you to upgrade to the new Masterpact NW.
        """
        
        result = engine.extract_ranges_semantic(test_text, "DA_test_document.txt")
        
        print("\n🎯 SEMANTIC EXTRACTION RESULTS")
        print("=" * 50)
        print(f"Detected Ranges: {result.detected_ranges}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Processing Time: {result.processing_time_ms:.1f}ms")
        
        print("\n📊 SEMANTIC MATCHES:")
        for match in result.semantic_matches:
            print(f"  {match.range_label}: {match.confidence:.2f} ({match.match_type})")
        
        print("\n📝 EVIDENCE:")
        for evidence in result.evidence_text[:5]:
            print(f"  - {evidence}")
        
        if result.missed_opportunities:
            print("\n⚠️ MISSED OPPORTUNITIES:")
            for missed in result.missed_opportunities:
                print(f"  - {missed}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    finally:
        if engine.conn:
            engine.conn.close()


if __name__ == "__main__":
    exit(main()) 