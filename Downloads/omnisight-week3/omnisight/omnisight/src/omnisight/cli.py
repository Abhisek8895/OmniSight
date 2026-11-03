"""Command line interface: `omnisight capture` and `omnisight render`."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from omnisight.context_pipeline.config import PipelineConfig, Viewport, load_config, load_targets
from omnisight.context_pipeline.pipeline import run_pipeline
from omnisight.context_pipeline.render import render_vlm_context


def _parse_viewports(spec: str, cfg: PipelineConfig) -> list[Viewport]:
    by_name = {v.name: v for v in cfg.viewports}
    out: list[Viewport] = []
    for part in (p.strip() for p in spec.split(",") if p.strip()):
        if part in by_name:
            out.append(by_name[part])
            continue
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})(m?)", part)
        if not m:
            raise SystemExit(
                f"Unknown viewport {part!r}. Use a configured name ({', '.join(by_name)}) "
                "or WIDTHxHEIGHT (append 'm' for mobile emulation), e.g. 1280x720 or 390x844m."
            )
        out.append(Viewport(part, int(m.group(1)), int(m.group(2)), is_mobile=bool(m.group(3))))
    return out


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="omnisight",
        description="OmniSight - Week 2: screenshot & HTML/CSS context pipeline for the UI-defect VLM.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("capture", help="Capture screenshots and HTML/CSS context for pages.")
    c.add_argument("targets", nargs="*", help="URLs or local HTML files (default: `targets:` from config).")
    c.add_argument("-c", "--config", help="YAML config file (see config/default.yaml).")
    c.add_argument("-o", "--output", help="Output directory (default: outputs).")
    c.add_argument("--viewports", help="Comma list of viewport names or WIDTHxHEIGHT[m], e.g. desktop,mobile,1280x720.")
    c.add_argument("--wait-for", dest="wait_for", help="CSS selector to wait for (e.g. '#root > *' for React apps).")
    c.add_argument("--wait-until", choices=["load", "domcontentloaded", "networkidle", "commit"])
    c.add_argument("--timeout-ms", type=int)
    c.add_argument("--no-full-page", action="store_true", help="Skip the full-page screenshot.")
    c.add_argument("--no-annotate", action="store_true", help="Skip the annotated screenshot.")
    c.add_argument("--no-scroll", action="store_true", help="Do not scroll to trigger lazy loading.")
    c.add_argument("--max-context-chars", type=int, help="Budget for vlm_context.md.")
    c.add_argument("--json", action="store_true", help="Print the run manifest as JSON.")

    a = sub.add_parser(
        "after-fix",
        help="Week 3: apply CSS fixes / render a repaired page and save before/after screenshots.",
    )
    a.add_argument("target", help="Original page: URL or local HTML file.")
    src = a.add_mutually_exclusive_group(required=True)
    src.add_argument("--fix", help="Fixes file: .json (list of {selector, css}) or .css.")
    src.add_argument("--css", help="Inline CSS (declarations need --selector).")
    src.add_argument("--repaired", help="An already-repaired page (URL or HTML file) to shoot as 'after'.")
    a.add_argument("--selector", help="Target element selector for a .css file / --css declarations.")
    a.add_argument("-c", "--config", help="YAML config file (see config/default.yaml).")
    a.add_argument("-o", "--output", help="Output directory (default: outputs).")
    a.add_argument("--viewports", help="Comma list of viewport names or WIDTHxHEIGHT[m].")
    a.add_argument("--wait-for", dest="wait_for", help="CSS selector to wait for before capturing.")
    a.add_argument("--timeout-ms", type=int)
    a.add_argument("--before-image", help="Reuse this screenshot (e.g. Week 2 screenshot_full.png) as 'before'.")
    a.add_argument("--capture-on-failure", action="store_true", help="Take the 'after' shot even if no fix applied.")
    a.add_argument("--no-comparison", action="store_true", help="Skip comparison.png / diff.png.")
    a.add_argument("--json", action="store_true", help="Print the results as JSON.")

    r = sub.add_parser("render", help="Re-render vlm_context.md from an existing context.json.")
    r.add_argument("context", help="Path to context.json")
    r.add_argument("--max-chars", type=int, default=60_000)
    r.add_argument("--suspect-limit", type=int, default=15)
    r.add_argument("-o", "--output", help="Write to a file instead of stdout.")
    return p


def _cmd_capture(args: argparse.Namespace) -> int:
    cfg = load_config(
        args.config,
        wait_for_selector=args.wait_for,
        wait_until=args.wait_until,
        timeout_ms=args.timeout_ms,
        max_context_chars=args.max_context_chars,
        **({"capture_full_page": False} if args.no_full_page else {}),
        **({"annotate": "none"} if args.no_annotate else {}),
        **({"scroll_to_load": False} if args.no_scroll else {}),
    )
    targets = list(args.targets)
    if not targets and args.config:
        targets = load_targets(args.config)
    if not targets:
        print("No targets given. Pass URLs/files or set `targets:` in the config.", file=sys.stderr)
        return 2
    viewports = _parse_viewports(args.viewports, cfg) if args.viewports else None

    results = run_pipeline(targets, cfg, viewports=viewports, output_dir=args.output)

    if args.json:
        print(json.dumps(results, indent=2))
    failures = 0
    for entry in results:
        if not args.json:
            print(f"\n{entry['target']}")
        for name, info in entry["viewports"].items():
            if "error" in info:
                failures += 1
                print(f"  {name:<8} FAILED  {info['error']}", file=sys.stderr)
                continue
            if not args.json:
                s = info["summary"]
                h = s["hints"]
                print(
                    f"  {name:<8} {s['document']:>10}px  {s['elements']:>3} elements  "
                    f"{s['css_rules']:>3} css rules  hints: {h['high']} high / {h['medium']} medium / {h['low']} low"
                    f"  -> {info['dir']}"
                )
    return 1 if failures else 0


def _cmd_after_fix(args: argparse.Namespace) -> int:
    # Imported here so `capture`/`render` keep working if Week 3 code is absent.
    from omnisight.fix_pipeline import AfterFixOptions, CssFix, load_fixes, run_after_fix

    cfg = load_config(args.config, wait_for_selector=args.wait_for, timeout_ms=args.timeout_ms)
    viewports = _parse_viewports(args.viewports, cfg) if args.viewports else None
    fixes = None
    if args.fix:
        fixes = load_fixes(args.fix, selector=args.selector)
    elif args.css:
        fixes = [CssFix(css=args.css, selector=args.selector)]
    opts = AfterFixOptions(
        capture_on_apply_failure=args.capture_on_failure,
        make_comparison=not args.no_comparison,
        make_diff=not args.no_comparison,
    )
    results = run_after_fix(
        [args.target], cfg, fixes=fixes, repaired_target=args.repaired,
        viewports=viewports, output_dir=args.output, options=opts, before_image=args.before_image,
    )
    if args.json:
        print(json.dumps(results, indent=2))
    failures = 0
    for entry in results:
        if not args.json:
            print(f"\n{entry['target']}")
        for name, info in entry["viewports"].items():
            if info["status"] != "ok":
                failures += 1
                print(f"  {name:<8} {info['status'].upper()}  {info['error']}", file=sys.stderr)
            elif not args.json:
                changed = "changed" if info["visible_change"] else "NO visible change"
                print(f"  {name:<8} ok  ({changed})  -> {info['dir']}")
    return 1 if failures else 0


def _cmd_render(args: argparse.Namespace) -> int:
    bundle = json.loads(Path(args.context).read_text(encoding="utf-8"))
    text = render_vlm_context(bundle, args.max_chars, args.suspect_limit)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {len(text)} characters to {args.output}")
    else:
        sys.stdout.write(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "capture":
        return _cmd_capture(args)
    if args.command == "after-fix":
        return _cmd_after_fix(args)
    return _cmd_render(args)


if __name__ == "__main__":
    raise SystemExit(main())
