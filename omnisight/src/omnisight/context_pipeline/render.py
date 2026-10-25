"""Render a context bundle into compact, prompt-ready text for the VLM.

The bundle (context.json) is the full-fidelity record. This module produces
the budgeted text view the Week 3 prompts will embed next to the screenshots.
"""

from __future__ import annotations

import re

_SEV_ORDER = {"high": 3, "medium": 2, "low": 1}
_UNIVERSAL_PART = re.compile(r"\*?(::?[\w-]+)*")


def _is_universal(selector: str) -> bool:
    """`*`, `*::before`, `*, *::after` ... apply to everything and say nothing about one element."""
    return all(_UNIVERSAL_PART.fullmatch(p.strip()) for p in selector.split(","))


def _cap(text: str, limit: int, note: str = "") -> str:
    """Cut `text` at a line boundary so it fits `limit` characters."""
    if len(text) <= limit:
        return text
    cut = text.rfind("\n", 0, max(limit, 1))
    cut = cut if cut > 0 else limit
    omitted = len(text) - cut
    tail = f"\n… [{omitted} more characters omitted{(' — ' + note) if note else ''}]"
    return text[:cut] + tail


def _bbox(b: dict) -> str:
    return f"x={b['x']:.0f} y={b['y']:.0f} w={b['w']:.0f} h={b['h']:.0f}"


def _hint_line(h: dict) -> str:
    ref = ""
    if h.get("element_id"):
        ref = f" el#{h['element_id']}"
        if h.get("related_id"):
            ref += f"↔el#{h['related_id']}"
    return f"- H{h['id']} [{h['severity']}] {h['type']}{ref}: {h['message']}"


def _section_header(bundle: dict) -> str:
    pg, vp = bundle["page"], bundle["viewport"]
    doc = pg["document"]
    lines = [
        "# Page context",
        f"- URL: {bundle['target']['url']}",
        f"- Title: {pg.get('title') or '(none)'}",
        f"- Viewport: {vp['name']} {vp['width']}×{vp['height']}px"
        + (" (mobile emulation)" if vp.get("is_mobile") else ""),
        f"- Full document size: {doc['scroll_width']}×{doc['scroll_height']}px",
        "- All coordinates are CSS pixels, origin at the top-left of the full page, "
        "so they map 1:1 onto the screenshots.",
    ]
    if pg.get("horizontal_overflow"):
        o = pg["horizontal_overflow"]
        lines.append(
            f"- ⚠ Horizontal scroll: content is {o['scrollWidth']}px wide in a {o['clientWidth']}px viewport."
        )
    diag = bundle.get("diagnostics", {})
    problems = []
    if diag.get("page_errors"):
        problems.append(f"{len(diag['page_errors'])} uncaught JS errors")
    if diag.get("console_errors"):
        problems.append(f"{len(diag['console_errors'])} console errors/warnings")
    if diag.get("failed_requests"):
        problems.append(f"{len(diag['failed_requests'])} failed requests")
    if diag.get("http_errors"):
        problems.append(f"{len(diag['http_errors'])} HTTP errors")
    if problems:
        lines.append("- Load problems: " + ", ".join(problems) + " (see Diagnostics).")
    failed_fonts = [f for f in pg.get("font_faces", []) if f["status"] == "error"]
    if failed_fonts:
        lines.append("- ⚠ Web fonts failed to load: " + ", ".join(sorted({f["family"] for f in failed_fonts})))
    return "\n".join(lines)


def _section_screenshots(bundle: dict) -> str:
    s = bundle["screenshots"]
    lines = ["## Screenshots"]
    for key in ("viewport", "full_page", "annotated"):
        if s.get(key):
            lines.append(f"- `{s[key]['path']}` ({s[key]['width']}×{s[key]['height']}): {s[key]['description']}")
    fp = s.get("full_page")
    if fp and fp.get("truncated"):
        doc = bundle["page"]["document"]
        lines.append(
            f"- ⚠ The page is {doc['scroll_width']}×{doc['scroll_height']}px but screenshots only cover "
            f"{fp['width']}×{fp['height']}px. Elements below/right of that exist only in the HTML/CSS context."
        )
    if s.get("tiles"):
        t = s["tiles"]
        lines.append(
            f"- {len(t)} tiles in `tiles/` (full-width slices, top to bottom, overlapping) for reading small text: "
            + ", ".join(f"{x['path'].split('/')[-1]} y={x['y_start']}–{x['y_end']}" for x in t)
        )
    if s.get("crops"):
        lines.append(
            "- Zoomed crops of the most serious suspects in `crops/`: "
            + ", ".join(f"{c['path'].split('/')[-1]}" for c in s["crops"])
        )
    return "\n".join(lines)


def _section_hints(bundle: dict) -> str:
    hints = bundle["hints"]
    if not hints:
        return "## Automated layout checks\nNo issues flagged by the heuristics. Rely on the screenshots for visual defects."
    lines = [
        "## Automated layout checks",
        "Heuristic findings measured in the browser. They are leads, not verdicts: confirm each one "
        "against the screenshot and look for visual defects they cannot measure (misalignment, "
        "inconsistent spacing, wrong colours, broken imagery).",
    ]
    lines += [_hint_line(h) for h in hints]
    return "\n".join(lines)


def _rule_line(rule: dict) -> str:
    body = f"{rule['selector']} {{ {rule['css']} }}"
    for at in reversed(rule["at"]):
        body = f"{at} {{ {body} }}"
    flags = []
    if rule["at"] and not rule["media_active"]:
        flags.append("NOT active at this viewport")
    if rule["states"]:
        flags.append("pseudo-state/element")
    src = rule["source"].rsplit("/", 1)[-1]
    return f"  r{rule['id']} ({src}): {body}" + (f"  /* {', '.join(flags)} */" if flags else "")


