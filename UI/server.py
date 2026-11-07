
import json
import os
import sys
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

UI_DIR = ROOT / "UI"
PIPELINE_FILE = ROOT / "run_pipeline.py"

OUTPUT_DIR = ROOT / "outputs" / "integrated_pipeline"
VERIFICATION_DIR = ROOT / "verification" / "verification_results"

app = FastAPI(
    title="OmniSight Dashboard API",
    description="Dashboard backend for the OmniSight self-healing pipeline",
    version="1.0.0"
)


# --------------------------------------------------
# PIPELINE STATE
# --------------------------------------------------

pipeline_state = {
    "running": False,
    "status": "idle",
    "message": "Pipeline is ready",
    "logs": [],
    "started_at": None,
    "finished_at": None,
    "return_code": None,
    "result": {}
}

state_lock = threading.Lock()


class RunRequest(BaseModel):
    target_url: HttpUrl


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def add_log(message):
    with state_lock:
        pipeline_state["logs"].append(message)


def latest_file(directory, filename):
    if not directory.exists():
        return None

    files = list(directory.rglob(filename))

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def latest_json(directory):
    if not directory.exists():
        return None

    files = list(directory.glob("*.json"))

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def relative_url(path, base_directory, route):
    if path is None or not path.exists():
        return None

    relative_path = path.relative_to(base_directory).as_posix()
    return f"/{route}/{relative_path}"


# --------------------------------------------------
# RESULT COLLECTION
# --------------------------------------------------

def build_result():
    result = {
        "defect": None,
        "before_screenshot": None,
        "after_screenshot": None,
        "focused_screenshot": None,
        "generated_css": None,
        "verification": None,
        "attempts": 0
    }

    # Read anomaly detection output
    detection_file = OUTPUT_DIR / "anomaly_detection.json"

    if detection_file.exists():
        try:
            with open(detection_file, "r", encoding="utf-8") as file:
                detection = json.load(file)

            anomalies = detection.get("anomalies", [])

            if isinstance(anomalies, list) and anomalies:
                result["defect"] = anomalies[0]

            elif detection.get("primary"):
                result["defect"] = detection["primary"]

            else:
                result["defect"] = detection

        except (json.JSONDecodeError, OSError) as error:
            add_log(f"Could not read anomaly report: {error}")

    # Before screenshot
    before = latest_file(
        OUTPUT_DIR / "context",
        "screenshot_full.png"
    )

    result["before_screenshot"] = relative_url(
        before, OUTPUT_DIR, "artifacts"
    )

    # After screenshot
    after = latest_file(
        OUTPUT_DIR / "repairs",
        "after_full.png"
    )

    result["after_screenshot"] = relative_url(
        after, OUTPUT_DIR, "artifacts"
    )

    # Focused component screenshot
    focused = latest_file(
        OUTPUT_DIR / "focused",
        "*.png"
    )

    if focused:
        result["focused_screenshot"] = relative_url(
            focused, OUTPUT_DIR, "artifacts"
        )

    # Generated CSS
    css_file = latest_file(
        OUTPUT_DIR / "repairs",
        "generated_fix.css"
    )

    if css_file:
        try:
            result["generated_css"] = css_file.read_text(
                encoding="utf-8"
            )
        except OSError:
            pass

    # Verification report
    report = latest_json(VERIFICATION_DIR)

    if report:
        try:
            with open(report, "r", encoding="utf-8") as file:
                result["verification"] = json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            add_log(f"Could not read verification report: {error}")

    # Count repair attempts
    repairs_directory = OUTPUT_DIR / "repairs"

    if repairs_directory.exists():
        result["attempts"] = sum(
            1 for path in repairs_directory.glob("attempt_*")
            if path.is_dir()
        )

    return result


# --------------------------------------------------
# PIPELINE EXECUTION
# --------------------------------------------------

def run_pipeline(target_url):
    global pipeline_state

    try:
        environment = os.environ.copy()
        environment["OMNISIGHT_TARGET"] = target_url

        add_log("Starting OmniSight self-healing pipeline...")

        process = subprocess.Popen(
            [sys.executable, "-u", str(PIPELINE_FILE)],
            cwd=str(ROOT),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1
        )

        for line in process.stdout:
            line = line.strip()

            if line:
                add_log(line)

        process.wait()

        result = build_result()

        with state_lock:
            pipeline_state["return_code"] = process.returncode
            pipeline_state["result"] = result
            pipeline_state["running"] = False
            pipeline_state["finished_at"] = datetime.now().isoformat()

            if process.returncode == 0:
                pipeline_state["status"] = "completed"
                pipeline_state["message"] = "Pipeline execution completed"
            else:
                pipeline_state["status"] = "failed"
                pipeline_state["message"] = "Pipeline execution failed"

        add_log("Pipeline execution finished.")

    except Exception as error:
        with state_lock:
            pipeline_state["running"] = False
            pipeline_state["status"] = "failed"
            pipeline_state["message"] = str(error)
            pipeline_state["finished_at"] = datetime.now().isoformat()

        add_log(f"Pipeline error: {error}")


# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

@app.get("/")
def dashboard():
    return FileResponse(UI_DIR / "index.html")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "OmniSight Dashboard API"
    }


@app.post("/api/run")
def start_pipeline(request: RunRequest):
    target_url = str(request.target_url)
    parsed_url = urlparse(target_url)

    # Only allow local test websites
    if parsed_url.hostname not in {"localhost", "127.0.0.1"}:
        raise HTTPException(
            status_code=400,
            detail="Only local test websites are allowed."
        )

    if not PIPELINE_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="run_pipeline.py was not found."
        )

    with state_lock:
        if pipeline_state["running"]:
            raise HTTPException(
                status_code=409,
                detail="Pipeline is already running."
            )

        pipeline_state.update({
            "running": True,
            "status": "running",
            "message": "Pipeline is executing",
            "logs": [],
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "return_code": None,
            "result": {}
        })

    thread = threading.Thread(
        target=run_pipeline,
        args=(target_url,),
        daemon=True
    )

    thread.start()

    return {
        "status": "started",
        "message": "OmniSight pipeline started successfully"
    }


@app.get("/api/status")
def get_pipeline_status():
    with state_lock:
        return pipeline_state.copy()


# --------------------------------------------------
# STATIC FILES
# --------------------------------------------------

app.mount(
    "/assets",
    StaticFiles(directory=UI_DIR),
    name="assets"
)

if OUTPUT_DIR.exists():
    app.mount(
        "/artifacts",
        StaticFiles(directory=OUTPUT_DIR),
        name="artifacts"
    )

if VERIFICATION_DIR.exists():
    app.mount(
        "/verification-reports",
        StaticFiles(directory=VERIFICATION_DIR),
        name="verification-reports"
    )
