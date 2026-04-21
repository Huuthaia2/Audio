import google.generativeai as genai
import os

API_KEY = "AIzaSyD0WBwGovIv-5dVqtyfjjRQmkwrL9V3vpU"
genai.configure(api_key=API_KEY)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
