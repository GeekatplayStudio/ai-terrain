import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found.")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    print(f"{'Model Name':<40} | {'Supported Generation Methods'}")
    print("-" * 80)
    
    for model in data.get('models', []):
        name = model.get('name')
        methods = model.get('supportedGenerationMethods', [])
        print(f"{name:<40} | {', '.join(methods)}")
        
except Exception as e:
    print(f"Error listing models: {e}")
