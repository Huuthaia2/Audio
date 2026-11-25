from google import genai
import sys

API_KEY = "AIzaSyCJWY4EXp--S2HU26wm590pOB4xxSSYDOc"
client = genai.Client(api_key=API_KEY)

print("Listing models with New SDK...")
try:
    for m in client.models.list():
        print(f"Name: {m.name}, DisplayName: {m.display_name}")
except Exception as e:
    print(f"Error: {e}")
