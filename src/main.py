import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import threading
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

        self.generate_btn = ctk.CTkButton(self.sidebar_frame, text="Generate Terrain", command=self.start_generation)
        self.generate_btn.grid(row=2, column=0, padx=20, pady=10)
        self.generate_btn.configure(state="disabled")

        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")

        self.image_paths = []
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
            self.log_message(f"{len(self.image_paths)} images selected.")

    def display_uploaded_images(self):
        for widget in self.images_frame.winfo_children():
            widget.destroy()
        
        for img_path in self.image_paths:
            try:
                img = Image.open(img_path)
                img.thumbnail((100, 100))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                label = ctk.CTkLabel(self.images_frame, image=ctk_img, text="")
                label.pack(side="left", padx=5, pady=5)
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")

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
            result = self.api.generate_terrain(self.image_paths, status_callback=callback)
            self.after(0, self.display_results, result)
        except Exception as e:
            self.after(0, self.show_error, str(e))

    def display_results(self, result):
        self.log_message("Generation Complete.")
        self.generate_btn.configure(state="normal")
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Display Atmosphere Settings
        if "atmosphere" in result:
            atm_frame = ctk.CTkFrame(self.results_frame)
            atm_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(atm_frame, text="Atmosphere Settings", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
            ctk.CTkTextbox(atm_frame, height=100).pack(fill="x", padx=10, pady=5)
            # Insert text... (TODO)

        # Display Height Map (Placeholder if text only)
        hm_frame = ctk.CTkFrame(self.results_frame)
        hm_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(hm_frame, text="Height Map Info", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        if "height_map_text" in result:
             lbl = ctk.CTkLabel(hm_frame, text=result["height_map_text"], wraplength=600, justify="left")
             lbl.pack(padx=10, pady=5)

    def show_error(self, message):
        self.status_label.configure(text="Error occurred.")
        self.generate_btn.configure(state="normal")
        messagebox.showerror("Error", message)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = TerrainApp()
    app.mainloop()
