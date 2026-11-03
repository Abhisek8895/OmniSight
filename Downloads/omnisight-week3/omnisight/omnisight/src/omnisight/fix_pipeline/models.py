"""Shared data contract for Week 3 (Task 1 CSS application + Task 2 screenshots).

Both tasks import from here, so merging them only requires that Task 1
produces `CssFix` inputs / an `ApplyResult` and Task 2 consumes them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- per-fix outcome statuses (Task 1 sets these, Task 2 records them) ------
APPLIED = "applied"
TARGET_NOT_FOUND = "target_not_found"
INVALID_SELECTOR = "invalid_selector"
INVALID_CSS = "invalid_css"
APPLY_ERROR = "apply_error"

# --- overall run statuses (Task 2 sets these) ------------------------------
STATUS_OK = "ok"
STATUS_APPLY_FAILED = "apply_failed"
STATUS_RENDER_FAILED = "render_failed"
STATUS_CAPTURE_FAILED = "capture_failed"


@dataclass(frozen=True)
class CssFix:
    """One validated CSS fix produced by the AI.

    `css` is either a list of declarations (`"width:auto; white-space:normal"`,
    which needs `selector`) or complete rules (`".submit { width:auto }"`).
    `selector` is the DOM element the fix targets; it is optional when `css`
    carries its own selectors (a whole stylesheet).
    `element_id` / `hint_id` link back to the Week 2 `context.json` ids.
    """

    css: str
    selector: str | None = None
    element_id: int | None = None
    hint_id: int | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CssFix":
        css = d.get("css") or d.get("fix_css") or d.get("code") or ""
        return cls(
            css=str(css),
            selector=(d.get("selector") or None),
            element_id=d.get("element_id"),
            hint_id=d.get("hint_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "selector": self.selector,
            "element_id": self.element_id,
            "hint_id": self.hint_id,
            "css": self.css,
        }


@dataclass
class FixOutcome:
    """What happened when one `CssFix` was applied to the live DOM."""

    index: int
    status: str
    selector: str | None = None
    matched: int | None = None          # elements matched by `selector`
    message: str = ""
    element_id: int | None = None
    hint_id: int | None = None

    @property
    def applied(self) -> bool:
        return self.status == APPLIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "status": self.status,
            "selector": self.selector,
            "matched": self.matched,
            "message": self.message,
            "element_id": self.element_id,
            "hint_id": self.hint_id,
        }


@dataclass
class ApplyResult:
    """Aggregate result of applying a list of fixes to one page."""

    outcomes: list[FixOutcome] = field(default_factory=list)
    applied_css: str = ""               # the CSS that actually went into the page

    @property
    def applied_count(self) -> int:
        return sum(o.applied for o in self.outcomes)

    @property
    def failed_count(self) -> int:
        return len(self.outcomes) - self.applied_count

    @property
    def ok(self) -> bool:
        """True when at least one fix was applied."""
        return self.applied_count > 0

    @property
    def all_applied(self) -> bool:
        return bool(self.outcomes) and self.failed_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "all_applied": self.all_applied,
            "applied": self.applied_count,
            "failed": self.failed_count,
            "outcomes": [o.to_dict() for o in self.outcomes],
        }
