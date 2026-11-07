# Page context
- URL: http://localhost:8000/Mock-Website/
- Title: OmniSight - Demo Store
- Viewport: desktop 1366×768px
- Full document size: 1366×2325px
- All coordinates are CSS pixels, origin at the top-left of the full page, so they map 1:1 onto the screenshots.

## Screenshots
- `screenshot_viewport.png` (1366×768): Above-the-fold view exactly as a user first sees it.
- `screenshot_full.png` (1366×2325): Entire scrollable page.
- 3 tiles in `tiles/` (full-width slices, top to bottom, overlapping) for reading small text: tile_01.png y=0–1100, tile_02.png y=1000–2100, tile_03.png y=2000–2325

## Automated layout checks
No issues flagged by the heuristics. Rely on the screenshots for visual defects.

## Element map (id, selector, page-coordinate box, text)
el#1 <header> #top @ x=0 y=0 w=1366 h=70
el#2 <h1> #top > h1 @ x=109 y=17 w=190 h=35 "OmniSight Store"
el#3 <nav> #top > nav @ x=906 y=16 w=351 h=38
el#4 <a> #top > nav > a.active:nth-of-type(1) @ x=906 y=16 w=68 h=38 "Home"
el#5 <a> #top > nav > a:nth-of-type(2) @ x=980 y=16 w=88 h=38 "Products"
el#6 <a> #top > nav > a:nth-of-type(3) @ x=1074 y=16 w=85 h=38 "Cart"
el#7 <span> #cart-count @ x=1125 y=26 w=22 h=21 "0"
el#8 <a> #top > nav > a:nth-of-type(4) @ x=1165 y=16 w=92 h=38 "Checkout"
el#12 <h2> #home > div.hero-text > h2 @ x=123 y=170 w=560 h=110 "Welcome to OmniSight"
el#13 <p> #home > div.hero-text > p @ x=123 y=296 w=480 h=58 "Move your cursor around. Pick up gear you can see "
el#14 <a> #home > div.hero-text > a.cta @ x=123 y=378 w=157 h=50 "Shop products"
el#16 <h2> #products > h2 @ x=114 y=553 w=1138 h=38 "Our Products"
el#18 <input> #search @ x=114 y=608 w=596 h=52
el#20 <button> #chips > button.chip.active:nth-of-type(1) @ x=722 y=616 w=48 h=34 "All"
el#21 <button> #chips > button.chip:nth-of-type(2) @ x=778 y=616 w=70 h=34 "Audio"
el#22 <button> #chips > button.chip:nth-of-type(3) @ x=856 y=616 w=100 h=34 "Wearables"
el#23 <button> #chips > button.chip:nth-of-type(4) @ x=964 y=616 w=112 h=34 "Accessories"
el#24 <select> #sort @ x=1088 y=611 w=164 h=45
el#27 <span> #product-grid > article:nth-of-type(1) > span.icon @ x=131 y=700 w=237 h=83 "🎧"
el#28 <h3> #product-grid > article:nth-of-type(1) > h3 @ x=131 y=793 w=237 h=26 "Wireless Headphones"
el#29 <p> #product-grid > article:nth-of-type(1) > p @ x=131 y=823 w=237 h=29 "Price: ₹2,499"
el#30 <button> #product-grid > article:nth-of-type(1) > button @ x=193 y=866 w=112 h=38 "Add to Cart"
el#32 <span> #product-grid > article:nth-of-type(2) > span.icon @ x=420 y=700 w=237 h=83 "⌚"
el#33 <h3> #product-grid > article:nth-of-type(2) > h3 @ x=420 y=793 w=237 h=26 "Smart Watch"
el#34 <p> #product-grid > article:nth-of-type(2) > p @ x=420 y=823 w=237 h=29 "Price: ₹3,299"
el#35 <button> #product-grid > article:nth-of-type(2) > button @ x=482 y=866 w=112 h=38 "Add to Cart"
el#37 <span> #product-grid > article:nth-of-type(3) > span.icon @ x=709 y=700 w=237 h=83 "🔊"
el#38 <h3> #product-grid > article:nth-of-type(3) > h3 @ x=709 y=793 w=237 h=26 "Bluetooth Speaker"
el#39 <p> #product-grid > article:nth-of-type(3) > p @ x=709 y=823 w=237 h=29 "Price: ₹1,799"
el#40 <button> #product-grid > article:nth-of-type(3) > button @ x=771 y=866 w=112 h=38 "Add to Cart"
el#42 <span> #product-grid > article:nth-of-type(4) > span.icon @ x=998 y=700 w=237 h=83 "💪"
el#43 <h3> #product-grid > article:nth-of-type(4) > h3 @ x=998 y=793 w=237 h=26 "Fitness Band"
el#44 <p> #product-grid > article:nth-of-type(4) > p @ x=998 y=823 w=237 h=29 "Price: ₹1,999"
el#45 <button> #product-grid > article:nth-of-type(4) > button @ x=1060 y=866 w=112 h=38 "Add to Cart"
el#47 <span> #product-grid > article:nth-of-type(5) > span.icon @ x=131 y=964 w=237 h=83 "🎵"
el#48 <h3> #product-grid > article:nth-of-type(5) > h3 @ x=131 y=1057 w=237 h=26 "True Wireless Earbuds"
el#49 <p> #product-grid > article:nth-of-type(5) > p @ x=131 y=1086 w=237 h=29 "Price: ₹2,199"
el#50 <button> #product-grid > article:nth-of-type(5) > button @ x=193 y=1129 w=112 h=38 "Add to Cart"
el#52 <span> #product-grid > article:nth-of-type(6) > span.icon @ x=420 y=964 w=237 h=83 "🔋"
el#53 <h3> #product-grid > article:nth-of-type(6) > h3 @ x=420 y=1057 w=237 h=26 "Power Bank 20000mAh"
el#54 <p> #product-grid > article:nth-of-type(6) > p @ x=420 y=1086 w=237 h=29 "Price: ₹1,499"
el#55 <button> #product-grid > article:nth-of-type(6) > button @ x=482 y=1129 w=112 h=38 "Add to Cart"
el#57 <h2> #cart > h2 @ x=114 y=1275 w=1138 h=38 "Shopping Cart"
el#58 <p> #cart > p @ x=114 y=1330 w=1138 h=26 "Your cart is empty. Add a product above to get sta"
el#60 <h2> #checkout > h2 @ x=114 y=1454 w=1138 h=38 "Checkout"
el#62 <form> #checkout-form @ x=114 y=1509 w=606 h=462
el#63 <label> #checkout-form > label:nth-of-type(1) @ x=114 y=1523 w=606 h=26 "Full Name:"
el#64 <input> #name @ x=114 y=1554 w=606 h=52
el#66 <label> #checkout-form > label:nth-of-type(2) @ x=114 y=1640 w=606 h=26 "Email:"
el#67 <input> #email @ x=114 y=1672 w=606 h=52
el#69 <label> #checkout-form > label:nth-of-type(3) @ x=114 y=1757 w=606 h=26 "Delivery Address:"
el#70 <textarea> #address @ x=114 y=1789 w=606 h=100
el#72 <button> #checkout-form > button.place @ x=114 y=1925 w=606 h=45 "Place Demo Order"
el#74 <h3> #summary > h3 @ x=768 y=1530 w=462 h=27 "Order summary"
el#75 <p> #summary > p @ x=768 y=1567 w=462 h=26 "Nothing here yet. Add a product to see your order."
el#77 <h2> #confirmation > h2 @ x=114 y=2060 w=1138 h=38 "Order Confirmation"
el#78 <p> #confirmation > p @ x=114 y=2115 w=1138 h=26 "Your order confirmation message will appear here."
el#79 <footer> body > footer @ x=0 y=2218 w=1366 h=107
el#80 <p> body > footer > p:nth-of-type(1) @ x=15 y=2247 w=1336 h=22 "© 2026 OmniSight Demo Store"
el#81 <p> body > footer > p:nth-of-type(2) @ x=15 y=2274 w=1336 h=22 "This is a mock e-commerce website for testing purp"

