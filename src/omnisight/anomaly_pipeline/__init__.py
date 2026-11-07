"""Week 4 / Task 4: anomaly detection and bounding-box extraction from VLM analysis.

    from omnisight.anomaly_pipeline import load_bundle, detect_anomalies

    bundle = load_bundle("outputs/sample_run/defective-login/desktop")
    result = detect_anomalies(bundle, vlm_reply_text)
    result.primary.bbox      # BBox(x=556.5, y=315, w=90, h=42)  CSS px, full-page origin
"""

from omnisight.anomaly_pipeline.bbox import BBox
from omnisight.anomaly_pipeline.context import ContextIndex, load_bundle
from omnisight.anomaly_pipeline.detector import detect_anomalies
from omnisight.anomaly_pipeline.models import Anomaly, DetectionResult, RawFinding
from omnisight.anomaly_pipeline.output import write_outputs
from omnisight.anomaly_pipeline.prompts import build_prompt
from omnisight.anomaly_pipeline.vlm_parser import parse_vlm_response

__all__ = [
    "Anomaly",
    "BBox",
    "ContextIndex",
    "DetectionResult",
    "RawFinding",
    "build_prompt",
    "detect_anomalies",
    "load_bundle",
    "parse_vlm_response",
    "write_outputs",
]
