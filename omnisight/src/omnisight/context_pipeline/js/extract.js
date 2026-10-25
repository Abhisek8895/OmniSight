/*
 * In-page extractor. Evaluated by Playwright as `page.evaluate(<this file>, opts)`.
 *
 * Returns everything a VLM needs besides the pixels:
 *   - element map   (selector, bbox, text, non-default computed styles, React component)
 *   - CSS rules     (only rules that match something on the page, in cascade order)
 *   - layout hints  (overflow, clipping, overlap, occlusion, contrast, tap targets, images)
 *   - an HTML snapshot where each recorded element carries data-omni-id
 *
 * It never mutates the live DOM.
 */
(opts) => {
  const {
    maxElements, maxHints, maxRules, maxTextLen, styleProps, externalSheets,
  } = opts;
  const MAX_SCAN = 6000;

  // ------------------------------------------------------------------ utils
  const round = (n) => Math.round(n * 10) / 10;
  const sx = window.scrollX, sy = window.scrollY;
  const de = document.documentElement;
  const cw = de.clientWidth, ch = de.clientHeight;
  const csCache = new Map();
  const getCS = (el) => {
    let c = csCache.get(el);
    if (!c) { c = getComputedStyle(el); csCache.set(el, c); }
    return c;
  };
  const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s.replace(/[^\w-]/g, '\\$&'));
  const trunc = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

  const uniqueIdCache = new Map();
  const isUniqueId = (id) => {
    if (!uniqueIdCache.has(id)) {
      uniqueIdCache.set(id, document.querySelectorAll('#' + esc(id)).length === 1);
    }
    return uniqueIdCache.get(id);
  };

  function structuralPath(el, withClasses) {
    const parts = [];
    let cur = el;
    while (cur && cur.nodeType === 1 && cur !== de) {
      if (cur !== el && cur.id && isUniqueId(cur.id)) { parts.unshift('#' + esc(cur.id)); break; }
      if (cur === document.body) { parts.unshift('body'); break; }
      let part = cur.tagName.toLowerCase();
      if (withClasses) {
        const cls = Array.from(cur.classList).slice(0, 2);
        if (cls.length) part += '.' + cls.map(esc).join('.');
      }
      const parent = cur.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter((c) => c.tagName === cur.tagName);
        if (same.length > 1) part += ':nth-of-type(' + (same.indexOf(cur) + 1) + ')';
      }
      parts.unshift(part);
      cur = cur.parentElement;
    }
    return parts.join(' > ');
  }
  function cssPath(el) {
    if (el === document.body) return 'body';
    if (el.id && isUniqueId(el.id)) return '#' + esc(el.id);
    try {
      const withCls = structuralPath(el, true);
      if (document.querySelectorAll(withCls).length === 1) return withCls;
    } catch (e) { /* fall through */ }
    return structuralPath(el, false);
  }

  const ownText = (el) => {
    let t = '';
    for (const n of el.childNodes) if (n.nodeType === 3) t += n.nodeValue;
    return t.replace(/\s+/g, ' ').trim();
  };
  function textRect(el) {
    let l = Infinity, t = Infinity, r = -Infinity, b = -Infinity, any = false;
    for (const n of el.childNodes) {
      if (n.nodeType !== 3 || !n.nodeValue.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const rc of range.getClientRects()) {
        if (rc.width === 0 && rc.height === 0) continue;
        any = true;
        l = Math.min(l, rc.left); t = Math.min(t, rc.top);
        r = Math.max(r, rc.right); b = Math.max(b, rc.bottom);
      }
    }
    return any ? { left: l, top: t, right: r, bottom: b } : null;
  }
  const pageBox = (r) => ({ x: round(r.left + sx), y: round(r.top + sy), w: round(r.width), h: round(r.height) });

  // ------------------------------------------------------------- colour maths
  function parseColor(s) {
    if (!s) return null;
    let m = s.match(/^rgba?\(([^)]+)\)$/);
    if (m) {
      const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
      if (p.length >= 3 && p.slice(0, 3).every((n) => !isNaN(n))) {
        return { r: p[0], g: p[1], b: p[2], a: p.length > 3 && !isNaN(p[3]) ? p[3] : 1 };
      }
    }
    m = s.match(/^color\(srgb\s+([^)]+)\)$/);
    if (m) {
      const [rgb, a] = m[1].split('/');
      const p = rgb.trim().split(/\s+/).map(Number);
      if (p.length >= 3) return { r: p[0] * 255, g: p[1] * 255, b: p[2] * 255, a: a ? Number(a) : 1 };
    }
    return null;
  }
  const blend = (top, base) => ({
    r: top.r * top.a + base.r * (1 - top.a),
    g: top.g * top.a + base.g * (1 - top.a),
    b: top.b * top.a + base.b * (1 - top.a),
    a: 1,
  });
  const lum = (c) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
  };
  const contrastRatio = (a, b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  };
  function effectiveBackground(el) {
    const layers = [];
    let uncertain = false;
    for (let cur = el; cur && cur.nodeType === 1; cur = cur.parentElement) {
      const cs = getCS(cur);
      const c = parseColor(cs.backgroundColor);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') uncertain = true;
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let base = { r: 255, g: 255, b: 255, a: 1 };
    for (let i = layers.length - 1; i >= 0; i--) base = blend(layers[i], base);
    return { color: base, uncertain };
  }

  // ------------------------------------------------------------ style compaction
  const DROP = {
    position: ['static'], top: ['auto'], right: ['auto'], bottom: ['auto'], left: ['auto'],
    'z-index': ['auto'], 'min-width': ['auto', '0px'], 'max-width': ['none'],
    'min-height': ['auto', '0px'], 'max-height': ['none'], margin: ['0px'], padding: ['0px'],
    'background-color': ['rgba(0, 0, 0, 0)'], 'background-image': ['none'], opacity: ['1'],
    visibility: ['visible'], 'line-height': ['normal'], 'text-align': ['start'],
    'text-overflow': ['clip'], 'white-space': ['normal'], 'word-break': ['normal'],
    'overflow-x': ['visible'], 'overflow-y': ['visible'], 'flex-direction': ['row'],
    'flex-wrap': ['nowrap'], 'justify-content': ['normal'], 'align-items': ['normal'],
    gap: ['normal', 'normal normal'], 'grid-template-columns': ['none'], float: ['none'],
    'object-fit': ['fill'], 'border-radius': ['0px'], 'box-shadow': ['none'], transform: ['none'],
    cursor: ['auto', 'default'], 'font-weight': ['400'], 'box-sizing': [],
  };
  const INHERITED = new Set(['color', 'font-family', 'font-size', 'font-weight', 'line-height',
    'text-align', 'visibility', 'cursor', 'white-space', 'word-break']);
  const ALWAYS_FOR_TEXT = new Set(['color', 'font-family', 'font-size', 'font-weight']);
  const BLOCK_TAGS = new Set(['div', 'p', 'section', 'article', 'header', 'footer', 'main', 'nav',
    'aside', 'ul', 'ol', 'li', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'body', 'fieldset', 'figure']);
  const INLINE_TAGS = new Set(['span', 'a', 'b', 'i', 'em', 'strong', 'small', 'code', 'label', 'abbr']);

  function compactStyles(el, cs, hasText) {
    const parent = el.parentElement ? getCS(el.parentElement) : null;
    const tag = el.tagName.toLowerCase();
    const out = {};
    for (const p of styleProps) {
      const v = cs.getPropertyValue(p);
      if (!v) continue;
      if (DROP[p] && DROP[p].includes(v)) continue;
      if (p === 'border' && /^0px none/.test(v)) continue;
      if (p === 'display' && ((v === 'block' && BLOCK_TAGS.has(tag)) || (v === 'inline' && INLINE_TAGS.has(tag)))) continue;
      if (INHERITED.has(p) && parent && parent.getPropertyValue(p) === v &&
          !(hasText && ALWAYS_FOR_TEXT.has(p))) continue;
      out[p] = p === 'font-family' ? trunc(v, 80) : p === 'background-image' ? trunc(v, 120) : v;
    }
    return out;
  }

  function reactInfo(el) {
    const key = Object.keys(el).find((k) => k.startsWith('__reactFiber$') || k.startsWith('__reactInternalInstance$'));
    if (!key) return null;
    const names = [];
    let source = null;
    for (let f = el[key], i = 0; f && i < 40 && names.length < 3; i++, f = f.return) {
      const t = f.type;
      if (!t || typeof t === 'string') continue;
      const n = t.displayName || t.name || (t.render && (t.render.displayName || t.render.name)) ||
        (t.type && (t.type.displayName || t.type.name));
      if (n && !names.includes(n)) {
        names.push(n);
        if (!source && f._debugSource) source = f._debugSource.fileName + ':' + f._debugSource.lineNumber;
      }
    }
    return names.length ? { components: names, source } : null;
  }

  // -------------------------------------------------------------- scan DOM
  const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'LINK', 'META', 'NOSCRIPT', 'TEMPLATE', 'HEAD',
    'TITLE', 'BASE', 'BR', 'WBR', 'SOURCE', 'TRACK', 'DATALIST', 'OPTION', 'OPTGROUP']);
  const INTERACTIVE_SEL = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=tab],[role=menuitem]';
  const LEAF_MEDIA = new Set(['IMG', 'VIDEO', 'CANVAS', 'INPUT', 'SELECT', 'TEXTAREA', 'BUTTON', 'IFRAME']);
  const IMPORTANT_TAGS = new Set(['IMG', 'PICTURE', 'VIDEO', 'CANVAS', 'SVG', 'INPUT', 'SELECT', 'TEXTAREA',
    'BUTTON', 'A', 'IFRAME', 'LABEL', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'NAV', 'HEADER', 'FOOTER',
    'MAIN', 'ASIDE', 'FORM', 'TABLE', 'DIALOG']);

  const everything = Array.from(document.body ? document.body.querySelectorAll('*') : []);
  const candidates = [];
  const byEl = new Map();
  let domIndex = 0;
  for (const el of everything) {
    if (candidates.length >= MAX_SCAN) break;
    domIndex++;
    if (SKIP_TAGS.has(el.tagName)) continue;
    if (el instanceof SVGElement && el.tagName.toLowerCase() !== 'svg') continue;
    const cs = getCS(el);
    if (cs.display === 'none' || cs.display === 'contents') continue;
    if (cs.visibility === 'hidden' || cs.visibility === 'collapse') continue;
    if (parseFloat(cs.opacity) === 0) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) continue;
    const text = ownText(el);
    const tr = text ? textRect(el) : null;
    const isSrOnly = rect.width <= 2 && rect.height <= 2;
    const interactive = el.matches(INTERACTIVE_SEL);
    const c = {
      el, cs, rect, text, tr, domIndex, isSrOnly, interactive,
      tag: el.tagName, hints: [],
      ink: tr || (LEAF_MEDIA.has(el.tagName) || (el instanceof SVGElement) ? rect : null),
    };
    candidates.push(c);
    byEl.set(el, c);
  }

  // ----------------------------------------------------------------- hints
  const hints = [];
  const addHint = (type, severity, c, message, details = {}, related = null) => {
    hints.push({ type, severity, ref: c, related, message, details });
  };
  const SEV = { high: 3, medium: 2, low: 1 };
  const overflowsClip = (cs) => ['hidden', 'clip'].includes(cs.overflowX) || ['hidden', 'clip'].includes(cs.overflowY);

  // 1. Page-level horizontal overflow + offenders
  const escapesViewportX = (c) => {
    if (c.rect.right <= cw + 1 || c.isSrOnly) return false;
    if (c.cs.position === 'fixed') return false;
    for (let a = c.el.parentElement; a && a !== de; a = a.parentElement) {
      const acs = getCS(a);
      if (acs.overflowX !== 'visible' && a.getBoundingClientRect().right <= cw + 1) return false;
    }
    return true;
  };
  let pageOverflow = null;
  if (de.scrollWidth > cw + 1) {
    const escaping = candidates.filter(escapesViewportX);
    const escapingEls = new Set(escaping.map((c) => c.el));
    // Report only the outermost offenders; their descendants overflow because they do.
    const offenders = escaping
      .filter((c) => { for (let a = c.el.parentElement; a; a = a.parentElement) if (escapingEls.has(a)) return false; return true; })
      .sort((a, b) => b.rect.right - a.rect.right).slice(0, 5);
    pageOverflow = { scrollWidth: de.scrollWidth, clientWidth: cw, extra: de.scrollWidth - cw };
    addHint('horizontal-scroll', 'high', null,
      `Page scrolls horizontally: content is ${de.scrollWidth}px wide in a ${cw}px viewport.`,
      { ...pageOverflow, offenders: offenders.length });
    offenders.forEach((c) => addHint('viewport-overflow', 'medium', c,
      `Extends ${Math.round(c.rect.right - cw)}px beyond the right edge of the viewport.`,
      { right: round(c.rect.right + sx), viewport_width: cw }));
  }

  // 2. Text overflowing / clipped by its own box or an ancestor
  for (const c of candidates) {
    if (!c.tr || c.isSrOnly) continue;
    const fs = parseFloat(c.cs.fontSize) || 16;
    const tolX = 2, tolY = Math.max(3, fs * 0.25);
    const r = c.rect, t = c.tr;
    const spill = { right: t.right - r.right, left: r.left - t.left, bottom: t.bottom - r.bottom, top: r.top - t.top };
    const exceeds = spill.right > tolX || spill.left > tolX || spill.bottom > tolY || spill.top > tolY;
    const scrolls = ['auto', 'scroll'].includes(c.cs.overflowX) || ['auto', 'scroll'].includes(c.cs.overflowY);
    if (exceeds && !scrolls) {
      const clips = overflowsClip(c.cs);
      const ellipsis = c.cs.textOverflow === 'ellipsis';
      addHint(clips ? 'text-clipped' : 'text-overflow', clips ? (ellipsis ? 'medium' : 'high') : 'medium', c,
        clips
          ? `Text is cut off by its own box${ellipsis ? ' (ellipsis)' : ''}: "${trunc(c.text, 40)}".`
          : `Text spills outside its box: "${trunc(c.text, 40)}".`,
        { spill_px: { right: round(spill.right), bottom: round(spill.bottom), left: round(spill.left), top: round(spill.top) },
          white_space: c.cs.whiteSpace, overflow: c.cs.overflowX + '/' + c.cs.overflowY });
      continue;
    }
    // clipped by an ancestor with overflow hidden
    for (let a = c.el.parentElement; a && a !== de; a = a.parentElement) {
      const acs = getCS(a);
      if (!overflowsClip(acs)) continue;
      const ar = a.getBoundingClientRect();
      const out = Math.max(t.right - ar.right, ar.left - t.left, t.bottom - ar.bottom, ar.top - t.top);
      if (out > Math.max(tolX, fs * 0.25)) {
        const cc = byEl.get(a);
        addHint('clipped-by-ancestor', 'high', c,
          `Text is cut off by an ancestor with overflow:hidden (${cssPath(a)}): "${trunc(c.text, 40)}".`,
          { ancestor: cssPath(a), hidden_px: round(out) }, cc || null);
      }
      break;
    }
  }

  // 3. Overlapping content (text / media / controls)
  // Fixed/sticky chrome (cookie bars, headers) overlaps content by design; the
  // occlusion check below reports the cases where that actually hides something.
  const fixedCache = new Map();
  const inFixed = (el) => {
    if (!fixedCache.has(el)) {
      const pos = getCS(el).position;
      fixedCache.set(el, pos === 'fixed' || pos === 'sticky' || (el.parentElement ? inFixed(el.parentElement) : false));
    }
    return fixedCache.get(el);
  };
  const inkEls = candidates.filter((c) => c.ink && !c.isSrOnly).slice(0, 700);
  const seenPair = new Set();
  const overlapPairs = [];
  for (let i = 0; i < inkEls.length; i++) {
    const a = inkEls[i];
    for (let j = i + 1; j < inkEls.length; j++) {
      const b = inkEls[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      if (inFixed(a.el) !== inFixed(b.el)) continue;
      const ix =Math.min(a.ink.right, b.ink.right) - Math.max(a.ink.left, b.ink.left);
      const iy = Math.min(a.ink.bottom, b.ink.bottom) - Math.max(a.ink.top, b.ink.top);
      if (ix <= 3 || iy <= 3) continue;
      const areaA = (a.ink.right - a.ink.left) * (a.ink.bottom - a.ink.top);
      const areaB = (b.ink.right - b.ink.left) * (b.ink.bottom - b.ink.top);
      const ratio = (ix * iy) / Math.max(1, Math.min(areaA, areaB));
      if (ratio < 0.15) continue;
      const key = i + ':' + j;
      if (seenPair.has(key)) continue;
      seenPair.add(key);
      overlapPairs.push([a.el, b.el]);
      addHint('overlap', ratio > 0.5 ? 'high' : 'medium', a,
        `Overlaps ${cssPath(b.el)} (${Math.round(ratio * 100)}% of the smaller element).`,
        { overlap_ratio: round(ratio), other: cssPath(b.el) }, b);
    }
  }

  // 4. Occlusion: something else is painted on top of visible content
  const occluders = new Map();
  for (const c of inkEls) {
    if (!c.text && !c.interactive) continue;
    const cx = (c.ink.left + c.ink.right) / 2, cy = (c.ink.top + c.ink.bottom) / 2;
    if (cx < 0 || cy < 0 || cx >= cw || cy >= ch) continue;
    const top = document.elementFromPoint(cx, cy);
    if (!top || top === c.el || c.el.contains(top) || top.contains(c.el)) continue;
    if (!occluders.has(top)) occluders.set(top, []);
    occluders.get(top).push(c);
  }
  for (const [top, list] of occluders) {
    const tc = byEl.get(top) || null;
    if (list.length >= 4) {
      addHint('overlay-covers-content', 'high', tc,
        `${cssPath(top)} is painted over ${list.length} visible elements.`,
        { covered: list.length, occluder: cssPath(top) });
    } else {
      list.forEach((c) => {
        // Already reported as an overlap between the same two elements.
        const dup = overlapPairs.some(([x, y]) =>
          (x === c.el && (y === top || y.contains(top))) || (y === c.el && (x === top || x.contains(top))));
        if (!dup) addHint('occluded', 'medium', c, `Covered by ${cssPath(top)} at its centre point.`, { occluder: cssPath(top) }, tc);
      });
    }
  }

  // 4b. Content spilling out of a visible container (card, panel, form)
  const hasVisibleBox = (cs) => cs.backgroundColor !== 'rgba(0, 0, 0, 0)' || cs.boxShadow !== 'none' ||
    (cs.borderTopWidth !== '0px' && cs.borderTopStyle !== 'none');
  for (const c of candidates) {
    const p = c.el.parentElement;
    if (!p || p === document.body || c.isSrOnly || !['static', 'relative', 'sticky'].includes(c.cs.position)) continue;
    const pcs = getCS(p);
    if (pcs.overflowX !== 'visible' || pcs.overflowY !== 'visible' || !hasVisibleBox(pcs)) continue;
    if (c.cs.display === 'inline' || pcs.display === 'contents') continue;
    const pr = p.getBoundingClientRect();
    const out = {
      right: c.rect.right - pr.right, left: pr.left - c.rect.left,
      bottom: c.rect.bottom - pr.bottom, top: pr.top - c.rect.top,
    };
    const worst = Math.max(out.right, out.left, out.bottom, out.top);
    if (worst > 2) {
      addHint('container-overflow', worst > 8 ? 'medium' : 'low', c,
        `Sticks out ${Math.round(worst)}px beyond its parent ${cssPath(p)}, which has a visible background/border.`,
        { parent: cssPath(p), overflow_px: { right: round(out.right), left: round(out.left), bottom: round(out.bottom), top: round(out.top) } },
        byEl.get(p) || null);
    }
  }

  // 5. Per-element checks
  const fontSizes = new Map();
  for (const c of candidates) {
    const { el, cs, rect } = c;
    const tag = c.tag;
    if (c.text) {
      const fam = (cs.fontFamily.split(',')[0] || '').replace(/["']/g, '').trim();
      fontSizes.set(fam, (fontSizes.get(fam) || 0) + 1);
    }
    if (c.isSrOnly) continue;

    if (c.text) {
      const fs = parseFloat(cs.fontSize) || 16;
      if (fs < 12 && /[\p{L}\p{N}]/u.test(c.text)) addHint('tiny-text', fs < 10 ? 'medium' : 'low', c,
        `Font size ${round(fs)}px is hard to read: "${trunc(c.text, 40)}".`, { font_size: round(fs) });

      const fg = parseColor(cs.color);
      if (fg) {
        const { color: bg, uncertain } = effectiveBackground(el);
        const fgc = blend({ ...fg, a: fg.a * (parseFloat(cs.opacity) || 1) }, bg);
        const ratio = contrastRatio(fgc, bg);
        const bold = parseInt(cs.fontWeight, 10) >= 700;
        const large = fs >= 24 || (bold && fs >= 18.66);
        const need = large ? 3 : 4.5;
        if (ratio < need) {
          const sev = uncertain ? 'low' : (ratio < 2.5 ? 'high' : 'medium');
          addHint('low-contrast', sev, c,
            `Contrast ${round(ratio)}:1 is below ${need}:1 for "${trunc(c.text, 40)}"` +
            (uncertain ? ' (background image/gradient; verify visually).' : '.'),
            { ratio: round(ratio), required: need, color: cs.color, background: `rgb(${Math.round(bg.r)}, ${Math.round(bg.g)}, ${Math.round(bg.b)})`, uncertain });
        }
      }
    }

    if (tag === 'IMG') {
      const img = el;
      if (!img.hasAttribute('alt') && img.getAttribute('role') !== 'presentation') {
        addHint('image-missing-alt', 'low', c, 'Image has no alt attribute.', { src: trunc(img.currentSrc || img.src || '', 120) });
      }
      if (img.complete && img.naturalWidth === 0 && (img.currentSrc || img.src)) {
        addHint('image-broken', 'high', c, 'Image failed to load.', { src: trunc(img.currentSrc || img.src, 160) });
      } else if (img.naturalWidth > 0 && rect.width >= 24 && rect.height >= 24 && cs.objectFit === 'fill') {
        const nat = img.naturalWidth / img.naturalHeight, ren = rect.width / rect.height;
        if (Math.abs(nat / ren - 1) > 0.1) {
          addHint('image-distorted', 'medium', c,
            `Image is stretched: natural size ${img.naturalWidth}×${img.naturalHeight}, rendered ${Math.round(rect.width)}×${Math.round(rect.height)}.`,
            { natural: [img.naturalWidth, img.naturalHeight], rendered: [round(rect.width), round(rect.height)] });
        }
      }
    }

    if (c.interactive) {
      const minSide = Math.min(rect.width, rect.height);
      if (cs.display !== 'inline' && minSide < 24 && !(tag === 'INPUT' && ['checkbox', 'radio'].includes(el.type) && minSide >= 13)) {
        addHint('small-tap-target', minSide < 16 ? 'medium' : 'low', c,
          `Interactive target is only ${round(rect.width)}×${round(rect.height)}px (WCAG 2.2 minimum is 24×24).`,
          { width: round(rect.width), height: round(rect.height) });
      }
      const hasName = c.text || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') ||
        el.getAttribute('title') || (el.value && ['submit', 'button', 'reset'].includes(el.type)) ||
        el.querySelector('img[alt]:not([alt=""]), svg title, [aria-label]') ||
        (el.textContent && el.textContent.trim()) ||
        (tag === 'INPUT' && (el.placeholder || (el.labels && el.labels.length) || el.id && document.querySelector('label[for="' + esc(el.id) + '"]')));
      if (!hasName && tag !== 'TEXTAREA' && tag !== 'SELECT' && tag !== 'INPUT') {
        addHint('empty-interactive', 'medium', c, 'Interactive element has no visible text or accessible name.', {});
      }
    }

    if ((c.text || c.interactive) && cs.position !== 'fixed' && (rect.right < 0 || rect.bottom < 0)) {
      addHint('offscreen-content', 'low', c, 'Visible content is positioned off-screen (above/left of the page).',
        { right: round(rect.right), bottom: round(rect.bottom) });
    }
  }

  // ------------------------------------------------- choose hints & elements
  hints.sort((a, b) => SEV[b.severity] - SEV[a.severity]);
  const keptHints = hints.slice(0, maxHints);
  const flagged = new Set();
  for (const h of keptHints) {
    if (h.ref) { flagged.add(h.ref); h.ref.hints.push(h.type); }
    if (h.related) flagged.add(h.related);
  }
  const hasBox = (c) => {
    const cs = c.cs;
    return (cs.backgroundColor !== 'rgba(0, 0, 0, 0)') || cs.boxShadow !== 'none' ||
      (cs.borderTopWidth !== '0px' && cs.borderTopStyle !== 'none');
  };
  const important = (c) => flagged.has(c) || c.text || IMPORTANT_TAGS.has(c.tag) || c.interactive || hasBox(c);
  let chosen = candidates.filter((c) => flagged.has(c));
  const rest = candidates.filter((c) => !flagged.has(c));
  const prio = rest.filter(important), others = rest.filter((c) => !important(c));
  for (const c of prio.concat(others)) {
    if (chosen.length >= maxElements) break;
    chosen.push(c);
  }
  chosen.sort((a, b) => a.domIndex - b.domIndex);
  const idOf = new Map();
  chosen.forEach((c, i) => idOf.set(c, i + 1));
  const idByEl = new Map();
  chosen.forEach((c) => idByEl.set(c.el, idOf.get(c)));

  // ---------------------------------------------------------------- CSS rules
  const rules = [];
  const stats = { sheets: 0, total: 0, kept: 0, dropped_unmatched: 0, unparsable: 0, keyframes: [], font_faces: [], unavailable: [] };
  const chosenEls = new Set(chosen.map((c) => c.el));
  const elRules = new Map();

  function splitSelectors(sel) {
    const out = []; let depth = 0, cur = '';
    for (const ch2 of sel) {
      if (ch2 === '(' || ch2 === '[') depth++;
      else if (ch2 === ')' || ch2 === ']') depth--;
      if (ch2 === ',' && depth === 0) { out.push(cur.trim()); cur = ''; } else cur += ch2;
    }
    if (cur.trim()) out.push(cur.trim());
    return out;
  }
  const PSEUDO_RE = /::?(?:hover|focus-visible|focus-within|focus|active|visited|target|before|after|first-line|first-letter|placeholder|selection|marker|backdrop|file-selector-button|-webkit-[\w-]+|-moz-[\w-]+|-ms-[\w-]+)(\([^)]*\))?/gi;
  function stripDynamic(part) {
    let states = false;
    let s = part.replace(PSEUDO_RE, () => { states = true; return ''; }).trim();
    if (!s || /[>+~]$/.test(s)) s += '*';
    return { sel: s, states };
  }
  function matchSelector(selectorText) {
    const matched = new Set();
    let states = false, ok = false, total = 0;
    for (const part of splitSelectors(selectorText)) {
      const { sel, states: st } = stripDynamic(part);
      let list;
      try { list = document.querySelectorAll(sel); ok = true; } catch (e) { continue; }
      if (list.length && st) states = true;
      total += list.length;
      list.forEach((el) => { if (chosenEls.has(el)) matched.add(el); });
    }
    return { matched, states, ok, total };
  }

  function addStyleRule(rule, ctx, parentSel) {
    if (rules.length >= maxRules) return;
    let sel = rule.selectorText;
    if (parentSel) sel = sel.includes('&') ? sel.replace(/&/g, ':is(' + parentSel + ')') : ':is(' + parentSel + ') ' + sel;
    stats.total++;
    const m = matchSelector(sel);
    if (!m.ok) stats.unparsable++;
    if (m.total === 0) stats.dropped_unmatched++;
    else {
      const id = rules.length + 1;
      rules.push({
        id, source: ctx.source, at: ctx.at, selector: parentSel ? sel : rule.selectorText,
        css: rule.style.cssText.trim(), matches: m.total, media_active: ctx.active, states: m.states,
      });
      stats.kept++;
      m.matched.forEach((el) => {
        if (!elRules.has(el)) elRules.set(el, []);
        const arr = elRules.get(el);
        if (arr.length < 30) arr.push(id);
      });
    }
    if (rule.cssRules && rule.cssRules.length) {
      for (const child of rule.cssRules) if (child instanceof CSSStyleRule) addStyleRule(child, ctx, sel);
    }
  }
  function walkRules(list, ctx) {
    for (const rule of list) {
      if (rules.length >= maxRules) return;
      if (rule instanceof CSSStyleRule) addStyleRule(rule, ctx, null);
      else if (rule instanceof CSSMediaRule) {
        const cond = rule.conditionText != null ? rule.conditionText : rule.media.mediaText;
        let active = false;
        try { active = window.matchMedia(cond).matches; } catch (e) { /* ignore */ }
        walkRules(rule.cssRules, { ...ctx, at: [...ctx.at, '@media ' + cond], active: ctx.active && active });
      } else if (rule instanceof CSSSupportsRule) {
        let active = true;
        try { active = CSS.supports(rule.conditionText); } catch (e) { /* ignore */ }
        walkRules(rule.cssRules, { ...ctx, at: [...ctx.at, '@supports ' + rule.conditionText], active: ctx.active && active });
      } else if (rule instanceof CSSFontFaceRule) {
        stats.font_faces.push(trunc(rule.cssText.replace(/\s+/g, ' '), 200));
      } else if (rule instanceof CSSKeyframesRule) {
        stats.keyframes.push(rule.name);
      } else if (rule instanceof CSSImportRule) {
        try { if (rule.styleSheet) walkRules(rule.styleSheet.cssRules, ctx); } catch (e) { /* cross-origin */ }
      } else if (rule.cssRules) {
        const header = rule.cssText.slice(0, rule.cssText.indexOf('{')).trim();
        walkRules(rule.cssRules, { ...ctx, at: [...ctx.at, header] });
      }
    }
  }

  let styleTagCount = 0;
  const sheets = Array.from(document.styleSheets);
  const adopted = (document.adoptedStyleSheets || []).slice();
  sheets.concat(adopted).forEach((sheet, idx) => {
    stats.sheets++;
    const isTag = sheet.ownerNode && sheet.ownerNode.tagName === 'STYLE';
    const source = sheet.href || (isTag ? '<style>#' + (++styleTagCount) : '<adopted>#' + idx);
    let cssRules = null;
    try { cssRules = sheet.cssRules; } catch (e) { /* cross-origin / file:// */ }
    if (!cssRules && sheet.href && externalSheets && externalSheets[sheet.href] != null) {
      try {
        const s = new CSSStyleSheet();
        s.replaceSync(externalSheets[sheet.href]);
        cssRules = s.cssRules;
      } catch (e) { /* unparsable */ }
    }
    if (!cssRules) { stats.unavailable.push(source); return; }
    walkRules(cssRules, { source, at: [], active: true });
  });

  // ------------------------------------------------------------ build output
  const elements = chosen.map((c) => {
    const el = c.el;
    const attrs = {};
    for (const name of ['id', 'class', 'href', 'src', 'alt', 'type', 'name', 'placeholder', 'role',
      'aria-label', 'title', 'for', 'style', 'data-testid', 'tabindex']) {
      const v = el.getAttribute(name);
      if (v != null && v !== '') attrs[name] = trunc(v, 160);
    }
    let parentId = null;
    for (let p = el.parentElement; p; p = p.parentElement) {
      if (idByEl.has(p)) { parentId = idByEl.get(p); break; }
    }
    const vis = c.rect.right > 0 && c.rect.bottom > 0 && c.rect.left < cw && c.rect.top < ch;
    const rec = {
      id: idOf.get(c), selector: cssPath(el), tag: el.tagName.toLowerCase(), attrs,
      text: trunc(c.text, maxTextLen), bbox: pageBox(c.rect), in_viewport: vis,
      parent: parentId, styles: compactStyles(el, c.cs, !!c.text),
      rule_ids: elRules.get(el) || [], flags: Array.from(new Set(c.hints)),
    };
    const rx = reactInfo(el);
    if (rx) rec.react = rx;
    return rec;
  });

  const outHints = keptHints.map((h, i) => ({
    id: i + 1, type: h.type, severity: h.severity,
    element_id: h.ref ? idOf.get(h.ref) || null : null,
    related_id: h.related ? idOf.get(h.related) || null : null,
    message: h.message, details: h.details,
  }));

  // HTML snapshot with data-omni-id on recorded elements (live DOM untouched).
  const clone = de.cloneNode(true);
  const liveAll = Array.from(de.querySelectorAll('*'));
  const cloneAll = Array.from(clone.querySelectorAll('*'));
  if (liveAll.length === cloneAll.length) {
    liveAll.forEach((el, i) => {
      const id = idByEl.get(el);
      if (id !== undefined) cloneAll[i].setAttribute('data-omni-id', String(id));
    });
  }
  const doctype = document.doctype ? '<!DOCTYPE ' + document.doctype.name + '>\n' : '';

  const fonts = [];
  try {
    document.fonts.forEach((f) => fonts.push({ family: f.family.replace(/["']/g, ''), weight: f.weight, style: f.style, status: f.status }));
  } catch (e) { /* ignore */ }

  const images = Array.from(document.images);
  return {
    page: {
      url: location.href, title: document.title, lang: de.lang || null,
      viewport: { width: window.innerWidth, height: window.innerHeight, client_width: cw, client_height: ch },
      document: { scroll_width: de.scrollWidth, scroll_height: de.scrollHeight },
      device_pixel_ratio: window.devicePixelRatio,
      total_dom_elements: everything.length, rendered_elements: candidates.length,
      recorded_elements: chosen.length, images: images.length,
      fonts_used: Array.from(fontSizes.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([family, count]) => ({ family, text_elements: count })),
      font_faces: fonts.slice(0, 30), horizontal_overflow: pageOverflow,
    },
    elements, hints: outHints, rules, rule_stats: stats,
    html: doctype + clone.outerHTML,
  };
}
