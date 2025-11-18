#!/usr/bin/env python3
"""
List available Google AI models
"""
import requests
import json

API_KEY = "AIzaSyDQ2Ap4cRxKAZmbVPmY-TICGdPhgBCHKFg"

# Try different API versions
endpoints = [
    f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}",
    f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
]

for endpoint in endpoints:
    print(f"\nTrying: {endpoint.split('?')[0]}")
    print("-" * 60)
    try:
        response = requests.get(endpoint, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nAvailable Models:")
            if 'models' in data:
                for model in data['models']:
                    print(f"  - {model.get('name', 'N/A')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
