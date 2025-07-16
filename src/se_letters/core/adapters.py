"""Adapter classes to integrate existing services with modular architecture."""

from typing import Dict, Any, List
from pathlib import Path

from .interfaces import (
    IDocumentProcessor, IMetadataExtractor, IProductMatcher, IReportGenerator,
    ProcessingResult
)
from ..models.document import Document
from ..services.document_processor import DocumentProcessor
from ..services.xai_service import XAIService
# from ..services.excel_service import ExcelService  # Removed - using SOTA DuckDB
from ..services.sota_product_database_service import SOTAProductDatabaseService
from ..services.embedding_service import EmbeddingService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessorAdapter(IDocumentProcessor):
    """Adapter for the existing DocumentProcessor service."""
    
    def __init__(self, processor: DocumentProcessor):
        """Initialize the adapter.
        
        Args:
            processor: Existing DocumentProcessor instance
        """
        self.processor = processor
    
    async def process_document(self, file_path: Path) -> ProcessingResult:
        """Process a single document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Processing result with document data
        """
        try:
            # Use the existing processor
            result = self.processor.process_document(file_path)
            
            if result:
                return ProcessingResult(
                    success=True,
                    data=result,
                    metadata={'file_path': str(file_path)}
                )
            else:
                return ProcessingResult(
                    success=False,
                    error="Document processing returned None"
                )
                
        except Exception as e:
            logger.error(f"Document processing failed for {file_path}: {e}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def supports_format(self, file_path: Path) -> bool:
        """Check if processor supports this file format.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if format is supported
        """
        supported_extensions = {'.pdf', '.doc', '.docx'}
        return file_path.suffix.lower() in supported_extensions
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # The existing processor doesn't have cleanup
        pass


class MetadataExtractorAdapter(IMetadataExtractor):
    """Adapter for the existing XAIService for metadata extraction."""
    
    def __init__(self, xai_service: XAIService):
        """Initialize the adapter.
        
        Args:
            xai_service: Existing XAIService instance
        """
        self.xai_service = xai_service
        self._last_confidence = 0.0
    
    async def extract_metadata(self, document: Document) -> ProcessingResult:
        """Extract metadata from document.
        
        Args:
            document: Document to extract metadata from
            
        Returns:
            Processing result with extracted metadata
        """
        try:
            # Extract text from document
            text = getattr(document, 'text_content', '')
            if not text:
                return ProcessingResult(
                    success=False,
                    error="No text content in document"
                )
            
            # Use XAI service to extract metadata
            metadata = self.xai_service.extract_comprehensive_metadata(
                text, 
                getattr(document, 'file_name', 'unknown')
            )
            
            # Store confidence score
            self._last_confidence = metadata.get('confidence_score', 0.0)
            
            return ProcessingResult(
                success=True,
                data=metadata,
                metadata={'confidence': self._last_confidence}
            )
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def get_confidence_score(self) -> float:
        """Get confidence score for last extraction.
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        return self._last_confidence


class ProductMatcherAdapter(IProductMatcher):
    """Adapter for the existing SOTAProductDatabaseService and EmbeddingService."""
    
    def __init__(
        self, sota_service: SOTAProductDatabaseService, embedding_service: EmbeddingService
    ):
        """Initialize the adapter.
        
        Args:
            sota_service: Existing SOTAProductDatabaseService instance
            embedding_service: Existing EmbeddingService instance
        """
        self.sota_service = sota_service
        self.embedding_service = embedding_service
        self._index_built = False
    
    async def find_matching_products(
        self, metadata: Dict[str, Any]
    ) -> ProcessingResult:
        """Find products matching the metadata.
        
        Args:
            metadata: Extracted metadata
            
        Returns:
            Processing result with matching products
        """
        try:
            # Extract ranges from metadata
            ranges = []
            if 'product_identification' in metadata:
                ranges = metadata['product_identification'].get('ranges', [])
            
            if not ranges:
                return ProcessingResult(
                    success=False,
                    error="No product ranges found in metadata"
                )
            
            # Find matching products
            all_products = []
            for range_name in ranges:
                products = self.excel_service.find_products_by_range(range_name)
                all_products.extend(products)
            
            # Remove duplicates
            unique_products = []
            seen_ids = set()
            for product in all_products:
                product_id = getattr(product, 'product_id', None)
                if product_id and product_id not in seen_ids:
                    unique_products.append(product)
                    seen_ids.add(product_id)
            
            return ProcessingResult(
                success=True,
                data=unique_products,
                metadata={
                    'ranges_searched': ranges,
                    'total_matches': len(unique_products)
                }
            )
            
        except Exception as e:
            logger.error(f"Product matching failed: {e}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    async def build_index(self) -> None:
        """Build search index."""
        if not self._index_built:
            try:
                # Load IBcatalogue data
                self.excel_service.load_ibcatalogue()
                
                # Build embedding index if available
                if hasattr(self.embedding_service, 'build_index'):
                    self.embedding_service.build_index()
                
                self._index_built = True
                logger.info("Product matching index built successfully")
                
            except Exception as e:
                logger.error(f"Failed to build index: {e}")
                raise


class ReportGeneratorAdapter(IReportGenerator):
    """Adapter for report generation."""
    
    def __init__(self, format_type: str = "excel"):
        """Initialize the adapter.
        
        Args:
            format_type: Type of report to generate
        """
        self.format_type = format_type
    
    async def generate_report(self, results: List[ProcessingResult]) -> ProcessingResult:
        """Generate final report.
        
        Args:
            results: List of processing results
            
        Returns:
            Processing result with report data
        """
        try:
            # Extract products from results
            all_products = []
            for result in results:
                if result.success and result.data:
                    if isinstance(result.data, list):
                        all_products.extend(result.data)
                    else:
                        all_products.append(result.data)
            
            # Generate report based on format
            if self.format_type == "excel":
                report_data = self._generate_excel_report(all_products)
            elif self.format_type == "json":
                report_data = self._generate_json_report(all_products)
            else:
                report_data = self._generate_summary_report(all_products)
            
            return ProcessingResult(
                success=True,
                data=report_data,
                metadata={
                    'format': self.format_type,
                    'product_count': len(all_products)
                }
            )
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def supports_format(self, format_type: str) -> bool:
        """Check if generator supports this format.
        
        Args:
            format_type: Format to check
            
        Returns:
            True if format is supported
        """
        supported_formats = {"excel", "json", "summary"}
        return format_type in supported_formats
    
    def _generate_excel_report(self, products: List[Any]) -> Dict[str, Any]:
        """Generate Excel report data.
        
        Args:
            products: List of products
            
        Returns:
            Report data dictionary
        """
        return {
            'type': 'excel',
            'products': products,
            'summary': {
                'total_products': len(products),
                'format': 'excel'
            }
        }
    
    def _generate_json_report(self, products: List[Any]) -> Dict[str, Any]:
        """Generate JSON report data.
        
        Args:
            products: List of products
            
        Returns:
            Report data dictionary
        """
        return {
            'type': 'json',
            'products': [self._product_to_dict(p) for p in products],
            'summary': {
                'total_products': len(products),
                'format': 'json'
            }
        }
    
    def _generate_summary_report(self, products: List[Any]) -> Dict[str, Any]:
        """Generate summary report data.
        
        Args:
            products: List of products
            
        Returns:
            Report data dictionary
        """
        # Group products by range
        ranges = {}
        for product in products:
            range_name = getattr(product, 'range_name', 'Unknown')
            if range_name not in ranges:
                ranges[range_name] = []
            ranges[range_name].append(product)
        
        return {
            'type': 'summary',
            'total_products': len(products),
            'ranges': {name: len(prods) for name, prods in ranges.items()},
            'summary': {
                'total_products': len(products),
                'total_ranges': len(ranges),
                'format': 'summary'
            }
        }
    
    def _product_to_dict(self, product: Any) -> Dict[str, Any]:
        """Convert product to dictionary.
        
        Args:
            product: Product object
            
        Returns:
            Product as dictionary
        """
        if hasattr(product, '__dict__'):
            return product.__dict__
        elif hasattr(product, '_asdict'):
            return product._asdict()
        else:
            return {'product': str(product)} 