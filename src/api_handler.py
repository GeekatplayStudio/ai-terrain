import os
from datetime import datetime
from io import BytesIO
import base64
import json

from PIL import Image
import requests

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

    def _call_gemini_text(self, content_parts, log_callback, model_name="gemini-2.0-flash"):
        """Helper to send request to Gemini and return concatenated text"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": content_parts}]}
        log_callback(f"Sending request to {model_name} for text analysis...")
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})

        try:
            result_json = response.json()
        except Exception as e:
            log_callback(f"Failed to decode response: {e}")
            return ""

        if response.status_code != 200:
            log_callback(f"API Error {response.status_code}: {result_json}")
            response.raise_for_status()

        try:
            candidates = result_json.get('candidates', [])
            if not candidates:
                log_callback(f"No candidates returned. Feedback: {result_json.get('promptFeedback', 'N/A')}")
                return ""
            parts = candidates[0]['content']['parts']
            texts = []
            for part in parts:
                if 'text' in part:
                    texts.append(part['text'])
            return "\n".join(texts).strip()
        except Exception as e:
            log_callback(f"Failed to extract text: {e}")
            return ""

    def analyze_sun_angles(self, image_path, status_callback=None):
        def log(message):
            if status_callback: status_callback(message)
            print(message)

        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Google API Key not found.")

        payload = self._prepare_image_payload(image_path)
        if not payload:
            raise ValueError("Invalid sky reference image.")

        prompt = """
        You are a lighting TD. From the attached sky photo, estimate the sun direction.
        Return ONLY compact JSON with keys: sun_azimuth_deg (0-360, clockwise from North) and sun_elevation_deg (-10 to 90).
        Example: {"sun_azimuth_deg": 215, "sun_elevation_deg": 14}
        Do not include any extra text.
        """

        parts = [payload, {"text": prompt}]
        raw = self._call_gemini_text(parts, log)
        if not raw:
            raise Exception("No sun analysis returned.")

        try:
            # Attempt to extract JSON snippet
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1:
                snippet = raw[start:end+1]
                return json.loads(snippet)
        except Exception as e:
            log(f"Failed to parse sun JSON: {e}")
        raise Exception("Could not parse sun azimuth/elevation from analysis.")

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

    def analyze_atmosphere(self, image_path, status_callback=None):
        def log(message):
            if status_callback: status_callback(message)
            print(message)

        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Google API Key not found.")

        payload = self._prepare_image_payload(image_path)
        if not payload:
            raise ValueError("Invalid sky reference image.")

        prompt = """
        You are an expert Terragen TD. Analyze the attached sky/cloud reference and describe settings to recreate the atmosphere in Terragen.
        - Time: time of day; Sun: azimuth (deg), elevation (deg), color temperature (K), overall light tint.
        - Clouds: list each layer with type (e.g., cumulus, stratocumulus, cirrus, altocumulus), coverage %, density/softness, base altitude km, top altitude km, notable features (anvils, wisps, towering, flat deck).
        - Atmosphere: horizon haze/turbidity, ambient light level, aerial perspective strength, visibility km, color casts or weather hints (clear, stormy, overcast, sunset).
        - Output concise bullet points; no JSON; keep under 120 words; no image generation instructions.
        """

        parts = [payload, {"text": prompt}]
        result = self._call_gemini_text(parts, log)
        if not result:
            raise Exception("No analysis returned for sky reference.")
        return result

    def generate_heightfield(self, image_paths, generate_texture=True, status_callback=None):
        """Generate heightmap (and optional texture), save to disk, and return file paths."""

        def log(message):
            if status_callback:
                status_callback(message)
            print(message)

        # Reuse the existing image generation pipeline
        images = self.generate_heightmap_images(image_paths, generate_texture, status_callback=log)
        if not images:
            raise Exception("No images returned from Gemini.")

        output_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save heightmap
        heightmap_img = images[0]
        hf_filename = os.path.join(output_dir, f"heightfield_{timestamp}.png")
        heightmap_img.save(hf_filename, format="PNG")
        log(f"Saved heightfield to {hf_filename}")

        texture_path = None
        if generate_texture and len(images) > 1:
            texture_img = images[1]
            tex_filename = os.path.join(output_dir, f"texture_{timestamp}.png")
            texture_img.save(tex_filename, format="PNG")
            texture_path = tex_filename
            log(f"Saved texture to {tex_filename}")

        return {"heightfield_path": hf_filename, "texture_path": texture_path}
