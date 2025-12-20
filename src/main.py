import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import json
import threading
import webbrowser
import platform
from datetime import datetime
from dotenv import load_dotenv
from api_handler import TerrainGeneratorAPI

APP_VERSION = "0.1.0"

load_dotenv()


class TerrainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.os_profile = self._detect_os_profile()

        self.title("Terrain AI Generator")
        self.geometry("1000x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(1, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Terrain AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        version_text = f"Build {APP_VERSION}\nOS: {self._friendly_os_name()}"
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text=version_text, font=ctk.CTkFont(size=12))
        self.version_label.grid(row=0, column=1, padx=5, pady=(20, 10), sticky="e")

        self.upload_btn = ctk.CTkButton(self.sidebar_frame, text="Upload Reference Images", command=self.upload_images)
        self.upload_btn.grid(row=1, column=0, padx=20, pady=10)

        self.gen_texture_var = ctk.BooleanVar(value=True)
        self.gen_texture_chk = ctk.CTkCheckBox(self.sidebar_frame, text="Generate Texture", variable=self.gen_texture_var)
        self.gen_texture_chk.grid(row=2, column=0, padx=20, pady=10)

        self.gen_hf_btn = ctk.CTkButton(self.sidebar_frame, text="Generate Heightfield Images", fg_color="#800080", hover_color="#4b0082", command=self.start_heightfield_generation)
        self.gen_hf_btn.grid(row=3, column=0, padx=20, pady=10)
        self.gen_hf_btn.configure(state="disabled")

        self.settings_btn = ctk.CTkButton(self.sidebar_frame, text="Settings", fg_color="gray", hover_color="gray30", command=self.open_settings)
        self.settings_btn.grid(row=6, column=0, padx=20, pady=10)

        self.quit_btn = ctk.CTkButton(self.sidebar_frame, text="Quit", fg_color="red", hover_color="darkred", command=self.quit_app)
        self.quit_btn.grid(row=7, column=0, padx=20, pady=10)

        self.footer_label = ctk.CTkLabel(self.sidebar_frame, text="Created by\nGeekatplay Studio", font=ctk.CTkFont(size=12))
        self.footer_label.grid(row=8, column=0, padx=20, pady=(20, 0))
        
        self.youtube_btn = ctk.CTkButton(self.sidebar_frame, text="Tutorials: @geekatplay", fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"), command=self.open_youtube)
        self.youtube_btn.grid(row=9, column=0, padx=20, pady=(5, 20))

        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.log_frame = ctk.CTkFrame(self, corner_radius=0)
        self.log_frame.grid(row=1, column=1, sticky="nsew")

        self.image_paths = []
        self.heightfield_path = None
        self.generated_texture_path = None
        self.last_result = None
        self.sky_image_path = None
        self.sky_preview_img = None
        self.last_analysis_data = None  # Cache for analysis JSON
        self.api = TerrainGeneratorAPI()
        self.is_generating = False

        self.status_label = ctk.CTkLabel(self.main_frame, text="Upload reference images to start.")
        self.status_label.pack(pady=10)

        self.log_textbox = ctk.CTkTextbox(self.log_frame)
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=5)
        self.log_textbox.configure(state="disabled")

        self.images_frame = ctk.CTkFrame(self.main_frame)
        self.images_frame.pack(fill="x", padx=20, pady=10)

        self.results_frame = ctk.CTkFrame(self.main_frame)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Sky / Atmosphere Analysis ---
        self.sky_frame = ctk.CTkFrame(self.main_frame)
        self.sky_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.sky_frame, text="Sky and Clouds Reference", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # Row 1: Upload & Analyze
        row1_bar = ctk.CTkFrame(self.sky_frame, fg_color="transparent")
        row1_bar.pack(fill="x", padx=10, pady=2)

        self.upload_sky_btn = ctk.CTkButton(row1_bar, text="Upload Sky/Cloud Image", command=self.upload_sky_reference)
        self.upload_sky_btn.pack(side="left", padx=5)

        self.analyze_sky_btn = ctk.CTkButton(row1_bar, text="Analyze Atmosphere", fg_color="#0066cc", hover_color="#004b99", state="disabled", command=self.start_sky_analysis)
        self.analyze_sky_btn.pack(side="left", padx=5)

        # Row 2: Cloud Actions
        row2_bar = ctk.CTkFrame(self.sky_frame, fg_color="transparent")
        row2_bar.pack(fill="x", padx=10, pady=2)

        self.add_clouds_from_analysis_btn = ctk.CTkButton(row2_bar, text="Create Clouds from Analysis", fg_color="#1f7a99", hover_color="#155a70", command=self.create_clouds_from_analysis)
        self.add_clouds_from_analysis_btn.pack(side="left", padx=5)

        # Row 3: Lighting & Atmosphere
        row3_bar = ctk.CTkFrame(self.sky_frame, fg_color="transparent")
        row3_bar.pack(fill="x", padx=10, pady=2)

        self.setup_atm_btn = ctk.CTkButton(row3_bar, text="Setup Atmosphere & Lighting", fg_color="#cc8800", hover_color="#a86d00", command=self.start_setup_lighting)
        self.setup_atm_btn.pack(side="left", padx=5)

        preview_bar = ctk.CTkFrame(self.sky_frame, fg_color="transparent")
        preview_bar.pack(fill="x", padx=10, pady=5)

        self.sky_preview_lbl = ctk.CTkLabel(preview_bar, text="No sky reference selected")
        self.sky_preview_lbl.pack(side="left", padx=5)

        self.sky_output = ctk.CTkTextbox(self.sky_frame, height=200)
        self.sky_output.pack(fill="x", padx=10, pady=(5, 10))
        self.sky_output.configure(state="disabled")

        # --- Manual Terragen Tools ---
        self.tools_frame = ctk.CTkFrame(self.main_frame)
        self.tools_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.tools_frame, text="Terragen Integration", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

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

    def _detect_os_profile(self):
        """Capture platform-specific node class preferences for Terragen builds."""
        sys_name = platform.system().lower()
        is_mac = "darwin" in sys_name
        is_windows = "windows" in sys_name

        # Default ordering works for most Windows installs; macOS builds sometimes expose v3 first.
        cloud_classes = ["cloud_layer", "cloud_layer_v3", "cloud_layer_v2"]
        if is_mac:
            cloud_classes = ["cloud_layer_v3", "cloud_layer", "cloud_layer_v2"]

        # Image map shader class IDs differ across builds; keep broad lists but tweak priority.
        image_map_classes = ["image_map_shader", "image_map_shader_v2", "image_map", "image_map_v3"]
        if is_mac:
            image_map_classes = ["image_map_shader_v2", "image_map_shader", "image_map_v3", "image_map"]

        # Surface shaders are generally consistent; keep a short list.
        # Prefer surface_layer so we can layer over existing planet surfaces without replacing base shading
        surface_classes = ["surface_layer", "default_shader", "fractal_shader"]

        compute_classes = ["compute_terrain"]

        return {
            "cloud_classes": cloud_classes,
            "image_map_classes": image_map_classes,
            "surface_classes": surface_classes,
            "compute_classes": compute_classes,
            "platform": sys_name,
            "is_mac": is_mac,
            "is_windows": is_windows,
        }

    def _friendly_os_name(self):
        """Return a short label for the current OS."""
        sys_name = platform.system()
        release = platform.release()
        if sys_name:
            return f"{sys_name} {release}".strip()
        return "Unknown OS"

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

    def deploy_to_terragen(self, hf_path, tex_path, append_mode=False):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project:
                messagebox.showerror("Error", "Not connected.")
                return

            self.log_message(f"--- Deploying to Terragen (HF: {os.path.basename(hf_path) if hf_path else 'None'}, Tex: {os.path.basename(tex_path) if tex_path else 'None'}) ---")

            def _val_to_set(value, is_node=False):
                if is_node and hasattr(value, "path"):
                    return value.path()
                return value

            def set_and_verify(node, param, value, is_node=False):
                """Set a parameter and log the readback; return readback string."""
                val_to_set = _val_to_set(value, is_node)
                node.set_param(param, val_to_set)
                actual = node.get_param_as_string(param)
                self.log_message(f"Set {node.name()}.{param} = '{val_to_set}' | Readback: '{actual}'")
                return actual

            def set_first_param(node, params, value, is_node=False):
                """Try a list of parameter names; stop at first that reads back non-empty/matching."""
                val_target = _val_to_set(value, is_node)
                for p in params:
                    try:
                        actual = set_and_verify(node, p, val_target, is_node=False)
                        if actual and (actual == val_target or str(actual).lower() == str(val_target).lower()):
                            return p, actual
                    except Exception as e:
                        self.log_message(f"Param attempt failed {node.name()}.{p}: {e}")
                return None, None

            def get_first_param(node, params):
                """Read parameters in order and return the first non-empty value."""
                for p in params:
                    try:
                        val = node.get_param_as_string(p)
                        if val:
                            return p, val
                    except Exception as e:
                        self.log_message(f"Read attempt failed {node.name()}.{p}: {e}")
                return None, None

            def copy_param_value(src_node, dst_node, src_params, dst_params, label):
                """Copy first available value from src to dst using param name lists; log what sticks."""
                src_param, src_val = get_first_param(src_node, src_params)
                if not src_val:
                    self.log_message(f"Copy {label}: source empty (checked {src_params})")
                    return None, None, None
                dst_param, dst_read = set_first_param(dst_node, dst_params, src_val, is_node=False)
                self.log_message(f"Copy {label}: {src_param} -> {dst_param} | val '{src_val}' readback '{dst_read}'")
                return src_val, dst_param, dst_read

            def resolve_node_by_path(path_str):
                if not path_str:
                    return None
                try:
                    return tg.node_by_path(path_str)
                except Exception:
                    return None

            def dump_params(node, label):
                """Attempt to list parameter names/values for debugging across Terragen builds."""
                try:
                    self.log_message(f"--- Params for {label} ({node.name()}) ---")
                    # Try common introspection methods
                    for attr in ("params", "parameters", "param_names", "list_params", "keys"):
                        try:
                            fn = getattr(node, attr, None)
                            if callable(fn):
                                vals = fn()
                                self.log_message(f"{attr}(): {vals}")
                        except Exception as e:
                            self.log_message(f"{label} {attr}() failed: {e}")
                    # Try dir-based guessing
                    try:
                        possible = [d for d in dir(node) if "param" in d.lower()]
                        self.log_message(f"param-like attrs: {possible}")
                    except Exception:
                        pass
                except Exception as e:
                    self.log_message(f"Failed to dump params for {label}: {e}")

            def set_gui_pos(node, x, y):
                """Try to set GUI position to avoid node stacking (best-effort)."""
                try:
                    node.set_param("gui_node_pos", f"{x} {y}")
                except Exception:
                    pass

            def pick_param_by_substring(node, substrings):
                """Pick the first param name containing any of the substrings (case-insensitive)."""
                try:
                    names = node.param_names()
                except Exception:
                    return None
                lower = [n.lower() for n in names]
                for sub in substrings:
                    sub_l = sub.lower()
                    for i, lname in enumerate(lower):
                        if sub_l in lname:
                            return names[i]
                return None

            def set_param_by_substring(node, substrings, value, is_node=False):
                """Set the first parameter whose name contains any substring; return (param, readback)."""
                try:
                    names = node.param_names()
                except Exception:
                    names = []
                for name in names:
                    lname = name.lower()
                    if any(sub.lower() in lname for sub in substrings):
                        try:
                            readback = set_and_verify(node, name, value, is_node=is_node)
                            if readback:
                                return name, readback
                        except Exception as e:
                            self.log_message(f"Param-by-substring attempt failed {node.name()}.{name}: {e}")
                return None, None

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
                for cls in self.os_profile["compute_classes"]:
                    cts = project.children_filtered_by_class(cls)
                    if cts:
                        compute_terrain = cts[0]
                        self.log_message(f"Found Compute Terrain by class '{cls}': {compute_terrain.path()}")
                        break

            if not compute_terrain:
                self.log_message("Compute Terrain not found. Attempting creation...")
                try:
                    new_node = tg.create_child(project, self.os_profile["compute_classes"][0])
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

            def _numbered_name(base_name):
                """Generate a numbered name like AI_Base_01 to help user see connections."""
                try:
                    existing = [c.name() for c in project.children() if c.name().startswith(f"AI_{base_name}")]
                    max_n = 0
                    for n in existing:
                        try:
                            suffix = n.split("AI_" + base_name + "_")[-1]
                            max_n = max(max_n, int(suffix))
                        except Exception:
                            continue
                    return f"AI_{base_name}_{max_n + 1:02d}"
                except Exception:
                    return f"AI_{base_name}_01"

            def find_or_create(name, class_names):
                """Locate node by name/prefix, then by acceptable class list; create using first class that works."""
                node = tg.node_by_path(f"/{name}")
                if node:
                    return node, True

                # Look for any node with matching base or AI_ prefix among allowed classes
                for cls in class_names:
                    for c in project.children_filtered_by_class(cls):
                        if c.name() == name or c.name().startswith(f"AI_{name}"):
                            return c, True

                # Try to create using first working class
                numbered = _numbered_name(name)
                for cls in class_names:
                    try:
                        node = tg.create_child(project, cls)
                        if node:
                            node.set_param("name", numbered)
                            self.log_message(f"Created '{numbered}' using class '{cls}'")
                            return node, False
                    except Exception as create_err:
                        self.log_message(f"Create attempt failed for {name} class '{cls}': {create_err}")
                return None, False

            hf_load, _ = find_or_create("Manual_HF_Load", ["heightfield_load"])
            if hf_path:
                set_and_verify(hf_load, "filename", hf_path)
            set_gui_pos(hf_load, -200, -200)
            
            hf_shader, _ = find_or_create("Manual_HF_Shader", ["heightfield_shader"])
            set_and_verify(hf_shader, "heightfield", hf_load, is_node=True)
            set_gui_pos(hf_shader, -50, -200)
            
            current_ct_input = compute_terrain.get_param_as_string("input_node")
            current_ct_node = resolve_node_by_path(current_ct_input)

            if append_mode:
                self.log_message(f"Append mode enabled. Existing CT input: '{current_ct_input or 'none'}'")

                # Try to reconstruct/align with common Terragen chain: Base PF -> Fractal Warp -> (optional mask) -> CT
                warp_node, _ = find_or_create("Fractal Warp Shader 01", ["fractal_warp_shader"])
                base_pf, _ = find_or_create("Power Fractal Base", ["power_fractal_shader_v3", "power_fractal_shader"])
                mask_node, _ = find_or_create(
                    "Valley Mask",
                    ["simple_shape_shader", "power_fractal_shader_v3", "image_map_shader"],
                )

                # Wire warp input from existing chain or base PF
                warp_input_params = ["input_node", "shader_input", "main_input", "input_primary"]
                if current_ct_node:
                    set_first_param(warp_node, warp_input_params, current_ct_node, is_node=True)
                elif base_pf:
                    set_first_param(warp_node, warp_input_params, base_pf, is_node=True)

                # Mask into warp if available
                mask_params = ["mask_input", "mask", "input_mask", "blend_input", "mix_input"]
                if mask_node:
                    set_first_param(warp_node, mask_params, mask_node, is_node=True)

                # Create merger to blend existing/warp output with new HF
                merger, _ = find_or_create("HF_Merger", ["merger_shader", "merge_shader", "merger"])
                primary_params = ["input_node", "main_input", "primary_input", "input_primary", "input_a", "A"]
                secondary_params = ["input_node_2", "secondary_input", "input_secondary", "input_b", "mask_input", "B", "input_B", "input_b"]
                set_gui_pos(merger, 150, -200)

                # Expand param names dynamically if available (helps builds with different labels)
                dyn_primary = pick_param_by_substring(merger, ["primary", "input", "main", "a"])
                if dyn_primary and dyn_primary not in primary_params:
                    primary_params.insert(0, dyn_primary)
                dyn_secondary = pick_param_by_substring(merger, ["secondary", "input 2", "b", "mask"])
                if dyn_secondary and dyn_secondary not in secondary_params:
                    secondary_params.insert(0, dyn_secondary)

                # Log available params to aid debugging
                try:
                    self.log_message(f"Merger param_names(): {merger.param_names()}")
                except Exception:
                    pass

                primary_source = warp_node if warp_node else current_ct_node
                if primary_source:
                    set_first_param(merger, primary_params, primary_source, is_node=True)
                elif current_ct_input:
                    # if only string path, pass directly
                    set_first_param(merger, primary_params, current_ct_input, is_node=False)

                set_first_param(merger, secondary_params, hf_shader, is_node=True)

                # Verify merger wiring so we don't leave inputs empty; if secondary fails, hard-wire it via substring search
                prim_param, prim_val = get_first_param(merger, primary_params)
                sec_param, sec_val = get_first_param(merger, secondary_params)
                if not sec_val:
                    sec_param, sec_val = set_param_by_substring(merger, ["secondary", "input 2", "b", "mask"], hf_shader, is_node=True)
                if not sec_val:
                    # Try direct set_param with HF path for every known input-ish param
                    try:
                        for p in merger.param_names():
                            if "input" in p.lower() or p.lower() in ("a", "b"):
                                try:
                                    merger.set_param(p, hf_shader.path())
                                    sec_val = merger.get_param_as_string(p)
                                    if sec_val:
                                        sec_param = p
                                        break
                                except Exception:
                                    continue
                    except Exception:
                        pass
                self.log_message(
                    f"Merger inputs -> primary ({prim_param or 'n/a'}) = {prim_val or 'empty'}, secondary ({sec_param or 'n/a'}) = {sec_val or 'empty'}"
                )

                if not sec_val:
                    # Fallback: bypass merger so HF still drives CT
                    set_and_verify(compute_terrain, "input_node", hf_shader, is_node=True)
                    self.log_message("Merger secondary empty; fell back to Compute Terrain -> HF Shader directly")
                else:
                    set_and_verify(compute_terrain, "input_node", merger, is_node=True)
                    self.log_message("Connected Compute Terrain -> HF_Merger (warp/existing + new HF)")
            else:
                if current_ct_input != hf_shader.path():
                    if current_ct_node and current_ct_input != hf_shader.path():
                        set_and_verify(hf_shader, "input_node", current_ct_node, is_node=True)
                        self.log_message(f"Chained HF Shader -> Old Terrain Source ({current_ct_input})")
                    elif current_ct_input:
                        set_and_verify(hf_shader, "input_node", current_ct_input, is_node=False)
                        self.log_message(f"Chained HF Shader -> Old Terrain Source ({current_ct_input}) [string]")
                    set_and_verify(compute_terrain, "input_node", hf_shader, is_node=True)
                    self.log_message("Connected Compute Terrain -> HF Shader")
                else:
                    self.log_message("Compute Terrain already connected to HF Shader")

            if tex_path:
                # Preserve existing planet surface chain so we don't override base shading
                planet_surface_prev = planet.get_param_as_string("surface_shader") or ""
                planet_surface_node = resolve_node_by_path(planet_surface_prev)

                surf_shader, _ = find_or_create("Manual_Surface", self.os_profile["surface_classes"])
                set_gui_pos(surf_shader, 100, 100)

                # Prefer to chain on top of existing planet surface; fall back to compute terrain
                base_surface_target = planet_surface_node if planet_surface_node else compute_terrain
                set_and_verify(surf_shader, "input_node", base_surface_target, is_node=True)

                # If readback is empty or not the CT when we expect it, force CT to ensure displacement context
                surf_in_param, surf_in_val = get_first_param(surf_shader, ["input_node", "shader_input", "surface_shader_input"])
                if not surf_in_val:
                    set_and_verify(surf_shader, "input_node", compute_terrain, is_node=True)
                elif surf_in_val == planet_surface_prev:
                    # Try to rewire to compute terrain when previous surface couldn't resolve a node
                    set_and_verify(surf_shader, "input_node", compute_terrain, is_node=True)

                # Create or reuse an image map shader to feed the texture into the surface shader
                tex_shader, _ = find_or_create("AI_Texture_Image", self.os_profile["image_map_classes"])
                set_gui_pos(tex_shader, 300, 100)
                # Try multiple filename params (covering US/UK spellings and legacy names)
                filename_params = [
                    "image_filename",
                    "filename",
                    "texture_filename",
                    "file",
                    "map_filename",
                    "colour_image",
                    "color_image",
                ]
                used_file_param, file_readback = set_first_param(tex_shader, filename_params, tex_path, is_node=False)
                self.log_message(
                    f"Texture file set result -> param: {used_file_param or 'none'}, readback: {file_readback or 'empty'}"
                )

                # Mapping: Plan Y, use actual image dimensions, center at origin, repeats/flip off
                projection_params = ["projection", "mapping_mode", "map_projection", "mapping"]
                set_first_param(tex_shader, projection_params, "Plan Y", is_node=False)

                try:
                    img_w, img_h = Image.open(tex_path).size
                except Exception as e:
                    self.log_message(f"Failed to read texture size: {e}")
                    img_w, img_h = 1024, 1024
                img_sz3 = max(img_w, img_h)
                size_str = f"{img_w} {img_h}"

                size_params = ["size", "map_size", "tile_size", "scale", "repeat_scale", "texture_size"]
                set_first_param(tex_shader, size_params, size_str, is_node=False)

                size_xy_params = [
                    ("size_x", str(img_w)),
                    ("size_y", str(img_h)),
                    ("repeat_x", "0"),
                    ("repeat_y", "0"),
                ]
                for p, v in size_xy_params:
                    set_first_param(tex_shader, [p], v, is_node=False)

                center_params = [
                    "position_center",
                    "center",
                    "map_center",
                    "offset",
                    "origin",
                    "position",
                    "centre",
                    "pivot",
                ]
                set_first_param(tex_shader, center_params, "0 0 0", is_node=False)

                # Explicitly request center-origin mode using known params from param dump
                set_first_param(tex_shader, ["position_center"], "1", is_node=False)
                set_first_param(tex_shader, ["position_lower_left"], "0", is_node=False)

                # Disable tiling/repeat and flips if such toggles exist
                repeat_flags = ["tile", "tiling", "repeat", "wrap", "use_repeat", "repeat_enabled", "clamp"]
                set_first_param(tex_shader, repeat_flags, "0", is_node=False)
                flip_flags = ["flip", "flip_x", "flip_y", "mirror_x", "mirror_y"]
                set_first_param(tex_shader, flip_flags, "0", is_node=False)

                # Try multiple possible color input params across Terragen variants
                color_params = [
                    "color_function_input",
                    "color_function",
                    "colour_function_input",
                    "colour_function",
                    "color_input",
                    "colour_input",
                    "surface_shader_input",
                    "shader_input",
                    "input_node",
                ]
                used_param, readback = set_first_param(surf_shader, color_params, tex_shader, is_node=True)
                self.log_message(
                    f"Texture wiring result -> param: {used_param or 'none'}, readback: {readback or 'empty'}"
                )

                # Verify downstream connections after wiring
                _, tex_read = get_first_param(surf_shader, color_params)
                self.log_message(f"Post-check surface color input reads as: {tex_read or 'empty'}")
                surf_input_param, surf_input_val = get_first_param(planet, ["surface_shader", "surface_shader_input"])
                self.log_message(f"Post-check planet surface input ({surf_input_param or 'n/a'}) = {surf_input_val or 'empty'}")
                ct_input_param, ct_input_val = get_first_param(compute_terrain, ["input_node"])
                self.log_message(f"Post-check compute terrain input ({ct_input_param or 'n/a'}) = {ct_input_val or 'empty'}")

                # Dump param introspection to see actual names on this build
                dump_params(tex_shader, "AI_Texture_Image")
                dump_params(surf_shader, "Manual_Surface")
                dump_params(planet, "Planet 01")

                set_and_verify(planet, "surface_shader", surf_shader, is_node=True)
                self.log_message("Connected Planet surface -> Manual_Surface shader with texture (layered)")
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
        if self.is_generating:
            messagebox.showinfo("Info", "Generation already in progress.")
            return
        self.is_generating = True
        self.gen_hf_btn.configure(state="disabled")
        thread = threading.Thread(target=self.generate_heightfield)
        thread.daemon = True
        thread.start()

    def generate_heightfield(self):
        if not self.image_paths:
            messagebox.showerror("Error", "Please upload reference images first.")
            self.is_generating = False
            self.gen_hf_btn.configure(state="normal")
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
        finally:
            self.is_generating = False
            self.gen_hf_btn.configure(state="normal")

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

    def open_settings(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("400x200")
        
        # Make modal
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Google Gemini API Key:").pack(pady=(20, 5))
        
        current_key = os.getenv("GOOGLE_API_KEY", "")
        entry = ctk.CTkEntry(dialog, width=300)
        entry.pack(pady=5)
        entry.insert(0, current_key)
        
        def save():
            new_key = entry.get().strip()
            if not new_key:
                messagebox.showwarning("Warning", "API Key cannot be empty.")
                return
            
            # Update env var
            os.environ["GOOGLE_API_KEY"] = new_key
            
            # Update .env file
            try:
                with open(".env", "w") as f:
                    f.write(f"GOOGLE_API_KEY={new_key}\n")
                messagebox.showinfo("Success", "API Key saved.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save .env file: {e}")
            
            # Re-init API
            self.api = TerrainGeneratorAPI()
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)

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
        """Send the best-available heightfield/texture without source selection."""
        # Priority: generated result -> manual selection -> uploaded images fallback
        hf_path = self.heightfield_path or self.manual_hf_path
        tex_path = self.generated_texture_path or self.manual_tex_path

        if not hf_path and self.image_paths:
            hf_path = self.image_paths[0]
            tex_path = self.image_paths[1] if len(self.image_paths) > 1 else None

        if not hf_path:
            messagebox.showerror("Error", "No heightfield available. Generate or select a heightfield first.")
            return

        self.deploy_to_terragen(hf_path, tex_path, append_mode=False)

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

    def _extract_json_from_response(self, raw):
        # Already structured
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            return raw[0]
        if not isinstance(raw, str):
            self.log_message(f"Unexpected analysis type: {type(raw)}")
            return None

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        # Try direct parse
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Try substring between first '{' and last '}'
        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = cleaned[start : end + 1]
                return json.loads(snippet)
        except Exception:
            pass

        # Final fallback: replace single quotes with double quotes
        try:
            alt = cleaned.replace("'", '"')
            return json.loads(alt)
        except Exception:
            pass
        return None

    def analyze_sky(self):
        self.log_message("Analyzing atmosphere and clouds...")
        try:
            summary = self.api.analyze_atmosphere(self.sky_image_path)
            
            # Try to parse and cache immediately
            data = self._extract_json_from_response(summary)
            if data:
                self.last_analysis_data = data
                pretty_json = json.dumps(data, indent=2)
                self.sky_output.configure(state="normal")
                self.sky_output.delete("1.0", "end")
                self.sky_output.insert("end", pretty_json)
                self.sky_output.configure(state="disabled")
                self.log_message("Atmosphere analysis complete and parsed.")
            else:
                self.sky_output.configure(state="normal")
                self.sky_output.delete("1.0", "end")
                self.sky_output.insert("end", summary)
                self.sky_output.configure(state="disabled")
                self.log_message("Atmosphere analysis complete (raw text).")
                
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

            def set_first_param(node, params, value):
                """Try several param names; return first that sticks."""
                for p in params:
                    try:
                        node.set_param(p, value)
                        readback = node.get_param_as_string(p)
                        if readback:
                            self.log_message(f"Set {node.name()}.{p} -> {readback}")
                            return p, readback
                    except Exception as e:
                        self.log_message(f"Param attempt failed {node.name()}.{p}: {e}")
                return None, None

            def get_first_param(node, params):
                for p in params:
                    try:
                        val = node.get_param_as_string(p)
                        if val:
                            return p, val
                    except Exception:
                        continue
                return None, None

            atmosphere = tg.node_by_path("/Atmosphere 01") or tg.node_by_path("Atmosphere 01")
            if not atmosphere:
                atmospheres = project.children_filtered_by_class("atmosphere")
                atmosphere = atmospheres[0] if atmospheres else None
            if not atmosphere:
                messagebox.showerror("Error", "Atmosphere node not found.")
                return

            # Collect clouds across platform-specific class IDs
            clouds = []
            seen_paths = set()
            for cls in self.os_profile["cloud_classes"]:
                try:
                    for c in project.children_filtered_by_class(cls):
                        if c.path() not in seen_paths:
                            clouds.append(c)
                            seen_paths.add(c.path())
                except Exception:
                    continue
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

            # Try known cloud class names in order (platform-tuned)
            new_cloud = None
            for cloud_class in self.os_profile["cloud_classes"]:
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

            atm_input_params = ["input_node", "main_input", "atmosphere_input", "shader_input", "cloud_input"]
            cloud_link_params = ["input_node", "main_input", "shader_input", "cloud_input", "layer_input"]

            def resolve_node(node_path):
                if not node_path:
                    return None
                try:
                    return tg.node_by_path(node_path)
                except Exception:
                    return None

            def find_head_and_tail():
                head_param, head_val = get_first_param(atmosphere, atm_input_params)
                head = resolve_node(head_val) if head_val else None

                if head:
                    self.log_message(f"Atmosphere input before connect: {head_param} -> {head_val}")
                else:
                    self.log_message("Atmosphere has no resolved cloud input; searching for standalone head...")
                    # Try to find a cloud with no upstream connection (or empty input) to treat as head
                    for c in clouds:
                        p, v = get_first_param(c, cloud_link_params)
                        if not v:
                            head = c
                            head_val = c.path()
                            self.log_message(f"Selected head candidate with empty input: {c.name()} ({c.path()})")
                            break
                    if not head and clouds:
                        head = clouds[0]
                        head_val = head.path()
                        self.log_message(f"Fallback head candidate: {head.name()} ({head.path()})")

                # Walk forward to find tail
                visited = set()
                tail = head
                node = head
                while node and node.path() not in visited:
                    visited.add(node.path())
                    next_param, next_val = get_first_param(node, cloud_link_params)
                    if next_val:
                        nxt = resolve_node(next_val)
                        if nxt and nxt.path() not in visited:
                            tail = nxt
                            node = nxt
                            continue
                    break

                if head:
                    self.log_message(f"Chain head: {head.name()} ({head.path()}); tail: {tail.name() if tail else 'n/a'}")
                return head, tail, head_val

            head_cloud, tail_cloud, head_path = find_head_and_tail()

            # Helper: find a cloud with an open main input
            def find_cloud_with_open_input(candidates):
                for c in candidates:
                    p, v = get_first_param(c, cloud_link_params)
                    if not v:
                        return c, p
                return None, None

            if not head_cloud and not head_path:
                # No clouds wired to Atmosphere; make new cloud the head
                try:
                    new_cloud.set_param("input_node", "")
                except Exception:
                    pass
                used_param, readback = set_first_param(atmosphere, atm_input_params, new_cloud.path())
                self.log_message(f"No existing clouds; Atmosphere now points to {readback}")
            else:
                # There is at least one cloud. Connect new cloud to an open main input of an existing cloud.
                target_cloud, target_param = find_cloud_with_open_input(clouds)
                if not target_cloud:
                    target_cloud, target_param = find_cloud_with_open_input([head_cloud] if head_cloud else [])

                if target_cloud:
                    # Feed target cloud from new cloud; do not touch Atmosphere or other connections
                    set_first_param(target_cloud, cloud_link_params, new_cloud.path())
                    self.log_message(f"Connected {new_name} into {target_cloud.name()}'s main input")
                    try:
                        new_cloud.set_param("input_node", "")
                    except Exception:
                        pass
                else:
                    # Fallback: append upstream of head without altering Atmosphere
                    if head_cloud:
                        set_first_param(head_cloud, cloud_link_params, new_cloud.path())
                        self.log_message(f"Inserted {new_name} before head {head_cloud.name()} (no open inputs found)")
                        try:
                            new_cloud.set_param("input_node", "")
                        except Exception:
                            pass
                    elif head_path:
                        # Unresolved head path; place new cloud in front
                        try:
                            new_cloud.set_param("input_node", head_path)
                        except Exception:
                            pass
                        self.log_message(f"Chained {new_name} before unresolved head path {head_path}")

            check_param, check_val = get_first_param(atmosphere, atm_input_params)
            if check_val:
                self.log_message(f"Atmosphere input after connect: {check_param} -> {check_val}")
            else:
                self.log_message("WARNING: Atmosphere input still empty; verify manually.")

            messagebox.showinfo("Success", f"Created cloud layer: {new_name}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create cloud node: {e}")
            self.log_message(f"Cloud node creation failed: {e}")

    def create_clouds_from_analysis(self):
        if not self.sky_image_path:
            messagebox.showerror("Error", "Select a sky image first.")
            return

        try:
            data = self.last_analysis_data
            if not data:
                self.log_message("No cached analysis found, calling API...")
                summary = self.api.analyze_atmosphere(self.sky_image_path, status_callback=self.log_message)
                data = self._extract_json_from_response(summary)
                if data:
                    self.last_analysis_data = data
            
            if not data:
                messagebox.showerror("Error", "Could not parse analysis JSON.")
                return

            layers = data.get("cloud_layers") or []
            # Note: Atmosphere settings are now handled by separate button

            if not layers:
                messagebox.showinfo("Info", "No cloud layers detected in analysis.")
                return

            self.log_message(f"Analysis returned {len(layers)} cloud layers; creating...")
            for idx, layer in enumerate(layers, start=1):
                self._create_cloud_with_settings(layer, idx)

            messagebox.showinfo("Success", f"Created {len(layers)} cloud layers from analysis.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create clouds from analysis: {e}")
            self.log_message(f"Clouds-from-analysis failed: {e}")

    def _apply_atmosphere_settings(self, atm_spec):
        changes = []
        if not atm_spec:
            return changes
        try:
            import terragen_rpc as tg
            project = tg.root()
            atm = tg.node_by_path("/Atmosphere 01") or tg.node_by_path("Atmosphere 01")
            if not atm:
                atms = project.children_filtered_by_class("atmosphere")
                atm = atms[0] if atms else None
            if not atm:
                self.log_message("Atmosphere node not found, skipping atmosphere settings.")
                return changes

            self.log_message(f"Applying atmosphere settings: {atm_spec}")

            # Check for direct Terragen params first
            tg_params = atm_spec.get("terragen_params")
            if tg_params:
                for param, val in tg_params.items():
                    try:
                        # Handle color strings or numbers
                        atm.set_param(param, val)
                        msg = f"Direct set {param} = {val}"
                        self.log_message(msg)
                        changes.append(msg)
                    except Exception as e:
                        self.log_message(f"Failed to set direct param {param}: {e}")

            # Fallback / Heuristics if direct params missing
            
            # Haze / Visibility (only if haze_density not set directly)
            if not tg_params or "haze_density" not in tg_params:
                vis_km = atm_spec.get("visibility_km")
                if vis_km is not None:
                    # Heuristic: Haze density ~ 20 / visibility_km
                    try:
                        haze_val = 20.0 / max(float(vis_km), 1.0)
                        atm.set_param("haze_density", haze_val)
                        msg = f"Set haze_density to {haze_val:.2f} based on {vis_km}km visibility"
                        self.log_message(msg)
                        changes.append(msg)
                    except Exception:
                        pass

            # Tint -> Horizon Colour (only if haze_horizon_colour not set directly)
            if not tg_params or "haze_horizon_colour" not in tg_params:
                tint = str(atm_spec.get("tint", "")).lower()
                color_map = {
                    "golden": "1.0 0.8 0.5",
                    "orange": "1.0 0.6 0.3",
                    "blue": "0.6 0.7 1.0",
                    "gray": "0.8 0.8 0.8",
                    "grey": "0.8 0.8 0.8",
                    "clear": "1.0 1.0 1.0",
                    "neutral": "1.0 1.0 1.0"
                }
                
                col_val = None
                for key, val in color_map.items():
                    if key in tint:
                        col_val = val
                        break
                
                if col_val:
                    atm.set_param("haze_horizon_colour", col_val)
                    msg = f"Set haze_horizon_colour to {col_val} based on tint '{tint}'"
                    self.log_message(msg)
                    changes.append(msg)

        except Exception as e:
            self.log_message(f"Failed to apply atmosphere settings: {e}")
        
        return changes

    def _map_cloud_type_to_class(self, cloud_type: str):
        if not cloud_type:
            return self.os_profile["cloud_classes"]
        t = cloud_type.lower()
        if "cirrus" in t:
            return ["cloud_layer_v3", "cloud_layer", "cloud_layer_v2"]
        if "cumul" in t:
            return ["cloud_layer", "cloud_layer_v3", "cloud_layer_v2"]
        if "strato" in t or "alto" in t or "nimbus" in t:
            return ["cloud_layer", "cloud_layer_v3", "cloud_layer_v2"]
        return self.os_profile["cloud_classes"]

    def _create_cloud_with_settings(self, layer_spec, layer_idx):
        import terragen_rpc as tg

        def safe_set(node, param, value):
            try:
                node.set_param(param, value)
                rb = node.get_param_as_string(param)
                self.log_message(f"Set {node.name()}.{param} = {value} (rb: {rb})")
                return rb
            except Exception as e:
                self.log_message(f"Failed set {node.name()}.{param}: {e}")
                return None

        project = tg.root()
        if not project:
            raise Exception("Not connected to Terragen")

        # Pick class order based on type
        class_order = self._map_cloud_type_to_class(layer_spec.get("type"))

        # Reuse existing create logic but with chosen class order
        clouds = []
        seen_paths = set()
        for cls in class_order:
            try:
                for c in project.children_filtered_by_class(cls):
                    if c.path() not in seen_paths:
                        clouds.append(c)
                        seen_paths.add(c.path())
            except Exception:
                continue

        new_cloud = None
        for cloud_class in class_order:
            try:
                new_cloud = tg.create_child(project, cloud_class)
                if new_cloud:
                    self.log_message(f"Created cloud {layer_idx} using class '{cloud_class}'")
                    break
            except Exception as create_err:
                self.log_message(f"Create attempt failed for class '{cloud_class}': {create_err}")

        if not new_cloud:
            raise Exception("Failed to create cloud layer via RPC")

        new_name = f"AI Cloud {layer_idx}"
        safe_set(new_cloud, "name", new_name)

        # Apply settings
        base_km = layer_spec.get("base_alt_km") or 2.0
        top_km = layer_spec.get("top_alt_km") or base_km + 1.0
        thickness_m = layer_spec.get("thickness_m") or max((top_km - base_km) * 1000, 500)
        coverage_pct = layer_spec.get("coverage_pct") or 50
        
        # Convert percentage to 0-1
        coverage_val = float(coverage_pct) / 100.0

        safe_set(new_cloud, "cloud_altitude", base_km * 1000)
        safe_set(new_cloud, "cloud_depth", thickness_m)
        # Some builds use coverage/opacity params
        for p in ("cloud_cover", "coverage", "density_multiplier", "cloud_density"):
            safe_set(new_cloud, p, coverage_val)

        density_str = str(layer_spec.get("density") or "medium").lower()
        softness_str = str(layer_spec.get("softness") or "medium").lower()
        
        # Map softness to edge_sharpness
        sharpness_map = {"soft": 0.0, "medium": 0.5, "hard": 1.0, "high": 1.0, "low": 0.0}
        sharpness_val = sharpness_map.get(softness_str, 0.5)
        safe_set(new_cloud, "edge_sharpness", sharpness_val)
        safe_set(new_cloud, "edge_softness", 1.0 - sharpness_val)

        # Reuse existing append logic: connect to available cloud input without touching Atmosphere
        atm = tg.node_by_path("/Atmosphere 01") or tg.node_by_path("Atmosphere 01")
        if not atm:
            atms = project.children_filtered_by_class("atmosphere")
            atm = atms[0] if atms else None
        if not atm:
            raise Exception("Atmosphere node not found")

        # Find existing clouds to wire
        clouds = []
        seen_paths = set()
        for cls in self.os_profile["cloud_classes"]:
            try:
                for c in project.children_filtered_by_class(cls):
                    if c.path() not in seen_paths and c.path() != new_cloud.path(): # Exclude self
                        clouds.append(c)
                        seen_paths.add(c.path())
            except Exception:
                continue

        atm_input_params = ["input_node", "main_input", "atmosphere_input", "shader_input", "cloud_input"]
        cloud_link_params = ["input_node", "main_input", "shader_input", "cloud_input", "layer_input"]

        def get_first_param(node, params):
            for p in params:
                try:
                    val = node.get_param_as_string(p)
                    if val:
                        return p, val
                except Exception:
                    continue
            return None, None

        def set_first_param(node, params, value):
            for p in params:
                try:
                    node.set_param(p, value)
                    rb = node.get_param_as_string(p)
                    if rb:
                        return p, rb
                except Exception:
                    continue
            return None, None

        def find_cloud_with_open_input(candidates):
            for c in candidates:
                p, v = get_first_param(c, cloud_link_params)
                if not v:
                    return c, p
            return None, None

        head_param, head_val = get_first_param(atm, atm_input_params)
        if not head_val:
            set_first_param(atm, atm_input_params, new_cloud.path())
            self.log_message(f"Atmosphere empty; connected to {new_name}")
        else:
            target_cloud, _ = find_cloud_with_open_input(clouds)
            if target_cloud:
                set_first_param(target_cloud, cloud_link_params, new_cloud.path())
                self.log_message(f"Connected {new_name} into {target_cloud.name()} main input")
            else:
                # If no open inputs, leave new cloud disconnected to avoid rewiring; log for manual fix
                self.log_message(f"No open cloud inputs found; {new_name} created but not wired")

    def start_setup_lighting(self):
        if not self.last_analysis_data:
            if not self.sky_image_path:
                messagebox.showerror("Error", "Select a sky image first.")
                return
            # Trigger analysis if not cached
            self.analyze_sky()
            if not self.last_analysis_data:
                return

        thread = threading.Thread(target=self._setup_lighting_task)
        thread.daemon = True
        thread.start()

    def _setup_lighting_task(self):
        try:
            import terragen_rpc as tg
            project = tg.root()
            if not project:
                messagebox.showerror("Error", "Terragen not connected.")
                return

            data = self.last_analysis_data
            self.log_message("--- Setting up Lighting & Atmosphere ---")
            
            report_lines = ["\n--- Applied Settings ---"]

            # 1. Apply Atmosphere Settings
            atm_data = data.get("atmosphere")
            if atm_data:
                applied_atm = self._apply_atmosphere_settings(atm_data)
                if applied_atm:
                    report_lines.extend(applied_atm)
            else:
                self.log_message("No atmosphere data in analysis.")

            # 2. Apply Sun Settings
            sun_data = data.get("sun")
            if sun_data:
                sun_node = tg.node_by_path("/Sunlight 01") or tg.node_by_path("Sunlight 01")
                if not sun_node:
                    suns = project.children_filtered_by_class("sun")
                    sun_node = suns[0] if suns else None
                
                if sun_node:
                    az = sun_data.get("azimuth_deg")
                    el = sun_data.get("elevation_deg")
                    
                    if az is not None:
                        sun_node.set_param("heading", float(az))
                        msg = f"Sun Heading: {az}"
                        self.log_message(f"Set {msg}")
                        report_lines.append(msg)
                    if el is not None:
                        sun_node.set_param("elevation", float(el))
                        msg = f"Sun Elevation: {el}"
                        self.log_message(f"Set {msg}")
                        report_lines.append(msg)
                else:
                    self.log_message("Sunlight node not found.")
            else:
                self.log_message("No sun data in analysis.")

            self.log_message("--- Lighting & Atmosphere Setup Complete ---")
            
            # Append report to sky_output
            self.sky_output.configure(state="normal")
            self.sky_output.insert("end", "\n".join(report_lines))
            self.sky_output.see("end")
            self.sky_output.configure(state="disabled")
            
            messagebox.showinfo("Success", "Lighting and Atmosphere updated.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to setup lighting: {e}")
            self.log_message(f"Lighting setup failed: {e}")

    def open_youtube(self):
        webbrowser.open("https://youtube.com/@geekatplay")


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = TerrainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
