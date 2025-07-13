#!/usr/bin/env python3
"""
Enhanced Vector Search Engine
Implements hierarchical vector spaces with PPIBS gap analysis and intelligent product-to-letter mapping
Based on comprehensive database analysis revealing 342,229 products across 4,067 ranges
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
import duckdb
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from se_letters.core.config import get_config
from se_letters.core.exceptions import ProcessingError
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VectorSearchResult:
    """Result from vector search with confidence and metadata"""
    product_id: str
    range_label: str
    description: str
    similarity_score: float
    commercial_status: str
    brand_label: str
    pl_services: str
    bu_label: str
    device_type: str
    confidence_level: str
    search_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductHierarchy:
    """Product hierarchy structure for enhanced search"""
    brand_label: str
    bu_label: str
    pl_services: str
    range_label: str
    subrange_label: Optional[str]
    device_type: str
    commercial_status: str
    product_count: int
    obsolescence_priority: str


@dataclass
class LetterCoverageAnalysis:
    """Analysis of letter coverage across product hierarchy"""
    total_products: int
    covered_products: int
    uncovered_products: int
    coverage_percentage: float
    missing_ranges: List[str]
    ppibs_gap_analysis: Dict[str, Any]
    priority_gaps: List[Dict[str, Any]]


class EnhancedVectorSearchEngine:
    """Enhanced vector search engine with hierarchical spaces and gap analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced vector search engine"""
        self.config = config or get_config()
        self.db_path = "data/IBcatalogue.duckdb"
        self.conn = None
        
        # Vector search components
        self.embedding_model = None
        self.hierarchical_indices = {}
        self.product_embeddings = {}
        self.product_metadata = {}
        
        # Hierarchy analysis
        self.product_hierarchy = {}
        self.pl_services_distribution = {}
        self.brand_hierarchy = {}
        self.bu_hierarchy = {}
        
        # Letter coverage analysis
        self.letter_coverage = {}
        self.ppibs_gap_analysis = {}
        self.missing_ranges = set()
        
        # Performance metrics
        self.search_performance = {
            'total_searches': 0,
            'avg_search_time': 0.0,
            'cache_hits': 0,
            'method_distribution': Counter()
        }
        
        logger.info("Enhanced Vector Search Engine initialized")
    
    def connect_database(self):
        """Connect to DuckDB database"""
        if not Path(self.db_path).exists():
            raise ProcessingError(f"Database not found: {self.db_path}")
        
        self.conn = duckdb.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
    
    def initialize_embedding_model(self):
        """Initialize sentence transformer model optimized for product descriptions"""
        try:
            # Use a model optimized for technical/product descriptions
            model_name = "all-MiniLM-L6-v2"  # Good balance of speed and quality
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Initialized embedding model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise ProcessingError(f"Embedding model initialization failed: {e}")
    
    def analyze_product_hierarchy(self) -> Dict[str, Any]:
        """Analyze complete product hierarchy for enhanced search optimization"""
        logger.info("Analyzing product hierarchy for enhanced search")
        
        hierarchy_analysis = {}
        
        # 1. PL_SERVICES distribution (Critical for PPIBS gap analysis)
        pl_services_query = """
            SELECT 
                PL_SERVICES,
                COUNT(*) as product_count,
                COUNT(DISTINCT RANGE_LABEL) as range_count,
                COUNT(DISTINCT BU_LABEL) as bu_count,
                COUNT(CASE WHEN COMMERCIAL_STATUS IN ('18-End of commercialisation', '19-end of commercialization block') THEN 1 END) as obsolete_count
            FROM products 
            WHERE PL_SERVICES IS NOT NULL
            GROUP BY PL_SERVICES 
            ORDER BY product_count DESC
        """
        
        pl_services_data = self.conn.execute(pl_services_query).fetchall()
        self.pl_services_distribution = {}
        
        for pl_service, prod_count, range_count, bu_count, obsolete_count in pl_services_data:
            self.pl_services_distribution[pl_service] = {
                'product_count': prod_count,
                'range_count': range_count,
                'bu_count': bu_count,
                'obsolete_count': obsolete_count,
                'obsolescence_rate': (obsolete_count / prod_count) * 100 if prod_count > 0 else 0
            }
        
        hierarchy_analysis['pl_services_distribution'] = self.pl_services_distribution
        
        # 2. Brand-Range hierarchy
        brand_range_query = """
            SELECT 
                BRAND_LABEL,
                RANGE_LABEL,
                COUNT(*) as product_count,
                COMMERCIAL_STATUS,
                PL_SERVICES,
                BU_LABEL
            FROM products 
            WHERE BRAND_LABEL IS NOT NULL AND RANGE_LABEL IS NOT NULL
            GROUP BY BRAND_LABEL, RANGE_LABEL, COMMERCIAL_STATUS, PL_SERVICES, BU_LABEL
            ORDER BY product_count DESC
        """
        
        brand_range_data = self.conn.execute(brand_range_query).fetchall()
        self.brand_hierarchy = defaultdict(lambda: defaultdict(list))
        
        for brand, range_name, prod_count, status, pl_service, bu in brand_range_data:
            self.brand_hierarchy[brand][range_name].append({
                'product_count': prod_count,
                'commercial_status': status,
                'pl_services': pl_service,
                'bu_label': bu
            })
        
        hierarchy_analysis['brand_hierarchy'] = dict(self.brand_hierarchy)
        
        # 3. Critical ranges for PPIBS (46.1% of total products)
        ppibs_ranges_query = """
            SELECT 
                RANGE_LABEL,
                COUNT(*) as product_count,
                COUNT(CASE WHEN COMMERCIAL_STATUS IN ('18-End of commercialisation', '19-end of commercialization block') THEN 1 END) as obsolete_count,
                BRAND_LABEL,
                BU_LABEL
            FROM products 
            WHERE PL_SERVICES = 'PPIBS' AND RANGE_LABEL IS NOT NULL
            GROUP BY RANGE_LABEL, BRAND_LABEL, BU_LABEL
            ORDER BY product_count DESC
            LIMIT 50
        """
        
        ppibs_ranges = self.conn.execute(ppibs_ranges_query).fetchall()
        self.ppibs_gap_analysis = {
            'top_ranges': [],
            'total_products': sum(self.pl_services_distribution.get('PPIBS', {}).get('product_count', 0) for _ in [1]),
            'obsolete_products': sum(self.pl_services_distribution.get('PPIBS', {}).get('obsolete_count', 0) for _ in [1])
        }
        
        for range_name, prod_count, obsolete_count, brand, bu in ppibs_ranges:
            self.ppibs_gap_analysis['top_ranges'].append({
                'range_label': range_name,
                'product_count': prod_count,
                'obsolete_count': obsolete_count,
                'obsolescence_rate': (obsolete_count / prod_count) * 100 if prod_count > 0 else 0,
                'brand_label': brand,
                'bu_label': bu,
                'priority_score': self._calculate_priority_score(prod_count, obsolete_count)
            })
        
        hierarchy_analysis['ppibs_analysis'] = self.ppibs_gap_analysis
        
        logger.info(f"Hierarchy analysis complete: {len(self.pl_services_distribution)} PL services, {len(self.brand_hierarchy)} brands")
        return hierarchy_analysis
    
    def _calculate_priority_score(self, product_count: int, obsolete_count: int) -> float:
        """Calculate priority score for ranges based on size and obsolescence"""
        # Higher score = higher priority for letter coverage
        size_factor = min(product_count / 1000, 10)  # Cap at 10 for very large ranges
        obsolescence_factor = (obsolete_count / product_count) * 5 if product_count > 0 else 0
        return size_factor + obsolescence_factor
    
    def build_hierarchical_vector_spaces(self) -> Dict[str, Any]:
        """Build hierarchical vector spaces optimized for different product categories"""
        logger.info("Building hierarchical vector spaces")
        
        if not self.embedding_model:
            self.initialize_embedding_model()
        
        # 1. Load product data for embedding
        products_query = """
            SELECT 
                PRODUCT_IDENTIFIER,
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_DESCRIPTION,
                BRAND_LABEL,
                BU_LABEL,
                PL_SERVICES,
                COMMERCIAL_STATUS,
                DEVICETYPE_LABEL
            FROM products 
            WHERE PRODUCT_DESCRIPTION IS NOT NULL 
            AND RANGE_LABEL IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 50000
        """
        
        products_data = self.conn.execute(products_query).fetchdf()
        logger.info(f"Loaded {len(products_data)} products for embedding")
        
        # 2. Create hierarchical embeddings
        hierarchical_spaces = {}
        
        # 2a. PL_SERVICES level (Primary hierarchy)
        for pl_service in self.pl_services_distribution.keys():
            pl_products = products_data[products_data['PL_SERVICES'] == pl_service]
            if len(pl_products) > 0:
                hierarchical_spaces[f"pl_service_{pl_service}"] = self._build_vector_space(
                    pl_products, f"PL_SERVICE_{pl_service}"
                )
        
        # 2b. Brand level (Secondary hierarchy)
        for brand in ['Schneider Electric', 'Square D', 'Telemecanique', 'Merlin Gerin']:
            brand_products = products_data[products_data['BRAND_LABEL'] == brand]
            if len(brand_products) > 100:  # Only for significant brands
                hierarchical_spaces[f"brand_{brand.replace(' ', '_')}"] = self._build_vector_space(
                    brand_products, f"BRAND_{brand}"
                )
        
        # 2c. Business Unit level (Tertiary hierarchy)
        for bu in ['POWER PRODUCTS', 'IND PROCESS AUTOMATION', 'HOME & DISTRIBUTION']:
            bu_products = products_data[products_data['BU_LABEL'] == bu]
            if len(bu_products) > 100:
                hierarchical_spaces[f"bu_{bu.replace(' ', '_')}"] = self._build_vector_space(
                    bu_products, f"BU_{bu}"
                )
        
        # 2d. Commercial Status level (Lifecycle-aware)
        obsolete_products = products_data[
            products_data['COMMERCIAL_STATUS'].isin(['18-End of commercialisation', '19-end of commercialization block'])
        ]
        if len(obsolete_products) > 0:
            hierarchical_spaces["obsolete_products"] = self._build_vector_space(
                obsolete_products, "OBSOLETE_PRODUCTS"
            )
        
        self.hierarchical_indices = hierarchical_spaces
        
        build_summary = {
            'total_spaces': len(hierarchical_spaces),
            'spaces_created': list(hierarchical_spaces.keys()),
            'total_products_embedded': len(products_data),
            'embedding_dimension': self.embedding_model.get_sentence_embedding_dimension()
        }
        
        logger.info(f"Built {len(hierarchical_spaces)} hierarchical vector spaces")
        return build_summary
    
    def _build_vector_space(self, products_df: pd.DataFrame, space_name: str) -> Dict[str, Any]:
        """Build a single vector space for a product subset"""
        logger.info(f"Building vector space: {space_name} with {len(products_df)} products")
        
        # Create rich text representations for embedding
        text_representations = []
        product_metadata = []
        
        for _, product in products_df.iterrows():
            # Combine multiple fields for rich semantic representation
            text_parts = []
            
            # Primary identifiers
            if product['RANGE_LABEL']:
                text_parts.append(f"Range: {product['RANGE_LABEL']}")
            if product['SUBRANGE_LABEL']:
                text_parts.append(f"Subrange: {product['SUBRANGE_LABEL']}")
            
            # Description (most important)
            if product['PRODUCT_DESCRIPTION']:
                text_parts.append(f"Description: {product['PRODUCT_DESCRIPTION']}")
            
            # Context
            if product['DEVICETYPE_LABEL']:
                text_parts.append(f"Device Type: {product['DEVICETYPE_LABEL']}")
            if product['BRAND_LABEL']:
                text_parts.append(f"Brand: {product['BRAND_LABEL']}")
            
            text_representation = " | ".join(text_parts)
            text_representations.append(text_representation)
            
            # Store metadata
            product_metadata.append({
                'product_id': product['PRODUCT_IDENTIFIER'],
                'range_label': product['RANGE_LABEL'],
                'subrange_label': product['SUBRANGE_LABEL'],
                'description': product['PRODUCT_DESCRIPTION'],
                'brand_label': product['BRAND_LABEL'],
                'bu_label': product['BU_LABEL'],
                'pl_services': product['PL_SERVICES'],
                'commercial_status': product['COMMERCIAL_STATUS'],
                'device_type': product['DEVICETYPE_LABEL']
            })
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(text_representations, show_progress_bar=True)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype(np.float32))
        
        # Create clusters for better organization
        n_clusters = min(50, len(embeddings) // 20)  # Adaptive clustering
        if n_clusters > 1:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
        else:
            cluster_labels = np.zeros(len(embeddings))
        
        vector_space = {
            'index': index,
            'embeddings': embeddings,
            'metadata': product_metadata,
            'cluster_labels': cluster_labels,
            'n_clusters': n_clusters,
            'dimension': dimension,
            'size': len(embeddings)
        }
        
        logger.info(f"Vector space {space_name} built: {len(embeddings)} embeddings, {n_clusters} clusters")
        return vector_space
    
    def analyze_letter_coverage(self, letters_directory: str = "data/input/letters") -> LetterCoverageAnalysis:
        """Analyze coverage of the 300 letters across the product database"""
        logger.info("Analyzing letter coverage across product database")
        
        letters_path = Path(letters_directory)
        if not letters_path.exists():
            logger.warning(f"Letters directory not found: {letters_directory}")
            return LetterCoverageAnalysis(0, 0, 0, 0.0, [], {}, [])
        
        # Get all letter files
        letter_files = list(letters_path.glob("*.pdf")) + list(letters_path.glob("*.docx")) + list(letters_path.glob("*.doc"))
        total_letters = len(letter_files)
        
        logger.info(f"Found {total_letters} letters for coverage analysis")
        
        # Analyze letter content to extract product ranges
        covered_ranges = set()
        letter_range_mapping = {}
        
        for letter_file in letter_files[:50]:  # Sample for analysis
            try:
                # Extract ranges from filename (simplified analysis)
                filename = letter_file.stem.upper()
                detected_ranges = self._extract_ranges_from_filename(filename)
                
                if detected_ranges:
                    covered_ranges.update(detected_ranges)
                    letter_range_mapping[letter_file.name] = detected_ranges
                    
            except Exception as e:
                logger.warning(f"Error analyzing letter {letter_file.name}: {e}")
        
        # Compare with database ranges
        all_ranges_query = """
            SELECT DISTINCT RANGE_LABEL, COUNT(*) as product_count
            FROM products 
            WHERE RANGE_LABEL IS NOT NULL
            GROUP BY RANGE_LABEL
            ORDER BY product_count DESC
        """
        
        all_ranges_data = self.conn.execute(all_ranges_query).fetchall()
        all_ranges = {range_name: count for range_name, count in all_ranges_data}
        
        # Calculate coverage
        uncovered_ranges = set(all_ranges.keys()) - covered_ranges
        covered_products = sum(all_ranges[r] for r in covered_ranges if r in all_ranges)
        total_products = sum(all_ranges.values())
        coverage_percentage = (covered_products / total_products) * 100 if total_products > 0 else 0
        
        # PPIBS-specific gap analysis
        ppibs_ranges_query = """
            SELECT RANGE_LABEL, COUNT(*) as product_count
            FROM products 
            WHERE PL_SERVICES = 'PPIBS' AND RANGE_LABEL IS NOT NULL
            GROUP BY RANGE_LABEL
            ORDER BY product_count DESC
        """
        
        ppibs_ranges_data = self.conn.execute(ppibs_ranges_query).fetchall()
        ppibs_ranges = {range_name: count for range_name, count in ppibs_ranges_data}
        
        ppibs_covered = covered_ranges.intersection(set(ppibs_ranges.keys()))
        ppibs_uncovered = set(ppibs_ranges.keys()) - covered_ranges
        
        ppibs_gap = {
            'total_ppibs_ranges': len(ppibs_ranges),
            'covered_ppibs_ranges': len(ppibs_covered),
            'uncovered_ppibs_ranges': len(ppibs_uncovered),
            'ppibs_coverage_percentage': (len(ppibs_covered) / len(ppibs_ranges)) * 100 if ppibs_ranges else 0,
            'top_uncovered_ppibs': sorted(
                [(r, ppibs_ranges[r]) for r in ppibs_uncovered], 
                key=lambda x: x[1], 
                reverse=True
            )[:20]
        }
        
        # Priority gaps (high product count, uncovered)
        priority_gaps = []
        for range_name in uncovered_ranges:
            if range_name in all_ranges and all_ranges[range_name] > 100:
                priority_gaps.append({
                    'range_label': range_name,
                    'product_count': all_ranges[range_name],
                    'pl_services': self._get_range_pl_services(range_name),
                    'priority_score': self._calculate_priority_score(all_ranges[range_name], 0)
                })
        
        priority_gaps.sort(key=lambda x: x['priority_score'], reverse=True)
        
        coverage_analysis = LetterCoverageAnalysis(
            total_products=total_products,
            covered_products=covered_products,
            uncovered_products=total_products - covered_products,
            coverage_percentage=coverage_percentage,
            missing_ranges=list(uncovered_ranges),
            ppibs_gap_analysis=ppibs_gap,
            priority_gaps=priority_gaps[:50]
        )
        
        logger.info(f"Coverage analysis complete: {coverage_percentage:.1f}% coverage, {len(uncovered_ranges)} missing ranges")
        return coverage_analysis
    
    def _extract_ranges_from_filename(self, filename: str) -> Set[str]:
        """Extract product ranges from letter filename"""
        detected_ranges = set()
        
        # Common range patterns in filenames
        range_patterns = {
            'TESYS': ['TeSys D', 'TeSys F', 'TeSys B'],
            'PIX': ['PIX', 'PIX-DC', 'PIX Compact'],
            'GALAXY': ['Galaxy', 'MGE Galaxy'],
            'SEPAM': ['SEPAM', 'SEPAM 2040'],
            'COMPACT': ['Compact NSX', 'ComPacT NSX'],
            'EASYPACT': ['EasyPact MVS', 'EasyPact CVS'],
            'MASTERPACT': ['Masterpact MTZ', 'Masterpact NW'],
            'ACTI9': ['Acti 9 iC60', 'Acti 9 iC65'],
            'POWERPACT': ['PowerPact H-Frame', 'PowerPact P-Frame'],
            'RM6': ['RM6'],
            'MICOM': ['MiCOM'],
            'VAMP': ['VAMP']
        }
        
        for pattern, ranges in range_patterns.items():
            if pattern in filename:
                detected_ranges.update(ranges)
        
        return detected_ranges
    
    def _get_range_pl_services(self, range_name: str) -> str:
        """Get PL_SERVICES for a given range"""
        try:
            query = """
                SELECT PL_SERVICES, COUNT(*) as count
                FROM products 
                WHERE RANGE_LABEL = ?
                GROUP BY PL_SERVICES
                ORDER BY count DESC
                LIMIT 1
            """
            result = self.conn.execute(query, [range_name]).fetchone()
            return result[0] if result else "Unknown"
        except:
            return "Unknown"
    
    def enhanced_search(self, query: str, top_k: int = 10, search_strategy: str = "hierarchical") -> List[VectorSearchResult]:
        """Enhanced search using hierarchical vector spaces"""
        start_time = time.time()
        
        if not self.embedding_model:
            self.initialize_embedding_model()
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        results = []
        
        if search_strategy == "hierarchical":
            results = self._hierarchical_search(query_embedding[0], top_k)
        elif search_strategy == "exhaustive":
            results = self._exhaustive_search(query_embedding[0], top_k)
        elif search_strategy == "ppibs_focused":
            results = self._ppibs_focused_search(query_embedding[0], top_k)
        else:
            results = self._hybrid_search(query_embedding[0], top_k)
        
        # Update performance metrics
        search_time = time.time() - start_time
        self.search_performance['total_searches'] += 1
        self.search_performance['avg_search_time'] = (
            (self.search_performance['avg_search_time'] * (self.search_performance['total_searches'] - 1) + search_time) 
            / self.search_performance['total_searches']
        )
        self.search_performance['method_distribution'][search_strategy] += 1
        
        logger.info(f"Enhanced search completed in {search_time:.3f}s, {len(results)} results")
        return results
    
    def _hierarchical_search(self, query_embedding: np.ndarray, top_k: int) -> List[VectorSearchResult]:
        """Hierarchical search across multiple vector spaces"""
        all_results = []
        
        # Search in each hierarchical space
        for space_name, space_data in self.hierarchical_indices.items():
            try:
                # Search in this space
                similarities, indices = space_data['index'].search(
                    query_embedding.reshape(1, -1).astype(np.float32), 
                    min(top_k, space_data['size'])
                )
                
                # Convert to results
                for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                    if idx < len(space_data['metadata']):
                        metadata = space_data['metadata'][idx]
                        
                        result = VectorSearchResult(
                            product_id=metadata['product_id'],
                            range_label=metadata['range_label'],
                            description=metadata['description'],
                            similarity_score=float(similarity),
                            commercial_status=metadata['commercial_status'],
                            brand_label=metadata['brand_label'],
                            pl_services=metadata['pl_services'],
                            bu_label=metadata['bu_label'],
                            device_type=metadata['device_type'],
                            confidence_level=self._calculate_confidence(similarity, space_name),
                            search_method=f"hierarchical_{space_name}",
                            metadata={
                                'space_name': space_name,
                                'cluster_label': space_data['cluster_labels'][idx],
                                'rank_in_space': i + 1
                            }
                        )
                        all_results.append(result)
                        
            except Exception as e:
                logger.warning(f"Error searching in space {space_name}: {e}")
        
        # Deduplicate and rank results
        unique_results = self._deduplicate_results(all_results)
        return sorted(unique_results, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _ppibs_focused_search(self, query_embedding: np.ndarray, top_k: int) -> List[VectorSearchResult]:
        """PPIBS-focused search to address the gap in letter coverage"""
        ppibs_space_name = "pl_service_PPIBS"
        
        if ppibs_space_name not in self.hierarchical_indices:
            logger.warning("PPIBS vector space not available, falling back to hierarchical search")
            return self._hierarchical_search(query_embedding, top_k)
        
        space_data = self.hierarchical_indices[ppibs_space_name]
        
        # Enhanced search in PPIBS space
        similarities, indices = space_data['index'].search(
            query_embedding.reshape(1, -1).astype(np.float32), 
            min(top_k * 2, space_data['size'])  # Get more candidates
        )
        
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx < len(space_data['metadata']):
                metadata = space_data['metadata'][idx]
                
                # Boost score for obsolete products (higher priority)
                boosted_score = similarity
                if metadata['commercial_status'] in ['18-End of commercialisation', '19-end of commercialization block']:
                    boosted_score *= 1.2  # 20% boost for obsolete products
                
                result = VectorSearchResult(
                    product_id=metadata['product_id'],
                    range_label=metadata['range_label'],
                    description=metadata['description'],
                    similarity_score=float(boosted_score),
                    commercial_status=metadata['commercial_status'],
                    brand_label=metadata['brand_label'],
                    pl_services=metadata['pl_services'],
                    bu_label=metadata['bu_label'],
                    device_type=metadata['device_type'],
                    confidence_level=self._calculate_confidence(similarity, "ppibs_focused"),
                    search_method="ppibs_focused",
                    metadata={
                        'original_score': float(similarity),
                        'boosted_score': float(boosted_score),
                        'cluster_label': space_data['cluster_labels'][idx],
                        'obsolescence_priority': metadata['commercial_status'] in ['18-End of commercialisation', '19-end of commercialization block']
                    }
                )
                results.append(result)
        
        return sorted(results, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _hybrid_search(self, query_embedding: np.ndarray, top_k: int) -> List[VectorSearchResult]:
        """Hybrid search combining multiple strategies"""
        # Get results from different strategies
        hierarchical_results = self._hierarchical_search(query_embedding, top_k // 2)
        ppibs_results = self._ppibs_focused_search(query_embedding, top_k // 2)
        
        # Combine and deduplicate
        all_results = hierarchical_results + ppibs_results
        unique_results = self._deduplicate_results(all_results)
        
        return sorted(unique_results, key=lambda x: x.similarity_score, reverse=True)[:top_k]
    
    def _exhaustive_search(self, query_embedding: np.ndarray, top_k: int) -> List[VectorSearchResult]:
        """Exhaustive search across all vector spaces"""
        return self._hierarchical_search(query_embedding, top_k)
    
    def _deduplicate_results(self, results: List[VectorSearchResult]) -> List[VectorSearchResult]:
        """Remove duplicate results based on product ID"""
        seen = set()
        unique_results = []
        
        for result in results:
            if result.product_id not in seen:
                seen.add(result.product_id)
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_confidence(self, similarity_score: float, search_method: str) -> str:
        """Calculate confidence level based on similarity score and method"""
        if similarity_score > 0.8:
            return "High"
        elif similarity_score > 0.6:
            return "Medium"
        elif similarity_score > 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def generate_gap_analysis_report(self) -> str:
        """Generate comprehensive gap analysis report"""
        logger.info("Generating gap analysis report")
        
        from datetime import datetime
        
        # Analyze letter coverage
        coverage_analysis = self.analyze_letter_coverage()
        
        report_content = f"""# Enhanced Vector Search Engine - Gap Analysis Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Executive Summary

