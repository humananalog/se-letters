#!/usr/bin/env python3
"""
Demo script for embedded image extraction from Word documents.

This script demonstrates the enhanced capabilities for extracting and processing
embedded images in Schneider Electric obsolescence letters, specifically targeting
modernization path tables and diagrams.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.services.enhanced_image_processor import EnhancedImageProcessor
from se_letters.services.document_processor import DocumentProcessor
from se_letters.core.config import get_config
from se_letters.utils.logger import get_logger

logger = get_logger(__name__)


def demo_image_extraction():
    """Demonstrate embedded image extraction capabilities."""
    
    print("🖼️  SE Letters - Embedded Image Extraction Demo")
    print("=" * 60)
    
    # Initialize processors
    try:
        config = get_config()
        image_processor = EnhancedImageProcessor()
        document_processor = DocumentProcessor(config)
        
        print("✅ Processors initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize processors: {e}")
        return
    
    # Demo capabilities
    print("\n🔍 CAPABILITIES OVERVIEW:")
    print("-" * 40)
    
    capabilities = [
        "📄 Extract embedded images from DOCX/DOC files",
        "🔍 OCR processing with specialized configurations",
        "📊 Table structure detection and parsing",
        "🔄 Modernization path extraction",
        "🎯 Product code mapping identification",
        "📈 Confidence scoring and quality assessment",
        "🖼️ Image enhancement for better OCR results",
        "🔗 Integration with document processing pipeline"
    ]
    
    for capability in capabilities:
        print(f"  {capability}")
    
    # Show processing methods
    print("\n⚙️  PROCESSING METHODS:")
    print("-" * 40)
    
    methods = {
        "Image Extraction": [
            "ZIP-based extraction from DOCX files",
            "Relationship-based extraction via python-docx",
            "Size filtering to exclude decorative images",
            "Format validation and conversion"
        ],
        "Image Enhancement": [
            "Contrast enhancement for better text visibility",
            "Noise reduction using OpenCV (if available)",
            "Adaptive thresholding for text detection",
            "Sharpening filters for clarity"
        ],
        "OCR Processing": [
            "Table-optimized OCR configuration",
            "Diagram-specific character recognition",
            "Confidence scoring per word/region",
            "Multiple language support"
        ],
        "Content Analysis": [
            "Modernization keyword detection",
            "Product code pattern matching",
            "Table structure recognition",
            "Replacement mapping extraction"
        ]
    }
    
    for method_type, method_list in methods.items():
        print(f"\n  📋 {method_type}:")
        for method in method_list:
            print(f"    • {method}")
    
    # Show example patterns
    print("\n🎯 DETECTION PATTERNS:")
    print("-" * 40)
    
    patterns = {
        "Product Mappings": [
            "LC1D09 → LC1D09BD (Direct replacement)",
            "LC1D09 replaced by LC1D09BD",
            "Old: LC1D09 New: LC1D09BD",
            "LC1D09 | LC1D09BD (Table format)"
        ],
        "Table Types": [
            "Replacement tables (obsolete → new)",
            "Modernization tables (upgrade paths)",
            "Product catalog tables (specifications)",
            "General information tables"
        ],
        "Modernization Paths": [
            "TeSys D → TeSys F → TeSys GV4 (Multi-step)",
            "PIX Compact → PIX-DC (Single-step)",
            "Migration from Galaxy 3000 to Galaxy 6000"
        ]
    }
    
    for pattern_type, pattern_list in patterns.items():
        print(f"\n  🔍 {pattern_type}:")
        for pattern in pattern_list:
            print(f"    • {pattern}")
    
    # Show expected results
    print("\n📊 EXPECTED RESULTS:")
    print("-" * 40)
    
    result_example = {
        "total_images": 5,
        "processed_images": 5,
        "modernization_content": [
            {
                "product_mappings": [
                    {"obsolete_code": "LC1D09", "replacement_code": "LC1D09BD", "mapping_type": "direct_replacement"},
                    {"obsolete_code": "LC1D12", "replacement_code": "LC1D12BD", "mapping_type": "direct_replacement"}
                ],
                "replacement_tables": [
                    {
                        "type": "replacement_table",
                        "headers": ["Obsolete Part", "Replacement Part", "Notes"],
                        "rows": [
                            {"Obsolete Part": "LC1D09", "Replacement Part": "LC1D09BD", "Notes": "Direct replacement"},
                            {"Obsolete Part": "LC1D12", "Replacement Part": "LC1D12BD", "Notes": "Direct replacement"}
                        ],
                        "row_count": 2,
                        "column_count": 3
                    }
                ],
                "modernization_paths": [
                    {
                        "type": "single_step",
                        "from": "TeSys D",
                        "to": "TeSys F",
                        "description": "Migration path: TeSys D → TeSys F"
                    }
                ]
            }
        ]
    }
    
    print(json.dumps(result_example, indent=2))
    
    # Show integration benefits
    print("\n🚀 INTEGRATION BENEFITS:")
    print("-" * 40)
    
    benefits = [
        "📈 Dramatically improved extraction accuracy for table-based content",
        "🎯 Specialized handling of Schneider Electric product documentation",
        "🔄 Seamless integration with existing document processing pipeline",
        "📊 Comprehensive metadata extraction for business intelligence",
        "🛡️ Robust error handling with graceful degradation",
        "⚡ Efficient processing with configurable quality settings",
        "🔍 Debug capabilities for troubleshooting and optimization",
        "📋 Structured output ready for downstream processing"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    # Show usage example
    print("\n💻 USAGE EXAMPLE:")
    print("-" * 40)
    
    usage_code = '''
# Basic usage
from se_letters.services.enhanced_image_processor import EnhancedImageProcessor

processor = EnhancedImageProcessor()
results = processor.extract_embedded_images(document_path)

# Check results
if results["processed_images"] > 0:
    print(f"Processed {results['processed_images']} images")
    print(f"Found {len(results['modernization_content'])} with modernization content")
    
    # Get summary
    summary = processor.create_modernization_summary(results)
    print(f"Total product mappings: {len(summary['all_product_mappings'])}")
    print(f"Total replacement tables: {len(summary['all_replacement_tables'])}")
    print(f"Extraction quality: {summary['extraction_quality']}")

# Integrated usage (automatic with DocumentProcessor)
from se_letters.services.document_processor import DocumentProcessor
from se_letters.core.config import get_config

config = get_config()
processor = DocumentProcessor(config)
document = processor.process_document(document_path)

# Enhanced text will include image-extracted content
if document and "image_enhanced" in document.metadata:
    print("Document enhanced with embedded image content!")
    modernization_summary = document.metadata["modernization_summary"]
    print(f"Found {len(modernization_summary['all_product_mappings'])} product mappings")
'''
    
    print(usage_code)
    
    # Show requirements
    print("\n📋 REQUIREMENTS:")
    print("-" * 40)
    
    requirements = {
        "Core Dependencies": [
            "python-docx (DOCX file handling)",
            "Pillow (Image processing)",
            "pytesseract (OCR engine)",
            "Tesseract OCR (System dependency)"
        ],
        "Optional Dependencies": [
            "OpenCV (Advanced image enhancement)",
            "numpy (Image array processing)"
        ],
        "System Requirements": [
            "Tesseract OCR installed and in PATH",
            "Sufficient RAM for image processing (2GB+ recommended)",
            "Disk space for temporary image files"
        ]
    }
    
    for req_type, req_list in requirements.items():
        print(f"\n  📦 {req_type}:")
        for req in req_list:
            print(f"    • {req}")
    
    print("\n✨ DEMO COMPLETE!")
    print("=" * 60)
    print("The enhanced image processor is ready to extract modernization")
    print("path tables and diagrams from Schneider Electric obsolescence letters!")
    print("\nTo test with real documents, use the integrated DocumentProcessor")
    print("which will automatically process embedded images when available.")


if __name__ == "__main__":
    demo_image_extraction() 