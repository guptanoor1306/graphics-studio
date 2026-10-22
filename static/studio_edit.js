(function () {
  const bar = document.createElement("div");
  bar.className = "studio-layer-bar";
  bar.hidden = true;
  bar.innerHTML =
    '<button type="button" data-act="edit" title="Edit text / style">✎</button>' +
    '<button type="button" data-act="replace" title="Replace (kit or reference)">↻</button>' +
    '<button type="button" data-act="delete" title="Remove">×</button>';
  document.body.appendChild(bar);

  let hoverEl = null;
  let idx = null;

  function send(action) {
    if (idx == null || Number.isNaN(idx)) return;
    window.parent.postMessage({ studio: "edit", action, idx }, "*");
  }

  function positionBar(el) {
    const r = el.getBoundingClientRect();
    bar.hidden = false;
    const bw = bar.offsetWidth || 120;
    let left = r.left + r.width / 2 - bw / 2;
    let top = r.top - 48;
    if (top < 8) top = r.bottom + 8;
    left = Math.max(8, Math.min(left, window.innerWidth - bw - 8));
    bar.style.left = left + "px";
    bar.style.top = top + "px";
  }

  function clearHover() {
    if (hoverEl) hoverEl.classList.remove("studio-hover");
    hoverEl = null;
    idx = null;
    bar.hidden = true;
  }

  function activate(el) {
    if (!el || el === hoverEl) return;
    if (hoverEl) hoverEl.classList.remove("studio-hover");
    hoverEl = el;
    idx = parseInt(el.dataset.specIdx, 10);
    el.classList.add("studio-hover");
    positionBar(el);
  }

  bar.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    e.stopPropagation();
    e.preventDefault();
    send(btn.dataset.act);
  });

  document.addEventListener(
    "mouseover",
    (e) => {
      const el = e.target.closest("[data-spec-idx]");
      if (el) activate(el);
    },
    true
  );

  document.addEventListener(
    "mouseout",
    (e) => {
      if (!hoverEl) return;
      const from = e.target.closest("[data-spec-idx]");
      if (from !== hoverEl) return;
      const rel = e.relatedTarget;
      if (rel && (hoverEl.contains(rel) || bar.contains(rel))) return;
      clearHover();
    },
    true
  );

  bar.addEventListener("mouseleave", (ev) => {
    if (hoverEl && ev.relatedTarget && hoverEl.contains(ev.relatedTarget)) return;
    if (ev.relatedTarget && bar.contains(ev.relatedTarget)) return;
    clearHover();
  });

  window.addEventListener("scroll", () => {
    if (hoverEl) positionBar(hoverEl);
  });

  function boot() {
    const n = document.querySelectorAll("[data-spec-idx]").length;
    if (!n) {
      const tip = document.createElement("div");
      tip.className = "studio-edit-empty";
      tip.textContent =
        "No editable layers found — regenerate the frame or use Apply on the frame panel.";
      document.body.appendChild(tip);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
