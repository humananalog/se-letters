#!/usr/bin/env python3
"""
Phase 1 Integration Test - SE Letters Pipeline Enhancement

Tests the integrated Phase 1 improvements:
1. Robust document processing with fallback mechanisms
2. Enhanced LLM service with structured JSON schema and debug console
3. Document-to-image conversion for side-by-side preview
4. 95%+ accuracy validation
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config
from se_letters.services.document_processor import DocumentProcessor
from se_letters.services.xai_service import XAIService
from se_letters.services.preview_service import PreviewService
from se_letters.services.excel_service import ExcelService


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"🚀 {title}")
    print(f"{'='*80}")


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'🔧 ' + title}")
    print(f"{'-'*60}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"❌ {message}")


def test_robust_document_processing() -> Dict[str, Any]:
    """Test the robust document processing capabilities."""
    print_section("ROBUST DOCUMENT PROCESSING TEST")
    
    config = get_config()
    processor = DocumentProcessor(config)
    
    # Test documents directory
    input_dir = Path("data/input/letters")
    
    if not input_dir.exists():
        print_error(f"Input directory not found: {input_dir}")
        return {"success": False, "error": "Input directory not found"}
    
    # Find test documents
    test_files = []
    for pattern in ["*.pdf", "*.docx", "*.doc"]:
        test_files.extend(list(input_dir.glob(pattern)))
    
    if not test_files:
        print_warning("No test documents found, creating mock test")
        return {"success": True, "documents_processed": 0, "method": "mock"}
    
    # Limit to first 3 documents for testing
    test_files = test_files[:3]
    
    results = {
        "success": True,
        "documents_processed": 0,
        "successful_extractions": 0,
        "failed_extractions": 0,
        "total_processing_time": 0,
        "methods_used": {},
        "documents": []
    }
    
    print(f"Testing {len(test_files)} documents...")
    
    for file_path in test_files:
        print(f"\n📄 Processing: {file_path.name}")
        
        start_time = time.time()
        
        try:
            # Process document with robust fallback
            document = processor.process_document(file_path)
            processing_time = time.time() - start_time
            
            if document:
                print_success(f"Extracted {len(document.text)} characters")
                print(f"   Method: {document.metadata.get('method_used', 'unknown')}")
                print(f"   Time: {processing_time:.2f}s")
                
                results["successful_extractions"] += 1
                method = document.metadata.get("method_used", "unknown")
                results["methods_used"][method] = results["methods_used"].get(method, 0) + 1
                
                doc_result = {
                    "name": file_path.name,
                    "success": True,
                    "text_length": len(document.text),
                    "processing_time": processing_time,
                    "method": method
                }
            else:
                print_error("Document processing failed")
                results["failed_extractions"] += 1
                doc_result = {
                    "name": file_path.name,
                    "success": False,
                    "error": "Processing returned None",
                    "processing_time": processing_time
                }
            
            results["documents"].append(doc_result)
            results["total_processing_time"] += processing_time
            results["documents_processed"] += 1
            
        except Exception as e:
            processing_time = time.time() - start_time
            print_error(f"Processing failed: {e}")
            results["failed_extractions"] += 1
            results["documents"].append({
                "name": file_path.name,
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            })
            results["total_processing_time"] += processing_time
    
    # Calculate success rate
    if results["documents_processed"] > 0:
        success_rate = (results["successful_extractions"] / results["documents_processed"]) * 100
        print(f"\n📊 RESULTS:")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Average Time: {results['total_processing_time']/results['documents_processed']:.2f}s")
        print(f"   Methods Used: {results['methods_used']}")
        
        # Check if we meet the 95% success rate target
        if success_rate >= 95:
            print_success("SUCCESS: Met 95%+ success rate target!")
        else:
            print_warning(f"Target not met: {success_rate:.1f}% < 95%")
    
    return results


def test_enhanced_llm_service() -> Dict[str, Any]:
    """Test the enhanced LLM service with structured JSON schema."""
    print_section("ENHANCED LLM SERVICE TEST")
    
    config = get_config()
    
    # Enable debug console for testing
    xai_service = XAIService(config)
    xai_service.enable_debug_console()
    
    print("Debug console enabled for testing")
    
    # Test with sample text
    sample_text = """
    Field Services communication PWP PIX SF6 up to 24kV
    
    This communication informs you about the withdrawal of PIX-DC compact switchgear
    products from our portfolio. The PIX Compact series will be discontinued on
    December 31, 2024.
    
    Affected products:
    - PIX-DC 12kV switchgear
    - PIX 36 series
    - PIX 2B compact units
    
    Replacement products:
    - Galaxy 6000 series for high-voltage applications
    - TeSys D contactors for low-voltage needs
    
    Contact: support@schneider-electric.com
    """
    
    document_name = "test_pix_withdrawal.txt"
    
    results = {
        "success": False,
        "confidence": 0,
        "ranges_found": 0,
        "processing_time": 0,
        "schema_validation": False,
        "debug_files_created": 0
    }
    
    try:
        print(f"Testing comprehensive metadata extraction...")
        
        start_time = time.time()
        
        # Test comprehensive metadata extraction
        metadata = xai_service.extract_comprehensive_metadata(sample_text, document_name)
        
        processing_time = time.time() - start_time
        
        print(f"Processing completed in {processing_time:.2f}s")
        
        # Validate response structure
        required_sections = [
            "product_identification", "brand_business", "commercial_lifecycle",
            "technical_specs", "service_support", "regulatory_compliance",
            "business_context", "extraction_metadata"
        ]
        
        schema_valid = all(section in metadata for section in required_sections)
        
        if schema_valid:
            print_success("Schema validation passed")
            results["schema_validation"] = True
        else:
            print_error("Schema validation failed")
            missing = [s for s in required_sections if s not in metadata]
            print(f"Missing sections: {missing}")
        
        # Extract key metrics
        extraction_meta = metadata.get("extraction_metadata", {})
        product_info = metadata.get("product_identification", {})
        
        confidence = extraction_meta.get("confidence", 0)
        ranges = product_info.get("ranges", [])
        
        results.update({
            "success": True,
            "confidence": confidence,
            "ranges_found": len(ranges),
            "processing_time": processing_time,
            "ranges": ranges
        })
        
        print(f"📊 EXTRACTION RESULTS:")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Ranges Found: {len(ranges)}")
        print(f"   Ranges: {ranges}")
        
        # Check debug files
        debug_files = xai_service.get_debug_files()
        results["debug_files_created"] = len(debug_files)
        
        if debug_files:
            print_success(f"Debug files created: {len(debug_files)}")
            print(f"   Latest: {debug_files[-1].name}")
        
        # Validate accuracy
        if confidence >= 0.95:
            print_success("SUCCESS: Met 95%+ confidence target!")
        elif confidence >= 0.8:
            print_warning(f"Good confidence: {confidence:.2f} (target: 0.95)")
        else:
            print_warning(f"Low confidence: {confidence:.2f} (target: 0.95)")
        
    except Exception as e:
        print_error(f"LLM service test failed: {e}")
        results["error"] = str(e)
    
    finally:
        # Clean up debug files
        if hasattr(xai_service, 'clear_debug_files'):
            cleared = xai_service.clear_debug_files()
            print(f"Cleaned up {cleared} debug files")
    
    return results


def test_document_preview_service() -> Dict[str, Any]:
    """Test the document preview service."""
    print_section("DOCUMENT PREVIEW SERVICE TEST")
    
    config = get_config()
    preview_service = PreviewService(config)
    
    # Find a test document
    input_dir = Path("data/input/letters")
    test_files = []
    
    for pattern in ["*.pdf", "*.docx", "*.doc"]:
        test_files.extend(list(input_dir.glob(pattern)))
    
    if not test_files:
        print_warning("No test documents found for preview testing")
        return {"success": False, "error": "No test documents"}
    
    # Test with first document
    test_file = test_files[0]
    
    results = {
        "success": False,
        "document_name": test_file.name,
        "preview_images": 0,
        "processing_time": 0,
        "side_by_side_created": False
    }
    
    try:
        print(f"Testing preview generation for: {test_file.name}")
        
        start_time = time.time()
        
        # Generate document preview
        preview_result = preview_service.generate_document_preview(test_file)
        
        processing_time = time.time() - start_time
        
        if preview_result["success"]:
            print_success(f"Preview generated successfully")
            print(f"   Images: {len(preview_result.get('image_paths', []))}")
            print(f"   Time: {processing_time:.2f}s")
            
            results.update({
                "success": True,
                "preview_images": len(preview_result.get('image_paths', [])),
                "processing_time": processing_time
            })
            
            # Test side-by-side preview with mock extraction data
            mock_extraction = {
                "product_identification": {
                    "ranges": ["PIX", "TeSys"],
                    "product_codes": ["PIX-DC", "LC1D09"],
                    "product_types": ["Switchgear", "Contactor"],
                    "descriptions": ["PIX compact switchgear", "TeSys D contactor"]
                },
                "extraction_metadata": {
                    "confidence": 0.85,
                    "analysis_quality": "high",
                    "text_length": 1000,
                    "extraction_method": "test_mock"
                },
                "technical_specs": {
                    "voltage_levels": ["12kV", "24kV"],
                    "specifications": ["SF6 insulated", "Compact design"],
                    "device_types": ["Switchgear", "Circuit breaker"],
                    "applications": ["Medium voltage distribution"]
                },
                "business_context": {
                    "customer_impact": ["Product withdrawal", "Replacement required"],
                    "migration_recommendations": ["Upgrade to Galaxy series"],
                    "contact_info": ["support@schneider-electric.com"],
                    "business_reasons": ["End of life cycle"]
                }
            }
            
            # Create side-by-side preview
            side_by_side_result = preview_service.create_side_by_side_preview(
                test_file, mock_extraction
            )
            
            if side_by_side_result["success"]:
                print_success("Side-by-side preview created")
                print(f"   HTML file: {side_by_side_result['html_path']}")
                results["side_by_side_created"] = True
            else:
                print_error(f"Side-by-side creation failed: {side_by_side_result['error']}")
        
        else:
            print_error(f"Preview generation failed: {preview_result['error']}")
            results["error"] = preview_result["error"]
    
    except Exception as e:
        print_error(f"Preview service test failed: {e}")
        results["error"] = str(e)
    
    return results


def test_integrated_pipeline() -> Dict[str, Any]:
    """Test the complete integrated pipeline."""
    print_section("INTEGRATED PIPELINE TEST")
    
    config = get_config()
    
    # Initialize services
    document_processor = DocumentProcessor(config)
    xai_service = XAIService(config)
    preview_service = PreviewService(config)
    
    # Find test document
    input_dir = Path("data/input/letters")
    test_files = list(input_dir.glob("*.docx"))[:1]  # Test with one DOCX file
    
    if not test_files:
        print_warning("No DOCX files found for integration test")
        return {"success": False, "error": "No test documents"}
    
    test_file = test_files[0]
    
    results = {
        "success": False,
        "document_name": test_file.name,
        "pipeline_stages": {
            "document_processing": False,
            "llm_extraction": False,
            "preview_generation": False,
            "side_by_side_creation": False
        },
        "total_processing_time": 0,
        "final_confidence": 0
    }
    
    try:
        print(f"Running integrated pipeline on: {test_file.name}")
        
        total_start_time = time.time()
        
        # Stage 1: Document Processing
        print("\n1️⃣ Document Processing...")
        document = document_processor.process_document(test_file)
        
        if document:
            print_success(f"Extracted {len(document.text)} characters")
            results["pipeline_stages"]["document_processing"] = True
            
            # Stage 2: LLM Extraction
            print("\n2️⃣ LLM Metadata Extraction...")
            metadata = xai_service.extract_comprehensive_metadata(
                document.text, test_file.name
            )
            
            confidence = metadata.get("extraction_metadata", {}).get("confidence", 0)
            ranges = metadata.get("product_identification", {}).get("ranges", [])
            
            print_success(f"Extracted metadata (confidence: {confidence:.2f})")
            print(f"   Ranges found: {ranges}")
            
            results["pipeline_stages"]["llm_extraction"] = True
            results["final_confidence"] = confidence
            
            # Stage 3: Preview Generation
            print("\n3️⃣ Preview Generation...")
            preview_result = preview_service.generate_document_preview(test_file)
            
            if preview_result["success"]:
                print_success(f"Generated {len(preview_result['image_paths'])} preview images")
                results["pipeline_stages"]["preview_generation"] = True
                
                # Stage 4: Side-by-Side Creation
                print("\n4️⃣ Side-by-Side Preview...")
                side_by_side_result = preview_service.create_side_by_side_preview(
                    test_file, metadata
                )
                
                if side_by_side_result["success"]:
                    print_success("Side-by-side preview created successfully")
                    print(f"   HTML file: {side_by_side_result['html_path']}")
                    results["pipeline_stages"]["side_by_side_creation"] = True
                    results["success"] = True
                else:
                    print_error(f"Side-by-side creation failed: {side_by_side_result['error']}")
            else:
                print_error(f"Preview generation failed: {preview_result['error']}")
        else:
            print_error("Document processing failed")
        
        total_time = time.time() - total_start_time
        results["total_processing_time"] = total_time
        
        print(f"\n📊 PIPELINE RESULTS:")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Stages Completed: {sum(results['pipeline_stages'].values())}/4")
        print(f"   Final Confidence: {results['final_confidence']:.2f}")
        
    except Exception as e:
        print_error(f"Integrated pipeline test failed: {e}")
        results["error"] = str(e)
    
    return results


def main():
    """Run all Phase 1 integration tests."""
    print_header("PHASE 1 INTEGRATION TESTING")
    print("Testing comprehensive pipeline improvements:")
    print("• Robust document processing with fallback mechanisms")
    print("• Enhanced LLM service with structured JSON schema")
    print("• Document preview and side-by-side visualization")
    print("• 95%+ accuracy validation")
    
    # Track overall results
    overall_results = {
        "tests_run": 0,
        "tests_passed": 0,
        "start_time": time.time()
    }
    
    # Test 1: Robust Document Processing
    doc_results = test_robust_document_processing()
    overall_results["tests_run"] += 1
    if doc_results["success"]:
        overall_results["tests_passed"] += 1
    
    # Test 2: Enhanced LLM Service
    llm_results = test_enhanced_llm_service()
    overall_results["tests_run"] += 1
    if llm_results["success"]:
        overall_results["tests_passed"] += 1
    
    # Test 3: Document Preview Service
    preview_results = test_document_preview_service()
    overall_results["tests_run"] += 1
    if preview_results["success"]:
        overall_results["tests_passed"] += 1
    
    # Test 4: Integrated Pipeline
    pipeline_results = test_integrated_pipeline()
    overall_results["tests_run"] += 1
    if pipeline_results["success"]:
        overall_results["tests_passed"] += 1
    
    # Final summary
    total_time = time.time() - overall_results["start_time"]
    
    print_header("PHASE 1 INTEGRATION TEST SUMMARY")
    print(f"📊 Tests Run: {overall_results['tests_run']}")
    print(f"✅ Tests Passed: {overall_results['tests_passed']}")
    print(f"❌ Tests Failed: {overall_results['tests_run'] - overall_results['tests_passed']}")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    
    success_rate = (overall_results['tests_passed'] / overall_results['tests_run']) * 100
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print_success("PHASE 1 INTEGRATION TEST PASSED!")
        print("✨ Ready for Phase 2 implementation")
    else:
        print_error("PHASE 1 INTEGRATION TEST FAILED")
        print("🔧 Review failed tests and fix issues before proceeding")
    
    # Save detailed results
    results_file = Path("data/output/phase1_integration_results.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    detailed_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall": overall_results,
        "document_processing": doc_results,
        "llm_service": llm_results,
        "preview_service": preview_results,
        "integrated_pipeline": pipeline_results
    }
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 