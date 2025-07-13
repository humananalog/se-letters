"""Embedding and vector search service for the SE Letters project."""

import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

import faiss
from sentence_transformers import SentenceTransformer

from ..core.config import Config
from ..core.exceptions import ProcessingError
from ..models.product import Product, ProductRange
from ..models.letter import Letter
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings and performing vector similarity search."""

    def __init__(self, config: Config) -> None:
        """Initialize the embedding service.
        
        Args:
            config: Configuration instance.
        """
        self.config = config
        self.model_name = config.embedding.model_name
        self.vector_dim = config.embedding.vector_dimension
        self.similarity_threshold = config.embedding.similarity_threshold
        self.top_k = config.embedding.top_k_results
        
        # Initialize sentence transformer
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # FAISS index
        self.index: Optional[faiss.Index] = None
        self.product_texts: List[str] = []
        self.products: List[Product] = []
        
        # Index file paths
        self.index_dir = Path(config.embedding.index_directory)
        self.index_file = self.index_dir / "faiss_index.idx"
        self.metadata_file = self.index_dir / "metadata.pkl"

    def build_product_index(self, products: List[Product]) -> None:
        """Build FAISS index from product data.
        
        Args:
            products: List of Product objects to index.
        """
        start_time = time.time()
        
        logger.info(f"Building FAISS index for {len(products)} products")
        
        # Prepare text representations
        self.products = products
        self.product_texts = []
        
        for product in products:
            # Create searchable text from product attributes
            text_parts = []
            
            if product.range_name:
                text_parts.append(product.range_name)
            
            if product.subrange:
                text_parts.append(product.subrange)
            
            if product.model:
                text_parts.append(product.model)
            
            if product.description:
                text_parts.append(product.description)
            
            # Add computed properties
            text_parts.append(product.full_range)
            text_parts.append(product.full_name)
            
            # Join all text parts
            product_text = " ".join(text_parts)
            self.product_texts.append(product_text)
        
        # Generate embeddings
        logger.info("Generating embeddings...")
        embeddings = self.model.encode(
            self.product_texts,
            batch_size=self.config.embedding.batch_size,
            show_progress_bar=True,
            normalize_embeddings=True
        )
        
        # Create FAISS index
        logger.info("Creating FAISS index...")
        self.index = faiss.IndexFlatIP(embeddings.shape[1])  # Inner product for cosine similarity
        self.index.add(embeddings.astype('float32'))
        
        # Save index and metadata
        self._save_index()
        
        processing_time = time.time() - start_time
        logger.info(f"Index built successfully in {processing_time:.2f}s")

    def load_index(self) -> bool:
        """Load existing FAISS index from disk.
        
        Returns:
            True if index loaded successfully, False otherwise.
        """
        try:
            if not self.index_file.exists() or not self.metadata_file.exists():
                logger.info("No existing index found")
                return False
            
            logger.info("Loading existing FAISS index...")
            
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_file))
            
            # Load metadata
            with open(self.metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            self.products = metadata['products']
            self.product_texts = metadata['product_texts']
            
            logger.info(f"Index loaded: {len(self.products)} products")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False

    def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        try:
            # Ensure directory exists
            self.index_dir.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_file))
            
            # Save metadata
            metadata = {
                'products': self.products,
                'product_texts': self.product_texts,
                'config': {
                    'model_name': self.model_name,
                    'vector_dim': self.vector_dim,
                    'similarity_threshold': self.similarity_threshold,
                }
            }
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info("Index and metadata saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise ProcessingError(f"Index save failed: {e}")

    def search_similar_products(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for products similar to the query.
        
        Args:
            query: Search query string.
            top_k: Number of results to return. If None, uses config default.
            
        Returns:
            List of search results with similarity scores.
        """
        if self.index is None:
            raise ProcessingError("No index loaded. Build or load an index first.")
        
        if top_k is None:
            top_k = self.top_k
        
        # Generate query embedding
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Prepare results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty results
                continue
            
            if score < self.similarity_threshold:
                continue
            
            product = self.products[idx]
            result = {
                'rank': i + 1,
                'product': product,
                'similarity_score': float(score),
                'product_text': self.product_texts[idx],
                'query': query,
            }
            results.append(result)
        
        return results

    def match_letter_ranges(self, letter: Letter) -> Dict[str, Any]:
        """Match letter ranges against product database using embeddings.
        
        Args:
            letter: Letter object with extracted ranges.
            
        Returns:
            Dictionary with matching results.
        """
        if self.index is None:
            raise ProcessingError("No index loaded. Build or load an index first.")
        
        start_time = time.time()
        
        logger.info(f"Matching ranges for letter: {letter.letter_id}")
        
        all_matches = []
        range_results = {}
        
        # Search for each detected range
        for range_name in letter.ranges:
            logger.debug(f"Searching for range: {range_name}")
            
            # Search with the range name
            matches = self.search_similar_products(range_name)
            
            # Also search with variations
            variations = self._generate_range_variations(range_name)
            for variation in variations:
                variation_matches = self.search_similar_products(variation)
                matches.extend(variation_matches)
            
            # Remove duplicates and sort by score
            unique_matches = {}
            for match in matches:
                product_key = (match['product'].range_name, match['product'].subrange, match['product'].model)
                if product_key not in unique_matches or match['similarity_score'] > unique_matches[product_key]['similarity_score']:
                    unique_matches[product_key] = match
            
            sorted_matches = sorted(unique_matches.values(), key=lambda x: x['similarity_score'], reverse=True)
            
            range_results[range_name] = sorted_matches
            all_matches.extend(sorted_matches)
        
        processing_time = time.time() - start_time
        
        # Aggregate results
        results = {
            'letter_id': letter.letter_id,
            'ranges_searched': letter.ranges,
            'total_matches': len(all_matches),
            'range_results': range_results,
            'processing_time': processing_time,
            'best_matches': sorted(all_matches, key=lambda x: x['similarity_score'], reverse=True)[:self.top_k]
        }
        
        logger.info(f"Found {len(all_matches)} total matches in {processing_time:.2f}s")
        
        return results

    def _generate_range_variations(self, range_name: str) -> List[str]:
        """Generate variations of a range name for better matching.
        
        Args:
            range_name: Original range name.
            
        Returns:
            List of variations to search.
        """
        variations = []
        
        # Add the original
        variations.append(range_name)
        
        # Add with different separators
        if '-' in range_name:
            variations.append(range_name.replace('-', ' '))
            variations.append(range_name.replace('-', ''))
        
        if ' ' in range_name:
            variations.append(range_name.replace(' ', '-'))
            variations.append(range_name.replace(' ', ''))
        
        # Add lowercase version
        variations.append(range_name.lower())
        
        # Add uppercase version
        variations.append(range_name.upper())
        
        # Remove duplicates while preserving order
        unique_variations = []
        seen = set()
        for variation in variations:
            if variation not in seen:
                unique_variations.append(variation)
                seen.add(variation)
        
        return unique_variations[1:]  # Exclude the original

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index.
        
        Returns:
            Dictionary with index statistics.
        """
        stats = {
            'index_loaded': self.index is not None,
            'model_name': self.model_name,
            'vector_dimension': self.vector_dim,
            'similarity_threshold': self.similarity_threshold,
            'top_k_results': self.top_k,
        }
        
        if self.index is not None:
            stats.update({
                'total_products': len(self.products),
                'index_size': self.index.ntotal,
                'index_dimension': self.index.d,
            })
        
        # Check file existence
        stats.update({
            'index_file_exists': self.index_file.exists(),
            'metadata_file_exists': self.metadata_file.exists(),
        })
        
        if self.index_file.exists():
            stats['index_file_size'] = self.index_file.stat().st_size
        
        if self.metadata_file.exists():
            stats['metadata_file_size'] = self.metadata_file.stat().st_size
        
        return stats

    def rebuild_index(self, products: List[Product]) -> None:
        """Rebuild the index from scratch.
        
        Args:
            products: List of products to index.
        """
        logger.info("Rebuilding index from scratch...")
        
        # Clear existing index
        self.index = None
        self.products = []
        self.product_texts = []
        
        # Build new index
        self.build_product_index(products)
        
        logger.info("Index rebuilt successfully")

    def validate_index(self) -> Dict[str, Any]:
        """Validate the current index integrity.
        
        Returns:
            Validation results.
        """
        validation = {
            'valid': True,
            'issues': [],
            'warnings': [],
        }
        
        if self.index is None:
            validation['valid'] = False
            validation['issues'].append("No index loaded")
            return validation
        
        # Check consistency
        if len(self.products) != len(self.product_texts):
            validation['valid'] = False
            validation['issues'].append("Product count mismatch with text count")
        
        if self.index.ntotal != len(self.products):
            validation['valid'] = False
            validation['issues'].append("Index size mismatch with product count")
        
        # Check for empty products
        empty_products = sum(1 for text in self.product_texts if not text.strip())
        if empty_products > 0:
            validation['warnings'].append(f"{empty_products} products have empty text")
        
        # Test search functionality
        try:
            test_results = self.search_similar_products("test", top_k=1)
            validation['search_working'] = True
        except Exception as e:
            validation['valid'] = False
            validation['issues'].append(f"Search test failed: {e}")
        
        return validation 