def _section_suspects(bundle: dict, limit: int) -> str:
    els = {e["id"]: e for e in bundle["elements"]}
    rules = {r["id"]: r for r in bundle["css"]["rules"]}
    by_el: dict[int, list[dict]] = {}
    for h in sorted(bundle["hints"], key=lambda x: (-_SEV_ORDER[x["severity"]], x["id"])):
        for key in ("element_id", "related_id"):
            eid = h.get(key)
            if eid in els:
                by_el.setdefault(eid, []).append(h)
    if not by_el:
        return ""
    lines = ["## Suspect elements (detail)"]
    for eid, hs in list(by_el.items())[:limit]:
        e = els[eid]
        lines.append(f"\n### el#{eid}  `{e['selector']}`  <{e['tag']}>")
        lines.append(f"- Flagged by: {', '.join('H' + str(h['id']) for h in hs)}")
        lines.append(f"- Box: {_bbox(e['bbox'])}" + ("" if e["in_viewport"] else "  (below the fold)"))
        if e.get("text"):
            lines.append(f"- Text: \"{e['text']}\"")
        if e.get("react"):
            r = e["react"]
            lines.append(
                f"- React component: {' ← '.join(r['components'])}" + (f"  ({r['source']})" if r.get("source") else "")
            )
        if e["attrs"].get("style"):
            lines.append(f"- Inline style: `{e['attrs']['style']}`")
        if e["styles"]:
            lines.append("- Computed (non-default): " + "; ".join(f"{k}: {v}" for k, v in e["styles"].items()))
        if e.get("html_snippet"):
            lines.append(f"- HTML: `{e['html_snippet']}`")
        applicable = [
            rules[i] for i in e["rule_ids"] if i in rules and not _is_universal(rules[i]["selector"])
        ][:10]
        if applicable:
            lines.append("- CSS rules that apply (cascade order):")
            lines += [_rule_line(r) for r in applicable]
    return "\n".join(lines)


def _section_element_map(bundle: dict, limit: int) -> str:
    rows = []
    for e in bundle["elements"]:
        if not (e.get("text") or e.get("flags") or e["tag"] in ("img", "button", "a", "input", "select", "textarea", "nav", "header", "footer", "form", "h1", "h2", "h3")):
            continue
        txt = f' "{e["text"][:50]}"' if e.get("text") else ""
        flag = f" ⚑{','.join(e['flags'])}" if e["flags"] else ""
        rows.append(f"el#{e['id']} <{e['tag']}> {e['selector']} @ {_bbox(e['bbox'])}{txt}{flag}")
    if not rows:
        return ""
    return _cap("## Element map (id, selector, page-coordinate box, text)\n" + "\n".join(rows), limit, "see context.json for all elements")


def _section_css(bundle: dict, limit: int) -> str:
    css = bundle["css"]
    st = css["stats"]
    head = (
        f"## Relevant CSS ({st['kept']} of {st['total']} rules match elements on this page; "
        f"unmatched rules dropped, cascade order preserved)"
    )
    if st.get("unavailable"):
        head += "\n⚠ Could not read: " + ", ".join(st["unavailable"])
    return _cap(head + "\n```css\n" + css["text"].rstrip() + "\n```", limit, "see styles.css")


def _section_html(bundle: dict, limit: int) -> str:
    h = bundle["html"]
    head = (
        "## Rendered HTML (cleaned: scripts, styles, SVG internals removed; `data-omni-id` = el#)"
    )
    if h.get("omitted_subtrees"):
        head += f"\n{h['omitted_subtrees']} large unflagged subtrees were collapsed to fit the budget."
    return _cap(head + "\n```html\n" + h["text"].rstrip() + "\n```", limit, "see page.cleaned.html")


def _section_diagnostics(bundle: dict) -> str:
    d = bundle.get("diagnostics", {})
    lines = []
    for label, key, fmt in (
        ("Uncaught JS errors", "page_errors", lambda x: x),
        ("Console errors/warnings", "console_errors", lambda x: x),
        ("Failed requests", "failed_requests", lambda x: f"{x['type']} {x['url']} ({x['error']})"),
        ("HTTP errors", "http_errors", lambda x: f"{x['status']} {x['type']} {x['url']}"),
    ):
        items = d.get(key) or []
        if items:
            lines.append(f"- {label}:")
            lines += [f"  - {fmt(i)[:200]}" for i in items[:8]]
    return "## Diagnostics\n" + "\n".join(lines) if lines else ""


def render_vlm_context(bundle: dict, max_chars: int = 60_000, suspect_limit: int = 15) -> str:
    """Compose the text half of the VLM input within `max_chars`.

    Priority order: header, screenshots, layout hints, suspect detail,
    diagnostics, element map, relevant CSS, then HTML with whatever is left.
    """
    parts: list[str] = []
    used = 0

    def add(text: str, cap: int | None = None) -> None:
        nonlocal used
        if not text:
            return
        if cap is not None:
            text = _cap(text, cap)
        parts.append(text)
        used += len(text) + 2

    add(_section_header(bundle))
    add(_section_screenshots(bundle))
    add(_section_hints(bundle), cap=int(max_chars * 0.20))
    add(_section_suspects(bundle, suspect_limit), cap=int(max_chars * 0.30))
    add(_section_diagnostics(bundle), cap=int(max_chars * 0.05))
    remaining = max(max_chars - used, 0)
    add(_section_element_map(bundle, int(remaining * 0.25)))
    remaining = max(max_chars - used, 0)
    add(_section_css(bundle, int(remaining * 0.45)))
    remaining = max(max_chars - used, 0)
    add(_section_html(bundle, remaining))
    return "\n\n".join(p for p in parts if p) + "\n"
