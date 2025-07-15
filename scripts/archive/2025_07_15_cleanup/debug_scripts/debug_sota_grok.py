#!/usr/bin/env python3
"""Debug script to test SOTA Grok service"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config
from se_letters.services.sota_grok_service import SOTAGrokService

def main():
    try:
        print("🔧 Debug: Testing SOTA Grok Service")
        
        # Load config
        config = get_config()
        print(f"✅ Config loaded: API Key: {config.api.api_key[:10]}...")
        
        # Initialize service
        service = SOTAGrokService(config)
        print(f"✅ Service initialized: Model: {service.model}")
        
        # Test document
        file_path = Path("data/test/documents/PIX2B_Phase_out_Letter.pdf")
        print(f"📄 Testing file: {file_path}")
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return
            
        # Process document
        print("🤖 Processing document...")
        result = service.process_raw_document(file_path)
        
        print(f"📊 Result keys: {list(result.keys())}")
        print(f"✅ Success: {result.get('success', False)}")
        
        if result.get('error'):
            print(f"❌ Error: {result.get('error')}")
            
        if result.get('extraction_confidence'):
            print(f"📈 Confidence: {result.get('extraction_confidence')}")
            
        # Close service
        service.close()
        
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 