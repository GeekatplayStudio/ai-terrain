# Terrain AI Generator

This application allows you to upload reference photos of terrain and uses Google's Gemini Pro AI to analyze them and generate:
1. **Terragen RPC Script**: A complete Python script that connects to Terragen Professional and procedurally creates the terrain, atmosphere, and lighting to match your images.
2. **Visual Analysis**: A detailed description of the terrain features found in the images.

## Requirements

- **Terragen Professional** (running with RPC enabled)
- Python 3.13+
- Google Gemini API Key

## Setup

### Quick Setup (Recommended)

**macOS / Linux:**
```bash
./setup.sh
```

**Windows:**
Double-click `setup.bat` or run it from the command line.

### Manual Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Google API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com/).
   - Create an API Key.
   - *See [docs/GOOGLE_API_SETUP.md](docs/GOOGLE_API_SETUP.md) for a detailed step-by-step guide.*

3. **Set API Key**:
   - You can set it as an environment variable:
     ```bash
     export GOOGLE_API_KEY="your_api_key_here"
     ```
   - Or create a `.env` file in the project root (not committed to git) with:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## Running the Application

```bash
python src/main.py
```

## Usage

1. Click "Upload Images" to select one or more reference photos.
2. Click "Generate Terrain".
3. Wait for the AI to analyze and return the settings.
