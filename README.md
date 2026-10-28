# OmniSight – AI-Powered Self-Healing UI Testing

OmniSight is an AI-powered UI testing project designed to identify website interface issues, analyze visual defects using Vision-Language Models (VLMs), and generate potential code fixes. The project aims to support an autonomous self-healing QA pipeline.

## Project Overview

This project was developed as part of the Infotact internship. My work during Weeks 1 and 2 focused on preparing a mock e-commerce website, defining UI test scenarios, integrating a VLM using Groq, and implementing AI-based fix generation and code extraction.

## Week 1: Mock Website and UI Test Scenarios

### Work Completed

- Created a basic mock e-commerce website.
- Added the required pages and sections for the shopping flow.
- Added product information and pricing.
- Implemented cart and checkout sections.
- Prepared the website for UI automation and testing.
- Identified important user actions to test.
- Defined repeatable test scenarios for the shopping flow.

### Website Features

- Product display
- Shopping cart
- Cart quantity and total display
- Checkout page
- Place Order button
- Basic shopping-flow test scenarios

### Objective

To create a functional mock website that can be used to test UI behavior, capture screenshots, identify interface defects, and support automated testing.

## Week 2: VLM Integration, Fix Generation and Code Extraction

### Task 1: VLM Setup and Integration

#### Work Completed

- Configured the Groq API integration for VLM-based website analysis.
- Loaded API configuration from an environment file.
- Used a website screenshot as input for visual analysis.
- Encoded the screenshot in Base64 format for processing.
- Sent the screenshot to the configured vision model.
- Processed the model response and saved the analysis report.

#### Output

The VLM analysis was saved to:

`vlm_integration/outputs/vlm_analysis.txt`

#### Objective

To analyze the website's visual interface using a Vision-Language Model and obtain an AI-generated report that can help identify potential UI issues.

### Task 4: Fix Generation and Code Extraction

#### Work Completed

- Implemented a code extraction module in `fix_generation/code_extractor.py`.
- Implemented an AI-based fix generation module in `fix_generation/fix_generator.py`.
- Configured the language model through environment variables.
- Processed AI-generated responses to identify code blocks.
- Generated proposed CSS fixes based on the AI response.
- Saved the generated response and proposed fixes in the output directory.
- Handled API and model configuration issues during development.

#### Output Files

- `outputs/generated_fixes/ai_fix_response.txt`
- `outputs/generated_fixes/proposed_fix_20261026_000024_1.css`

*Note: The generated CSS is a proposed fix and should be reviewed and tested before being applied to the website.*

#### Objective

To convert AI-generated recommendations into usable code snippets that can help address potential UI defects.

## Project Structure

```text
OmniSight/
│
├── mock_website/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── test-scenarios.md
│
├── vlm_integration/
│   ├── test_vlm.py
│   ├── screenshot.png
│   ├── .env
│   └── outputs/
│       └── vlm_analysis.txt
│
├── fix_generation/
│   ├── code_extractor.py
│   └── fix_generator.py
│
├── outputs/
│   └── generated_fixes/
│       ├── ai_fix_response.txt
│       └── proposed_fix_20261026_000024_1.css
│
├── .gitignore
└── README.md
```

*The structure above represents the main files and outputs from the completed tasks. Your local repository may contain additional files or directories.*

## Technologies Used

- Python
- HTML
- CSS
- JavaScript
- Groq API
- Vision-Language Models (VLMs)
- Large Language Models (LLMs)
- Base64 image encoding
- Git and GitHub

## Prerequisites

- Python 3.10 or a compatible Python version
- Git
- VS Code or another code editor
- A Groq API key
- Internet connectivity for API-based model requests

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Abhisek8895/OmniSight.git
cd OmniSight
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

Install the dependencies required by the Python modules:

```bash
pip install requests python-dotenv
```

If the project contains a `requirements.txt` file, use it to install the complete dependency list:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create or update the `.env` file in the appropriate module directory and configure the API key expected by the Python scripts.

Example:

```env
GROQ_API_KEY=your_groq_api_key
```

Use the exact variable names expected by your scripts. Never commit API keys or other secrets to GitHub.

### 5. Run the VLM Analysis

From the repository root, run:

```bash
python vlm_integration/test_vlm.py
```

Ensure that the screenshot path, environment configuration, and model settings match your local setup.

### 6. Run Fix Generation

Run the fix-generation script:

```bash
python fix_generation/fix_generator.py
```

Follow the script's configuration requirements and check the generated output directory for the AI response and proposed code fixes.

## Workflow

1. Prepare the mock e-commerce website.
2. Define repeatable UI test scenarios.
3. Capture a website screenshot.
4. Submit the screenshot for VLM-based analysis.
5. Save the AI-generated analysis report.
6. Generate a proposed fix using an LLM.
7. Extract relevant code blocks from the AI response.
8. Save the proposed fixes for review and testing.

## Current Progress

- [x] Created the mock e-commerce website.
- [x] Added the shopping and checkout flow.
- [x] Defined UI test scenarios.
- [x] Integrated VLM-based screenshot analysis.
- [x] Generated and saved a VLM analysis report.
- [x] Implemented the fix-generation module.
- [x] Implemented the code-extraction module.
- [x] Generated and saved a proposed CSS fix.
- [ ] Validate the generated fix against the actual website.
- [ ] Integrate the complete workflow into an autonomous self-healing QA pipeline.

## Important Notes

- Keep API keys in `.env` files and exclude them from version control.
- Review AI-generated code before applying it.
- Test proposed fixes to ensure that they do not introduce new UI issues.
- Model availability, API limits, and token restrictions may affect execution.
- Generated fixes are proposals; their successful application and validation require separate testing.

## Conclusion

During Weeks 1 and 2 of the Infotact internship, I worked on the foundational components of OmniSight. Week 1 focused on building the mock e-commerce website and defining UI test scenarios. Week 2 focused on VLM integration, screenshot analysis, AI-based fix generation, and code extraction.

These components provide a foundation for the broader goal of developing an AI-powered self-healing UI testing system.
