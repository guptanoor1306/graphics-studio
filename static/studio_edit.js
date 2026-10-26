(function () {
  const overlay = document.createElement("div");
  overlay.id = "studio-overlay";
  overlay.setAttribute("aria-hidden", "true");
  document.body.appendChild(overlay);

  function send(action, idx, layerEl) {
    if (idx == null || Number.isNaN(idx)) return;
    const payload = { studio: "edit", action, idx };
    if (layerEl) {
      const mp = layerEl.dataset.mfPath || layerEl.dataset.mfDrag;
      if (mp) payload.mfPath = mp;
      if (layerEl.dataset.cardIdx != null) {
        payload.cardIdx = parseInt(layerEl.dataset.cardIdx, 10);
      }
    }
    window.parent.postMessage(payload, "*");
  }

  function chip(label, idx, layerEl) {
    const el = document.createElement("div");
    el.className = "studio-chip";
    el.innerHTML =
      '<span class="studio-chip-label">' +
      label +
      '</span><span class="studio-chip-actions">' +
      '<button type="button" data-act="edit" title="Edit">✎</button>' +
      '<button type="button" data-act="replace" title="Replace">↻</button>' +
      '<button type="button" data-act="delete" title="Remove">×</button></span>';
    el.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();
        send(btn.dataset.act, idx, layerEl);
      });
    });
    return el;
  }

  function labelFor(el, idx) {
    const t = el.dataset.layerType || el.getAttribute("data-layer-type") || "layer";
    const short = el.dataset.layerLabel || "";
    if (el.dataset.cardIdx != null) {
      return short ? t + " · " + short : t + " #" + (parseInt(el.dataset.cardIdx, 10) + 1);
    }
    return short ? t + " · " + short : t + " #" + (idx + 1);
  }

  function placeChips() {
    overlay.innerHTML = "";
    const layers = [...document.querySelectorAll("[data-spec-idx]")];
    if (!layers.length) {
      if (!(window.OPTS && window.OPTS.studioEdit && window.FRAME)) {
        const empty = document.createElement("div");
        empty.className = "studio-edit-empty";
        empty.textContent = "No tagged layers yet — wait a moment or use Layers on the right.";
        overlay.appendChild(empty);
      }
      emitLayerBoundsToParent();
      return;
    }
    layers.forEach((el) => {
      const idx = parseInt(el.dataset.specIdx, 10);
      const r = el.getBoundingClientRect();
      if (r.width < 2 && r.height < 2) return;
      const c = chip(labelFor(el, idx), idx, el);
      let top = r.top - 4;
      let left = r.left;
      if (top < 4) top = r.bottom + 4;
      if (left + 160 > window.innerWidth) left = window.innerWidth - 168;
      c.style.top = top + "px";
      c.style.left = Math.max(4, left) + "px";
      overlay.appendChild(c);
    });
    placeResizeHandles();
    emitLayerBoundsToParent();
  }

  function emitLayerBoundsToParent() {
    if (!window.parent || window.parent === window) return;
    const layers = [];
    document.querySelectorAll("[data-spec-idx]").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 2 && r.height < 2) return;
      layers.push({
        idx: parseInt(el.dataset.specIdx, 10),
        type: el.dataset.layerType || "",
        label: el.dataset.layerLabel || labelFor(el, parseInt(el.dataset.specIdx, 10)),
        mfPath: el.dataset.mfPath || el.dataset.mfDrag || null,
        cardIdx: el.dataset.cardIdx != null ? parseInt(el.dataset.cardIdx, 10) : null,
        top: r.top,
        left: r.left,
        width: r.width,
        height: r.height,
      });
    });
    window.parent.postMessage({ studio: "layer-bounds", layers }, "*");
  }

  function resizeMode(el) {
    if (!el) return "";
    if (el.dataset.resize) return el.dataset.resize;
    const t = el.dataset.layerType || "";
    if (t === "person") return "person";
    if (t === "asset") return "asset";
    return "";
  }

  function resizableLayer(el) {
    return !!resizeMode(el);
  }

  function widthBox(el) {
    return (
      el.querySelector(".glass, .card, .points, .nlist, .defcard, .def, .popup") || el
    );
  }

  function readTableFontSize(wrapper) {
    const table = wrapper.querySelector("table");
    if (!table) return null;
    return parseFloat(getComputedStyle(table).fontSize) || null;
  }

  function applyWidthResize(wrapper, newW, startW, startFs) {
    const min = 160;
    const max = 1700;
    newW = clamp(Math.round(newW), min, max);
    const box = widthBox(wrapper);
    box.style.width = newW + "px";
    box.style.maxWidth = newW + "px";
    const out = { w: newW };
    const table = wrapper.querySelector("table");
    if (table && startFs) {
      const fs = clamp(Math.round(startFs * (newW / Math.max(startW, 1))), 14, 42);
      table.style.fontSize = fs + "px";
      out.size = fs;
    }
    return out;
  }

  function fontBox(wrapper) {
    return (
      wrapper.querySelector(".htab, .callout, .num, .pill-title, .result-pill") ||
      wrapper.querySelector("[style*='font-size']") ||
      wrapper.firstElementChild ||
      wrapper
    );
  }

  function readFontSize(wrapper) {
    const el = fontBox(wrapper);
    return parseFloat(getComputedStyle(el).fontSize) || 34;
  }

  function applyFontResize(wrapper, newFs) {
    newFs = clamp(Math.round(newFs), 16, 96);
    const el = fontBox(wrapper);
    el.style.fontSize = newFs + "px";
    if (wrapper.dataset.layerType === "text" || wrapper.dataset.layerType === "label") {
      const inner = wrapper.querySelector("[style*='font-size']");
      if (inner) inner.style.fontSize = newFs + "px";
    }
    return newFs;
  }

  function applyBarsResize(wrapper, w, h) {
    w = clamp(Math.round(w), 400, 1700);
    h = clamp(Math.round(h), 280, 900);
    const svg = wrapper.querySelector("svg");
    if (svg) {
      svg.setAttribute("width", String(w));
      svg.setAttribute("height", String(h));
    }
    const card = wrapper.querySelector(".chartcard");
    if (card) card.style.width = w + "px";
    return { w, h };
  }

  function placeResizeHandles() {
    [...overlay.querySelectorAll(".studio-resize-handle")].forEach((h) => h.remove());
    document.querySelectorAll("[data-spec-idx].studio-editable, [data-mf-drag].studio-editable").forEach((el) => {
      if (!resizableLayer(el)) return;
      const r = el.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) return;
      const h = document.createElement("div");
      h.className = "studio-resize-handle";
      h.dataset.specIdx = el.dataset.specIdx;
      if (el.dataset.cardIdx != null) h.dataset.cardIdx = el.dataset.cardIdx;
      h.style.left = r.right + "px";
      h.style.top = r.bottom + "px";
      h.title = "Drag to resize";
      overlay.appendChild(h);
    });
  }

  function clamp(n, lo, hi) {
    return Math.max(lo, Math.min(hi, n));
  }

  /** asset/person + any absolutely positioned spec layer (html, htab, etc.) */
  function canDrag(el) {
    if (!el || !el.classList.contains("studio-editable")) return false;
    if (el.dataset.specIdx == null) return false;
    const t = el.dataset.layerType || "";
    if (t === "asset" || t === "person" || t === "card") return true;
    if (el.dataset.mfDrag) return true;
    if (el.dataset.mfProp != null) return true;
    const pos = getComputedStyle(el).position;
    if (pos !== "absolute" && pos !== "fixed") return false;
    if (el.closest(".flow")) return false;
    return true;
  }

  function readPos(el) {
    const left = parseFloat(el.style.left);
    const top = parseFloat(el.style.top);
    if (!Number.isNaN(left) && !Number.isNaN(top)) return { x: left, y: top };
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top };
  }

  function initDrag() {
    let drag = null;

    document.addEventListener(
      "pointerdown",
      (e) => {
        if (e.button !== 0) return;
        const el = e.target.closest("[data-spec-idx].studio-editable");
        if (!el || e.target.closest(".studio-chip")) return;
        if (e.target.closest('[contenteditable="true"]')) return;
        if (!canDrag(el)) return;
        e.preventDefault();
        const pos = readPos(el);
        drag = {
          el,
          idx: parseInt(el.dataset.specIdx, 10),
          pointerId: e.pointerId,
          offX: e.clientX - pos.x,
          offY: e.clientY - pos.y,
        };
        el.classList.add("studio-dragging");
        el.setPointerCapture(e.pointerId);
      },
      true
    );

    document.addEventListener("pointermove", (e) => {
      if (!drag || e.pointerId !== drag.pointerId) return;
      const w = elDim().w;
      const h = elDim().h;
      const ew = drag.el.offsetWidth || 80;
      const eh = drag.el.offsetHeight || 80;
      const x = clamp(Math.round(e.clientX - drag.offX), 0, w - ew);
      const y = clamp(Math.round(e.clientY - drag.offY), 0, h - eh);
      drag.el.style.position = "absolute";
      drag.el.style.left = x + "px";
      drag.el.style.top = y + "px";
    });

    function finishDrag(e) {
      if (!drag || (e.pointerId != null && e.pointerId !== drag.pointerId)) return;
      const el = drag.el;
      const idx = drag.idx;
      const x = parseInt(el.style.left, 10) || 0;
      const y = parseInt(el.style.top, 10) || 0;
      el.classList.remove("studio-dragging");
      try {
        el.releasePointerCapture(drag.pointerId);
      } catch (_) {}
      drag = null;
      const payload = { studio: "move", idx, x, y };
      if (el.dataset.cardIdx != null) payload.cardIdx = parseInt(el.dataset.cardIdx, 10);
      if (el.dataset.mfDrag) payload.mfPath = el.dataset.mfDrag;
      window.parent.postMessage(payload, "*");
      placeChips();
    }

    document.addEventListener("pointerup", finishDrag);
    document.addEventListener("pointercancel", finishDrag);
  }

  function applyAssetSize(el, w) {
    const img = el.tagName === "IMG" ? el : el.querySelector("img");
    const node = img || el;
    const min = 48;
    const max = 1600;
    w = clamp(Math.round(w), min, max);
    node.style.width = w + "px";
    node.style.height = "auto";
    return w;
  }

  function applyPersonSize(el, h) {
    const min = 120;
    const max = 720;
    h = clamp(Math.round(h), min, max);
    const s = h / 400;
    el.style.width = Math.round(200 * s) + "px";
    el.style.height = h + "px";
    const svg = el.querySelector("svg");
    if (svg) {
      svg.setAttribute("width", String(200 * s));
      svg.setAttribute("height", String(h));
    }
    return h;
  }

  function initResize() {
    let resize = null;

    overlay.addEventListener(
      "pointerdown",
      (e) => {
        const handle = e.target.closest(".studio-resize-handle");
        if (!handle) return;
        e.preventDefault();
        e.stopPropagation();
        const idx = parseInt(handle.dataset.specIdx, 10);
        let el = null;
        if (handle.dataset.cardIdx !== undefined && handle.dataset.cardIdx !== "") {
          el = document.querySelector(
            `[data-spec-idx="${idx}"][data-card-idx="${handle.dataset.cardIdx}"]`
          );
        }
        if (!el) el = document.querySelector(`[data-spec-idx="${idx}"].studio-editable`);
        if (!el || !resizableLayer(el)) return;
        const mode = resizeMode(el);
        const box = widthBox(el);
        resize = {
          el,
          handle,
          idx,
          mode,
          pointerId: e.pointerId,
          startX: e.clientX,
          startY: e.clientY,
          startW: box.offsetWidth || el.offsetWidth,
          startH: (() => {
            if (mode !== "wh") return el.offsetHeight;
            const svg = el.querySelector("svg");
            const ah = svg && svg.getAttribute("height");
            return ah ? parseFloat(ah) : el.offsetHeight;
          })(),
          startFs: mode === "font" ? readFontSize(el) : readTableFontSize(el),
          last: {},
        };
        el.classList.add("studio-resizing");
        handle.setPointerCapture(e.pointerId);
      },
      true
    );

    document.addEventListener("pointermove", (e) => {
      if (!resize || e.pointerId !== resize.pointerId) return;
      const dx = e.clientX - resize.startX;
      const dy = e.clientY - resize.startY;
      const mode = resize.mode;
      if (mode === "person") {
        applyPersonSize(resize.el, resize.startH + dy);
      } else if (mode === "asset") {
        const ar = resize.startW / Math.max(resize.startH, 1);
        const dw = Math.abs(dx) >= Math.abs(dy) ? dx : dy * ar;
        const w = applyAssetSize(resize.el, resize.startW + dw);
        resize.last = { w };
      } else if (mode === "w") {
        const dw = Math.abs(dx) >= Math.abs(dy) ? dx : dy;
        resize.last = applyWidthResize(
          resize.el,
          resize.startW + dw,
          resize.startW,
          resize.startFs
        );
      } else if (mode === "font") {
        const delta = (dx + dy) * 0.35;
        const fs = applyFontResize(resize.el, resize.startFs + delta);
        resize.last = { size: fs };
      } else if (mode === "wh") {
        resize.last = applyBarsResize(
          resize.el,
          resize.startW + dx,
          resize.startH + dy
        );
      }
      placeResizeHandles();
    });

    function finishResize(e) {
      if (!resize || (e.pointerId != null && e.pointerId !== resize.pointerId)) return;
      const { el, idx, mode, last } = resize;
      el.classList.remove("studio-resizing");
      try {
        resize.handle.releasePointerCapture(resize.pointerId);
      } catch (_) {}
      const payload = { studio: "resize", idx };
      if (mode === "person") payload.h = el.offsetHeight;
      else if (mode === "asset") {
        const img = el.tagName === "IMG" ? el : el.querySelector("img");
        payload.w =
          last.w ||
          Math.round(parseFloat((img || el).style.width) || el.offsetWidth);
      } else if (mode === "w" || mode === "wh") {
        if (last.w != null) payload.w = last.w;
        if (last.h != null) payload.h = last.h;
        if (last.size != null) payload.size = last.size;
      } else if (mode === "font") {
        payload.size = last.size != null ? last.size : readFontSize(el);
      }
      if (el.dataset.cardIdx != null) payload.cardIdx = parseInt(el.dataset.cardIdx, 10);
      resize = null;
      window.parent.postMessage(payload, "*");
      placeChips();
    }

    document.addEventListener("pointerup", finishResize);
    document.addEventListener("pointercancel", finishResize);
  }

  function elDim() {
    return { w: document.documentElement.clientWidth || 1920, h: document.documentElement.clientHeight || 1080 };
  }

  const INLINE_SELECTORS = {
    htab: ".htab",
    text: ".studio-editable",
    label: ".studio-editable",
    pill: ".pill-title",
    num: ".num",
    callout: ".callout",
    result_pill: ".result-pill",
  };

  function inlineTarget(wrap) {
    const type = wrap.dataset.layerType || "";
    const sel = INLINE_SELECTORS[type];
    if (!sel) return null;
    const el = wrap.matches(sel) ? wrap : wrap.querySelector(sel);
    return el || null;
  }

  function initInlineText() {
    document.querySelectorAll("[data-spec-idx][data-inline-field]").forEach((wrap) => {
      const field = wrap.dataset.inlineField;
      const idx = wrap.dataset.specIdx;
      if (field == null || idx == null) return;
      const el = inlineTarget(wrap) || wrap;
      if (el.dataset.inlineBound) return;
      el.dataset.inlineBound = "1";
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
        window.parent.postMessage(
          { studio: "inline", idx: parseInt(idx, 10), field, value },
          "*"
        );
      });
    });
    if (window.OPTS && window.OPTS.studioEdit && typeof window.initMfInlineText === "function") {
      window.initMfInlineText();
    }
  }

  function bootLayers() {
    initInlineText();
    placeChips();
  }

  window.studioBootLayers = bootLayers;

  function waitForMfRender(tries) {
    if (window.RENDERED) {
      bootLayers();
      return;
    }
    if (tries <= 0) {
      setTimeout(() => waitForMfRender(40), 120);
      return;
    }
    setTimeout(() => waitForMfRender(tries - 1), 80);
  }

  function boot() {
    initDrag();
    initResize();
    window.addEventListener("resize", placeChips);
    window.addEventListener("scroll", placeChips, true);
    if (window.OPTS && window.OPTS.studioEdit && typeof window.FRAME !== "undefined") {
      waitForMfRender(100);
    } else {
      bootLayers();
      setTimeout(bootLayers, 400);
      setTimeout(bootLayers, 1200);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
