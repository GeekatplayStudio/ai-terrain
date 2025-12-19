# Distribution Guide

To create a standalone version of Terrain AI for users who don't have Python installed:

## 1. Prerequisites
Ensure you have the build tools installed in your environment:
```bash
pip install pyinstaller
```

## 2. Build the App
Run the build script:
```bash
python build_app.py
```

## 3. Locate the App
- **macOS**: Go to the `dist/` folder. You will see `TerrainAI.app`.
- **Windows**: Go to the `dist/` folder. You will see `TerrainAI` folder or `.exe`.

## 4. Distribution
- **macOS**: You can zip the `TerrainAI.app` and send it to users.
- **Important**: Since this app uses an API Key (`GOOGLE_API_KEY`), users still need to provide it.
    - **Option A**: Users create a `.env` file in the same folder where they run the app.
    - **Option B**: You bundle a `.env` file (NOT RECOMMENDED if it contains your private key).

## 5. Troubleshooting
- If the app opens and closes immediately, run it from a terminal to see the error:
    - macOS: `dist/TerrainAI.app/Contents/MacOS/TerrainAI`
