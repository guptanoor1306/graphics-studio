// Zero1 reel renderer — window.FRAME + window.OPTS { overlay, studioEdit, tagLayers }
(function () {
  const W = 1080;
  const H = 1920;
  const A = "../assets/";
  const fontsReady = document.fonts.ready.catch(() => {});
  fontsReady.then(() => {
    try {
      run();
    } catch (e) {
      window.RENDER_ERROR = "render error: " + e.message;
    }
    window.RENDERED = true;
    if ((window.OPTS || {}).studioEdit) {
      notifyStudioLayers();
    }
  });

  function run() {
    const F = window.FRAME || {};
    const O = window.OPTS || {};
    const stage = document.getElementById("stage");
    const overlay = !!O.overlay && ["ost", "anchor"].includes(F.type);

    function el(tag, cls, css, html) {
      const e = document.createElement(tag);
      if (cls) e.className = cls;
      if (css) Object.assign(e.style, css);
      if (html !== undefined) e.innerHTML = html;
      return e;
    }
    function add(e) {
      stage.appendChild(e);
      return e;
    }
    function esc(s) {
      return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    }
    function rich(s) {
      return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>");
    }

    if (!overlay && F.bg) {
      const bg = F.bg === "dark" ? "bg-dark" : F.bg === "green" ? "bg-green" : "bg-cream";
      add(el("div", "fill " + bg));
    }
    if (F.plate && !overlay) {
      const p = add(el("div", "fill", { backgroundImage: `url(${F.plate.startsWith("../") ? F.plate : A + F.plate})`, backgroundSize: "cover" }));
      p.dataset.bleed = "1";
    }

    const root = add(el("div", "abs reel-html-shell", { left: 0, top: 0, width: W + "px", height: H + "px" }, F.html || ""));

    if (F.subtitle) {
      const sub = add(
        el(
          "div",
          "abs studio-editable",
          {
            left: "50%",
            transform: "translateX(-50%)",
            bottom: "380px",
            font: "600 45px Manrope,sans-serif",
            color: "#fff",
            textShadow: "0 2px 12px rgba(0,0,0,.55)",
            textAlign: "center",
            maxWidth: "840px",
          },
          rich(F.subtitle)
        )
      );
      sub.dataset.mfPath = "subtitle";
      sub.dataset.content = "1";
    }

    if (O.studioEdit) notifyStudioLayers();
    else if (O.tagLayers) tagStudioLayers();
  }

  function tagOne(el, type, label, path) {
    if (!el || el.dataset.mfTagged) return;
    el.dataset.mfTagged = "1";
    el.classList.add("studio-editable");
    el.dataset.layerType = type;
    el.dataset.layerLabel = label;
    if (path) el.dataset.mfPath = path;
    const idx = document.querySelectorAll(".studio-editable[data-spec-idx]").length;
    el.dataset.specIdx = String(idx);
  }

  function tagStudioLayers() {
    document.querySelectorAll("[data-mf-path]").forEach((el) => {
      const path = el.getAttribute("data-mf-path");
      const lab = (el.innerText || path || "layer").slice(0, 40);
      tagOne(el, "html", lab, path);
    });
    document.querySelectorAll("#stage .abs, #stage [data-content]").forEach((el) => {
      if (el.dataset.mfTagged || el.id === "stage" || el.classList.contains("reel-html-shell")) return;
      if (!el.dataset.mfPath) {
        const lab = (el.innerText || el.className || "block").slice(0, 36);
        tagOne(el, "block", lab, null);
      }
    });
  }

  function notifyStudioLayers(pingParent) {
    tagStudioLayers();
    if (
      pingParent !== false &&
      window.parent &&
      window.parent !== window &&
      !window.__reelLayersReadyPinged
    ) {
      window.__reelLayersReadyPinged = true;
      window.parent.postMessage({ studio: "layers-ready" }, "*");
    }
  }

  window.studioBootLayers = () => notifyStudioLayers();
  window.initMfInlineText = () => {};

  window.QA = function () {
    const warns = [];
    const F = window.FRAME || {};
    document.querySelectorAll("[data-content], .studio-editable, #stage .abs").forEach((e) => {
      if (e.dataset.bleed) return;
      const b = e.getBoundingClientRect();
      const name = (e.innerText || e.className || "").slice(0, 40).replace(/\n/g, " ");
      if (b.left < -2 || b.top < -2 || b.right > W + 2 || b.bottom > H + 2) {
        warns.push(`off-frame: "${name}" [${b.left | 0},${b.top | 0},${b.right | 0},${b.bottom | 0}]`);
      }
    });
    if (window.RENDER_ERROR) warns.push(window.RENDER_ERROR);
    if (!F.html && !F.subtitle && !F.plate) warns.push("empty frame — add html or subtitle");
    return warns;
  };
})();
