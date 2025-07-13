#!/usr/bin/env python3
"""Debug XAI extraction with proper config loading"""

import yaml
import requests
import json
from pathlib import Path


def test_xai_extraction():
    """Test XAI extraction with sample text"""
    
    # Load API key from config
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
            api_key = config.get("api", {}).get("xai", {}).get("api_key", "")
    else:
        api_key = "xai-RPhTjf3SzTbm11ZKcpFV0hsOqVTSj8QUbTFUhUrrQWaE"
    
    print(f"Using API key: {api_key[:10]}...")
    
    sample_text = """
    SEPAM LD V3 Protection Relay End of Service Notice
    
    Dear Customer,
    
    We would like to inform you that Schneider Electric has decided to discontinue 
    the SEPAM LD V3 series protection relays effective December 31, 2024.
    
    This affects the following SEPAM LD products:
    - SEPAM LD3 relays
    - SEPAM LD4 relay units
    
    Technical specifications:
    - Voltage: 110-250V AC/DC
    - Protection functions: overcurrent, earth fault
    
    Recommended migration: SEPAM M series relays
    """
    
    prompt = f"""Analyze this Schneider Electric document and extract product ranges mentioned.

CONTEXT: Protection relay document
DOCUMENT: test_sepam.txt
CONTENT: {sample_text}

Extract ONLY product ranges explicitly mentioned in the document text.
Return a JSON array: ["Range1", "Range2"]

Looking for ranges like SEPAM, TeSys, PIX, etc. Only return what is actually mentioned."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "grok-beta",
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        print("🤖 Testing XAI extraction...")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content_resp = result['choices'][0]['message']['content']
            print(f"Response: {content_resp}")
            
            try:
                ranges = json.loads(content_resp)
                print(f"✅ Parsed ranges: {ranges}")
                return ranges
            except Exception as e:
                print(f"⚠️ JSON parse failed: {e}")
                import re
                matches = re.findall(r'["\']([^"\']+)["\']', content_resp)
                print(f"Regex extracted: {matches}")
                return matches
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []


if __name__ == "__main__":
    result = test_xai_extraction()
    print(f"\nFinal result: {result}") 