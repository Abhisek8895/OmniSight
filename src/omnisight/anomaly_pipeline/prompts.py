"""Prompt that asks the VLM for output this stage can parse reliably.

The detector also copes with looser replies (see `vlm_parser.py`), but asking for
this schema gives the best coordinates: the model quotes `el#N` ids from the
context, so the exact DOM box can be used instead of a pixel guess.
"""

from __future__ import annotations

from typing import Any

from omnisight.context_pipeline.render import render_vlm_context

OUTPUT_SCHEMA = """\
Reply with ONLY a JSON object, no prose before or after:

{
  "anomalies": [
    {
      "element_id": 11,                  // the el#N id from the context, if the defect is on a listed element
      "related_element_id": null,        // second el#N for overlaps / occlusion, else null
      "type": "text-clipped",            // e.g. text-clipped, overlap, low-contrast, image-broken, misalignment ...
      "severity": "high",                // high | medium | low
      "confidence": 0.9,                 // 0..1
      "description": "Button label is cut off: 'Sign in securely'.",
      "bbox": [556, 315, 646, 357]       // [x1, y1, x2, y2] in CSS pixels of screenshot_full.png (top-left origin)
    }
  ]
}

Rules:
- The `// ...` comments above are explanations only; do not include them in your JSON.
- Order anomalies from most to least severe.
- Prefer `element_id` whenever the defect is on an element listed in the context; still give your best `bbox`.
- If the defect is NOT on a listed element (e.g. misalignment, wrong colour, uneven spacing), omit `element_id` and give a tight `bbox`.
- Coordinates are pixels of the full-page screenshot as given, NOT normalised.
- Confirm each automated hint against the image; drop false positives, and add defects the checks cannot see.
- If the page has no defects, return {"anomalies": []}.
"""

TASK = (
    "You are inspecting a rendered web page for visual UI defects. You receive the page screenshot(s) "
    "and structured context measured in the browser. Identify every anomalous UI component, say what is "
    "wrong, and locate it precisely."
)


def build_prompt(bundle: dict[str, Any], max_chars: int = 2_000) -> str:
    """Full text prompt: task + schema + the Week 2 `vlm_context.md` text view of the bundle."""
    context = render_vlm_context(bundle, max_chars)
    return f"{TASK}\n\n{OUTPUT_SCHEMA}\n---\n{context}"
