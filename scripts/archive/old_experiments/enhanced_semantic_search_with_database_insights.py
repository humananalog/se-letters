#!/usr/bin/env python3
"""
Enhanced Semantic Search with Database Insights
Implements optimized embeddings and vector search based on comprehensive database analysis
"""

import sys
import time
import json
import pickle
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import duckdb
import pandas as pd

# Import faiss with fallback
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not available - using fallback search")

@dataclass
class SearchResult:
    """Enhanced search result with database context"""
    product_id: str
    range_label: str
    product_description: str
    brand_label: str
    commercial_status: str
    device_type: str
    similarity_score: float
    context_score: float
    final_score: float
    match_type: str  # 'exact', 'semantic', 'hybrid'


class DatabaseIntelligentEmbedding:
    """Intelligent embedding system using database insights"""
    
    def __init__(self, db_path: str = "data/IBcatalogue.duckdb"):
        self.db_path = db_path
        self.conn = None
        self.embeddings = {}
        self.indices = {}
        self.product_data = {}
        self.embedding_model = None
        
        # Database insights
        self.range_embeddings = {}
        self.brand_embeddings = {}
        self.device_type_embeddings = {}
        
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the embedding system"""
        print("🚀 Initializing Enhanced Semantic Search System")
        print("=" * 60)
        
        # Connect to database
        self.conn = duckdb.connect(self.db_path)
        
        # Initialize embedding model
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded sentence transformer model")
        except ImportError:
            print("⚠️ sentence-transformers not available, using mock embeddings")
            self.embedding_model = None
        
        # Load product data
        self._load_product_data()
        
        # Create hierarchical embeddings
        self._create_hierarchical_embeddings()
        
        # Build optimized search indices
        self._build_search_indices()
    
    def _load_product_data(self):
        """Load and structure product data"""
        print("\n📊 Loading product data...")
        
        # Load core product data
        query = """
            SELECT 
                PRODUCT_IDENTIFIER,
                RANGE_LABEL,
                SUBRANGE_LABEL,
                PRODUCT_DESCRIPTION,
                BRAND_LABEL,
                COMMERCIAL_STATUS,
                DEVICETYPE_LABEL,
                BU_LABEL,
                PL_SERVICES
            FROM products
            WHERE PRODUCT_IDENTIFIER IS NOT NULL
            AND PRODUCT_DESCRIPTION IS NOT NULL
        """
        
        df = self.conn.execute(query).fetchdf()
        print(f"✅ Loaded {len(df):,} products")
        
        # Structure data for efficient access
        for _, row in df.iterrows():
            product_id = row['PRODUCT_IDENTIFIER']
            self.product_data[product_id] = {
                'product_id': product_id,
                'range_label': row['RANGE_LABEL'] or '',
                'subrange_label': row['SUBRANGE_LABEL'] or '',
                'product_description': row['PRODUCT_DESCRIPTION'] or '',
                'brand_label': row['BRAND_LABEL'] or '',
                'commercial_status': row['COMMERCIAL_STATUS'] or '',
                'device_type': row['DEVICETYPE_LABEL'] or '',
                'bu_label': row['BU_LABEL'] or '',
                'pl_services': row['PL_SERVICES'] or ''
            }
    
    def _create_hierarchical_embeddings(self):
        """Create hierarchical embeddings based on database structure"""
        print("\n🌳 Creating hierarchical embeddings...")
        
        if not self.embedding_model:
            print("⚠️ Skipping embedding creation (no model available)")
            return
        
        # 1. Range-level embeddings
        print("  📦 Creating range embeddings...")
        range_texts = {}
        
        # Get range descriptions
        range_query = """
            SELECT 
                RANGE_LABEL,
                COUNT(*) as product_count,
                STRING_AGG(DISTINCT PRODUCT_DESCRIPTION, ' | ') as descriptions,
                STRING_AGG(DISTINCT DEVICETYPE_LABEL, ' | ') as device_types,
                STRING_AGG(DISTINCT BRAND_LABEL, ' | ') as brands
            FROM products
            WHERE RANGE_LABEL IS NOT NULL
            GROUP BY RANGE_LABEL
            ORDER BY product_count DESC
            LIMIT 1000
        """
        
        range_data = self.conn.execute(range_query).fetchall()
        
        for range_label, count, descriptions, device_types, brands in range_data:
            # Create rich text representation
            range_text = f"Range: {range_label}"
            
            if descriptions:
                # Take first few descriptions
                desc_list = descriptions.split(' | ')[:5]
                range_text += f" Products: {' '.join(desc_list)}"
            
            if device_types:
                range_text += f" Types: {device_types}"
            
            if brands:
                range_text += f" Brands: {brands}"
            
            range_texts[range_label] = range_text
        
        # Generate embeddings for ranges
        if range_texts:
            range_names = list(range_texts.keys())
            range_descriptions = list(range_texts.values())
            
            embeddings = self.embedding_model.encode(range_descriptions)
            
            for i, range_name in enumerate(range_names):
                self.range_embeddings[range_name] = embeddings[i]
        
        print(f"    ✅ Created {len(self.range_embeddings)} range embeddings")
        
        # 2. Brand-level embeddings
        print("  🏢 Creating brand embeddings...")
        brand_query = """
            SELECT 
                BRAND_LABEL,
                COUNT(*) as product_count,
                STRING_AGG(DISTINCT RANGE_LABEL, ' | ') as ranges,
                STRING_AGG(DISTINCT DEVICETYPE_LABEL, ' | ') as device_types
            FROM products
            WHERE BRAND_LABEL IS NOT NULL
            GROUP BY BRAND_LABEL
            ORDER BY product_count DESC
            LIMIT 100
        """
        
        brand_data = self.conn.execute(brand_query).fetchall()
        brand_texts = {}
        
        for brand_label, count, ranges, device_types in brand_data:
            brand_text = f"Brand: {brand_label}"
            
            if ranges:
                range_list = ranges.split(' | ')[:10]
                brand_text += f" Ranges: {' '.join(range_list)}"
            
            if device_types:
                brand_text += f" Types: {device_types}"
            
            brand_texts[brand_label] = brand_text
        
        if brand_texts:
            brand_names = list(brand_texts.keys())
            brand_descriptions = list(brand_texts.values())
            
            embeddings = self.embedding_model.encode(brand_descriptions)
            
            for i, brand_name in enumerate(brand_names):
                self.brand_embeddings[brand_name] = embeddings[i]
        
        print(f"    ✅ Created {len(self.brand_embeddings)} brand embeddings")
        
        # 3. Device type embeddings
        print("  🔧 Creating device type embeddings...")
        device_query = """
            SELECT 
                DEVICETYPE_LABEL,
                COUNT(*) as product_count,
                STRING_AGG(DISTINCT RANGE_LABEL, ' | ') as ranges,
                STRING_AGG(DISTINCT BRAND_LABEL, ' | ') as brands
            FROM products
            WHERE DEVICETYPE_LABEL IS NOT NULL
            GROUP BY DEVICETYPE_LABEL
            ORDER BY product_count DESC
            LIMIT 200
        """
        
        device_data = self.conn.execute(device_query).fetchall()
        device_texts = {}
        
        for device_label, count, ranges, brands in device_data:
            device_text = f"Device: {device_label}"
            
            if ranges:
                range_list = ranges.split(' | ')[:10]
                device_text += f" Ranges: {' '.join(range_list)}"
            
            if brands:
                brand_list = brands.split(' | ')[:5]
                device_text += f" Brands: {' '.join(brand_list)}"
            
            device_texts[device_label] = device_text
        
        if device_texts:
            device_names = list(device_texts.keys())
            device_descriptions = list(device_texts.values())
            
            embeddings = self.embedding_model.encode(device_descriptions)
            
            for i, device_name in enumerate(device_names):
                self.device_type_embeddings[device_name] = embeddings[i]
        
        print(f"    ✅ Created {len(self.device_type_embeddings)} device type embeddings")
    
    def _build_search_indices(self):
        """Build optimized search indices"""
        print("\n🔍 Building search indices...")
        
        if not self.embedding_model or not FAISS_AVAILABLE:
            print("⚠️ Skipping index creation (no model or FAISS available)")
            return
        
        # 1. Product-level index
        print("  📦 Building product index...")
        product_texts = []
        product_ids = []
        
        for product_id, data in list(self.product_data.items())[:10000]:  # Limit for demo
            # Create rich product representation
            product_text = f"{data['range_label']} {data['product_description']}"
            if data['brand_label']:
                product_text += f" {data['brand_label']}"
            if data['device_type']:
                product_text += f" {data['device_type']}"
            
            product_texts.append(product_text)
            product_ids.append(product_id)
        
        if product_texts:
            product_embeddings = self.embedding_model.encode(product_texts)
            
            # Create FAISS index
            dimension = product_embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(product_embeddings)
            index.add(product_embeddings.astype(np.float32))
            
            self.indices['products'] = {
                'index': index,
                'ids': product_ids,
                'embeddings': product_embeddings
            }
            
            print(f"    ✅ Built product index with {len(product_ids)} products")
        
        # 2. Range-level index
        if self.range_embeddings:
            print("  📦 Building range index...")
            range_names = list(self.range_embeddings.keys())
            range_embeddings = np.array(list(self.range_embeddings.values()))
            
            dimension = range_embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            
            faiss.normalize_L2(range_embeddings)
            index.add(range_embeddings.astype(np.float32))
            
            self.indices['ranges'] = {
                'index': index,
                'ids': range_names,
                'embeddings': range_embeddings
            }
            
            print(f"    ✅ Built range index with {len(range_names)} ranges")
    
    def search_products(self, query: str, top_k: int = 10, search_type: str = 'hybrid') -> List[SearchResult]:
        """Enhanced product search with multiple strategies"""
        
        if not self.embedding_model:
            return self._fallback_search(query, top_k)
        
        print(f"\n🔍 Searching for: '{query}' (type: {search_type})")
        
        results = []
        
        if search_type in ['hybrid', 'semantic']:
            # Semantic search
            semantic_results = self._semantic_search(query, top_k)
            results.extend(semantic_results)
        
        if search_type in ['hybrid', 'exact']:
            # Exact/pattern search
            exact_results = self._exact_search(query, top_k)
            results.extend(exact_results)
        
        # Combine and rank results
        final_results = self._combine_and_rank_results(results, query)
        
        return final_results[:top_k]
    
    def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Semantic search using embeddings"""
        results = []
        
        if not FAISS_AVAILABLE:
            print("⚠️ FAISS not available for semantic search")
            return results
        
        # Get query embedding
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search in product index
        if 'products' in self.indices:
            index_data = self.indices['products']
            scores, indices = index_data['index'].search(query_embedding.astype(np.float32), top_k * 2)
            
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0:  # Valid index
                    product_id = index_data['ids'][idx]
                    product_data = self.product_data[product_id]
                    
                    # Calculate context score
                    context_score = self._calculate_context_score(product_data, query)
                    
                    # Final score combines similarity and context
                    final_score = (score * 0.7) + (context_score * 0.3)
                    
                    result = SearchResult(
                        product_id=product_id,
                        range_label=product_data['range_label'],
                        product_description=product_data['product_description'],
                        brand_label=product_data['brand_label'],
                        commercial_status=product_data['commercial_status'],
                        device_type=product_data['device_type'],
                        similarity_score=float(score),
                        context_score=context_score,
                        final_score=final_score,
                        match_type='semantic'
                    )
                    
                    results.append(result)
        
        return results
    
    def _exact_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Exact/pattern search using database queries"""
        results = []
        
        query_upper = query.upper()
        
        # Search patterns
        search_patterns = [
            f"UPPER(RANGE_LABEL) LIKE '%{query_upper}%'",
            f"UPPER(PRODUCT_DESCRIPTION) LIKE '%{query_upper}%'",
            f"UPPER(PRODUCT_IDENTIFIER) LIKE '%{query_upper}%'",
            f"UPPER(BRAND_LABEL) LIKE '%{query_upper}%'",
            f"UPPER(DEVICETYPE_LABEL) LIKE '%{query_upper}%'"
        ]
        
        search_query = f"""
            SELECT 
                PRODUCT_IDENTIFIER,
                RANGE_LABEL,
                PRODUCT_DESCRIPTION,
                BRAND_LABEL,
                COMMERCIAL_STATUS,
                DEVICETYPE_LABEL,
                CASE 
                    WHEN UPPER(RANGE_LABEL) LIKE '%{query_upper}%' THEN 1.0
                    WHEN UPPER(PRODUCT_IDENTIFIER) LIKE '%{query_upper}%' THEN 0.9
                    WHEN UPPER(PRODUCT_DESCRIPTION) LIKE '%{query_upper}%' THEN 0.8
                    WHEN UPPER(BRAND_LABEL) LIKE '%{query_upper}%' THEN 0.7
                    WHEN UPPER(DEVICETYPE_LABEL) LIKE '%{query_upper}%' THEN 0.6
                    ELSE 0.5
                END as match_score
            FROM products
            WHERE ({' OR '.join(search_patterns)})
            ORDER BY match_score DESC
            LIMIT {top_k * 2}
        """
        
        try:
            exact_matches = self.conn.execute(search_query).fetchall()
            
            for row in exact_matches:
                product_id, range_label, description, brand, status, device_type, match_score = row
                
                # Calculate context score
                product_data = {
                    'range_label': range_label or '',
                    'product_description': description or '',
                    'brand_label': brand or '',
                    'commercial_status': status or '',
                    'device_type': device_type or ''
                }
                
                context_score = self._calculate_context_score(product_data, query)
                final_score = (match_score * 0.8) + (context_score * 0.2)
                
                result = SearchResult(
                    product_id=product_id,
                    range_label=range_label or '',
                    product_description=description or '',
                    brand_label=brand or '',
                    commercial_status=status or '',
                    device_type=device_type or '',
                    similarity_score=float(match_score),
                    context_score=context_score,
                    final_score=final_score,
                    match_type='exact'
                )
                
                results.append(result)
        
        except Exception as e:
            print(f"⚠️ Exact search error: {e}")
        
        return results
    
    def _calculate_context_score(self, product_data: Dict[str, str], query: str) -> float:
        """Calculate context relevance score"""
        score = 0.0
        query_upper = query.upper()
        
        # Range relevance
        if product_data['range_label'] and query_upper in product_data['range_label'].upper():
            score += 0.3
        
        # Description relevance
        if product_data['product_description']:
            desc_words = product_data['product_description'].upper().split()
            query_words = query_upper.split()
            common_words = set(desc_words) & set(query_words)
            if common_words:
                score += 0.2 * (len(common_words) / max(len(query_words), 1))
        
        # Brand relevance
        if product_data['brand_label'] and query_upper in product_data['brand_label'].upper():
            score += 0.2
        
        # Device type relevance
        if product_data['device_type'] and query_upper in product_data['device_type'].upper():
            score += 0.2
        
        # Commercial status bonus (prefer active products)
        if product_data['commercial_status'] == '08-Commercialised':
            score += 0.1
        
        return min(1.0, score)
    
    def _combine_and_rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Combine and rank results from different search methods"""
        
        # Group by product ID to avoid duplicates
        product_results = {}
        
        for result in results:
            product_id = result.product_id
            
            if product_id not in product_results:
                product_results[product_id] = result
            else:
                # Keep the result with higher final score
                if result.final_score > product_results[product_id].final_score:
                    product_results[product_id] = result
        
        # Sort by final score
        sorted_results = sorted(product_results.values(), key=lambda x: x.final_score, reverse=True)
        
        return sorted_results
    
    def _fallback_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Fallback search when embeddings are not available"""
        print("⚠️ Using fallback search (no embeddings)")
        
        # Simple database search
        query_upper = query.upper()
        
        search_query = f"""
            SELECT 
                PRODUCT_IDENTIFIER,
                RANGE_LABEL,
                PRODUCT_DESCRIPTION,
                BRAND_LABEL,
                COMMERCIAL_STATUS,
                DEVICETYPE_LABEL
            FROM products
            WHERE UPPER(RANGE_LABEL) LIKE '%{query_upper}%'
               OR UPPER(PRODUCT_DESCRIPTION) LIKE '%{query_upper}%'
               OR UPPER(PRODUCT_IDENTIFIER) LIKE '%{query_upper}%'
            LIMIT {top_k}
        """
        
        results = []
        
        try:
            matches = self.conn.execute(search_query).fetchall()
            
            for row in matches:
                product_id, range_label, description, brand, status, device_type = row
                
                result = SearchResult(
                    product_id=product_id,
                    range_label=range_label or '',
                    product_description=description or '',
                    brand_label=brand or '',
                    commercial_status=status or '',
                    device_type=device_type or '',
                    similarity_score=0.5,
                    context_score=0.5,
                    final_score=0.5,
                    match_type='fallback'
                )
                
                results.append(result)
        
        except Exception as e:
            print(f"⚠️ Fallback search error: {e}")
        
        return results
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    """Main function to test enhanced semantic search"""
    print("🚀 ENHANCED SEMANTIC SEARCH WITH DATABASE INSIGHTS")
    print("=" * 80)
    print("🧠 Hierarchical Embeddings | 🔍 Hybrid Search | 📊 Context Scoring")
    print()
    
    # Initialize search system
    search_system = DatabaseIntelligentEmbedding()
    
    try:
        # Test queries
        test_queries = [
            "PIX",
            "circuit breaker",
            "TeSys D",
            "Schneider Electric",
            "contactor",
            "protection relay",
            "Masterpact",
            "power supply",
            "automation",
            "obsolete products"
        ]
        
        print("🔍 TESTING ENHANCED SEARCH CAPABILITIES")
        print("=" * 60)
        
        all_results = {}
        
        for query in test_queries:
            print(f"\n📋 Query: '{query}'")
            print("-" * 40)
            
            # Test different search types
            search_types = ['hybrid', 'semantic', 'exact']
            
            for search_type in search_types:
                start_time = time.time()
                results = search_system.search_products(query, top_k=5, search_type=search_type)
                search_time = time.time() - start_time
                
                print(f"\n{search_type.upper()} SEARCH ({search_time:.3f}s):")
                
                if results:
                    for i, result in enumerate(results[:3], 1):
                        print(f"  {i}. {result.range_label} - {result.product_description[:50]}...")
                        print(f"     Score: {result.final_score:.3f} | Type: {result.match_type}")
                        print(f"     Brand: {result.brand_label} | Status: {result.commercial_status}")
                else:
                    print("     No results found")
                
                # Store results for analysis
                all_results[f"{query}_{search_type}"] = {
                    'query': query,
                    'search_type': search_type,
                    'result_count': len(results),
                    'search_time': search_time,
                    'results': [
                        {
                            'product_id': r.product_id,
                            'range_label': r.range_label,
                            'description': r.product_description,
                            'final_score': r.final_score,
                            'match_type': r.match_type
                        }
                        for r in results[:5]
                    ]
                }
        
        # Save results
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "enhanced_search_results.json"
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\n✅ Search results saved: {results_file}")
        
        # Summary statistics
        print(f"\n📊 SEARCH PERFORMANCE SUMMARY")
        print("=" * 50)
        
        total_queries = len(test_queries) * len(search_types)
        successful_queries = sum(1 for r in all_results.values() if r['result_count'] > 0)
        
        print(f"Total queries tested: {total_queries}")
        print(f"Successful queries: {successful_queries}")
        print(f"Success rate: {(successful_queries/total_queries)*100:.1f}%")
        
        avg_search_time = sum(r['search_time'] for r in all_results.values()) / len(all_results)
        print(f"Average search time: {avg_search_time:.3f}s")
        
        return 0
        
    except Exception as e:
        print(f"❌ Search system test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        search_system.close()


if __name__ == "__main__":
    exit(main()) 