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
      empty.textContent = "No tagged layers in this preview — use the Layers list on the left.";
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

  function boot() {
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
