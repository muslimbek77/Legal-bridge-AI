import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv('backend/.env')
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

model_name = "gemini-2.0-flash-lite-preview-02-05"
print(f"Testing model: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello, are you working?")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
