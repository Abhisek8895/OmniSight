# Page context
- URL: file:///home/claude/omnisight/samples/defective_dashboard.html
- Title: Defective dashboard (test fixture)
- Viewport: mobile 375×812px (mobile emulation)
- Full document size: 375×900px
- All coordinates are CSS pixels, origin at the top-left of the full page, so they map 1:1 onto the screenshots.
- Load problems: 1 console errors/warnings, 1 failed requests (see Diagnostics).
- ⚠ Web fonts failed to load: Brand Sans

## Screenshots
- `screenshot_viewport.png` (375×812): Above-the-fold view exactly as a user first sees it.
- `screenshot_full.png` (375×900): Entire scrollable page.
- `screenshot_annotated.png` (375×900): Same page with numbered boxes (H<n>) marking elements flagged by the layout checks. Colour: red=high, orange=medium, blue=low severity.
- Zoomed crops of the most serious suspects in `crops/`: h01_clipped-by-ancestor.png, h02_overlay-covers-content.png, h03_low-contrast.png, h04_occluded.png, h05_small-tap-target.png

## Automated layout checks
Heuristic findings measured in the browser. They are leads, not verdicts: confirm each one against the screenshot and look for visual defects they cannot measure (misalignment, inconsistent spacing, wrong colours, broken imagery).
- H1 [high] clipped-by-ancestor el#9↔el#6: Text is cut off by an ancestor with overflow:hidden (#card-revenue): "Up 12% on last month, driven by enterpr…".
- H2 [high] overlay-covers-content el#30: #root > div.cookie:nth-of-type(3) is painted over 17 visible elements.
- H3 [high] low-contrast el#4: Contrast 1.9:1 is below 4.5:1 for "Last synced 2 minutes ago".
- H4 [medium] occluded el#27↔el#31: Covered by #root > div.cookie:nth-of-type(3) > div.bar at its centre point.
- H5 [low] small-tap-target el#32: Interactive target is only 56.8×21px (WCAG 2.2 minimum is 24×24).

## Suspect elements (detail)

### el#9  `#card-revenue > p.notes`  <p>
- Flagged by: H1
- Box: x=36 y=160 w=303 h=55
- Text: "Up 12% on last month, driven by enterprise renewals in the EMEA region and two large expansions that closed late."
- Computed (non-default): margin: 8px 0px 0px; color: rgb(226, 232, 240); font-family: "Brand Sans", Helvetica, Arial, sans-serif; font-size: 13px; line-height: 18.2px
- HTML: `<p class="notes" data-omni-id="9">Up 12% on last month, driven by enterprise renewals in the EMEA region and two large expansions that closed late.</p>`
- CSS rules that apply (cascade order):
  r9 (dashboard.css): .card .notes { margin: 8px 0px 0px; font-size: 13px; line-height: 1.4; }

### el#6  `#card-revenue`  <div>
- Flagged by: H1
- Box: x=20 y=80 w=335 h=120
- React component: MetricCard ← Dashboard  (src/MetricCard.jsx:8)
- Computed (non-default): padding: 16px; background-color: rgb(30, 41, 59); overflow-x: hidden; overflow-y: hidden; border-radius: 10px
- HTML: `<div class="card" data-omni-id="6" id="card-revenue"><h2 data-omni-id="7">Monthly revenue</h2><div class="metric" data-omni-id="8">$48,200</div> <p class="notes" data-omni-id="9">Up 12% on last month, driven by enterprise renewals in the EMEA region and two large expansions that closed late.</p></div>`
- CSS rules that apply (cascade order):
  r6 (dashboard.css): .card { background: rgb(30, 41, 59); border-radius: 10px; padding: 16px; height: 120px; overflow: hidden; }
  r10 (dashboard.css): .card:hover { background: rgb(39, 52, 73); }  /* pseudo-state/element */

### el#30  `#root > div.cookie:nth-of-type(3)`  <div>
- Flagged by: H2
- Box: x=0 y=0 w=375 h=812
- Computed (non-default): display: flex; position: fixed; top: 0px; right: 0px; bottom: 0px; left: 0px; z-index: 50; background-color: rgba(15, 23, 42, 0); align-items: flex-end
- HTML: `<div class="cookie" data-omni-id="30"><div class="bar" data-omni-id="31">We use cookies. <button data-omni-id="32">Accept</button></div></div>`
- CSS rules that apply (cascade order):
  r15 (dashboard.css): .cookie { position: fixed; left: 0px; right: 0px; top: 0px; height: 100%; background: rgba(15, 23, 42, 0); z-index: 50; display: flex; align-items: flex-end; }