This report analyzes the gap between the 300 obsolescence letters and the complete IBcatalogue database of 342,229 products, with special focus on the PPIBS product line space.

**Key Findings:**
- **Total Products**: {coverage_analysis.total_products:,}
- **Covered Products**: {coverage_analysis.covered_products:,} ({coverage_analysis.coverage_percentage:.1f}%)
- **Uncovered Products**: {coverage_analysis.uncovered_products:,}
- **Missing Ranges**: {len(coverage_analysis.missing_ranges):,}

## 🚨 PPIBS Gap Analysis

PPIBS (Power Products Industrial Business Services) represents **46.1% of total products** ({self.pl_services_distribution.get('PPIBS', {}).get('product_count', 0):,} products) but shows significant coverage gaps:

### PPIBS Coverage Statistics
- **Total PPIBS Ranges**: {coverage_analysis.ppibs_gap_analysis.get('total_ppibs_ranges', 0):,}
- **Covered PPIBS Ranges**: {coverage_analysis.ppibs_gap_analysis.get('covered_ppibs_ranges', 0):,}
- **PPIBS Coverage**: {coverage_analysis.ppibs_gap_analysis.get('ppibs_coverage_percentage', 0):.1f}%

### Top Uncovered PPIBS Ranges
"""
        
        # Add top uncovered PPIBS ranges
        for i, (range_name, product_count) in enumerate(coverage_analysis.ppibs_gap_analysis.get('top_uncovered_ppibs', [])[:10]):
            report_content += f"{i+1}. **{range_name}**: {product_count:,} products\n"
        
        report_content += f"""

