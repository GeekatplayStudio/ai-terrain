import os
from PIL import Image
import json
import requests
import base64
from io import BytesIO

class TerrainGeneratorAPI:
    def __init__(self):
        # Try to get API key from environment variable
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
    def _prepare_image_payload(self, image_source):
        """Helper to convert PIL Image or file path to API payload"""
        try:
            if isinstance(image_source, str):
                img = Image.open(image_source)
            else:
                img = image_source
                
            if img.mode != 'RGB': img = img.convert('RGB')
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
        except Exception as e:
            print(f"Failed to process image: {e}")
            return None

    def _call_gemini(self, content_parts, log_callback):
        """Helper to send request to Gemini and parse images"""
        model_name = "gemini-3-pro-image-preview" 
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": content_parts}]}
        
        log_callback(f"Sending request to {model_name}...")
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        try:
            # print(f"DEBUG STATUS: {response.status_code}") # Reduced debug noise
            result_json = response.json()
        except Exception as e:
            log_callback(f"Failed to decode response: {e}")
            return []

        if response.status_code != 200:
            log_callback(f"API Error {response.status_code}: {result_json}")
            response.raise_for_status()

        generated_images = []
        try:
            candidates = result_json.get('candidates', [])
            if not candidates:
                log_callback(f"No candidates returned. Feedback: {result_json.get('promptFeedback', 'N/A')}")
                
            if candidates:
                parts = candidates[0]['content']['parts']
                for part in parts:
                    inline_data = part.get('inline_data') or part.get('inlineData')
                    if inline_data:
                        mime_type = inline_data.get('mime_type') or inline_data.get('mimeType')
                        data = inline_data.get('data')
                        if data:
                            img_data = base64.b64decode(data)
                            img = Image.open(BytesIO(img_data))
                            generated_images.append(img)
                            log_callback(f"Received generated image ({mime_type})")
                    elif 'text' in part:
                        log_callback(f"Model Text: {part['text'][:100]}...")
        except Exception as e:
            log_callback(f"Failed to extract images: {e}")
            
        return generated_images

    def generate_heightmap_images(self, image_paths, generate_texture=True, status_callback=None):
        def log(message):
            if status_callback: status_callback(message)
            print(message)

        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Google API Key not found.")

        # --- Prepare Reference Images ---
        reference_payloads = []
        for path in image_paths:
            payload = self._prepare_image_payload(path)
            if payload: reference_payloads.append(payload)

        if not reference_payloads:
            raise ValueError("No valid reference images found.")

        # --- STEP 1: Generate Heightmap ---
        log("Step 1/2: Generating Heightmap (1:1 Square, Top-Down)...")
        
        prompt_hf = """
        You are an expert Terrain Artist AI.
        **TASK**: Generate a **Heightmap** based on the attached reference images.
        **REQUIREMENTS**:
        1. **View**: Strictly TOP-DOWN ORTHOGRAPHIC (satellite/nadir, 0° tilt). No side, oblique, or perspective mixes; horizon must never appear.
        2. **Format**: 1:1 Square aspect ratio.
        3. **Style**: 16-bit style grayscale heightmap. White = High, Black = Low.
        4. **Content**: Hallucinate realistic terrain details (erosion, mountains) implied by the references.
        5. **Consistency**: If any angled/side view would appear, regenerate to keep strict top-down.
        **OUTPUT**: Return ONLY the heightmap image.
        """
        
        parts_step1 = reference_payloads + [{"text": prompt_hf}]
        hf_images = self._call_gemini(parts_step1, log)
        
        if not hf_images:
            raise Exception("Failed to generate heightmap in Step 1.")
            
        heightmap_img = hf_images[0]
        log("Heightmap generated successfully.")

        if not generate_texture:
            log("Texture generation skipped by user.")
            return [heightmap_img]

        # --- STEP 2: Generate Texture ---
        log("Step 2/2: Generating Texture Map (Matching Heightmap)...")
        
        # Convert generated heightmap to payload
        hf_payload = self._prepare_image_payload(heightmap_img)
        
        prompt_tex = """
        You are an expert Terrain Artist AI.
        **INPUT**: 
        1. The first image attached is a **Heightmap** you just generated.
        2. The other images are reference photos for style/colors.
        
        **TASK**: Generate a **Texture Map** that perfectly matches the provided Heightmap.
        **REQUIREMENTS**:
        1. **View**: Strictly TOP-DOWN ORTHOGRAPHIC (satellite/nadir, 0° tilt). No side, oblique, or perspective mixes; horizon must never appear. Must align 1:1 with the heightmap.
        2. **Format**: 1:1 Square aspect ratio.
        3. **Style**: Realistic satellite texture (rock, snow, grass) based on the elevation in the heightmap and style from references.
        4. **Consistency**: If any angled/side view would appear, regenerate to keep strict top-down.
        **OUTPUT**: Return ONLY the texture map image.
        """
        
        # Order: Heightmap first, then references, then prompt
        parts_step2 = [hf_payload] + reference_payloads + [{"text": prompt_tex}]
        tex_images = self._call_gemini(parts_step2, log)
        
        if not tex_images:
            log("Warning: Failed to generate texture in Step 2. Returning only heightmap.")
            return [heightmap_img]
            
        texture_img = tex_images[0]
        log("Texture map generated successfully.")

        return [heightmap_img, texture_img]
