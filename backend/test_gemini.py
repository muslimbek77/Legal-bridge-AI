
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

print(f"✅ Found API Key: {api_key[:5]}...{api_key[-5:]}")

try:
    genai.configure(api_key=api_key)
    
    print("📋 Listing available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")

    model = genai.GenerativeModel('gemini-flash-latest')
    
    print("\n🤖 Sending request to Gemini...")
    response = model.generate_content("Hello, are you working? Please reply with 'Yes, I am working!'")
    
    print(f"✅ Response received: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
