#!/usr/bin/env python3
"""
Debug script to check production pipeline output structure
"""

import json
import sys
from pathlib import Path
from dataclasses import asdict, is_dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from se_letters.services.production_pipeline_service import ProductionPipelineService


def convert_to_json_serializable(obj):
    """Convert dataclass objects to JSON-serializable format"""
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj


def main():
    """Test the pipeline output structure"""
    print("🔍 Testing Production Pipeline Output Structure")
    
    # Initialize the service
    service = ProductionPipelineService()
    
    # Test document
    test_document = Path("data/test/documents/PIX2B_Phase_out_Letter.pdf")
    
    if not test_document.exists():
        print(f"❌ Test document not found: {test_document}")
        return
    
    print(f"📄 Processing: {test_document.name}")
    
    # Process the document with force reprocess to get full pipeline output
    result = service.process_document(test_document, force_reprocess=True)
    
    # Print result structure
    print("\n📊 Processing Result Structure:")
    print(f"  Success: {result.success}")
    print(f"  Status: {result.status}")
    print(f"  Document ID: {result.document_id}")
    print(f"  Processing Time: {result.processing_time_ms:.2f}ms")
    print(f"  Confidence Score: {result.confidence_score}")
    
    # Check for product matching results
    if hasattr(result, 'product_matching_result') and result.product_matching_result:
        print(f"\n🧠 Product Matching Results:")
        pm_result = result.product_matching_result
        print(f"  Total Matches: {pm_result.get('total_matches', 0)}")
        print(f"  Range-based Matching: {pm_result.get('range_based_matching', False)}")
        print(f"  Processing Time: {pm_result.get('processing_time_ms', 0):.2f}ms")
        
        letter_info = pm_result.get('letter_product_info', {})
        print(f"  Letter Product: {letter_info.get('product_identifier', 'N/A')}")
        
        matching_products = pm_result.get('matching_products', [])
        if matching_products:
            print(f"  Matching Products:")
            for i, match in enumerate(matching_products, 1):
                print(f"    {i}. {match.get('product_identifier', 'N/A')} (confidence: {match.get('confidence', 0):.2f})")
    else:
        print(f"\n⚠️ No product matching results found")
    
    # Convert to JSON-like structure for API
    result_dict = {
        "success": result.success,
        "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
        "document_id": result.document_id,
        "processing_time_ms": result.processing_time_ms,
        "confidence_score": result.confidence_score,
        "error_message": getattr(result, 'error_message', None),
        "file_hash": getattr(result, 'file_hash', None),
        "file_size": getattr(result, 'file_size', None),
        "processed_at": getattr(result, 'processed_at', None)
    }
    
    # Add product matching results if available
    if hasattr(result, 'product_matching_result') and result.product_matching_result:
        pm_result = result.product_matching_result
        result_dict["product_matching_result"] = convert_to_json_serializable(pm_result)
    
    print(f"\n📋 JSON Output Structure:")
    print(json.dumps(result_dict, indent=2, default=str))


if __name__ == "__main__":
    main() 