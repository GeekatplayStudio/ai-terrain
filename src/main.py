import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import sys
import threading
import webbrowser
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from api_handler import TerrainGeneratorAPI

load_dotenv()

class TerrainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Terrain AI Generator")
        self.geometry("1000x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Terrain AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.upload_btn = ctk.CTkButton(self.sidebar_frame, text="Upload Images", command=self.upload_images)
        self.upload_btn.grid(row=1, column=0, padx=20, pady=10)

        self.hf_btn = ctk.CTkButton(self.sidebar_frame, text="Select Heightfield", command=self.select_heightfield)
        self.hf_btn.grid(row=2, column=0, padx=20, pady=10)

        self.gen_hf_btn = ctk.CTkButton(self.sidebar_frame, text="Generate Heightfield", fg_color="#800080", hover_color="#4b0082", command=self.start_heightfield_generation)
        self.gen_hf_btn.grid(row=3, column=0, padx=20, pady=10)
        self.gen_hf_btn.configure(state="disabled")

        self.generate_btn = ctk.CTkButton(self.sidebar_frame, text="Generate Terrain", command=self.start_generation)
        self.generate_btn.grid(row=4, column=0, padx=20, pady=10)
        self.generate_btn.configure(state="disabled")

        self.load_btn = ctk.CTkButton(self.sidebar_frame, text="Load Project (JSON)", command=self.load_project)
        self.load_btn.grid(row=5, column=0, padx=20, pady=10)

        self.save_btn = ctk.CTkButton(self.sidebar_frame, text="Save Project (JSON)", command=self.save_project)
        self.save_btn.grid(row=6, column=0, padx=20, pady=10)
        self.save_btn.configure(state="disabled")

        self.quit_btn = ctk.CTkButton(self.sidebar_frame, text="Quit", fg_color="red", hover_color="darkred", command=self.quit_app)
        self.quit_btn.grid(row=7, column=0, padx=20, pady=10)

        self.footer_label = ctk.CTkLabel(self.sidebar_frame, text="Created by\nGeekatplay Studio", font=ctk.CTkFont(size=12))
        self.footer_label.grid(row=8, column=0, padx=20, pady=(20, 0))
        
        self.youtube_btn = ctk.CTkButton(self.sidebar_frame, text="Tutorials: @geekatplay", fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"), command=self.open_youtube)
        self.youtube_btn.grid(row=9, column=0, padx=20, pady=(5, 20))

        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.image_paths = []
        self.heightfield_path = None
        self.last_result = None
        self.api = TerrainGeneratorAPI()

        self.status_label = ctk.CTkLabel(self.main_frame, text="Upload reference images to start.")
        self.status_label.pack(pady=10)

        self.log_textbox = ctk.CTkTextbox(self.main_frame, height=100)
        self.log_textbox.pack(fill="x", padx=20, pady=5)
        self.log_textbox.configure(state="disabled")

        self.images_frame = ctk.CTkFrame(self.main_frame)
        self.images_frame.pack(fill="x", padx=20, pady=10)

        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Manual Terragen Tools ---
        self.tools_frame = ctk.CTkFrame(self.main_frame)
        self.tools_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.tools_frame, text="Terragen Integration", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        # Source Selector
        self.source_selector = ctk.CTkSegmentedButton(self.tools_frame, values=["Manual Files", "Generated Result", "Uploaded Images"])
        self.source_selector.pack(fill="x", padx=10, pady=5)
        self.source_selector.set("Manual Files")

        self.manual_hf_path = None
        self.manual_tex_path = None
        
        btn_frame = ctk.CTkFrame(self.tools_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.sel_hf_btn = ctk.CTkButton(btn_frame, text="Select Heightfield", command=self.select_manual_hf)
        self.sel_hf_btn.pack(side="left", padx=5)
        
        self.sel_tex_btn = ctk.CTkButton(btn_frame, text="Select Texture", command=self.select_manual_tex)
        self.sel_tex_btn.pack(side="left", padx=5)
        
        self.send_tg_btn = ctk.CTkButton(btn_frame, text="Send to Terragen", fg_color="green", command=self.send_to_terragen)
        self.send_tg_btn.pack(side="left", padx=5)
        # self.send_tg_btn.configure(state="disabled") # Enable by default, validate on click

        # --- Debug Tools ---
        debug_frame = ctk.CTkFrame(self.tools_frame, fg_color="transparent")
        debug_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(debug_frame, text="Read Node Structure", command=self.read_node_structure).pack(side="left", padx=5)
        # Removed "Add Fractal & Nodes" as it is now integrated into Send to Terragen

        # Preview Frame for Manual Tools
        self.manual_preview_frame = ctk.CTkFrame(self.tools_frame, fg_color="transparent")
        self.manual_preview_frame.pack(fill="x", padx=10, pady=5)
        
        self.hf_preview_lbl = ctk.CTkLabel(self.manual_preview_frame, text="No HF Selected")
        self.hf_preview_lbl.pack(side="left", padx=10)
        
        self.tex_preview_lbl = ctk.CTkLabel(self.manual_preview_frame, text="No Texture Selected")
        self.tex_preview_lbl.pack(side="left", padx=10)

    def read_node_structure(self):
        try:
            import terragen_rpc as tg
            try:
                project = tg.root()
                if not project: raise Exception("No project")
            except:
                messagebox.showerror("Error", "Could not connect to Terragen.")
                return

            self.log_message("--- Reading Terragen Node Structure ---")
            
            # List children of root
            children = project.children()
            self.log_message(f"Root Children ({len(children)}):")
            for child in children:
                self.log_message(f" - {child.name()} ({child.path()}) [Class: {child.path().split('/')[-1]}]") # Class isn't directly available, guessing from path/name

            # Inspect Planet 01
            planet = tg.node_by_path("/Planet 01")
            if planet:
                self.log_message("\n--- Planet 01 Details ---")
                surf_shader = planet.get_param_as_string("surface_shader")
                self.log_message(f"Surface Shader Input: '{surf_shader}'")
            else:
                self.log_message("\nWARNING: Planet 01 not found!")

            # Inspect Compute Terrain
            ct = tg.node_by_path("/Compute Terrain")
            if ct:
                self.log_message("\n--- Compute Terrain Details ---")
                input_node = ct.get_param_as_string("input_node")
                self.log_message(f"Input Node: '{input_node}'")
            else:
                self.log_message("\nWARNING: Compute Terrain not found!")
                
            self.log_message("---------------------------------------")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read structure: {e}")

    def deploy_to_terragen(self, hf_path, tex_path):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project: 
                messagebox.showerror("Error", "Not connected.")
                return

            self.log_message(f"--- Deploying to Terragen (HF: {os.path.basename(hf_path) if hf_path else 'None'}, Tex: {os.path.basename(tex_path) if tex_path else 'None'}) ---")

            # Helper to set and verify
            def set_and_verify(node, param, value, is_node=False):
                val_to_set = value.path() if is_node else value
                node.set_param(param, val_to_set)
                actual = node.get_param_as_string(param)
                self.log_message(f"Set {node.name()}.{param} = '{val_to_set}' | Readback: '{actual}'")

            # 1. Find Key Nodes
            planet = tg.node_by_path("/Planet 01")
            if not planet:
                planet = tg.node_by_path("Planet 01") # Try without slash
            
            if not planet:
                planets = project.children_filtered_by_class("planet")
                if planets: 
                    planet = planets[0]
                    self.log_message(f"Found planet by class: {planet.path()}")

            compute_terrain = tg.node_by_path("/Compute Terrain")
            if not compute_terrain:
                compute_terrain = tg.node_by_path("Compute Terrain") # Try without slash

            if not compute_terrain:
                cts = project.children_filtered_by_class("compute_terrain")
                if cts: 
                    compute_terrain = cts[0]
                    self.log_message(f"Found Compute Terrain by class: {compute_terrain.path()}")

            # If still not found, create it
            if not compute_terrain:
                self.log_message("Compute Terrain not found. Attempting creation...")
                try:
                    # Create using generic create_child
                    new_node = tg.create_child(project, "compute_terrain")
                    if new_node:
                        new_node.set_param("name", "Compute Terrain")
                        compute_terrain = new_node
                        self.log_message(f"Created 'Compute Terrain' node: {compute_terrain.path()}")
                    else:
                        self.log_message("create_child returned None/False")
                except Exception as e:
                    self.log_message(f"Creation failed: {e}")

            # Final check: Scan all children for name "Compute Terrain" just in case
            if not compute_terrain:
                self.log_message("Scanning all root children for 'Compute Terrain'...")
                try:
                    for c in project.children():
                        if c.name() == "Compute Terrain" or c.path() == "/Compute Terrain":
                            compute_terrain = c
                            self.log_message(f"Found Compute Terrain by name scan: {c.path()}")
                            break
                except: pass

            if not planet:
                self.log_message("CRITICAL: Planet node not found. Listing all nodes:")
                try:
                    for c in project.children():
                        self.log_message(f" - {c.name()} ({c.path()})")
                except: pass
                messagebox.showerror("Error", "Could not find a Planet node. See log for available nodes.")
                return

            if not compute_terrain:
                self.log_message("CRITICAL: Compute Terrain node not found. Listing all nodes:")
                try:
                    for c in project.children():
                        self.log_message(f" - {c.name()} ({c.path()})")
                except: pass
                messagebox.showerror("Error", "Could not find Compute Terrain node. See log for available nodes.")
                return

            # Helper to find or create node
            def find_or_create(name, class_name):
                # Try exact path first
                node = tg.node_by_path(f"/{name}")
                if node: return node, True # Node, Existed
                
                # Try searching by name in children
                children = project.children_filtered_by_class(class_name)
                for c in children:
                    if c.name() == name:
                        return c, True
                
                # Create new
                node = tg.create_child(project, class_name)
                if node:
                    node.set_param("name", name)
                    return node, False # Node, Created
                return None, False

            # 2. Create/Update Heightfield Chain
            hf_load, hf_load_existed = find_or_create("Manual_HF_Load", "heightfield_load")
            if hf_path:
                set_and_verify(hf_load, "filename", hf_path)
            
            hf_shader, hf_shader_existed = find_or_create("Manual_HF_Shader", "heightfield_shader")
            set_and_verify(hf_shader, "heightfield", hf_load, is_node=True)
            
            # Connect to Compute Terrain (Only if not already connected)
            current_ct_input = compute_terrain.get_param_as_string("input_node")
            if current_ct_input != hf_shader.path():
                # Inject HF Shader
                if current_ct_input and current_ct_input != hf_shader.path():
                    set_and_verify(hf_shader, "input_node", current_ct_input)
                    self.log_message(f"Chained HF Shader -> Old Terrain Source ({current_ct_input})")
                
                set_and_verify(compute_terrain, "input_node", hf_shader, is_node=True)
                self.log_message("Connected Compute Terrain -> HF Shader")
            else:
                self.log_message("Compute Terrain already connected to HF Shader.")

            # 3. Create/Update Texture Chain
            surf_layer = None
            if tex_path:
                img_map, _ = find_or_create("Manual_Texture_Map", "image_map_shader")
                set_and_verify(img_map, "image_filename", tex_path)

                surf_layer, surf_layer_existed = find_or_create("Manual_Texture_Layer", "surface_layer")
                set_and_verify(surf_layer, "colour_function", img_map, is_node=True)
                self.log_message("Texture Nodes Ready")
            else:
                self.log_message("No texture selected.")

            # 4. Create/Update Fractal
            fractal, fractal_existed = find_or_create("Manual_Fractal", "power_fractal_shader_v3")
            
            # 5. Chain Surface Shaders
            # Check if Planet is already connected to our chain
            current_surf = planet.get_param_as_string("surface_shader")
            
            # Identify our top node
            top_node = surf_layer if surf_layer else fractal
            
            # SAFETY: Break potential loops before connecting
            # We want: Planet -> [Texture] -> Fractal -> [Previous]
            # So Fractal should NEVER input from Texture.
            if surf_layer and fractal:
                fractal_input = fractal.get_param_as_string("input_node")
                if fractal_input == surf_layer.path():
                    self.log_message("Breaking loop: Disconnecting Fractal from Texture Layer")
                    fractal.set_param("input_node", "") # Clear it temporarily

            # If Planet is already pointing to our top node, we assume the chain is fine (or we just updated files)
            if current_surf == top_node.path():
                self.log_message("Planet already connected to our chain. Updates applied.")
                
                # Ensure internal chain (Texture -> Fractal) is correct if we have texture
                if surf_layer:
                     set_and_verify(surf_layer, "input_node", fractal, is_node=True)
            else:
                # New connection needed
                self.log_message("Building new Surface Chain...")
                
                # Connect Fractal to whatever was previously on the planet
                # But ensure we don't connect to ourselves
                if current_surf:
                    is_self = False
                    if surf_layer and current_surf == surf_layer.path(): is_self = True
                    if current_surf == fractal.path(): is_self = True
                    
                    if not is_self:
                        set_and_verify(fractal, "input_node", current_surf)
                        self.log_message(f"Chained Fractal -> Previous Surface ({current_surf})")
                
                # Connect Texture -> Fractal
                if surf_layer:
                    set_and_verify(surf_layer, "input_node", fractal, is_node=True)
                
                # Connect Planet -> Top Node
                set_and_verify(planet, "surface_shader", top_node, is_node=True)
                self.log_message(f"Connected Planet -> {top_node.name()}")

            messagebox.showinfo("Success", "Terragen updated successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create nodes: {e}")

    def select_manual_hf(self):
        filename = filedialog.askopenfilename(title="Select Heightfield", filetypes=[("Images", "*.png *.jpg *.tif *.exr")])
        if filename:
            self.manual_hf_path = filename
            self.log_message(f"Manual HF: {os.path.basename(filename)}")
            self.check_manual_ready()
            
            # Update Preview
            try:
                img = Image.open(filename)
                img.thumbnail((100, 100))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.hf_preview_lbl.configure(image=ctk_img, text="")
            except Exception as e:
                print(f"Error previewing HF: {e}")

            # Try to update Terragen immediately if node exists
            try:
                import terragen_rpc as tg
                project = tg.root()
                if project:
                    # Look for our specific node name
                    # Note: Terragen might rename duplicates (e.g. Manual_HF_Load_1), so this finds the first match or exact match
                    # We'll try to find the one we likely created.
                    # For now, let's search for "Manual_HF_Load"
                    hf_load = tg.node_by_path("/Manual_HF_Load")
                    if not hf_load:
                        # Try searching children if path lookup fails (sometimes reliable)
                        loads = project.children_filtered_by_class("heightfield_load")
                        for node in loads:
                            if node.name().startswith("Manual_HF_Load"):
                                hf_load = node
                                break
                    
                    if hf_load:
                        hf_load.set_param("filename", filename)
                        self.log_message(f"Updated Terragen node '{hf_load.name()}' with new file.")
            except Exception as e:
                print(f"Auto-update failed (Terragen might not be running): {e}")

    def select_manual_tex(self):
        filename = filedialog.askopenfilename(title="Select Texture", filetypes=[("Images", "*.png *.jpg *.tif")])
        if filename:
            self.manual_tex_path = filename
            self.log_message(f"Manual Texture: {os.path.basename(filename)}")
            self.check_manual_ready()
            
            # Update Preview
            try:
                img = Image.open(filename)
                img.thumbnail((100, 100))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.tex_preview_lbl.configure(image=ctk_img, text="")
            except Exception as e:
                print(f"Error previewing Texture: {e}")

            # Try to update Terragen immediately if node exists
            try:
                import terragen_rpc as tg
                project = tg.root()
                if project:
                    img_map = tg.node_by_path("/Manual_Texture_Map")
                    if not img_map:
                        maps = project.children_filtered_by_class("image_map_shader")
                        for node in maps:
                            if node.name().startswith("Manual_Texture_Map"):
                                img_map = node
                                break
                    
                    if img_map:
                        img_map.set_param("image_filename", filename)
                        self.log_message(f"Updated Terragen node '{img_map.name()}' with new file.")
            except Exception as e:
                print(f"Auto-update failed: {e}")

    def check_manual_ready(self):
        if self.manual_hf_path and self.manual_tex_path:
            self.send_tg_btn.configure(state="normal")

    def send_to_terragen(self):
        mode = self.source_selector.get()
        hf_path = None
        tex_path = None
        
        if mode == "Manual Files":
            hf_path = self.manual_hf_path
            tex_path = self.manual_tex_path
            if not hf_path and not tex_path:
                messagebox.showwarning("Warning", "Please select at least a Heightfield or Texture file.")
                return

        elif mode == "Generated Result":
            if not self.heightfield_path:
                messagebox.showwarning("Warning", "No generated heightfield available. Please generate one first.")
                return
            hf_path = self.heightfield_path
            
            # Try to get texture from last result
            if self.last_result and "generated_images" in self.last_result and self.last_result["generated_images"]:
                try:
                    # Save first image as texture
                    tex_path = os.path.abspath("generated_texture_temp.png")
                    self.last_result["generated_images"][0].save(tex_path)
                    self.log_message(f"Saved generated texture to {tex_path}")
                except Exception as e:
                    self.log_message(f"Failed to save generated texture: {e}")
            else:
                self.log_message("No generated texture found in results.")

        elif mode == "Uploaded Images":
            # Use generated HF if available, else manual
            if self.heightfield_path:
                hf_path = self.heightfield_path
            elif self.manual_hf_path:
                hf_path = self.manual_hf_path
            
            if self.image_paths:
                tex_path = self.image_paths[0]
            else:
                messagebox.showwarning("Warning", "No uploaded images found.")
                return

        # Validate paths
        if hf_path:
            hf_path = os.path.abspath(hf_path)
            if not os.path.exists(hf_path):
                messagebox.showerror("Error", f"Heightfield file not found:\n{hf_path}")
                return
        
        if tex_path:
            tex_path = os.path.abspath(tex_path)
            if not os.path.exists(tex_path):
                messagebox.showerror("Error", f"Texture file not found:\n{tex_path}")
                return

        self.deploy_to_terragen(hf_path, tex_path)

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.status_label.configure(text=message)

    def upload_images(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        filenames = filedialog.askopenfilenames(title="Select Reference Images", filetypes=filetypes)
        if filenames:
            self.image_paths = list(filenames)
            self.display_uploaded_images()
            self.generate_btn.configure(state="normal")
            self.gen_hf_btn.configure(state="normal")
            self.log_message(f"{len(self.image_paths)} images selected.")

    def select_heightfield(self):
        filetypes = (("Heightfield files", "*.ter *.tif *.exr *.png *.jpg"), ("All files", "*.*"))
        filename = filedialog.askopenfilename(title="Select Heightfield Image", filetypes=filetypes)
        if filename:
            self.heightfield_path = filename
            self.log_message(f"Selected Heightfield: {os.path.basename(filename)}")
            self.generate_btn.configure(state="normal")

    def display_uploaded_images(self):
        for widget in self.images_frame.winfo_children():
            widget.destroy()
        
        for i, img_path in enumerate(self.image_paths):
            try:
                # Container for image and close button
                container = ctk.CTkFrame(self.images_frame, fg_color="transparent")
                container.pack(side="left", padx=5, pady=5)

                img = Image.open(img_path)
                img.thumbnail((100, 100))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                
                # Image Label
                label = ctk.CTkLabel(container, image=ctk_img, text="")
                label.pack(side="top")
                
                # Remove Button (Tiny X)
                remove_btn = ctk.CTkButton(container, text="✕", width=20, height=20, 
                                         fg_color="#ff4444", hover_color="#cc0000",
                                         font=ctk.CTkFont(size=10, weight="bold"),
                                         command=lambda idx=i: self.remove_image(idx))
                remove_btn.pack(side="top", pady=2)
                
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

    def remove_image(self, index):
        if 0 <= index < len(self.image_paths):
            removed = self.image_paths.pop(index)
            self.log_message(f"Removed image: {os.path.basename(removed)}")
            self.display_uploaded_images()
            
            # Update button states if list is empty
            if not self.image_paths:
                self.generate_btn.configure(state="disabled")
                self.gen_hf_btn.configure(state="disabled")

    def start_heightfield_generation(self):
        self.log_message("Starting Heightfield Generation...")
        self.gen_hf_btn.configure(state="disabled")
        thread = threading.Thread(target=self.process_heightfield_generation)
        thread.start()

    def process_heightfield_generation(self):
        try:
            callback = lambda msg: self.after(0, self.log_message, msg)
            script_code = self.api.generate_heightmap_script(self.image_paths, status_callback=callback)
            
            if not script_code:
                raise Exception("Failed to generate heightmap script.")

            # Save script to file
            script_path = os.path.abspath("generate_hf.py")
            with open(script_path, "w") as f:
                f.write(script_code)
            
            self.after(0, self.log_message, f"Executing script: {script_path}")
            
            # Execute script using current python interpreter
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
            
            # Log output
            if result.stdout: print(f"Script STDOUT: {result.stdout}")
            if result.stderr: print(f"Script STDERR: {result.stderr}")

            if result.returncode != 0:
                raise Exception(f"Script execution failed: {result.stderr}")
            
            self.after(0, self.log_message, "Heightmap generation script finished.")
            
            # Rename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_output = "generated_heightmap.png"
            
            # Ensure we look in the same dir as the script
            if not os.path.exists(default_output):
                default_output = os.path.abspath(default_output)

            if not os.path.exists(default_output):
                # Debug info
                cwd = os.getcwd()
                files = os.listdir(cwd)
                print(f"CWD: {cwd}")
                print(f"Files: {files}")
                raise Exception(f"Output file {default_output} not found. Check console for details.")

            new_filename = f"generated_heightmap_{timestamp}.png"
            hf_path = os.path.abspath(new_filename)
            
            os.rename(default_output, hf_path)

            self.heightfield_path = hf_path
            
            def update_ui():
                self.log_message(f"Heightfield set to: {os.path.basename(hf_path)}")
                self.gen_hf_btn.configure(state="normal")
                
                # Display the generated heightmap
                try:
                    img = Image.open(hf_path)
                    img.thumbnail((300, 300))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    
                    # Clear previous results to show this new one
                    for widget in self.results_frame.winfo_children():
                        widget.destroy()
                        
                    lbl = ctk.CTkLabel(self.results_frame, text=f"Generated Heightfield\n{os.path.basename(hf_path)}", font=ctk.CTkFont(weight="bold"))
                    lbl.pack(pady=5)
                    
                    img_lbl = ctk.CTkLabel(self.results_frame, image=ctk_img, text="")
                    img_lbl.pack(pady=10)
                    
                except Exception as e:
                    print(f"Error displaying heightmap: {e}")

            self.after(0, update_ui)

        except Exception as e:
            self.after(0, self.show_error, str(e))
            self.after(0, lambda: self.gen_hf_btn.configure(state="normal"))

    def start_generation(self):
        self.log_message("Starting generation process...")
        self.generate_btn.configure(state="disabled")
        
        # Run in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.process_generation)
        thread.start()

    def process_generation(self):
        try:
            # This is where we call the API
            # We pass a lambda that uses after() to ensure UI updates happen on the main thread
            callback = lambda msg: self.after(0, self.log_message, msg)
            result = self.api.generate_terrain(self.image_paths, heightfield_path=self.heightfield_path, status_callback=callback)
            self.after(0, self.display_results, result)
        except Exception as e:
            self.after(0, self.show_error, str(e))

    def display_results(self, result):
        self.last_result = result
        self.log_message("Generation Complete.")
        self.generate_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Display Generated Images
        if "generated_images" in result and result["generated_images"]:
            img_frame = ctk.CTkFrame(self.results_frame)
            img_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(img_frame, text="Generated Maps", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            
            for i, img in enumerate(result["generated_images"]):
                try:
                    # Resize for display
                    display_img = img.copy()
                    display_img.thumbnail((300, 300))
                    ctk_img = ctk.CTkImage(light_image=display_img, dark_image=display_img, size=display_img.size)
                    
                    lbl = ctk.CTkLabel(img_frame, image=ctk_img, text="")
                    lbl.pack(side="left", padx=10, pady=10)
                    
                    # Save button
                    def save_img(image=img, index=i):
                        filename = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
                        if filename:
                            image.save(filename)
                            messagebox.showinfo("Saved", f"Image saved to {filename}")

                    btn = ctk.CTkButton(img_frame, text=f"Save Map {i+1}", command=save_img)
                    btn.pack(side="left", padx=5)
                    
                except Exception as e:
                    print(f"Error displaying image: {e}")

        # Display Atmosphere Settings
        if "atmosphere" in result and result["atmosphere"]:
            atm_frame = ctk.CTkFrame(self.results_frame)
            atm_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(atm_frame, text="Atmosphere Settings", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            
            atm_text = ctk.CTkTextbox(atm_frame, height=150)
            atm_text.pack(fill="x", padx=10, pady=5)
            atm_text.insert("0.0", str(result["atmosphere"]))
            atm_text.configure(state="disabled")

        # Display Height Map Info
        hm_frame = ctk.CTkFrame(self.results_frame)
        hm_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(hm_frame, text="Terrain Description", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        if "height_map_text" in result:
             lbl = ctk.CTkLabel(hm_frame, text=result["height_map_text"], wraplength=600, justify="left")
             lbl.pack(padx=10, pady=5)

        # Display Terragen RPC Code
        if "terragen_rpc_code" in result and result["terragen_rpc_code"]:
            code_frame = ctk.CTkFrame(self.results_frame)
            code_frame.pack(fill="both", expand=True, pady=10)
            
            header_frame = ctk.CTkFrame(code_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Terragen Script", font=ctk.CTkFont(weight="bold")).pack(side="left")
            
            def run_script():
                code = result["terragen_rpc_code"]
                try:
                    # Execute the code in a new thread to avoid freezing UI
                    def execute():
                        try:
                            exec(code, {"__name__": "__main__"})
                            self.after(0, lambda: messagebox.showinfo("Success", "Script executed successfully! Check Terragen."))
                        except Exception as e:
                            error_msg = str(e)
                            print(f"Script Execution Error: {error_msg}")
                            self.after(0, lambda: messagebox.showerror("Execution Error", error_msg))
                    
                    threading.Thread(target=execute).start()
                except Exception as e:
                    messagebox.showerror("Error", str(e))

            ctk.CTkButton(header_frame, text="Run in Terragen", fg_color="green", hover_color="darkgreen", command=run_script).pack(side="right")
            
            code_box = ctk.CTkTextbox(code_frame, height=300, font=("Courier", 12))
            code_box.pack(fill="both", expand=True, padx=10, pady=5)
            code_box.insert("0.0", result["terragen_rpc_code"])

    def save_project(self):
        if not self.last_result:
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                # Filter out non-serializable objects (like PIL images) if any
                save_data = {k: v for k, v in self.last_result.items() if k != "generated_images"}
                with open(filename, 'w') as f:
                    json.dump(save_data, f, indent=4)
                messagebox.showinfo("Saved", f"Project saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {e}")

    def load_project(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.display_results(data)
                self.log_message(f"Loaded project from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {e}")

    def show_error(self, message):
        self.status_label.configure(text="Error occurred.")
        self.generate_btn.configure(state="normal")
        messagebox.showerror("Error", message)

    def quit_app(self):
        self.destroy()

    def open_youtube(self):
        webbrowser.open("https://www.youtube.com/@geekatplay")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = TerrainApp()
    app.mainloop()
