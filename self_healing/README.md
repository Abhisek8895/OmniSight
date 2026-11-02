# Agentic Self-Healing Loop

## Overview

The Self-Healing Loop is responsible for controlling the repair and verification process for UI defects.

It applies a generated repair, validates the repair code, captures an updated screenshot, and checks whether the defect has been resolved. If the defect is not resolved, the process can retry until the maximum retry limit is reached.

## Workflow

The self-healing process follows this flow:

```text
AI-Generated CSS Fix
        ↓
Apply Fix
        ↓
Validate Repair Code
        ↓
Take New Screenshot
        ↓
VLM Verification
        ↓
Is the Defect Fixed?
     ↙         ↘
   Yes          No
    ↓            ↓
  Finish       Retry
                 ↓
          Maximum Retries?
             ↙       ↘
           Yes        No
            ↓          ↓
          Stop      Apply Fix Again
```

## Responsibilities

The self-healing loop is responsible for:

- Receiving the generated repair code.
- Validating the repair code before continuing.
- Applying the proposed fix.
- Capturing a new screenshot after the repair.
- Sending the updated screenshot for verification.
- Determining whether the UI defect has been resolved.
- Retrying the repair when verification indicates that the defect remains.
- Limiting the number of repair attempts.
- Safely stopping when the maximum retry limit is reached.

## Retry Handling

The loop uses a maximum retry limit to prevent continuous repair attempts.

```python
MAX_RETRIES = 3
```

The process stops when:

1. The verification step confirms that the defect is fixed, or
2. The maximum number of repair attempts has been reached.

## Code Validation

Before screenshot capture and verification, the generated repair code is checked for:

- Missing code
- Invalid code type
- Unsupported repair type
- Excessive code length

Currently supported repair types are:

```python
SUPPORTED_TYPES = ["css", "react"]
```

## Current Implementation

The `self_healing_loop.py` file provides the foundation for the agentic repair workflow.

The current implementation includes:

```text
Repair Code
     ↓
Code Validation
     ↓
Fix Application
     ↓
Screenshot Capture
     ↓
Verification
     ↓
Retry Decision
```

The screenshot capture uses Playwright to open the local mock website and generate an updated screenshot.

The VLM verification function is currently implemented as a placeholder because the actual VLM model and API connection are not yet available. It will be replaced with the project's actual VLM verification service when the model/API is provided.

## Current Limitations

- The actual VLM API is not yet connected.
- The current VLM verification function uses a placeholder response.
- The current fix application function returns the generated repair code but does not yet modify the live webpage DOM/CSS.
- Full end-to-end self-healing will be completed once the actual VLM and repair application components are connected.

## Future Integration

The complete workflow will connect:

```text
Defect Detection
        ↓
AI Fix Generation
        ↓
Fix Application
        ↓
Playwright Screenshot
        ↓
VLM Verification
        ↓
Retry / Success Decision
```

This will allow OmniSight to automatically attempt repairs and verify the result before stopping.