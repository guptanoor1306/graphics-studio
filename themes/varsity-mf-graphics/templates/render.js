// Varsity MF graphics renderer. window.FRAME (one frame from spec.json) + window.OPTS {overlay:bool}
(function () {
 const fontsReady = Promise.all(["500","600","700","800","900"].map(w => document.fonts.load(w + " 40px Inter"))).catch(() => {});
 fontsReady.then(() => {
  try { run(); } catch (e) { window.RENDER_ERROR = "render error: " + e.message; }
  window.RENDERED = true;
  if ((window.OPTS || {}).studioEdit) {
    if (typeof window.initMfInlineText === "function") window.initMfInlineText();
    if (typeof window.studioBootLayers === "function") window.studioBootLayers();
  }
 });
 function run() {
  const A = "../assets/";
  const F = window.FRAME, O = window.OPTS || {};
  const stage = document.getElementById("stage");
  const ANCHOR_TYPES = ["ribbon", "definition", "anchor"];
  const isAnchor = ANCHOR_TYPES.includes(F.type);
  const overlay = !!O.overlay && isAnchor;

  // ---------- helpers ----------
  function el(tag, cls, css, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (css) Object.assign(e.style, css);
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function add(e, parent) { (parent || stage).appendChild(e); return e; }
  function px(v) { return typeof v === "number" ? v + "px" : v; }
  function img(src, x, y, w, extra) {
    if (String(src).startsWith("TODO:")) {
      const ph = el("div", "abs", Object.assign({ left: px(x), top: px(y), width: px(w || 300), height: px(Math.round((w || 300) * 0.75)), border: "4px dashed #e4950b", background: "rgba(255,255,255,.6)", display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center", font: "600 24px Inter", color: "#a35f00", padding: "12px" }, extra || {}), "ASSET NEEDED<br>" + esc(src.slice(5)));
      return add(ph);
    }
    const i = el("img", "abs", Object.assign({ left: px(x), top: px(y), width: w ? px(w) : "auto" }, extra || {}));
    i.src = src.startsWith("http") || src.startsWith("data:") || src.startsWith("/") || src.startsWith("../") ? src : A + src;
    return add(i);
  }
  function content(e) { e.dataset.content = "1"; return e; }
  function isText(e) { return /(^| )(pill|nlabel|qbox|chip|defbox|tbl|caption)( |$)/.test(e.className) || e.tagName === "TABLE"; }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
  function rich(s) { // **bold** and line breaks
    return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(\w)-(?=\w)/g, "$1\u2011").replace(/\n/g, "<br>");
  }

  // ---------- backgrounds ----------
  function background(kind) {
    if (overlay) return;
    if (kind === "light") add(el("div", "bg light"));
    else if (kind === "dark") { add(el("div", "bg dark")); document.body.classList.add("darkmode"); }
    else if (kind === "plate") {
      const b = add(el("div", "bg plate"));
      if (F.plate) b.style.backgroundImage = `url(${F.plate.startsWith("../") ? F.plate : A + F.plate})`;
    }
  }
  function darkGrid() {
    const g = add(el("div", "gridlines"));
    [384, 767, 1150, 1535].forEach(x => add(el("i", "", { left: x + "px", top: 0, width: "3px", height: "1080px" }), g));
    [310, 694].forEach(y => add(el("i", "", { top: y + "px", left: 0, height: "3px", width: "1920px" }), g));
  }

  // ---------- decor ----------
  const ZIG = '<svg width="36" height="90" viewBox="0 0 36 90"><polyline points="26,4 8,30 28,46 10,86" fill="none" stroke="#f2b632" stroke-width="7" stroke-linejoin="miter"/></svg>';
  function zig(x, y, rot) { add(el("div", "abs decor", { left: x + "px", top: y + "px", transform: `rotate(${rot || 0}deg)` }, ZIG)); }
  function diamond(x, y, s, c) { add(el("div", "abs decor", { left: x + "px", top: y + "px", width: s + "px", height: s + "px", background: c || "#f39a2b", transform: "rotate(45deg)" })); }
  function bar(x, y, w, h, rot, c) { add(el("div", "abs decor", { left: x + "px", top: y + "px", width: w + "px", height: h + "px", background: c || "#4f8ff0", transform: `rotate(${rot || 0}deg)` })); }
  function pixbar(x, y) { // stepped blue "pixel" bar from the light scenes
    bar(x, y, 26, 80, 0, "#4f9bf0"); bar(x - 24, y + 78, 26, 80, 0, "#4f9bf0");
  }
  function decor(set) {
    if (F.decor === false || set === "none") return;
    if (set === "light") {
      pixbar(236, 103); pixbar(1680, 181); bar(1790, 499, 26, 80); pixbar(104, 730); bar(1680, 863, 26, 81);
      zig(66, 111); zig(1625, 493, 0); diamond(1650, 260, 22); diamond(330, 980, 18, "#9a9a9a");
    } else if (set === "light-frames") {
      img("decor/frame_square_green.png", 90, 870, 190); img("decor/frame_square_blue.png", 1800, 140, 220);
      diamond(1700, 230, 22); bar(250, 160, 18, 70, -35, "#5b55e6"); bar(1860, 860, 14, 60, 15, "#5b55e6"); diamond(380, 860, 16, "#8f8f8f");
    } else if (set === "light-min") {
      bar(205, 45, 22, 70, -30, "#5b55e6"); diamond(1610, 130, 22); diamond(1840, 600, 30); diamond(60, 520, 22); bar(1785, 975, 14, 55, 20, "#5b55e6");
    } else if (set === "dark-min") {
      img("decor/burst_orange.png", 1100, 1030, 216);
    } else if (set === "dark") {
      img("decor/star_blue.png", 1470, 92, 107); img("decor/leaf_green.png", 1730, 930, 82);
      img("decor/burst_orange.png", 265, 1030, 216);
    } else if (set === "anchor") {
      zig(174, 62); zig(1726, 444); diamond(1206, 610, 30); diamond(1603, 942, 20); diamond(969, 288, 20, "#b9b9b9");
      bar(222, 972, 18, 80, 35, "#5b55e6"); bar(1690, -20, 18, 60, 15, "#5b55e6");
    } else if (set === "anchor-frame") {
      zig(208, 112); zig(1760, 494); diamond(1799, 112, 32); diamond(586, 863, 34, "#c9c9c9");
      add(el("div", "abs decor", { left: "380px", top: "-80px", width: "190px", height: "190px", border: "34px solid #3b82e6", transform: "rotate(30deg)" }));
      diamond(445, -20, 64);
    }
  }

  // ---------- components ----------
  const PILL_BG = "linear-gradient(90deg,#4a44c9 0%,#5b55e6 50%,#7b76ee 100%)";
  function pill(p, x, y, opts) {
    opts = opts || {};
    const icon = p.icon || "search";
    const e = el("div", "pill" + (p.size ? " " + p.size : ""));
    e.style.background = PILL_BG;
    let h = "";
    if (icon === "search") h += `<img class="ic" src="${A}ui/icon_search.png">`;
    if (icon === "coin") h += `<div class="coin"><img src="${A}ui/icon_rupee_coin.png"></div>`;
    h += `<span class="t" style="color:#fff${p.fontSize ? ";font-size:" + p.fontSize + "px" : ""}">${esc(p.text)}</span>`;
    if (p.knob !== false && icon !== "coin") h += `<span class="knob"></span>`;
    h += `<div class="grain"></div>`;
    e.innerHTML = h;
    add(content(e));
    // position: x can be "center"
    requestAnimationFrame(() => {});
    const w = e.offsetWidth;
    e.style.left = (x === "center" ? (960 - w / 2) : x === "right" ? (1920 - w - 60) : x === "left" ? 60 : x) + "px";
    if (opts.cx !== undefined) e.style.left = (opts.cx - w / 2) + "px";
    e.style.top = y + "px";
    if (opts.studioLayer) e.dataset.mfStudioLayer = opts.studioLayer;
    return e;
  }
  function cursor(c) {
    if (!c) return;
    const src = c.style === "outline" ? "ui/cursor_arrow_outline.png" : "ui/cursor_pixel_3d.png";
    img(src, c.x, c.y, c.w || (c.style === "outline" ? 121 : 103));
  }
  function disclaimer() {
    if (!F.disclaimer) return;
    const t = F.disclaimer === true ? "The securities quoted are for illustration only and are not recommendatory." : F.disclaimer;
    add(el("div", "disclaimer", {}, esc(t)));
  }
  function logoCard(c) {
    if (c.asset) {
      const i = img(c.asset, c.x, c.y, c.w || 170, { transform: `rotate(${c.rot || 0}deg)` });
      content(i); return i;
    }
    // generic card: tilted coloured frame + white inner + logo image or text
    const s = c.w || 175, col = c.color || "#2f4fd0";
    const e = el("div", "abs", { left: c.x + "px", top: c.y + "px", width: s + "px", height: s + "px", background: col, transform: `rotate(${c.rot || 0}deg)`, padding: (s * 0.13) + "px" });
    const inner = el("div", "", { width: "100%", height: "100%", background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: (s * 0.17) + "px", textAlign: "center", lineHeight: 1.05, padding: "6px" });
    inner.innerHTML = c.logo ? `<img src="${c.logo.startsWith("../") ? c.logo : A + c.logo}" style="max-width:88%;max-height:88%">` : esc(c.text || "");
    e.appendChild(inner); add(content(e));
    e.appendChild(el("div", "grain"));
    return e;
  }
  function numLabel(it) {
    const e = el("div", "nlabel" + (it.state ? " " + it.state : ""), {}, `<span class="c">${it.n}</span><span>${esc(it.text)}</span>`);
    if (it.fontSize) e.style.fontSize = it.fontSize + "px";
    add(content(e));
    const w = e.offsetWidth;
    const ax = it.align === "right" ? it.x - w : it.align === "center" ? it.x - w / 2 : it.x;
    e.style.left = ax + "px"; e.style.top = it.y + "px";
    return e;
  }
  function orbitPositions(n, cx, cy, rx, ry) {
    const out = [];
    for (let i = 0; i < n; i++) {
      const a = Math.PI * (1 - (i + 0.5) / n) ; // 180..0 deg
      const ang = Math.PI * 0.94 - i * (Math.PI * 0.88) / Math.max(n - 1, 1);
      const x = cx + rx * Math.cos(ang), y = cy - ry * Math.sin(ang);
      out.push({ x: x, y: y, align: "center" });
    }
    return out;
  }

  // ---------- frame types ----------
  const T = {};

  // Light (or dark) illustrated scene: keyword pill + hero illustration + labels/cards/chain
  T.scene = function () {
    const bgk = F.bg || "light";
    background(bgk);
    if (bgk === "dark") darkGrid();
    decor(F.decorset || (bgk === "dark" ? "dark" : "light"));
    if (F.floor !== false && F.hero) img("decor/floor_stripes.png", 484, 778, 926);
    if (F.burst) img("decor/burst_orange.png", F.burst.x, F.burst.y, F.burst.w || 842);
    if (F.hero) { const h = img(F.hero.asset, F.hero.x, F.hero.y, F.hero.w); content(h); h.dataset.hero = "1"; if (F.hero.bleed) h.dataset.bleed = "1"; if (F.hero.rot) h.style.transform = `rotate(${F.hero.rot}deg)`; }
    (F.props || []).forEach((p, pi) => {
      const i = img(p.asset, p.x, p.y, p.w);
      if (p.rot) i.style.transform = `rotate(${p.rot}deg)`;
      i.dataset.mfProp = String(pi);
      content(i);
    });
    (F.cards || []).forEach((c, ci) => {
      const node = logoCard(c);
      if (node) node.dataset.mfCard = String(ci);
    });
    if (F.labels) {
      const L = F.labels, n = L.items.length;
      const pos = L.layout === "orbit" ? orbitPositions(n, L.cx || 960, L.cy || 760, L.rx || 720, L.ry || 470) : null;
      L.items.forEach((it, i) => {
        const q = Object.assign({}, pos ? pos[i] : {}, it, { n: it.n || i + 1 });
        if (L.active !== undefined) q.state = (L.active === i + 1 || (Array.isArray(L.active) && L.active.includes(i + 1))) ? "on" : (L.dimOthers ? "off" : "");
        numLabel(q);
      });
    }
    if (F.chain) chain(F.chain);
    if (F.pill) pill(Object.assign({ size: "lg" }, F.pill), F.pill.x !== undefined ? F.pill.x : "center", F.pill.y !== undefined ? F.pill.y : 104, { studioLayer: "pill" });
    if (F.html) add(el("div", "abs", { left: 0, top: 0, width: "1920px", height: "1080px" }, F.html));
    cursor(F.cursor);
    disclaimer();
  };

  // India → Gujarat → ... breadcrumb of small pills
  function chain(c) {
    const wrap = el("div", "abs", { left: "0", top: c.y + "px", width: "1920px", display: "flex", justifyContent: c.align || "center", alignItems: "center", gap: "26px" });
    c.items.forEach((t, i) => {
      if (i) wrap.appendChild(el("span", "", { fontWeight: 900, fontSize: "56px", color: c.dark ? "#fff" : "#1d1d1d" }, "→"));
      const on = c.active === undefined || c.active === i + 1 || c.active === "all";
      const p = el("div", "pill sm", { position: "relative", opacity: on ? 1 : .35, background: PILL_BG }, `<span class="t" style="color:#fff">${esc(t)}</span><div class="grain"></div>`);
      if (i === c.items.length - 1 && c.lastIcon !== false) p.innerHTML = `<img class="ic" src="${A}ui/icon_search.png">` + p.innerHTML;
      wrap.appendChild(p);
    });
    add(content(wrap));
  }

  // Roto big text: keyword on the white ribbon, anchor in front (editor rotos)
  T.ribbon = function () {
    background("plate");
    decor("anchor-frame");
    img("decor/ribbon_yellow_curve_full.png", 0, 0, 1920);
    img("ui/ribbon_blank_full.png", 0, 0, 1920);
    const text = F.text;
    const len = text.length;
    const fs = F.size || 150;
    const svg = `<svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute;left:0;top:0">
      <defs><path id="rp" d="M 40 600 C 300 470, 560 520, 760 585 S 1000 610, 1080 560"/>
      <filter id="gr"><feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="1" seed="3"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -2.6 1.1"/><feComposite in2="SourceGraphic" operator="in"/><feBlend in="SourceGraphic" mode="screen"/></filter></defs>
      <text class="ribbon-text" font-size="${fs}" letter-spacing="-1" filter="url(#gr)"><textPath href="#rp" startOffset="${F.offset || 50}%" text-anchor="middle" dominant-baseline="central">${esc(text)}</textPath></text></svg>`;
    const holder = content(add(el("div", "abs", { left: 0, top: 0, width: "1920px", height: "1080px" }, svg)));
    const tEl = holder.querySelector("text");
    let f = fs; while (tEl.getComputedTextLength() > (F.maxlen || 960) && f > 60) { f -= 4; tEl.setAttribute("font-size", f); }
    if (!overlay && F.anchor_cutout !== false) img("anchor/anchor_cutout_right.png", 0, 0, 1920);
  };

  // Definition OST over anchor: coin pill with term + grey definition box + blue tab
  T.definition = function () {
    background("plate");
    decor("anchor");
    const y = F.y || 238;
    add(el("div", "deftab", { left: "-20px", top: (y + 162) + "px", width: "213px" }));
    pill({ text: F.term, icon: "coin", fontSize: F.term_font }, 20, y, { studioLayer: "term" });
    const d = el("div", "defbox", { left: "214px", top: (y + 160) + "px", whiteSpace: "nowrap" }, rich(F.text));
    add(content(d));
    let f = F.def_font || 35;
    d.style.fontSize = f + "px";
    while (d.offsetWidth > (F.maxw || 1100) && f > 24) { f -= 1; d.style.fontSize = f + "px"; }
  };

  // Plain anchor frame with free html (e.g. a number popup)
  T.anchor = function () {
    background("plate"); decor("anchor");
    if (F.pill) pill(F.pill, F.pill.x || 20, F.pill.y || 238, { studioLayer: "pill" });
    if (F.html) content(add(el("div", "abs", { left: 0, top: 0, width: "1920px", height: "1080px" }, F.html)));
  };

  // SOP / agenda tiles on the dark grid
  T.sop = function () {
    background("dark"); darkGrid(); decor("dark");
    const q = F.questions, n = q.length;
    const cols = n === 3 ? [0, 767, 1534] : n === 2 ? [384, 1150] : [0, 767, 1534].slice(0, n);
    const colors = F.colors || ["orange", "pink", "green"];
    q.forEach((text, i) => {
      const x = cols[i], dim = F.active && F.active !== i + 1;
      const t = el("div", "tile " + colors[i % 3] + (dim ? " dim" : ""), { left: x + "px", top: "308px" }, `<span class="n">${i + 1}</span>`);
      [[-13, -13], [373, -13], [-13, 373], [373, 373]].forEach(([a, b]) => t.appendChild(el("i", "h", { left: a + "px", top: b + "px" })));
      add(content(t));
      const below = i % 2 === 0;
      const b = el("div", "qbox" + (dim ? " dim" : ""), {}, rich(text));
      if (F.question_font) b.style.fontSize = F.question_font + "px";
      add(content(b));
      const w = b.offsetWidth, h = b.offsetHeight;
      let left = x + 193 - w / 2; left = Math.max(24, Math.min(1896 - w, left));
      if (n === 3 && i === 0) left = Math.max(24, x + 123);
      b.style.left = left + "px"; b.style.top = (below ? 722 : 272 - h) + "px";
      if (F.active === i + 1 && F.cursor !== false) img("ui/cursor_pixel_3d.png", Math.min(left + w - 60, 1780), below ? 800 : 230, 110);
    });
    if (!F.active && F.cursor !== false) img("ui/cursor_pixel_3d.png", 991, 800, 137);
  };

  // Tables (light FSS default; bg:"dark" for the reveal style)
  T.table = function () {
    const bgk = F.bg || "light";
    background(bgk);
    if (bgk === "light") {
      if (F.stairs !== false) stairs();
    }
    decor(bgk === "dark" ? "none" : "light-min");
    if (bgk === "dark") { diamond(230, 70, 26, "#6a64f0"); diamond(1610, 130, 20, "#f39a2b"); diamond(400, 1010, 20, "#8f8f8f"); diamond(1380, 1015, 30, "#f39a2b"); }
    if (F.pill) pill(Object.assign({ size: "sm" }, F.pill), "center", F.pill.y || 60, { studioLayer: "pill" });
    const box = F.box || {};
    const t = el("table", "tbl" + (F.center ? " center" : ""));
    const cols = F.columns, W = box.w || (cols.length <= 2 ? 1200 : cols.length === 3 ? 1640 : 1760);
    const rowHead = F.row_header !== undefined ? F.row_header : cols[0] === "";
    const cw = F.widths || cols.map(() => 1 / cols.length);
    let h = "<colgroup>" + cw.map(f => `<col style="width:${Math.round(f * W)}px">`).join("") + "</colgroup><tr>";
    const blurFrom = F.reveal_upto !== undefined ? F.reveal_upto : 99;
    cols.forEach((c, j) => h += `<th class="${j >= blurFrom ? "blur-cell" : ""}${c === "" ? " empty" : ""}"><span class="${j >= blurFrom ? "blur" : ""}">${rich(c)}</span></th>`);
    h += "</tr>";
    const tags = Object.assign({ "Active": "tag-active", "Passive FoF": "tag-passive", "Passive": "tag-passive", "FoF": "tag-fof" }, F.tags || {});
    F.rows.forEach((r, i) => {
      const rowHl = (F.highlight_rows || []).includes(i + 1);
      h += `<tr class="${rowHl ? "hl" : ""}">`;
      r.forEach((c, j) => {
        let cls = tags[c] || (String(c).startsWith("FoF") ? "tag-fof" : "");
        const cellHl = (F.highlight_cells || []).some(([a, b]) => a === i + 1 && b === j + 1) || (F.highlight_col === j + 1);
        h += `<td class="${cellHl ? "hl" : ""}${rowHead && j === 0 ? " rh" : ""}"><span class="${cls} ${j >= blurFrom ? "blur" : ""}">${rich(c)}</span></td>`;
      });
      h += "</tr>";
    });
    t.innerHTML = h;
    t.style.width = W + "px";
    if (F.font) { t.querySelectorAll("td").forEach(td => td.style.fontSize = F.font + "px"); }
    if (F.head_font) { t.querySelectorAll("th").forEach(td => td.style.fontSize = F.head_font + "px"); }
    if (F.row_h) { t.querySelectorAll("td").forEach(td => td.style.height = F.row_h + "px"); }
    if (F.head_h) { t.querySelectorAll("th").forEach(td => td.style.height = F.head_h + "px"); }
    add(content(t));
    const th = t.offsetHeight;
    t.style.left = (box.x !== undefined ? box.x : 960 - W / 2) + "px";
    t.style.top = (box.y !== undefined ? box.y : 540 - th / 2 + (F.pill ? 50 : 0)) + "px";
    if (F.reveal_upto !== undefined && F.marker !== false) {
      // yellow scrub marker on the reveal edge
      let x = parseFloat(t.style.left); for (let j = 0; j < blurFrom; j++) x += cw[j] * W;
      add(el("div", "marker", { left: (x - 5) + "px", top: (parseFloat(t.style.top) - 120) + "px", height: (th + 180) + "px" }));
    }
    if (F.caption) add(el("div", "caption", { left: t.style.left, top: (parseFloat(t.style.top) + th + 14) + "px" }, esc(F.caption)));
    cursor(F.cursor);
  };
  function stairs() {
    const g = (css, grad) => { const d = add(el("div", "abs decor", Object.assign({ background: grad }, css))); d.appendChild(el("div", "grain")); };
    g({ left: "982px", top: "0", width: "938px", height: "250px", clipPath: "polygon(0 8%,30% 8%,30% 0,100% 0,100% 100%,62% 100%,62% 70%,0 70%)" }, "linear-gradient(100deg,#2f86e0,#2a5fd0 60%,#2f86e0)");
    g({ left: "0", top: "700px", width: "430px", height: "380px", clipPath: "polygon(0 0,52% 0,52% 12%,70% 12%,70% 40%,100% 40%,100% 100%,0 100%)" }, "linear-gradient(160deg,#ef8a2a,#f0b23a)");
  }

  // Process cycle (e.g. You invest → You get units → Fund invests → You redeem)
  T.cycle = function () {
    background("dark"); darkGrid(); decor("dark-min");
    img("decor/star_blue.png", 145, 690, 107); img("decor/leaf_green.png", 30, 160, 82);
    if (F.pill) pill(Object.assign({ icon: "search", size: "lg" }, F.pill), "center", 104, { cx: 1150, studioLayer: "pill" });
    const steps = F.steps, n = steps.length, act = F.active || n;
    const cx = 1150, cy = 690, r = 220;
    const grads = ["url(#g1)", "url(#g2)", "url(#g3)", "url(#g4)"];
    let s = `<svg width="1920" height="1080" style="position:absolute;left:0;top:0"><defs>
      <linearGradient id="g1" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#e85a8c"/><stop offset="1" stop-color="#5a3fc8"/></linearGradient>
      <linearGradient id="g2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e05f2c"/><stop offset="1" stop-color="#eab43a"/></linearGradient>
      <linearGradient id="g3" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8fcb5a"/><stop offset="1" stop-color="#5e9e3a"/></linearGradient>
      <linearGradient id="g4" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5cc6ee"/><stop offset="1" stop-color="#2a4fc8"/></linearGradient></defs>
      <circle cx="${cx}" cy="${cy}" r="${r + 72}" fill="none" stroke="#e8e8e8" stroke-width="2.5"/>`;
    for (let i = 0; i < n; i++) {
      const a0 = -Math.PI / 2 - Math.PI / 2 + i * 2 * Math.PI / n, a1 = a0 + 2 * Math.PI / n;
      const p = (a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
      const [x0, y0] = p(a0), [x1, y1] = p(a1);
      const fill = i < act ? grads[i % 4] : "#f4f4f4";
      s += `<path d="M${cx},${cy} L${x0},${y0} A${r},${r} 0 0 1 ${x1},${y1} Z" fill="${fill}" stroke="#1b1b1b" stroke-width="2"/>`;
      const am = (a0 + a1) / 2, bx = cx + (r + 72) * Math.cos(am) * 0.93, by = cy + (r + 72) * Math.sin(am) * 0.93;
      if (i < act) s += `<circle cx="${bx}" cy="${by}" r="24" fill="#fff" stroke="#070708" stroke-width="3.5"/><text x="${bx}" y="${by + 11}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="30">${i + 1}</text>`;
    }
    s += "</svg>";
    content(add(el("div", "abs", { left: 0, top: 0 }, s)));
    const cells = n === 4 ? [[384, 310], [1535, 310], [1535, 694], [384, 694]] : [[384, 310], [1535, 310], [1535, 694], [384, 694], [0, 694], [0, 310]].slice(0, n);
    const col = ["pink", "orange", "green", "pink"];
    steps.forEach((st, i) => {
      if (i >= act) return;
      const [x, y] = cells[i];
      const t = el("div", "tile " + (st.color || col[i % 4]), { left: x + "px", top: y + "px", width: "383px", height: "383px" }, `<span class="lbl">${esc(st.label)}</span>` + (st.asset ? `<img class="art" src="${A + st.asset}">` : ""));
      [[-13, -13], [370, -13], [-13, 370], [370, 370]].forEach(([a, b]) => t.appendChild(el("i", "h", { left: a + "px", top: b + "px" })));
      add(content(t));
    });
    if (F.cursor !== false) img("ui/cursor_pixel_3d.png", 1190, 950, 100);
  };

  // Bulleted points (Key benefits / Key limitations / Things to remember)
  T.points = function () {
    const bgk = F.bg || "dark";
    background(bgk); if (bgk === "dark") darkGrid();
    decor(bgk === "dark" ? "dark" : "light-frames");
    pill({ text: F.title, icon: F.pill_icon || "coin" }, "center", F.title_y || 80, { studioLayer: "title" });
    const items = F.items, n = items.length;
    const twoCol = n > 4, perCol = twoCol ? Math.ceil(n / 2) : n;
    const colors = ["orange", "pink", "green"];
    const reveal = F.reveal || n;
    const colW = twoCol ? 790 : 1240, gapX = 70, gapY = twoCol ? 150 : 190;
    const x0 = twoCol ? (1920 - 2 * colW - gapX) / 2 : (1920 - colW) / 2;
    const top0 = F.top || (twoCol ? 300 : Math.round(330 + (690 - n * gapY) / 2));
    items.forEach((it, i) => {
      if (i >= reveal) return;
      const c = twoCol ? Math.floor(i / perCol) : 0, r = twoCol ? i % perCol : i;
      const x = x0 + c * (colW + gapX), y = top0 + r * gapY;
      const dim = F.active && F.active !== i + 1;
      const chip = el("div", "chip " + (bgk === "dark" ? "darkbg" : "lightbg") + (F.active === i + 1 ? " on" : "") + (dim ? " off" : ""), { left: x + "px", top: y + "px", width: colW + "px", whiteSpace: "normal", borderRadius: "28px" },
        `<span class="k" style="background-image:url(${A}ui/tile_${colors[i % 3]}.png)">${i + 1}</span><span>${rich(it)}</span>`);
      add(content(chip));
      if (!twoCol) { chip.style.fontSize = "54px"; chip.style.padding = "24px 40px 24px 24px"; chip.querySelector(".k").style.cssText += ";width:88px;height:88px;font-size:46px"; }
      let f = F.point_font || (twoCol ? 44 : 54);
      chip.style.fontSize = f + "px";
      while (chip.offsetHeight > gapY - 24 && f > 30) { f -= 2; chip.style.fontSize = f + "px"; }
    });
    cursor(F.cursor);
  };

  // Free-form: any bg + raw html using house classes
  T.html = function () {
    background(F.bg || "light"); if (F.bg === "dark") darkGrid();
    decor(F.decorset || (F.bg === "dark" ? "dark" : "light"));
    if (F.pill) pill(F.pill, F.pill.x !== undefined ? F.pill.x : "center", F.pill.y || 104, { studioLayer: "pill" });
    content(add(el("div", "abs", { left: 0, top: 0, width: "1920px", height: "1080px" }, F.html || "")));
    cursor(F.cursor); disclaimer();
  };

  function bindMfInline() {
    if (!O.studioEdit) return;
    function bindEl(el, path) {
      if (!el || el.dataset.inlineBound) return;
      el.dataset.inlineBound = "1";
      el.dataset.mfPath = path;
      el.classList.add("studio-inline-edit");
      el.contentEditable = "true";
      el.spellcheck = true;
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); el.blur(); }
      });
      el.addEventListener("blur", () => {
        const value = el.innerText.replace(/\u00a0/g, " ").trim();
        window.parent.postMessage({ studio: "inline", mfPath: path, value }, "*");
      });
    }
    const pillT = document.querySelector(".pill .t");
    if (F.pill && pillT) bindEl(pillT, F.type === "definition" ? "term" : (F.type === "points" ? "title" : "pill.text"));
    if (F.type === "definition") {
      const d = document.querySelector(".defbox");
      if (d) bindEl(d, "text");
    }
    document.querySelectorAll(".chip").forEach((chip, i) => {
      const span = chip.querySelector("span:last-child");
      if (span) bindEl(span, "items." + i);
    });
    document.querySelectorAll(".qbox").forEach((box, i) => bindEl(box, "questions." + i));
    document.querySelectorAll(".nlabel").forEach((nl, i) => {
      const span = nl.querySelector("span:last-child");
      if (span) bindEl(span, "labels.items." + i + ".text");
    });
    document.querySelectorAll(".tile .lbl").forEach((lbl, i) => {
      if (F.steps && F.steps[i]) bindEl(lbl, "steps." + i + ".label");
    });
    const cap = document.querySelector(".caption");
    if (F.caption && cap) bindEl(cap, "caption");
  }
  function mfResizeMode(type) {
    if (["pill", "definition", "label", "point", "tile"].includes(type)) return "font";
    if (type === "table") return "w";
    if (["hero", "prop", "card"].includes(type)) return "asset";
    return "";
  }
  function tagOne(el, type, label, mfDrag) {
    if (!el || el.dataset.mfTagged) return;
    el.dataset.mfTagged = "1";
    el.dataset.specIdx = String(window.__mfLayerSeq++);
    el.dataset.layerType = type;
    el.dataset.layerLabel = String(label || type).slice(0, 32);
    el.classList.add("studio-editable");
    const rm = mfResizeMode(type);
    if (rm) el.dataset.resize = rm;
    if (mfDrag) {
      el.dataset.mfDrag = mfDrag;
      el.dataset.mfPath = mfDrag;
    }
  }

  function tagMfStudioLayers() {
    if (!O.studioEdit && !O.tagLayers) return;
    window.__mfLayerSeq = 0;
    document.querySelectorAll("[data-spec-idx]").forEach((el) => {
      delete el.dataset.mfTagged;
      delete el.dataset.specIdx;
      delete el.dataset.mfPath;
      delete el.dataset.mfDrag;
      delete el.dataset.resize;
    });
    document.querySelectorAll(".pill[data-mf-studio-layer]").forEach((pillEl) => {
      const t = pillEl.querySelector(".t");
      const path = pillEl.dataset.mfStudioLayer;
      const label = (t && t.innerText) || path || "pill";
      tagOne(pillEl, "pill", label, path);
    });
    document.querySelectorAll(".defbox").forEach((el) => {
      tagOne(el, "definition", String(F.text || el.innerText || "").slice(0, 32), "text");
    });
    document.querySelectorAll("[data-mf-card]").forEach((el) => {
      const i = parseInt(el.dataset.mfCard, 10);
      const c = F.cards && F.cards[i];
      const lab = (c && (c.text || c.label || c.asset || "")).toString().split("/").pop();
      tagOne(el, "card", lab || "card " + (i + 1), "cards." + i);
    });
    document.querySelectorAll("[data-content][data-hero]").forEach((el) => {
      tagOne(el, "hero", String(F.hero && F.hero.asset || "hero").split("/").pop(), "hero");
    });
    document.querySelectorAll(".nlabel").forEach((el, i) => {
      const tx = (F.labels && F.labels.items && F.labels.items[i] && F.labels.items[i].text) || el.innerText || "";
      tagOne(el, "label", tx.slice(0, 32), "labels.items." + i);
    });
    document.querySelectorAll("img[data-mf-prop]").forEach((el) => {
      const i = parseInt(el.dataset.mfProp, 10);
      const p = F.props && F.props[i];
      tagOne(el, "prop", (p && p.asset || "prop").split("/").pop(), "props." + i);
    });
    document.querySelectorAll("table.tbl").forEach((el) => {
      tagOne(el, "table", F.caption || "table", "table");
    });
    document.querySelectorAll(".tile").forEach((el, i) => {
      const lbl = (el.querySelector(".lbl") || el.querySelector(".n") || el).innerText.slice(0, 28) || "tile " + (i + 1);
      let path = null;
      if (F.steps && F.steps[i]) path = "steps." + i + ".label";
      else if (F.questions && F.questions[i] != null) path = "questions." + i;
      tagOne(el, "tile", lbl, path);
    });
    document.querySelectorAll(".chip").forEach((el, i) => {
      const path = F.type === "points" && F.items ? "items." + i : null;
      tagOne(el, "point", el.innerText.slice(0, 36), path);
    });
    document.querySelectorAll(".qbox").forEach((el, i) => {
      tagOne(el, "label", el.innerText.slice(0, 36), "questions." + i);
    });
  }

  function notifyStudioLayers(pingParent) {
    tagMfStudioLayers();
    bindMfInline();
    if (
      pingParent !== false &&
      window.parent &&
      window.parent !== window &&
      !window.__mfLayersReadyPinged
    ) {
      window.__mfLayersReadyPinged = true;
      window.parent.postMessage({ studio: "layers-ready" }, "*");
    }
  }

  window.initMfInlineText = function () {
    notifyStudioLayers(false);
  };

  const fn = T[F.type];
  if (!fn) { document.body.innerHTML = `<h1 style="color:red">Unknown type ${F.type}</h1>`; window.RENDER_ERROR = "unknown type " + F.type; }
  else fn();
  if (O.studioEdit) notifyStudioLayers();
  else if (O.tagLayers) tagMfStudioLayers();

  // ---------- QA: report off-frame, clipped text, anchor-face overlap ----------
  window.QA = function () {
    const warns = [];
    const face = { l: 1330, t: 110, r: 1590, b: 480 };
    document.querySelectorAll("[data-content]").forEach(e => {
      const b = e.getBoundingClientRect();
      const name = (e.innerText || e.getAttribute("src") || e.className).slice(0, 40).replace(/\n/g, " ");
      if (!e.dataset.bleed && (b.left < -2 || b.top < -2 || b.right > 1922 || b.bottom > 1082)) warns.push(`off-frame: "${name}" [${b.left|0},${b.top|0},${b.right|0},${b.bottom|0}]`);
      if (isAnchor && F.type !== "ribbon" && b.right > face.l && b.left < face.r && b.bottom > face.t && b.top < face.b) warns.push(`covers anchor face: "${name}"`);
    });
    const cs = [...document.querySelectorAll("[data-content]")].filter(e => !e.dataset.hero && !e.dataset.bleed && e.offsetWidth < 1900);
    for (let i = 0; i < cs.length; i++) for (let j = i + 1; j < cs.length; j++) {
      const a = cs[i], b = cs[j];
      if (!isText(a) && !isText(b)) continue;
      if (a.contains(b) || b.contains(a)) continue;
      const r1 = a.getBoundingClientRect(), r2 = b.getBoundingClientRect();
      const ix = Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left), iy = Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top);
      if (ix > 6 && iy > 6) warns.push(`overlap: "${(a.innerText || a.className).slice(0, 25).replace(/\n/g, " ")}" x "${(b.innerText || b.getAttribute("src") || b.className).slice(0, 25).replace(/\n/g, " ")}"`);
    }
    document.querySelectorAll(".qbox,.defbox,.pill .t,.chip span,td,th").forEach(e => {
      if (e.scrollWidth > e.clientWidth + 2) warns.push(`text clipped: "${e.innerText.slice(0, 30)}"`);
    });
    if (window.RENDER_ERROR) warns.push(window.RENDER_ERROR);
    return warns;
  };
 }
})();
