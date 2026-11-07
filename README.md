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

### Task 3: VLM Repair Verification

#### Objective

Develop a verification module that checks whether an applied UI repair
resolves the original defect using a Vision Language Model.

#### Tasks Completed

-   Developed the repair verification module.
-   Captured post-fix website screenshots.
-   Integrated the Groq API with the Qwen VLM.
-   Sent post-fix screenshots for visual analysis.
-   Provided the original defect description as context.
-   Processed the VLM verification response.
-   Implemented `FIXED` and `NOT_FIXED` result identification.
-   Generated structured verification results.
-   Handled API and response-processing errors.

#### Verification Workflow

1.  Receive the original UI defect description.
2.  Capture the post-fix website screenshot.
3.  Send the screenshot and defect context to the VLM.
4.  Analyze whether the original defect still exists.
5.  Generate a verification result.
6.  Save the result in the configured output format.

#### Key Components

-   CSS Fix Application Module
-   Repair Verification Module
-   Playwright Screenshot Capture
-   Groq API Integration
-   Qwen Vision Language Model

#### Outcome

Implemented a verification workflow that uses the VLM to determine
whether the original UI defect remains after a repair.

-   **FIXED:** The original defect is no longer visible.
-   **NOT_FIXED:** The original defect is still present.

------------------------------------------------------------------------

## Week 4 -- VLM Optimization and Performance Analysis

### Objective

Evaluate VLM performance with different screenshot-processing approaches
and compare their impact on analysis time, token usage, and processing
performance.

### Work Areas

-   Analyze VLM performance using website screenshots.
-   Evaluate full-screenshot processing.
-   Explore cropped-screenshot processing.
-   Explore screenshot chunking for focused analysis.
-   Measure API response time.
-   Track token usage and processing metrics where available.
-   Collect performance results.
-   Compare the results of different screenshot-processing approaches.
-   Generate structured performance reports.

### Key Components

-   VLM performance analysis
-   Performance metrics
-   Comparison module
-   Test screenshots
-   Performance output reports

### Outcome

The objective is to compare screenshot-processing approaches and
understand their impact on VLM response time, token consumption, and
analysis performance.

------------------------------------------------------------------------

# Overall Project Workflow

``` text
          Mock E-commerce Website
                    |
                    v
           Playwright Automation
                    |
                    v
            Screenshot Capture
                    |
                    v
            VLM Defect Analysis
                    |
                    v
             LLM Fix Generation
                    |
                    v
              Code Extraction
                    |
                    v
             CSS Fix Application
                    |
                    v
           Post-Fix Screenshot
                    |
                    v
             VLM Verification
                    |
              +-----+-----+
              |           |
              v           v
            FIXED      NOT_FIXED
              |           |
              v           v
           Complete   Further Repair
```

------------------------------------------------------------------------

# Project Directory Structure

The following is an indicative structure. Keep the actual filenames and
folders in sync with the repository as the implementation evolves.

``` text
OmniSight/
│
├── mock_website/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   └── test-scenarios.md
│
├── vlm_integration/
│   ├── test_vlm.py
│   ├── screenshot.png
│   └── outputs/
│
├── fix_generation/
│   ├── fix_generator.py
│   └── code_extractor.py
│
├── outputs/
│   └── generated_fixes/
│
├── verification/
│   ├── repair_verifier.py
│   ├── post_fix_screenshot.png
│   └── verification_results/
│
├── .gitignore
├── requirements.txt
└── README.md
```

# Key Features

-   Screenshot-based UI analysis using a Vision Language Model.
-   AI-assisted identification of UI defects.
-   LLM-based CSS fix generation.
-   Extraction of code blocks from AI responses.
-   Application of generated CSS fixes to target UI elements.
-   Post-fix screenshot capture.
-   VLM-based repair verification.
-   `FIXED` and `NOT_FIXED` verification outcomes.
-   Exploration of VLM performance optimization techniques.

# Project Goal

The ultimate goal of OmniSight is to build an autonomous self-healing QA
pipeline that can detect UI defects, generate code-level repairs, apply
fixes, and verify the results with minimal manual intervention.

------------------------------------------------------------------------

**Project:** OmniSight -- AI-Powered Autonomous Self-Healing QA System\
**Domain:** AI & Automation Engineering\
**Internship:** Infotact Solutions
