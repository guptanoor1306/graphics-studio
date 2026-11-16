/* Graphics Studio side of a hand-written ZO frame (the chat skill's look).
   - window.RENDERED once fonts and decor are in place (the renderer waits for it);
   - window.QA(): the checks the chat skill does on its contact sheets, as warnings;
   - studio edit mode: every data-name block becomes a selectable layer (data-mf-path = its name). */
(function () {
  const W = 1920, H = 1080;
  const leafText = () => [...document.querySelectorAll('#content *')].filter(e => {
    if (!e.innerText || !e.innerText.trim()) return false;
    return ![...e.children].some(c => c.innerText && c.innerText.trim());
  });
  const hit = (a, b, pad = 0) => !(a.right + pad <= b.left || a.left - pad >= b.right || a.bottom + pad <= b.top || a.top - pad >= b.bottom);
  const area = r => Math.max(0, r.width) * Math.max(0, r.height);
  const inter = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
  const label = e => (e.innerText || e.getAttribute('data-name') || e.tagName).trim().slice(0, 40).replace(/\n/g, ' ');

  window.QA = function () {
    const warn = [], texts = leafText();
    const rects = texts.map(e => {
      const rg = document.createRange(); rg.selectNodeContents(e);
      const rs = [...rg.getClientRects()].filter(r => r.width > 0);
      if (!rs.length) return null;
      return { e, r: { left: Math.min(...rs.map(r => r.left)), top: Math.min(...rs.map(r => r.top)), right: Math.max(...rs.map(r => r.right)), bottom: Math.max(...rs.map(r => r.bottom)) } };
    }).filter(Boolean);
    for (const { e, r } of rects) {
      const cs = getComputedStyle(e);
      if (r.left < -2 || r.top < -2 || r.right > W + 2 || r.bottom > H + 2) warn.push(`off-frame: "${label(e)}"`);
      if (parseFloat(cs.fontSize) < 25.5) warn.push(`text under 26px: "${label(e)}" (${parseFloat(cs.fontSize)}px)`);
      if (parseInt(cs.fontWeight) > 700) warn.push(`weight ${cs.fontWeight} isn't embedded (use 400–700): "${label(e)}"`);
      // a label running out of the box it sits in (card, pill, step, cell)
      for (let a = e.parentElement; a && a.id !== 'content'; a = a.parentElement) {
        const ac = getComputedStyle(a), box = a.getBoundingClientRect();
        const drawn = (ac.backgroundColor && !/rgba\(.*, 0\)$/.test(ac.backgroundColor) && ac.backgroundColor !== 'transparent') || parseFloat(ac.borderLeftWidth) > 0;
        if (!drawn || !box.width) continue;
        if (r.right > box.right + 3 || r.left < box.left - 3 || r.bottom > box.bottom + 3) warn.push(`text runs out of its box: "${label(e)}"`);
        break;
      }
    }
    for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
      const a = rects[i], b = rects[j];
      if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
      if (inter(a.r, b.r) > 0.25 * Math.min(area(a.r), area(b.r))) warn.push(`text overlaps text: "${label(a.e)}" / "${label(b.e)}"`);
    }
    for (const d of document.querySelectorAll('#decor > *')) {
      const dr = d.getBoundingClientRect();
      if (dr.left < -40 || dr.top < -40 || dr.right > W + 40 || dr.bottom > H + 40) warn.push(`decor ${d.getAttribute('data-name')} is off the frame: move it`);
      for (const { e, r } of rects) if (hit(dr, r, 10)) { warn.push(`decor ${d.getAttribute('data-name')} touches "${label(e)}": move it with decor.${({Squiggle:'doodleAt',Sparkle:'starAt'})[d.getAttribute('data-name')] || 'tri1/tri2/dash1/dash2'}`); break; }
    }
    const face = JSON.parse(document.body.dataset.face || 'null');
    if (face) {
      const fr = { left: face[0], top: face[1], right: face[2], bottom: face[3] };
      for (const { e, r } of rects) if (hit(fr, r)) warn.push(`covers the presenter's face: "${label(e)}"`);
    }
    if (!document.querySelector('#content *')) warn.push('empty frame: add html');
    if (window.RENDER_ERROR) warn.push(window.RENDER_ERROR);
    return [...new Set(warn)];
  };

  function tagLayers() {
    let i = 0;
    document.querySelectorAll('#content [data-name], #decor [data-name], [data-name="Presenter plate"], [data-name="Plate shade"]').forEach(el => {
      if (el.dataset.mfTagged) return;
      el.dataset.mfTagged = '1';
      el.classList.add('studio-editable');
      el.dataset.layerType = 'html';
      el.dataset.layerLabel = (el.getAttribute('data-name') || label(el)).slice(0, 40);
      el.dataset.mfPath = 'html:' + el.getAttribute('data-name');
      el.dataset.specIdx = String(i++);
    });
    if (window.parent && window.parent !== window && !window.__zoLayersPinged) {
      window.__zoLayersPinged = true;
      window.parent.postMessage({ studio: 'layers-ready' }, '*');
    }
  }
  window.studioBootLayers = tagLayers;
  window.initMfInlineText = () => {};

  const done = () => {
    if ((window.OPTS || {}).studioEdit) tagLayers();
    window.RENDERED = true;
  };
  window.addEventListener('error', e => { window.RENDER_ERROR = 'script error: ' + (e.message || e); });
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => requestAnimationFrame(done));
})();
