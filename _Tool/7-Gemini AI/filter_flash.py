from google import genai
import sys

API_KEY = "AIzaSyCJWY4EXp--S2HU26wm590pOB4xxSSYDOc"
client = genai.Client(api_key=API_KEY)

print("Searching for Flash models...")
try:
    models = client.models.list()
    for m in models:
        if "flash" in m.name.lower():
            print(f"Name: {m.name}")
except Exception as e:
    print(f"Error: {e}")
