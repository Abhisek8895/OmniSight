"""Week 2: Screenshot & HTML Context Pipeline.

Captures screenshots of a page and collects the HTML/CSS context a
vision-language model needs to find UI defects and propose fixes.
"""

from omnisight.context_pipeline.config import PipelineConfig, Viewport, load_config
from omnisight.context_pipeline.pipeline import capture_context, run_pipeline
from omnisight.context_pipeline.render import render_vlm_context

__all__ = [
    "PipelineConfig",
    "Viewport",
    "load_config",
    "capture_context",
    "run_pipeline",
    "render_vlm_context",
]