## Relevant CSS (62 of 88 rules match elements on this page; unmatched rules dropped, cascade order preserved)
```css
/* ===== http://localhost:8000/Mock-Website/style.css ===== */
/* r1 */ :root { --ink: #0e1330; --ink-2: #1b2150; --paper: #f2f4fa; --line: #dde2f0; --text: #232846; --muted: #666d8f; --accent: #5b4bff; --accent-d: #4636e0; --lens: #2fd4e8; --ok: #12945a; --err: #c62a47; }
/* r2 */ * { margin: 0px; padding: 0px; box-sizing: border-box; }
/* r3 */ html { scroll-behavior: smooth; }
/* r4 */ body { font-family: "Segoe UI", Arial, sans-serif; background: var(--paper); color: var(--text); line-height: 1.6; }
/* r5 */ h1, h2, h3 { font-family: Sora, Arial, sans-serif; }
/* r6 */ header { position: sticky; top: 0px; z-index: 20; background: var(--ink); color: rgb(255, 255, 255); padding: 16px 8%; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
/* r7 */ header h1 { font-size: 22px; }
/* r8 */ nav { display: flex; flex-wrap: wrap; gap: 6px; }
/* r9 */ nav a { color: rgb(255, 255, 255); text-decoration: none; font-weight: 600; padding: 6px 12px; border-radius: 999px; transition: background 0.2s; }
/* r10 */ nav a:hover, nav a.active { background: var(--ink-2); color: var(--lens); }  /* pseudo-state/element */
/* r11 */ .badge { display: inline-block; min-width: 22px; padding: 0px 6px; margin-left: 4px; background: var(--lens); color: var(--ink); border-radius: 999px; font-size: 13px; text-align: center; }
/* r12 */ main { width: 88%; max-width: 1200px; margin: 30px auto; }
/* r13 */ section { background: rgb(255, 255, 255); padding: 30px; margin-bottom: 25px; border-radius: 14px; border: 1px solid var(--line); scroll-margin-top: 80px; }
/* r14 */ section h2 { font-size: 24px; color: var(--ink); margin-bottom: 16px; }
/* r15 */ section p { margin-bottom: 12px; }
/* r16 */ #home { --x: 70%; --y: 40%; position: relative; overflow: hidden; border: 0px; padding: 70px 40px; color: rgb(255, 255, 255); background: radial-gradient(circle 220px at var(--x) var(--y), rgba(47, 212, 232, .35), transparent 70%),
        radial-gradient(circle 1.5px, rgba(255, 255, 255, .22) 98%, transparent) 0 0 / 26px 26px,
        var(--ink); }
/* r17 */ #home h2 { color: rgb(255, 255, 255); font-size: clamp(30px, 5vw, 48px); line-height: 1.15; max-width: 560px; }
/* r18 */ #home p { color: rgb(197, 203, 232); font-size: 18px; max-width: 480px; margin: 14px 0px 24px; }
/* r19 */ .cta { display: inline-block; background: var(--lens); color: var(--ink); text-decoration: none; font-weight: 700; padding: 12px 24px; border-radius: 8px; transition: transform 0.2s; }
/* r20 */ .cta:hover { transform: translateY(-2px); }  /* pseudo-state/element */
/* r21 */ .tools { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 20px; }
/* r22 */ .tools input[type="search"] { flex: 1 1 200px; width: auto; }
/* r23 */ .chips { display: flex; flex-wrap: wrap; gap: 8px; }
/* r24 */ .chip { background: rgb(255, 255, 255); color: var(--text); border: 1px solid var(--line); padding: 8px 14px; border-radius: 999px; }
/* r25 */ .chip:hover { background: rgb(238, 240, 255); }  /* pseudo-state/element */
/* r26 */ .chip.active { background: var(--ink); color: rgb(255, 255, 255); border-color: var(--ink); }
/* r27 */ select { padding: 10px; border: 1px solid var(--line); border-radius: 8px; font: inherit; background: rgb(255, 255, 255); }
/* r28 */ #product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 18px; }
/* r29 */ #products article { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 20px 16px; text-align: center; transition: transform 0.2s, border-color 0.2s; }
/* r30 */ #products article:hover { transform: translateY(-4px); border-color: var(--accent); }  /* pseudo-state/element */
/* r31 */ .icon { font-size: 52px; display: block; transition: transform 0.3s; }
/* r32 */ #products article:hover .icon { transform: scale(1.15) rotate(-6deg); }  /* pseudo-state/element */
/* r33 */ #products article h3 { font-size: 16px; margin: 10px 0px 4px; color: var(--ink); }
/* r34 */ #products article p { color: var(--accent); font-weight: 700; font-size: 18px; margin-bottom: 14px; }
/* r35 */ #no-results { color: var(--muted); }
/* r36 */ button { background: var(--accent); color: rgb(255, 255, 255); border: 0px; padding: 11px 18px; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; transition: background 0.2s, transform 0.1s; }
/* r37 */ button:hover { background: var(--accent-d); }  /* pseudo-state/element */
/* r38 */ button:active { transform: scale(0.96); }  /* pseudo-state/element */
/* r39 */ button:focus-visible, nav a:focus-visible, .cta:focus-visible { outline: rgb(245, 158, 11) solid 3px; outline-offset: 3px; }  /* pseudo-state/element */
/* r40 */ #cart { min-height: 150px; }
/* r41 */ #cart p { color: var(--muted); }
/* r42 */ .checkout-layout { display: grid; grid-template-columns: 1.2fr 1fr; gap: 28px; align-items: start; }
/* r43 */ label { display: block; margin: 14px 0px 6px; font-weight: 700; color: var(--ink); }
/* r44 */ input, textarea { width: 100%; padding: 12px; border: 1px solid rgb(201, 208, 230); border-radius: 8px; font: inherit; background: rgb(255, 255, 255); transition: border-color 0.2s, box-shadow 0.2s; }
/* r45 */ textarea { min-height: 100px; resize: vertical; }
/* r46 */ input:focus, textarea:focus { outline: none; border-color: var(--accent); box-shadow: rgba(91, 75, 255, 0.2) 0px 0px 0px 3px; }  /* pseudo-state/element */
/* r47 */ .error { display: block; min-height: 20px; color: var(--err); font-size: 13px; }
/* r48 */ .place { margin-top: 10px; width: 100%; padding: 14px; font-size: 15px; }
/* r49 */ #summary { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 20px; }
/* r50 */ #summary h3 { color: var(--ink); margin-bottom: 10px; font-size: 17px; }
/* r51 */ #summary p { color: var(--muted); }
/* r52 */ #confirmation { text-align: center; border-top: 4px solid var(--ok); }
/* r53 */ #confirmation h2 { color: var(--ok); }
/* r54 */ #toast { position: fixed; left: 50%; bottom: 24px; transform: translate(-50%, 120px); background: var(--ink); color: rgb(255, 255, 255); padding: 12px 22px; border-radius: 10px; font-weight: 600; transition: transform 0.3s; z-index: 50; }
/* r55 */ footer { background: var(--ink); color: rgb(197, 203, 232); text-align: center; padding: 25px 15px; margin-top: 35px; }
/* r56 */ footer p { margin: 4px 0px; font-size: 14px; }
/* r57 */ @media (max-width: 800px) { .checkout-layout { grid-template-columns: 1fr; } }  /* inactive at this viewport */
/* r58 */ @media (max-width: 600px) { header { flex-direction: column; text-align: center; } }  /* inactive at this viewport */
/* r59 */ @media (max-width: 600px) { main { width: 94%; margin: 20px auto; } }  /* inactive at this viewport */
/* r60 */ @media (max-width: 600px) { section { padding: 20px 15px; } }  /* inactive at this viewport */
/* r61 */ @media (max-width: 600px) { #home { padding: 44px 20px; } }  /* inactive at this viewport */
/* r62 */ @media (prefers-reduced-motion: reduce) { * { animation: auto ease 0s 1 normal none running none !important; transition: none !important; scroll-behavior: auto !important; } }
```

