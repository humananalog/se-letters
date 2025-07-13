#!/usr/bin/env python3
"""Simple test to verify Phase 1 services work correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all services can be imported."""
    try:
        from se_letters.core.config import get_config
        from se_letters.services.document_processor import DocumentProcessor
        from se_letters.services.preview_service import PreviewService
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from se_letters.core.config import get_config
        config = get_config()
        print(f"✅ Config loaded successfully")
        print(f"   API Base URL: {config.api.base_url}")
        print(f"   Model: {config.api.model}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_document_processor():
    """Test document processor initialization."""
    try:
        from se_letters.core.config import get_config
        from se_letters.services.document_processor import DocumentProcessor
        
        config = get_config()
        processor = DocumentProcessor(config)
        print("✅ Document processor initialized successfully")
        print(f"   Supported formats: {processor.supported_formats}")
        return True
    except Exception as e:
        print(f"❌ Document processor test failed: {e}")
        return False

def test_preview_service():
    """Test preview service initialization."""
    try:
        from se_letters.core.config import get_config
        from se_letters.services.preview_service import PreviewService
        
        config = get_config()
        preview_service = PreviewService(config)
        print("✅ Preview service initialized successfully")
        print(f"   Preview directory: {preview_service.preview_dir}")
        return True
    except Exception as e:
        print(f"❌ Preview service test failed: {e}")
        return False

def main():
    """Run simple service tests."""
    print("🚀 SIMPLE SERVICE TESTS")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Document Processor", test_document_processor),
        ("Preview Service", test_preview_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Testing {test_name}...")
        if test_func():
            passed += 1
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 