#!/usr/bin/env python3
"""
Setup script for SE Letters environment configuration.
"""

import os
import sys
from pathlib import Path


def setup_api_key():
    """Interactive setup for XAI API key."""
    print("🔑 XAI API Key Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("💡 Run: cp config/env.example .env")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Check if API key is already set
    if "XAI_API_KEY=your_xai_api_key_here" not in content:
        print("✅ API key appears to be already configured!")
        
        # Extract and show partial key
        for line in content.split('\n'):
            if line.startswith('XAI_API_KEY=') and not line.endswith('your_xai_api_key_here'):
                key_value = line.split('=', 1)[1]
                if len(key_value) > 10:
                    print(f"🔑 Current key: {key_value[:10]}...")
                break
        
        choice = input("\n🔄 Do you want to update it? (y/N): ").lower()
        if choice != 'y':
            return True
    
    # Get API key from user
    print("\n📝 Please enter your XAI API key:")
    print("   Get it from: https://console.x.ai/")
    print("   Format: xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    
    api_key = input("\n🔑 XAI API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        return False
    
    if not api_key.startswith('xai-'):
        print("⚠️  Warning: API key should start with 'xai-'")
        choice = input("   Continue anyway? (y/N): ").lower()
        if choice != 'y':
            return False
    
    # Update .env file
    updated_content = content.replace(
        "XAI_API_KEY=your_xai_api_key_here",
        f"XAI_API_KEY={api_key}"
    )
    
    with open(env_file, 'w') as f:
        f.write(updated_content)
    
    print("✅ API key saved to .env file!")
    return True


def test_configuration():
    """Test if the configuration is working."""
    print("\n🧪 Testing Configuration")
    print("=" * 40)
    
    try:
        # Test environment loading
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('XAI_API_KEY')
        if not api_key or api_key == 'your_xai_api_key_here':
            print("❌ XAI_API_KEY not properly configured")
            return False
        
        print(f"✅ XAI_API_KEY loaded: {api_key[:10]}...")
        
        # Test basic imports
        try:
            import pandas as pd
            print("✅ pandas imported successfully")
        except ImportError:
            print("❌ pandas not installed")
            return False
        
        try:
            import fitz
            print("✅ PyMuPDF imported successfully")
        except ImportError:
            print("❌ PyMuPDF not installed")
            return False
        
        # Test file paths
        excel_file = Path("data/input/letters/IBcatalogue.xlsx")
        if excel_file.exists():
            print(f"✅ IBcatalogue.xlsx found ({excel_file.stat().st_size / (1024*1024):.1f} MB)")
        else:
            print("❌ IBcatalogue.xlsx not found")
            return False
        
        letter_file = Path("data/input/letters/PSIBS_MODERNIZATION/07_ PWP communication letters & SLA/20170608_PIX-DC - Phase out_communication_letter-Rev00.doc")
        if letter_file.exists():
            print(f"✅ PIX-DC letter found ({letter_file.stat().st_size / 1024:.1f} KB)")
        else:
            print("❌ PIX-DC letter not found")
            return False
        
        print("\n🎉 Configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 SE Letters Environment Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/se_letters").exists():
        print("❌ Please run this script from the project root directory")
        print("   Current directory:", os.getcwd())
        return 1
    
    # Setup API key
    if not setup_api_key():
        print("\n❌ API key setup failed!")
        return 1
    
    # Test configuration
    if not test_configuration():
        print("\n❌ Configuration test failed!")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n🚀 Next steps:")
    print("   1. Run: python scripts/simple_test.py")
    print("   2. Run: python scripts/test_ibcatalogue.py")
    print("   3. Run: python scripts/run_pipeline.py")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 