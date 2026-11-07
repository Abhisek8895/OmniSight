# OmniSight — Multimodal UI Self-Healing & RPA Agent

OmniSight is an AI-powered UI monitoring and self-healing automation system that detects visual defects in web applications, analyzes affected components using a Vision-Language Model (VLM), generates CSS repairs, applies the fixes, and verifies the results through automated browser screenshots.

The project combines **Playwright, Python, FastAPI, Groq-powered VLM analysis, image optimization, and automated CSS repair** to reduce manual UI testing and debugging.

---

## 1. Project Overview

Modern web applications can experience visual issues such as:

- Text clipping and truncation
- Overlapping UI components
- Misaligned elements
- Layout inconsistencies
- Responsive design issues
- Incorrect component spacing

Traditional UI testing can identify failures but often requires developers to investigate and fix them manually.

OmniSight introduces an automated workflow that:

1. Opens and captures a target webpage.
2. Analyzes screenshots for visual anomalies.
3. Optimizes screenshots using image chunking and cropping.
4. Uses a VLM to identify defective UI components.
5. Generates CSS repair suggestions.
6. Validates and applies the generated CSS.
7. Captures the repaired webpage and verifies whether the issue is resolved.

## 2. Key Features

- **Automated Browser Testing:** Uses Playwright to interact with webpages and capture screenshots.
- **Visual Defect Detection:** Identifies UI anomalies using VLM-based analysis.
- **Image Optimization:** Divides large screenshots into smaller overlapping chunks to focus visual analysis and reduce unnecessary image processing.
- **Focused Component Analysis:** Crops detected anomalous regions for more targeted VLM inspection.
- **AI-Based CSS Repair:** Generates CSS fixes for detected UI problems.
- **Code Validation:** Checks generated repair code before application.
- **Self-Healing Loop:** Applies fixes, captures new screenshots, and retries verification when necessary.
- **Automated Verification:** Uses VLM analysis to determine whether the UI defect has been resolved.
- **FastAPI Webhook:** Provides a separate endpoint for simulated CI/CD event handling.
- **Web Dashboard:** Provides a visual interface to launch and monitor pipeline execution, inspect defects, and view results.

## 3. System Architecture

```text
                 Target Web Application
                           |
                           v
                 Playwright Automation
                           |
                           v
                 Page Context Capture
                           |
                           v
                  Screenshot Capture
                           |
                           v
                  Image Optimization
                  (Chunking / Cropping)
                           |
                           v
                  VLM Defect Detection
                           |
                           v
                Anomalous Component Crop
                           |
                           v
                   CSS Fix Generation
                           |
                           v
                  Code Validation
                           |
                           v
                   CSS Application
                           |
                           v
                Post-Fix Screenshot
                           |
                           v
                 VLM Verification
                           |
                  +--------+--------+
                  |                 |
                Fixed          Not Fixed
                  |                 |
                  v                 v
             Completed         Retry Fix
                                  |
                             Max 3 Attempts
```

## 4. Project Workflow

The integrated pipeline consists of seven main stages.

### Stage 1 — Page Context and Screenshot Capture

- Launches the target webpage using Playwright.
- Captures relevant page and DOM context.
- Records the baseline screenshot.
- Identifies information required for subsequent visual analysis.

### Stage 2 — Image Optimization and VLM Detection

- Processes the full-page screenshot.
- Divides large images into smaller overlapping chunks.
- Sends optimized image regions for visual analysis.
- Identifies potential UI anomalies.

### Stage 3 — Focused Component Cropping

- Extracts the region surrounding the detected anomaly.
- Uses component coordinates to generate a focused image.
- Provides the VLM with a more targeted view of the defective component.

### Stage 4 — CSS Repair Generation

- Analyzes the detected UI issue.
- Generates a CSS repair suggestion.
- Associates the repair with the identified component.

### Stage 5 — Code Validation and Fix Application

- Checks whether generated code belongs to a supported type.
- Enforces code-length validation.
- Applies validated CSS to the target component.
- Handles invalid or unsuccessful repair attempts.

### Stage 6 — Post-Fix Screenshot and Verification

- Reloads or renders the repaired webpage.
- Captures a new screenshot.
- Sends the resulting screenshot for VLM verification.
- Evaluates whether the original visual issue remains.

### Stage 7 — Self-Healing Result

- Marks the repair as successful when verification confirms the issue is fixed.
- Retries when the issue remains unresolved.
- Stops after the configured maximum retry count.
- Records the final execution status and generated artifacts.

## 5. Image Optimization

The image optimization module improves the efficiency of visual analysis.

Instead of processing only a large full-page screenshot, the module:

- Divides screenshots into smaller image chunks.
- Uses overlapping regions to reduce the possibility of missing defects near chunk boundaries.
- Stores the generated image chunks.
- Supports focused cropping of anomalous UI components.

This approach helps the VLM concentrate on relevant visual regions rather than repeatedly analyzing an entire webpage.

## 6. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core implementation |
| Playwright | Browser automation and screenshots |
| FastAPI | Dashboard backend and CI/CD webhook |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| JavaScript | Dashboard interactions |
| Groq API | VLM integration |
| Vision-Language Model | UI defect detection and verification |
| Pillow | Image processing and cropping |
| Pydantic | Request validation |
| Git & GitHub | Version control and collaboration |

## 7. Project Structure

The repository is organized into independent modules that are integrated through the main pipeline.

