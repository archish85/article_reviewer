#!/usr/bin/env python3
"""Quick test script to check Gemini API."""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✓ API Key found: {api_key[:10]}...")

# Configure API
genai.configure(api_key=api_key)

print("\n📋 Available models:")
print("-" * 50)

try:
    # List all available models
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  • {model.name}")

    print("\n🧪 Testing API with a simple prompt...")

    # Try with the latest model
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Say 'Hello, API is working!'")

    print(f"✓ Success! Response: {response.text}")
    print("\n✅ Your Gemini API is working correctly!")
    print(f"\n💡 Use model: gemini-2.5-flash (fastest, cheapest)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTry these models instead:")
    print("  - gemini-1.5-flash")
    print("  - gemini-1.5-pro")
