# Page context
- URL: file:///home/claude/omnisight/samples/clean_page.html
- Title: Clean baseline page
- Viewport: desktop 1440×900px
- Full document size: 1440×900px
- All coordinates are CSS pixels, origin at the top-left of the full page, so they map 1:1 onto the screenshots.

## Screenshots
- `screenshot_viewport.png` (1440×900): Above-the-fold view exactly as a user first sees it.
- `screenshot_full.png` (1440×900): Entire scrollable page.

## Automated layout checks
No issues flagged by the heuristics. Rely on the screenshots for visual defects.

## Element map (id, selector, page-coordinate box, text)
el#1 <header> body > header @ x=0 y=0 w=1440 h=73
el#2 <strong> body > header > strong @ x=24 y=24 w=45 h=24 "Acme"
el#3 <nav> body > header > nav @ x=1153 y=16 w=263 h=40
el#4 <a> body > header > nav > a:nth-of-type(1) @ x=1153 y=16 w=92 h=40 "Products"
el#5 <a> body > header > nav > a:nth-of-type(2) @ x=1261 y=16 w=77 h=40 "Pricing"
el#6 <a> body > header > nav > a:nth-of-type(3) @ x=1353 y=16 w=63 h=40 "Docs"
el#8 <h1> body > main > h1 @ x=384 y=105 w=672 h=48 "Welcome back"
el#9 <p> body > main > p @ x=384 y=161 w=672 h=24 "Everything on this page is laid out correctly, so "
el#11 <h2> body > main > div.card > h2 @ x=401 y=238 w=638 h=36 "Getting started"
el#12 <p> body > main > div.card > p @ x=401 y=294 w=638 h=24 "Create a project, invite your team, and ship your "
el#13 <button> body > main > div.card > button.btn @ x=401 y=334 w=140 h=38 "Create project"
el#14 <img> body > main > img @ x=384 y=405 w=400 h=100
el#15 <footer> body > footer @ x=0 y=537 w=1440 h=69 "© 2026 Acme Inc."

## Relevant CSS (13 of 13 rules match elements on this page; unmatched rules dropped, cascade order preserved)
```css
/* ===== <style>#1 ===== */
/* r1 */ :root { --ink: #1f2937; --brand: #1d4ed8; }
/* r2 */ * { box-sizing: border-box; }
/* r3 */ body { margin: 0px; font: 16px / 1.5 system-ui, sans-serif; color: var(--ink); background: rgb(255, 255, 255); }
/* r4 */ header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-bottom: 1px solid rgb(229, 231, 235); }
/* r5 */ header nav { display: flex; gap: 16px; }
/* r6 */ header a { color: var(--brand); text-decoration: none; padding: 8px 12px; }
/* r7 */ main { max-width: 720px; margin: 0px auto; padding: 32px 24px; }
/* r8 */ h1 { font-size: 32px; margin: 0px 0px 8px; }
/* r9 */ p { margin: 0px 0px 16px; }
/* r10 */ .card { border: 1px solid rgb(229, 231, 235); border-radius: 8px; padding: 16px; margin-bottom: 16px; }
/* r11 */ .btn { display: inline-block; background: var(--brand); color: rgb(255, 255, 255); padding: 10px 20px; border-radius: 6px; border: 0px; font-size: 16px; cursor: pointer; }
/* r12 */ img { max-width: 100%; height: auto; display: block; }
/* r13 */ footer { padding: 24px; text-align: center; color: rgb(75, 85, 99); font-size: 14px; }
```

## Rendered HTML (cleaned: scripts, styles, SVG internals removed; `data-omni-id` = el#)
```html
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta content="width=device-width, initial-scale=1" name="viewport"/>
  <title>
   Clean baseline page
  </title>
 </head>
 <body>
  <header data-omni-id="1">
   <strong data-omni-id="2">
    Acme
   </strong>
   <nav data-omni-id="3">
    <a data-omni-id="4" href="#a">
     Products
    </a>
    <a data-omni-id="5" href="#b">
     Pricing
    </a>
    <a data-omni-id="6" href="#c">
     Docs
    </a>
   </nav>
  </header>
  <main data-omni-id="7">
   <h1 data-omni-id="8">
    Welcome back
   </h1>
   <p data-omni-id="9">
    Everything on this page is laid out correctly, so the layout checks should stay quiet.
   </p>
   <div class="card" data-omni-id="10">
    <h2 data-omni-id="11">
     Getting started
    </h2>
    <p data-omni-id="12">
     Create a project, invite your team, and ship your first release in minutes.
    </p>
    <button class="btn" data-omni-id="13">
     Create project
    </button>
   </div>
   <img alt="Placeholder banner" data-omni-id="14" height="100" src="data:image/svg+xml;utf8,…(132 chars)" width="400"/>
  </main>
  <footer data-omni-id="15">
   © 2026 Acme Inc.
  </footer>
 </body>
</html>
```