```text
OmniSight/
│
├── ui/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── server.py
│
├── FastAPI/
│   └── main.py
│
├── Playwright/
│
├── Validation/
│
├── self_healing/
│
├── image_optimization/
│
├── vlm_integration/
│   └── .env
│
├── outputs/
│   └── integrated_pipeline/
│
├── verification/
│   └── verification_results/
│
├── team_contributions/
│
├── run_pipeline.py
│
├── README.md
└── .gitignore
```

*Note: The structure above highlights the main project modules. Individual modules may contain additional Python files, tests, and configuration files.*

## 8. Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- Google Chrome or Chromium-compatible browser
- Groq API key
- Local target website for testing

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Abhisek8895/OmniSight.git
cd OmniSight
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

Install the main dependencies:

```bash
python -m pip install fastapi uvicorn pydantic playwright pillow python-dotenv groq
```

Install the Playwright browser:

```bash
python -m playwright install chromium
```

Install any additional dependencies specified in the individual module requirements files.

### Step 4 — Configure Environment Variables

Create or update:

`vlm_integration/.env`

Add your Groq API key and model configuration:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=your_supported_model_name
```

Replace the example values with your actual credentials and supported model.

**Important:** Never commit API keys or other secrets to GitHub.

## 9. Running the Project

OmniSight contains separate services for the integrated pipeline, dashboard, and CI/CD webhook.

### A. Start the Target Mock Website

Start the local mock website using its configured development server.

The default pipeline target is:

```text
http://127.0.0.1:8000/Mock-Website/
```

Make sure the target website is accessible before starting an inspection.

### B. Run the Integrated Pipeline

From the repository root:

```bash
python -u run_pipeline.py
```

The pipeline executes the seven stages and stores its generated outputs in the configured output directories.

### C. Launch the Dashboard

From the repository root:

```bash
python -m uvicorn UI.server:app --reload --port 9000
```

Open:

```text
http://127.0.0.1:9000
```

The dashboard provides an interface to:

- Enter the target website URL.
- Start an inspection.
- Monitor pipeline progress.
- View execution logs.
- Inspect detected UI defects.
- View before-and-after screenshots.
- Review generated CSS and verification results.

### D. Run the Separate CI/CD Webhook

The webhook service is independent of the dashboard backend.

```bash
python -m uvicorn FastAPI.main:app --reload --port 8001
```

Open its API documentation:

```text
http://127.0.0.1:8001/docs
```

The webhook handles simulated CI/CD events such as push, build, test, and deployment notifications.

## 10. Output and Generated Artifacts

The integrated pipeline stores its execution artifacts under:

```text
outputs/
└── integrated_pipeline/
    ├── context/
    │   └── screenshots and page context
    │
    ├── optimized_images/
    │   └── image chunks
    │
    ├── anomaly_detection.json
    │
    ├── focused/
    │   └── cropped_ui.png
    │
    └── repairs/
        └── attempt_1/
            ├── before_full.png
            └── after_full.png
```

Verification reports are stored under:

```text
verification/
└── verification_results/
```

Generated artifacts can include:

- Original webpage screenshots
- Optimized screenshot chunks
- Focused component crops
- Detected anomaly information
- Generated repair code
- Before-and-after screenshots
- VLM verification reports
- Pipeline execution logs

The exact artifact contents depend on the modules executed and the pipeline configuration.

## 11. Self-Healing and Retry Mechanism

OmniSight uses a retry-based repair workflow.

When the VLM determines that a defect remains:

1. The pipeline records the unsuccessful verification.
2. Another repair attempt can be initiated.
3. The updated fix is applied.
4. A new screenshot is captured.
5. The VLM verifies the updated result.

The maximum retry count is configurable. The current integrated pipeline uses a maximum of three attempts.

The process terminates when:

- The defect is verified as fixed.
- The maximum retry count is reached.
- An execution or validation failure prevents further processing.

## 12. API Endpoints

### Dashboard Backend — Port 9000

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Dashboard interface |
| GET | `/api/health` | Backend health check |
| POST | `/api/run` | Start pipeline execution |
| GET | `/api/status` | Retrieve pipeline status and logs |

### CI/CD Webhook — Port 8001

The webhook provides endpoints for health checks and simulated CI/CD event processing.

See the interactive API documentation at:

```text
http://127.0.0.1:8001/docs
```

## 13. Error Handling

The project includes handling for common execution problems:

- Invalid or unsupported repair code.
- CSS application failures.
- Browser automation failures.
- Missing environment variables.
- VLM API errors.
- Image-processing failures.
- Unsuccessful repair verification.
- Maximum retry exhaustion.
- Webhook request validation errors.

Check the pipeline logs and verification reports when troubleshooting an execution.

## 14. Future Improvements

Potential improvements include:

- Support for additional visual defect categories.
- More advanced responsive UI analysis.
- Improved anomaly localization.
- Smarter CSS repair generation.
- Additional frontend framework support.
- More detailed pipeline analytics.
- Real CI/CD integration.
- Automated regression testing after repair.
- Improved retry and repair-selection strategies.

## 15. Team and Development

OmniSight was developed collaboratively as part of the Infotact Solutions project.

The work covers browser automation, visual defect detection, image optimization, code validation, self-healing automation, VLM integration, backend services, and dashboard development.

## 16. Repository

**GitHub:** https://github.com/Abhisek8895/OmniSight

---

**OmniSight — Detect. Analyze. Repair. Verify.**

An intelligent approach to automated UI defect detection and self-healing.
