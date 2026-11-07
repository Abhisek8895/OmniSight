from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "Validation"))

from dotenv import load_dotenv

ENV_PATH = ROOT / "vlm_integration" / ".env"
load_dotenv(ENV_PATH)

from groq import Groq

from omnisight.context_pipeline.config import PipelineConfig, Viewport
from omnisight.context_pipeline.pipeline import run_pipeline as capture_context
from omnisight.anomaly_pipeline.prompts import build_prompt
from omnisight.anomaly_pipeline.detector import detect_anomalies
from omnisight.fix_pipeline.after_capture import run_after_fix
from omnisight.fix_pipeline.models import CssFix

from image_optimization.screenshot_chunking import chunk_screenshot
from image_optimization.screenshot_cropping import crop_image
from fix_generation.fix_generator import generate_fix
from fix_generation.code_extractor import extract_code_blocks
from code_validator import validate_code
from vlm_integration.test_vlm import analyze_screenshot
from verification.repair_verifier import verify_repair, save_verification_report


TARGET = os.getenv(
    "OMNISIGHT_TARGET",
    "http://127.0.0.1:8000/mock_website/"
)

MAX_RETRIES = 3
VIEWPORT = Viewport("desktop", 1366, 768)
OUTPUT = ROOT / "outputs" / "integrated_pipeline"


