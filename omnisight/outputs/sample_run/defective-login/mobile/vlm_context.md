# Page context
- URL: file:///home/claude/omnisight/samples/defective_login.html
- Title: Defective login page (test fixture)
- Viewport: mobile 375×812px (mobile emulation)
- Full document size: 653×1412px
- All coordinates are CSS pixels, origin at the top-left of the full page, so they map 1:1 onto the screenshots.
- ⚠ Horizontal scroll: content is 653px wide in a 375px viewport.
- Load problems: 2 console errors/warnings, 2 failed requests (see Diagnostics).

## Screenshots
- `screenshot_viewport.png` (375×812): Above-the-fold view exactly as a user first sees it.
- `screenshot_full.png` (653×1412): Entire scrollable page.
- `screenshot_annotated.png` (653×1412): Same page with numbered boxes (H<n>) marking elements flagged by the layout checks. Colour: red=high, orange=medium, blue=low severity.
- Zoomed crops of the most serious suspects in `crops/`: h02_text-clipped.png, h03_overlap.png, h04_low-contrast.png, h05_image-broken.png, h06_viewport-overflow.png, h08_small-tap-target.png, h09_empty-interactive.png, h10_image-distorted.png

## Automated layout checks
Heuristic findings measured in the browser. They are leads, not verdicts: confirm each one against the screenshot and look for visual defects they cannot measure (misalignment, inconsistent spacing, wrong colours, broken imagery).
- H1 [high] horizontal-scroll: Page scrolls horizontally: content is 653px wide in a 375px viewport.
- H2 [high] text-clipped el#11: Text is cut off by its own box: "Sign in securely".
- H3 [high] overlap el#3↔el#4: Overlaps body > div.wrap > span.badge (100% of the smaller element).
- H4 [high] low-contrast el#7: Contrast 1.7:1 is below 4.5:1 for "We'll never share your email with anyon…".
- H5 [high] image-broken el#15: Image failed to load.
- H6 [medium] viewport-overflow el#17: Extends 277px beyond the right edge of the viewport.
- H7 [medium] container-overflow el#17↔el#1: Sticks out 277px beyond its parent body > div.wrap, which has a visible background/border.
- H8 [medium] small-tap-target el#2: Interactive target is only 14×14px (WCAG 2.2 minimum is 24×24).
- H9 [medium] empty-interactive el#10: Interactive element has no visible text or accessible name.
- H10 [medium] image-distorted el#13: Image is stretched: natural size 300×300, rendered 311×40.
- H11 [medium] tiny-text el#16: Font size 9px is hard to read: "By continuing you agree to the Terms of…".
- H12 [low] image-missing-alt el#13: Image has no alt attribute.

## Suspect elements (detail)