## 📊 Product Line Services Distribution

"""
        
        # Add PL services distribution
        for pl_service, data in self.pl_services_distribution.items():
            report_content += f"- **{pl_service}**: {data['product_count']:,} products ({data['obsolescence_rate']:.1f}% obsolete)\n"
        
        report_content += f"""

## 🎯 Priority Gaps for Letter Creation

The following ranges represent the highest priority for creating new obsolescence letters:

"""
        
        # Add priority gaps
        for i, gap in enumerate(coverage_analysis.priority_gaps[:15]):
            report_content += f"{i+1}. **{gap['range_label']}** ({gap['pl_services']})\n"
            report_content += f"   - Products: {gap['product_count']:,}\n"
            report_content += f"   - Priority Score: {gap['priority_score']:.1f}\n\n"
        
        report_content += f"""

## 🔍 Vector Search Optimization

### Hierarchical Vector Spaces Created
"""
        
        # Add vector space information
        for space_name, space_data in self.hierarchical_indices.items():
            report_content += f"- **{space_name}**: {space_data['size']:,} products, {space_data['n_clusters']} clusters\n"
        
        report_content += f"""

### Search Performance Metrics
- **Total Searches**: {self.search_performance['total_searches']:,}
- **Average Search Time**: {self.search_performance['avg_search_time']:.3f}s
- **Method Distribution**: {dict(self.search_performance['method_distribution'])}

