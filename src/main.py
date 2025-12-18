import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import sys
import threading
    def create_cloud_node(self):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project:
                messagebox.showerror("Error", "Could not connect to Terragen.")
                return

            def find_atmos():
                atmos = tg.node_by_path("/Atmosphere 01") or tg.node_by_path("Atmosphere 01")
                if atmos:
                    return atmos
                atmos_nodes = project.children_filtered_by_class("atmosphere")
                return atmos_nodes[0] if atmos_nodes else None

            def link_to_atmosphere(cloud_node):
                atmos = find_atmos()
                if not atmos:
                    self.log_message("Atmosphere node not found; cannot connect cloud.")
                    return
                link_params = ["cloud_shader", "clouds", "cloud_layer", "primary_cloud"]
                for param in link_params:
                    try:
                        current = atmos.get_param_as_string(param)
                    except Exception:
                        continue
                    if current != cloud_node.path():
                        atmos.set_param(param, cloud_node.path())
                        actual = atmos.get_param_as_string(param)
                        self.log_message(f"Connected {cloud_node.name()} -> {atmos.name()} via '{param}' (set '{cloud_node.path()}', readback '{actual}')")
                        return
                self.log_message("Could not set cloud link on Atmosphere (no matching params).")

            # Gather existing cloud chain
            existing = []
            for cls in ("easy_cloud", "cloud_layer_v3"):
                try:
                    for c in project.children_filtered_by_class(cls):
                        if c.name().startswith("AI_Cloud_Layer"):
                            existing.append(c)
                except Exception:
                    pass

            def suffix(n):
                try:
                    return int(n.split("_")[-1])
                except Exception:
                    return 0

            existing.sort(key=lambda n: suffix(n.name()))
            next_idx = suffix(existing[-1].name()) + 1 if existing else 1
            name = f"AI_Cloud_Layer_{next_idx:02d}"

            # Create new cloud node
            node = tg.create_child(project, "easy_cloud")
            if not node:
                node = tg.create_child(project, "cloud_layer_v3")
            if not node:
                messagebox.showerror("Error", "Failed to create cloud node (Easy Cloud / Cloud Layer V3).")
                return

            node.set_param("name", name)

            # Chain to previous cloud if any
            if existing:
                prev = existing[-1]
                for param in ("input_node", "main_input", "input"):
                    try:
                        node.set_param(param, prev.path())
                        actual = node.get_param_as_string(param)
                        self.log_message(f"Chained {name} -> {prev.name()} via '{param}' (set '{prev.path()}', readback '{actual}')")
                        break
                    except Exception:
                        continue
            else:
                self.log_message("First cloud in chain; no previous cloud to link.")

            link_to_atmosphere(node)
            self.log_message(f"Created Terragen cloud node: {node.path()}")
            messagebox.showinfo("Success", f"Created cloud node: {node.name()}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create cloud node: {e}")
        self.sky_frame = ctk.CTkFrame(self.main_frame)
        self.sky_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.sky_frame, text="Sky and Clouds Reference", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        btn_bar = ctk.CTkFrame(self.sky_frame, fg_color="transparent")
        btn_bar.pack(fill="x", padx=10, pady=5)

        self.upload_sky_btn = ctk.CTkButton(btn_bar, text="Upload Sky/Cloud Image", command=self.upload_sky_reference)
        self.upload_sky_btn.pack(side="left", padx=5)

        self.analyze_sky_btn = ctk.CTkButton(btn_bar, text="Analyze Atmosphere", fg_color="#0066cc", hover_color="#004b99", state="disabled", command=self.start_sky_analysis)
        self.analyze_sky_btn.pack(side="left", padx=5)

        self.add_cloud_btn = ctk.CTkButton(btn_bar, text="Add Cloud Node in Terragen", fg_color="#228b22", hover_color="#176617", command=self.create_cloud_node)
        self.add_cloud_btn.pack(side="left", padx=5)

        self.sync_sun_btn = ctk.CTkButton(btn_bar, text="Sync Sunlight to Analysis", fg_color="#cc8800", hover_color="#a86d00", command=self.start_sync_sun)
        self.sync_sun_btn.pack(side="left", padx=5)

        preview_bar = ctk.CTkFrame(self.sky_frame, fg_color="transparent")
        preview_bar.pack(fill="x", padx=10, pady=5)

        self.sky_preview_lbl = ctk.CTkLabel(preview_bar, text="No sky reference selected")
        self.sky_preview_lbl.pack(side="left", padx=5)

        self.sky_output = ctk.CTkTextbox(self.sky_frame, height=140)
        self.sky_output.pack(fill="x", padx=10, pady=(5, 10))
        self.sky_output.configure(state="disabled")

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
            
            # Use generated texture if available
            if hasattr(self, 'generated_texture_path') and self.generated_texture_path:
                tex_path = self.generated_texture_path
            else:
                self.log_message("No generated texture found.")

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

    def upload_sky_reference(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        filename = filedialog.askopenfilename(title="Select Sky/Cloud Reference", filetypes=filetypes)
        if filename:
            self.sky_image_path = filename
            self.analyze_sky_btn.configure(state="normal")
            self.log_message(f"Sky reference: {os.path.basename(filename)}")

            try:
                img = Image.open(filename)
                img.thumbnail((160, 160))
                self.sky_preview_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.sky_preview_lbl.configure(image=self.sky_preview_img, text="")
            except Exception as e:
                print(f"Error previewing sky reference: {e}")

    def start_sky_analysis(self):
        if not self.sky_image_path:
            messagebox.showwarning("Warning", "Please select a sky/cloud reference image first.")
            return
        self.analyze_sky_btn.configure(state="disabled")
        self.log_message("Analyzing sky reference...")
        thread = threading.Thread(target=self.process_sky_analysis)
        thread.start()

    def process_sky_analysis(self):
        try:
            callback = lambda msg: self.after(0, self.log_message, msg)
            result = self.api.analyze_atmosphere(self.sky_image_path, status_callback=callback)

            def update_ui():
                self.sky_output.configure(state="normal")
                self.sky_output.delete("1.0", "end")
                self.sky_output.insert("end", result)
                self.sky_output.configure(state="disabled")
                self.log_message("Sky analysis complete.")
                self.analyze_sky_btn.configure(state="normal")

            self.after(0, update_ui)

        except Exception as e:
            self.after(0, self.show_error, str(e))
            self.after(0, lambda: self.analyze_sky_btn.configure(state="normal"))

    def create_cloud_node(self):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project:
                messagebox.showerror("Error", "Could not connect to Terragen.")
                return

            name = "AI_Cloud_Layer"
            # Helper: connect cloud to Atmosphere node
            def connect_to_atmosphere(cloud_node):
                try:
                    atmos = tg.node_by_path("/Atmosphere 01") or tg.node_by_path("Atmosphere 01")
                    if not atmos:
                        # fallback by class
                        atmos_nodes = project.children_filtered_by_class("atmosphere")
                        if atmos_nodes:
                            atmos = atmos_nodes[0]
                    if not atmos:
                        self.log_message("Atmosphere node not found; cannot connect cloud.")
                        return

                    # Attempt common parameter names for cloud attachment
                    candidates = ["cloud_shader", "clouds", "cloud_layer", "primary_cloud"]
                    for param in candidates:
                        try:
                            current = atmos.get_param_as_string(param)
                        except Exception:
                            continue

                        if current != cloud_node.path():
                            atmos.set_param(param, cloud_node.path())
                            actual = atmos.get_param_as_string(param)
                            self.log_message(f"Connected {cloud_node.name()} -> {atmos.name()} via '{param}' (set '{cloud_node.path()}', readback '{actual}')")
                            return
                    self.log_message("Could not set cloud link on Atmosphere (no matching params).")
                except Exception as e:
                    self.log_message(f"Failed to connect cloud to Atmosphere: {e}")

            # Try to find existing
            node = tg.node_by_path(f"/{name}")
            if not node:
                # Search by class for partial matches
                candidates = project.children_filtered_by_class("easy_cloud")
                for c in candidates:
                    if c.name().startswith(name):
                        node = c
                        break

            if node:
                self.log_message(f"Cloud node already exists: {node.path()}")
                connect_to_atmosphere(node)
                messagebox.showinfo("Info", f"Cloud node already exists: {node.name()}")
                return

            # Try creating Easy Cloud; fallback to Cloud Layer V3
            node = tg.create_child(project, "easy_cloud")
            if not node:
                node = tg.create_child(project, "cloud_layer_v3")

            if not node:
                messagebox.showerror("Error", "Failed to create cloud node (Easy Cloud / Cloud Layer V3).")
                return

            node.set_param("name", name)
            self.log_message(f"Created Terragen cloud node: {node.path()}")
            connect_to_atmosphere(node)
            messagebox.showinfo("Success", f"Created cloud node: {node.name()}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create cloud node: {e}")

    def start_sync_sun(self):
        if not self.sky_image_path:
            messagebox.showwarning("Warning", "Please select a sky/cloud reference image first.")
            return
        self.sync_sun_btn.configure(state="disabled")
        self.log_message("Syncing sun position to Terragen...")
        thread = threading.Thread(target=self.process_sync_sun)
        thread.start()

    def process_sync_sun(self):
        try:
            callback = lambda msg: self.after(0, self.log_message, msg)
            angles = self.api.analyze_sun_angles(self.sky_image_path, status_callback=callback)

            az = angles.get("sun_azimuth_deg")
            el = angles.get("sun_elevation_deg")
            if az is None or el is None:
                raise Exception("Sun analysis did not return azimuth/elevation.")

            # Apply to Terragen
            def apply():
                try:
                    import terragen_rpc as tg
                    project = tg.root()
                    if not project:
                        raise Exception("Could not connect to Terragen.")

                    # Find Sunlight node
                    sun = tg.node_by_path("/Sunlight 01") or tg.node_by_path("Sunlight 01")
                    if not sun:
                        # Search by class
                        suns = project.children_filtered_by_class("sunlight")
                        if suns:
                            sun = suns[0]

                    if not sun:
                        raise Exception("Sunlight node not found in Terragen.")

                    sun.set_param("heading", float(az))
                    sun.set_param("elevation", float(el))
                    self.log_message(f"Set Sunlight heading={az:.1f}°, elevation={el:.1f}°")
                    messagebox.showinfo("Success", f"Sunlight updated to heading {az:.1f}°, elevation {el:.1f}°")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update Sunlight: {e}")
                finally:
                    self.sync_sun_btn.configure(state="normal")

            self.after(0, apply)

        except Exception as e:
            self.after(0, self.show_error, str(e))
            self.after(0, lambda: self.sync_sun_btn.configure(state="normal"))

    def upload_images(self):
        filetypes = (("Image files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        filenames = filedialog.askopenfilenames(title="Select Reference Images", filetypes=filetypes)
        if filenames:
            self.image_paths = list(filenames)
            self.display_uploaded_images()
            self.gen_hf_btn.configure(state="normal")
            self.log_message(f"{len(self.image_paths)} images selected.")

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
                self.gen_hf_btn.configure(state="disabled")

    def start_heightfield_generation(self):
        self.log_message("Starting Heightfield Generation...")
        self.gen_hf_btn.configure(state="disabled")
        thread = threading.Thread(target=self.process_heightfield_generation)
        thread.start()

    def process_heightfield_generation(self):
        try:
            callback = lambda msg: self.after(0, self.log_message, msg)
            
            # Call API to generate images directly
            generate_texture = self.gen_texture_var.get()
            generated_images = self.api.generate_heightmap_images(self.image_paths, generate_texture=generate_texture, status_callback=callback)
            
            if not generated_images:
                raise Exception("No images were generated by the AI.")

            self.after(0, self.log_message, f"Received {len(generated_images)} images from AI.")
            
            # Create Output Directory
            output_dir = "highfield_output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.after(0, self.log_message, f"Created output directory: {output_dir}")

            # Save Images with Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Handle Single Image Response (Potential Side-by-Side)
            final_images = []
            if len(generated_images) == 1:
                img = generated_images[0]
                width, height = img.size
                # If width is significantly larger than height (e.g., > 1.8 aspect ratio), assume side-by-side
                if width > height * 1.5:
                    self.after(0, self.log_message, "Detected side-by-side image. Splitting...")
                    # Split into two
                    half_width = width // 2
                    hf_part = img.crop((0, 0, half_width, height))
                    tex_part = img.crop((half_width, 0, width, height))
                    final_images = [hf_part, tex_part]
                else:
                    final_images = [img]
            else:
                final_images = generated_images

            # Save Heightmap
            hf_img = final_images[0]
            hf_filename = f"generated_heightmap_{timestamp}.png"
            hf_path = os.path.abspath(os.path.join(output_dir, hf_filename))
            hf_img.save(hf_path)
            self.heightfield_path = hf_path
            
            tex_path = None
            if len(final_images) > 1:
                tex_img = final_images[1]
                tex_filename = f"generated_texture_{timestamp}.png"
                tex_path = os.path.abspath(os.path.join(output_dir, tex_filename))
                tex_img.save(tex_path)
                self.generated_texture_path = tex_path
            else:
                self.generated_texture_path = None

            def update_ui():
                self.log_message(f"Heightfield saved: {os.path.basename(hf_path)}")
                if tex_path:
                    self.log_message(f"Texture saved: {os.path.basename(tex_path)}")
                
                self.gen_hf_btn.configure(state="normal")
                
                # Clear previous results
                for widget in self.results_frame.winfo_children():
                    widget.destroy()

                # Display Heightmap
                try:
                    img = hf_img.copy()
                    img.thumbnail((300, 300))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    
                    hf_frame = ctk.CTkFrame(self.results_frame)
                    hf_frame.pack(side="left", padx=10, pady=10)
                    
                    lbl = ctk.CTkLabel(hf_frame, text=f"Heightfield\n{os.path.basename(hf_path)}", font=ctk.CTkFont(weight="bold"))
                    lbl.pack(pady=5)
                    
                    img_lbl = ctk.CTkLabel(hf_frame, image=ctk_img, text="")
                    img_lbl.pack(pady=10)
                except Exception as e:
                    print(f"Error displaying heightmap: {e}")

                # Display Texture
                if tex_path:
                    try:
                        img = Image.open(tex_path)
                        img.thumbnail((300, 300))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                        
                        tex_frame = ctk.CTkFrame(self.results_frame)
                        tex_frame.pack(side="left", padx=10, pady=10)
                        
                        lbl = ctk.CTkLabel(tex_frame, text=f"Texture\n{os.path.basename(tex_path)}", font=ctk.CTkFont(weight="bold"))
                        lbl.pack(pady=5)
                        
                        img_lbl = ctk.CTkLabel(tex_frame, image=ctk_img, text="")
                        img_lbl.pack(pady=10)
                    except Exception as e:
                        print(f"Error displaying texture: {e}")

            self.after(0, update_ui)

        except Exception as e:
            self.after(0, self.show_error, str(e))
            self.after(0, lambda: self.gen_hf_btn.configure(state="normal"))

    def show_error(self, message):
        self.status_label.configure(text="Error occurred.")
        messagebox.showerror("Error", message)

    def quit_app(self):
        self.destroy()

    def open_youtube(self):
        webbrowser.open("https://www.youtube.com/@geekatplay")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = TerrainApp()
    app.mainloop()
