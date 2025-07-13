#!/usr/bin/env python3
"""
Validate SE Letters configuration.
"""

import os
import sys
from pathlib import Path


def main():
    """Validate configuration."""
    print("🔍 SE Letters Configuration Validation")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    issues = []
    
    # Check API key
    api_key = os.getenv('XAI_API_KEY')
    if not api_key or api_key == 'your_xai_api_key_here':
        issues.append("❌ XAI_API_KEY not configured")
    else:
        print(f"✅ XAI_API_KEY: {api_key[:10]}...")
    
    # Check files
    files_to_check = [
        ("IBcatalogue.xlsx", "data/input/letters/IBcatalogue.xlsx"),
        ("PIX-DC letter", "data/input/letters/PSIBS_MODERNIZATION/07_ PWP communication letters & SLA/20170608_PIX-DC - Phase out_communication_letter-Rev00.doc"),
        ("Config file", "config/config.yaml"),
        ("Environment file", ".env")
    ]
    
    for name, path in files_to_check:
        if Path(path).exists():
            print(f"✅ {name}: {path}")
        else:
            issues.append(f"❌ {name} not found: {path}")
    
    # Check dependencies
    deps_to_check = [
        ("pandas", "pandas"),
        ("PyMuPDF", "fitz"),
        ("python-docx", "docx"),
        ("loguru", "loguru"),
        ("python-dotenv", "dotenv")
    ]
    
    for name, module in deps_to_check:
        try:
            __import__(module)
            print(f"✅ {name} installed")
        except ImportError:
            issues.append(f"❌ {name} not installed")
    
    # Summary
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Run: python scripts/setup_env.py")
        return 1
    else:
        print("\n🎉 All checks passed!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 