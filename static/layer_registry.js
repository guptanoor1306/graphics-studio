/**
 * Shared layer registry for edit mode and export flatten.
 * Elements tagged with data-spec-idx are the source of truth.
 */
(function (global) {
  function layerLabel(el, idx) {
    const t = el.dataset.layerType || el.getAttribute("data-layer-type") || "layer";
    const short = el.dataset.layerLabel || "";
    if (el.dataset.cardIdx != null) {
      const ci = parseInt(el.dataset.cardIdx, 10);
      return short ? t + " · " + short : t + " #" + (ci + 1);
    }
    return short ? t + " · " + short : t + " #" + (idx + 1);
  }

  function exportLayerName(el) {
    const lt = el.dataset.layerType || "";
    const ll = (el.dataset.layerLabel || "").trim();
    if (lt && ll) return lt + ":" + ll.replace(/\s+/g, " ").slice(0, 40);
    const t = (el.innerText || el.getAttribute("src") || "")
      .trim()
      .replace(/\s+/g, " ")
      .slice(0, 40);
    const cls =
      el.className && typeof el.className === "string"
        ? el.className.split(/\s+/)[0]
        : el.tagName.toLowerCase();
    return (lt || cls) + (t ? ":" + t : ll ? ":" + ll.slice(0, 40) : "");
  }

  function applyExportLayerAttrs(el) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    el.dataset.layer = el.dataset.layer || exportLayerName(el);
    el.dataset.x = String(Math.round(r.left));
    el.dataset.y = String(Math.round(r.top));
    el.dataset.w = String(Math.round(r.width));
    el.dataset.h = String(Math.round(r.height));
  }

  function layersFromDocument(root) {
    root = root || document;
    const layers = [];
    root.querySelectorAll("[data-spec-idx]").forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 2 && r.height < 2) return;
      const idx = parseInt(el.dataset.specIdx, 10);
      if (Number.isNaN(idx)) return;
      layers.push({
        el,
        idx,
        type: el.dataset.layerType || "",
        label: el.dataset.layerLabel || layerLabel(el, idx),
        mfPath: el.dataset.mfPath || el.dataset.mfDrag || null,
        cardIdx: el.dataset.cardIdx != null ? parseInt(el.dataset.cardIdx, 10) : null,
        top: r.top,
        left: r.left,
        width: r.width,
        height: r.height,
        exportName: exportLayerName(el),
      });
    });
    return layers;
  }

  function flattenRegistryLayers(overlay) {
    layersFromDocument().forEach(({ el }) => applyExportLayerAttrs(el));
  }

  global.StudioLayerRegistry = {
    layerLabel,
    exportLayerName,
    applyExportLayerAttrs,
    layersFromDocument,
    flattenRegistryLayers,
  };
})(typeof window !== "undefined" ? window : globalThis);
