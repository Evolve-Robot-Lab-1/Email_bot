#!/usr/bin/env python3
"""
Interactive test script for Google AI API (Gemini)
Allows you to input prompts and receive AI-generated responses
"""
import requests
import json
import sys

def chat_with_gemini(api_key, prompt):
    """
    Send a prompt to Gemini and get a response
    """
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print("\n⏳ Sending request to Gemini AI...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()

            # Extract the generated text
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']

                # Get token usage info
                usage = data.get('usageMetadata', {})
                prompt_tokens = usage.get('promptTokenCount', 'N/A')
                response_tokens = usage.get('candidatesTokenCount', 'N/A')
                total_tokens = usage.get('totalTokenCount', 'N/A')

                print("\n" + "="*70)
                print("🤖 GEMINI AI RESPONSE:")
                print("="*70)
                print(text)
                print("="*70)
                print(f"📊 Token Usage: Prompt={prompt_tokens}, Response={response_tokens}, Total={total_tokens}")
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

def main():
    API_KEY = "AIzaSyDQ2Ap4cRxKAZmbVPmY-TICGdPhgBCHKFg"

    print("="*70)
    print("🚀 GOOGLE GEMINI AI - INTERACTIVE TEST")
    print("="*70)
    print("Type your prompt and press Enter to get AI response")
    print("Type 'quit' or 'exit' to stop")
    print("="*70)

    while True:
        try:
            # Get user input
            print("\n💬 Your prompt: ", end="")
            user_input = input().strip()

            # Check if user wants to quit
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            # Skip empty inputs
            if not user_input:
                print("⚠️  Please enter a prompt")
                continue

            # Send to Gemini and get response
            chat_with_gemini(API_KEY, user_input)

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
