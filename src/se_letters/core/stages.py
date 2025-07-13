"""Modular pipeline stages for the SE Letters pipeline."""

from typing import List, Dict, Any
from pathlib import Path
import asyncio

from .interfaces import IPipelineStage, PipelineContext, ProcessingResult
from .interfaces import IDocumentProcessor, IMetadataExtractor, IProductMatcher
from .event_bus import EventTypes
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessingStage(IPipelineStage):
    """Stage for processing documents."""
    
    def __init__(self, processor: IDocumentProcessor):
        """Initialize the stage.
        
        Args:
            processor: Document processor implementation
        """
        self.processor = processor
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute document processing stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated pipeline context
        """
        logger.info("Starting document processing stage")
        
        try:
            # Get input files from context
            input_files = context.data.get('input_files', [])
            if not input_files:
                raise ValueError("No input files provided")
            
            # Process documents
            processed_docs = []
            for file_path in input_files:
                result = await self.processor.process_document(Path(file_path))
                if result.success:
                    processed_docs.append(result.data)
                else:
                    context.errors.append(f"Failed to process {file_path}: {result.error}")
            
            # Update context
            context.data['processed_documents'] = processed_docs
            context.metadata['documents_processed'] = len(processed_docs)
            context.metadata['processing_errors'] = len(context.errors)
            
            logger.info(f"Processed {len(processed_docs)} documents")
            
        except Exception as e:
            error_msg = f"Document processing stage failed: {e}"
            logger.error(error_msg)
            context.errors.append(error_msg)
        
        return context
    
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        return "document_processing"
    
    def get_dependencies(self) -> List[str]:
        """Get list of required previous stages."""
        return []  # First stage, no dependencies


class MetadataExtractionStage(IPipelineStage):
    """Stage for extracting metadata from documents."""
    
    def __init__(self, extractor: IMetadataExtractor):
        """Initialize the stage.
        
        Args:
            extractor: Metadata extractor implementation
        """
        self.extractor = extractor
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute metadata extraction stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated pipeline context
        """
        logger.info("Starting metadata extraction stage")
        
        try:
            # Get processed documents from context
            processed_docs = context.data.get('processed_documents', [])
            if not processed_docs:
                raise ValueError("No processed documents available")
            
            # Extract metadata from each document
            extracted_metadata = []
            for doc in processed_docs:
                result = await self.extractor.extract_metadata(doc)
                if result.success:
                    extracted_metadata.append(result.data)
                else:
                    context.errors.append(f"Failed to extract metadata: {result.error}")
            
            # Update context
            context.data['extracted_metadata'] = extracted_metadata
            context.metadata['metadata_extracted'] = len(extracted_metadata)
            
            logger.info(f"Extracted metadata from {len(extracted_metadata)} documents")
            
        except Exception as e:
            error_msg = f"Metadata extraction stage failed: {e}"
            logger.error(error_msg)
            context.errors.append(error_msg)
        
        return context
    
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        return "metadata_extraction"
    
    def get_dependencies(self) -> List[str]:
        """Get list of required previous stages."""
        return ["document_processing"]


class ProductMatchingStage(IPipelineStage):
    """Stage for matching products based on metadata."""
    
    def __init__(self, matcher: IProductMatcher):
        """Initialize the stage.
        
        Args:
            matcher: Product matcher implementation
        """
        self.matcher = matcher
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute product matching stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated pipeline context
        """
        logger.info("Starting product matching stage")
        
        try:
            # Get extracted metadata from context
            extracted_metadata = context.data.get('extracted_metadata', [])
            if not extracted_metadata:
                raise ValueError("No extracted metadata available")
            
            # Build index if not already built
            await self.matcher.build_index()
            
            # Match products for each metadata set
            matched_products = []
            for metadata in extracted_metadata:
                result = await self.matcher.find_matching_products(metadata)
                if result.success:
                    matched_products.extend(result.data)
                else:
                    context.errors.append(f"Failed to match products: {result.error}")
            
            # Update context
            context.data['matched_products'] = matched_products
            context.metadata['products_matched'] = len(matched_products)
            
            logger.info(f"Matched {len(matched_products)} products")
            
        except Exception as e:
            error_msg = f"Product matching stage failed: {e}"
            logger.error(error_msg)
            context.errors.append(error_msg)
        
        return context
    
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        return "product_matching"
    
    def get_dependencies(self) -> List[str]:
        """Get list of required previous stages."""
        return ["metadata_extraction"]


class ReportGenerationStage(IPipelineStage):
    """Stage for generating reports."""
    
    def __init__(self, generators: List[Any]):
        """Initialize the stage.
        
        Args:
            generators: List of report generators
        """
        self.generators = generators
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute report generation stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated pipeline context
        """
        logger.info("Starting report generation stage")
        
        try:
            # Get matched products from context
            matched_products = context.data.get('matched_products', [])
            
            # Generate reports using all generators
            generated_reports = []
            for generator in self.generators:
                # Create processing result for the generator
                processing_results = [
                    ProcessingResult(success=True, data=matched_products)
                ]
                
                result = await generator.generate_report(processing_results)
                if result.success:
                    generated_reports.append(result.data)
                else:
                    context.errors.append(f"Failed to generate report: {result.error}")
            
            # Update context
            context.data['generated_reports'] = generated_reports
            context.metadata['reports_generated'] = len(generated_reports)
            
            logger.info(f"Generated {len(generated_reports)} reports")
            
        except Exception as e:
            error_msg = f"Report generation stage failed: {e}"
            logger.error(error_msg)
            context.errors.append(error_msg)
        
        return context
    
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        return "report_generation"
    
    def get_dependencies(self) -> List[str]:
        """Get list of required previous stages."""
        return ["product_matching"]


class ValidationStage(IPipelineStage):
    """Stage for validating pipeline results."""
    
    def __init__(self, validation_rules: Dict[str, Any] = None):
        """Initialize the stage.
        
        Args:
            validation_rules: Validation rules to apply
        """
        self.validation_rules = validation_rules or {}
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute validation stage.
        
        Args:
            context: Pipeline context
            
        Returns:
            Updated pipeline context
        """
        logger.info("Starting validation stage")
        
        try:
            # Validate pipeline results
            validation_results = []
            
            # Check if we have processed documents
            processed_docs = context.data.get('processed_documents', [])
            if not processed_docs:
                validation_results.append("No documents were processed")
            
            # Check if we have extracted metadata
            extracted_metadata = context.data.get('extracted_metadata', [])
            if not extracted_metadata:
                validation_results.append("No metadata was extracted")
            
            # Check if we have matched products
            matched_products = context.data.get('matched_products', [])
            if not matched_products:
                validation_results.append("No products were matched")
            
            # Check error count
            error_count = len(context.errors)
            if error_count > 0:
                validation_results.append(f"Pipeline had {error_count} errors")
            
            # Update context
            context.data['validation_results'] = validation_results
            context.metadata['validation_passed'] = len(validation_results) == 0
            
            if validation_results:
                logger.warning(f"Validation issues found: {validation_results}")
            else:
                logger.info("Validation passed")
            
        except Exception as e:
            error_msg = f"Validation stage failed: {e}"
            logger.error(error_msg)
            context.errors.append(error_msg)
        
        return context
    
    def get_stage_name(self) -> str:
        """Get the name of this stage."""
        return "validation"
    
    def get_dependencies(self) -> List[str]:
        """Get list of required previous stages."""
        return ["report_generation"] 