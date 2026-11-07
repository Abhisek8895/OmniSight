"""Load AI-generated fixes from disk into `CssFix` objects."""

from __future__ import annotations

import json
from pathlib import Path

from omnisight.fix_pipeline.models import CssFix


def load_fixes(path: str | Path, selector: str | None = None) -> list[CssFix]:
    """Read fixes from a `.json` or `.css` file.

    Accepted shapes:

    * `.css`  - one fix; `selector` (optional) is attached to bare declarations.
    * `.json` - a list of fix objects, or `{"fixes": [...]}`, or one fix object.
      Each object: `{"selector", "css", "element_id"?, "hint_id"?}`.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        raw = json.loads(text)
        if isinstance(raw, dict):
            raw = raw.get("fixes", [raw])
        if not isinstance(raw, list):
            raise ValueError(f"{p}: expected a list of fixes or an object with a 'fixes' list")
        return [CssFix.from_dict(item) for item in raw]
    return [CssFix(css=text, selector=selector)]
