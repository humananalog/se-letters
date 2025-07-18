#!/usr/bin/env python3
"""
Simple test script to verify webapp can run Python scripts
"""

import json
import sys

print("This is a test message")
print("Another test message")
print(json.dumps({
    "success": True,
    "message": "Test script executed successfully",
    "test_data": "Hello from Python!"
})) 