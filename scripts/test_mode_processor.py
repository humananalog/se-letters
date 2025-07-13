#!/usr/bin/env python3
"""
Test Mode Document Processor for SE Letters Pipeline

This script processes documents in test mode with comprehensive debugging,
vector search, and product matching while using an isolated test database.
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.se_letters.services.document_processor import DocumentProcessor
from src.se_letters.services.xai_service import XAIService
from src.se_letters.services.embedding_service import EmbeddingService
from src.se_letters.core.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingStep:
    """Represents a single processing step with status and details."""
    step: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    startTime: float
    endTime: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class ProcessingResult:
    """Complete processing result with all debugging information."""
    documentId: str
    steps: List[ProcessingStep]
    metadata: Dict[str, Any]
    vectorSearch: List[Dict[str, Any]]
    productMatches: List[Dict[str, Any]]
    obsoleteProducts: List[Dict[str, Any]]
    modernizationProducts: List[Dict[str, Any]]
    debugLog: List[str]

class TestModeProcessor:
    """Handles document processing in test mode with comprehensive debugging."""
    
    def __init__(self, config):
        self.config = config
        self.debug_log = []
        self.steps = []
        
        # Initialize services
        self.doc_processor = DocumentProcessor(config)
        self.xai_service = XAIService(config)
        self.embedding_service = EmbeddingService(config)
        
        # Test mode configuration
        self.test_mode = True
        self.test_db_path = project_root / "data" / "test" / "test_ibcatalogue.duckdb"
        
        self.log_debug("Test mode processor initialized")
    
    def log_debug(self, message: str):
        """Add message to debug log."""
        timestamp = time.strftime("%H:%M:%S")
        self.debug_log.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def add_step(self, step_name: str) -> ProcessingStep:
        """Add a new processing step."""
        step = ProcessingStep(
            step=step_name,
            status="running",
            startTime=time.time()
        )
        self.steps.append(step)
        self.log_debug(f"Started step: {step_name}")
        return step
    
    def complete_step(self, step: ProcessingStep, details: Optional[Dict[str, Any]] = None):
        """Mark a step as completed."""
        step.status = "completed"
        step.endTime = time.time()
        step.details = details
        self.log_debug(f"Completed step: {step.step}")
    
    def fail_step(self, step: ProcessingStep, error: str):
        """Mark a step as failed."""
        step.status = "failed"
        step.endTime = time.time()
        step.error = error
        self.log_debug(f"Failed step: {step.step} - {error}")
    
    def process_document(self, document_path: str, document_id: str) -> ProcessingResult:
        """Process a document with comprehensive debugging."""
        self.log_debug(f"Starting document processing: {document_path}")
        
        try:
            # Step 1: Document Processing
            step1 = self.add_step("document_processing")
            try:
                extracted_text = self.doc_processor.extract_text(document_path)
                self.complete_step(step1, {
                    "file": document_path,
                    "text_length": len(extracted_text),
                    "extracted_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                })
                self.log_debug(f"Document processed: {len(extracted_text)} characters extracted")
            except Exception as e:
                self.fail_step(step1, str(e))
                raise
            
            # Step 2: AI Metadata Extraction
            step2 = self.add_step("ai_metadata_extraction")
            try:
                metadata = self.xai_service.extract_comprehensive_metadata(
                    extracted_text, 
                    Path(document_path).name
                )
                self.complete_step(step2, {
                    "text_length": len(extracted_text),
                    "metadata": metadata
                })
                self.log_debug(f"AI metadata extracted: {len(metadata.get('product_identification', {}).get('ranges', []))} ranges found")
            except Exception as e:
                self.fail_step(step2, str(e))
                raise
            
            # Step 3: Vector Search
            step3 = self.add_step("vector_search")
            try:
                search_results = self.embedding_service.search_products(metadata)
                self.complete_step(step3, {
                    "ranges": metadata.get('product_identification', {}).get('ranges', []),
                    "search_results": search_results
                })
                self.log_debug(f"Vector search completed: {len(search_results)} products found")
            except Exception as e:
                self.fail_step(step3, str(e))
                raise
            
            # Step 4: Product Analysis
            step4 = self.add_step("product_analysis")
            try:
                obsolete_products = [
                    p for p in search_results 
                    if p.get('obsoleteStatus', '').lower() == 'obsolete' or 
                       p.get('OBSOLETE_STATUS', '').lower() == 'obsolete'
                ]
                modernization_products = [
                    p for p in search_results 
                    if p.get('commercialStatus', '').lower() == 'modernization' or
                       p.get('COMMERCIAL_STATUS', '').lower() == 'modernization'
                ]
                
                self.complete_step(step4, {
                    "total_products": len(search_results),
                    "obsolete_count": len(obsolete_products),
                    "modernization_count": len(modernization_products)
                })
                self.log_debug(f"Product analysis: {len(obsolete_products)} obsolete, {len(modernization_products)} modernization products")
            except Exception as e:
                self.fail_step(step4, str(e))
                raise
            
            # Compile results
            result = ProcessingResult(
                documentId=document_id,
                steps=self.steps,
                metadata=metadata,
                vectorSearch=search_results,
                productMatches=search_results,
                obsoleteProducts=obsolete_products,
                modernizationProducts=modernization_products,
                debugLog=self.debug_log
            )
            
            self.log_debug("Document processing completed successfully")
            return result
            
        except Exception as e:
            self.log_debug(f"Document processing failed: {str(e)}")
            # Create error result
            return ProcessingResult(
                documentId=document_id,
                steps=self.steps,
                metadata={},
                vectorSearch=[],
                productMatches=[],
                obsoleteProducts=[],
                modernizationProducts=[],
                debugLog=self.debug_log
            )

def main():
    """Main entry point for test mode processing."""
    if len(sys.argv) < 3:
        print("Usage: python test_mode_processor.py <document_path> <document_id>")
        sys.exit(1)
    
    document_path = sys.argv[1]
    document_id = sys.argv[2]
    
    try:
        # Load configuration
        config = get_config()
        
        # Initialize processor
        processor = TestModeProcessor(config)
        
        # Process document
        result = processor.process_document(document_path, document_id)
        
        # Convert to dict for JSON serialization
        result_dict = asdict(result)
        
        # Save results to test directory
        output_path = project_root / "data" / "test" / "results" / f"{document_id}_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        # Print result to stdout for API capture
        print(json.dumps(result_dict, default=str))
        
    except Exception as e:
        logger.error(f"Test mode processing failed: {e}")
        error_result = {
            "documentId": document_id,
            "error": str(e),
            "debugLog": [f"Error: {str(e)}"]
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main() 