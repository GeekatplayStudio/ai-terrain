import google.generativeai as genai
import os
from PIL import Image
import json

class TerrainGeneratorAPI:
    def __init__(self):
        # Try to get API key from environment variable
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
    def generate_terrain(self, image_paths, status_callback=None):
        def log(message):
            if status_callback:
                status_callback(message)
            print(message)

        if not self.api_key:
            # Check if key is set in env now (in case user set it after init)
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if self.api_key:
                genai.configure(api_key=self.api_key)
            else:
                raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY environment variable.")

        log("Loading images...")
        # Load images
        images = []
        for path in image_paths:
            try:
                img = Image.open(path)
                images.append(img)
            except Exception as e:
                log(f"Failed to load {path}: {e}")

        if not images:
            raise ValueError("No valid images loaded.")

        log(f"Loaded {len(images)} images. Preparing API request...")

        # Model setup
        model = genai.GenerativeModel('gemini-1.5-pro')

        prompt = """
        Analyze these reference images of terrain. I need you to generate configuration data for a 3D application (like Terragen).
        
        1. **Atmosphere Settings**: Provide a JSON object with parameters for:
           - Sun position (azimuth, elevation)
           - Cloud coverage (0-1)
           - Fog density
           - Sky color (RGB)
           - Ambient light intensity
        
        2. **Terrain Analysis**: Describe the terrain features in detail (mountains, valleys, plains, roughness).
        
        3. **Height Map Generation**: Since you cannot directly generate an image file, please write a Python function using `numpy` and `PIL` (or `scipy`) that generates a 1024x1024 grayscale heightmap image representing this terrain. The function should return a PIL Image object. The terrain should match the features seen in the reference images (e.g., if there are mountains, generate noise that looks like mountains).
        
        Output the response in this format:
        ```json
        {
            "atmosphere": { ... },
            "terrain_description": "...",
            "python_code": "..."
        }
        ```
        Ensure the python code is valid and self-contained (imports included).
        """

        log(f"--- Prompt Sent to API ---\n{prompt}\n----------------------------")
        log("Sending request to Gemini Pro (this may take a minute)...")
        response = model.generate_content(images + [prompt])
        
        log("Response received. Parsing data...")
        # Parse response (simple extraction for now)
        text = response.text
        
        # Try to extract JSON
        try:
            # Find first { and last }
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                data = json.loads(json_str)
                log("Data parsed successfully.")
                return {
                    "atmosphere": data.get("atmosphere"),
                    "height_map_text": data.get("terrain_description"),
                    "python_code": data.get("python_code"),
                    "raw_text": text
                }
        except Exception as e:
            log(f"JSON parsing failed: {e}")
        
        log("Returning raw text response.")
        return {"raw_text": text, "height_map_text": text}
