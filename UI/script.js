
// OmniSight Dashboard API
// Uses the same server that serves the dashboard (port 9000).

const API_BASE = "";

let pollingInterval = null;
let generatedCssValue = "";

const form = document.getElementById("inspectionForm");
const startButton = document.getElementById("startButton");
const runMessage = document.getElementById("runMessage");

const stages = [
    "Website Capture",
    "Image Optimization",
    "AI Defect Detection",
    "Fix Generation",
    "CSS Application",
    "VLM Verification",
    "Final Result"
];


// --------------------------------------------------
// BACKEND CONNECTION
// --------------------------------------------------

async function checkBackend() {
    const status = document.getElementById("connectionStatus");

    try {
        const response = await fetch(`${API_BASE}/api/health`);

        if (!response.ok) {
            throw new Error("Backend unavailable");
        }

        if (status) {
            status.innerHTML =
                '<span class="status-dot" style="background:#39d6a0"></span> Backend connected';
        }

    } catch (error) {
        if (status) {
            status.innerHTML =
                '<span class="status-dot" style="background:#ff667d"></span> Backend offline';
        }
    }
}


// --------------------------------------------------
// START INSPECTION
// --------------------------------------------------

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const websiteUrl = document.getElementById("websiteUrl").value.trim();

    if (!websiteUrl) {
        showMessage("Please enter a website URL.", "error");
        return;
    }

    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }

    startButton.disabled = true;
    startButton.textContent = "Starting...";

    showMessage("Sending inspection request...", "normal");

    resetDashboard();

    try {
        const response = await fetch(`${API_BASE}/api/run`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                target_url: websiteUrl
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to start inspection.");
        }

        showMessage(
            data.message || "Pipeline started successfully.",
            "success"
        );

        document.getElementById("overallStatus").textContent = "Running";
        document.getElementById("pipelineTag").textContent = "RUNNING";

        await fetchPipelineStatus();

        pollingInterval = setInterval(fetchPipelineStatus, 2000);

    } catch (error) {
        showMessage(error.message, "error");

        startButton.disabled = false;
        startButton.innerHTML = "<span>▶</span> Start Inspection";

        document.getElementById("overallStatus").textContent = "Idle";
    }
});


// --------------------------------------------------
// FETCH PIPELINE STATUS
// --------------------------------------------------

async function fetchPipelineStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);

        if (!response.ok) {
            throw new Error("Could not retrieve pipeline status.");
        }

        const data = await response.json();

        updatePipeline(data);

        if (!data.running) {
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }

            startButton.disabled = false;
            startButton.innerHTML = "<span>▶</span> Start Inspection";

            if (data.status === "completed") {
                showMessage(
                    "Pipeline execution completed.",
                    "success"
                );
            } else if (data.status === "failed") {
                showMessage(
                    data.message || "Pipeline execution failed.",
                    "error"
                );
            }
        }

    } catch (error) {
        showMessage(error.message, "error");

        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }

        startButton.disabled = false;
        startButton.innerHTML = "<span>▶</span> Start Inspection";
    }
}


// --------------------------------------------------
// UPDATE DASHBOARD
// --------------------------------------------------

