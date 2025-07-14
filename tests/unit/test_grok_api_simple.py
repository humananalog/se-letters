#!/usr/bin/env python3
"""
Simple Grok API Test
Tests basic connectivity and model availability
"""

import sys
import json
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from se_letters.core.config import get_config

def test_grok_api():
    """Test basic Grok API connectivity"""
    print("🧪 Testing Grok API Connectivity")
    print("=" * 50)
    
    try:
        config = get_config()
        
        print(f"🔑 API Key: {config.api.api_key[:10]}...")
        print(f"🌐 Base URL: {config.api.base_url}")
        print(f"🤖 Model: {config.api.model}")
        
        # Test different model names
        models_to_test = [
            "grok-beta",
            "grok-2-mini", 
            "grok-1",
            "grok-mini",
            config.api.model  # From config
        ]
        
        headers = {
            "Authorization": f"Bearer {config.api.api_key}",
            "Content-Type": "application/json"
        }
        
        for model in models_to_test:
            print(f"\n🔍 Testing model: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Respond in JSON format."
                    },
                    {
                        "role": "user",
                        "content": "Extract the product name from this text: 'PIX2B is being withdrawn'. Respond with JSON: {\"product\": \"product_name\"}"
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            
            try:
                response = requests.post(
                    f"{config.api.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                print(f"   📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    parsed = json.loads(content)
                    print(f"   ✅ SUCCESS: {parsed}")
                    return model  # Return first working model
                    
                elif response.status_code == 404:
                    print(f"   ❌ Model not found")
                elif response.status_code == 401:
                    print(f"   ❌ Authentication failed")
                else:
                    print(f"   ❌ Error: {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"   ⏱️ Timeout")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print(f"\n❌ No working models found")
        return None
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return None

if __name__ == "__main__":
    working_model = test_grok_api()
    if working_model:
        print(f"\n🎉 Working model found: {working_model}")
        print("💡 Update your config to use this model")
    else:
        print(f"\n💥 No working models found")
        print("💡 Check your API key and x.ai documentation") 