import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import threading
import webbrowser
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

        self.upload_btn = ctk.CTkButton(self.sidebar_frame, text="Upload Reference Images", command=self.upload_images)
        self.upload_btn.grid(row=1, column=0, padx=20, pady=10)

        self.gen_texture_var = ctk.BooleanVar(value=True)
        self.gen_texture_chk = ctk.CTkCheckBox(self.sidebar_frame, text="Generate Texture", variable=self.gen_texture_var)
        self.gen_texture_chk.grid(row=2, column=0, padx=20, pady=10)

        self.gen_hf_btn = ctk.CTkButton(self.sidebar_frame, text="Generate Heightfield Images", fg_color="#800080", hover_color="#4b0082", command=self.start_heightfield_generation)
        self.gen_hf_btn.grid(row=3, column=0, padx=20, pady=10)
        self.gen_hf_btn.configure(state="disabled")

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
        self.generated_texture_path = None
        self.last_result = None
        self.sky_image_path = None
        self.sky_preview_img = None
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

        # --- Sky / Atmosphere Analysis ---
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

        debug_frame = ctk.CTkFrame(self.tools_frame, fg_color="transparent")
        debug_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(debug_frame, text="Read Node Structure", command=self.read_node_structure).pack(side="left", padx=5)

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
                if not project:
                    raise Exception("No project")
            except Exception:
                messagebox.showerror("Error", "Could not connect to Terragen.")
                return

            self.log_message("--- Reading Terragen Node Structure ---")
            
            children = project.children()
            self.log_message(f"Root Children ({len(children)}):")
            for child in children:
                self.log_message(f" - {child.name()} ({child.path()}) [Class: {child.path().split('/')[-1]}]")

            planet = tg.node_by_path("/Planet 01")
            if planet:
                self.log_message("\n--- Planet 01 Details ---")
                surf_shader = planet.get_param_as_string("surface_shader")
                self.log_message(f"Surface Shader Input: '{surf_shader}'")
            else:
                self.log_message("\nWARNING: Planet 01 not found!")

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

            def set_and_verify(node, param, value, is_node=False):
                val_to_set = value.path() if is_node else value
                node.set_param(param, val_to_set)
                actual = node.get_param_as_string(param)
                self.log_message(f"Set {node.name()}.{param} = '{val_to_set}' | Readback: '{actual}'")

            planet = tg.node_by_path("/Planet 01")
            if not planet:
                planet = tg.node_by_path("Planet 01")
            if not planet:
                planets = project.children_filtered_by_class("planet")
                if planets:
                    planet = planets[0]
                    self.log_message(f"Found planet by class: {planet.path()}")

            compute_terrain = tg.node_by_path("/Compute Terrain")
            if not compute_terrain:
                compute_terrain = tg.node_by_path("Compute Terrain")
            if not compute_terrain:
                cts = project.children_filtered_by_class("compute_terrain")
                if cts:
                    compute_terrain = cts[0]
                    self.log_message(f"Found Compute Terrain by class: {compute_terrain.path()}")

            if not compute_terrain:
                self.log_message("Compute Terrain not found. Attempting creation...")
                try:
                    new_node = tg.create_child(project, "compute_terrain")
                    if new_node:
                        new_node.set_param("name", "Compute Terrain")
                        compute_terrain = new_node
                        self.log_message(f"Created 'Compute Terrain' node: {compute_terrain.path()}")
                    else:
                        self.log_message("create_child returned None/False")
                except Exception as e:
                    self.log_message(f"Creation failed: {e}")

            if not compute_terrain:
                self.log_message("Scanning all root children for 'Compute Terrain'...")
                try:
                    for c in project.children():
                        if c.name() == "Compute Terrain" or c.path() == "/Compute Terrain":
                            compute_terrain = c
                            self.log_message(f"Found Compute Terrain by name scan: {c.path()}")
                            break
                except Exception:
                    pass

            if not planet:
                self.log_message("CRITICAL: Planet node not found. Listing all nodes:")
                try:
                    for c in project.children():
                        self.log_message(f" - {c.name()} ({c.path()})")
                except Exception:
                    pass
                messagebox.showerror("Error", "Could not find a Planet node. See log for available nodes.")
                return

            if not compute_terrain:
                self.log_message("CRITICAL: Compute Terrain node not found. Listing all nodes:")
                try:
                    for c in project.children():
                        self.log_message(f" - {c.name()} ({c.path()})")
                except Exception:
                    pass
                messagebox.showerror("Error", "Could not find Compute Terrain node. See log for available nodes.")
                return

            def find_or_create(name, class_name):
                node = tg.node_by_path(f"/{name}")
                if node:
                    return node, True
                children = project.children_filtered_by_class(class_name)
                for c in children:
                    if c.name() == name:
                        return c, True
                node = tg.create_child(project, class_name)
                if node:
                    node.set_param("name", name)
                    return node, False
                return None, False

            hf_load, _ = find_or_create("Manual_HF_Load", "heightfield_load")
            if hf_path:
                set_and_verify(hf_load, "filename", hf_path)
            
            hf_shader, _ = find_or_create("Manual_HF_Shader", "heightfield_shader")
            set_and_verify(hf_shader, "heightfield", hf_load, is_node=True)
            
            current_ct_input = compute_terrain.get_param_as_string("input_node")
            if current_ct_input != hf_shader.path():
                if current_ct_input and current_ct_input != hf_shader.path():
                    set_and_verify(hf_shader, "input_node", current_ct_input)
                    self.log_message(f"Chained HF Shader -> Old Terrain Source ({current_ct_input})")
                set_and_verify(compute_terrain, "input_node", hf_shader, is_node=True)
                self.log_message("Connected Compute Terrain -> HF Shader")
            else:
                self.log_message("Compute Terrain already connected to HF Shader")

            if tex_path:
                surf_shader, _ = find_or_create("Manual_Surface", "default_shader")
                set_and_verify(surf_shader, "input_node", compute_terrain, is_node=True)
                set_and_verify(surf_shader, "color_function_input", tex_path)
                set_and_verify(planet, "surface_shader", surf_shader, is_node=True)
                self.log_message("Connected Planet surface -> Manual_Surface shader")
            else:
                set_and_verify(planet, "surface_shader", compute_terrain, is_node=True)
                self.log_message("Connected Planet surface -> Compute Terrain")

            self.log_message("--- Deploy complete ---")
            messagebox.showinfo("Success", "Files sent to Terragen.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send to Terragen: {e}")

    def upload_images(self):
        files = filedialog.askopenfilenames(title="Select Reference Images", filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")])
        if files:
            self.image_paths = list(files)
            self.status_label.configure(text=f"Selected {len(files)} reference images.")
            self.gen_hf_btn.configure(state="normal")
            self.update_image_previews()

    def update_image_previews(self):
        for widget in self.images_frame.winfo_children():
            widget.destroy()

        for idx, path in enumerate(self.image_paths):
            img = ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=(150, 150))
            label = ctk.CTkLabel(self.images_frame, image=img, text=f"Reference {idx + 1}")
            label.image = img
            label.pack(side="left", padx=10, pady=10)

    def start_heightfield_generation(self):
        thread = threading.Thread(target=self.generate_heightfield)
        thread.daemon = True
        thread.start()

    def generate_heightfield(self):
        if not self.image_paths:
            messagebox.showerror("Error", "Please upload reference images first.")
            return

        self.status_label.configure(text="Generating heightfields and texture...")
        self.log_message("Starting generation using uploaded reference images...")

        try:
            result = self.api.generate_heightfield(self.image_paths, self.gen_texture_var.get())
            self.last_result = result

            self.heightfield_path = result.get("heightfield_path")
            self.generated_texture_path = result.get("texture_path")

            self.update_result_previews()
            self.status_label.configure(text="Generation complete.")
            self.log_message("Generation completed successfully.")
        except Exception as e:
            self.status_label.configure(text="Generation failed.")
            messagebox.showerror("Error", f"Failed to generate heightfields: {e}")
            self.log_message(f"Error during generation: {e}")

    def update_result_previews(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if self.heightfield_path:
            img = ctk.CTkImage(light_image=Image.open(self.heightfield_path), dark_image=Image.open(self.heightfield_path), size=(300, 300))
            label = ctk.CTkLabel(self.results_frame, image=img, text="Heightfield")
            label.image = img
            label.pack(side="left", padx=10, pady=10)

        if self.generated_texture_path:
            img = ctk.CTkImage(light_image=Image.open(self.generated_texture_path), dark_image=Image.open(self.generated_texture_path), size=(300, 300))
            label = ctk.CTkLabel(self.results_frame, image=img, text="Texture")
            label.image = img
            label.pack(side="left", padx=10, pady=10)

    def log_message(self, message):
        self.log_textbox.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def quit_app(self):
        self.destroy()

    def select_manual_hf(self):
        path = filedialog.askopenfilename(title="Select Heightfield File", filetypes=[("Image files", "*.png *.exr *.tif *.tiff"), ("All files", "*.*")])
        if path:
            self.manual_hf_path = path
            self.hf_preview_lbl.configure(text=os.path.basename(path))

    def select_manual_tex(self):
        path = filedialog.askopenfilename(title="Select Texture File", filetypes=[("Image files", "*.png *.jpg *.jpeg *.tif *.tiff"), ("All files", "*.*")])
        if path:
            self.manual_tex_path = path
            self.tex_preview_lbl.configure(text=os.path.basename(path))

    def send_to_terragen(self):
        source = self.source_selector.get()
        hf_path = None
        tex_path = None

        if source == "Manual Files":
            hf_path = self.manual_hf_path
            tex_path = self.manual_tex_path
        elif source == "Generated Result" and self.last_result:
            hf_path = self.heightfield_path
            tex_path = self.generated_texture_path
        elif source == "Uploaded Images" and self.image_paths:
            hf_path = self.image_paths[0]
            tex_path = self.image_paths[1] if len(self.image_paths) > 1 else None

        if not hf_path:
            messagebox.showerror("Error", "No heightfield selected or available.")
            return

        self.deploy_to_terragen(hf_path, tex_path)

    def upload_sky_reference(self):
        path = filedialog.askopenfilename(title="Select Sky Image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")])
        if not path:
            return
        self.sky_image_path = path
        img = ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=(200, 120))
        self.sky_preview_img = img
        self.sky_preview_lbl.configure(text=os.path.basename(path), image=img, compound="top")
        self.analyze_sky_btn.configure(state="normal")

    def start_sky_analysis(self):
        if not self.sky_image_path:
            messagebox.showerror("Error", "Select a sky image first.")
            return
        thread = threading.Thread(target=self.analyze_sky)
        thread.daemon = True
        thread.start()

    def analyze_sky(self):
        self.log_message("Analyzing atmosphere and clouds...")
        try:
            summary = self.api.analyze_atmosphere(self.sky_image_path)
            self.sky_output.configure(state="normal")
            self.sky_output.delete("1.0", "end")
            self.sky_output.insert("end", summary)
            self.sky_output.configure(state="disabled")
            self.log_message("Atmosphere analysis complete.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze atmosphere: {e}")
            self.log_message(f"Sky analysis failed: {e}")

    def create_cloud_node(self):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project:
                messagebox.showerror("Error", "Terragen not connected.")
                return

            self.log_message("Creating or chaining cloud node to Atmosphere...")

            atmosphere = tg.node_by_path("/Atmosphere 01") or tg.node_by_path("Atmosphere 01")
            if not atmosphere:
                atmospheres = project.children_filtered_by_class("atmosphere")
                atmosphere = atmospheres[0] if atmospheres else None
            if not atmosphere:
                messagebox.showerror("Error", "Atmosphere node not found.")
                return

            clouds = project.children_filtered_by_class("cloud_layer")
            if not clouds:
                # Log what Terragen thinks exists to help debugging class name mismatches
                all_classes = [c.path().split("/")[-1] for c in project.children()]
                self.log_message(f"No cloud_layer nodes found. Root child classes: {all_classes}")

            base_name = "AI Cloud"
            idx = 1
            existing_names = {c.name() for c in clouds}
            while f"{base_name} {idx}" in existing_names:
                idx += 1
            new_name = f"{base_name} {idx}"

            # Try known cloud class names in order
            new_cloud = None
            for cloud_class in ("cloud_layer", "cloud_layer_v3", "cloud_layer_v2"):
                try:
                    new_cloud = tg.create_child(project, cloud_class)
                    if new_cloud:
                        self.log_message(f"Created cloud using class '{cloud_class}'")
                        break
                except Exception as create_err:
                    self.log_message(f"Create attempt failed for class '{cloud_class}': {create_err}")

            if not new_cloud:
                messagebox.showerror(
                    "Error",
                    "Failed to create cloud layer via RPC. Check Terragen is unlocked and RPC allows create_child for cloud_layer/cloud_layer_v3.",
                )
                return

            new_cloud.set_param("name", new_name)
            new_cloud.set_param("cloud_depth", 3000)
            new_cloud.set_param("cloud_altitude", 5000)

            if clouds:
                last_cloud = clouds[-1]
                new_cloud.set_param("input_node", last_cloud.path())
                self.log_message(f"Chained {new_name} to {last_cloud.name()}")
            else:
                new_cloud.set_param("input_node", atmosphere.path())
                self.log_message(f"Attached {new_name} to Atmosphere 01")

            atmosphere.set_param("input_node", new_cloud.path())
            self.log_message(f"Linked Atmosphere input to {new_name}")
            messagebox.showinfo("Success", f"Created cloud layer: {new_name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create cloud node: {e}")
            self.log_message(f"Cloud node creation failed: {e}")

    def start_sync_sun(self):
        if not self.sky_image_path:
            messagebox.showerror("Error", "Select a sky image first.")
            return
        thread = threading.Thread(target=self.sync_sun_from_image)
        thread.daemon = True
        thread.start()

    def sync_sun_from_image(self):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project:
                messagebox.showerror("Error", "Terragen not connected.")
                return

            self.log_message("Analyzing sun angles from sky image...")
            sun_data = self.api.analyze_sun_angles(self.sky_image_path)
            az = sun_data.get("azimuth")
            el = sun_data.get("elevation")
            self.log_message(f"Sun angles -> Azimuth: {az}, Elevation: {el}")

            sun_node = tg.node_by_path("/Sunlight 01") or tg.node_by_path("Sunlight 01")
            if not sun_node:
                suns = project.children_filtered_by_class("sun")
                sun_node = suns[0] if suns else None
            if not sun_node:
                messagebox.showerror("Error", "Sunlight node not found.")
                return

            if az is not None:
                sun_node.set_param("heading", float(az))
            if el is not None:
                sun_node.set_param("elevation", float(el))

            self.log_message("Sunlight synced to analysis angles.")
            messagebox.showinfo("Success", "Sunlight updated from sky analysis.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sync sun: {e}")
            self.log_message(f"Sun sync failed: {e}")

    def open_youtube(self):
        webbrowser.open("https://youtube.com/@geekatplay")


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = TerrainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
