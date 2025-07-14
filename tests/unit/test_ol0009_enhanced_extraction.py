#!/usr/bin/env python3
"""
Enhanced Test Script for OL0009.pdf - Complex French Obsolescence Letter
Tests the enhanced SOTA Grok service with comprehensive product extraction
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from se_letters.core.config import get_config
from se_letters.services.document_processor import DocumentProcessor
from se_letters.services.sota_grok_service import SOTAGrokService


def test_ol0009_enhanced_extraction():
    """Test enhanced extraction capabilities with OL0009.pdf"""
    
    # File paths
    ol0009_path = Path("/Users/alexandre/workshop/devApp/SE_letters/data/input/letters/PSIBS_MODERNIZATION/Obsolescence letters/OL0009.pdf")
    debug_dir = Path("data/test/debug/ol0009")
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Enhanced OL0009.pdf Extraction Test")
    print("=" * 50)
    print(f"📄 File: {ol0009_path}")
    print(f"📁 Debug output: {debug_dir}")
    
    if not ol0009_path.exists():
        print(f"❌ File not found: {ol0009_path}")
        return False
    
    # Initialize services
    config = get_config()
    grok_service = SOTAGrokService(config)
    
    print(f"📊 File size: {ol0009_path.stat().st_size / 1024:.1f} KB")
    
    # Test 1: Direct file extraction (bypassing OCR)
    print("\n🚀 Test 1: Direct File Extraction (Enhanced)")
    print("-" * 40)
    
    try:
        start_time = datetime.now()
        structured_data = grok_service.extract_structured_data_from_file(
            str(ol0009_path), 
            "OL0009.pdf"
        )
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Direct extraction completed in {processing_time:.2f}s")
        print(f"📦 Products extracted: {len(structured_data.products)}")
        print(f"🎯 Confidence: {structured_data.extraction_confidence:.2f}")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = debug_dir / f"direct_extraction_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {results_file}")
        
        # Analyze extracted data
        analyze_extraction_results(structured_data)
        
    except Exception as e:
        print(f"❌ Direct extraction failed: {e}")
        
        # Save error details
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = debug_dir / f"direct_extraction_error_{timestamp}.json"
        
        error_data = {
            "error": str(e),
            "error_type": type(e).__name__,
            "file_path": str(ol0009_path),
            "file_size": ol0009_path.stat().st_size,
            "processing_time": processing_time if 'processing_time' in locals() else 0
        }
        
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Error details saved to: {error_file}")
        return False
    
    # Test 2: OCR-based extraction for comparison
    print("\n🔄 Test 2: OCR-based Extraction (Comparison)")
    print("-" * 40)
    
    try:
        processor = DocumentProcessor(config)
        document = processor.process_document(ol0009_path)
        
        print(f"📝 OCR extracted text length: {len(document.text)} characters")
        
        start_time = datetime.now()
        ocr_structured_data = grok_service.extract_structured_data(
            document.text, 
            "OL0009.pdf"
        )
        end_time = datetime.now()
        ocr_processing_time = (end_time - start_time).total_seconds()
        
        print(f"✅ OCR extraction completed in {ocr_processing_time:.2f}s")
        print(f"📦 Products extracted: {len(ocr_structured_data.products)}")
        print(f"🎯 Confidence: {ocr_structured_data.extraction_confidence:.2f}")
        
        # Mark as OCR extraction
        for product in ocr_structured_data.products:
            product.extraction_method = "OCR-based Extraction"
        
        # Save OCR results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ocr_results_file = debug_dir / f"ocr_extraction_{timestamp}.json"
        
        with open(ocr_results_file, 'w', encoding='utf-8') as f:
            json.dump(ocr_structured_data.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"💾 OCR results saved to: {ocr_results_file}")
        
        # Compare results
        compare_extraction_methods(structured_data, ocr_structured_data)
        
    except Exception as e:
        print(f"❌ OCR extraction failed: {e}")
    
    print("\n🎉 Enhanced extraction test completed!")
    return True


def analyze_extraction_results(structured_data):
    """Analyze and display extraction results"""
    print("\n📊 Extraction Analysis")
    print("-" * 30)
    
    # Document metadata analysis
    metadata = structured_data.document_metadata
    print(f"📄 Document type: {metadata.document_type}")
    print(f"🌍 Language: {metadata.language}")
    print(f"📋 Document number: {metadata.document_number}")
    print(f"🏢 Business units: {len(metadata.business_units)}")
    print(f"🌎 Affected countries: {len(metadata.affected_countries)}")
    print(f"📅 Key dates: {len(metadata.key_dates)}")
    print(f"📊 Has tables: {metadata.has_tables}")
    print(f"🔧 Has technical specs: {metadata.has_technical_specs}")
    
    # Product analysis
    print(f"\n📦 Product Analysis ({len(structured_data.products)} products)")
    print("-" * 30)
    
    for i, product in enumerate(structured_data.products, 1):
        print(f"\n🔹 Product {i}: {product.product_identifier}")
        print(f"   Range: {product.range_label}")
        print(f"   Product Line: {product.product_line}")
        print(f"   Codification: {product.codification}")
        print(f"   Ref commerciale: {product.ref_commerciale}")
        print(f"   Ref technique: {product.ref_technique}")
        print(f"   Designation: {product.designation_constructeur}")
        print(f"   GTIN: {product.code_gtin}")
        print(f"   Voltage: {product.voltage_level}")
        print(f"   Current: {product.current_rating}")
        print(f"   Extraction method: {product.extraction_method}")
        print(f"   Confidence: {product.confidence_score:.2f}")
        
        if product.technical_specs:
            print(f"   Technical specs: {len(product.technical_specs)} items")
        if product.certifications:
            print(f"   Certifications: {len(product.certifications)} items")


def compare_extraction_methods(direct_data, ocr_data):
    """Compare direct file vs OCR extraction results"""
    print("\n🔄 Extraction Method Comparison")
    print("-" * 35)
    
    print(f"📦 Products - Direct: {len(direct_data.products)}, OCR: {len(ocr_data.products)}")
    print(f"🎯 Confidence - Direct: {direct_data.extraction_confidence:.2f}, OCR: {ocr_data.extraction_confidence:.2f}")
    
    # Analyze product details
    direct_with_codification = sum(1 for p in direct_data.products if p.codification)
    ocr_with_codification = sum(1 for p in ocr_data.products if p.codification)
    
    direct_with_gtin = sum(1 for p in direct_data.products if p.code_gtin)
    ocr_with_gtin = sum(1 for p in ocr_data.products if p.code_gtin)
    
    print(f"🏷️  Codification - Direct: {direct_with_codification}, OCR: {ocr_with_codification}")
    print(f"📊 GTIN codes - Direct: {direct_with_gtin}, OCR: {ocr_with_gtin}")
    
    # Document metadata comparison
    direct_dates = len(direct_data.document_metadata.key_dates)
    ocr_dates = len(ocr_data.document_metadata.key_dates)
    
    print(f"📅 Key dates - Direct: {direct_dates}, OCR: {ocr_dates}")


if __name__ == "__main__":
    success = test_ol0009_enhanced_extraction()
    sys.exit(0 if success else 1) 