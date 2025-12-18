import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
model_name = "gemini-3-pro-image-preview"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

prompt = "Generate an image of a terrain heightmap."

payload = {
    "contents": [{
        "parts": [{"text": prompt}]
    }]
}

print(f"Testing {model_name}...")
response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})

print(f"Status: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)
