// Zerodha Online Product IP — studio renderer (Python builds #stage HTML; this fits + tags layers like MF render.js)
(function () {
  const F = window.FRAME || {};
  const O = window.OPTS || {};
  const stage = document.getElementById("stage");

  function fitBoxes() {
    stage?.querySelectorAll(".fitbox").forEach((b) => {
      const w = b.parentElement;
      if (!w) return;
      const mx = parseFloat(b.dataset.max || "1");
      const anchor = stage && !stage.classList.contains("fss");
      const minS = anchor ? 0.42 : 0.55;
      const s = Math.max(
        minS,
        Math.min(
          (w.clientWidth * 0.94) / b.offsetWidth,
          (w.clientHeight * 0.94) / b.offsetHeight,
          mx
        )
      );
      if (Math.abs(s - 1) > 0.02) b.style.transform = `scale(${s.toFixed(3)})`;
      b.dataset.scale = s.toFixed(3);
    });
  }

  function itemLabel(it) {
    if (!it || typeof it !== "object") return "layer";
    const t = it.t || "layer";
    for (const k of ["text", "title", "label", "value", "name"]) {
      if (it[k]) return t + " · " + String(it[k]).slice(0, 32);
    }
    return t;
  }

  function zoResizeMode(t) {
    if (["chart", "kite_chart", "kite_watchlist", "kite_depth", "img", "bars", "auction"].includes(t)) {
      return "wh";
    }
    if (["heading", "text", "note"].includes(t)) return "font";
    return "w";
  }

  function tagOne(el, type, label, mfPath) {
    if (!el || el.dataset.mfTagged) return;
    el.dataset.mfTagged = "1";
    el.dataset.specIdx = String(window.__zoLayerSeq++);
    el.dataset.layerType = type;
    el.dataset.layerLabel = String(label || type).slice(0, 32);
    el.classList.add("studio-editable");
    const rm = zoResizeMode(type);
    if (rm) el.dataset.resize = rm;
    if (mfPath) {
      el.dataset.mfDrag = mfPath;
      el.dataset.mfPath = mfPath;
    }
  }

  function itemPlaced(it) {
    return !!(it && (it.abs || it._abs));
  }

  function applyItemScale(el, it) {
    if (!el || !it || it.scale == null) return;
    const s = parseFloat(it.scale);
    if (Number.isNaN(s) || Math.abs(s - 1) <= 0.02) return;
    el.style.transform = `scale(${s.toFixed(3)})`;
    el.style.transformOrigin = "center center";
  }

  function applyItemGeometry(el, it) {
    if (!el || !it) return;
    if (itemPlaced(it) && (it.x != null || it.y != null)) {
      el.style.position = "absolute";
      if (it.x != null) el.style.left = Math.round(it.x) + "px";
      if (it.y != null) el.style.top = Math.round(it.y) + "px";
      el.style.zIndex = "5";
    }
    if (it.w != null && el.dataset.resize === "w") el.style.width = Math.round(it.w) + "px";
    applyItemScale(el, it);
  }

  function tagZoLayers() {
    if (!O.studioEdit && !O.tagLayers) return;
    window.__zoLayerSeq = 0;
    document.querySelectorAll("[data-zo-item]").forEach((el) => {
      delete el.dataset.mfTagged;
      delete el.dataset.specIdx;
      delete el.dataset.mfPath;
      delete el.dataset.mfDrag;
      delete el.dataset.resize;
      el.classList.remove("studio-editable");
    });
    document.querySelectorAll("[data-zo-item]").forEach((el) => {
      const i = parseInt(el.dataset.zoItem, 10);
      const it = F.items && F.items[i];
      if (!it) return;
      applyItemGeometry(el, it);
      tagOne(el, it.t || "layer", itemLabel(it), "items." + i);
    });
  }

  function bindEl(el, path) {
    if (!el || el.dataset.inlineBound) return;
    el.dataset.inlineBound = "1";
    el.dataset.mfPath = path;
    el.classList.add("studio-inline-edit");
    el.contentEditable = "true";
    el.spellcheck = true;
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        el.blur();
      }
    });
    el.addEventListener("blur", () => {
      const value = el.innerText.replace(/\u00a0/g, " ").trim();
      window.parent.postMessage({ studio: "inline", mfPath: path, value }, "*");
    });
  }

  function bindZoInline() {
    if (!O.studioEdit) return;
    (F.items || []).forEach((it, i) => {
      if (!it || typeof it !== "object") return;
      const base = "items." + i;
      const wrap = document.querySelector('[data-zo-item="' + i + '"]');
      if (!wrap) return;
      if (it.t === "heading") {
        const t = wrap.querySelector(".heading") || wrap.querySelector(".ihead b");
        if (t) bindEl(t, base + ".text");
        const sub = wrap.querySelector(".subhead");
        if (sub && it.sub) bindEl(sub, base + ".sub");
      } else if (it.t === "text" || it.t === "note") {
        bindEl(wrap.querySelector(".note .box") || wrap, base + ".text");
      } else if (it.t === "status" && it.title) {
        const t = wrap.querySelector(".status .title, .status-h");
        if (t) bindEl(t, base + ".title");
      } else if (it.t === "pillv") {
        const t = wrap.querySelector(".pillv");
        if (t) bindEl(t, base + ".text");
      } else if (it.t === "formula") {
        const d = wrap.querySelector(".fdef");
        if (d && it.definition) bindEl(d, base + ".definition");
      }
    });
  }

  function notifyStudioLayers() {
    tagZoLayers();
    bindZoInline();
    if (
      window.parent &&
      window.parent !== window &&
      !window.__zoLayersReadyPinged
    ) {
      window.__zoLayersReadyPinged = true;
      window.parent.postMessage({ studio: "layers-ready" }, "*");
    }
  }

  window.bindMfStudioInline = bindZoInline;
  window.initMfInlineText = bindZoInline;

  function run() {
    try {
      fitBoxes();
    } catch (e) {
      window.RENDER_ERROR = String(e.message || e);
    }
    window.RENDERED = true;
    tagZoLayers();
    bindZoInline();
    if (O.studioEdit) {
      if (typeof window.studioBootLayers === "function") window.studioBootLayers();
      notifyStudioLayers();
    } else if (O.tagLayers) tagZoLayers();
  }

  window.QA = function () {
    if (typeof window.__ZO_CHECK === "function") return window.__ZO_CHECK();
    return window.RENDER_ERROR ? [window.RENDER_ERROR] : [];
  };

  const fontsReady = document.fonts
    ? Promise.all(
        ["400", "500", "600", "700"].map((w) =>
          document.fonts.load(w + " 16px Inter").catch(() => {})
        )
      )
    : Promise.resolve();
  fontsReady.then(run);
})();