### el#11  `body > div.wrap > button.submit:nth-of-type(3)`  <button>
- Flagged by: H2
- Box: x=76 y=357 w=90 h=42
- Text: "Sign in securely"
- Computed (non-default): display: inline-block; margin: 16px 0px 0px; padding: 12px; color: rgb(255, 255, 255); background-color: rgb(11, 95, 255); font-family: Arial; font-size: 16px; text-align: center; white-space: nowrap; overflow-x: hidden; overflow-y: hidden; border-radius: 6px
- HTML: `<button class="submit" data-omni-id="11">Sign in securely</button>`
- CSS rules that apply (cascade order):
  r9 (<style>#1): .submit { width: 90px; white-space: nowrap; overflow: hidden; background: rgb(11, 95, 255); color: rgb(255, 255, 255); border: 0px; padding: 12px; border-radius: 6px; margin-top: 16px; font-size: 16px; }

### el#3  `body > div.wrap > h1`  <h1>
- Flagged by: H3
- Box: x=32 y=72 w=311 h=84
- Text: "Sign in to your account"
- Computed (non-default): margin: 0px 0px 12px; color: rgb(34, 34, 34); font-family: Arial, sans-serif; font-size: 28px; font-weight: 700; line-height: 42px
- HTML: `<h1 data-omni-id="3">Sign in to your account</h1>`
- CSS rules that apply (cascade order):
  r4 (<style>#1): h1 { margin: 0px 0px 12px; font-size: 28px; }

### el#4  `body > div.wrap > span.badge`  <span>
- Flagged by: H3
- Box: x=120 y=80 w=114 h=29
- Text: "New: passkeys"
- Computed (non-default): display: block; position: absolute; top: 40px; right: 140.844px; bottom: 497.5px; left: 120px; padding: 4px 10px; color: rgb(34, 34, 34); background-color: rgb(255, 213, 74); font-family: Arial, sans-serif; font-size: 14px; line-height: 21px; border-radius: 12px
- HTML: `<span class="badge" data-omni-id="4">New: passkeys</span>`
- CSS rules that apply (cascade order):
  r5 (<style>#1): .badge { position: absolute; top: 40px; left: 120px; background: rgb(255, 213, 74); padding: 4px 10px; border-radius: 12px; font-size: 14px; }

### el#7  `body > div.wrap > p.hint:nth-of-type(1)`  <p>
- Flagged by: H4
- Box: x=32 y=240 w=311 h=21
- Text: "We'll never share your email with anyone."
- Computed (non-default): margin: 4px 0px 0px; color: rgb(200, 200, 200); font-family: Arial, sans-serif; font-size: 14px; line-height: 21px
- HTML: `<p class="hint" data-omni-id="7">We'll never share your email with anyone.</p>`
- CSS rules that apply (cascade order):
  r8 (<style>#1): .hint { color: rgb(200, 200, 200); font-size: 14px; margin: 4px 0px 0px; }

### el#15  `body > div.wrap > div.avatar:nth-of-type(2) > img`  <img>
- Flagged by: H5
- Box: x=32 y=467 w=97 h=24
- Computed (non-default): display: inline; overflow-x: clip; overflow-y: clip; border-radius: 50%
- HTML: `<img alt="Your avatar" data-omni-id="15" src="does-not-exist.png"/>`
- CSS rules that apply (cascade order):
  r14 (<style>#1): .avatar img { width: 48px; height: 48px; border-radius: 50%; }

### el#17  `body > div.wrap > table.wide-table`  <table>
- Flagged by: H6, H7
- Box: x=32 y=536 w=620 h=38
- Computed (non-default): display: table; min-width: 620px; margin: 16px 0px 0px
- HTML: `<table class="wide-table" data-omni-id="17"> <tbody data-omni-id="18"><tr data-omni-id="19"><td data-omni-id="20">Last login</td><td data-omni-id="21">Today 09:14</td><td data-omni-id="22">Chrome on macOS</td><td data-omni-id="23">Hyderabad, IN</td></tr> </tbody></table>`
- CSS rules that apply (cascade order):
  r16 (<style>#1): .wide-table { min-width: 620px; border-collapse: collapse; margin-top: 16px; }

### el#1  `body > div.wrap`  <div>
- Flagged by: H7
- Box: x=0 y=40 w=375 h=566
- Computed (non-default): position: relative; top: 0px; right: 0px; bottom: 0px; left: 0px; max-width: 480px; margin: 40px 0px; padding: 32px; background-color: rgb(255, 255, 255); border-radius: 8px
- HTML: `<div class="wrap" data-omni-id="1"> <button aria-label="Close" class="close" data-omni-id="2">×</button> <h1 data-omni-id="3">Sign in to your account</h1> <span class="badge" data-omni-id="4">New: passkeys</span> <label data-omni-id="5" for="email">Email</label> <input data-omni-id="6" id="email" placeholder="you@example.com" type="email"/> <p class="hint" data-omni-id="7">We'll never share your email with anyone.</p> <label data-omni-id="8" for="pw">Password</label> <input data-omni-id="9" id="pw" type="password"/> <button class="icon-btn" data-omni-id="10"></button> <button class="submit" data-omni-id="11">Sign in securely</button> <div class="hero" data-omni-id="12"> <img data-omni-id="1…`
- CSS rules that apply (cascade order):
  r3 (<style>#1): .wrap { max-width: 480px; margin: 40px auto; background: rgb(255, 255, 255); padding: 32px; border-radius: 8px; position: relative; }

### el#2  `body > div.wrap > button.close:nth-of-type(1)`  <button>
- Flagged by: H8
- Box: x=353 y=48 w=14 h=14
- Text: "×"
- Computed (non-default): display: block; position: absolute; top: 8px; right: 8px; bottom: 544.5px; left: 353px; color: rgb(0, 0, 0); background-color: rgb(238, 238, 238); font-family: Arial; font-size: 10px; line-height: 10px; text-align: center
- HTML: `<button aria-label="Close" class="close" data-omni-id="2">×</button>`
- CSS rules that apply (cascade order):
  r10 (<style>#1): .close { position: absolute; top: 8px; right: 8px; width: 14px; height: 14px; padding: 0px; font-size: 10px; line-height: 1; border: 0px; background: rgb(238, 238, 238); }

### el#10  `body > div.wrap > button.icon-btn:nth-of-type(2)`  <button>
- Flagged by: H9
- Box: x=40 y=353 w=32 h=32
- Computed (non-default): display: inline-block; margin: 0px 0px 0px 8px; padding: 1px 6px; color: rgb(0, 0, 0); background-color: rgb(255, 255, 255); font-family: Arial; font-size: 13.3333px; text-align: center; border: 1px solid rgb(204, 204, 204)
- HTML: `<button class="icon-btn" data-omni-id="10"></button>`
- CSS rules that apply (cascade order):
  r11 (<style>#1): .icon-btn { width: 32px; height: 32px; border: 1px solid rgb(204, 204, 204); background: rgb(255, 255, 255); margin-left: 8px; }

### el#13  `body > div.wrap > div.hero:nth-of-type(1) > img`  <img>
- Flagged by: H10, H12
- Box: x=32 y=415 w=311 h=40
- Computed (non-default): display: block; margin: 16px 0px 0px; overflow-x: clip; overflow-y: clip
- HTML: `<img data-omni-id="13" src="data:image/svg+xml;utf8,…(135 chars)"/>`
- CSS rules that apply (cascade order):
  r12 (<style>#1): .hero img { width: 100%; height: 40px; display: block; margin-top: 16px; }

### el#16  `body > div.wrap > p.fine-print:nth-of-type(2)`  <p>
- Flagged by: H11
- Box: x=32 y=507 w=311 h=14
- Text: "By continuing you agree to the Terms of Service and Privacy Policy."
- Computed (non-default): margin: 16px 0px 9px; color: rgb(85, 85, 85); font-family: Arial, sans-serif; font-size: 9px; line-height: 13.5px
- HTML: `<p class="fine-print" data-omni-id="16">By continuing you agree to the Terms of Service and Privacy Policy.</p>`
- CSS rules that apply (cascade order):
  r15 (<style>#1): .fine-print { font-size: 9px; color: rgb(85, 85, 85); margin-top: 16px; }

## Diagnostics
- Console errors/warnings:
  - Failed to load resource: net::ERR_FILE_NOT_FOUND
  - Failed to load resource: net::ERR_FILE_NOT_FOUND
- Failed requests:
  - image file:///home/claude/omnisight/samples/does-not-exist.png (net::ERR_FILE_NOT_FOUND)
  - image file:///home/claude/omnisight/samples/does-not-exist.png (net::ERR_FILE_NOT_FOUND)

## Element map (id, selector, page-coordinate box, text)
el#2 <button> body > div.wrap > button.close:nth-of-type(1) @ x=353 y=48 w=14 h=14 "×" ⚑small-tap-target
el#3 <h1> body > div.wrap > h1 @ x=32 y=72 w=311 h=84 "Sign in to your account" ⚑overlap
el#4 <span> body > div.wrap > span.badge @ x=120 y=80 w=114 h=29 "New: passkeys"
el#5 <label> body > div.wrap > label:nth-of-type(1) @ x=32 y=168 w=311 h=24 "Email"
el#6 <input> #email @ x=32 y=196 w=311 h=40
el#7 <p> body > div.wrap > p.hint:nth-of-type(1) @ x=32 y=240 w=311 h=21 "We'll never share your email with anyone." ⚑low-contrast
el#8 <label> body > div.wrap > label:nth-of-type(2) @ x=32 y=273 w=311 h=24 "Password"
el#9 <input> #pw @ x=32 y=301 w=311 h=40
el#10 <button> body > div.wrap > button.icon-btn:nth-of-type(2) @ x=40 y=353 w=32 h=32 ⚑empty-interactive
el#11 <button> body > div.wrap > button.submit:nth-of-type(3) @ x=76 y=357 w=90 h=42 "Sign in securely" ⚑text-clipped
el#13 <img> body > div.wrap > div.hero:nth-of-type(1) > img @ x=32 y=415 w=311 h=40 ⚑image-distorted,image-missing-alt
el#15 <img> body > div.wrap > div.avatar:nth-of-type(2) > img @ x=32 y=467 w=97 h=24 ⚑image-broken
el#16 <p> body > div.wrap > p.fine-print:nth-of-type(2) @ x=32 y=507 w=311 h=14 "By continuing you agree to the Terms of Service an" ⚑tiny-text
el#17 <table> body > div.wrap > table.wide-table @ x=32 y=536 w=620 h=38 ⚑viewport-overflow,container-overflow
el#20 <td> body > div.wrap > table.wide-table > tbody > tr > td:nth-of-type(1) @ x=32 y=537 w=116 h=37 "Last login"
el#21 <td> body > div.wrap > table.wide-table > tbody > tr > td:nth-of-type(2) @ x=148 y=537 w=140 h=37 "Today 09:14"
el#22 <td> body > div.wrap > table.wide-table > tbody > tr > td:nth-of-type(3) @ x=288 y=537 w=204 h=37 "Chrome on macOS"
el#23 <td> body > div.wrap > table.wide-table > tbody > tr > td:nth-of-type(4) @ x=491 y=537 w=160 h=37 "Hyderabad, IN"

## Relevant CSS (17 of 17 rules match elements on this page; unmatched rules dropped, cascade order preserved)
```css
/* ===== <style>#1 ===== */
/* r1 */ * { box-sizing: border-box; }
/* r2 */ body { margin: 0px; font: 16px / 1.5 Arial, sans-serif; color: rgb(34, 34, 34); background: rgb(245, 247, 250); }
/* r3 */ .wrap { max-width: 480px; margin: 40px auto; background: rgb(255, 255, 255); padding: 32px; border-radius: 8px; position: relative; }
/* r4 */ h1 { margin: 0px 0px 12px; font-size: 28px; }
/* r5 */ .badge { position: absolute; top: 40px; left: 120px; background: rgb(255, 213, 74); padding: 4px 10px; border-radius: 12px; font-size: 14px; }
/* r6 */ label { display: block; margin: 12px 0px 4px; font-weight: bold; }
/* r7 */ input { width: 100%; padding: 10px; border: 1px solid rgb(187, 187, 187); border-radius: 4px; font-size: 16px; }
/* r8 */ .hint { color: rgb(200, 200, 200); font-size: 14px; margin: 4px 0px 0px; }
/* r9 */ .submit { width: 90px; white-space: nowrap; overflow: hidden; background: rgb(11, 95, 255); color: rgb(255, 255, 255); border: 0px; padding: 12px; border-radius: 6px; margin-top: 16px; font-size: 16px; }
/* r10 */ .close { position: absolute; top: 8px; right: 8px; width: 14px; height: 14px; padding: 0px; font-size: 10px; line-height: 1; border: 0px; background: rgb(238, 238, 238); }
/* r11 */ .icon-btn { width: 32px; height: 32px; border: 1px solid rgb(204, 204, 204); background: rgb(255, 255, 255); margin-left: 8px; }
/* r12 */ .hero img { width: 100%; height: 40px; display: block; margin-top: 16px; }
/* r13 */ .avatar { margin-top: 12px; }
/* r14 */ .avatar img { width: 48px; height: 48px; border-radius: 50%; }
/* r15 */ .fine-print { font-size: 9px; color: rgb(85, 85, 85); margin-top: 16px; }
/* r16 */ .wide-table { min-width: 620px; border-collapse: collapse; margin-top: 16px; }
/* r17 */ .wide-table td { border: 1px solid rgb(221, 221, 221); padding: 6px 10px; }
```

## Rendered HTML (cleaned: scripts, styles, SVG internals removed; `data-omni-id` = el#)
```html
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta content="width=device-width, initial-scale=1" name="viewport"/>
  <title>
   Defective login page (test fixture)
  </title>
 </head>
 <body>
  <div class="wrap" data-omni-id="1">
   <button aria-label="Close" class="close" data-omni-id="2">
    ×
   </button>
   <h1 data-omni-id="3">
    Sign in to your account
   </h1>
   <span class="badge" data-omni-id="4">
    New: passkeys
   </span>
   <label data-omni-id="5" for="email">
    Email
   </label>
   <input data-omni-id="6" id="email" placeholder="you@example.com" type="email"/>
   <p class="hint" data-omni-id="7">
    We'll never share your email with anyone.
   </p>
   <label data-omni-id="8" for="pw">
    Password
   </label>
   <input data-omni-id="9" id="pw" type="password"/>
   <button class="icon-btn" data-omni-id="10">
   </button>
   <button class="submit" data-omni-id="11">
    Sign in securely
   </button>
   <div class="hero" data-omni-id="12">
    <img data-omni-id="13" src="data:image/svg+xml;utf8,…(135 chars)"/>
   </div>
   <div class="avatar" data-omni-id="14">
    <img alt="Your avatar" data-omni-id="15" src="does-not-exist.png"/>
   </div>
   <p class="fine-print" data-omni-id="16">
    By continuing you agree to the Terms of Service and Privacy Policy.
   </p>
   <table class="wide-table" data-omni-id="17">
    <tbody data-omni-id="18">
     <tr data-omni-id="19">
      <td data-omni-id="20">
       Last login
      </td>
      <td data-omni-id="21">
       Today 09:14
      </td>
      <td data-omni-id="22">
       Chrome on macOS
      </td>
      <td data-omni-id="23">
       Hyderabad, IN
      </td>
     </tr>
    </tbody>
   </table>
  </div>
 </body>
</html>
```