function updatePipeline(data) {
    const logs = data.logs || [];
    const result = data.result || {};

    // Read actual pipeline stage from terminal logs
    const stageLog = [...logs].reverse().find(log =>
        /\[\d+\/7\]/.test(log)
    );

    let currentStep = 0;

    if (stageLog) {
        const match = stageLog.match(/\[(\d+)\/7\]/);
        if (match) {
            currentStep = Number(match[1]);
        }
    }

    let progress = Math.round((currentStep / 7) * 100);

    if (data.status === "completed") {
        progress = 100;
    }

    document.getElementById("progressFill").style.width =
        `${progress}%`;

    document.getElementById("progressPercent").textContent =
        `${progress}%`;

    document.getElementById("progressText").textContent =
        stageLog || data.message || "Processing...";

    document.getElementById("overallStatus").textContent =
        capitalize(data.status || "running");

    document.getElementById("pipelineTag").textContent =
        (data.status || "running").toUpperCase();


    // Update pipeline stages
    document.querySelectorAll(".pipeline-step").forEach(element => {
        const stepNumber = Number(element.dataset.step);
        const status = element.querySelector(".step-status");

        if (!status) return;

        element.classList.remove("running", "completed", "failed");

        if (data.status === "completed") {
            element.classList.add("completed");
            status.textContent = "Completed";
        } else if (data.status === "failed" && stepNumber === currentStep) {
            element.classList.add("failed");
            status.textContent = "Failed";
        } else if (stepNumber < currentStep) {
            element.classList.add("completed");
            status.textContent = "Completed";
        } else if (stepNumber === currentStep && data.running) {
            element.classList.add("running");
            status.textContent = "Running";
        } else {
            status.textContent = "Waiting";
        }
    });


    // Display live logs
    displayLogs(logs);


    // Display defect
    if (result.defect) {
        displayDefect(result.defect);

        document.getElementById("defectCount").textContent = "1";
    }


    // Display verification
    if (result.verification) {
        displayVerification(result.verification);

        if (result.verification.status === "FIXED") {
            document.getElementById("verifiedCount").textContent = "1";
        }
    }


    // Display before screenshot
    if (result.before_screenshot) {
        displayScreenshot(
            "beforeContainer",
            result.before_screenshot
        );
    }


    // Display after screenshot
    if (result.after_screenshot) {
        displayScreenshot(
            "afterContainer",
            result.after_screenshot
        );
    }


    // Display focused component screenshot, if the HTML has a container
    if (result.focused_screenshot) {
        displayScreenshot(
            "focusedContainer",
            result.focused_screenshot
        );
    }


    // Display generated CSS
    if (result.generated_css) {
        generatedCssValue = result.generated_css;

        document.getElementById("generatedCss").textContent =
            generatedCssValue;

        document.getElementById("copyCssButton").disabled = false;
    }


    // Display repair attempts
    if (result.attempts !== undefined) {
        document.getElementById("totalRuns").textContent =
            result.attempts;
    }
}


// --------------------------------------------------
// DISPLAY LIVE LOGS
// --------------------------------------------------

function displayLogs(logs) {
    const container =
        document.getElementById("pipelineLogs") ||
        document.getElementById("logOutput") ||
        document.getElementById("logsContent");

    if (!container) return;

    container.textContent = logs.join("\n");
    container.scrollTop = container.scrollHeight;
}


// --------------------------------------------------
// DISPLAY DEFECT
// --------------------------------------------------

function displayDefect(defect) {
    const container = document.getElementById("defectContent");

    const component = defect.component || {};

    const title =
        defect.title ||
        defect.description ||
        "UI defect detected";

    const selector =
        defect.selector ||
        component.selector ||
        component.element_id ||
        "Not provided";

    const severity = defect.severity || "Unknown";

    const description =
        defect.description ||
        "No description available.";

    container.className = "defect-result";
    container.replaceChildren();

    const badge = document.createElement("span");
    badge.className = "severity";
    badge.textContent = severity.toUpperCase();

    const heading = document.createElement("h3");
    heading.textContent = title;

    const selectorText = document.createElement("p");
    selectorText.textContent = `Target: ${selector}`;

    const descriptionText = document.createElement("p");
    descriptionText.textContent = description;

    container.append(
        badge,
        heading,
        selectorText,
        descriptionText
    );
}


// --------------------------------------------------
// DISPLAY VERIFICATION
// --------------------------------------------------

