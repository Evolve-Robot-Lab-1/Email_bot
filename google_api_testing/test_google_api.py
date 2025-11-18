#!/usr/bin/env python3
"""
Test script for Google AI API (Gemini)
"""
import requests
import json

def test_google_ai_api(api_key):
    """
    Test the Google AI API (Gemini) with a simple prompt
    """
    # Gemini API endpoint (using v1 API with gemini-2.5-flash model)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

    # Simple test prompt
    payload = {
        "contents": [{
            "parts": [{
                "text": "Hello! Please respond with a simple greeting to confirm you're working."
            }]
        }]
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🔍 Testing Google AI API (Gemini)...")
    print(f"📡 Endpoint: {url.split('?')[0]}")
    print("-" * 60)

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"Status Code: {response.status_code}")
        print("-" * 60)

        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! API is working!\n")
            print("Response:")
            print(json.dumps(data, indent=2))

            # Extract and display the generated text
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                print("\n" + "=" * 60)
                print("Generated Text:")
                print("=" * 60)
                print(text)
                print("=" * 60)

            return True
        else:
            print(f"❌ FAILED! Error {response.status_code}")
            print("\nError Response:")
            print(json.dumps(response.json(), indent=2))
            return False

    except requests.exceptions.Timeout:
        print("❌ FAILED! Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED! Request error: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ FAILED! Invalid JSON response")
        print(f"Response text: {response.text}")
        return False
    except Exception as e:
        print(f"❌ FAILED! Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Your API key
    API_KEY = "AIzaSyDQ2Ap4cRxKAZmbVPmY-TICGdPhgBCHKFg"

    # Test the API
    success = test_google_ai_api(API_KEY)

    print("\n" + "=" * 60)
    if success:
        print("✅ Google AI API is functioning correctly!")
    else:
        print("❌ Google AI API test failed. Check the error messages above.")
    print("=" * 60)
