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
        
    def generate_heightmap_script(self, image_paths, status_callback=None):
        def log(message):
            if status_callback:
                status_callback(message)
            print(message)

        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Google API Key not found.")

        log("Preparing Heightmap Generation Request...")
        contents_parts = []
        
        for path in image_paths:
            try:
                img = Image.open(path)
                if img.mode != 'RGB': img = img.convert('RGB')
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                contents_parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img_str}})
            except Exception as e:
                log(f"Failed to load {path}: {e}")

        prompt = """
        You are an expert Python programmer and Terrain Artist.
        
        **TASK**: Write a Python script using `numpy`, `PIL`, and `scipy` to generate a 2048x2048 16-bit grayscale heightmap.
        
        **CRITICAL REQUIREMENT**: The heightmap must match the **COMPOSITION and LAYOUT** of the first reference image provided. 
        
        **STRATEGY**: 
        Instead of guessing coordinates, you MUST:
        1. **Load the first reference image** provided in the list `image_paths`.
        2. **Convert it to Grayscale**. Brighter pixels = Higher elevation. Darker = Lower.
        3. **Resize** it to 2048x2048.
        4. **Apply Gaussian Blur** (sigma=2 to 5) using `scipy.ndimage` to smooth out JPEG artifacts and make it look like rolling terrain.
        5. **Normalize** the data to use the full 16-bit range (0-65535).
        6. **Save** as `generated_heightmap.png`.
        
        **CODE TEMPLATE**:
        ```python
        import numpy as np
        from PIL import Image
        import scipy.ndimage
        import sys
        import os
        
        # The paths are passed to the script or hardcoded. 
        # Since this script runs locally, we can assume the image path is available.
        # [AI: Insert the actual path of the first image here]
        image_path = r"__IMAGE_PATH__" 
        
        def main():
            print(f"Processing {{image_path}}...")
            
            # 1. Load Image
            try:
                if not os.path.exists(image_path):
                    print(f"Error: Image file not found at {{image_path}}")
                    print(f"CWD: {{os.getcwd()}}")
                    return
                img = Image.open(image_path).convert('L') # Convert to grayscale
            except Exception as e:
                print(f"Error loading image: {{e}}")
                return

            # 2. Resize to Target Resolution
            W, H = 2048, 2048
            img = img.resize((W, H), Image.Resampling.LANCZOS)
            
            # 3. Convert to Numpy Array
            elevation = np.array(img, dtype=np.float32)
            
            # 4. Apply Smoothing (Terrain shouldn't look like a pixelated photo)
            elevation = scipy.ndimage.gaussian_filter(elevation, sigma=3.0)
            
            # 5. Normalize to 0-1
            elevation = (elevation - np.min(elevation)) / (np.max(elevation) - np.min(elevation))
            
            # 6. Scale to 16-bit
            elevation = (elevation * 65535).astype(np.uint16)
            
            # 7. Save
            output_path = os.path.abspath("generated_heightmap.png")
            Image.fromarray(elevation, mode='I;16').save(output_path)
            print(f"Heightmap saved to {{output_path}}")

        if __name__ == "__main__":
            main()
        ```
        
        Return ONLY the Python code in a markdown block.
        """
        
        # Inject the actual image path into the prompt
        if image_paths:
            # Use forward slashes for compatibility and avoid escape issues
            clean_path = image_paths[0].replace("\\", "/")
            prompt = prompt.replace("__IMAGE_PATH__", clean_path)
        
        contents_parts.append({"text": prompt})
        
        model_name = "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": contents_parts}]}
        
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            result_json = response.json()
            
            text_response = ""
            try:
                parts = result_json['candidates'][0]['content']['parts']
                for part in parts:
                    if 'text' in part: text_response += part['text']
            except Exception:
                pass

            # Extract Code
            code = None
            code_start = text_response.find("```python")
            if code_start != -1:
                code_start += 9
                code_end = text_response.find("```", code_start)
                if code_end != -1:
                    code = text_response[code_start:code_end].strip()
            
            return code
            
        except Exception as e:
            log(f"Heightmap generation failed: {e}")
            raise

    def generate_terrain(self, image_paths, heightfield_path=None, status_callback=None):
        def log(message):
            if status_callback:
                status_callback(message)
            print(message)

        if not self.api_key:
            # Check if key is set in env now (in case user set it after init)
            self.api_key = os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY environment variable.")

        log("Loading images...")
        # Load images and convert to base64
        contents_parts = []
        
        for path in image_paths:
            try:
                img = Image.open(path)
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                contents_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_str
                    }
                })
            except Exception as e:
                log(f"Failed to load {path}: {e}")

        if not contents_parts and not heightfield_path:
            raise ValueError("No valid images loaded and no heightfield selected.")

        log(f"Loaded {len(contents_parts)} images. Preparing API request...")

        hf_instruction = ""
        if heightfield_path:
            hf_instruction = f"""
            **HEIGHTFIELD MODE ACTIVE**:
            The user has provided a specific heightfield file at: `{heightfield_path}`.
            
            **Your Script MUST**:
            1. Create a `heightfield_load` node.
            2. Set its `filename` parameter to `{heightfield_path}`.
            3. Create a `heightfield_shader` node and connect the load node to it.
            4. Connect the `heightfield_shader` to the `compute_terrain` (or planet).
            5. **CRITICAL**: Create a `power_fractal_shader_v3` for FINE DETAIL ONLY (small rocks, roughness) and blend it over the heightfield.
               - Do NOT create large mountains with the fractal; the heightfield provides the shape.
               - Tune the fractal for `smallest_scale` (e.g., 0.1 to 1.0) and `feature_scale` (e.g., 10.0).
            """
        else:
            hf_instruction = """
            **PROCEDURAL MODE ACTIVE**:
            No heightfield file provided. You MUST generate the terrain shape procedurally using `power_fractal_shader_v3` nodes as described below.
            """

        prompt = f"""
        You are an expert Terragen Professional scripter.
        
        **TASK**: Write a Python script using `terragen_rpc` to generate terrain.
        {hf_instruction}
        
        **VISUAL ANALYSIS (If images provided)**:
        - Analyze the images for:
          1. **Roughness**: Is it jagged/rocky (high roughness) or smooth/eroded (low roughness)?
          2. **Features**: Ridges, cliffs, dunes?
          3. **Atmosphere**: Sun angle, haze?

        **MANDATORY CODE STRUCTURE**:
        You MUST use this exact structure for finding and connecting nodes.
        **WARNING**: `terragen_rpc` does NOT have a `node_by_name` function. You MUST use `node_by_path` or `children_filtered_by_class`.
        **WARNING**: Do NOT use `combiner_shader`. Use `merge_shader` to combine terrains.
        **WARNING**: Always check if `create_child` returns a valid node before calling `set_param`.

        ```python
        import terragen_rpc as tg
        import sys

        def get_project():
            try:
                p = tg.root()
                if not p: raise Exception("Project root not found")
                return p
            except Exception as e:
                print(f"Error connecting to Terragen: {{e}}")
                sys.exit(1)

        def find_node_by_class(project, class_name):
            nodes = project.children_filtered_by_class(class_name)
            return nodes[0] if nodes else None

        def create_node(parent, class_name, name=None):
            try:
                node = tg.create_child(parent, class_name)
                if not node:
                    print(f"Failed to create node of class {{class_name}}")
                    return None
                if name:
                    node.set_param("name", name)
                return node
            except Exception as e:
                print(f"Error creating {{class_name}}: {{e}}")
                return None

        def main():
            project = get_project()
            
            # FIND COMPUTE TERRAIN
            # We must connect our terrain to the 'Compute Terrain' node to make it visible.
            compute_terrain = find_node_by_class(project, "compute_terrain")
            if not compute_terrain:
                # Fallback: Try to find by path
                compute_terrain = tg.node_by_path("/Compute Terrain")
            
            if not compute_terrain:
                print("Error: Could not find 'Compute Terrain' node. Cannot connect terrain.")
                return

            print(f"Found Compute Terrain: {{compute_terrain.path}}")

            # 1. CREATE NODES
            
            # [INSERT LOGIC HERE: Create your Heightfield Load / Shader nodes]
            # USE create_node() helper function!
            # Ensure you assign them to variables like `final_terrain_node`
            
            # Example:
            # hf_load = create_node(project, "heightfield_load", "My Heightfield")
            # if hf_load:
            #     hf_load.set_param("filename", r"{heightfield_path}")
            #     hf_shader = create_node(project, "heightfield_shader", "My HF Shader")
            #     if hf_shader:
            #         hf_shader.set_param("input_node", hf_load.id)
            #         final_terrain_node = hf_shader

            # 2. CONNECT TO TERRAIN PIPELINE
            # Connect the output of your new chain to the input of Compute Terrain
            if 'final_terrain_node' in locals() and final_terrain_node:
                # Check if Compute Terrain already has an input
                current_input = compute_terrain.get_param_as_string("input_node")
                
                # Connect our new node to Compute Terrain
                compute_terrain.set_param("input_node", final_terrain_node.id)
                print(f"Connected {{final_terrain_node.name}} to Compute Terrain")
                
                # Optional: If there was a previous input, maybe connect it to our new node's input?
                # if current_input:
                #     final_terrain_node.set_param("input_node", current_input)

            # 3. CAMERA & ATMOSPHERE
            # [Add your camera/atmosphere code here]

        if __name__ == "__main__":
            main()
        ```
        
        **Output Format**:
        1. Provide a JSON object for the description:
        ```json
        {{
            "terrain_description": "Detailed description of the visual analysis..."
        }}
        ```
        2. Provide the Python code in a separate Markdown code block:
        ```python
        # Your code here
        ```
        """
        
        contents_parts.append({"text": prompt})

        log(f"--- Prompt Sent to API ---\n{prompt}\n----------------------------")
        
        # Using Gemini 2.0 Flash for better code generation logic (switching back from image preview model)
        model_name = "gemini-2.0-flash"
        log(f"Sending request to Gemini Model: {model_name}...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": contents_parts
            }]
        }
        
        try:
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
            result_json = response.json()
            
            log("Response received. Parsing data...")
            
            generated_images = []
            text_response = ""

            try:
                parts = result_json['candidates'][0]['content']['parts']
                for part in parts:
                    if 'text' in part:
                        text_response += part['text']
                    if 'inline_data' in part:
                        # Handle generated image
                        mime_type = part['inline_data']['mime_type']
                        data = part['inline_data']['data']
                        img_data = base64.b64decode(data)
                        img = Image.open(BytesIO(img_data))
                        generated_images.append(img)
                        log(f"Received generated image ({mime_type})")
            except (KeyError, IndexError) as e:
                log(f"Unexpected response format: {result_json}")
                raise ValueError("Failed to parse API response")

            # Try to extract JSON from text
            parsed_data = {}
            terragen_code = None
            
            # Extract JSON
            try:
                start = text_response.find('{')
                end = text_response.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = text_response[start:end]
                    parsed_data = json.loads(json_str)
                    log("JSON Data parsed successfully.")
            except Exception as e:
                log(f"JSON parsing failed: {e}")

            # Extract Python Code Block
            try:
                code_start = text_response.find("```python")
                if code_start != -1:
                    code_start += 9 # Skip ```python
                    code_end = text_response.find("```", code_start)
                    if code_end != -1:
                        terragen_code = text_response[code_start:code_end].strip()
                        log("Python code block extracted successfully.")
            except Exception as e:
                log(f"Code extraction failed: {e}")
            
            return {
                "height_map_text": parsed_data.get("terrain_description", text_response),
                "terragen_rpc_code": terragen_code,
                "raw_text": text_response
            }
            
        except requests.exceptions.RequestException as e:
            log(f"API Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                log(f"Error details: {e.response.text}")
            raise
