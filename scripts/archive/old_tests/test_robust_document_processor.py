#!/usr/bin/env python3
"""
Test script for Robust Document Processor
Validates enhanced DOC file processing capabilities
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.se_letters.services.robust_document_processor import (
    RobustDocumentProcessor,
    DocumentResult
)

def test_robust_document_processor():
    """Test the robust document processor with various file types"""
    print("🔧 ROBUST DOCUMENT PROCESSOR - VALIDATION TEST")
    print("=" * 80)
    print("Testing enhanced DOC file processing with comprehensive fallback chain")
    print()
    
    # Initialize processor
    processor = RobustDocumentProcessor()
    
    # Find test documents
    docs_dir = Path("data/input/letters")
    test_files = []
    
    # Find various file types
    for pattern in ["*.doc", "*.docx", "*.pdf"]:
        test_files.extend(docs_dir.glob(pattern))
        test_files.extend(docs_dir.glob(f"*/{pattern}"))
        test_files.extend(docs_dir.glob(f"*/*/{pattern}"))
    
    if not test_files:
        print("❌ No test documents found")
        return
    
    # Test up to 5 documents
    selected_files = test_files[:5]
    print(f"📄 Testing {len(selected_files)} documents:")
    for i, file_path in enumerate(selected_files, 1):
        print(f"  {i}. {file_path.name} ({file_path.suffix.upper()})")
    print()
    
    results = []
    total_start_time = time.time()
    
    for i, file_path in enumerate(selected_files, 1):
        print(f"🔄 Processing Document {i}/{len(selected_files)}: {file_path.name}")
        print("-" * 60)
        
        try:
            # Process document
            result = processor.process_document(file_path)
            results.append(result)
            
            # Display results
            print(f"✅ Success: {result.success}")
            print(f"📄 Content Length: {len(result.content):,} characters")
            print(f"🔧 Extraction Method: {result.extraction_method}")
            print(f"⏱️  Processing Time: {result.processing_time:.2f}s")
            print(f"📁 File Size: {result.file_size:,} bytes")
            print(f"🖼️  Preview Images: {len(result.preview_images)}")
            
            if result.errors:
                print(f"❌ Errors ({len(result.errors)}):")
                for error in result.errors:
                    print(f"   - {error}")
            
            if result.warnings:
                print(f"⚠️  Warnings ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"   - {warning}")
            
            # Show content preview
            if result.content:
                preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                print(f"📝 Content Preview:")
                print(f"   {preview}")
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            results.append(DocumentResult(
                file_path=file_path,
                success=False,
                errors=[str(e)]
            ))
        
        print()
    
    # Summary statistics
    total_time = time.time() - total_start_time
    successful = len([r for r in results if r.success])
    failed = len(results) - successful
    
    print("📊 PROCESSING SUMMARY")
    print("=" * 40)
    print(f"📄 Total Documents: {len(results)}")
    print(f"✅ Successful: {successful} ({successful/len(results)*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/len(results)*100:.1f}%)")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"📈 Average Time: {total_time/len(results):.2f}s per document")
    
    # Method breakdown
    methods = {}
    for result in results:
        if result.success:
            method = result.extraction_method
            methods[method] = methods.get(method, 0) + 1
    
    if methods:
        print(f"\n🔧 EXTRACTION METHODS USED:")
        for method, count in methods.items():
            print(f"   - {method}: {count} documents")
    
    # File type breakdown
    file_types = {}
    for result in results:
        ext = result.file_path.suffix.lower()
        if result.success:
            file_types[ext] = file_types.get(ext, [0, 0])
            file_types[ext][0] += 1
        else:
            file_types[ext] = file_types.get(ext, [0, 0])
            file_types[ext][1] += 1
    
    if file_types:
        print(f"\n📁 FILE TYPE BREAKDOWN:")
        for ext, (success, failed) in file_types.items():
            total = success + failed
            success_rate = success / total * 100 if total > 0 else 0
            print(f"   - {ext.upper()}: {success}/{total} successful ({success_rate:.1f}%)")
    
    # Quality assessment
    print(f"\n🎯 QUALITY ASSESSMENT:")
    
    # Check if we achieved target success rate
    success_rate = successful / len(results) * 100
    if success_rate >= 95:
        print(f"🏆 EXCELLENT: {success_rate:.1f}% success rate (Target: 95%+)")
    elif success_rate >= 80:
        print(f"✅ GOOD: {success_rate:.1f}% success rate (Target: 95%+)")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% success rate (Target: 95%+)")
    
    # Check processing time
    avg_time = total_time / len(results)
    if avg_time <= 30:
        print(f"🏆 EXCELLENT: {avg_time:.1f}s average processing time (Target: <30s)")
    elif avg_time <= 60:
        print(f"✅ GOOD: {avg_time:.1f}s average processing time (Target: <30s)")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: {avg_time:.1f}s average processing time (Target: <30s)")
    
    # Check preview generation
    preview_success = len([r for r in results if r.preview_images])
    preview_rate = preview_success / len(results) * 100
    if preview_rate >= 80:
        print(f"🏆 EXCELLENT: {preview_rate:.1f}% preview generation rate")
    elif preview_rate >= 50:
        print(f"✅ GOOD: {preview_rate:.1f}% preview generation rate")
    else:
        print(f"⚠️  NEEDS IMPROVEMENT: {preview_rate:.1f}% preview generation rate")
    
    print(f"\n🔧 RECOMMENDATIONS:")
    
    # Analyze failures
    doc_failures = [r for r in results if not r.success and r.file_path.suffix.lower() == '.doc']
    if doc_failures:
        print(f"- Install LibreOffice for better DOC file support")
        print(f"- Consider installing antiword: brew install antiword")
        print(f"- Consider installing textract: pip install textract")
    
    pdf_failures = [r for r in results if not r.success and r.file_path.suffix.lower() == '.pdf']
    if pdf_failures:
        print(f"- Install additional PDF libraries: pip install pdfplumber")
        print(f"- Consider OCR for scanned PDFs: pip install pytesseract pdf2image")
    
    if preview_rate < 80:
        print(f"- Install pdf2image for better preview generation: pip install pdf2image")
        print(f"- Ensure LibreOffice is installed for DOC/DOCX previews")
    
    # Cleanup
    processor.cleanup()
    
    print(f"\n✅ Robust Document Processor validation complete!")
    
    return results

def analyze_extraction_methods():
    """Analyze which extraction methods are available"""
    print("\n🔍 EXTRACTION METHODS AVAILABILITY")
    print("=" * 50)
    
    # Check PDF methods
    print("📄 PDF Extraction Methods:")
    try:
        import fitz
        print("  ✅ PyMuPDF (fitz) - Available")
    except ImportError:
        print("  ❌ PyMuPDF (fitz) - Not available")
    
    try:
        import pdfplumber
        print("  ✅ pdfplumber - Available")
    except ImportError:
        print("  ❌ pdfplumber - Not available")
    
    try:
        import PyPDF2
        print("  ✅ PyPDF2 - Available")
    except ImportError:
        print("  ❌ PyPDF2 - Not available")
    
    # Check DOCX methods
    print("\n📄 DOCX Extraction Methods:")
    try:
        import docx
        print("  ✅ python-docx - Available")
    except ImportError:
        print("  ❌ python-docx - Not available")
    
    # Check DOC methods
    print("\n📄 DOC Extraction Methods:")
    try:
        import subprocess
        result = subprocess.run(['libreoffice', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✅ LibreOffice - Available")
        else:
            print("  ❌ LibreOffice - Not working")
    except:
        print("  ❌ LibreOffice - Not available")
    
    try:
        import subprocess
        result = subprocess.run(['antiword', '-v'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✅ antiword - Available")
        else:
            print("  ❌ antiword - Not working")
    except:
        print("  ❌ antiword - Not available")
    
    try:
        import textract
        print("  ✅ textract - Available")
    except ImportError:
        print("  ❌ textract - Not available")
    
    # Check OCR methods
    print("\n🔍 OCR Methods:")
    try:
        import pytesseract
        print("  ✅ pytesseract - Available")
    except ImportError:
        print("  ❌ pytesseract - Not available")
    
    try:
        from pdf2image import convert_from_path
        print("  ✅ pdf2image - Available")
    except ImportError:
        print("  ❌ pdf2image - Not available")

if __name__ == "__main__":
    try:
        # Analyze available methods
        analyze_extraction_methods()
        
        # Run validation test
        results = test_robust_document_processor()
        
        # Exit with appropriate code
        successful = len([r for r in results if r.success])
        success_rate = successful / len(results) * 100 if results else 0
        
        if success_rate >= 95:
            print(f"\n🎉 SUCCESS: Achieved {success_rate:.1f}% success rate!")
            sys.exit(0)
        else:
            print(f"\n⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% success rate (Target: 95%+)")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1) 