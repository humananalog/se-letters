#!/usr/bin/env python3
"""Debug XAI extraction"""

import requests
import json

def test_xai_extraction():
    """Test XAI extraction with sample text"""
    
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

CONTEXT: Unknown | Unknown | PPIBS
DOCUMENT: test_sepam.txt
CONTENT: {sample_text}

Extract ONLY product ranges explicitly mentioned in the document text.
Return a JSON array: ["Range1", "Range2"]

Do NOT infer ranges from filename or context - only from actual document content."""

    headers = {
        "Authorization": "Bearer xai-RPhTjf3SzTbm11ZKcpFV0hsOqVTSj8QUbTFUhUrrQWaE",
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
                print(f"Parsed ranges: {ranges}")
            except:
                import re
                matches = re.findall(r'["\']([^"\']+)["\']', content_resp)
                print(f"Regex extracted: {matches}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_xai_extraction() 