## Rendered HTML (cleaned: scripts, styles, SVG internals removed; `data-omni-id` = el#)
```html
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
  <title>
   OmniSight - Demo Store
  </title>
 </head>
 <body>
  <header data-omni-id="1" id="top">
   <h1 data-omni-id="2">
    OmniSight Store
   </h1>
   <nav data-omni-id="3">
    <a class="active" data-omni-id="4" href="#home">
     Home
    </a>
    <a data-omni-id="5" href="#products">
     Products
    </a>
    <a data-omni-id="6" href="#cart">
     Cart
     <span aria-live="polite" class="badge" data-omni-id="7" id="cart-count">
      0
     </span>
    </a>
    <a data-omni-id="8" href="#checkout">
     Checkout
    </a>
   </nav>
  </header>
  <main data-omni-id="9">
   <section data-omni-id="10" id="home">
    <div class="hero-text" data-omni-id="11">
     <h2 data-omni-id="12">
      Welcome to OmniSight
     </h2>
     <p data-omni-id="13">
      Move your cursor around. Pick up gear you can see clearly, and check out in under a minute.
     </p>
     <a class="cta" data-omni-id="14" href="#products">
      Shop products
     </a>
    </div>
   </section>
   <section data-omni-id="15" id="products">
    <h2 data-omni-id="16">
     Our Products
    </h2>
    <div class="tools" data-omni-id="17">
     <input aria-label="Search products" data-omni-id="18" id="search" placeholder="Search products" type="search"/>
     <div aria-label="Filter by category" class="chips" data-omni-id="19" id="chips" role="group">
      <button class="chip active" data-cat="all" data-omni-id="20" type="button">
       All
      </button>
      <button class="chip" data-cat="audio" data-omni-id="21" type="button">
       Audio
      </button>
      <button class="chip" data-cat="wearables" data-omni-id="22" type="button">
       Wearables
      </button>
      <button class="chip" data-cat="accessories" data-omni-id="23" type="button">
       Accessories
      </button>
     </div>
     <select aria-label="Sort products" data-omni-id="24" id="sort">
      <option value="default">
       Sort: Featured
      </option>
      <option value="low">
       Price: low to high
      </option>
      <option value="high">
       Price: high to low
      </option>
     </select>
    </div>
    <div data-omni-id="25" id="product-grid">
     <article data-id="1" data-omni-id="26">
      <span aria-hidden="true" class="icon" data-omni-id="27">
       🎧
      </span>
      <h3 data-omni-id="28">
       Wireless Headphones
      </h3>
      <p data-omni-id="29">
       Price: ₹2,499
      </p>
      <button data-omni-id="30" type="button">
       Add to Cart
      </button>
     </article>
     <article data-id="2" data-omni-id="31">
      <span aria-hidden="true" class="icon" data-omni-id="32">
       ⌚
      </span>
      <h3 data-omni-id="33">
       Smart Watch
      </h3>
      <p data-omni-id="34">
       Price: ₹3,299
      </p>
      <button data-omni-id="35" type="button">
       Add to Cart
      </button>
     </article>
     <article data-id="3" data-omni-id="36">
      <span aria-hidden="true" class="icon" data-omni-id="37">
       🔊
      </span>
      <h3 data-omni-id="38">
       Bluetooth Speaker
      </h3>
      <p data-omni-id="39">
       Price: ₹1,799
      </p>
      <button data-omni-id="40" type="button">
       Add to Cart
      </button>
     </article>
     <article data-id="4" data-omni-id="41">
      <span aria-hidden="true" class="icon" data-omni-id="42">
       💪
      </span>
      <h3 data-omni-id="43">
       Fitness Band
      </h3>
      <p data-omni-id="44">
       Price: ₹1,999
      </p>
      <button data-omni-id="45" type="button">
       Add to Cart
      </button>
     </article>
     <article data-id="5" data-omni-id="46">
      <span aria-hidden="true" class="icon" data-omni-id="47">
       🎵
      </span>
      <h3 data-omni-id="48">
       True Wireless Earbuds
      </h3>
      <p data-omni-id="49">
       Price: ₹2,199
      </p>
      <button data-omni-id="50" type="button">
       Add to Cart
      </button>
     </article>
     <article data-id="6" data-omni-id="51">
      <span aria-hidden="true" class="icon" data-omni-id="52">
       🔋
      </span>
      <h3 data-omni-id="53">
       Power Bank 20000mAh
      </h3>
      <p data-omni-id="54">
       Price: ₹1,499
      </p>
      <button data-omni-id="55" type="button">
       Add to Cart
      </button>
     </article>
    </div>
    <p hidden="" id="no-results">
     No products match your search. Try a different word or category.
    </p>
   </section>
   <section data-omni-id="56" id="cart">
    <h2 data-omni-id="57">
     Shopping Cart
    </h2>
    <p data-omni-id="58">
     Your cart is empty. Add a product above to get started.
    </p>
   </section>
   <section data-omni-id="59" id="checkout">
    <h2 data-omni-id="60">
     Checkout
    </h2>
    <div class="checkout-layout" data-omni-id="61">
     <form data-omni-id="62" id="checkout-form" novalidate="">
      <label data-omni-id="63" for="name">
       Full Name:
      </label>
      <input autocomplete="name" data-omni-id="64" id="name" name="name" required="" type="text"/>
      <small class="error" data-for="name" data-omni-id="65">
      </small>
      <label data-omni-id="66" for="email">
       Email:
      </label>
      <input autocomplete="email" data-omni-id="67" id="email" name="email" required="" type="email"/>
      <small class="error" data-for="email" data-omni-id="68">
      </small>
      <label data-omni-id="69" for="address">
       Delivery Address:
      </label>
      <textarea data-omni-id="70" id="address" name="address" required=""></textarea>
      <small class="error" data-for="address" data-omni-id="71">
      </small>
      <button class="place" data-omni-id="72" type="submit">
       Place Demo Order
      </button>
     </form>
     <aside aria-live="polite" data-omni-id="73" id="summary">
      <h3 data-omni-id="74">
       Order summary
      </h3>
      <p data-omni-id="75">
       Nothing here yet. Add a product to see your order.
      </p>
     </aside>
    </div>
   </section>
   <section data-omni-id="76" id="confirmation">
    <h2 data-omni-id="77">
     Order Confirmation
    </h2>
    <p data-omni-id="78">
     Your order confirmation message will appear here.
    </p>
   </section>
  </main>
  <footer data-omni-id="79">
   <p data-omni-id="80">
    © 2026 OmniSight Demo Store
   </p>
   <p data-omni-id="81">
    This is a mock e-commerce website for testing purposes.
   </p>
  </footer>
  <div aria-live="polite" data-omni-id="82" id="toast" role="status">
  </div>
 </body>
</html>
```
