/* Edit layers = the PSD's layers. Runs in the edit iframe after studio_edit.js.
   LA Studio's own collector (psd_collect.js, copied from source2psd.py) lists every element that becomes a PSD layer.
   Each one that is not a layer here yet gets tagged so the studio's existing tools work on it (select, drag, text,
   delete, copy, AI, replace):
     - inside a hand-written html block (ZO #content, an MF html block):  "<field>><child index path>"
     - a frame turned into a fixed design (body[data-page]):               "page><child index path>"
     - anything the kit draws itself (typed frames, plates, decor):        "locked:<why>" — listed, not editable
       until the frame is made editable (Graphics Studio turns it into a fixed design). */
(function () {
  if (!window.PSD_COLLECT || window.__psdLayers) return;
  window.__psdLayers = true;
  const KIND = { text: 'text', box: 'shape', shape: 'shape', picture: 'img', icon: 'drawing', group: 'drawing', tablelines: 'table', page: 'background' };

  function canvas() {
    const m = document.querySelector('meta[name="studio-canvas"]');
    const [w, h] = (m ? m.getAttribute('content') : '1920,1080').split(',').map(Number);
    return { x: 0, y: 0, w: w || 1920, h: h || 1080 };
  }
  function indexPath(el, root) {
    const p = [];
    while (el && el !== root) {
      const par = el.parentElement;
      if (!par) return null;
      p.unshift([...par.children].indexOf(el));
      el = par;
    }
    return el === root ? p.join('.') : null;
  }
  function editRoot(el) {
    const blk = el.closest('[data-html-block]');
    if (blk && blk !== el) return { root: blk, base: blk.dataset.htmlBlock };
    const zc = document.getElementById('content');
    if (zc && window.FRAME && typeof window.FRAME.html === 'string' && zc !== el && zc.contains(el)) return { root: zc, base: 'html' };
    if (document.body.dataset.page === '1' && el !== document.body) return { root: document.body, base: 'page' };
    return null;
  }
  function lockedWhy(el) {
    if (el.matches('[data-name="Presenter plate"],[data-name="Plate shade"]') || el.closest('[data-name="Presenter plate"]')) return 'plate';
    if (el.closest('#decor')) return 'decor';
    if (el.matches('[data-name="Background grid"]')) return 'background';
    return 'kit';
  }

  let seq = 5000, busy = false;
  function tag() {
    if (busy) return;
    busy = true;
    const ov = document.getElementById('studio-overlay'), ovd = ov ? ov.style.display : '';
    if (ov) ov.style.display = 'none';
    let list = [];
    try { list = window.PSD_COLLECT(canvas()) || []; } catch (e) { console.warn('psd layers:', e); }
    const byI = {};
    document.querySelectorAll('[data-zo]').forEach(el => { el.getAttribute('data-zo').split(/\s+/).forEach(k => { byI[k] = el; }); el.removeAttribute('data-zo'); });
    if (ov) ov.style.display = ovd;
    document.querySelectorAll('[data-spec-idx]').forEach(e => { seq = Math.max(seq, (parseInt(e.dataset.specIdx, 10) || 0) + 1); });
    let added = 0;
    for (const it of list) {
      const el = byI[it.i];
      if (!el || el.dataset.mfTagged || el.dataset.specIdx != null || el.closest('#studio-overlay')) continue;
      const r = editRoot(el), type = KIND[it.kind] || 'drawing';
      if (!r && el.parentElement && el.parentElement.closest('[data-spec-idx]')) continue;   // part of a layer the kit already lists (a decor shape's icon)
      el.dataset.mfTagged = '1';
      el.dataset.layerType = type;
      el.dataset.layerLabel = String(it.name || it.text || type).replace(/\s+/g, ' ').trim().slice(0, 40);
      el.dataset.specIdx = String(seq++);
      if (it.kind === 'box') el.dataset.psdBox = '1';
      const path = r ? indexPath(el, r.root) : null;
      if (r && path && it.kind !== 'page') {
        el.dataset.mfPath = r.base + '>' + path;
        el.classList.add('studio-editable');
        if (it.kind === 'text' && !el.children.length && window.studioInline) {
          window.studioInline(el, () => window.parent.postMessage({ studio: 'inline', mfPath: el.dataset.mfPath, outer: el.outerHTML }, '*'));
        }
      } else {
        el.dataset.mfPath = 'locked:' + (it.kind === 'page' ? 'background' : lockedWhy(el));
      }
      added++;
    }
    busy = false;
    if (added) window.dispatchEvent(new Event('resize'));     // studio_edit.js re-sends the layer list to the page
  }

  function later() {
    if (window.OPTS && window.OPTS.studioEdit && window.FRAME && !window.RENDERED && later.n++ < 60) return setTimeout(later, 120);
    setTimeout(tag, 500);
    setTimeout(tag, 1400);
  }
  later.n = 0;
  if (document.readyState === 'complete') later(); else window.addEventListener('load', later);
  window.addEventListener('message', e => { if (e.data && e.data.studio === 'psd-retag') tag(); });
})();