### el#4  `#root > div.topbar:nth-of-type(1) > span.status`  <span>
- Flagged by: H3
- Box: x=169 y=12 w=186 h=36
- Text: "Last synced 2 minutes ago"
- Computed (non-default): display: block; color: rgb(71, 85, 105); font-family: "Brand Sans", Helvetica, Arial, sans-serif; font-size: 16px
- HTML: `<span class="status" data-omni-id="4">Last synced 2 minutes ago</span>`
- CSS rules that apply (cascade order):
  r11 (dashboard.css): .status { color: rgb(71, 85, 105); }

### el#27  `#root > div.grid:nth-of-type(2) > div.card:nth-of-type(6) > h2`  <h2>
- Flagged by: H4
- Box: x=36 y=776 w=303 h=16
- Text: "Uptime"
- Computed (non-default): margin: 0px 0px 8px; color: rgb(148, 163, 184); font-family: "Brand Sans", Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 700
- HTML: `<h2 data-omni-id="27">Uptime</h2>`
- CSS rules that apply (cascade order):
  r7 (dashboard.css): .card h2 { font-size: 14px; margin: 0px 0px 8px; color: rgb(148, 163, 184); }

### el#31  `#root > div.cookie:nth-of-type(3) > div.bar`  <div>
- Flagged by: H4
- Box: x=0 y=759 w=375 h=53
- Text: "We use cookies."
- Computed (non-default): padding: 16px 24px; color: rgb(15, 23, 42); background-color: rgb(248, 250, 252); font-family: "Brand Sans", Helvetica, Arial, sans-serif; font-size: 16px
- HTML: `<div class="bar" data-omni-id="31">We use cookies. <button data-omni-id="32">Accept</button></div>`
- CSS rules that apply (cascade order):
  r16 (dashboard.css): .cookie .bar { width: 100%; background: rgb(248, 250, 252); color: rgb(15, 23, 42); padding: 16px 24px; }

### el#32  `#root > div.cookie:nth-of-type(3) > div.bar > button`  <button>
- Flagged by: H5
- Box: x=146 y=775 w=57 h=21
- Text: "Accept"
- Computed (non-default): display: inline-block; padding: 1px 6px; color: rgb(0, 0, 0); background-color: rgb(239, 239, 239); font-family: Arial; font-size: 13.3333px; text-align: center; border: 2px outset rgb(0, 0, 0)
- HTML: `<button data-omni-id="32">Accept</button>`

## Diagnostics
- Console errors/warnings:
  - Failed to load resource: net::ERR_FILE_NOT_FOUND
- Failed requests:
  - font file:///home/claude/omnisight/samples/assets/missing-font.woff2 (net::ERR_FILE_NOT_FOUND)

## Element map (id, selector, page-coordinate box, text)
el#3 <h1> #root > div.topbar:nth-of-type(1) > h1 @ x=20 y=12 w=149 h=36 "Revenue dashboard"
el#4 <span> #root > div.topbar:nth-of-type(1) > span.status @ x=169 y=12 w=186 h=36 "Last synced 2 minutes ago" ⚑low-contrast
el#7 <h2> #card-revenue > h2 @ x=36 y=96 w=303 h=16 "Monthly revenue"
el#8 <div> #card-revenue > div.metric @ x=36 y=120 w=303 h=32 "$48,200"
el#9 <p> #card-revenue > p.notes @ x=36 y=160 w=303 h=55 "Up 12% on last month, driven by enterprise renewal" ⚑clipped-by-ancestor
el#11 <h2> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(2) > h2 @ x=36 y=232 w=303 h=16 "New users"
el#12 <div> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(2) > div.metric @ x=36 y=256 w=303 h=32 "1,284"
el#13 <p> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(2) > p.notes @ x=36 y=296 w=303 h=18 "Steady growth."
el#15 <h2> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(3) > h2 @ x=36 y=368 w=303 h=16 "Churn"
el#16 <div> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(3) > div.metric @ x=36 y=392 w=303 h=32 "2.1%"
el#17 <p> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(3) > p.notes @ x=36 y=432 w=303 h=18 "Down slightly."
el#19 <h2> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(4) > h2 @ x=36 y=504 w=303 h=16 "Open tickets"
el#20 <div> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(4) > div.metric @ x=36 y=528 w=303 h=32 "37"
el#21 <p> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(4) > p.notes @ x=36 y=568 w=303 h=18 "Median response 3h."
el#23 <h2> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(5) > h2 @ x=36 y=640 w=303 h=16 "NPS"
el#24 <div> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(5) > div.metric @ x=36 y=664 w=303 h=32 "61"
el#25 <p> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(5) > p.notes @ x=36 y=704 w=303 h=18 "Survey sample 410."
el#27 <h2> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(6) > h2 @ x=36 y=776 w=303 h=16 "Uptime" ⚑occluded
el#28 <div> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(6) > div.metric @ x=36 y=800 w=303 h=32 "99.98%"
el#29 <p> #root > div.grid:nth-of-type(2) > div.card:nth-of-type(6) > p.notes @ x=36 y=840 w=303 h=18 "No incidents this week."
el#30 <div> #root > div.cookie:nth-of-type(3) @ x=0 y=0 w=375 h=812 ⚑overlay-covers-content
el#31 <div> #root > div.cookie:nth-of-type(3) > div.bar @ x=0 y=759 w=375 h=53 "We use cookies."
el#32 <button> #root > div.cookie:nth-of-type(3) > div.bar > button @ x=146 y=775 w=57 h=21 "Accept" ⚑small-tap-target

