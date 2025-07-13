"""Main pipeline orchestration for the SE Letters project."""

from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Config
from .exceptions import ProcessingError
from ..models.document import Document
from ..models.letter import Letter
from ..services.document_processor import DocumentProcessor
from ..services.embedding_service import EmbeddingService
from ..services.xai_service import XAIService
from ..services.excel_service import ExcelService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Pipeline:
    """Main pipeline for processing obsolescence letters."""

    def __init__(self, config: Config) -> None:
        """Initialize the pipeline with configuration.
        
        Args:
            config: Configuration instance.
        """
        self.config = config
        self.document_processor = DocumentProcessor(config)
        self.embedding_service = EmbeddingService(config)
        self.xai_service = XAIService(config)
        self.excel_service = ExcelService(config)
        
        # Initialize directories
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.config.data.json_directory,
            self.config.data.temp_directory,
            self.config.data.logs_directory,
            Path(self.config.data.excel_output).parent,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    async def run(self) -> Dict[str, Any]:
        """Run the complete pipeline.
        
        Returns:
            Dictionary containing pipeline results and statistics.
            
        Raises:
            ProcessingError: If pipeline execution fails.
        """
        logger.info("Starting SE Letters pipeline")
        
        try:
            # Step 1: Load and process documents
            logger.info("Step 1: Loading and processing documents")
            documents = await self._load_documents()
            logger.info(f"Loaded {len(documents)} documents")
            
            # Step 2: Build embedding index
            logger.info("Step 2: Building embedding index")
            await self._build_embedding_index()
            
            # Step 3: Process letters with LLM
            logger.info("Step 3: Processing letters with LLM")
            letters = await self._process_letters(documents)
            logger.info(f"Processed {len(letters)} letters")
            
            # Step 4: Match to Excel records
            logger.info("Step 4: Matching to Excel records")
            results = await self._match_to_excel(letters)
            
            # Step 5: Generate reports
            logger.info("Step 5: Generating reports")
            report = self._generate_report(results)
            
            logger.info("Pipeline completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise ProcessingError(f"Pipeline execution failed: {e}") from e

    async def _load_documents(self) -> List[Document]:
        """Load and process all documents from the input directory.
        
        Returns:
            List of processed documents.
        """
        input_dir = Path(self.config.data.letters_directory)
        if not input_dir.exists():
            raise ProcessingError(f"Input directory not found: {input_dir}")
        
        # Find all supported files
        supported_files = []
        for ext in self.config.data.supported_formats:
            supported_files.extend(input_dir.glob(f"*{ext}"))
        
        if not supported_files:
            raise ProcessingError(f"No supported files found in {input_dir}")
        
        logger.info(f"Found {len(supported_files)} files to process")
        
        # Process files in parallel
        documents = []
        with ThreadPoolExecutor(
            max_workers=self.config.processing.max_workers
        ) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self.document_processor.process_document, file_path
                ): file_path
                for file_path in supported_files
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    document = future.result()
                    if document:
                        documents.append(document)
                        logger.debug(f"Processed document: {file_path}")
                    else:
                        logger.warning(
                            f"Failed to process document: {file_path}"
                        )
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        return documents

    async def _build_embedding_index(self) -> None:
        """Build the embedding index for range detection."""
        try:
            # Load Excel data
            excel_data = self.excel_service.load_excel_data()
            
            # Extract unique ranges
            ranges = self.excel_service.extract_ranges(excel_data)
            logger.info(f"Extracted {len(ranges)} unique ranges")
            
            # Build embedding index
            await self.embedding_service.build_index(ranges)
            logger.info("Embedding index built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build embedding index: {e}")
            msg = f"Embedding index creation failed: {e}"
            raise ProcessingError(msg) from e

    async def _process_letters(self, documents: List[Document]) -> List[Letter]:
        """Process documents with LLM to extract letter metadata.
        
        Args:
            documents: List of processed documents.
            
        Returns:
            List of processed letters with metadata.
        """
        letters = []
        
        # Process in batches
        batch_size = self.config.processing.batch_size
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}")
            
            # Process batch in parallel
            batch_letters = await self._process_batch(batch)
            letters.extend(batch_letters)
        
        return letters

    async def _process_batch(self, documents: List[Document]) -> List[Letter]:
        """Process a batch of documents.
        
        Args:
            documents: Batch of documents to process.
            
        Returns:
            List of processed letters.
        """
        letters = []
        
        for document in documents:
            try:
                # Get similar ranges from embedding index
                embedding_service = self.embedding_service
                ranges = await embedding_service.find_similar_ranges(
                    document.text
                )
                
                # Process with LLM
                letter_metadata = await self.xai_service.process_letter(
                    document.text, ranges
                )
                
                # Create letter object
                letter = Letter(
                    document=document,
                    metadata=letter_metadata,
                    similar_ranges=ranges
                )
                
                letters.append(letter)
                logger.debug(f"Processed letter: {document.file_path}")
                
            except Exception as e:
                logger.error(
                    f"Error processing letter {document.file_path}: {e}"
                )
                # Continue with other documents
        
        return letters

    async def _match_to_excel(self, letters: List[Letter]) -> Dict[str, Any]:
        """Match letters to Excel records.
        
        Args:
            letters: List of processed letters.
            
        Returns:
            Dictionary containing matching results.
        """
        try:
            # Perform matching
            results = self.excel_service.match_letters_to_records(letters)
            
            # Save results
            output_path = Path(self.config.data.excel_output)
            self.excel_service.save_results(results, output_path)
            
            # Save individual letter JSONs
            self._save_letter_jsons(letters)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to match letters to Excel: {e}")
            raise ProcessingError(f"Excel matching failed: {e}") from e

    def _save_letter_jsons(self, letters: List[Letter]) -> None:
        """Save individual letter JSON files.
        
        Args:
            letters: List of processed letters.
        """
        json_dir = Path(self.config.data.json_directory)
        
        for letter in letters:
            try:
                # Generate filename from document path
                filename = f"{letter.document.file_path.stem}.json"
                json_path = json_dir / filename
                
                # Save JSON
                letter.save_json(json_path)
                logger.debug(f"Saved letter JSON: {json_path}")
                
            except Exception as e:
                logger.error(f"Error saving letter JSON: {e}")

    def _generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final pipeline report.
        
        Args:
            results: Matching results.
            
        Returns:
            Pipeline report.
        """
        return {
            "status": "completed",
            "total_documents": results.get("total_documents", 0),
            "total_letters": results.get("total_letters", 0),
            "matched_records": results.get("matched_records", 0),
            "unmatched_records": results.get("unmatched_records", 0),
            "processing_time": results.get("processing_time", 0),
            "output_files": {
                "excel": self.config.data.excel_output,
                "json_directory": self.config.data.json_directory,
            }
        }

    async def cleanup(self) -> None:
        """Cleanup temporary files and resources."""
        if self.config.data.cleanup_on_exit:
            temp_dir = Path(self.config.data.temp_directory)
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary files")
        
        # Close any open resources
        await self.embedding_service.cleanup()
        await self.xai_service.cleanup() 