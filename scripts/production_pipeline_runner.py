#!/usr/bin/env python3
"""
SE Letters - Production Pipeline Runner with Enhanced Token Tracking
This script provides a command-line interface to the Stage 1 production pipeline
with comprehensive token tracking and analytics.

Usage:
    python scripts/production_pipeline_runner.py <document_path> [--force-reprocess] [--json-output]
"""

import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.postgresql_production_pipeline_service_stage1 import (
    PostgreSQLProductionPipelineServiceStage1
)


def process_document_with_tracking(
    document_path: str, 
    force_reprocess: bool = False
) -> Dict[str, Any]:
    """
    Process a document using the Stage 1 pipeline with enhanced token tracking.
    
    Args:
        document_path: Path to the document to process
        force_reprocess: Whether to force reprocessing
        
    Returns:
        Dictionary containing processing results and token tracking data
    """
    try:
        # Initialize the Stage 1 pipeline with enhanced tracking
        pipeline = PostgreSQLProductionPipelineServiceStage1()
        
        # Determine request type based on force_reprocess flag
        request_type = "FORCE" if force_reprocess else "PROCESS"
        
        # Process the document
        start_time = time.time()
        result = pipeline.process_document(Path(document_path), request_type=request_type)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Extract token usage from the result
        tracking_metadata = result.get('tracking_metadata', {}) if isinstance(result, dict) else {}
        token_usage = tracking_metadata.get('token_usage')
        call_id = tracking_metadata.get('call_id')
        raw_content_id = tracking_metadata.get('raw_content_id')
        
        # Build comprehensive response
        response = {
            "success": result.get('success', False),
            "document_name": Path(document_path).name,
            "document_path": document_path,
            "processing_decision": result.get('decision', 'UNKNOWN'),
            "products_found": result.get('products_found', 0),
            "extraction_confidence": result.get('confidence_score', 0.0),
            "processing_time_ms": processing_time,
            "letter_id": result.get('letter_id'),
            "from_cache": result.get('from_cache', False),
            "extracted_ranges": [],  # Will be populated from database if needed
            # Enhanced token tracking data
            "token_tracking": {
                "call_id": call_id,
                "token_usage": token_usage,
                "raw_content_id": raw_content_id,
                "prompt_version": "2.2.0"  # From our prompts.yaml
            },
            "api_processing_time": int(time.time() * 1000)
        }
        
        # Add error information if processing failed
        if not result.get('success', False):
            response["error"] = result.get('error', 'Processing failed')
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Pipeline processing failed: {str(e)}",
            "document_name": Path(document_path).name,
            "document_path": document_path,
            "processing_time_ms": 0,
            "api_processing_time": int(time.time() * 1000)
        }


def main():
    """Main entry point for the production pipeline runner."""
    parser = argparse.ArgumentParser(
        description="SE Letters Production Pipeline Runner with Enhanced Token Tracking"
    )
    parser.add_argument(
        "document_path", 
        help="Path to the document to process"
    )
    parser.add_argument(
        "--force-reprocess", 
        action="store_true",
        help="Force reprocessing even if document was already processed"
    )
    parser.add_argument(
        "--json-output", 
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Validate document path
    document_path = Path(args.document_path)
    if not document_path.exists():
        print(json.dumps({
            "success": False,
            "error": f"Document not found: {document_path}",
            "document_path": str(document_path)
        }))
        sys.exit(1)
    
    # Process the document
    result = process_document_with_tracking(
        str(document_path), 
        force_reprocess=args.force_reprocess
    )
    
    # Output results
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        if result["success"]:
            print(f"✅ Processing completed successfully")
            print(f"📄 Document: {result['document_name']}")
            print(f"📋 Decision: {result['processing_decision']}")
            print(f"📦 Products found: {result['products_found']}")
            print(f"🎯 Confidence: {result['extraction_confidence']:.3f}")
            print(f"⏱️ Processing time: {result['processing_time_ms']:.2f}ms")
            
            if result.get("token_tracking", {}).get("token_usage"):
                usage = result["token_tracking"]["token_usage"]
                print(f"🪙 Token usage: {usage}")
            
            if result.get("extracted_ranges"):
                print(f"📊 Extracted ranges:")
                for i, range_info in enumerate(result["extracted_ranges"], 1):
                    print(f"  {i}. {range_info['range_name']} - {range_info['subrange_name']} ({range_info['confidence']:.3f})")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main() 