def parse_anomaly_json(response_text: str) -> list[dict]:
    """Extract the VLM's JSON anomaly list from one chunk response."""

    text = response_text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\s*```$", "", text)

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)

    if not match:
        return []

    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []

    items = (
        payload.get("anomalies", [])
        if isinstance(payload, dict)
        else payload
    )

    if not isinstance(items, list):
        return []

    normalized = []

    for item in items:
        if not isinstance(item, dict):
            continue

        item = dict(item)
        item.setdefault("coordinate_space", "css")
        item.setdefault("bbox_format", "xyxy")

        normalized.append(item)

    return normalized


def analyze_chunks(
    client,
    bundle: dict,
    screenshot_path: Path
) -> tuple[str, list[dict]]:
    """Send optimized screenshot chunks to the VLM."""

    chunk_dir = OUTPUT / "chunks"

    chunks = chunk_screenshot(
    screenshot_path=str(screenshot_path),
    output_dir=str(chunk_dir),
    chunk_width=400,
    chunk_height=400,
    overlap=50,
)

    if not chunks:
        raise RuntimeError(
            "Image optimization did not produce any screenshot chunks."
        )

    full_prompt = build_prompt(bundle)

    findings = []
    raw_responses = []

    for chunk in chunks:

        chunk_path = chunk_dir / chunk["filename"]
        coords = chunk["coordinates"]

        prompt = (
            full_prompt
            + "\n\nCHUNK INSTRUCTIONS:\n"
            + f"You are viewing a crop from the full-page screenshot. "
              f"The crop origin in full-page CSS pixels is "
              f"x={coords['x1']}, y={coords['y1']}; "
              f"crop size is {chunk['width']}x{chunk['height']}.\n"
            + "Return the required JSON schema. Report bbox as "
              "[x1,y1,x2,y2] in FULL-PAGE CSS PIXELS, not crop-local pixels. "
              "Add the crop origin to any coordinates measured inside this "
              "crop. Only report defects visible in this crop. "
              'If none, return {"anomalies": []}.'
        )

        response = analyze_screenshot(
            client,
            chunk_path,
            prompt=prompt
        )

        if not response:
            continue

        raw_responses.append(
            f"CHUNK {chunk['chunk_id']} ({coords}):\n{response}"
        )

        findings.extend(parse_anomaly_json(response))

    return "\n\n".join(raw_responses), findings


def main() -> int:

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            f"GROQ_API_KEY is missing. Add it to {ENV_PATH} "
            "(do not commit that file)."
        )

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    OUTPUT.mkdir(parents=True, exist_ok=True)

    cfg = PipelineConfig(
        output_dir=str(OUTPUT / "context"),
        viewports=(VIEWPORT,),
        headless=True,
        scroll_to_load=True,
    )

    print("[1/7] Capturing page context and baseline screenshot...")

    captures = capture_context(
        targets=[TARGET],
        cfg=cfg,
        viewports=[VIEWPORT],
        output_dir=OUTPUT / "context",
    )

    viewport_result = captures[0]["viewports"][VIEWPORT.name]

    if "error" in viewport_result:
        raise RuntimeError(viewport_result["error"])

    context_path = Path(viewport_result["context"])

    bundle = json.loads(
        context_path.read_text(encoding="utf-8")
    )

    screenshot_path = context_path.parent / "screenshot_full.png"

    if not screenshot_path.is_file():
        raise FileNotFoundError(
            f"Context screenshot not found: {screenshot_path}"
        )

    print(
        "[2/7] Optimizing screenshot into overlapping chunks "
        "and running VLM detection..."
    )

    raw_vlm_report, findings = analyze_chunks(
        client,
        bundle,
        screenshot_path
    )

    if not findings:
        print(
            "No machine-readable UI anomalies were returned by the VLM."
        )

        print(
            "Raw chunk responses are saved in the run output for inspection."
        )

        (OUTPUT / "vlm_chunk_responses.txt").write_text(
            raw_vlm_report,
            encoding="utf-8"
        )

        return 0

    detection = detect_anomalies(
        bundle,
        {
            "anomalies": findings,
            "coordinate_space": "css"
        },
    )

    detection_path = OUTPUT / "anomaly_detection.json"

    detection_path.write_text(
        json.dumps(
            detection.to_dict(),
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    primary = detection.primary

    if primary is None:
        print(
            "The VLM returned findings, but none could be mapped "
            "to the page DOM."
        )

        print(f"Detection details: {detection_path}")

        return 1

    selector = (
        primary.element.get("selector")
        if primary.element
        else None
    )

    defect = primary.description
    bbox = primary.bbox

    print(f"Primary defect: {defect}")

    print(
        f"Target selector: "
        f"{selector or '(not resolved; CSS must contain its own selector)'}"
    )

    print(
        "[3/7] Cropping the anomalous component "
        "for focused VLM inspection..."
    )

    crop_result = crop_image(
        image_path=str(screenshot_path),
        coordinates=(
            bbox.x,
            bbox.y,
            bbox.x2,
            bbox.y2
        ),
        padding=24,
        output_dir=str(OUTPUT / "focused"),
    )

    focused_image = (
        OUTPUT / "focused" / crop_result["filename"]
    )

    focused_prompt = (
        "Inspect this cropped UI component only. "
        "Confirm the visible defect and describe the smallest "
        "CSS-only correction. Do not invent selectors or claim "
        "that a change has already been applied. "
        "Original defect: "
        + defect
        + f"\nDOM selector from browser context: "
        f"{selector or 'not resolved'}"
    )

    focused_analysis = analyze_screenshot(
        client,
        focused_image,
        prompt=focused_prompt
    )

    feedback = ""

    for attempt in range(1, MAX_RETRIES + 1):

        print(
            f"[4/7] Generating CSS repair "
            f"(attempt {attempt}/{MAX_RETRIES})..."
        )

        repair_context = {
            "original_defect": defect,
            "severity": primary.severity,
            "confidence": primary.confidence,
            "target_selector": selector,
            "element_context": primary.element,
            "focused_vlm_analysis": focused_analysis,
            "relevant_existing_css": (
                bundle.get("css", {}).get("text", "")[:10000]
            ),
            "previous_verification_feedback": feedback,
        }

        ai_response = generate_fix(
            json.dumps(
                repair_context,
                ensure_ascii=False
            )
        )

        code_blocks = extract_code_blocks(ai_response)

        css_blocks = [
            block
            for block in code_blocks
            if block["language"] == "css"
        ]

        if not css_blocks:
            raise RuntimeError(
                "Fix generator did not return a CSS fenced code block. "
                "Check the generated response and fix-generation prompt."
            )

        css_code = css_blocks[0]["code"]

        validation = validate_code(css_code, "css")

        if not validation["valid"]:

            feedback = (
                f"Generated CSS was rejected: "
                f"{validation['reason']}"
            )

            print(feedback)

            continue

        print(
            "[5/7] Applying validated CSS and capturing "
            "before/after screenshots..."
        )

        attempt_output = (
            OUTPUT / "repairs" / f"attempt_{attempt}"
        )

        repair_results = run_after_fix(
            targets=[TARGET],
            cfg=cfg,
            fixes=[
                CssFix(
                    css=css_code,
                    selector=selector
                )
            ],
            viewports=[VIEWPORT],
            output_dir=attempt_output,
        )

        attempt_view = (
            repair_results[0]["viewports"][VIEWPORT.name]
        )

        if attempt_view["status"] != "ok":

            feedback = (
                "CSS application/capture failed: "
                f"{attempt_view.get('error')}"
            )

            print(feedback)

            continue

        after_screenshot = (
            Path(attempt_view["dir"]) / "after_full.png"
        )

        if not after_screenshot.is_file():

            feedback = (
                "Post-fix screenshot was not created: "
                f"{after_screenshot}"
            )

            print(feedback)

            continue

        print(
            "[6/7] Verifying the actual post-fix screenshot "
            "with the VLM..."
        )

        verification, raw_verification = verify_repair(
            client,
            after_screenshot,
            defect,
        )

        report_path = save_verification_report(
            verification,
            after_screenshot,
            defect,
            raw_verification,
        )

        print(
            f"Verification: {verification['status']} "
            f"(confidence: {verification['confidence']})"
        )

        print(f"Verification report: {report_path}")

        if verification["status"] == "FIXED":

            print(
                f"[7/7] Repair verified successfully "
                f"on attempt {attempt}."
            )

            print(f"Run artifacts: {OUTPUT}")

            return 0

        feedback = (
            f"Previous repair verification status: "
            f"{verification['status']}. "
            f"Evidence: {verification['evidence']}. "
            f"Reason: {verification['reason']}. "
            "Generate a revised CSS repair."
        )

        print(
            "The original defect is not yet confirmed fixed; retrying..."
        )

    print(
        f"Maximum repair attempts reached. "
        f"Inspect artifacts in: {OUTPUT}"
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())