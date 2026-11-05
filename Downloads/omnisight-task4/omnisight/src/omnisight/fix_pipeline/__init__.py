"""Week 3: apply AI-generated CSS fixes (Task 1) and capture before/after screenshots (Task 2).

Merge point between the two tasks: `CssFixApplier.apply(page, fixes) -> ApplyResult`.
"""

from omnisight.fix_pipeline.after_capture import (
    AfterFixOptions,
    capture_before_after,
    run_after_fix,
    wait_for_render,
)
from omnisight.fix_pipeline.css_applier import CssFixApplier, DomCssApplier
from omnisight.fix_pipeline.loader import load_fixes
from omnisight.fix_pipeline.models import ApplyResult, CssFix, FixOutcome

__all__ = [
    "AfterFixOptions",
    "ApplyResult",
    "CssFix",
    "CssFixApplier",
    "DomCssApplier",
    "FixOutcome",
    "capture_before_after",
    "load_fixes",
    "run_after_fix",
    "wait_for_render",
]
