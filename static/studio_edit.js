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

  function layers() {
    return [...document.querySelectorAll("[data-spec-idx]")];
  }

  function send(action) {
    if (idx == null) return;
    window.parent.postMessage({ studio: "edit", action, idx }, "*");
  }

  function positionBar(el) {
    const r = el.getBoundingClientRect();
    bar.hidden = false;
    const bw = bar.offsetWidth || 120;
    let left = r.left + r.width / 2 - bw / 2;
    let top = r.top - 44;
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

  bar.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    e.stopPropagation();
    send(btn.dataset.act);
  });

  layers().forEach((el) => {
    el.addEventListener("mouseenter", () => {
      if (hoverEl && hoverEl !== el) hoverEl.classList.remove("studio-hover");
      hoverEl = el;
      idx = parseInt(el.dataset.specIdx, 10);
      el.classList.add("studio-hover");
      positionBar(el);
    });
    el.addEventListener("mouseleave", (ev) => {
      if (bar.contains(ev.relatedTarget)) return;
      clearHover();
    });
  });

  bar.addEventListener("mouseleave", (ev) => {
    if (hoverEl && hoverEl.contains(ev.relatedTarget)) return;
    clearHover();
  });

  window.addEventListener("scroll", () => {
    if (hoverEl) positionBar(hoverEl);
  });
})();
