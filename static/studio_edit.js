(function () {
  const overlay = document.createElement("div");
  overlay.id = "studio-overlay";
  overlay.setAttribute("aria-hidden", "true");
  document.body.appendChild(overlay);

  function send(action, idx) {
    if (idx == null || Number.isNaN(idx)) return;
    window.parent.postMessage({ studio: "edit", action, idx }, "*");
  }

  function chip(label, idx) {
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
        send(btn.dataset.act, idx);
      });
    });
    return el;
  }

  function labelFor(el, idx) {
    const t = el.dataset.layerType || el.getAttribute("data-layer-type") || "layer";
    const short = el.dataset.layerLabel || "";
    return short ? t + " · " + short : t + " #" + (idx + 1);
  }

  function placeChips() {
    overlay.innerHTML = "";
    const layers = [...document.querySelectorAll("[data-spec-idx]")];
    if (!layers.length) {
      const empty = document.createElement("div");
      empty.className = "studio-edit-empty";
      empty.textContent = "No tagged layers — use the Layers list on the right.";
      overlay.appendChild(empty);
      return;
    }
    layers.forEach((el) => {
      const idx = parseInt(el.dataset.specIdx, 10);
      const r = el.getBoundingClientRect();
      if (r.width < 2 && r.height < 2) return;
      const c = chip(labelFor(el, idx), idx);
      let top = r.top - 4;
      let left = r.left;
      if (top < 4) top = r.bottom + 4;
      if (left + 160 > window.innerWidth) left = window.innerWidth - 168;
      c.style.top = top + "px";
      c.style.left = Math.max(4, left) + "px";
      overlay.appendChild(c);
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
    if (t === "asset" || t === "person") return true;
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
      window.parent.postMessage({ studio: "move", idx, x, y }, "*");
      placeChips();
    }

    document.addEventListener("pointerup", finishDrag);
    document.addEventListener("pointercancel", finishDrag);
  }

  function elDim() {
    return { w: document.documentElement.clientWidth || 1920, h: document.documentElement.clientHeight || 1080 };
  }

  function boot() {
    initDrag();
    placeChips();
    window.addEventListener("resize", placeChips);
    window.addEventListener("scroll", placeChips, true);
    setTimeout(placeChips, 400);
    setTimeout(placeChips, 1200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
