# How to Set Up Your Google API Key

This project uses Google's Gemini Pro AI model to analyze images and generate terrain data. To use it, you need a valid API key from Google AI Studio.

## Step 1: Get the API Key

1.  **Go to Google AI Studio**
    Visit [https://aistudio.google.com/](https://aistudio.google.com/) in your web browser.

2.  **Sign In**
    Sign in with your Google Account.

3.  **Create an API Key**
    -   On the left sidebar (or top menu), look for **"Get API key"**.
    -   Click on **"Create API key"**.
    -   You can choose to create a key in a new project or an existing Google Cloud project. For simplicity, creating a key in a **new project** is usually the easiest option.

4.  **Copy the Key**
    -   Once generated, you will see a long string of characters (e.g., `AIzaSy...`).
    -   **Copy this key** to your clipboard. Do not share this key with anyone.

## Step 2: Configure the Key in the Application

You have two ways to provide this key to the application. Method A is recommended for local development.

### Method A: Using a `.env` file (Recommended)

1.  Open the `terrain-ai` project folder on your computer.
2.  Create a new file named `.env` (just `.env`, no name before the dot).
3.  Open this file with a text editor (Notepad, TextEdit, VS Code, etc.).
4.  Paste your API key in the following format:

    ```env
    GOOGLE_API_KEY=AIzaSyYourActualKeyHere...
    ```

5.  Save the file. The application will automatically read this file when it starts.

### Method B: Using Environment Variables

If you prefer not to create a file, you can set it as an environment variable in your terminal before running the app.

**On macOS / Linux:**
```bash
export GOOGLE_API_KEY="AIzaSyYourActualKeyHere..."
python src/main.py
```

**On Windows (Command Prompt):**
```cmd
set GOOGLE_API_KEY=AIzaSyYourActualKeyHere...
python src\main.py
```

## Troubleshooting

-   **"Google API Key not found" Error**: This means the application couldn't find the key. Ensure you named the file exactly `.env` and it is located in the root folder (same folder as `requirements.txt`).
-   **"Invalid API Key" Error**: Double-check that you copied the entire key string correctly and that there are no extra spaces in the `.env` file.
-   **Quota Limits**: The free tier of Gemini API has usage limits. If you make too many requests too quickly, you might get a temporary error. Wait a minute and try again.
