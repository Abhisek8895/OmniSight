# UI Defect Detector

A beginner-friendly Flask application that sends a website screenshot and a user-written prompt to a vision-capable OpenAI model. It returns a structured report of possible visible UI defects.

## Features

- Screenshot upload for PNG, JPG/JPEG, and WEBP
- Prompt editing
- AI-assisted visual review
- Structured findings with category, location, evidence, severity, confidence, and suggested fix
- JSON report download
- Upload validation and friendly API error messages
- Uploaded screenshots are processed in memory and are not saved by this app

## Requirements

- Windows 10 or 11
- Python 3.10 or newer
- Internet connection
- An OpenAI API key with API access and available billing/credits

ChatGPT subscriptions and API billing are separate. API usage may cost money.

## Setup on Windows

1. Install Python from https://www.python.org/downloads/. During installation, select **Add Python to PATH**.
2. Install VS Code from https://code.visualstudio.com/download (optional, but recommended).
3. Extract the ZIP to a folder such as `C:\Projects\ui_defect_detector`.
4. Open that folder in VS Code.
5. Select **Terminal → New Terminal**.
6. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

7. Activate it in PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt instead:

   ```bat
   .venv\Scripts\activate.bat
   ```

   Or run the app using the environment's Python directly:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

8. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

9. Copy `.env.example` and name the copy `.env`.
10. Open `.env` and replace `your_api_key_here` with your API key. Do not add quotes. Do not share this file.
11. Run the app:

   ```powershell
   python app.py
   ```

12. Open http://127.0.0.1:5000 in your browser.
13. Upload a screenshot, adjust the prompt if needed, and click **Analyze screenshot**.

Keep the terminal open while using the app. Press `Ctrl+C` in the terminal to stop it.

## If `python` does not work

Try:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Common errors

- **OPENAI_API_KEY is missing:** confirm the file is named `.env`, is in the same folder as `app.py`, and contains your key.
- **API key rejected / 401:** check the key in your API account and make sure it has not been revoked.
- **Rate limit / billing / 429:** check your API account limits and billing. A ChatGPT plan does not automatically include API credits.
- **Model not found or unavailable:** change `OPENAI_MODEL` in `.env` to a vision-capable model available to your account.
- **ModuleNotFoundError:** activate `.venv`, then run `python -m pip install -r requirements.txt`.
- **Port 5000 is in use:** close the other local app using port 5000, or change `port=5000` at the bottom of `app.py` to `port=5001`, then visit http://127.0.0.1:5001.
- **PowerShell script execution blocked:** use the Command Prompt activation command shown above, or run `.venv\Scripts\python.exe app.py`.
- **Upload rejected:** use a valid PNG/JPG/WEBP image under 8 MB.

## How it works

1. Flask receives the screenshot and prompt.
2. Pillow validates the image file.
3. The backend encodes the image and sends it to the vision model.
4. The model returns JSON following a schema.
5. Flask returns the report to the browser.
6. JavaScript displays the findings and lets you download the JSON.

## Important limitations

- AI findings are suggestions, not proof. Verify them in the actual website.
- A screenshot cannot confirm click behavior, API failures, keyboard accessibility, or backend bugs.
- The bounding-box coordinates are approximate and can be inaccurate.
- The app does not save uploaded screenshots, but screenshots are sent to the AI provider for processing. Do not upload confidential images unless you are allowed to share them.
- This is a local learning project. Do not deploy Flask's development server or debug mode as a public production server.
