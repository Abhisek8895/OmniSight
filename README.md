# OmniSight -- AI-Powered Autonomous Self-Healing QA System

## Project Overview

OmniSight is an AI-powered self-healing QA system designed to identify,
analyze, and repair UI defects in web applications using Vision Language
Models (VLMs), Large Language Models (LLMs), and browser automation.

The project aims to automate key stages of UI testing: screenshot
analysis, defect identification, code-fix generation, repair
application, and post-fix verification. It also explores ways to
evaluate and optimize screenshot-based VLM analysis.

## Technologies Used

-   **Programming Language:** Python
-   **AI Models:** Large Language Models (LLMs) and Vision Language
    Models (VLMs)
-   **AI API:** Groq API
-   **Vision Model:** Qwen
-   **Browser Automation:** Playwright
-   **Backend / API:** FastAPI (project integration)
-   **Code Integration:** GitHub API / PyGithub (project integration)
-   **Frontend:** HTML, CSS, JavaScript
-   **Libraries:** OpenAI SDK, Pillow, python-dotenv
-   **Version Control:** Git and GitHub

------------------------------------------------------------------------

# Weekly Task Implementation

## Week 1 -- Mock Website and UI Test Scenarios

### Objective

Develop a mock e-commerce website and define repeatable UI test
scenarios to provide a controlled environment for identifying website
functionality and interface defects.

### Tasks Completed

-   Created a mock e-commerce website.
-   Developed product listing and product information sections.
-   Implemented shopping cart functionality.
-   Created checkout and order placement sections.
-   Defined normal user interaction workflows.
-   Identified important UI elements for automated testing.
-   Prepared repeatable test scenarios for defect identification.

### Key Components

-   Mock e-commerce website
-   Product pages
-   Shopping cart
-   Checkout page
-   UI test scenarios

### Outcome

Created a mock website and repeatable test scenarios to serve as the
testing environment for the OmniSight self-healing QA workflow.

------------------------------------------------------------------------

## Week 2 -- VLM Integration, Fix Generation and Code Extraction

### Task 1: VLM Setup & Integration

#### Objective

Integrate a Vision Language Model to analyze website screenshots and
identify UI elements and potential defects.

#### Tasks Completed

-   Configured the Groq API.
-   Integrated the Qwen Vision Language Model.
-   Captured website screenshots.
-   Converted screenshots into Base64 format for API input.
-   Sent screenshots to the VLM for analysis.
-   Processed the model responses.
-   Generated UI analysis reports.

#### Outcome

The VLM analyzed website screenshots and produced descriptions of
visible UI elements and potential interface issues.

### Task 4: Fix Generation & Code Extraction

#### Objective

Generate code fixes for identified UI defects and extract usable code
blocks from AI-generated responses.

#### Tasks Completed

-   Integrated the Groq API for fix generation.
-   Provided defect descriptions to the LLM.
-   Generated CSS repair suggestions for UI problems.
-   Extracted code blocks from AI responses.
-   Saved generated fixes into separate files.
-   Implemented reusable code extraction functionality.

#### Key Files

-   `fix_generation/fix_generator.py`
-   `fix_generation/code_extractor.py`
-   `outputs/generated_fixes/`

#### Outcome

Generated CSS repair suggestions and extracted code into separate files
for use in the repair workflow.

------------------------------------------------------------------------

## Week 3 -- CSS Fix Application and VLM Repair Verification

### Task 1: CSS Fix Application

#### Objective

Develop a module to apply AI-generated CSS fixes to the target website
and resolve identified UI defects.

#### Tasks Completed

-   Retrieved AI-generated CSS fixes.
-   Validated generated CSS before applying changes.
-   Identified the target DOM element associated with the UI defect.
-   Applied the generated CSS to the appropriate website element.
-   Handled CSS application failures and invalid fixes.
-   Prepared the updated website for post-fix screenshot capture.

#### Workflow

1.  Receive the AI-generated CSS fix.
2.  Validate the generated CSS.
3.  Identify the affected DOM element.
4.  Apply the CSS changes to the target element.
5.  Handle errors during application.
6.  Prepare the updated website for verification.

#### Outcome

Implemented the CSS fix application functionality to apply AI-generated
repairs to identified UI defects.
