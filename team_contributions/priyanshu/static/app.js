const form = document.querySelector("#analyze-form");
const fileInput = document.querySelector("#screenshot");
const promptInput = document.querySelector("#prompt");
const uploadTitle = document.querySelector("#upload-title");
const uploadSubtitle = document.querySelector("#upload-subtitle");
const previewWrap = document.querySelector("#preview-wrap");
const previewImage = document.querySelector("#preview-image");
const removeImageButton = document.querySelector("#remove-image");
const charCount = document.querySelector("#char-count");
const analyzeButton = document.querySelector("#analyze-button");
const buttonText = document.querySelector("#button-text");
const emptyState = document.querySelector("#empty-state");
const loadingState = document.querySelector("#loading-state");
const errorBox = document.querySelector("#error-box");
const reportElement = document.querySelector("#report");
const findingCount = document.querySelector("#finding-count");
const downloadButton = document.querySelector("#download-report");

let previewUrl = null;
let lastReport = null;

function show(element) {
  element.classList.remove("hidden");
}

function hide(element) {
  element.classList.add("hidden");
}

function setError(message) {
  errorBox.textContent = message;
  show(errorBox);
}

function resetResults() {
  hide(errorBox);
  hide(reportElement);
  hide(downloadButton);
  show(emptyState);
  findingCount.textContent = "Waiting for scan";
  lastReport = null;
}

function clearPreview() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }
  fileInput.value = "";
  previewImage.removeAttribute("src");
  hide(previewWrap);
  uploadTitle.textContent = "Choose a screenshot";
  uploadSubtitle.textContent = "Click to browse files · Maximum 8 MB";
}

fileInput.addEventListener("change", () => {
  resetResults();
  const file = fileInput.files[0];
  if (!file) return;

  const allowedTypes = ["image/png", "image/jpeg", "image/webp"];
  if (!allowedTypes.includes(file.type)) {
    clearPreview();
    setError("Choose a PNG, JPG/JPEG, or WEBP image.");
    return;
  }
  if (file.size > 8 * 1024 * 1024) {
    clearPreview();
    setError("The image must be 8 MB or smaller.");
    return;
  }

  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  previewImage.src = previewUrl;
  uploadTitle.textContent = file.name;
  uploadSubtitle.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB selected`;
  show(previewWrap);
});

removeImageButton.addEventListener("click", () => {
  clearPreview();
  resetResults();
});

promptInput.addEventListener("input", () => {
  charCount.textContent = `${promptInput.value.length} / 1500`;
});

charCount.textContent = `${promptInput.value.length} / 1500`;

function makeDetail(label, value, extraClass = "") {
  const wrapper = document.createElement("div");
  const heading = document.createElement("span");
  heading.className = "detail-label";
  heading.textContent = label;
  const paragraph = document.createElement("p");
  paragraph.className = `detail-text ${extraClass}`.trim();
  paragraph.textContent = value || "Not provided.";
  wrapper.append(heading, paragraph);
  return wrapper;
}

function renderReport(data) {
  reportElement.replaceChildren();

  const summary = document.createElement("p");
  summary.className = "report-summary";
  summary.textContent = data.summary || "Analysis completed.";
  reportElement.append(summary);

  const status = document.createElement("div");
  status.className = "status-line";
  const statusLabels = {
    defects_found: "Visible issues reported — review each finding below.",
    no_visible_defects: "No visible defects identified in this screenshot.",
    needs_manual_review: "Manual review recommended.",
  };
  status.textContent = statusLabels[data.overall_status] || "Analysis completed.";
  reportElement.append(status);

  const findings = Array.isArray(data.findings) ? data.findings : [];
  findingCount.textContent = `${findings.length} ${findings.length === 1 ? "finding" : "findings"}`;

  if (findings.length === 0) {
    const noFindings = document.createElement("p");
    noFindings.className = "detail-text";
    noFindings.textContent = "No findings were returned. This does not prove the website is defect-free.";
    reportElement.append(noFindings);
  }

  findings.forEach((finding, index) => {
    const card = document.createElement("article");
    card.className = "finding-card";

    const top = document.createElement("div");
    top.className = "finding-top";
    const title = document.createElement("h3");
    title.textContent = `${index + 1}. ${finding.title || "Untitled finding"}`;
    const severity = document.createElement("span");
    const severityValue = ["low", "medium", "high"].includes(finding.severity) ? finding.severity : "low";
    severity.className = `severity ${severityValue}`;
    severity.textContent = severityValue;
    top.append(title, severity);
    card.append(top);

    const meta = document.createElement("div");
    meta.className = "meta-line";
    meta.textContent = `${finding.category || "other"} · Confidence: ${Number(finding.confidence) || 0}%`;
    card.append(meta);

    card.append(
      makeDetail("Visual evidence", finding.evidence),
      makeDetail("Suggested fix", finding.suggested_fix, "fix-text")
    );

    const location = document.createElement("div");
    location.className = "location-box";
    location.textContent = `Location: ${finding.location || "Not specified"} · Approximate box: left ${finding.x || 0}%, top ${finding.y || 0}%, width ${finding.width || 0}%, height ${finding.height || 0}%`;
    card.append(location);

    const track = document.createElement("div");
    track.className = "confidence-track";
    const fill = document.createElement("div");
    fill.className = "confidence-fill";
    fill.style.width = `${Math.max(0, Math.min(100, Number(finding.confidence) || 0))}%`;
    track.append(fill);
    card.append(track);

    if (finding.verification_needed) {
      const note = document.createElement("p");
      note.className = "verification";
      note.textContent = "Needs verification: confirm this issue in the live website before changing code.";
      card.append(note);
    }

    reportElement.append(card);
  });

  hide(emptyState);
  show(reportElement);
  show(downloadButton);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hide(errorBox);
  hide(reportElement);
  hide(downloadButton);

  const file = fileInput.files[0];
  const prompt = promptInput.value.trim();

  if (!file) {
    setError("Choose a screenshot first.");
    return;
  }
  if (!prompt) {
    setError("Enter a prompt describing what the AI should inspect.");
    return;
  }

  const formData = new FormData();
  formData.append("screenshot", file);
  formData.append("prompt", prompt);

  analyzeButton.disabled = true;
  buttonText.textContent = "Analyzing…";
  hide(emptyState);
  show(loadingState);
  findingCount.textContent = "Scanning";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(result.error || `Request failed (HTTP ${response.status}).`);
    }

    lastReport = result;
    renderReport(result);
    hide(loadingState);
  } catch (error) {
    hide(loadingState);
    show(emptyState);
    findingCount.textContent = "Scan failed";
    setError(error.message || "Could not analyze the screenshot. Try again.");
  } finally {
    analyzeButton.disabled = false;
    buttonText.textContent = "Analyze screenshot";
  }
});

downloadButton.addEventListener("click", () => {
  if (!lastReport) return;
  const blob = new Blob([JSON.stringify(lastReport, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ui-defect-report.json";
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
});