function displayVerification(verification) {
    const container =
        document.getElementById("verificationContent");

    container.className = "empty-state";
    container.replaceChildren();

    const icon = document.createElement("div");
    icon.className = "empty-icon";
    icon.textContent =
        verification.status === "FIXED" ? "✓" : "⚠";

    const heading = document.createElement("strong");
    heading.textContent =
        verification.status || "Verification pending";

    const description = document.createElement("p");
    description.textContent =
        verification.reason ||
        verification.evidence ||
        "No verification details provided.";

    const confidence = document.createElement("p");
    confidence.textContent = verification.confidence
        ? `Confidence: ${verification.confidence}`
        : "";

    container.append(
        icon,
        heading,
        description,
        confidence
    );
}


// --------------------------------------------------
// DISPLAY SCREENSHOTS
// --------------------------------------------------

function displayScreenshot(containerId, imageUrl) {
    const container = document.getElementById(containerId);

    if (!container) return;

    const image = document.createElement("img");

    image.src = imageUrl;
    image.alt = "OmniSight pipeline screenshot";

    image.onerror = () => {
        container.textContent =
            "Screenshot could not be loaded.";
    };

    container.replaceChildren(image);
}


// --------------------------------------------------
// COPY GENERATED CSS
// --------------------------------------------------

document.getElementById("copyCssButton").addEventListener(
    "click",
    async () => {
        if (!generatedCssValue) return;

        try {
            await navigator.clipboard.writeText(generatedCssValue);

            const button =
                document.getElementById("copyCssButton");

            button.textContent = "Copied!";

            setTimeout(() => {
                button.textContent = "Copy CSS";
            }, 1500);

        } catch (error) {
            showMessage("Unable to copy CSS.", "error");
        }
    }
);


// --------------------------------------------------
// RESET DASHBOARD
// --------------------------------------------------

function resetDashboard() {
    document.getElementById("progressFill").style.width = "0%";
    document.getElementById("progressPercent").textContent = "0%";

    document.getElementById("progressText").textContent =
        "Starting...";

    document.getElementById("defectCount").textContent = "—";
    document.getElementById("verifiedCount").textContent = "—";
    document.getElementById("totalRuns").textContent = "—";

    document.getElementById("defectContent").className =
        "empty-state";

    document.getElementById("defectContent").innerHTML = `
        <div class="empty-icon">◈</div>
        <strong>Analyzing website...</strong>
        <p>Waiting for defect detection results.</p>
    `;

    document.getElementById("verificationContent").className =
        "empty-state";

    document.getElementById("verificationContent").innerHTML = `
        <div class="empty-icon">✓</div>
        <strong>Awaiting verification</strong>
        <p>Verification results will appear here.</p>
    `;

    document.getElementById("beforeContainer").textContent =
        "Waiting for screenshot...";

    document.getElementById("afterContainer").textContent =
        "Waiting for screenshot...";

    const focused = document.getElementById("focusedContainer");

    if (focused) {
        focused.textContent = "Waiting for focused screenshot...";
    }

    generatedCssValue = "";

    document.getElementById("generatedCss").textContent =
        "Waiting for generated CSS...";

    document.getElementById("copyCssButton").disabled = true;

    document.querySelectorAll(".pipeline-step").forEach(element => {
        element.classList.remove(
            "running",
            "completed",
            "failed"
        );

        const status = element.querySelector(".step-status");

        if (status) {
            status.textContent = "Waiting";
        }
    });

    const logsContainer =
        document.getElementById("pipelineLogs") ||
        document.getElementById("logOutput") ||
        document.getElementById("logsContent");

    if (logsContainer) {
        logsContainer.textContent = "Waiting for pipeline logs...";
    }
}


// --------------------------------------------------
// MESSAGE DISPLAY
// --------------------------------------------------

function showMessage(message, type) {
    runMessage.textContent = message;

    if (type === "error") {
        runMessage.style.color = "#ff667d";
    } else if (type === "success") {
        runMessage.style.color = "#39d6a0";
    } else {
        runMessage.style.color = "#8996ad";
    }
}


function capitalize(value) {
    return value.charAt(0).toUpperCase() + value.slice(1);
}


// --------------------------------------------------
// INITIALIZATION
// --------------------------------------------------

checkBackend();
