(function () {
  const useParentChrome = document.body.classList.contains("in-studio-iframe");
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
    if (window.StudioLayerRegistry) {
      return window.StudioLayerRegistry.layerLabel(el, idx);
    }
    const t = el.dataset.layerType || el.getAttribute("data-layer-type") || "layer";
    const short = el.dataset.layerLabel || "";
    if (el.dataset.cardIdx != null) {
      return short ? t + " · " + short : t + " #" + (parseInt(el.dataset.cardIdx, 10) + 1);
    }
    return short ? t + " · " + short : t + " #" + (idx + 1);
  }

  function registryLayers() {
    if (window.StudioLayerRegistry) {
      return window.StudioLayerRegistry.layersFromDocument();
    }
    return [...document.querySelectorAll("[data-spec-idx]")]
      .map((el) => {
        const r = el.getBoundingClientRect();
        const idx = parseInt(el.dataset.specIdx, 10);
        return {
          el,
          idx,
          type: el.dataset.layerType || "",
          label: labelFor(el, idx),
          mfPath: el.dataset.mfPath || el.dataset.mfDrag || null,
          cardIdx: el.dataset.cardIdx != null ? parseInt(el.dataset.cardIdx, 10) : null,
          top: r.top,
          left: r.left,
          width: r.width,
          height: r.height,
        };
      })
      .filter((L) => L.width >= 2 && L.height >= 2);
  }

  let chipRaf = 0;
  function schedulePlaceChips() {
    if (chipRaf) return;
    chipRaf = requestAnimationFrame(() => {
      chipRaf = 0;
      placeChips();
    });
  }

  function placeChips() {
    overlay.innerHTML = "";
    const layers = registryLayers();
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
    if (!useParentChrome) {
      layers.forEach((L) => {
        const el = L.el;
        const idx = L.idx;
        const c = chip(L.label || labelFor(el, idx), idx, el);
        let top = L.top - 4;
        let left = L.left;
        if (top < 4) top = L.top + L.height + 4;
        if (left + 160 > window.innerWidth) left = window.innerWidth - 168;
        c.style.top = top + "px";
        c.style.left = Math.max(4, left) + "px";
        overlay.appendChild(c);
      });
    }
    if (!useParentChrome) placeResizeHandles();
    emitLayerBoundsToParent();
  }

  let lastBoundsSig = "";
  function emitLayerBoundsToParent() {
    if (!window.parent || window.parent === window) return;
    if (document.querySelector(".studio-dragging, .studio-resizing")) return;
    const layers = registryLayers().map((L) => ({
      idx: L.idx,
      type: L.type,
      label: L.label,
      mfPath: L.mfPath,
      cardIdx: L.cardIdx,
      resize: resizeMode(L.el),
      top: Math.round(L.top),
      left: Math.round(L.left),
      width: Math.round(L.width),
      height: Math.round(L.height),
    }));
    const sig = JSON.stringify(layers);
    if (sig === lastBoundsSig) return;
    lastBoundsSig = sig;
    window.parent.postMessage({ studio: "layer-bounds", layers }, "*");
  }

  const LAYER_RESIZE = {
    pill: "font",
    definition: "font",
    label: "font",
    point: "font",
    tile: "font",
    text: "font",
    callout: "font",
    num: "font",
    result_pill: "font",
    htab: "font",
    table: "w",
    hero: "asset",
    prop: "asset",
    card: "asset",
    person: "person",
    asset: "asset",
    glass_table: "w",
    calc_table: "w",
    nlist: "w",
    points: "w",
    defcard: "w",
    popup: "w",
    bars: "wh",
  };

  function resizeMode(el) {
    if (!el) return "";
    if (el.dataset.resize) return el.dataset.resize;
    const t = el.dataset.layerType || "";
    return LAYER_RESIZE[t] || "";
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
      wrapper.querySelector(
        ".htab, .callout, .num, .pill-title, .result-pill, .pill .t, .defbox, .nlabel, .qbox, .tile .lbl, .caption"
      ) ||
      wrapper.querySelector(".chip span:last-child") ||
      wrapper.querySelector("[style*='font-size']") ||
      (wrapper.classList && wrapper.classList.contains("chip") ? wrapper : null) ||
      wrapper.firstElementChild ||
      wrapper
    );
  }

  function readFontSize(wrapper) {
    const el = fontBox(wrapper);
    return parseFloat(getComputedStyle(el).fontSize) || 34;
  }

  function applyFontResize(wrapper, newFs) {
    newFs = clamp(Math.round(newFs), 14, 96);
    const el = fontBox(wrapper);
    el.style.fontSize = newFs + "px";
    const lt = wrapper.dataset.layerType || "";
    if (lt === "text" || lt === "label" || lt === "point") {
      const inner = wrapper.querySelector("[style*='font-size']");
      if (inner && inner !== el) inner.style.fontSize = newFs + "px";
    }
    if (lt === "point" && wrapper.classList.contains("chip")) {
      wrapper.style.fontSize = newFs + "px";
    }
    return newFs;
  }

  function postResize(el, idx, fields) {
    const payload = Object.assign({ studio: "resize", idx }, fields);
    const mp = el.dataset.mfPath || el.dataset.mfDrag;
    if (mp) payload.mfPath = mp;
    if (el.dataset.cardIdx != null) payload.cardIdx = parseInt(el.dataset.cardIdx, 10);
    window.parent.postMessage(payload, "*");
    schedulePlaceChips();
  }

  function beginResizeSession(el) {
    const mode = resizeMode(el);
    const box = widthBox(el);
    return {
      el,
      mode,
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
  }

  function applyResizeDelta(session, dx, dy) {
    session.accDx = (session.accDx || 0) + dx;
    session.accDy = (session.accDy || 0) + dy;
    const adx = session.accDx;
    const ady = session.accDy;
    const { el, mode } = session;
    if (mode === "person") {
      session.last = { h: applyPersonSize(el, session.startH + ady) };
    } else if (mode === "asset") {
      const ar = session.startW / Math.max(session.startH, 1);
      const dw = Math.abs(adx) >= Math.abs(ady) ? adx : ady * ar;
      session.last = { w: applyAssetSize(el, session.startW + dw) };
    } else if (mode === "w") {
      const dw = Math.abs(adx) >= Math.abs(ady) ? adx : ady;
      session.last = applyWidthResize(el, session.startW + dw, session.startW, session.startFs);
    } else if (mode === "font") {
      session.last = { size: applyFontResize(el, session.startFs + (adx + ady) * 0.35) };
    } else if (mode === "wh") {
      session.last = applyBarsResize(el, session.startW + adx, session.startH + ady);
    }
    return session.last;
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
    if (useParentChrome) return;
    [...overlay.querySelectorAll(".studio-resize-handle")].forEach((h) => h.remove());
    const sel = window.__studioSelected;
    document.querySelectorAll("[data-spec-idx].studio-editable, [data-mf-drag].studio-editable").forEach((el) => {
      if (!resizableLayer(el)) return;
      if (sel) {
        const idx = parseInt(el.dataset.specIdx, 10);
        const mp = el.dataset.mfPath || el.dataset.mfDrag || null;
        if (idx !== sel.idx || (mp || null) !== (sel.mfPath || null)) return;
      }
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

  function canDrag(el) {
    if (!el || !el.classList.contains("studio-editable")) return false;
    if (el.dataset.specIdx == null) return false;
    if (el.dataset.mfPath || el.dataset.mfDrag) return true;
    const t = el.dataset.layerType || "";
    if (["asset", "person", "card", "pill", "hero", "label", "prop", "table", "definition", "point"].includes(t)) {
      return true;
    }
    if (el.dataset.mfProp != null) return true;
    const pos = getComputedStyle(el).position;
    if (pos === "absolute" || pos === "fixed") return true;
    if (el.closest(".flow")) return false;
    return false;
  }

  function readPos(el) {
    const left = parseFloat(el.style.left);
    const top = parseFloat(el.style.top);
    if (!Number.isNaN(left) && !Number.isNaN(top)) return { x: left, y: top };
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top };
  }

  const STAGE_BOUNDS = { left: 0, top: 0, right: 1920, bottom: 1080 };
  let interactTargets = [];
  let pointerDragBound = false;

  function postMove(el, idx) {
    const x = parseInt(el.style.left, 10) || 0;
    const y = parseInt(el.style.top, 10) || 0;
    const payload = { studio: "move", idx, x, y };
    if (el.dataset.cardIdx != null) payload.cardIdx = parseInt(el.dataset.cardIdx, 10);
    const mp = el.dataset.mfPath || el.dataset.mfDrag;
    if (mp) payload.mfPath = mp;
    window.parent.postMessage(payload, "*");
    schedulePlaceChips();
  }

  function ensureAbsolute(el) {
    const pos = getComputedStyle(el).position;
    if (pos !== "absolute" && pos !== "fixed") {
      const r = el.getBoundingClientRect();
      el.style.position = "absolute";
      el.style.left = Math.round(r.left) + "px";
      el.style.top = Math.round(r.top) + "px";
    }
  }

  function stageRestriction() {
    return document.getElementById("stage") || document.body;
  }

  function initInteractDrag() {
    initPointerDrag();
    if (typeof interact === "undefined") return;
    interactTargets.forEach((t) => {
      try {
        t.unset();
      } catch (_) {}
    });
    interactTargets = [];
    const restrict =
      interact.modifiers && interact.modifiers.restrictRect
        ? [
            interact.modifiers.restrictRect({
              restriction: stageRestriction(),
              endOnly: true,
            }),
          ]
        : [];
    document.querySelectorAll("[data-spec-idx].studio-editable").forEach((el) => {
      if (!canDrag(el)) return;
      ensureAbsolute(el);
      const idx = parseInt(el.dataset.specIdx, 10);
      try {
        const draggable = interact(el).draggable({
          hold: 110,
          ignoreFrom: ".studio-chip, .studio-chip-actions, button",
          modifiers: restrict,
          listeners: {
            start() {
              el.classList.add("studio-dragging");
            },
            move(event) {
              const x =
                (parseFloat(el.getAttribute("data-x")) || parseFloat(el.style.left) || 0) + event.dx;
              const y =
                (parseFloat(el.getAttribute("data-y")) || parseFloat(el.style.top) || 0) + event.dy;
              el.style.left = Math.round(x) + "px";
              el.style.top = Math.round(y) + "px";
              el.setAttribute("data-x", String(Math.round(x)));
              el.setAttribute("data-y", String(Math.round(y)));
              schedulePlaceChips();
            },
            end() {
              el.classList.remove("studio-dragging");
              postMove(el, idx);
            },
          },
        });
        interactTargets.push(draggable);
      } catch (_) {
        /* pointer drag remains active */
      }
    });
  }

  function initPointerDrag() {
    if (pointerDragBound) return;
    pointerDragBound = true;
    let drag = null;
    let pending = null;
    let layerTap = null;
    const DRAG_PX = 6;

    document.addEventListener(
      "pointerdown",
      (e) => {
        if (e.button !== 0) return;
        if (e.target.closest(".studio-chip, button")) return;
        const el = e.target.closest("[data-spec-idx].studio-editable");
        if (!el || !canDrag(el)) return;
        ensureAbsolute(el);
        const pos = readPos(el);
        const idx = parseInt(el.dataset.specIdx, 10);
        layerTap = {
          el,
          idx,
          mfPath: el.dataset.mfPath || el.dataset.mfDrag || null,
          pointerId: e.pointerId,
          startX: e.clientX,
          startY: e.clientY,
        };
        pending = {
          el,
          idx,
          pointerId: e.pointerId,
          startX: e.clientX,
          startY: e.clientY,
          offX: e.clientX - pos.x,
          offY: e.clientY - pos.y,
        };
      },
      true
    );

    document.addEventListener("pointermove", (e) => {
      if (pending && !drag && e.pointerId === pending.pointerId) {
        const dx = e.clientX - pending.startX;
        const dy = e.clientY - pending.startY;
        if (Math.hypot(dx, dy) < DRAG_PX) return;
        drag = pending;
        pending = null;
        drag.el.classList.add("studio-dragging");
        try {
          drag.el.setPointerCapture(e.pointerId);
        } catch (_) {}
        e.preventDefault();
      }
      if (!drag || e.pointerId !== drag.pointerId) return;
      e.preventDefault();
      const w = elDim().w;
      const h = elDim().h;
      const ew = drag.el.offsetWidth || 80;
      const eh = drag.el.offsetHeight || 80;
      const x = clamp(Math.round(e.clientX - drag.offX), 0, w - ew);
      const y = clamp(Math.round(e.clientY - drag.offY), 0, h - eh);
      drag.el.style.position = "absolute";
      drag.el.style.left = x + "px";
      drag.el.style.top = y + "px";
      drag.el.setAttribute("data-x", String(x));
      drag.el.setAttribute("data-y", String(y));
      schedulePlaceChips();
    });

    function finishDrag(e) {
      if (layerTap && e.pointerId === layerTap.pointerId) {
        const dx = e.clientX - layerTap.startX;
        const dy = e.clientY - layerTap.startY;
        const tapped = !drag && Math.hypot(dx, dy) < DRAG_PX;
        if (tapped && window.parent && window.parent !== window) {
          window.parent.postMessage(
            {
              studio: "select-layer",
              idx: layerTap.idx,
              mfPath: layerTap.mfPath,
            },
            "*"
          );
        }
        layerTap = null;
      }
      if (pending && e.pointerId === pending.pointerId) {
        pending = null;
        return;
      }
      if (!drag || (e.pointerId != null && e.pointerId !== drag.pointerId)) return;
      const el = drag.el;
      const idx = drag.idx;
      el.classList.remove("studio-dragging");
      try {
        el.releasePointerCapture(drag.pointerId);
      } catch (_) {}
      drag = null;
      postMove(el, idx);
      lastBoundsSig = "";
      emitLayerBoundsToParent();
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
      const fields = {};
      if (mode === "person") fields.h = el.offsetHeight;
      else if (mode === "asset") {
        const img = el.tagName === "IMG" ? el : el.querySelector("img");
        fields.w =
          last.w ||
          Math.round(parseFloat((img || el).style.width) || el.offsetWidth);
      } else if (mode === "w" || mode === "wh") {
        if (last.w != null) fields.w = last.w;
        if (last.h != null) fields.h = last.h;
        if (last.size != null) fields.size = last.size;
      } else if (mode === "font") {
        fields.size = last.size != null ? last.size : readFontSize(el);
      }
      resize = null;
      postResize(el, idx, fields);
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
    if (window.OPTS && window.OPTS.studioEdit && typeof window.bindMfStudioInline === "function") {
      window.bindMfStudioInline();
    }
  }

  function initInlineTextOnce() {
    if (window.__studioInlineInit) return;
    window.__studioInlineInit = true;
    initInlineText();
  }

  function bootLayers() {
    lastBoundsSig = "";
    initInlineTextOnce();
    initInteractDrag();
    placeChips();
  }

  function bootLayersDelayed() {
    bootLayers();
    setTimeout(bootLayers, 400);
    setTimeout(bootLayers, 1200);
  }

  window.studioBootLayers = bootLayersDelayed;

  function waitForMfRender(tries) {
    if (window.RENDERED) {
      bootLayersDelayed();
      return;
    }
    if (tries <= 0) {
      setTimeout(() => waitForMfRender(40), 120);
      return;
    }
    setTimeout(() => waitForMfRender(tries - 1), 80);
  }

  function boot() {
    initResize();
    window.addEventListener("resize", schedulePlaceChips);
    window.addEventListener("scroll", schedulePlaceChips, true);
    if (window.OPTS && window.OPTS.studioEdit && typeof window.FRAME !== "undefined") {
      waitForMfRender(100);
    } else {
      bootLayersDelayed();
    }
  }

  function layerElForNudge(idx, mfPath) {
    if (mfPath) {
      const esc = (window.CSS && CSS.escape) ? CSS.escape(mfPath) : mfPath.replace(/"/g, '\\"');
      const byPathOnly = document.querySelector(`[data-mf-path="${esc}"], [data-mf-drag="${esc}"]`);
      if (byPathOnly) return byPathOnly;
      const byPath = document.querySelector(
        `[data-spec-idx="${idx}"][data-mf-path="${esc}"], [data-spec-idx="${idx}"][data-mf-drag="${esc}"]`
      );
      if (byPath) return byPath;
    }
    return document.querySelector(`[data-spec-idx="${idx}"].studio-editable`);
  }

  let parentResizeSession = null;

  function applyStudioSelection(d) {
    window.__studioSelected =
      d.idx == null ? null : { idx: d.idx, mfPath: d.mfPath || null };
    document.querySelectorAll(".studio-layer-selected").forEach((n) => {
      n.classList.remove("studio-layer-selected");
    });
    if (window.__studioSelected) {
      const el = layerElForNudge(d.idx, d.mfPath || null);
      if (el) el.classList.add("studio-layer-selected");
    }
    if (!useParentChrome) schedulePlaceChips();
  }

  window.addEventListener("message", (e) => {
    const d = e.data;
    if (!d) return;
    if (d.studio === "select-layer") {
      applyStudioSelection(d);
      return;
    }
    if (d.studio !== "parent-resize") return;
    const el = layerElForNudge(d.idx, d.mfPath || null);
    if (!el || !resizableLayer(el)) return;
    if (d.end) {
      el.classList.remove("studio-resizing");
      if (parentResizeSession && parentResizeSession.el === el) {
        postResize(el, d.idx, parentResizeSession.last);
        parentResizeSession = null;
      }
      schedulePlaceChips();
      return;
    }
    if (!parentResizeSession || parentResizeSession.el !== el) {
      parentResizeSession = beginResizeSession(el);
    }
    applyResizeDelta(parentResizeSession, d.dx || 0, d.dy || 0);
    el.classList.add("studio-resizing");
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
