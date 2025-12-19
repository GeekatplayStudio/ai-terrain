import PyInstaller.__main__
import customtkinter
import os
import shutil
import platform

# 1. Get the path to customtkinter library files (needed for themes/images)
ctk_path = os.path.dirname(customtkinter.__file__)

# 2. Define the build arguments
args = [
    'src/main.py',                  # Your main script
    '--name=TerrainAI',             # Name of the app
    '--noconfirm',                  # Overwrite output directory
    '--windowed',                   # No terminal window (GUI mode)
    '--clean',                      # Clean cache
    
    # Include customtkinter data (JSON themes, etc.)
    f'--add-data={ctk_path}:customtkinter',
    
    # Ensure imports inside functions are found
    '--hidden-import=terragen_rpc',
    '--hidden-import=PIL._tkinter_finder',
    
    # Icon (optional, if you have one. Commented out for now)
    # '--icon=assets/icon.icns', 
]

# 3. Run PyInstaller
print("--- Starting PyInstaller Build ---")
PyInstaller.__main__.run(args)

print("\n--- Build Complete ---")
print("You can find your standalone app in the 'dist' folder.")

# 4. Post-build instructions
if platform.system() == "Darwin": # macOS
    print("macOS detected: 'dist/TerrainAI.app' created.")
    print("Note: You may need to copy your .env file into the app bundle or keep it alongside.")
elif platform.system() == "Windows":
    print("Windows detected: 'dist/TerrainAI.exe' created.")