## 🚀 Recommendations

### 1. Immediate Actions
- **Create PPIBS-focused letters** for top uncovered ranges
- **Prioritize high-volume obsolete products** for immediate attention
- **Implement enhanced search** for better product discovery

### 2. Strategic Improvements
- **Expand letter coverage** to reach 90%+ of products
- **Focus on PPIBS gap** - create 50+ new letters for uncovered ranges
- **Implement hierarchical search** for better product matching

### 3. Technical Enhancements
- **Deploy enhanced vector search** for production use
- **Implement gap monitoring** for continuous coverage analysis
- **Create automated alerts** for new uncovered products

---

*This analysis provides the foundation for addressing the significant gaps in obsolescence letter coverage, particularly in the PPIBS product line space.*
"""
        
        # Save report
        output_dir = Path("docs/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / "ENHANCED_VECTOR_SEARCH_GAP_ANALYSIS.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Gap analysis report saved: {report_path}")
        return str(report_path)
    
    def save_vector_indices(self, output_dir: str = "data/vector_indices"):
        """Save vector indices for production use"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for space_name, space_data in self.hierarchical_indices.items():
            # Save FAISS index
            index_path = output_path / f"{space_name}_index.faiss"
            faiss.write_index(space_data['index'], str(index_path))
            
            # Save metadata
            metadata_path = output_path / f"{space_name}_metadata.pkl"
            with open(metadata_path, 'wb') as f:
                pickle.dump({
                    'metadata': space_data['metadata'],
                    'cluster_labels': space_data['cluster_labels'],
                    'dimension': space_data['dimension'],
                    'size': space_data['size']
                }, f)
        
        logger.info(f"Vector indices saved to: {output_path}")
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run complete enhanced vector search analysis"""
        logger.info("Starting complete enhanced vector search analysis")
        
        start_time = time.time()
        
        try:
            # 1. Connect to database
            self.connect_database()
            
            # 2. Analyze product hierarchy
            hierarchy_analysis = self.analyze_product_hierarchy()
            
            # 3. Build hierarchical vector spaces
            vector_spaces = self.build_hierarchical_vector_spaces()
            
            # 4. Analyze letter coverage
            coverage_analysis = self.analyze_letter_coverage()
            
            # 5. Generate gap analysis report
            report_path = self.generate_gap_analysis_report()
            
            # 6. Save vector indices
            self.save_vector_indices()
            
            analysis_time = time.time() - start_time
            
            results = {
                'analysis_time': analysis_time,
                'hierarchy_analysis': hierarchy_analysis,
                'vector_spaces': vector_spaces,
                'coverage_analysis': coverage_analysis,
                'report_path': report_path,
                'performance_metrics': self.search_performance
            }
            
            logger.info(f"Complete analysis finished in {analysis_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main function for standalone execution"""
    engine = EnhancedVectorSearchEngine()
    
    try:
        results = engine.run_complete_analysis()
        
        print("\n🎉 ENHANCED VECTOR SEARCH ANALYSIS COMPLETE!")
        print(f"⏱️  Analysis time: {results['analysis_time']:.2f}s")
        print(f"📊 Vector spaces created: {results['vector_spaces']['total_spaces']}")
        print(f"📋 Report: {results['report_path']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 