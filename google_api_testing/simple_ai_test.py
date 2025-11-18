#!/usr/bin/env python3
"""
Simple one-shot test for Google AI API - Input prompt via command line argument
"""
import requests
import json
import sys

def test_gemini(api_key, prompt):
    """Send a prompt to Gemini and get a response"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"\n📤 INPUT: {prompt}")
        print("-" * 70)
        print("⏳ Sending to Gemini AI...\n")

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()

            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                usage = data.get('usageMetadata', {})

                print("="*70)
                print("📥 OUTPUT:")
                print("="*70)
                print(text)
                print("="*70)
                print(f"Token Usage: {usage.get('promptTokenCount', 'N/A')} prompt + "
                      f"{usage.get('candidatesTokenCount', 'N/A')} response = "
                      f"{usage.get('totalTokenCount', 'N/A')} total")
                print("="*70)
                return text
            else:
                print("❌ No response generated")
                return None
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    API_KEY = "AIzaSyDQ2Ap4cRxKAZmbVPmY-TICGdPhgBCHKFg"

    # Get prompt from command line or use default
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Explain quantum computing in simple terms"

    test_gemini(API_KEY, prompt)