## Relevant CSS (16 of 16 rules match elements on this page; unmatched rules dropped, cascade order preserved)
```css
/* ===== file:///home/claude/omnisight/samples/assets/dashboard.css ===== */
/* r1 */ * { box-sizing: border-box; }
/* r2 */ body { margin: 0px; font-family: "Brand Sans", Helvetica, Arial, sans-serif; background: rgb(15, 23, 42); color: rgb(226, 232, 240); }
/* r3 */ .topbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; background: rgb(30, 41, 59); }
/* r4 */ .topbar h1 { font-size: 20px; margin: 0px; }
/* r5 */ .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 20px; }
/* r6 */ .card { background: rgb(30, 41, 59); border-radius: 10px; padding: 16px; height: 120px; overflow: hidden; }
/* r7 */ .card h2 { font-size: 14px; margin: 0px 0px 8px; color: rgb(148, 163, 184); }
/* r8 */ .metric { font-size: 28px; font-weight: 700; }
/* r9 */ .card .notes { margin: 8px 0px 0px; font-size: 13px; line-height: 1.4; }
/* r10 */ .card:hover { background: rgb(39, 52, 73); }  /* pseudo-state/element */
/* r11 */ .status { color: rgb(71, 85, 105); }
/* r12 */ @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
/* r13 */ @media (max-width: 600px) { .topbar h1 { font-size: 16px; } }
/* r14 */ @media (min-width: 1800px) { .grid { grid-template-columns: repeat(6, 1fr); } }  /* inactive at this viewport */
/* r15 */ .cookie { position: fixed; left: 0px; right: 0px; top: 0px; height: 100%; background: rgba(15, 23, 42, 0); z-index: 50; display: flex; align-items: flex-end; }
/* r16 */ .cookie .bar { width: 100%; background: rgb(248, 250, 252); color: rgb(15, 23, 42); padding: 16px 24px; }
```

## Rendered HTML (cleaned: scripts, styles, SVG internals removed; `data-omni-id` = el#)
```html
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta content="width=device-width, initial-scale=1" name="viewport"/>
  <title>
   Defective dashboard (test fixture)
  </title>
 </head>
 <body>
  <div data-omni-id="1" id="root">
   <div class="topbar" data-omni-id="2">
    <h1 data-omni-id="3">
     Revenue dashboard
    </h1>
    <span class="status" data-omni-id="4">
     Last synced 2 minutes ago
    </span>
   </div>
   <div class="grid" data-omni-id="5">
    <div class="card" data-omni-id="6" id="card-revenue">
     <h2 data-omni-id="7">
      Monthly revenue
     </h2>
     <div class="metric" data-omni-id="8">
      $48,200
     </div>
     <p class="notes" data-omni-id="9">
      Up 12% on last month, driven by enterprise renewals in the EMEA region and two large expansions that closed late.
     </p>
    </div>
    <div class="card" data-omni-id="10">
     <h2 data-omni-id="11">
      New users
     </h2>
     <div class="metric" data-omni-id="12">
      1,284
     </div>
     <p class="notes" data-omni-id="13">
      Steady growth.
     </p>
    </div>
    <div class="card" data-omni-id="14">
     <h2 data-omni-id="15">
      Churn
     </h2>
     <div class="metric" data-omni-id="16">
      2.1%
     </div>
     <p class="notes" data-omni-id="17">
      Down slightly.
     </p>
    </div>
    <div class="card" data-omni-id="18">
     <h2 data-omni-id="19">
      Open tickets
     </h2>
     <div class="metric" data-omni-id="20">
      37
     </div>
     <p class="notes" data-omni-id="21">
      Median response 3h.
     </p>
    </div>
    <div class="card" data-omni-id="22">
     <h2 data-omni-id="23">
      NPS
     </h2>
     <div class="metric" data-omni-id="24">
      61
     </div>
     <p class="notes" data-omni-id="25">
      Survey sample 410.
     </p>
    </div>
    <div class="card" data-omni-id="26">
     <h2 data-omni-id="27">
      Uptime
     </h2>
     <div class="metric" data-omni-id="28">
      99.98%
     </div>
     <p class="notes" data-omni-id="29">
      No incidents this week.
     </p>
    </div>
   </div>
   <div class="cookie" data-omni-id="30">
    <div class="bar" data-omni-id="31">
     We use cookies.
     <button data-omni-id="32">
      Accept
     </button>
    </div>
   </div>
  </div>
 </body>
</html>
```
