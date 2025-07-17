#!/usr/bin/env python3
"""
Production Pipeline Runner v2.3
Corrected workflow: Direct Grok → Intelligent Matching → Final Grok Validation → Database Storage

Author: Alexandre Huther
Version: 2.3.0
Date: 2025-07-17
"""

import argparse
import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.postgresql_production_pipeline_service_v2_3 import PostgreSQLProductionPipelineServiceV2_3


class ProductionPipelineRunnerV2_3:
    """
    Production Pipeline Runner v2.3
    
    CORRECTED WORKFLOW:
    1. Direct Grok Processing (no OCR/text extraction)
    2. Intelligent Product Matching (Range → Individual Products)
    3. Final Grok Validation (candidates passed back to Grok)
    4. Database Storage (1 letter → multiple IBcatalogue products)
    """
    
    def __init__(self):
        """Initialize the production pipeline runner v2.3"""
        self.pipeline_service = PostgreSQLProductionPipelineServiceV2_3()
        self.processing_results = []
        
        logger.info("🚀 Production Pipeline Runner v2.3 initialized")
        logger.info("📋 CORRECTED WORKFLOW: Direct Grok → Intelligent Matching → Final Grok Validation → Database")
    
    def process_single_document(self, file_path: Path, force_reprocess: bool = False):
        """Process a single document through the pipeline v2.3"""
        logger.info(f"📄 Processing document v2.3: {file_path}")
        logger.info(f"🔄 Force reprocess: {force_reprocess}")
        
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return {
                'success': False,
                'error': f"File not found: {file_path}"
            }
        
        if not file_path.is_file():
            logger.error(f"❌ Path is not a file: {file_path}")
            return {
                'success': False,
                'error': f"Path is not a file: {file_path}"
            }
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            logger.error(f"❌ Empty file: {file_path}")
            return {
                'success': False,
                'error': f"Empty file: {file_path}"
            }
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            logger.warning(f"⚠️ Large file detected: {file_size / (1024*1024):.2f}MB")
        
        try:
            # Process through pipeline v2.3
            result = self.pipeline_service.process_document(file_path, force_reprocess=force_reprocess)
            
            # Log result
            self._log_processing_result(file_path, result)
            
            # Store result
            self.processing_results.append(result)
            
            return {
                'success': result.success,
                'status': result.status.value,
                'document_id': result.document_id,
                'processing_time_ms': result.processing_time_ms,
                'confidence_score': result.confidence_score,
                'error_message': result.error_message,
                'pipeline_version': '2.3.0'
            }
            
        except Exception as e:
            logger.error(f"❌ Unexpected error processing {file_path}: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {e}",
                'pipeline_version': '2.3.0'
            }
    
    def _log_processing_result(self, file_path: Path, result):
        """Log processing result"""
        if result.success:
            logger.success(f"✅ Successfully processed: {file_path.name}")
            logger.info(f"📊 Document ID: {result.document_id}")
            logger.info(f"⏱️ Processing time: {result.processing_time_ms:.2f}ms")
            logger.info(f"🎯 Confidence: {result.confidence_score:.2f}")
            
            if result.final_grok_validation:
                validated_products = result.final_grok_validation.get('validated_products', [])
                logger.info(f"🔗 IBcatalogue products linked: {len(validated_products)}")
        else:
            logger.error(f"❌ Failed to process: {file_path.name}")
            logger.error(f"📝 Error: {result.error_message}")
    
    def get_statistics(self):
        """Get processing statistics"""
        return self.pipeline_service.get_processing_statistics()


def main():
    """Main function for production pipeline runner v2.3"""
    parser = argparse.ArgumentParser(
        description="Production Pipeline Runner v2.3 - Corrected workflow for SE Letters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CORRECTED WORKFLOW v2.3:
1. Direct Grok Processing (no OCR/text extraction)
2. Intelligent Product Matching (Range → Individual Products)  
3. Final Grok Validation (candidates passed back to Grok)
4. Database Storage (1 letter → multiple IBcatalogue products)

Examples:
  python scripts/production_pipeline_runner_v2_3.py document.pdf
  python scripts/production_pipeline_runner_v2_3.py --force-reprocess document.pdf
  python scripts/production_pipeline_runner_v2_3.py --json-output document.pdf
        """
    )
    
    parser.add_argument(
        'document_path',
        type=str,
        help='Path to the document to process'
    )
    
    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Force reprocessing even if document already exists'
    )
    
    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Production Pipeline Runner v2.3.0'
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = ProductionPipelineRunnerV2_3()
    
    # Process document
    file_path = Path(args.document_path)
    result = runner.process_single_document(file_path, force_reprocess=args.force_reprocess)
    
    # Output results
    if args.json_output:
        import json
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"✅ Successfully processed: {file_path.name}")
            print(f"📊 Document ID: {result.get('document_id')}")
            print(f"⏱️ Processing time: {result.get('processing_time_ms', 0):.2f}ms")
            print(f"🎯 Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"🔄 Pipeline version: {result.get('pipeline_version')}")
        else:
            print(f"❌ Failed to process: {file_path.name}")
            print(f"📝 Error: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main() 