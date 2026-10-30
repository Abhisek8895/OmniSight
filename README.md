
# OmniSight – Team Work Documentation

## Week 1 – Website Development, Automation & Backend Setup

**Objective:** To prepare the mock e-commerce website, automate its shopping workflow, establish backend communication, and create UI defects for testing.

### Task 1: Prepare the Mock Website and Define UI Test Scenarios

**Work Completed:**
- Created a basic mock e-commerce website.
- Developed the required pages for the shopping workflow.
- Added products and their basic information.
- Implemented shopping cart and checkout sections.
- Established the normal website navigation flow.
- Identified important website interactions.
- Created repeatable UI test scenarios.
- Prepared the website for automation and testing.

**Outcome:** A functional mock e-commerce website with predefined testing scenarios.

### Task 2: Set Up and Automate the Website Checkout

**Work Completed:**
- Configured the Python environment.
- Installed Playwright and the required browser.
- Verified browser execution.
- Connected Playwright to the mock website.
- Automated website navigation.
- Automated product selection and cart operations.
- Automated the checkout process.
- Tested the complete shopping workflow.

**Outcome:** Automated end-to-end website checkout using Python and Playwright.

### Task 3: Take Screenshots at Different Screen Sizes and Check the Layout

**Work Completed:**
- Selected different viewport sizes.
- Executed the website at different screen resolutions.
- Captured screenshots of important pages.
- Captured screenshots during important website interactions.
- Checked the website layout and responsiveness.
- Identified visual and layout problems.
- Organized screenshots for further testing.

**Outcome:** Baseline screenshots for visual comparison and UI defect analysis.

### Task 4: Create the FastAPI Application and Webhook

**Work Completed:**
- Set up the FastAPI project.
- Created the main application.
- Developed a webhook endpoint.
- Configured the endpoint to receive simulated CI/CD requests.
- Defined request and response formats.
- Started the FastAPI server.
- Sent sample requests to the webhook.
- Verified the JSON responses.

**Outcome:** FastAPI application with a functional webhook endpoint.

### Task 5: Test the Webhook and Check the UI Bugs

**Work Completed:**
- Tested valid webhook requests.
- Tested invalid and incomplete requests.
- Verified request handling and JSON responses.
- Executed the predefined website test scenarios.
- Introduced deliberate UI defects.
- Tested overlapping text and hidden submit buttons.
- Captured screenshots of defective elements.
- Documented expected and actual behavior.
- Checked whether defects could be reproduced consistently.

**Outcome:** Tested webhook functionality and reproducible UI defects for AI-based analysis.

---

## Week 2 – AI Integration, Defect Detection & Fix Generation

**Objective:** To integrate AI models, prepare website information for analysis, detect UI defects, generate code fixes, and prepare extracted code for validation.

### Task 1: VLM Setup & Integration

**Work Completed:**
- Configured the approved Vision Language Model.
- Established the model/API connection.
- Configured environment variables.
- Implemented the model request and response workflow.
- Tested model connectivity and response generation.

**Outcome:** Successful VLM integration for screenshot analysis.

### Task 2: Screenshot & HTML Context Pipeline

**Work Completed:**
- Captured website screenshots.
- Collected relevant HTML and CSS information.
- Prepared visual and source-code context.
- Organized the collected information.
- Prepared the input required for VLM analysis.

**Outcome:** Screenshot and HTML/CSS context prepared for AI processing.

### Task 3: Prompt Engineering & Defect Detection

**Work Completed:**
- Designed prompts for UI defect detection.
- Provided screenshots and website context to the AI model.
- Identified visual defects using model responses.
- Analyzed defective elements and their locations.
- Requested explanations and possible corrections.

**Outcome:** AI-based UI defect detection and analysis.

### Task 4: Fix Generation & Code Extraction

**Work Completed:**
- Developed the fix generation module.
- Connected the module to the configured AI model.
- Designed prompts for generating CSS and React fixes.
- Processed AI-generated responses.
- Implemented code extraction functionality.
- Extracted code blocks from AI responses.
- Handled responses without valid code blocks.
- Saved generated responses and extracted fixes into output files.

**Outcome:** Automated fix generation and code extraction from AI responses.

### Task 5: Code Validation & Fix Output

**Work Completed:**
- Prepared extracted code for validation.
- Checked code structure and formatting.
- Identified invalid or incomplete code.
- Organized the generated fixes for the next workflow stage.

**Outcome:** Prepared code fixes for the repair workflow.

---

## Technologies Used Across Week 1 & Week 2

| Technology | Purpose |
|---|---|
| Python | Automation and backend development |
| HTML5 | Website structure |
| CSS3 | Website styling |
| JavaScript | Website functionality |
| Playwright | Browser automation |
| FastAPI | Backend application and webhook |
| VLM | Visual defect analysis |
| Groq API | AI model integration |
| Git & GitHub | Version control and team collaboration |

## Summary of Team Progress

| Week | Focus Area | Main Deliverables |
|---|---|---|
| Week 1 | Website and testing foundation | Mock website, automated checkout, screenshots, FastAPI webhook, UI defects |
| Week 2 | AI integration and fix generation | VLM integration, screenshot context, defect detection, fix generation, code extraction and validation |

---

**Documentation:** OmniSight Team Work  
**Coverage:** Week 1 and Week 2  
**Project Domain:** AI & Automation Engineering
