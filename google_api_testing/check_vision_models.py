#!/usr/bin/env python3
"""
Check which Google AI models support vision/image analysis
"""
import requests
import json

API_KEY = "AIzaSyDQ2Ap4cRxKAZmbVPmY-TICGdPhgBCHKFg"

def get_model_details():
    """Fetch all available models and their capabilities"""

    endpoints = [
        ("v1", f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"),
        ("v1beta", f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}")
    ]

    vision_models = []

    for version, endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if 'models' in data:
                    for model in data['models']:
                        name = model.get('name', '')
                        display_name = model.get('displayName', '')
                        description = model.get('description', '')
                        supported_methods = model.get('supportedGenerationMethods', [])
                        input_token_limit = model.get('inputTokenLimit', 'N/A')
                        output_token_limit = model.get('outputTokenLimit', 'N/A')

                        # Check if it's a vision model (looks for image/vision keywords)
                        is_vision = any(keyword in name.lower() or keyword in description.lower()
                                      for keyword in ['vision', 'image', 'gemini-2', 'gemini-1.5', 'pro', 'flash'])

                        # Skip embedding models
                        if 'embedding' not in name.lower() and 'aqa' not in name.lower():
                            if 'generateContent' in supported_methods:
                                vision_models.append({
                                    'version': version,
                                    'name': name,
                                    'display_name': display_name,
                                    'description': description,
                                    'methods': supported_methods,
                                    'input_limit': input_token_limit,
                                    'output_limit': output_token_limit
                                })

        except Exception as e:
            print(f"Error fetching {version}: {e}")

    return vision_models

def test_vision_model(model_name, api_version="v1"):
    """Test a model with an image to see if it supports vision"""

    # Use a simple base64 encoded 1x1 red pixel PNG as test
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

    url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={API_KEY}"

    payload = {
        "contents": [{
            "parts": [
                {"text": "What color is this image?"},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": test_image_base64
                    }
                }
            ]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("="*80)
    print("🔍 CHECKING GOOGLE AI VISION MODELS")
    print("="*80)

    models = get_model_details()

    # Filter for likely vision models
    print("\n📋 MODELS THAT SUPPORT VISION (IMAGE INPUT):\n")

    vision_capable = []

    for model in models:
        model_name = model['name'].replace('models/', '')

        # Test if model supports vision
        print(f"Testing {model_name}... ", end="", flush=True)

        supports_vision = test_vision_model(model_name, model['version'])

        if supports_vision:
            print("✅ VISION SUPPORTED")
            vision_capable.append(model)
        else:
            print("❌ No vision support")

    print("\n" + "="*80)
    print("✅ VISION-CAPABLE MODELS SUMMARY:")
    print("="*80)

    for model in vision_capable:
        print(f"\n📷 {model['name'].replace('models/', '')}")
        if model['display_name']:
            print(f"   Display Name: {model['display_name']}")
        if model['description']:
            print(f"   Description: {model['description'][:100]}...")
        print(f"   API Version: {model['version']}")
        print(f"   Input Limit: {model['input_limit']} tokens")
        print(f"   Output Limit: {model['output_limit']} tokens")

    print("\n" + "="*80)
    print(f"Total vision-capable models found: {len(vision_capable)}")
    print("="*80)
