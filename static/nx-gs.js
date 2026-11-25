/* Make Graphics in LA Studio's design (handoff 2026-11-18, Part B: B2–B16).
   This file only draws the screens; the work is still done by index.html's own functions (askFrame, the edit mode,
   presenter, export, Make Layers, PDF batches…) and the same server calls, so nothing the old screens could do is lost.
   It is loaded before index.html's script and takes over when that script calls nxBoot() at its end.
   ?classic=1 opens the previous screens. */
(() => {
const QS = new URLSearchParams(location.search);
if (QS.has('classic')) return;

/* ---------------- small helpers ---------------- */
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const q1 = (s, r = document) => r.querySelector(s);
const E = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const ls = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (_) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) {} } };
const IC = {
  search: '<circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/>', plus: '<path d="M8 3v10M3 8h10"/>',
  chev: '<path d="M6 3.5L10.5 8 6 12.5"/>', down: '<path d="M4 6l4 4 4-4"/>', back: '<path d="M10 3.5L5.5 8 10 12.5"/>',
  arrow: '<path d="M3 8h10M9 4l4 4-4 4"/>', grid: '<rect x="2.5" y="2.5" width="4.5" height="4.5" rx="1"/><rect x="9" y="2.5" width="4.5" height="4.5" rx="1"/><rect x="2.5" y="9" width="4.5" height="4.5" rx="1"/><rect x="9" y="9" width="4.5" height="4.5" rx="1"/>',
  list: '<path d="M5.5 4h8M5.5 8h8M5.5 12h8M2.5 4h.5M2.5 8h.5M2.5 12h.5"/>', strip: '<rect x="2.5" y="3.5" width="11" height="6.5" rx="1.2"/><path d="M2.5 12.5h3M6.5 12.5h3M10.5 12.5h3"/>',
  filter: '<path d="M2.5 4.5h11M4.5 8h7M6.5 11.5h3"/>', more: '<circle cx="3.5" cy="8" r=".9" fill="currentColor"/><circle cx="8" cy="8" r=".9" fill="currentColor"/><circle cx="12.5" cy="8" r=".9" fill="currentColor"/>',
  trash: '<path d="M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.6 8.5h5.8l.6-8.5"/>', pencil: '<path d="M10.5 3.5l2 2L6 12H4v-2z"/>',
  check: '<path d="M3.5 8.5l3 3 6-7"/>', x: '<path d="M4 4l8 8M12 4l-8 8"/>', undo: '<path d="M5.5 6.5H10a3 3 0 0 1 0 6H7"/><path d="M7.5 4L5 6.5 7.5 9"/>',
  redo: '<path d="M10.5 6.5H6a3 3 0 0 0 0 6h3"/><path d="M8.5 4L11 6.5 8.5 9"/>', regen: '<path d="M12.5 8a4.5 4.5 0 1 1-1.3-3.2M12.5 3v2.5H10"/>',
  minus: '<path d="M3.5 8h9"/>', lock: '<rect x="3.5" y="7.2" width="9" height="6.3" rx="1.4"/><path d="M5.6 7.2V5.3a2.4 2.4 0 014.8 0v1.9"/>', skip: '<circle cx="8" cy="8" r="5.5"/><path d="M4.2 11.8l7.6-7.6"/>', info: '<circle cx="8" cy="8" r="5.5"/><path d="M8 7.3v3.5M8 5.2v.1"/>', download: '<path d="M8 2.5v8M4.5 7.5L8 11l3.5-3.5M3 13.5h10"/>',
  doc: '<path d="M4 2.5h5l3 3v8H4z"/><path d="M9 2.5v3h3M6 8.5h4M6 11h4"/>', wave: '<path d="M2.5 8h1M5 5.5v5M7.5 3v10M10 5.5v5M12.5 7.5v1"/>',
  upload: '<path d="M8 10.5v-8M4.5 6L8 2.5 11.5 6M3 13.5h10"/>', play: '<path d="M5.5 3.8l6.5 4.2-6.5 4.2z" fill="currentColor" stroke="none"/>', pause: '<path d="M5.5 4v8M10.5 4v8"/>',
  clock: '<circle cx="8" cy="8" r="5.5"/><path d="M8 5v3l2 1.5"/>', hash: '<path d="M6 2.5L5 13.5M11 2.5l-1 11M2.5 6h11M2 10h11"/>', video: '<rect x="2" y="3.5" width="9" height="9" rx="1.5"/><path d="M11 7l3-2v6l-3-2"/>',
  status: '<circle cx="8" cy="8" r="5.5"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/>', folder: '<path d="M2.5 4.5h4l1.5 1.5h5.5v6.5h-11z"/>', tag: '<path d="M2.5 2.5h5l6 6-5 5-6-6z"/><circle cx="5.5" cy="5.5" r=".8"/>',
  layers: '<path d="M8 2.5l5.5 3L8 8.5l-5.5-3z"/><path d="M2.5 8.5L8 11.5l5.5-3"/>', file: '<path d="M4 2.5h5l3 3v8H4z"/><path d="M9 2.5v3h3"/>',
  text: '<path d="M3.5 4h9M8 4v8.5"/>', picture: '<rect x="2.5" y="3" width="11" height="10" rx="1.5"/><path d="M2.8 11l3.2-3 2.5 2.3 1.8-1.6 3 2.6"/><circle cx="10.5" cy="6" r="1"/>',
  table: '<rect x="2.5" y="3" width="11" height="10" rx="1.2"/><path d="M2.5 6.3h11M2.5 9.6h11M6.5 3v10"/>', chart: '<path d="M3 13V3M3 13h10"/><path d="M5 10.5l2.5-3 2 1.5L13 5"/>',
  shape: '<circle cx="8" cy="8" r="5"/>', person: '<circle cx="8" cy="5.5" r="2.5"/><path d="M3.5 13.5c0-2.6 2-4.3 4.5-4.3s4.5 1.7 4.5 4.3"/>', block: '<rect x="2.5" y="3.5" width="11" height="9" rx="1.5"/><path d="M5 6.5h6M5 9.5h4"/>',
  frame: '<rect x="2.5" y="4" width="11" height="8" rx="1.5"/>', frames: '<rect x="2.5" y="5.5" width="9.5" height="7" rx="1.4"/><path d="M5 3.5h7.5a1 1 0 0 1 1 1V10"/>',
  reset: '<path d="M3.2 8a4.8 4.8 0 1 0 1.5-3.5"/><path d="M4.6 2.2v2.4H7"/>',
  gear: '<g transform="scale(.6667)" stroke-width="2.4"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></g>',
  copy: '<rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/><path d="M10.5 3.5V3A1.5 1.5 0 0 0 9 1.5H3A1.5 1.5 0 0 0 1.5 3v6A1.5 1.5 0 0 0 3 10.5h.5"/>',
  paste: '<rect x="3" y="2.5" width="10" height="11.5" rx="1.5"/><path d="M6 2.5V2h4v.5M6 7h4M6 10h3"/>', addtext: '<path d="M3 4h7M6.5 4v8.5M11 9v5M8.5 11.5h5"/>',
  chart: '<path d="M3 13V3M3 13h10"/><path d="M5.5 10.5V8M8 10.5V5.5M10.5 10.5V7"/>',
  attach: '<path d="M13 7.5L8 12.5a3 3 0 0 1-4.2-4.2l5.3-5.3a2 2 0 0 1 2.8 2.8L6.6 11a1 1 0 0 1-1.4-1.4L10 4.8"/>', scroll: '<path d="M5.5 11.5V4.3A1.8 1.8 0 0 1 7.3 2.5H12a1.5 1.5 0 0 1 0 3h-1.2"/><path d="M10.8 4v7.7a1.8 1.8 0 0 1-1.8 1.8H4a1.5 1.5 0 0 1 0-3h4.8v1"/>',
};
const I = (n, cls = 'i') => `<svg class="${cls}" viewBox="0 0 16 16">${IC[n] || ''}</svg>`;
const PDFIC = '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#E5484D" stroke-width="1.5" stroke-linejoin="round"><path d="M6 2.8h8.2L19 7.6V21.2H6z"/><path d="M14 2.8v5h5"/><path d="M8.6 17.2c1.6-1 3.6-4.2 3.8-6.4.1-1.4-1.2-1.5-1.3-.2-.2 2.2 2.6 5.4 4.9 5.7 1.2.2 1.3-1.1.1-1.2-2.1-.2-5.7 1.4-7.2 2.6-.9.7-.9-.3-.3-.5"/></svg>';
const LOGO = {
  varsity: '<svg viewBox="0 0 40 40"><path d="M8 7h24v13c0 8-5.5 12.5-12 15-6.5-2.5-12-7-12-15z" fill="#B7D0F7"/><path d="M8 7h12v28C13.5 32.5 8 28 8 20z" fill="#8FB3EE"/><text x="20" y="27" text-anchor="middle" font-family="Georgia,Times,serif" font-weight="700" font-size="17" fill="#1C2A48">V</text></svg>',
  zero1: '<svg viewBox="0 0 40 40"><text x="3" y="23" font-family="Inter,-apple-system,sans-serif" font-style="italic" font-weight="900" font-size="11.5" fill="#111" letter-spacing="-.3">ZERO1</text><path d="M36.5 12l-4 6h2.6l-2 6.5 5-7.5h-2.7l1.6-5z" fill="#F5B400"/><text x="4" y="30" font-family="Inter,-apple-system,sans-serif" font-size="3.6" fill="#555">By ZERODHA</text></svg>',
};
LOGO.zo = LOGO.varsity;   // ZO's logo has not been supplied yet (handoff: open point)
const CH = [
  { id: 'varsity', name: 'Varsity', c: '#A78BFA', line: 'English, Mutual Fund, Hindi Charts and Hindi Elements', kits: ['varsity-english', 'varsity-mf-graphics', 'varsity-hindi-graphics', 'varsity-hindi-fa-graphics'] },
  { id: 'zo', name: 'ZO', c: '#387ED1', line: 'Product and IPO videos: FSS, OSA, OST and TOS frames', kits: ['zo-product-graphics', 'zo-ipo-graphics'] },
  { id: 'zero1', name: 'Zero1', c: '#F5B400', line: 'Hindi long form and vertical Reels', kits: ['zero1-hindi-graphics', 'zero1-reel-graphics'] },
];
const KIT = { 'varsity-english': 'English', 'varsity-mf-graphics': 'Mutual Fund', 'varsity-hindi-graphics': 'Hindi – Charts', 'varsity-hindi-fa-graphics': 'Hindi – Elements', 'zo-product-graphics': 'Product', 'zo-ipo-graphics': 'IPO', 'zero1-hindi-graphics': 'Long form', 'zero1-reel-graphics': 'Reels' };
const chOfTheme = t => CH.find(c => c.kits.includes(t));
const chById = id => CH.find(c => c.id === String(id || '').toLowerCase() || c.name.toLowerCase() === String(id || '').toLowerCase());
const kitsOf = c => (c?.kits || []).filter(t => !themes.length || themes.includes(t));
const kitName = t => KIT[t] || (typeof themeLabel === 'function' ? themeLabel(t) : t);
const isReelTheme = t => /reel/.test(t || '');
const ago = ts => {
  if (!ts) return '';
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 60) return 'Edited just now';
  if (s < 3600) return `Edited ${Math.round(s / 60)} min ago`;
  if (s < 86400) return `Edited ${Math.round(s / 3600)} h ago`;
  if (s < 172800) return 'Edited Yesterday';
  if (s < 30 * 86400) return `Edited ${Math.round(s / 86400)} days ago`;
  return 'Edited ' + new Date(ts * 1000).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
};
const mmss = sec => sec == null || isNaN(sec) ? '' : `${Math.floor(sec / 60)}:${String(Math.floor(sec % 60)).padStart(2, '0')}`;
const words = s => (String(s || '').trim().match(/\S+/g) || []).length;
const fsize = b => !b ? '' : b < 1024 * 1024 ? `${Math.max(1, Math.round(b / 1024))} KB` : `${(b / 1048576).toFixed(1)} MB`;

/* ---------------- toasts, menus, windows ---------------- */
function toast(msg, { undo, err, ms } = {}) {
  let host = q1('.nx-toasts');
  if (!host) { host = document.createElement('div'); host.className = 'nx-toasts'; document.body.appendChild(host); }
  const t = document.createElement('div');
  t.className = 'nx-toast' + (err ? ' err' : '');
  t.innerHTML = `<i class="tk">${I(err ? 'x' : 'check')}</i><span>${E(msg)}</span>${undo ? '<button class="nx-tbtn" data-u>Undo</button>' : ''}<button class="x" aria-label="Close">${I('x')}</button>`;
  const close = () => t.remove();
  t.querySelector('.x').onclick = close;
  if (undo) t.querySelector('[data-u]').onclick = () => { close(); undo(); };
  host.appendChild(t);
  setTimeout(close, ms || (undo ? 8000 : err ? 9000 : 4500));
  return close;
}
let menuEl = null;
function closeMenu() { if (menuEl) { menuEl._btn?.setAttribute('aria-expanded', 'false'); menuEl.remove(); menuEl = null; } }
function menu(btn, items, { right = true, html } = {}) {
  if (menuEl && menuEl._btn === btn) return closeMenu();
  closeMenu();
  const m = document.createElement('div');
  m.className = 'nx-menu';
  m.innerHTML = html || items.map((it, i) => it === '-' ? '<hr>' : it.head ? `<div class="nx-mh">${E(it.head)}</div>` : `<button data-i="${i}" class="${it.red ? 'red' : ''}" ${it.disabled ? 'disabled' : ''}>${it.icon ? I(it.icon) : ''}${E(it.label)}</button>`).join('');
  document.body.appendChild(m);
  const r = btn.getBoundingClientRect();
  const w = m.offsetWidth, h = m.offsetHeight;
  let left = right ? r.right - w : r.left;
  left = Math.max(8, Math.min(left, innerWidth - w - 8));
  let top = r.bottom + 6;
  if (top + h > innerHeight - 8) top = Math.max(8, r.top - h - 6);
  m.style.left = left + 'px'; m.style.top = top + 'px';
  m._btn = btn; btn.setAttribute('aria-expanded', 'true');
  if (!html) m.onclick = e => { const b = e.target.closest('button[data-i]'); if (!b) return; const it = items[+b.dataset.i]; closeMenu(); it.run?.(); };
  menuEl = m;
  return m;
}
document.addEventListener('pointerdown', e => { if (menuEl && !menuEl.contains(e.target) && !menuEl._btn?.contains(e.target)) closeMenu(); }, true);
addEventListener('resize', closeMenu);

function win({ title, sub = '', text = '', body = '', ok = 'OK', wide = false, onOk, onClose, focus }) {
  const m = document.createElement('div');
  m.className = 'nx-modal';
  m.innerHTML = `<div class="nx-win${wide ? ' wide' : ''}" role="dialog" aria-label="${E(title)}"><div class="nx-wh"><b>${E(title)}</b>${sub ? `<small>${E(sub)}</small>` : ''}<button class="nx-ib x" data-x aria-label="Close" data-tip="Close">${I('x')}</button></div>${text ? `<p class="nx-wp">${text}</p>` : ''}<div class="nx-wb">${body}</div><div class="nx-wf"><button class="nx-btn primary lg" data-ok>${E(ok)}</button></div></div>`;
  document.body.appendChild(m);
  const close = (why) => { m.remove(); document.removeEventListener('keydown', key, true); if (why !== 'ok') onClose?.(); };
  const go = async () => {
    const b = m.querySelector('[data-ok]'); if (b.disabled) return;
    b.disabled = true;
    try { const r = await onOk?.(m); if (r !== false) close('ok'); } catch (e) { toast(e.message || String(e), { err: true }); } finally { b.disabled = false; }
  };
  const key = e => {
    if (e.key === 'Escape') { e.stopPropagation(); close(); }
    else if (e.key === 'Enter' && !e.shiftKey && (e.target.tagName === 'INPUT' || (e.target.tagName === 'TEXTAREA' && e.target.dataset.enter))) { e.preventDefault(); go(); }
  };
  document.addEventListener('keydown', key, true);
  m.querySelector('[data-x]').onclick = () => close();
  m.querySelector('[data-ok]').onclick = go;
  m.addEventListener('pointerdown', e => { if (e.target === m) close(); });
  setTimeout(() => (focus ? m.querySelector(focus) : m.querySelector('input,textarea'))?.focus(), 30);
  return { el: m, close };
}

/* ---------------- state ---------------- */
const S = {
  view: 'home', ch: null, kit: '', q: '', mode: ls.get('nx.view', 'grid'), sort: ls.get('nx.sort', { k: 'edited', d: -1 }),
  fst: new Set(), fpj: 'any', picked: new Set(), list: null, err: null, hidden: new Set(),
  strip: ls.get('nx.strip', 'strip'), zoom: 1, gen: null, sedit: false, bg: '', phSel: null, lw: ls.get('nx.lw', 380),
};
const inProject = () => !!LA.id;
window.nxS = S;

async function loadList() {
  try { S.list = await api('/api/projects/summary'); S.err = null; }
  catch (e) { if (!S.list) S.err = e.message || 'unreachable'; }
}
const visible = () => (S.list || []).filter(v => !S.hidden.has(v.id));
const genFor = id => S.gen && S.gen.pid === id;
function status(v) {
  if (genFor(v.id) || v.making) return { k: 'make', t: `Making ${v.frames ? v.frames + (S.gen?.total ? '/' + S.gen.total : '') : ''}`.trim(), o: 1 };
  if (v.in_layers) return { k: 'layers', t: 'In Layers', o: 3 };
  if (v.frames) return { k: 'ready', t: `${v.frames} frame${v.frames === 1 ? '' : 's'} ready`, o: 2 };
  return { k: '', t: 'Not started', o: 0 };
}
const thumbUrl = (pid, fid, ver, w = 480) => `/api/projects/${pid}/frames/${encodeURIComponent(fid)}/thumb.png?w=${w}&v=${E(ver || 0)}`;
const thumbHTML = (v, w) => v.first_fid ? `<img loading="lazy" alt="" src="${thumbUrl(v.id, v.first_fid, Math.round(v.updated_at || 0), w)}" onerror="this.remove()">` : '';

/* ---------------- layout shell ---------------- */
function shell() {
  document.body.classList.add('nx');
  document.body.classList.toggle('nx-embed', !!EMBED);
  if (!EMBED && !q1('#nxSide')) {
    const a = document.createElement('aside');
    a.id = 'nxSide';
    a.innerHTML = `<div class="nx-brand"><span class="nx-logo">GS</span><div><b>Graphics Studio</b><small>Graphics</small></div></div>
      <button class="nx-ri on" data-home><svg viewBox="0 0 16 16" class="i">${IC.scroll}</svg>Graphics</button>`;
    a.querySelector('[data-home]').onclick = () => goHomeNx();
    document.body.appendChild(a);
  }
}
function searchHTML(ph = 'Search videos') {
  return `<label class="nx-search">${I('search')}<input id="nxQ" placeholder="${ph}" value="${E(S.q)}" autocomplete="off"><span class="nx-kbd"><i>${/Mac/.test(navigator.platform) ? '⌘' : 'Ctrl'}</i><i>F</i></span></label>`;
}
function bindSearch() {
  const i = q1('#nxQ'); if (!i) return;
  i.oninput = () => { S.q = i.value; const pos = i.selectionStart; renderList(); const j = q1('#nxQ'); if (j) { j.focus(); j.setSelectionRange(pos, pos); } };
}
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'f' && !P && !editModeOpen) { const i = q1('#nxQ'); if (i) { e.preventDefault(); i.focus(); i.select(); } }
});
const main = () => q1('#main');

/* ---------------- lists: home and channel page (B2–B6) ---------------- */
function goHomeNx() {
  if (editModeOpen) { editModeOpen = false; document.body.classList.remove('edit-mode-on'); q1('#editModeApp').hidden = true; stopBoundsPoll?.(); }
  P = null; selectedFrameId = null; frameVer = {}; S.view = 'home'; S.ch = null; S.picked.clear(); S.q = '';
  renderList(); loadList().then(() => { if (!P) renderList(); });
}
function openChannel(id, kit = '') { S.view = 'channel'; S.ch = id; S.kit = kit; S.picked.clear(); S.q = ''; P = null; renderList(); }

function passes(v) {
  if (S.fst.size && !S.fst.has(status(v).k || 'none')) return false;
  if (S.fpj === 'in' && !v.la_project) return false;
  if (S.fpj === 'out' && v.la_project) return false;
  return true;
}
const SORTK = {
  name: v => String(v.name || '').toLowerCase(), kit: v => kitName(v.theme).toLowerCase(), status: v => status(v).o,
  project: v => v.la_project ? (v.la_name || '').toLowerCase() : '￿', edited: v => v.updated_at || 0,
};
function sorted(arr) {
  const { k, d } = S.sort, f = SORTK[k] || SORTK.edited;
  return [...arr].sort((a, b) => { const x = f(a), y = f(b); return (x < y ? -1 : x > y ? 1 : 0) * d || (b.updated_at - a.updated_at); });
}
function channelVideos() {
  const c = chById(S.ch);
  let vs = visible().filter(v => c?.kits.includes(v.theme));
  if (S.kit) vs = vs.filter(v => v.theme === S.kit);
  return vs;
}
function searchHits() {
  const qs = S.q.trim().toLowerCase();
  return visible().filter(v => String(v.name || '').toLowerCase().includes(qs) || kitName(v.theme).toLowerCase().includes(qs));
}
function skeleton(n = 8) { return `<div class="nx-cards">${Array.from({ length: n }, () => '<div class="nx-skel"><i style="height:16px;width:60%"></i><i style="aspect-ratio:16/9"></i><i style="height:12px;width:45%"></i></div>').join('')}</div>`; }

function cardHTML(v, showKit, showCh) {
  const s = status(v), pk = S.picked.has(v.id);
  const meta = [showKit ? kitName(v.theme) : '', v.la_project ? (v.la_name || 'In a project') : '', ago(v.updated_at)].filter(Boolean).join(' · ');
  const bar = s.k === 'make' ? `<span class="nx-bar"><i style="width:${S.gen?.total ? Math.round(100 * v.frames / S.gen.total) : 35}%"></i></span>` : '';
  const c = chOfTheme(v.theme);
  return `<div class="nx-card${pk ? ' picked' : ''}" data-v="${v.id}" tabindex="0"><div class="nx-cn">${showCh && c ? `<span class="nx-mark" style="width:18px;height:18px;vertical-align:-4px;margin-right:6px">${LOGO[c.id]}</span>` : ''}${E(v.name)}</div>
    <button class="nx-more" data-more aria-label="More" data-tip="More">${I('more')}</button>
    <div class="nx-thumb">${v.first_fid ? '' : '<span class="nx-nf"><i></i>No frames yet</span>'}${thumbHTML(v)}<span class="nx-pill ${s.k}"><i></i>${E(s.t)}</span>${bar}</div>
    <div class="nx-metar"><div class="nx-meta">${E(meta)}</div><button class="nx-ck" data-ck aria-label="Pick" data-tip="Pick" class="tip-up">${I('check')}</button></div></div>`;
}
function thHTML(k, label, icon, cls = '') {
  const on = S.sort.k === k, ar = on ? (S.sort.d > 0 ? '<path d="M8 12.5V3.5M4.5 7L8 3.5 11.5 7"/>' : '<path d="M8 3.5v9M4.5 9L8 12.5 11.5 9"/>') : '<path d="M5.5 6L8 3.5 10.5 6M5.5 10L8 12.5 10.5 10"/>';
  return `<th class="s ${cls}" data-sort="${k}"><span class="nx-th">${I(icon)}${label}<svg class="i ar${on ? ' on' : ''}" viewBox="0 0 16 16">${ar}</svg></span></th>`;
}
function tableHTML(vs, showKit) {
  return `<div class="nx-tbox"><table class="nx-table"><thead><tr><th class="num">#</th>${thHTML('name', 'Videos', 'video')}${showKit ? thHTML('kit', 'Kit', 'tag') : ''}${thHTML('status', 'Status', 'status')}${thHTML('project', 'Project', 'folder')}${thHTML('edited', 'Last edited', 'clock')}<th></th></tr></thead><tbody>
  ${vs.map((v, i) => { const s = status(v); return `<tr class="nx-tr${S.picked.has(v.id) ? ' picked' : ''}" data-v="${v.id}"><td class="num"><span class="n">${i + 1}</span><button class="nx-ck" data-ck aria-label="Pick">${I('check')}</button></td>
    <td><div class="nx-nm"><span class="nx-thumb${isReelTheme(v.theme) ? ' reelth' : ''}">${thumbHTML(v, 160)}</span><span>${E(v.name)}</span></div></td>
    ${showKit ? `<td><span class="nx-chip">${E(kitName(v.theme))}</span></td>` : ''}
    <td><span class="nx-pill inl ${s.k}"><i></i>${E(s.t)}</span></td><td>${v.la_project ? E(v.la_name || 'Project') : '<span class="nx-dim">—</span>'}</td><td class="nx-dim">${E(ago(v.updated_at).replace(/^Edited /, ''))}</td>
    <td class="more"><button class="nx-more" data-more aria-label="More" data-tip="More">${I('more')}</button></td></tr>`; }).join('')}</tbody></table></div>`;
}
function viewSwitch() { return `<div class="nx-view" role="group"><button class="${S.mode === 'grid' ? 'on' : ''}" data-mode="grid" data-tip="Cards">${I('grid')}</button><button class="${S.mode === 'table' ? 'on' : ''}" data-mode="table" data-tip="Table">${I('list')}</button></div>`; }
function filterBtn() {
  const n = S.fst.size + (S.fpj !== 'any' ? 1 : 0);
  return `<button class="nx-btn ghost nx-fbtn${n ? ' on' : ''}" data-filter>${I('filter')}Filter${n ? `<span class="nx-fc">${n}</span>` : ''}</button>`;
}
function selbar(vs) {
  if (!S.picked.size) return '';
  const all = vs.length && vs.every(v => S.picked.has(v.id));
  return `<div class="nx-selbar"><span class="n">${S.picked.size} selected</span><button class="nx-sbb" data-selall>${all ? 'Deselect all' : 'Select all'}</button><button class="nx-sbb red" data-seldel>${I('trash')}Delete</button></div>`;
}
function videosBlock(vs, { showKit, showCh, emptyHTML }) {
  if (!vs.length) return emptyHTML;
  return (S.mode === 'table' ? tableHTML(vs, showKit) : `<div class="nx-cards">${vs.map(v => cardHTML(v, showKit, showCh)).join('')}</div>`) + selbar(vs);
}

function renderList() {
  if (P) return;
  shell();
  document.body.classList.remove('reel');
  syncShellNav?.();
  const m = main();
  if (S.err && !S.list) {
    m.innerHTML = `<div class="nx-top"><h1>Graphics</h1></div><div class="nx-box"><div class="nx-empty"><b>Graphics can't be reached right now</b>Your videos are safe. Check the internet connection, then try again.<button class="nx-btn primary" data-retry>Try again</button></div></div>`;
    m.querySelector('[data-retry]').onclick = async () => { S.err = null; renderList(); await loadList(); renderList(); };
    return;
  }
  if (S.view === 'channel' && S.ch) return renderChannel();
  const loading = !S.list;
  const qs = S.q.trim();
  let res = '';
  if (qs && !loading) {
    const hits = sorted(searchHits().filter(passes));
    res = `<div class="nx-sec">Search results <small class="nx-dim" style="font-weight:400">${hits.length}</small><span class="nx-secr" style="display:flex;gap:12px">${viewSwitch()}</span></div>` +
      videosBlock(hits, { showKit: true, showCh: true, emptyHTML: `<div class="nx-empty"><b>Nothing matches "${E(qs)}"</b><button class="nx-btn ghost" data-clearq>Clear search</button></div>` });
  }
  const chs = loading ? Array.from({ length: 3 }, () => '<div class="nx-skel ch"><i style="width:64px;height:64px;border-radius:50%"></i><i style="height:18px;width:40%"></i><i style="height:12px;width:70%"></i></div>').join('')
    : CH.filter(c => kitsOf(c).length).map(c => `<button class="nx-ch" style="--c:${c.c}" data-ch="${c.id}" aria-label="Open ${c.name}"><span class="nx-logo-c">${LOGO[c.id]}</span><b>${c.name}</b><small>${E(c.line)}</small><span class="nx-go">${I('arrow')}</span></button>`).join('');
  m.innerHTML = `<div class="nx-top"><h1>Graphics</h1><span class="nx-sp"></span>${searchHTML()}<button class="nx-ib round" data-cost aria-label="Settings" data-tip="Settings" class="tip-l">${I('gear')}</button></div>
    <div class="nx-box${S.picked.size ? ' selmode' : ''}"><div class="nx-dash-h"><b>Welcome to LA Studio</b><button class="nx-btn primary lg" data-new>${I('plus')}New</button></div>
    <div class="nx-chs">${chs}</div>${res}</div>`;
  bindList(m, qs ? sorted(searchHits().filter(passes)) : []);
}
function renderChannel() {
  const m = main(), c = chById(S.ch), kits = kitsOf(c), multi = kits.length > 1;
  if (S.kit && !kits.includes(S.kit)) S.kit = '';
  const loading = !S.list;
  const all = loading ? [] : visible().filter(v => c.kits.includes(v.theme));
  let vs = channelVideos();
  const qs = S.q.trim().toLowerCase();
  if (qs) vs = vs.filter(v => String(v.name || '').toLowerCase().includes(qs));
  const filtered = sorted(vs.filter(passes));
  const tabs = multi ? `<div class="nx-tabs">${[['', 'All videos'], ...kits.map(t => [t, kitName(t)])].map(([t, l]) => `<button class="nx-tab${S.kit === t ? ' on' : ''}" data-kit="${t}">${E(l)}${S.kit === t && !loading ? ` (${t ? all.filter(v => v.theme === t).length : all.length})` : ''}</button>`).join('')}</div>`
    : `<div class="nx-allh">All videos${loading ? '' : ` (${all.length})`}</div>`;
  const where = c.name + (S.kit ? ' · ' + kitName(S.kit) : '');
  let empty;
  if (qs) empty = `<div class="nx-empty"><b>Nothing matches "${E(S.q.trim())}"</b><button class="nx-btn ghost" data-clearq>Clear search</button></div>`;
  else if (vs.length && !filtered.length) empty = `<div class="nx-empty"><b>No videos match these filters</b><button class="nx-btn ghost" data-clearf>Clear filters</button></div>`;
  else empty = `<div class="nx-empty"><b>No videos in ${E(where)} yet</b>Make one from a script, a voice-over or a storyboard.<button class="nx-btn primary" data-new>${I('plus')}New</button></div>`;
  m.innerHTML = `<div class="nx-top"><div class="nx-crumb"><button data-home>Graphics</button>${I('chev')}<span class="nx-mark">${LOGO[c.id]}</span><b>${c.name}</b></div>${searchHTML()}</div>
    <div class="nx-box${S.picked.size ? ' selmode' : ''}"><div class="nx-chrow">${tabs}<div class="nx-pright">${filterBtn()}${viewSwitch()}${kits.some(k => TK_THEMES.includes(k)) ? `<button class="nx-btn ghost lg" data-toolkit="${TK_THEMES.includes(S.kit) ? S.kit : ''}" data-tip="${TK_THEMES.includes(S.kit) ? `Ready-made frames for ${E(kitName(S.kit))} videos` : 'Ready-made frames for this channel’s videos'}">${I('frames')}Toolkit${TK_THEMES.includes(S.kit) ? '' : `<svg class="i" viewBox="0 0 16 16">${IC.chev}</svg>`}</button>` : ''}<button class="nx-btn primary lg" data-new>${I('plus')}New</button></div></div>
    ${loading ? skeleton() : videosBlock(filtered, { showKit: multi && !S.kit, emptyHTML: empty })}</div>`;
  bindList(m, filtered);
}
function bindList(m, vs) {
  bindSearch();
  m.onclick = e => {
    const t = e.target;
    const b = t.closest('button');
    if (t.closest('[data-home]')) return goHomeNx();
    const ch = t.closest('[data-ch]'); if (ch) return openChannel(ch.dataset.ch);
    if (t.closest('[data-new]')) return newVideo();
    const tkb = t.closest('[data-toolkit]'); if (tkb) { if (tkb.dataset.toolkit) return openToolkit(tkb.dataset.toolkit); return menu(tkb, kitsOf(chById(S.ch)).filter(k => TK_THEMES.includes(k)).map(k => ({ label: `${kitName(k)} toolkit`, icon: 'frames', run: () => openToolkit(k) }))); }
    if (t.closest('[data-cost]')) return costWin();
    if (t.closest('[data-clearq]')) { S.q = ''; return renderList(); }
    if (t.closest('[data-clearf]')) { S.fst.clear(); S.fpj = 'any'; return renderList(); }
    const kit = t.closest('[data-kit]'); if (kit) { S.kit = kit.dataset.kit; S.picked.clear(); return renderList(); }
    const mode = t.closest('[data-mode]'); if (mode) { S.mode = mode.dataset.mode; ls.set('nx.view', S.mode); return renderList(); }
    const so = t.closest('[data-sort]'); if (so) { const k = so.dataset.sort; S.sort = S.sort.k === k ? { k, d: -S.sort.d } : { k, d: k === 'edited' ? -1 : 1 }; ls.set('nx.sort', S.sort); return renderList(); }
    if (t.closest('[data-filter]')) return filterMenu(t.closest('[data-filter]'));
    if (t.closest('[data-selall]')) { const allOn = vs.every(v => S.picked.has(v.id)); vs.forEach(v => allOn ? S.picked.delete(v.id) : S.picked.add(v.id)); return renderList(); }
    if (t.closest('[data-seldel]')) return delVideos([...S.picked]);
    const row = t.closest('[data-v]'); if (!row) return;
    const id = +row.dataset.v, v = (S.list || []).find(x => x.id === id);
    if (t.closest('[data-ck]')) { S.picked.has(id) ? S.picked.delete(id) : S.picked.add(id); return renderList(); }
    if (t.closest('[data-more]')) return cardMenu(t.closest('[data-more]'), v);
    if (S.picked.size) { S.picked.has(id) ? S.picked.delete(id) : S.picked.add(id); return renderList(); }
    if (b && !b.closest('[data-v]')) return;
    openVideo(id);
  };
  m.onkeydown = e => { if (e.key === 'Enter' && e.target.matches('.nx-card[data-v]')) openVideo(+e.target.dataset.v); };
}
function filterMenu(btn) {
  const st = [['none', 'Not started'], ['make', 'Making'], ['ready', 'Frames ready'], ['layers', 'In Layers']];
  const pj = [['any', 'Any'], ['in', 'In a project'], ['out', 'Not in a project']];
  const n = S.fst.size + (S.fpj !== 'any' ? 1 : 0);
  const m = menu(btn, null, { right: true, html: `<div class="nx-mh">Status</div>${st.map(([k, l]) => `<label><input type="checkbox" data-st="${k}" ${S.fst.has(k) ? 'checked' : ''}>${l}</label>`).join('')}<hr><div class="nx-mh">Project</div>${pj.map(([k, l]) => `<label><input type="radio" name="nxpj" data-pj="${k}" ${S.fpj === k ? 'checked' : ''}>${l}</label>`).join('')}${n ? '<hr><button data-clear>Clear filters</button>' : ''}` });
  if (!m) return;
  m.onchange = e => {
    const i = e.target;
    if (i.dataset.st) i.checked ? S.fst.add(i.dataset.st) : S.fst.delete(i.dataset.st);
    if (i.dataset.pj) S.fpj = i.dataset.pj;
    closeMenu(); renderList(); filterMenu(q1('[data-filter]'));
  };
  m.onclick = e => { if (e.target.closest('[data-clear]')) { S.fst.clear(); S.fpj = 'any'; closeMenu(); renderList(); } };
}
function cardMenu(btn, v) {
  const items = [];
  if (EMBED && laOrigin) items.push({ label: v.la_project ? 'Move to another project' : 'Add to project', icon: 'folder', run: () => addToProject(v) });
  items.push({ label: 'Rename', icon: 'pencil', run: () => renameVideo(v) }, { label: 'Delete', icon: 'trash', red: true, run: () => delVideos([v.id]) });
  menu(btn, items);
}

/* ---------------- Cost: what Claude cost, by job, by day and by video; the cost switches ---------------- */
const JOB = { 'storyboard': 'Storyboard from a script (one Opus call)', 'storyboard-plan': 'Storyboard plan', 'storyboard-frames': 'Frames drawn from the plan',
  'pdf-batch': 'Frames from a storyboard PDF', 'edit': 'Frame edits, chat and Regenerate', 'edit-zo': 'Frame edits (ZO)', 'edit-z1': 'Frame edits (Zero1)',
  'check-fix': 'Layout fixes', 'asset-svg': 'Pictures drawn', 'asset-review': 'Picture checks' };
const money = v => v >= 100 ? '$' + Math.round(v) : '$' + (v || 0).toFixed(v >= 10 ? 1 : 2);
const ktok = n => n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? Math.round(n / 1e3) + 'k' : String(n || 0);
const modelName = m => /opus/.test(m) ? 'Opus' : /sonnet/.test(m) ? 'Sonnet' : /haiku/.test(m) ? 'Haiku' : m;
async function costWin(days = 30) {
  let d;
  try { d = await api('/api/usage?days=' + days); } catch (e) { return toast(e.message || String(e), { err: true }); }
  const max = Math.max(0.0001, ...d.by_day.map(x => x.cost));
  const seg = (k, val, a, b) => `<div class="nx-seg" role="group"><button class="${val !== 'on' ? 'on' : ''}" data-set="${k}" data-v="off">${a}</button><button class="${val === 'on' ? 'on' : ''}" data-set="${k}" data-v="on">${b}</button></div>`;
  const switches = `<div class="nx-lab">Models</div>
    <div class="nx-csw"><div><b>Storyboard from a script</b><small>Opus plans every frame; Sonnet (half the price) writes each frame's layout from that plan. Try it on a few videos and compare the frames before keeping it on.</small></div>${seg('sb_split', d.settings.sb_split, 'One Opus call', 'Opus plans, Sonnet draws')}</div>
    <div class="nx-csw"><div><b>Frames from a storyboard PDF</b><small>The PDF already decides the frames; Sonnet can copy them into the house style.</small></div>${seg('pdf_light', d.settings.pdf_light, 'Opus', 'Sonnet')}</div>
    <div class="nx-csw"><div><b>Layout fixes</b><small>After frames are made, Claude looks at them and fixes problems. "Only flagged" skips batches the layout check finds clean and does one pass, for less than half the cost; a frame that looks off without breaking a check rule won't get a second look.</small></div>${seg('fix_light', d.settings.fix_light, 'Always, 2 passes', 'Only flagged, 1 pass')}</div>
    <div class="nx-lab" style="margin-top:22px">Cost</div>`;
  const body = `<div class="nx-cost">${switches}
    <div class="nx-costh"><div><b>${money(d.total)}</b><span>${d.calls} Claude call${d.calls === 1 ? '' : 's'} in the last ${d.days} days</span></div>
      <div class="nx-seg" role="group">${[7, 30, 90].map(n => `<button class="${n === d.days ? 'on' : ''}" data-days="${n}">${n} days</button>`).join('')}</div></div>
    ${d.jobs.length ? `<table class="nx-ctab"><thead><tr><th>Job</th><th>Model</th><th class="r">Calls</th><th class="r">Tokens in / out</th><th class="r">Cost</th></tr></thead><tbody>
      ${d.jobs.map(j => `<tr><td>${E(JOB[j.label] || j.label)}</td><td><span class="nx-chip">${E(modelName(j.model))}</span></td><td class="r">${j.calls}</td><td class="r">${ktok(j.input + j.cache_read + j.cache_write)} / ${ktok(j.output)}</td><td class="r"><b>${money(j.cost)}</b></td></tr>`).join('')}</tbody></table>` : '<p class="nx-wp">No Claude calls recorded yet. The record starts with this update.</p>'}
    ${d.by_day.length ? `<div class="nx-lab" style="margin-top:18px">By day</div><div class="nx-cdays">${d.by_day.map(x => `<div class="nx-cday" data-tip="${x.day}: ${money(x.cost)} · ${x.calls} calls"><i style="height:${Math.max(3, Math.round(64 * x.cost / max))}px"></i><span>${x.day.slice(8)}</span></div>`).join('')}</div>` : ''}
    ${d.projects.length ? `<div class="nx-lab" style="margin-top:18px">Videos that cost the most</div><div class="nx-cproj">${d.projects.map(p => `<div><span>${E(p.name)}</span><b>${money(p.cost)}</b></div>`).join('')}</div>` : ''}
    <p class="nx-cnote">Prices: Opus 5.5 $4 in / $20 out, Sonnet 5.5 $2 / $10 per million tokens; cached input is billed at a small fraction. Picture generation outside Claude is not included.</p></div>`;
  const w = win({ title: 'Settings', ok: 'Done', wide: true, body, onOk: () => {} });
  w.el.querySelector('.nx-cost').onclick = async e => {
    const dd = e.target.closest('[data-days]'); if (dd) { w.close(); return costWin(+dd.dataset.days); }
    const s = e.target.closest('[data-set]');
    if (s) {
      try { await api('/api/settings', { method: 'PUT', body: JSON.stringify({ key: s.dataset.set, value: s.dataset.v }) }); }
      catch (er) { return toast(er.message || String(er), { err: true }); }
      s.parentElement.querySelectorAll('button').forEach(b => b.classList.toggle('on', b === s));
      const on = s.dataset.v === 'on';
      toast({ sb_split: on ? 'New storyboards: Opus plans, Sonnet draws' : 'New storyboards: one Opus call', pdf_light: on ? 'PDF frames: Sonnet' : 'PDF frames: Opus',
        fix_light: on ? 'Layout fixes: only when the check flags something, 1 pass' : 'Layout fixes: always, 2 passes' }[s.dataset.set] || 'Saved');
    }
  };
}

/* ---------------- windows (B7, B8) ---------------- */
function lookFor(theme) { return (isKitTheme(theme) || isZoProduct(theme) || theme === 'zero1-hindi-graphics') ? { look_line: '' } : { props: [...DEFAULT_PROPS] }; }
function chPills(sel) { return `<div class="nx-chseg" role="radiogroup">${CH.filter(c => kitsOf(c).length).map(c => `<button type="button" class="nx-chpill${sel === c.id ? ' on' : ''}" data-pch="${c.id}" role="radio" aria-checked="${sel === c.id}"><span class="nx-mark">${LOGO[c.id]}</span>${c.name}</button>`).join('')}</div>`; }
function kitChips(c, sel) { return `<div class="nx-kits">${kitsOf(c).map(t => `<button type="button" class="nx-kit${sel === t ? ' on' : ''}" data-pkit="${t}">${E(kitName(t))}</button>`).join('')}</div>`; }
/* Channel + kit picker used by New video and by a project's first step. Returns a function that reads {ch, kit, err}. */
function chKitPicker(host, { ch = null, kit = null, fixedCh = false }) {
  const st = { ch, kit };
  const draw = () => {
    const c = chById(st.ch), kits = kitsOf(c);
    if (c && kits.length === 1) st.kit = kits[0];
    host.innerHTML = `${fixedCh ? '' : `<span class="nx-lab" style="margin-top:22px">Channel</span>${chPills(st.ch)}<p class="nx-err" data-e="ch"></p>`}
      ${c && kits.length > 1 ? `<span class="nx-lab" style="margin-top:${fixedCh ? 18 : 14}px">Kit</span>${kitChips(c, st.kit)}<p class="nx-err" data-e="kit"></p>` : ''}`;
  };
  host.onclick = e => {
    const p = e.target.closest('[data-pch]'); if (p) { if (st.ch !== p.dataset.pch) { st.ch = p.dataset.pch; st.kit = null; } draw(); }
    const k = e.target.closest('[data-pkit]'); if (k) { st.kit = k.dataset.pkit; draw(); }
  };
  draw();
  return () => {
    host.querySelectorAll('.nx-err').forEach(x => x.textContent = '');
    if (!st.ch) { const x = host.querySelector('[data-e="ch"]'); if (x) x.textContent = 'Pick a channel.'; return null; }
    if (!st.kit) { const x = host.querySelector('[data-e="kit"]'); if (x) x.textContent = 'Pick a kit.'; return null; }
    return st;
  };
}
function newVideo() {
  const fromCh = S.view === 'channel' ? chById(S.ch) : null;
  const w = win({
    title: 'New video', ok: 'Create',
    body: `<span class="nx-lab">Name</span><input class="nx-field" id="nxNewName" placeholder="For example: The money decisions you should automate" autocomplete="off"><p class="nx-err" id="nxNewErr"></p><div id="nxNewPick"></div>`,
    onOk: async m => {
      const name = m.querySelector('#nxNewName').value.trim();
      const pick = read();
      m.querySelector('#nxNewErr').textContent = name ? '' : 'Give the video a name.';
      if (!name || !pick) return false;
      const p = await api('/api/projects', { method: 'POST', body: JSON.stringify({ name, theme: pick.kit, look: lookFor(pick.kit) }) });
      if (EMBED) laEnsureProject(p).catch(() => {});
      loadList();
      await openVideo(p.id);
    },
  });
  const read = chKitPicker(w.el.querySelector('#nxNewPick'), { ch: fromCh?.id || null, kit: fromCh ? (S.kit || null) : null, fixedCh: !!fromCh });
  w.el.querySelector('#nxNewName').addEventListener('input', () => { w.el.querySelector('#nxNewErr').textContent = ''; });
}
async function renameTo(id, name) {
  const r = await api('/api/projects/' + id, { method: 'PUT', body: JSON.stringify({ name, note: 'rename' }) });
  if (P && P.id === id) { P.name = r.name; }
  const v = (S.list || []).find(x => x.id === id); if (v) v.name = r.name;
  return r;
}
function renameVideo(v) {
  win({
    title: 'Rename video', ok: 'Rename', body: `<span class="nx-lab">Name</span><input class="nx-field" id="nxRen" value="${E(v.name)}">`,
    onOk: async m => { const n = m.querySelector('#nxRen').value.trim(); if (!n) return false; if (n !== v.name) await renameTo(v.id, n); P ? render() : renderList(); },
  });
}
async function addToProject(v) {
  let projects = [];
  try { projects = ((await laPost('projects', {})) || {}).projects || []; }
  catch (e) { toast('Update LA Studio to add videos to projects (Check for updates in its sidebar).', { err: true }); return; }
  const chName = chOfTheme(v.theme)?.name || '';
  let sel = v.la_project || '';
  const w = win({
    title: 'Add to project', ok: 'Add', wide: true,
    text: `"${E(v.name)}" becomes the project's Graphics step.`,
    body: `<div class="nx-plist">${projects.map(p => `<label class="nx-radio${sel === p.id ? ' on' : ''}"><input type="radio" name="nxap" value="${E(p.id)}" ${sel === p.id ? 'checked' : ''}>${E(p.name)}<small>${E(p.channel || '')}</small></label>`).join('')}
      <label class="nx-radio${sel === '' ? '' : ''}"><input type="radio" name="nxap" value="__new">New project…</label></div>
      <div id="nxApNew" hidden style="margin-top:10px"><span class="nx-lab">Name</span><input class="nx-field" id="nxApName" value="${E(v.name)}"></div><p class="nx-err" id="nxApErr"></p>`,
    onOk: async m => {
      const val = m.querySelector('input[name=nxap]:checked')?.value;
      if (!val) { m.querySelector('#nxApErr').textContent = 'Pick a project.'; return false; }
      let la, laName;
      if (val === '__new') {
        laName = m.querySelector('#nxApName').value.trim() || v.name;
        const r = await laPost('project', { gs_id: String(v.id), name: laName, channel: chName, channel_id: chOfTheme(v.theme)?.id || '', form: LA_FORM(v.theme), fresh: true });
        la = r && r.la; laName = r?.name || laName;
      } else { la = val; laName = (projects.find(p => p.id === val) || {}).name || ''; }
      if (!la) throw new Error('LA Studio could not make the project.');
      await api('/api/la/link', { method: 'POST', body: JSON.stringify({ la_project: la, la_name: laName, project_id: v.id }) });
      laPost('changed', {}).catch(() => {});
      toast(`Added to "${laName}"`);
      await loadList(); P ? render() : renderList();
    },
  });
  w.el.querySelector('.nx-plist').onchange = e => {
    w.el.querySelectorAll('.nx-radio').forEach(l => l.classList.toggle('on', l.contains(e.target) && e.target.checked));
    w.el.querySelector('#nxApNew').hidden = e.target.value !== '__new';
  };
}
/* Delete is instant with Undo: the video leaves the list at once and is deleted on the server when the toast ends. */
const pendingDel = new Map();
function delVideos(ids) {
  ids = ids.filter(Boolean); if (!ids.length) return;
  const names = ids.map(id => (S.list || []).find(v => v.id === id)?.name || (P && P.id === id ? P.name : 'Video'));
  ids.forEach(id => S.hidden.add(id));
  S.picked.clear();
  if (P && ids.includes(P.id)) { const c = chOfTheme(P.theme); P = null; selectedFrameId = null; S.view = c ? 'channel' : 'home'; S.ch = c?.id || null; }
  renderList();
  const fire = async () => {
    for (const id of ids) { pendingDel.delete(id); try { await _api0(`/api/projects/${id}/delete`, { method: 'POST' }); } catch (_) {} }
    ids.forEach(id => S.hidden.delete(id)); if (S.list) S.list = S.list.filter(v => !ids.includes(v.id));
    if (EMBED) laPost('changed', {}).catch(() => {});
  };
  const t = setTimeout(fire, 8000);
  ids.forEach(id => pendingDel.set(id, t));
  toast(ids.length > 1 ? `${ids.length} videos deleted` : `"${names[0]}" deleted`, {
    undo: () => { clearTimeout(t); ids.forEach(id => { S.hidden.delete(id); pendingDel.delete(id); }); renderList(); },
  });
}
addEventListener('pagehide', () => { [...pendingDel.keys()].forEach(id => { try { fetch(`/api/projects/${id}/delete`, { method: 'POST', keepalive: true }); } catch (_) {} }); });

/* ---------------- a video: Sources or frames ---------------- */
function loadingView(name, msg = 'Opening the video…') {
  const lines = Array.from({ length: 5 }, (_, i) => `<div style="padding:12px;display:flex;flex-direction:column;gap:8px"><i style="height:14px;width:${40 + (i % 3) * 12}%"></i><i style="height:11px;width:92%"></i><i style="height:11px;width:${70 + (i % 2) * 15}%"></i></div>`).join('');
  main().innerHTML = `<div class="nx-top">${name ? `<div class="nx-crumb"><b>${E(name)}</b></div>` : (gsSteps() ? projectStepsEmpty() : '')}</div>
    <div class="nx-row"><div class="nx-pan nx-left nx-skel" style="border:0;border-radius:14px;padding:12px 10px;--lw:${S.lw}px">${lines}</div>
    <div class="nx-pan nx-mid"><div class="nx-ldc"><span class="nx-spin" aria-hidden="true"></span><span>${E(msg)}</span></div></div></div>
    <div class="nx-dock"></div>`;
}
async function openVideo(id) {
  S.sedit = false; S.phSel = null; S.zoom = 1; S.bg = '';
  const v = (S.list || []).find(x => x.id === id);
  loadingView(v?.name || '');
  try { await open_(id); } catch (e) { toast(e.message || String(e), { err: true }); renderList(); }
}
function chOfP() { return chOfTheme(P?.theme) || CH[0]; }
const gsSteps = () => inProject() && QS.get('bar') === 'gs';   // LA Studio v2.18+ hides its own steps on this step and asks for ours
function topLeftHTML() {
  if (gsSteps()) return projectSteps();
  if (inProject()) return `<div class="nx-crumb"><span class="nx-title" data-title data-tip="Click to rename">${E(P.name)}</span></div>`;
  const c = chOfP();
  return `<div class="nx-crumb"><button data-home>Graphics</button>${I('chev')}<button data-chn class="nx-crch" style="display:inline-flex;align-items:center;gap:6px"><span class="nx-mark">${LOGO[c.id]}</span>${c.name}</button>${I('chev')}<span class="nx-title" data-title data-tip="Click to rename">${E(P.name)}</span></div>`;
}
function projectSteps() {
  const made = studioFrames().length > 0;
  const st = [['graphics', 'Graphics'], ['psd', 'Layers'], ['animate', 'Animate'], ['video', 'Edit on video']];
  const done = new Set((QS.get('done') || '').split(',').filter(Boolean)); if (made) done.add('graphics');
  return `<div class="nx-steps">${st.map(([k, l], i) => `<button class="nx-step${k === 'graphics' ? ' on' : ''}${done.has(k) ? ' done' : ''}" data-stage="${k}"><i>${done.has(k) ? '✓' : i + 1}</i>${l}</button>${i < 3 ? I('chev') : ''}`).join('')}</div>`;
}
function bindTop(m) {
  m.querySelector('[data-home]')?.addEventListener('click', goHomeNx);
  m.querySelector('[data-chn]')?.addEventListener('click', () => openChannel(chOfP().id));
  m.querySelectorAll('[data-stage]').forEach(b => b.addEventListener('click', () => { if (b.dataset.stage !== 'graphics') laPost('stage', { stage: b.dataset.stage }).catch(() => laPost('skip', {}).catch(() => {})); }));
  const t = m.querySelector('[data-title]');
  if (t) t.onclick = () => {
    const inp = document.createElement('input'); inp.className = 'nx-titlein'; inp.value = P.name;
    t.replaceWith(inp); inp.focus(); inp.select();
    let done = false;
    const end = async ok => { if (done) return; done = true; const n = inp.value.trim(); if (ok && n && n !== P.name) { try { await renameTo(P.id, n); toast('Video renamed'); } catch (e) { toast(e.message, { err: true }); } } render(); };
    inp.onkeydown = e => { if (e.key === 'Enter') end(true); if (e.key === 'Escape') end(false); };
    inp.onblur = () => end(true);
  };
}
function videoMenu(btn) {
  const items = [{ label: 'Rename video', icon: 'pencil', run: () => renameVideo({ id: P.id, name: P.name }) }];
  if (tkKit() && studioFrames().length) items.push({ label: 'Save this frame to toolkit', icon: 'frames', run: saveToToolkit });
  if (P.spec) {
    items.push({ label: 'Check the layout', icon: 'check', run: checkLayout });
    items.push({ label: 'Download storyboard instructions', icon: 'download', run: () => { location.href = `/api/projects/${P.id}/storyboard-instructions.csv`; } });
  }
  if (EMBED && laOrigin && !inProject()) items.push({ label: 'Add to project', icon: 'folder', run: async () => { await loadList(); addToProject((S.list || []).find(v => v.id === P.id) || { id: P.id, name: P.name, theme: P.theme }); } });
  items.push('-', { label: 'Delete video', icon: 'trash', red: true, run: () => delVideos([P.id]) });
  menu(btn, items);
}
async function checkLayout() {
  S.banner = { cls: '', text: 'Checking every frame for overlaps, cut-off text and off-frame parts…' }; render();
  try { const w = await api(`/api/projects/${P.id}/check`); S.banner = w.length ? { cls: 'bad', text: w.join('\n') } : null; if (!w.length) toast('No layout problems on any frame'); }
  catch (e) { S.banner = { cls: 'bad', text: e.message }; }
  render();
}

function render2() {
  if (!P) return renderList();
  shell();
  syncShellNav?.();
  if (editModeOpen) return;
  document.body.classList.toggle('reel', isReelTheme(P.theme));
  if (isTkProject()) return toolkitView();
  const hasFrames = studioFrames().length > 0;
  if (!hasFrames && !genFor(P.id)) return sourcesView();
  framesView();
}

/* ---------------- Sources: "Add what you have" (B9) ---------------- */
const pdfOn = () => !!P?.has_storyboard_pdf && P?.look?.sb_import !== 'script';
const scriptOn = () => scriptHasContent(P?.script || '');
const audioOn = () => !!(P?.has_episode_transcript || P?.has_episode_audio || S.audioBusy);
function estFrames() {
  const sec = P?.episode_audio_seconds || (words(P?.script) / 2.6);
  return sec ? Math.max(1, Math.round(sec / 9)) : 0;
}
const srcEmpty = (k, a, b, icon) => `<div class="nx-eb empty" data-add="${k}"><span class="ic">${I(icon)}</span><span>${a}</span><small>${b}</small></div>`;
const scriptBody = () => scriptOn() ? `<div class="nx-eb done"><span class="nx-okc">${I('check')}</span><div class="tx"><b>${words(P.script)} words${S.sedit ? ' · Editing' : ''}</b></div>${S.sedit ? '' : '<button class="nx-tbtn" data-sedit>Edit</button>'}<button class="nx-ib nx-trash" data-del="script" data-tip="Remove the script">${I('trash')}</button></div>` : srcEmpty('script', 'Write or paste', '⌘V works anywhere', 'pencil');
function srcDock() {
  const s = { sc: scriptOn(), pdf: pdfOn(), au: audioOn() };
  const added = [s.sc && 'Script', s.pdf && 'Storyboard PDF', s.au && 'Voice-over'].filter(Boolean);
  const n = estFrames();
  const tkb = tkKit() && (s.sc || s.au || s.pdf) ? `<button class="nx-btn ghost lg" data-tkpick ${S.audioBusy ? 'disabled' : ''}>${I('frames')}Pick from toolkit</button>` : '';
  return `<span class="tx">${E(added.length ? `${added.join(' + ')} added${n ? ` · about ${n} frame${n === 1 ? '' : 's'}` : ''}` : 'Add at least one to start')}</span>${tkb}<button class="nx-btn primary lg" data-gen ${added.length && !S.audioBusy && !S.pdfBusy ? '' : 'disabled'}>${s.pdf ? 'Generate frames' : 'Generate storyboard + frames'}</button>`;
}
function srcLive() {
  const c = q1('[data-card="script"]'); if (c) { c.classList.toggle('on', scriptOn() || S.sedit); const eb = c.querySelector('.nx-eb'); if (eb) eb.outerHTML = scriptBody(); }
  const d = q1('#nxSrcDock'); if (d) d.innerHTML = srcDock();
}
function sourcesView() {
  const m = main();
  const s = { sc: scriptOn(), pdf: pdfOn(), au: audioOn() };
  const empty = srcEmpty;
  const scBody = scriptBody();
  const pdfBody = s.pdf ? `<div class="nx-eb done"><span class="nx-pdfic">${PDFIC}</span><div class="tx"><b>${E((P.storyboard_pdf_name || P.look?.storyboard_pdf_name || 'Storyboard').replace(/\.pdf$/i, ''))}</b><small>${[P.look?.storyboard_pdf_pages ? `${P.look.storyboard_pdf_pages} pages` : '', fsize(P.look?.storyboard_pdf_bytes)].filter(Boolean).join(' · ') || 'Storyboard PDF'}</small></div><button class="nx-ib nx-trash" data-del="pdf" data-tip="Remove the storyboard PDF">${I('trash')}</button></div>`
    : S.pdfBusy ? `<div class="nx-eb done"><span class="nx-pdfic">${PDFIC}</span><div class="tx"><b>${E(S.pdfBusy)}</b><small>Saving…</small></div></div>` : empty('pdf', 'Upload or drop', 'PDF', 'upload');
  let auBody;
  if (s.au) {
    const secs = P.episode_audio_seconds || S.audioSecs;
    let st = S.audioBusy ? 'Transcribing…' : P.has_episode_transcript ? 'Transcribed' : 'Not transcribed';
    if (!S.audioBusy && s.sc && P.episode_transcript_segments) {
      const ws = words(P.script), aw = S.trWords || 0;
      if (aw) { const ok = Math.abs(ws - aw) / Math.max(ws, aw) < 0.2; st = `<span class="nx-match${ok ? '' : ' warn'}" data-tip="Script: ${ws} words · voice-over: ${aw} words">${ok ? '✓ Matches script' : '⚠ Length differs'}</span>`; }
    }
    auBody = `<div class="nx-eb done" style="flex-direction:column;align-items:stretch;justify-content:center;gap:0;padding:10px 12px 10px 16px"><div style="display:flex;align-items:center;gap:12px"><button class="nx-play" data-play data-tip="Play">${I(S.playing ? 'pause' : 'play')}</button><div class="tx" style="flex:1;min-width:0;display:flex;flex-direction:column"><b style="font-size:13.5px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${E((P.episode_audio_name || S.audioBusy || 'Voice-over').replace(/\.(mp3|m4a|wav|webm|ogg|mp4)$/i, ''))}</b><small style="font-size:12px;color:var(--mute)">${[mmss(secs), st].filter(Boolean).join(' · ')}</small></div><button class="nx-ib nx-trash" data-del="audio" data-tip="${S.audioBusy ? 'Stop and remove this voice-over' : 'Remove the voice-over'}" class="tip-l">${I('trash')}</button></div><div class="nx-wave" data-wave>${waveBars()}</div></div>`;
  } else auBody = empty('audio', 'Upload or drop', 'MP3, M4A or WAV', 'upload');
  const card = (k, icon, title, body, on) => `<div class="nx-ec${on ? ' on' : ''}" data-card="${k}"><span class="nx-eic">${icon}</span><b>${title}</b>${body}</div>`;
  m.innerHTML = `<div class="nx-top">${topLeftHTML()}<span class="nx-sp"></span><button class="nx-ib" data-vmore aria-label="More" data-tip="More">${I('more')}</button></div>
  <div class="nx-box"><div class="nx-srcw">
    <div class="nx-srch"><b>Add what you have</b><span>use one, or combine them</span><span class="nx-note" data-tip="With more than one: the storyboard decides the frames, the voice-over times them, the script fills in exact words and numbers.">${I('info')}</span></div>
    <div class="nx-srcs">${card('script', I('doc'), 'Script', scBody, s.sc || S.sedit)}<span class="nx-plus">+</span>${card('pdf', PDFIC.replace('width="22" height="22"', 'width="18" height="18"'), 'Storyboard PDF', pdfBody, s.pdf)}<span class="nx-plus">+</span>${card('audio', I('wave'), 'Voice-over', auBody, s.au)}</div>
    ${S.sedit ? `<div class="nx-sedit"><div class="nx-sedit-h"><b>Script</b><button class="nx-tbtn" data-sdone>Done</button></div><textarea id="nxScriptEd" spellcheck="true">${E(P.script || '')}</textarea><small id="nxScriptN"></small></div>` : ''}
  </div></div>
  <div class="nx-dock" id="nxSrcDock">${srcDock()}</div>
  <input type="file" id="nxPdfIn" accept="application/pdf,.pdf" hidden><input type="file" id="nxAuIn" accept="audio/*,.mp3,.m4a,.wav,.webm" hidden>`;
  bindTop(m);
  const ed = q1('#nxScriptEd');
  if (ed) { const upd = () => { const w = words(ed.value); q1('#nxScriptN').textContent = `${w} words · about ${Math.max(1, Math.round(w / 150))} min · about ${Math.max(1, Math.round(w / 2.6 / 9))} frames`; }; upd(); ed.oninput = () => { upd(); saveScriptSoon(ed.value); srcLive(); }; if (S.seditFocus) { ed.focus(); S.seditFocus = false; } }
  m.onclick = e => {
    const t = e.target;
    if (t.closest('[data-vmore]')) return videoMenu(t.closest('[data-vmore]'));
    const add = t.closest('[data-add]');
    if (add) { const k = add.dataset.add; if (k === 'script') { S.sedit = true; S.seditFocus = true; return sourcesView(); } q1(k === 'pdf' ? '#nxPdfIn' : '#nxAuIn').click(); return; }
    if (t.closest('[data-sedit]')) { S.sedit = true; S.seditFocus = true; return sourcesView(); }
    if (t.closest('[data-sdone]')) { S.sedit = false; flushScript(); return sourcesView(); }
    const del = t.closest('[data-del]'); if (del) return removeSource(del.dataset.del);
    if (t.closest('[data-play]')) return playAudio();
    const wv = t.closest('[data-wave]'); if (wv) { const r = wv.getBoundingClientRect(); return playAudio((e.clientX - r.left) / r.width); }
    if (t.closest('[data-tkpick]')) return tkPicker();
    if (t.closest('[data-gen]')) return startGen();
  };
  q1('#nxPdfIn').onchange = e => { const f = e.target.files[0]; if (f) addFile(f); e.target.value = ''; };
  q1('#nxAuIn').onchange = e => { const f = e.target.files[0]; if (f) addFile(f); e.target.value = ''; };
  if (s.au && P.has_episode_transcript && S.trWordsFor !== P.id) loadTranscriptWords();
  if (s.au && !S.peaks && !S.peaksBusy) loadPeaks();
}
function waveBars() {
  const pk = S.peaks || Array.from({ length: 72 }, (_, i) => 0.35 + 0.5 * Math.abs(Math.sin(i * 1.7) * Math.cos(i * 0.6)));
  const pos = S.playPos || 0;
  return pk.map((v, i) => `<i class="${i / pk.length < pos ? 'p' : ''}" style="height:${Math.round(18 + v * 82)}%"></i>`).join('');
}
async function loadPeaks() {
  S.peaksBusy = true;
  try {
    const buf = await (await fetch(`/api/projects/${P.id}/episode-audio/file`)).arrayBuffer();
    const ac = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 2, 44100);
    const au = await ac.decodeAudioData(buf);
    const d = au.getChannelData(0), n = 72, step = Math.floor(d.length / n), out = [];
    for (let i = 0; i < n; i++) { let mx = 0; for (let j = i * step; j < (i + 1) * step; j += 64) mx = Math.max(mx, Math.abs(d[j])); out.push(mx); }
    const top = Math.max(...out, 0.01); S.peaks = out.map(v => v / top); S.audioSecs = au.duration;
    if (P && !P.spec?.frames?.length) sourcesView();
  } catch (_) {} finally { S.peaksBusy = false; }
}
async function loadTranscriptWords() {
  S.trWordsFor = P.id;
  try { const tr = await api(`/api/projects/${P.id}/episode-transcript`); episodeTranscript = tr; S.trWords = (tr.segments || []).reduce((n, s) => n + words(s.text), 0); if (!P.spec?.frames?.length) sourcesView(); } catch (_) {}
}
let audioEl = null;
function playAudio(at) {
  if (!audioEl) {
    audioEl = new Audio(`/api/projects/${P.id}/episode-audio/file`);
    audioEl.ontimeupdate = () => { S.playPos = audioEl.duration ? audioEl.currentTime / audioEl.duration : 0; const w = q1('[data-wave]'); if (w) w.innerHTML = waveBars(); };
    audioEl.onended = () => { S.playing = false; S.playPos = 0; if (!P?.spec?.frames?.length) sourcesView(); };
  }
  if (at != null && audioEl.duration) audioEl.currentTime = at * audioEl.duration;
  if (at == null && S.playing) { audioEl.pause(); S.playing = false; } else { audioEl.play().catch(() => {}); S.playing = true; }
  const b = q1('[data-play]'); if (b) b.innerHTML = I(S.playing ? 'pause' : 'play');
}
let scriptT = null, scriptPending = null;
function saveScriptSoon(v) { P.script = v; scriptPending = v; clearTimeout(scriptT); scriptT = setTimeout(flushScript, 700); }
async function flushScript() {
  clearTimeout(scriptT); if (scriptPending == null || !P) return;
  const v = scriptPending; scriptPending = null;
  try { const r = await api('/api/projects/' + P.id, { method: 'PUT', body: JSON.stringify({ script: v, note: 'script' }) }); if (P && r.id === P.id) P.updated_at = r.updated_at; } catch (e) { toast('The script could not be saved: ' + e.message, { err: true }); }
}
async function addFile(f) {
  if (!P) return;
  const n = (f.name || '').toLowerCase(), ty = f.type || '';
  if (ty === 'application/pdf' || n.endsWith('.pdf')) {
    S.pdfBusy = f.name; render();
    try {
      const fd = new FormData(); fd.append('file', f, f.name || 'storyboard.pdf');
      const r = await fetch(`/api/projects/${P.id}/storyboard-pdf`, { method: 'POST', body: fd });
      if (!r.ok) throw new Error(parseApiErrorText(await r.text()));
      const d = await r.json(); P = d; P.look = normLook(P.look); P.has_storyboard_pdf = !!(d.has_storyboard_pdf || d.has_pdf);
      if (!P.has_storyboard_pdf) throw new Error('The PDF was not kept on the server. Try again.');
      toast('The storyboard PDF is added');
    } catch (e) { toast(e.message || String(e), { err: true }); } finally { S.pdfBusy = null; render(); }
    return;
  }
  if (/^audio\//.test(ty) || /\.(mp3|m4a|wav|webm|ogg)$/.test(n)) {
    S.audioBusy = f.name; S.peaks = null; audioEl = null;
    try { const url = URL.createObjectURL(f); const a = new Audio(url); a.onloadedmetadata = () => { S.audioSecs = a.duration; if (S.audioBusy) render(); }; } catch (_) {}
    render();
    try {
      const fd = new FormData(); fd.append('file', f, f.name || 'voice-over.mp3');
      const r = await fetch(`/api/projects/${P.id}/episode-audio`, { method: 'POST', body: fd });
      if (!r.ok) throw new Error(parseApiErrorText(await r.text()));
      P = await r.json(); P.look = normLook(P.look); episodeTranscript = null; S.trWordsFor = null;
      if (S.audioCancel) { S.audioCancel = false; P = await api(`/api/projects/${P.id}/episode-audio`, { method: 'DELETE' }); P.look = normLook(P.look); toast('Voice-over removed'); return; }
      toast(P.has_episode_transcript ? 'The voice-over is transcribed' : 'The voice-over is saved, but it could not be transcribed');
    } catch (e) { toast(e.message || String(e), { err: true }); } finally { S.audioBusy = null; render(); }
    return;
  }
  if (/^text\//.test(ty) || /\.(txt|md|srt|vtt)$/.test(n)) {
    const tx = await f.text(); saveScriptSoon(tx); flushScript(); S.sedit = true; render(); toast('The script is added'); return;
  }
  toast("That file couldn't be used (PDF, MP3, M4A or WAV)", { err: true });
}
async function removeSource(k) {
  if (k === 'script') {
    const old = P.script; saveScriptSoon(''); await flushScript(); S.sedit = false; render();
    toast('Script removed', { undo: async () => { saveScriptSoon(old); await flushScript(); render(); } });
  } else if (k === 'pdf') {
    const look = { ...P.look, sb_import: 'script' };
    P = await api('/api/projects/' + P.id, { method: 'PUT', body: JSON.stringify({ look, note: 'storyboard PDF removed' }) }); P.look = normLook(P.look); render();
    toast('Storyboard PDF removed', { undo: async () => { P = await api('/api/projects/' + P.id, { method: 'PUT', body: JSON.stringify({ look: { ...P.look, sb_import: 'pdf' }, note: 'storyboard PDF back' }) }); P.look = normLook(P.look); render(); } });
  } else if (k === 'audio') {
    if (audioEl) { audioEl.pause(); audioEl = null; S.playing = false; }
    if (S.audioBusy) { S.audioCancel = true; S.audioBusy = null; }
    P = await api(`/api/projects/${P.id}/episode-audio`, { method: 'DELETE' }); P.look = normLook(P.look); S.peaks = null; episodeTranscript = null; render();
    toast('Voice-over removed');
  }
}
/* Drop anywhere on a video's page; ⌘V anywhere pastes into the script */
let dragOv = null;
addEventListener('dragover', e => { if (!P || editModeOpen || !e.dataTransfer?.types?.includes('Files')) return; e.preventDefault(); if (!dragOv) { dragOv = document.createElement('div'); dragOv.className = 'nx-dropov'; dragOv.textContent = 'Drop a PDF, a voice-over or a text file'; document.body.appendChild(dragOv); } });
addEventListener('dragleave', e => { if (e.relatedTarget == null && dragOv) { dragOv.remove(); dragOv = null; } });
addEventListener('drop', e => { if (dragOv) { dragOv.remove(); dragOv = null; } if (!P || editModeOpen || !e.dataTransfer?.files?.length) return; e.preventDefault(); [...e.dataTransfer.files].forEach(addFile); });
addEventListener('paste', e => {
  if (!P || editModeOpen || studioFrames().length || genFor(P.id)) return;
  const a = document.activeElement; if (a && (a.isContentEditable || /^(INPUT|TEXTAREA)$/.test(a.tagName))) return;
  const tx = e.clipboardData?.getData('text'); if (!tx || !tx.trim()) return;
  e.preventDefault(); saveScriptSoon((P.script ? P.script.replace(/\s*$/, '\n\n') : '') + tx); flushScript(); S.sedit = true; render();
});
addEventListener('keydown', e => {
  if (!P || editModeOpen) return;
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && !studioFrames().length && !genFor(P.id)) { const b = q1('[data-gen]'); if (b && !b.disabled) { e.preventDefault(); startGen(); } }
});

/* ---------------- generating, never blocking (B10) ---------------- */
async function pollGen(pid) {
  while (S.gen && S.gen.pid === pid) {
    await new Promise(r => setTimeout(r, 2500));
    if (!S.gen || S.gen.pid !== pid) break;
    try { const s = await _api0(`/api/projects/${pid}/progress`); if (s && s.state === 'running') { S.gen.msg = s.msg || S.gen.msg; S.gen.written = s.written || 0; if (P?.id === pid && !editModeOpen) { updateDock(); const gm = q1('#nxGenMsg'); if (gm) gm.textContent = S.gen.msg || ''; const gh = q1('#nxGenHead'); if (gh && S.gen.written) gh.textContent = `${S.gen.written} frame${S.gen.written === 1 ? '' : 's'} written…`; } } } catch (_) {}
  }
}
function lookPayload(sb) { let lk; try { lk = getLook(); } catch (_) { lk = null; } return { ...(P.look || {}), ...(lk || {}), sb_import: sb }; }
async function startGen() {
  await flushScript();
  if (pdfOn()) return genPdf(false);
  return genScript();
}
async function genScript(again = false) {
  const pid = P.id, n0 = 0;
  const tok = S.gen = { pid, kind: 'script', n0, count: Math.max(3, estFrames() || 6), msg: 'Writing the storyboard…', again };
  selectedFrameId = null; S.phSel = 0; render(); pollGen(pid);
  try {
    const r = await api(`/api/projects/${pid}/storyboard`, { method: 'POST', body: JSON.stringify({ script: P.script || '', look: lookPayload('script'), notes: '' }) });
    if (tok.stopped || r.stopped) return;
    S.gen = null;
    if (P?.id === pid) { P = r; P.look = normLook(P.look); frameVer = {}; frameHistInit(); selectedFrameId = studioFrames()[0]?.id || null; S.phSel = null; render(); }
    loadList();
    if (r.background) { if (P?.id === pid) watchBackground(); toast('The storyboard is written. Frames finish one by one.'); }
    else toast(`All ${(r.spec?.frames || []).length} frames are generated`);
  } catch (e) { if (tok.stopped) return; S.gen = null; if (P?.id === pid) render(); toast(e.message || String(e), { err: true }); }
}
async function genPdf(all) {
  const pid = P.id;
  let total = 0, last = null;
  for (let round = 0; round < (all ? 48 : 1); round++) {
    const n0 = (P?.id === pid ? studioFrames().length : 0);
    const tok = S.gen = { pid, kind: 'pdf', n0, count: 10, msg: 'Reading the storyboard PDF…', all };
    if (P?.id === pid && !editModeOpen) { if (!selectedFrameId) S.phSel = 0; render(); }
    pollGen(pid);
    try {
      last = await api(`/api/projects/${pid}/storyboard-pdf/batch`, { method: 'POST', body: JSON.stringify({ script: P?.id === pid ? (P.script || '') : '', look: lookPayload('pdf'), notes: P?.id === pid ? tkPdfNote() : '', batch_size: 10, finish_all: false }) });
    } catch (e) { if (tok.stopped) return; S.gen = null; if (P?.id === pid) render(); toast(e.message || String(e), { err: true }); loadList(); return; }
    if (tok.stopped || last.stopped) return;
    const added = last.frames_added || 0; total += added;
    S.gen = null;
    if (P?.id === pid) { const wasEmpty = !studioFrames().length; P = last; P.look = normLook(P.look); frameVer = {}; frameHistInit(); if (wasEmpty || !selectedFrameId) selectedFrameId = studioFrames()[n0]?.id || studioFrames()[0]?.id; S.phSel = null; if (!editModeOpen) render(); }
    if (!added || last.spec?.pdf_done) break;
  }
  loadList();
  const n = (last?.spec?.frames || []).length;
  if (!total) toast(last?.spec?.pdf_done ? `All ${n} frames are made` : 'No more graphic frames in the storyboard');
  else if (all || last?.spec?.pdf_done) toast(`All ${n} frames are generated`);
  else toast(n === total ? `First ${total} frames are generated` : `${total} more frames are generated`);
}
async function fillPictures(redo) {
  const pid = P.id;
  S.gen = { pid, kind: 'pictures', n0: studioFrames().length, count: 0, msg: redo ? 'Making the generated pictures again…' : 'Making the missing pictures…' };
  updateDock(); render();
  try {
    const r = await api(`/api/projects/${pid}/assets/fill`, { method: 'POST', body: JSON.stringify({ redo: !!redo }) });
    S.gen = null;
    if (P?.id === pid) { P = r; P.look = normLook(P.look); frameVer = {}; render(); }
    const n = Object.keys(r.assets?.filled || {}).length;
    toast(n ? `${n} picture${n === 1 ? '' : 's'} ${redo ? 'made again' : 'made'}` : 'No pictures were made');
  } catch (e) { S.gen = null; if (P?.id === pid) render(); toast(e.message || String(e), { err: true }); }
}

/* ---------------- frames page (B11) ---------------- */
function frameType(fr) {
  const m = String(fr?.mode || '').toLowerCase(), t = String(fr?.type || '').toLowerCase();
  if (isZ1Hindi()) return t === 'title' || t === 'word' ? 'Big word' : 'Scene';
  if (/^ost|bigword|big_word|punch|word$/.test(m) || /bigword|big_word|punch/.test(t)) return 'Big word';
  if (/fss|full/.test(m)) return 'Full screen';
  if (/osa|anchor|side|main|blur|tos/.test(m)) return 'Beside presenter';
  if (typeof presenterSlotOf === 'function' && presenterSlotOf(fr)) return 'Beside presenter';
  if (P?.theme === 'varsity-english') return 'Beside presenter';
  if (/scene/.test(t)) return 'Scene';
  return 'Full screen';
}
function items() {
  const fs = studioFrames().map((f, i) => ({ f, i }));
  if (genFor(P.id) && S.gen.kind !== 'pictures') {
    const base = S.gen.kind === 'script' ? 0 : fs.length;
    const ph = Array.from({ length: S.gen.count }, (_, k) => ({ ph: true, i: base + k, k }));
    return S.gen.kind === 'script' ? ph : fs.concat(ph);
  }
  return fs;
}
function groups(its) {
  const frames = studioFrames();
  if (tkKit() && frames.some(f => Array.isArray(f.lines))) {
    if (!scriptOn() && pdfOn() && S.pdfLines?.pid !== P.id) tkPdfLoad().then(() => { if (P && !editModeOpen) render(); });
    if (tkLines().list.length) return tkGroups(its);
  }
  const out = new Map(its.map(x => [x.ph ? 'ph' + x.k : x.f.id, { x, lines: [] }]));
  const ids = frames.map(f => f.id);
  const segs = episodeTranscript?.segments;
  let kind = 'script';
  if (segs?.length && (pdfOn() || !scriptOn())) {
    kind = 'transcript';
    let prev = ids[0];
    segs.forEach(s => { const fid = frameIdForSegment(s, frames, P.storyboard) || prev; prev = fid; const g = out.get(fid); if (g) g.lines.push({ t: Number(s.start), text: (s.text || '').trim() }); });
  } else if (scriptOn()) {
    const sa = assignScriptRanges(P.script, frames, P.storyboard);
    const lines = scriptLines(P.script); let cum = 0, prev = ids[0];
    lines.forEach((ln, i) => { const w = words(ln); const t = cum / 2.6; cum += w; if (!ln.trim()) return; const fid = sa.lineToFrame[i] || prev; prev = fid; const g = out.get(fid); if (g) g.lines.push({ t, text: ln.trim() }); });
  } else if ((P.storyboard || '').trim()) {
    kind = 'storyboard';
    (P.storyboard || '').split('\n').map(l => l.trim()).filter(l => l && !/^(SB\s|Look:|Totals:|#)/i.test(l)).forEach(l => { const fid = storyboardLineFrameId(l) || frameIdForTime(parseTimeFromSb(l), frames, P.storyboard); const g = out.get(fid); if (g) g.lines.push({ t: parseTimeFromSb(l), text: l.replace(/\s*(→|->)\s*\S+.*$/, '') }); });
  }
  return { kind, list: [...out.values()] };
}
function frameTimes(gl) {
  const st = gl.map(g => g.lines[0]?.t ?? (g.x.f ? frameTimestampSec(g.x.f.id, P.storyboard) : null));
  return st.map((s, i) => ({ s, e: st.slice(i + 1).find(v => v != null) ?? (gl[i].lines.length ? gl[i].lines[gl[i].lines.length - 1].t + 4 : null) }));
}
function selIndex(its) {
  if (S.phSel != null) { const k = its.findIndex(x => x.ph && x.k === S.phSel); if (k >= 0) return k; }
  const k = its.findIndex(x => x.f && x.f.id === selectedFrameId);
  return k >= 0 ? k : 0;
}
function editTip() {
  const c = chOfP().id;
  return c === 'zo' ? 'Edit the components of each layer (compare, chart, positions…)' : c === 'zero1' ? 'Move or resize the character, props and text, or describe a change for the whole frame' : 'Change layers, apply prompts, or switch presenter / full-screen layout';
}
function exportSplit() {
  return `<div class="nx-split"><button class="nx-btn ghost" data-expall>${I('download')}Export all</button><button class="nx-btn ghost car" data-expmenu aria-label="Export options" data-tip="Export options">${I('down')}</button></div>`;
}
function framesView() {
  const m = main();
  const its = items(), si = selIndex(its), cur = its[si];
  if (cur?.f) { selectedFrameId = cur.f.id; S.phSel = null; } else if (cur?.ph) S.phSel = cur.k;
  const G = groups(its), times = G.tk ? tkTimes(G, its) : frameTimes(G.list);
  const nLines = G.list.reduce((n, g) => n + g.lines.length, 0);
  const head = G.kind === 'transcript' ? 'VO transcript' : G.kind === 'script' ? 'Voiceover script' : 'Storyboard';
  const ver = id => frameVer[id] || 0;
  const thumb = (x, w = 320) => x.f ? `<img loading="lazy" alt="" src="${thumbUrl(P.id, x.f.id, ver(x.f.id) + '_' + Math.round(P.updated_at || 0), w)}" onerror="this.style.visibility='hidden'">` : '';
  const grp = (g, i) => { if (g.x.todo) return tkTodoHTML(g); if (G.tk) i = its.indexOf(g.x); const x = g.x, on = i === si; return `<div class="nx-grp${on ? ' on' : ''}${x.ph ? ' todo' : ''}${x.f?.tk_from ? ' nx-tkf' : ''}" data-pick="${i}"><div class="nx-gh"><span class="nx-gth${x.ph ? ' nx-shim' : ''}">${thumb(x, 160)}</span><b>Frame ${x.i + 1}</b>${x.ph ? '<span class="nx-gt dash">To generate</span>' : `<span class="nx-gt">${E(frameType(x.f))}</span>`}</div>${g.lines.map(l => `<p class="nx-ln"><time>${l.t != null ? mmss(l.t) : ''}</time><span>${E(l.text)}</span></p>`).join('')}</div>`; };
  const pdfRow = pdfOn() ? `<div class="nx-src"><span class="nx-pdfic">${PDFIC}</span><div class="tx"><b>${E((P.storyboard_pdf_name || P.look?.storyboard_pdf_name || 'Storyboard').replace(/\.pdf$/i, ''))}</b><small>Storyboard PDF</small></div><button class="nx-ib" data-repdf data-tip="Replace the storyboard PDF" class="tip-l">${I('pencil')}</button></div>` : '';
  const leftOn = G.kind !== 'storyboard' || nLines || pdfOn();
  const cap = cur ? (() => { const tm = times[si] || {}; const range = tm.s != null ? `${mmss(tm.s)}${tm.e != null ? '–' + mmss(tm.e) : ''}` : ''; const note = cur.f ? sbForFrame(cur.f.id, P.storyboard) : ''; return `<b>Frame ${cur.i + 1}</b><span>${[range, cur.f ? frameType(cur.f) : 'To generate'].filter(Boolean).join(' · ')}</span>${note && !/^No storyboard line/.test(note) ? `<span class="nx-note" data-tip="${E(note.slice(0, 420))}">${I('info')}</span>` : ''}<span class="of">${si + 1} of ${its.length}</span>`; })() : '';
  const bigInner = !cur ? '' : cur.ph ? (genFor(P.id) ? `<div class="nx-ph0 nx-loading"><span class="nx-spin" aria-hidden="true"></span><b id="nxGenHead">${S.gen.kind === 'script' && !S.gen.written ? 'Writing the storyboard…' : `Making frame ${cur.i + 1}…`}</b><span id="nxGenMsg">${E(S.gen.msg || '')}</span><small>This can take a few minutes. You can keep working; frames appear here as they are ready.</small><button class="nx-btn ghost" data-stopgen style="margin-top:6px">${I('x')}Stop generating</button></div>` : `<div class="nx-ph0"><b>This frame isn't generated yet</b>Click <i>Generate next 10 frames</i> below to see it here.</div>`) : `<iframe id="nxBigFr" title="Frame ${cur.i + 1}" src="/preview/${P.id}/${encodeURIComponent(cur.f.id)}?v=${ver(cur.f.id)}"></iframe>`;
  const stage = S.strip === 'grid'
    ? `<div class="nx-allg">${its.map((x, i) => `<button class="nx-gcard${i === si ? ' on' : ''}" data-pick="${i}"><span class="im${x.ph ? ' nx-shim' : ''}">${thumb(x)}</span><span><b>Frame ${x.i + 1}</b> · ${x.f ? E(frameType(x.f)) : 'To generate'}</span></button>`).join('')}</div>`
    : `<div class="nx-bigw" id="nxBigW"><div class="nx-col"><div class="nx-tools" id="nxTools"><button class="nx-ib" id="nxUndo" data-undo data-tip="Undo">${I('undo')}</button><button class="nx-ib" id="nxRedo" data-redo data-tip="Redo">${I('redo')}</button><span class="sep"></span><button class="nx-btn dark" data-edit ${cur?.f ? '' : 'disabled'} data-tip="${E(editTip())}">${I('pencil')}Edit layers</button><span class="sep"></span><button class="nx-ib" data-zoom="-1" data-tip="Zoom out">${I('minus')}</button><button class="fit" data-zoom="0" data-tip="Fit the frame">Fit</button><button class="nx-ib" data-zoom="1" data-tip="Zoom in">${I('plus')}</button></div>
       ${S.banner ? `<div class="nx-banner ${S.banner.cls}">${E(S.banner.text)}</div>` : ''}
       <div class="nx-big" id="nxBig">${bigInner}</div><div class="nx-cap" id="nxCap">${cap}</div></div></div>
       <button class="nx-nav l" data-step="-1" ${si > 0 ? '' : 'disabled'} aria-label="Previous frame" data-tip="Previous frame">${I('back')}</button><button class="nx-nav r" data-step="1" ${si < its.length - 1 ? '' : 'disabled'} aria-label="Next frame" data-tip="Next frame">${I('chev')}</button>`;
  m.innerHTML = `<div class="nx-top">${topLeftHTML()}<span class="nx-sp"></span><div class="nx-topr" style="display:flex;gap:8px;align-items:center">${exportSplit()}${EMBED ? `<div class="nx-split"><button class="nx-btn primary" id="laSendBtn" data-layers ${studioFrames().length ? '' : 'disabled'} data-tip="LA Studio turns every frame into a layered PSD" class="tip-l">Make Layers</button><button class="nx-btn primary car" data-layersmenu ${studioFrames().length ? '' : 'disabled'} aria-label="Make layers for some frames" data-tip="Only some frames" class="tip-l">${I('down')}</button></div>` : ''}<button class="nx-ib" data-vmore aria-label="More" data-tip="More" class="tip-l">${I('more')}</button></div></div>
  <div class="nx-row" style="--lw:${S.lw}px">
    ${leftOn ? `<div class="nx-pan nx-left"><div class="nx-ph"><b>${head}</b><small>${nLines} lines · ${its.length} frames</small><button class="nx-ib" data-escript data-tip="Edit script">${I('pencil')}</button></div>${pdfRow}<div class="nx-lines" id="nxLines">${G.list.map(grp).join('')}</div><span class="nx-resz" data-resz></span></div>` : ''}
    <div class="nx-pan nx-mid"><div class="nx-stage"><div class="nx-vsw"><div class="nx-view"><button class="${S.strip === 'strip' ? 'on' : ''}" data-strip="strip" data-tip="One frame">${I('strip')}</button><button class="${S.strip === 'grid' ? 'on' : ''}" data-strip="grid" data-tip="All frames" class="tip-l">${I('grid')}</button></div></div>${stage}</div>
    ${S.strip === 'grid' ? '' : `<div class="nx-film" id="nxFilm">${its.map((x, i) => `<button class="nx-fth${i === si ? ' on' : ''}${x.ph ? ' nx-shim' : ''}" data-pick="${i}" aria-label="Frame ${x.i + 1}">${thumb(x, 280)}<i>${x.i + 1}</i></button>`).join('')}</div>`}</div>
  </div>
  <div class="nx-dock" id="nxDock"></div>
  <input type="file" id="nxPdfIn" accept="application/pdf,.pdf" hidden>`;
  bindTop(m);
  updateDock();
  nxUndoBar();
  fitBig();
  q1('.nx-grp.on')?.scrollIntoView({ block: 'nearest' });
  q1('.nx-fth.on')?.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  m.onclick = e => {
    const t = e.target;
    if (t.closest('[data-stopgen]')) return stopGen();
    const tp = t.closest('[data-tkpick]'); if (tp) { const [a, b] = (tp.dataset.tkpick || '').split('-').map(Number); return tkPicker(isNaN(a) ? null : { a, b }); }
    const tsk = t.closest('[data-tkskip]'); if (tsk) { const [a, b] = tsk.dataset.tkskip.split('-').map(Number); return tkSetSkip(a, b, true); }
    const tus = t.closest('[data-tkunskip]'); if (tus) { const [a, b] = tus.dataset.tkunskip.split('-').map(Number); return tkSetSkip(a, b, false); }
    const tex = t.closest('[data-tkexp]'); if (tex) { const a = +tex.dataset.tkexp; if (tkOpen.has(a)) tkOpen.delete(a); else tkOpen.add(a); return render(); }
    const pk = t.closest('[data-pick]'); if (pk) return pick(+pk.dataset.pick);
    const st = t.closest('[data-step]'); if (st) return pick(si + +st.dataset.step);
    const sw = t.closest('[data-strip]'); if (sw) { S.strip = sw.dataset.strip; ls.set('nx.strip', S.strip); return render(); }
    const z = t.closest('[data-zoom]'); if (z) { const d = +z.dataset.zoom; S.zoom = d ? Math.max(0.4, Math.min(2.5, S.zoom * (d > 0 ? 1.2 : 1 / 1.2))) : 1; return fitBig(); }
    if (t.closest('[data-edit]')) return cur?.f && openEditMode(cur.f.id);
    if (t.closest('[data-undo]')) return undoFrameEdit();
    if (t.closest('[data-redo]')) return redoFrameEdit();
    if (t.closest('[data-escript]')) return editScriptWin();
    if (t.closest('[data-repdf]')) return q1('#nxPdfIn').click();
    if (t.closest('[data-expall]')) return exp();
    if (t.closest('[data-expmenu]')) return menu(t.closest('[data-expmenu]'), [{ label: 'Export this frame', icon: 'frame', disabled: !cur?.f, run: () => expFrame() }, { label: 'Export all frames', icon: 'frames', run: () => exp() }]);
    if (t.closest('[data-layers]')) return makeLayers();
    if (t.closest('[data-layersmenu]')) { const n = studioFrames().length; return menu(t.closest('[data-layersmenu]'), [{ label: cur?.f ? `This frame (Frame ${cur.i + 1})` : 'This frame', icon: 'frame', disabled: !cur?.f, run: () => makeLayers([String(cur.f.id)]) }, { label: 'Choose frames…', icon: 'check', run: chooseLayerFrames }, '-', { label: `All ${n} frames`, icon: 'frames', run: () => makeLayers() }]); }
    if (t.closest('[data-vmore]')) return videoMenu(t.closest('[data-vmore]'));
  };
  q1('#nxPdfIn').onchange = async e => { const f = e.target.files[0]; e.target.value = ''; if (f) { if (!/pdf$/i.test(f.type) && !/\.pdf$/i.test(f.name)) return toast("That file couldn't be used (PDF only)", { err: true }); await addFile(f); } };
  const rz = q1('[data-resz]');
  if (rz) rz.onpointerdown = e => {
    e.preventDefault(); const row = q1('.nx-row'), x0 = e.clientX, w0 = S.lw;
    const mv = ev => { S.lw = Math.max(260, Math.min(560, w0 + ev.clientX - x0)); row.style.setProperty('--lw', S.lw + 'px'); fitBig(); };
    const up = () => { removeEventListener('pointermove', mv); removeEventListener('pointerup', up); ls.set('nx.lw', S.lw); };
    addEventListener('pointermove', mv); addEventListener('pointerup', up);
  };
  if (P.has_episode_transcript && !episodeTranscript?.segments && !S.trBusy) { S.trBusy = true; api(`/api/projects/${P.id}/episode-transcript`).then(tr => { episodeTranscript = tr; S.trBusy = false; if (P && !editModeOpen && studioFrames().length) render(); }).catch(() => { S.trBusy = false; }); }
  function pick(i) {
    const x = its[Math.max(0, Math.min(its.length - 1, i))]; if (!x) return;
    if (x.f) { selectedFrameId = x.f.id; S.phSel = null; } else S.phSel = x.k;
    S.banner = null; render();
  }
}
function fitBig() {
  const wrap = q1('#nxBigW'), big = q1('#nxBig'); if (!wrap || !big) return;
  const { w, h } = themeCanvas(P.theme);
  const extra = ['#nxTools', '.nx-banner', '#nxCap'].reduce((n, s) => { const el = wrap.querySelector(s); return n + (el ? el.offsetHeight + 12 : 0); }, 0);
  const W = wrap.clientWidth, H = wrap.clientHeight - extra;
  if (!W || H <= 0) return;
  const s = Math.min(W / w, H / h) * S.zoom;
  big.style.width = Math.round(w * s) + 'px'; big.style.height = Math.round(h * s) + 'px';
  const f = q1('#nxBigFr'); if (f) { f.style.width = w + 'px'; f.style.height = h + 'px'; f.style.transform = `scale(${s})`; }
  const cap = q1('#nxCap'); if (cap) cap.style.width = Math.min(W, Math.round(w * s)) + 'px';
  wrap.style.overflow = S.zoom > 1 ? 'auto' : 'hidden';
}
addEventListener('resize', () => { if (P && !editModeOpen) fitBig(); });
function updateDock() {
  const d = q1('#nxDock'); if (!d || !P) return;
  const n = studioFrames().length, pdf = pdfOn(), z1 = isZ1Hindi(), todo = specTodoCount(), gens = specGenCount();
  const g = genFor(P.id) ? S.gen : null;
  let tx, btns = '';
  if (g) {
    if (g.kind === 'pictures') tx = g.msg;
    else if (g.kind === 'script') tx = g.written ? `Generating frames… ${g.written} written` : (g.msg || 'Generating frames…');
    else if (g.kind === 'rest') tx = 'Generating frames for the lines without a toolkit frame…';
    else tx = `Generating frames ${g.n0 + 1}–${g.n0 + g.count}…`;
    tx += '<span class="nx-dots"><i></i><i></i><i></i></span>';
    if (g.kind !== 'pictures' && g.msg && g.kind === 'pdf') tx += ` <span class="nx-dim">· ${E(g.msg)}</span>`;
    if (g.kind !== 'pictures') btns += `<button class="nx-btn ghost" data-stopgen data-tip="Stop: nothing from this run is kept">${I('x')}Stop</button>`;
  } else if (S.bg) tx = E(S.bg) + '<span class="nx-dots"><i></i><i></i><i></i></span>';
  else if (tkKit() && tkFrames().length) { const k = tkFrames().length; tx = `${n} frame${n === 1 ? '' : 's'} · ${k === n ? 'all' : k} from the toolkit`; }
  else if (pdf) tx = P.spec?.pdf_done ? `All ${n} frames made` : `${n} frame${n === 1 ? '' : 's'} generated`;
  else tx = `${n} frame${n === 1 ? '' : 's'} · made from your script`;
  if (!g) {
    if (todo) btns += `<button class="nx-btn plain" data-fill>${z1 ? `Generate ${todo} picture${todo > 1 ? 's' : ''}` : `Make ${todo} missing picture${todo > 1 ? 's' : ''}`}</button>`;
    else if (gens) btns += `<button class="nx-btn plain" data-redo-pics>${z1 ? `Redo ${gens} generated frame${gens > 1 ? 's' : ''}` : `Redo ${gens} generated picture${gens > 1 ? 's' : ''}`}</button>`;
    if (tkKit()) btns += `<button class="nx-btn ghost" data-tkpick>${I('frames')}Pick from toolkit</button>`;
    if (pdf && pdfOn() && !P.spec?.pdf_done) { const tkn = tkKit() && tkFrames().length; btns += `<button class="nx-btn ghost" data-genall${tkn ? ' data-tip="Claude makes frames for every part of the storyboard without a toolkit frame"' : ''}>${tkn ? 'Generate all the rest' : 'Generate all'}</button><button class="nx-btn primary" data-gennext>Generate next 10 frames</button>`; }
    else if (!pdf && tkKit() && tkFrames().length) { const fr = tkFreeLines(); const again = studioFrames().length > tkFrames().length; btns += `<button class="nx-btn ${again ? 'ghost' : 'primary'}" data-tkrest ${fr ? '' : 'disabled'} data-tip="Claude writes frames only for the lines without a toolkit frame">${again ? 'Regenerate the rest' : `Generate the rest${fr ? ` (${fr} line${fr === 1 ? '' : 's'})` : ''}`}</button>`; }
    else if (!pdf) btns += `<button class="nx-btn ghost" data-regenall>Regenerate all</button>`;
  }
  d.innerHTML = `<span class="tx">${tx}</span>${btns}`;
  d.onclick = e => {
    const t = e.target;
    if (t.closest('[data-stopgen]')) return stopGen();
    if (t.closest('[data-tkpick]')) return tkPicker();
    if (t.closest('[data-tkrest]')) return genRest();
    if (t.closest('[data-gennext]')) return genPdf(false);
    if (t.closest('[data-genall]')) return genPdf(true);
    if (t.closest('[data-fill]')) return fillPictures(false);
    if (t.closest('[data-redo-pics]')) return fillPictures(true);
    if (t.closest('[data-regenall]')) win({ title: 'Regenerate all frames?', text: 'Every frame is made again from the script. Changes made to the frames are replaced.', ok: 'Regenerate all', onOk: () => { genScript(true); } });
  };
}
function nxUndoBar() {
  const u = q1('#nxUndo'), r = q1('#nxRedo'), fid = selectedFrameId;
  if (u) u.disabled = !(frameHist[fid] || []).length || frameHistBusy;
  if (r) r.disabled = !(frameRedo[fid] || []).length || frameHistBusy;
  const eu = q1('#nxEUndo'), er = q1('#nxERedo');
  if (eu) eu.disabled = !(frameHist[fid] || []).length || frameHistBusy;
  if (er) er.disabled = !(frameRedo[fid] || []).length || frameHistBusy;
  const nu = (frameHist[fid] || []).length, nr = (frameRedo[fid] || []).length;
  [u, eu].forEach(b => { if (b) { b.dataset.tip = nu ? `Undo the last change (${nu} of 5 left) · ⌘Z` : 'Undo: nothing to undo on this frame yet'; b.querySelector('.nx-uc')?.remove(); if (nu) b.insertAdjacentHTML('beforeend', `<span class="nx-uc">${nu}</span>`); } });
  [r, er].forEach(b => { if (b) b.dataset.tip = nr ? `Redo (${nr}) · ⇧⌘Z` : 'Redo'; });
  const rs = q1('#nxEReset'); if (rs) rs.disabled = !(frameBase[fid] !== undefined && frameBase[fid] !== frameSaved[fid]) || frameHistBusy;
  const ra = q1('[data-resetall]'); if (ra) ra.disabled = frameHistBusy || !changedFrames().length;
}
window.nxUndoBar = nxUndoBar;
async function putFrames(map, note) {
  frameHistBusy = true; renderUndoBar();
  try {
    const sp = { ...P.spec, frames: P.spec.frames.map(f => map[f.id] !== undefined ? map[f.id] : f) };
    P = await api('/api/projects/' + P.id, { method: 'PUT', body: JSON.stringify({ spec: sp, note }) }); P.look = normLook(P.look);
    Object.keys(map).forEach(id => { const now = P.spec.frames.find(f => String(f.id) === String(id)); if (now) frameSaved[now.id] = JSON.stringify(now); bumpFrame(now ? now.id : id); });
    if (editModeOpen) { refreshEditCanvas(); renderCanvasLayerList(); buildEditFrameStrip(); renderFrameModeSwitch?.(); } else render();
  } finally { frameHistBusy = false; renderUndoBar(); }
}
const changedFrames = () => (P?.spec?.frames || []).map(f => f.id).filter(id => frameBase[id] !== undefined && frameBase[id] !== frameSaved[id]);
async function resetFrame() {
  const fid = selectedFrameId; if (!fid || frameBase[fid] === undefined || frameBase[fid] === frameSaved[fid] || frameHistBusy) return;
  const cur = frameSaved[fid];
  try { await putFrames({ [fid]: JSON.parse(frameBase[fid]) }, 'reset ' + fid); } catch (e) { return toast(e.message || String(e), { err: true }); }
  const h = frameHist[fid] = frameHist[fid] || []; h.push(cur); if (h.length > FRAME_UNDO_MAX) h.shift(); delete frameRedo[fid]; renderUndoBar();
  toast('Frame reverted to its original state', { undo: () => undoFrameEdit() });
}
async function resetAll() {
  if (frameHistBusy) return;
  const ids = changedFrames();
  if (!ids.length) return toast('Every frame is already in its original state');
  const prev = Object.fromEntries(ids.map(id => [id, frameSaved[id]]));
  try { await putFrames(Object.fromEntries(ids.map(id => [id, JSON.parse(frameBase[id])])), 'reset all frames'); } catch (e) { return toast(e.message || String(e), { err: true }); }
  ids.forEach(id => { const h = frameHist[id] = frameHist[id] || []; h.push(prev[id]); if (h.length > FRAME_UNDO_MAX) h.shift(); delete frameRedo[id]; });
  renderUndoBar();
  toast(`${ids.length} frame${ids.length === 1 ? '' : 's'} reverted to the original state`, { undo: async () => { await putFrames(Object.fromEntries(ids.map(id => [id, JSON.parse(prev[id])])), 'undo reset all'); ids.forEach(id => frameHist[id]?.pop()); renderUndoBar(); } });
}
function editScriptWin() {
  win({
    title: 'Edit script', ok: 'Save', wide: true, text: 'Changes apply when you regenerate storyboard + frames.',
    body: `<textarea class="nx-field" id="nxEsc" style="min-height:180px;height:36vh;max-height:300px">${E(P.script || '')}</textarea>`,
    onOk: async m => { saveScriptSoon(m.querySelector('#nxEsc').value); await flushScript(); toast('Script is saved'); render(); },
  });
}
function chooseLayerFrames() {
  const fs = studioFrames(), pick = new Set(selectedFrameId ? [String(selectedFrameId)] : []);
  const ver = id => frameVer[id] || 0;
  const w = win({
    title: 'Make layers for some frames', ok: 'Make Layers', wide: true, text: 'Pick the frames LA Studio should turn into layered PSDs.',
    body: `<div class="nx-lpick-h"><button class="nx-tbtn" data-lall>Select all</button><span class="nx-dim" data-lcount></span></div><div class="nx-lpick">${fs.map((f, i) => `<button type="button" class="nx-lpk${pick.has(String(f.id)) ? ' on' : ''}" data-lid="${E(f.id)}"><span class="im"><img loading="lazy" alt="" src="${thumbUrl(P.id, f.id, ver(f.id) + '_' + Math.round(P.updated_at || 0), 280)}"><i class="nx-ck">${I('check')}</i></span><span>Frame ${i + 1}</span></button>`).join('')}</div>`,
    onOk: async () => { if (!pick.size) { toast('Pick at least one frame', { err: true }); return false; } const order = fs.map(f => String(f.id)).filter(id => pick.has(id)); setTimeout(() => makeLayers(order), 0); },
  });
  const sync = () => {
    w.el.querySelectorAll('[data-lid]').forEach(b => b.classList.toggle('on', pick.has(b.dataset.lid)));
    w.el.querySelector('[data-lcount]').textContent = `${pick.size} of ${fs.length} picked`;
    w.el.querySelector('[data-lall]').textContent = pick.size === fs.length ? 'Deselect all' : 'Select all';
    const ok = w.el.querySelector('[data-ok]'); ok.textContent = pick.size === fs.length ? 'Make Layers for all frames' : `Make Layers for ${pick.size} frame${pick.size === 1 ? '' : 's'}`; ok.disabled = !pick.size;
  };
  w.el.querySelector('.nx-wb').onclick = e => {
    const b = e.target.closest('[data-lid]'); if (b) { pick.has(b.dataset.lid) ? pick.delete(b.dataset.lid) : pick.add(b.dataset.lid); return sync(); }
    if (e.target.closest('[data-lall]')) { if (pick.size === fs.length) pick.clear(); else fs.forEach(f => pick.add(String(f.id))); sync(); }
  };
  sync();
}
async function makeLayers(only) {
  const fr = studioFrames(); if (!fr.length) return;
  const btn = q1('#laSendBtn');
  const label = t => { if (btn) btn.textContent = t; };
  if (btn) btn.disabled = true;
  const ids = (Array.isArray(only) && only.length ? only : P.spec.frames.map(f => String(f.id))), stem = laSlug(P.name);
  try {
    if (P.theme === 'zero1-hindi-graphics') {   // characters in the scene plates get their own layer + a clean background
      label('Separating characters…');
      try {
        const r = await api(`/api/projects/${P.id}/z1-split`, { method: 'POST', body: JSON.stringify({ ids }) });
        const why = [...Object.values(r.failed || {}), ...Object.values(r.kept || {})], bad = why.length;
        if (bad) toast(`${bad} picture${bad === 1 ? '' : 's'} could not be split (${String(why[0]).slice(0, 90)}); their characters stay part of the background layer.`);
      } catch (e) { toast('Characters could not be separated this time; they stay part of the background layer.'); }
    }
    const files = [];
    for (let i = 0; i < ids.length; i++) {
      label(`Preparing ${i + 1}/${ids.length}…`);
      const r = await fetch(`/api/projects/${P.id}/frames/${encodeURIComponent(ids[i])}/export.html`, { cache: 'no-store' });
      if (r.status === 404 || r.status === 400) continue;
      if (!r.ok) throw new Error(`Frame ${i + 1}: ${await r.text()}`);
      files.push(new File([await r.text()], `${stem}_${ids[i].replace(/[^\w.-]+/g, '_')}.html`, { type: 'text/html' }));
    }
    let csv = null; try { const r = await fetch(`/api/projects/${P.id}/storyboard-instructions.csv`); if (r.ok) csv = new File([await r.blob()], `${stem}_storyboard-instructions.csv`, { type: 'text/csv' }); } catch (_) {}
    label('Finding the project…');
    const la = await laEnsureProject(P);
    label('Sending to Layers…');
    await laPost('frames', { project: { id: P.id, name: P.name, theme: P.theme }, la, files, csv });
    try { await _api0(`/api/projects/${P.id}/sent-layers`, { method: 'POST' }); P.look = { ...P.look, sent_layers: Date.now() / 1000 }; } catch (_) {}
    toast(`${files.length} frame${files.length === 1 ? '' : 's'} sent to Layers. Each becomes a layered PSD.`);
    loadList();
    if (inProject()) laPost('stage', { stage: 'psd' }).catch(() => {});
  } catch (e) { toast(e.message || String(e), { err: true }); }
  finally { label('Make Layers'); if (btn) btn.disabled = false; }
}
addEventListener('keydown', e => {
  if (!P || editModeOpen || !studioFrames().length) return;
  const a = document.activeElement; if (a && (a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName))) return;
  if (q1('.nx-modal')) return;
  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { const b = q1(`[data-step="${e.key === 'ArrowLeft' ? -1 : 1}"]`); if (b && !b.disabled) { e.preventDefault(); b.click(); } }
});

/* ---------------- Edit layers (B12–B15): the existing edit mode, laid out as designed ---------------- */
const LT = { text: ['text', 'Text'], title: ['text', 'Text'], heading: ['text', 'Text'], subtitle: ['text', 'Text'], term: ['text', 'Text'], definition: ['text', 'Text'], point: ['text', 'Text'], label: ['text', 'Text'], pill: ['text', 'Text'], step: ['text', 'Text'], tile: ['text', 'Text'], lead: ['text', 'Text'],
  img: ['picture', 'Picture'], image: ['picture', 'Picture'], asset: ['picture', 'Picture'], hero: ['picture', 'Picture'], prop: ['picture', 'Picture'], picture: ['picture', 'Picture'],
  table: ['table', 'Table'], chart: ['chart', 'Chart'], bars: ['chart', 'Chart'], donut: ['chart', 'Chart'], person: ['person', 'Person'], char: ['person', 'Person'], card: ['block', 'Card'], cards: ['block', 'Cards'],
  html: ['block', 'Block'], drawing: ['shape', 'Drawing'], background: ['frame', 'Background'], decor: ['shape', 'Shape'], shape: ['shape', 'Shape'], box: ['shape', 'Shape'], dot: ['shape', 'Shape'], arrow: ['shape', 'Shape'], rect: ['shape', 'Shape'] };
function layerKind(label) {
  const m = String(label || '').match(/^\s*([A-Za-z_]+)(?:\s*\d+)?\s*(?::|·)\s*(.*)$/);
  let type = m ? m[1].toLowerCase() : '', name = m ? m[2] : String(label || '');
  if (/^asset:|^gen:|\.(png|jpe?g|svg|webp)$/i.test(name) && !LT[type]) type = 'picture';
  const k = LT[type] || (type ? ['block', type.charAt(0).toUpperCase() + type.slice(1)] : ['block', 'Layer']);
  name = name.replace(/^(asset:|gen:)/, '').replace(/\.(png|jpe?g|svg|webp)$/i, '').replace(/^.*\//, '') || k[1];
  return { icon: k[0], type: k[1], name };
}
const layerQueue = { p: Promise.resolve(), busy: new Set() };
function runQueued(key, fn) { layerQueue.busy.add(key); markBusy(); const p = layerQueue.p.then(fn, fn).finally(() => { layerQueue.busy.delete(key); markBusy(); }); layerQueue.p = p.catch(() => {}); return p; }
function markBusy() { $$('.nx-ls').forEach(s => s.classList.toggle('busy', layerQueue.busy.has(s.dataset.key))); }
let nxLayerBusy = 0;
let _setEditLoading = null;
const repFiles = {};
let _renderCanvasLayerList = null;
let rendering = false;
const nxRCL = function () {
  _renderCanvasLayerList();
  if (rendering) return;
  const list = q1('#canvasLayerList'); if (!list) return;
  const rows = $$('.canvas-layer-row', list).map(r => {
    const b = r.querySelector('.cl-actions button'); const a = b?.getAttribute('onclick') || '';
    const mm = a.match(/canvasLayerAction\((\d+),'edit'(?:,'((?:[^'\\]|\\.)*)')?\)/);
    return mm ? { idx: +mm[1], mfPath: mm[2] ? mm[2].replace(/\\'/g, "'").replace(/\\\\/g, '\\') : null, label: r.querySelector('.cl-name')?.getAttribute('title') || r.textContent, on: r.classList.contains('on') } : null;
  }).filter(Boolean);
  const tabN = q1('[data-etab="layers"] .nx-cnt'); if (tabN) tabN.textContent = rows.length;
  const frNow = studioFrames().find(x => x.id === selectedFrameId);
  const fixed = !!(frNow && typeof frNow.page === 'string' && frNow.page.trim());
  const kitLocked = !fixed && rows.some(r => r.mfPath === 'locked:kit');
  const tools = layerToolsHTML() + (fixed ? `<div class="nx-fixed">${I('check')}<span>Every layer of this frame can be edited.</span>${frNow.kit_frame ? `<button class="nx-tbtn" data-unfix data-tip="Undo making the layers editable: the kit draws this frame again">Back to kit version</button>` : ''}</div>`
    : kitLocked ? `<div class="nx-fixed lock">${I('lock')}<span>Layers with a lock are drawn by the kit.</span><button class="nx-tbtn" data-mkedit>Make all editable</button></div>` : '');
  if (!rows.length) { list.innerHTML = tools + `<div class="nx-lempty">${list.textContent.trim() ? E(list.textContent.trim()) : 'This frame has no layers to edit. Describe a change in Prompt, or regenerate it.'}</div>`; return; }
  const first = rows.find(r => !String(r.mfPath || '').startsWith('locked:'));
  if (first && !rows.some(r => r.on) && !selectedCanvasLayer && !S.noAutoPick) {
    rendering = true; try { selectedCanvasLayer = { idx: first.idx, mfPath: first.mfPath }; lastCanvasChipSig = ''; renderParentCanvasChips(lastCanvasLayers); syncIframeLayerSelect(); } finally { rendering = false; }
    first.on = true;
  }
  const fdoc = q1('#canvasEditFrame')?.contentDocument;
  const textOf = mf => { if (!mf || !/^html:/.test(mf) || !fdoc) return null; try { const el = fdoc.querySelector(`[data-mf-path="${CSS.escape(mf)}"]`); return el && el.classList.contains('studio-inline-text') ? el.innerText : null; } catch (_) { return null; } };
  const curF = studioFrames().find(x => x.id === selectedFrameId);
  const words = (isTkProject() || curF?.tk_from) ? rows.map(r => ({ r, tx: textOf(r.mfPath) })).filter(w => w.tx != null && w.tx.trim()) : [];
  const wordsHTML = words.length ? `<div class="nx-words"><span class="lab">Text on this frame</span>${words.map(w => `<textarea data-wtext data-mf="${E(w.r.mfPath)}" rows="${Math.min(4, w.tx.split('\n').length)}" aria-label="${E(layerKind(w.r.label).name)}">${E(w.tx)}</textarea>`).join('')}<small>Type to change the words · Enter saves · Shift+Enter for a new line</small></div>` : '';
  const LOCKED = { kit: 'Drawn by the kit. Make all layers editable to change it here, or describe the change in Prompt.', plate: 'The presenter photo: change it in Anchor frame.', decor: 'Kit decoration: move or remove it in Prompt.', background: 'The background of the frame.' };
  list.innerHTML = tools + wordsHTML + rows.map(r => {
    const k = layerKind(r.label), key = r.idx + '|' + (r.mfPath || ''), f = repFiles[key];
    const lk = /^locked:(.*)$/.exec(r.mfPath || '');
    if (lk) return `<div class="nx-ls locked${r.on ? ' open' : ''}" data-key="${E(key)}" data-idx="${r.idx}" data-mf="${E(r.mfPath)}">
      <div class="nx-lsh" data-open><span class="ty">${I(k.icon)}</span><span class="nm"><b>${E(k.type)}</b> · ${E(k.name)}</span><span class="nx-lk" aria-label="Locked">${I('lock')}</span></div>
      ${r.on ? `<div class="nx-lsb"><p class="nx-lkn">${E(LOCKED[lk[1]] || LOCKED.kit)}</p>${lk[1] === 'kit' ? '<button class="nx-tbtn" data-mkedit>Make all editable</button>' : ''}</div>` : ''}</div>`;
    const tx = r.on ? textOf(r.mfPath) : null;
    return `<div class="nx-ls${r.on ? ' open' : ''}${layerQueue.busy.has(key) ? ' busy' : ''}" data-key="${E(key)}" data-idx="${r.idx}" data-mf="${E(r.mfPath || '')}">
      <div class="nx-lsh" data-open><span class="ty">${I(k.icon)}</span><span class="nm"><b>${E(k.type)}</b> · ${E(k.name)}</span><button class="nx-ib" data-lcopy data-tip="Copy this layer (⌘C), then paste it into any frame (⌘V)" class="tip-l">${I('copy')}</button><button class="nx-ib nx-trash" data-ldel data-tip="Delete this layer" class="tip-l">${I('trash')}</button><svg class="i chev" viewBox="0 0 16 16">${IC.chev}</svg></div>
      ${r.on ? `<div class="nx-lsb">${tx != null ? `<span class="lab">Text</span><div class="nx-ai"><textarea data-ltext rows="${Math.min(4, tx.split('\n').length + 1)}" aria-label="Text">${E(tx)}</textarea><div class="row"><small>Enter to save · Shift+Enter for a new line</small><button class="nx-tbtn" data-ltextapply>Save</button></div></div>` : ''}<span class="lab">Edit with AI</span><div class="nx-ai"><textarea data-ai rows="2" aria-label="Edit with AI"></textarea><div class="row"><small>Enter to apply</small><button class="nx-tbtn off" data-aiapply>Apply</button></div></div>
        <span class="lab">Replace with an image</span><div class="nx-rep"><div class="nx-upl${f ? ' has' : ''}" data-upl><span class="tile">${f ? `<img src="${f.url}" alt=""><span class="rm" data-rmimg data-tip="Remove this image">${I('trash')}</span>` : I('upload')}</span><span class="tx"><b>${f ? E(f.file.name) : 'Upload or drop an image'}</b><small>${f ? 'Click to choose another' : 'PNG, JPG or SVG'}</small></span><input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" hidden data-repin></div>
        <div class="nx-ai"><textarea data-repnote rows="2" placeholder="Note (optional)" aria-label="Note"></textarea><div class="row"><button class="nx-tbtn${f ? '' : ' off'}" data-repapply>Apply</button></div></div></div></div>` : ''}</div>`;
  }).join('');
};
/* change a text layer's words right here (no AI, no cost): same save as double-clicking the text on the frame */
function layerText(L, val) {
  const v = (val ?? L.s?.querySelector('[data-ltext]')?.value ?? '').replace(/\s+$/, '');
  const el = q1('#canvasEditFrame')?.contentDocument?.querySelector(`[data-mf-path="${CSS.escape(L.mfPath || '')}"]`);
  if (!el || !v.trim()) return;
  el.innerText = v;
  patchFrameInline({ studio: 'inline', mfPath: L.mfPath, outer: el.outerHTML });
  toast('Text changed', { undo: () => undoFrameEdit() });
}
function layerOf(el) { const s = el.closest('.nx-ls'); return s ? { s, idx: +s.dataset.idx, mfPath: s.dataset.mf || null, key: s.dataset.key, label: s.querySelector('.nm')?.textContent || 'layer' } : null; }
async function layerAsk(L, text, file) {
  const fid = selectedFrameId;
  const opts = L.mfPath ? { mfPath: L.mfPath } : { itemIndex: L.idx };
  return runQueued(L.key, async () => {
    nxLayerBusy++;
    try {
      const r = await askFrame(fid, text || (file ? 'Replace with reference image' : ''), { ...opts, ...(file ? { itemReplace: true, refFile: file } : {}), quiet: true });
      if (r?.ok) { toast(file ? 'Layer replaced' : 'Layer changed', { undo: () => undoFrameEdit() }); if (file) { const f = repFiles[L.key]; if (f) URL.revokeObjectURL(f.url); delete repFiles[L.key]; renderCanvasLayerList(); } }
      else if (r) toast(r.error || 'That did not work', { err: true });
    } finally { nxLayerBusy--; }
  });
}
async function layerDelete(L) {
  if (!L) return;
  const name = (L.label || '').replace(/^[^·]*·\s*/, '');
  if (L.mfPath) await deleteMfPart(L.mfPath); else if (isKitTheme(P?.theme)) return toast('This layer cannot be removed on its own. Ask for it in Prompt.', { err: true }); else await deleteFrameItem(L.idx);
  selectedCanvasLayer = null; renderCanvasLayerList();
  try { q1('#canvasEditFrame')?.contentWindow?.studioBootLayers?.(); } catch (_) {}
  toast(`Removed "${name.trim().slice(0, 40)}"`, { undo: () => undoFrameEdit() });
}
const nxCLA = function (idx, action, mfPath = null) {
  const key = idx + '|' + (mfPath || '');
  if (action === 'copy') { const s = q1(`.nx-ls[data-key="${CSS.escape(key)}"]`); return copyLayer(s ? layerOf(s) : { idx, mfPath, key, label: 'layer' }); }
  if (action === 'delete') { const s = q1(`.nx-ls[data-key="${CSS.escape(key)}"]`); return layerDelete(s ? layerOf(s) : { idx, mfPath, key, label: 'layer' }); }
  selectCanvasLayer(idx, mfPath);
  setTab('layers');
  setTimeout(() => { const s = q1(`.nx-ls[data-key="${CSS.escape(key)}"]`); if (!s) return; s.scrollIntoView({ block: 'nearest' }); if (action === 'replace') s.querySelector('[data-repin]')?.click(); else s.querySelector('[data-ai]')?.focus(); }, 30);
};
function bindLayerPanel() {
  const list = q1('#canvasLayerList'); if (!list || list._nx) return; list._nx = true;
  list.addEventListener('click', e => {
    if (e.target.closest('[data-mkedit]')) { e.stopPropagation(); return makeLayersEditable(); }
    if (e.target.closest('[data-unfix]')) { e.stopPropagation(); return backToKitVersion(); }
    if (e.target.closest('[data-addtext]')) return addTextWin();
    if (e.target.closest('[data-lpaste]')) return pasteLayer();
    const t = e.target, L = layerOf(t); if (!L) return;
    if (t.closest('[data-ldel]')) { e.stopPropagation(); return layerDelete(L); }
    if (t.closest('[data-lcopy]')) { e.stopPropagation(); return copyLayer(L); }
    if (t.closest('[data-open]')) { if (L.s.classList.contains('open')) { S.noAutoPick = true; selectedCanvasLayer = null; lastCanvasChipSig = ''; renderParentCanvasChips(lastCanvasLayers); syncIframeLayerSelect(); renderCanvasLayerList(); S.noAutoPick = false; } else selectCanvasLayer(L.idx, L.mfPath); return; }
    if (t.closest('[data-rmimg]')) { e.stopPropagation(); const f = repFiles[L.key]; if (f) URL.revokeObjectURL(f.url); delete repFiles[L.key]; return renderCanvasLayerList(); }
    if (t.closest('[data-upl]') && !t.closest('[data-repin]')) return L.s.querySelector('[data-repin]').click();
    if (t.closest('[data-ltextapply]')) return layerText(L);
    if (t.closest('[data-aiapply]')) { const ta = L.s.querySelector('[data-ai]'); const v = ta.value.trim(); if (!v) return ta.focus(); ta.value = ''; return layerAsk(L, v); }
    if (t.closest('[data-repapply]')) { const f = repFiles[L.key]; const note = L.s.querySelector('[data-repnote]').value.trim(); if (!f) { toast('Pick an image to replace this layer with'); return L.s.querySelector('[data-repin]').click(); } return layerAsk(L, note, f.file); }
  });
  list.addEventListener('input', e => {
    const L = layerOf(e.target); if (!L) return;
    if (e.target.matches('[data-ai]')) L.s.querySelector('[data-aiapply]').classList.toggle('off', !e.target.value.trim());
    if (e.target.matches('[data-repnote]')) L.s.querySelector('[data-repapply]').classList.toggle('off', !(repFiles[L.key] || e.target.value.trim()));
  });
  list.addEventListener('paste', e => {
    const L = layerOf(e.target); if (!L) return;
    const f = [...(e.clipboardData?.files || [])].find(x => /^image\//.test(x.type)); if (!f) return;
    e.preventDefault(); repFiles[L.key] = { file: namedPicture(f), url: URL.createObjectURL(f) }; renderCanvasLayerList(); toast('Picture added to Replace with an image');
  });
  const saveWords = ta => { if (ta._nxSaved === ta.value) return; ta._nxSaved = ta.value; layerText({ mfPath: ta.dataset.mf }, ta.value); };
  list.addEventListener('focusout', e => { if (e.target.matches('[data-wtext]')) saveWords(e.target); });
  list.addEventListener('focusin', e => { if (e.target.matches('[data-wtext]') && e.target._nxSaved == null) e.target._nxSaved = e.target.value; });
  list.addEventListener('input', e => { if (e.target.matches('[data-wtext]')) { e.target.rows = Math.min(4, e.target.value.split('\n').length); try { const el = q1('#canvasEditFrame')?.contentDocument?.querySelector(`[data-mf-path="${CSS.escape(e.target.dataset.mf)}"]`); if (el) el.innerText = e.target.value; } catch (_) {} } });
  list.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && e.target.matches('[data-wtext]')) { e.preventDefault(); saveWords(e.target); return; }
    if (e.key === 'Enter' && !e.shiftKey && e.target.matches('[data-ltext]')) { e.preventDefault(); const L = layerOf(e.target); if (L) layerText(L); return; } if (e.key === 'Enter' && !e.shiftKey && e.target.matches('[data-ai]')) { e.preventDefault(); e.target.closest('.nx-ls').querySelector('[data-aiapply]').click(); } });
  list.addEventListener('change', e => {
    if (!e.target.matches('[data-repin]')) return;
    const L = layerOf(e.target), f = e.target.files[0]; if (!f || !L) return;
    if (!/^image\//.test(f.type)) return toast("That file couldn't be used (an image only)", { err: true });
    repFiles[L.key] = { file: f, url: URL.createObjectURL(f) }; renderCanvasLayerList();
  });
  list.addEventListener('dragover', e => { if (e.target.closest('[data-upl]')) e.preventDefault(); });
  list.addEventListener('drop', e => { const u = e.target.closest('[data-upl]'); if (!u) return; e.preventDefault(); e.stopPropagation(); const L = layerOf(u), f = e.dataTransfer.files[0]; if (f && L && /^image\//.test(f.type)) { repFiles[L.key] = { file: f, url: URL.createObjectURL(f) }; renderCanvasLayerList(); } });
}
/* ---- pictures into the chat ---- */
function namedPicture(f) {
  const ext = (f.type.split('/')[1] || 'png').replace('jpeg', 'jpg');
  return (!f.name || /^image\.(png|jpe?g|webp|gif)$/i.test(f.name)) ? new File([f], `pasted-picture.${ext}`, { type: f.type || 'image/png' }) : f;
}
function attachToChat(f) {
  const inp = q1('#editRef'); if (!inp || !f) return;
  const dt = new DataTransfer(); dt.items.add(namedPicture(f)); inp.files = dt.files;
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  setTab('prompt'); q1('#editFrameAsk')?.focus();
}
function refThumb() {
  const lb = q1('#editRefLabel'), inp = q1('#editRef'), f = inp?.files?.[0];
  if (!lb) return;
  if (!f) { lb.innerHTML = ''; lb.classList.remove('has'); return; }
  const url = URL.createObjectURL(f);
  lb.classList.add('has');
  lb.innerHTML = `<img src="${url}" alt=""><span>${E(f.name)}</span><button type="button" class="nx-refx" aria-label="Remove the picture" data-tip="Remove the picture">${I('x')}</button>`;
  lb.querySelector('.nx-refx').onclick = () => { inp.value = ''; inp.dispatchEvent(new Event('change', { bubbles: true })); setTimeout(refThumb, 0); };
}
/* ---- copy a layer, paste it into any frame; add text ---- */
const CLIP_KEY = 'gs.layerclip';
const clipGet = () => { const c = ls.get(CLIP_KEY, null); return c && Date.now() - (c.ts || 0) < 6 * 3600e3 ? c : null; };
function pathGet(obj, path) { return String(path || '').split('.').reduce((o, k) => (o == null ? undefined : o[/^\d+$/.test(k) ? +k : k]), obj); }
/* Edit layers lists the PSD's layers; a kit-drawn frame turns into a fixed design (its own page) so every layer can be
   edited, and "Back to kit version" lets the kit draw it again (server: /detach, /undetach). */
function makeLayersEditable() {
  const fid = selectedFrameId; if (!fid || !P) return;
  win({
    title: 'Make all layers editable?', ok: 'Make editable',
    body: `<p class="nx-wp" style="margin:0">This frame becomes a fixed design: you can move, change and delete every layer, exactly as it will be in the PSD.</p>
      <p class="nx-wp" style="margin:10px 0 0">The kit stops redrawing it. Prompt still works, and <b>Back to kit version</b> undoes this.</p>`,
    onOk: () => { setTimeout(() => frameStateCall(fid, 'detach', 'Every layer of this frame can be edited now'), 0); },
  });
}
function backToKitVersion() {
  const fid = selectedFrameId; if (!fid) return;
  frameStateCall(fid, 'undetach', 'Back to the kit version');
}
async function frameStateCall(fid, what, msg) {
  const fi = P?.spec?.frames?.findIndex(f => f.id === fid); if (fi == null || fi < 0) return;
  try { setEditLoading?.(true); } catch (_) {}
  try {
    const nf = await api(`/api/projects/${P.id}/frames/${encodeURIComponent(fid)}/${what}`, { method: 'POST' });
    P.spec.frames[fi] = nf;
    frameHistNote([nf]);
    selectedCanvasLayer = null; bumpFrame?.(fid); refreshEditCanvas(); renderCanvasLayerList();
    toast(msg, { undo: () => undoFrameEdit() });
  } catch (e) { toast(e.message || String(e), { err: true }); }
  finally { try { setEditLoading?.(false); } catch (_) {} }
}
function layerToolsHTML() {
  const c = clipGet();
  return `<div class="nx-ltools"><button class="nx-btn ghost" data-addtext data-tip="Add a new text layer to this frame">${I('addtext')}Add text</button>${c ? `<button class="nx-btn ghost" data-lpaste data-tip="Paste the copied layer into this frame (⌘V)">${I('paste')}Paste "${E(String(c.label).slice(0, 22))}"</button>` : ''}</div>`;
}
function copyLayer(L) {
  const fr = P?.spec?.frames?.find(f => f.id === selectedFrameId); if (!fr || !L) return;
  const fno = studioFrames().findIndex(f => f.id === fr.id) + 1;
  let arr = null, value;
  const m = /^(items|els|layers)\.(\d+)$/.exec(L.mfPath || '');
  if (m && Array.isArray(fr[m[1]])) { arr = m[1]; value = fr[arr][+m[2]]; }
  else if (!L.mfPath && L.idx >= 0) { arr = ['items', 'els', 'layers'].find(k => Array.isArray(fr[k])); value = arr ? fr[arr][L.idx] : undefined; }
  else if (L.mfPath) value = pathGet(fr, L.mfPath);
  let html = '', text = '';
  try {
    const d = q1('#canvasEditFrame')?.contentDocument;
    const el = d && (L.mfPath ? d.querySelector(`[data-mf-path="${CSS.escape(L.mfPath)}"],[data-mf-drag="${CSS.escape(L.mfPath)}"]`) : d.querySelector(`[data-spec-idx="${L.idx}"]`));
    if (el) { html = el.outerHTML.slice(0, 8000); text = (el.innerText || '').trim().slice(0, 600); }
  } catch (_) {}
  const label = (L.label || '').replace(/^[^·]*·\s*/, '').trim() || 'layer';
  ls.set(CLIP_KEY, { theme: P.theme, pid: P.id, fid: fr.id, fno, label, arr, value: value === undefined ? null : JSON.parse(JSON.stringify(value)), html, text, ts: Date.now() });
  try { navigator.clipboard?.writeText?.(`[Graphics layer] ${label}`).catch(() => {}); } catch (_) {}
  renderCanvasLayerList();
  toast(`Copied "${label.slice(0, 40)}". Open another frame and paste (⌘V).`);
}
async function pasteLayer() {
  const c = clipGet(), fid = selectedFrameId; if (!c || !fid || !P?.spec) return;
  const fi = P.spec.frames.findIndex(f => f.id === fid); if (fi < 0) return;
  const target = P.spec.frames[fi], fno = fi + 1;
  if (c.theme === P.theme && c.arr && c.value && Array.isArray(target[c.arr])) {   // same kit: an exact copy, instantly
    const v = JSON.parse(JSON.stringify(c.value));
    if (c.fid === fid && c.pid === P.id) ['x', 'y', 'cx', 'cy'].forEach(k => { if (typeof v[k] === 'number') v[k] += 30; });
    const nf = { ...target, [c.arr]: [...target[c.arr], v] };
    try { await putFrames({ [fid]: nf }, `paste ${c.label} into ${fid}`); } catch (e) { return toast(e.message || String(e), { err: true }); }
    const h = frameHist[fid] = frameHist[fid] || []; h.push(JSON.stringify(target)); if (h.length > FRAME_UNDO_MAX) h.shift(); renderUndoBar();
    return toast(`Pasted "${c.label.slice(0, 40)}" into frame ${fno}`, { undo: () => undoFrameEdit() });
  }
  // another kind of layer (or another kit): Claude adds it in this kit's style
  const what = c.value != null ? JSON.stringify(c.value).slice(0, 6000) : c.html || c.text;
  toast(`Pasting "${c.label.slice(0, 40)}" into frame ${fno}…`);
  const r = await askFrame(fid, `Add this element, copied from frame ${c.fno}, to this frame. Keep its words, numbers and look exactly; place it where it fits without covering other content, at a similar position if there is room.\nElement: ${what}`, { quiet: true });
  if (r?.ok) toast(`Pasted "${c.label.slice(0, 40)}" into frame ${fno}`, { undo: () => undoFrameEdit() }); else if (r) toast(r.error || 'Paste did not work', { err: true });
}
function addTextWin(prefill = '') {
  const fid = selectedFrameId, fno = studioFrames().findIndex(f => f.id === fid) + 1; if (!fid) return;
  let where = 'bottom', size = 'body';
  const segs = (k, opts, v) => `<div class="nx-seg" data-g="${k}">${opts.map(([a, b]) => `<button type="button" class="${a === v ? 'on' : ''}" data-v="${a}">${b}</button>`).join('')}</div>`;
  const w = win({
    title: 'Add text', sub: `Frame ${fno}`, ok: 'Add text',
    body: `<span class="nx-lab">Text</span><textarea class="nx-field" id="nxAddTx" style="min-height:84px">${E(prefill)}</textarea>
      <div class="nx-addrow"><div><span class="nx-lab">Where</span>${segs('where', [['top', 'Top'], ['middle', 'Middle'], ['bottom', 'Bottom']], where)}</div>
      <div><span class="nx-lab">Style</span>${segs('size', [['heading', 'Heading'], ['body', 'Body'], ['small', 'Small note']], size)}</div></div>
      <p class="nx-wp" style="margin:12px 0 0">The text is added in this kit's style; it can be moved, resized and edited like any layer.</p>`,
    onOk: async m => {
      const tx = m.querySelector('#nxAddTx').value.trim(); if (!tx) { m.querySelector('#nxAddTx').focus(); return false; }
      setTimeout(async () => {
        const st = { heading: 'as a heading (large, bold)', body: 'as body text', small: 'as a small note / caption' }[size];
        const r = await askFrame(fid, `Add ONE new text layer with exactly this text: "${tx}". Put it at the ${where} of the frame, ${st}, in this kit's text style, without moving or covering the other layers. Change nothing else.`, { quiet: true });
        if (r?.ok) toast(`Text added to frame ${fno}`, { undo: () => undoFrameEdit() }); else if (r) toast(r.error || 'Adding the text did not work', { err: true });
      }, 0);
    },
  });
  w.el.querySelector('.nx-wb').addEventListener('click', e => {
    const b = e.target.closest('.nx-seg button'); if (!b) return;
    const g = b.parentElement.dataset.g; b.parentElement.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
    if (g === 'where') where = b.dataset.v; else size = b.dataset.v;
  });
}
function setTab(k) {
  S.etab = k;
  const map = { layers: '#secLayers', prompt: '#secEdit', anchor: '#secAnchor' };
  Object.entries(map).forEach(([n, sel]) => { const d = q1(sel); if (d) { d.classList.toggle('nx-on', n === k); d.open = n === k; } });
  const sc = q1('#nxSecScript'); if (sc) { sc.hidden = k !== 'script'; if (k === 'script') scriptTab(); }
  $$('.nx-etabs [data-etab]').forEach(b => b.classList.toggle('on', b.dataset.etab === k));
  if (k === 'prompt') setTimeout(() => q1('#editFrameAsk')?.focus(), 20);
}
/* edit mode: the video's script beside the frame, this frame's lines first in view; click a line to copy it */
async function scriptTab() {
  const box = q1('#nxSecScript'); if (!box || !P) return;
  if (!scriptOn() && pdfOn() && !(S.pdfLines?.pid === P.id)) { box.innerHTML = '<div class="nx-escr-e">Loading the storyboard…</div>'; await tkPdfLoad(); }
  if (!scriptOn() && !episodeTranscript?.segments && P.has_episode_transcript) { try { episodeTranscript = await api(`/api/projects/${P.id}/episode-transcript`); } catch (_) {} }
  const L = tkLines(), f = studioFrames().find(x => x.id === selectedFrameId);
  if (!L.list.some(l => l.text.trim())) { box.innerHTML = '<div class="nx-escr-e">This video has no script, voice-over or storyboard text yet.</div>'; return; }
  let a = -1, b = -1;
  if (f && Array.isArray(f.lines)) [a, b] = f.lines;
  else if (f?.vo) { const w = String(f.vo).toLowerCase().split(/\W+/).filter(x => x.length > 3); let best = 0; L.list.forEach((l, j) => { const t = l.text.toLowerCase(); const sc = w.filter(x => t.includes(x)).length; if (sc > best) { best = sc; a = b = j; } }); }
  box.innerHTML = `<small class="nx-escr-h">Click a line to copy it, then paste it into a text box${a >= 0 ? ' · this frame’s lines are highlighted' : ''}</small>` + L.list.map((l, j) => !l.text.trim() ? '' : `<button type="button" class="nx-tkl${j >= a && j <= b ? ' on' : ''}" data-sline="${j}"><time>${l.t != null ? mmss(l.t) : ''}</time><span>${E(l.text.trim())}</span></button>`).join('');
  box.querySelector('.nx-tkl.on')?.scrollIntoView({ block: 'center' });
}
function decorateEdit() {
  const app = q1('#editModeApp'); if (!app) return;
  const top = app.querySelector('.edit-mode-top');
  let ui = top.querySelector('.nx-ui');
  if (!ui) { ui = document.createElement('div'); ui.className = 'nx-ui'; ui.style.cssText = 'display:flex;align-items:center;gap:12px;flex:1;min-width:0'; top.appendChild(ui); }
  editTopBar();
  const center = app.querySelector('.edit-mode-center');
  if (!center.querySelector('.nx-etools')) {
    const tb = document.createElement('div'); tb.className = 'nx-etools nx-ui';
    tb.innerHTML = `<div class="nx-tools"><button class="nx-ib" id="nxEUndo" data-tip="Undo">${I('undo')}</button><button class="nx-ib" id="nxERedo" data-tip="Redo">${I('redo')}</button><button class="nx-ttx" id="nxEReset" data-tip="Frame will revert to its original state." disabled>${I('reset')}Reset</button><span class="sep"></span><button class="nx-btn dark" id="nxERegen" data-tip="Make this frame again from scratch, optionally with a note">${I('regen')}Regenerate</button><span class="sep"></span><button class="nx-ib" data-ez="-1" data-tip="Zoom out">${I('minus')}</button><button class="fit" data-ez="0" data-tip="Fit the frame">Fit</button><button class="nx-ib" data-ez="1" data-tip="Zoom in">${I('plus')}</button></div>`;
    center.insertBefore(tb, center.firstChild);
    const cap = document.createElement('div'); cap.className = 'nx-ecap nx-ui'; cap.id = 'nxECap';
    const hint = document.createElement('div'); hint.className = 'nx-ehint nx-ui'; hint.textContent = 'Drag to move · drag the corner to resize · double-click text to change it';
    center.appendChild(cap); center.appendChild(hint);
    tb.onclick = e => {
      if (e.target.closest('#nxEUndo')) return undoFrameEdit();
      if (e.target.closest('#nxERedo')) return redoFrameEdit();
      if (e.target.closest('#nxERegen')) return regenWin();
      if (e.target.closest('#nxEReset')) return resetFrame();
      const z = e.target.closest('[data-ez]'); if (z) { const d = +z.dataset.ez; window.nxZoom = d ? Math.max(0.4, Math.min(2.5, (window.nxZoom || 1) * (d > 0 ? 1.2 : 1 / 1.2))) : 1; fitCanvasEdit(); }
    };
  }
  const side = app.querySelector('.edit-mode-side');
  if (!side.querySelector('.nx-etabs')) {
    const tabs = document.createElement('div'); tabs.className = 'nx-etabs nx-ui';
    tabs.innerHTML = `<button data-etab="prompt">Prompt</button><button data-etab="layers">Layers <span class="nx-cnt">0</span></button><button data-etab="anchor" id="nxTabAnc">Anchor frame</button><button data-etab="script">Script</button>`;
    side.insertBefore(tabs, side.firstChild);
    const sc = document.createElement('div'); sc.id = 'nxSecScript'; sc.className = 'nx-escr nx-ui'; sc.hidden = true;
    tabs.after(sc);
    sc.onclick = e => { const r = e.target.closest('[data-sline]'); if (!r) return; const tx = r.querySelector('span').innerText; navigator.clipboard?.writeText(tx).then(() => toast('Line copied. Paste it into a text box.'), () => toast('Could not copy', { err: true })); };
    tabs.onclick = e => { const b = e.target.closest('[data-etab]'); if (b) setTab(b.dataset.etab); };
    const look = q1('#editLookBlock'), body = q1('#secEdit .side-sec-body'); if (look && body) body.appendChild(look);
    const ask = q1('#editFrameAsk');
    if (ask) {
      ask.rows = 1; ask.placeholder = 'Ask for a change to this frame';
      const grow = () => { ask.style.height = 'auto'; ask.style.height = Math.min(ask.scrollHeight, 110) + 'px'; const sb = q1('#frameChatSend'); if (sb) sb.disabled = !ask.value.trim() && !q1('#editRef')?.files?.length; };
      ask.addEventListener('input', grow); setTimeout(grow, 0);
      q1('#editRef')?.addEventListener('change', grow);
      const at = q1('.fchat-attach'); if (at) { at.removeAttribute('title'); at.dataset.tip = 'Attach a picture to swap one in'; at.classList.add('tip-up'); }
      const sb = q1('#frameChatSend'); if (sb) { sb.setAttribute('aria-label', 'Send'); sb.dataset.tip = 'Send'; sb.classList.add('tip-up'); }
      ask.placeholder = 'Ask for a change to this frame (paste or drop a picture too)';
      ask.addEventListener('paste', e => { const f = [...(e.clipboardData?.files || [])].find(x => /^image\//.test(x.type)); if (f) { e.preventDefault(); attachToChat(f); } });
      const box = ask.closest('.fchat-box') || ask.parentElement;
      box.addEventListener('dragover', e => { if ([...(e.dataTransfer?.types || [])].includes('Files')) { e.preventDefault(); box.classList.add('drag'); } });
      box.addEventListener('dragleave', () => box.classList.remove('drag'));
      box.addEventListener('drop', e => { box.classList.remove('drag'); const f = [...(e.dataTransfer?.files || [])].find(x => /^image\//.test(x.type)); if (f) { e.preventDefault(); e.stopPropagation(); attachToChat(f); } });
      q1('#editRef')?.addEventListener('change', () => setTimeout(refThumb, 0));
    }
  }
  bindLayerPanel();
  const cf = q1('#canvasEditFrame');
  if (cf && !cf._nx) { cf._nx = true; const inject = () => { try { const d = cf.contentDocument; if (!d || d.getElementById('nxEditCss')) return; const s = d.createElement('style'); s.id = 'nxEditCss'; s.textContent = '.studio-edit-mode [data-spec-idx],.studio-edit-mode [data-mf-path],.studio-edit-mode [data-mf-drag]{outline:0!important}.studio-edit-mode [data-spec-idx]:hover,.studio-edit-mode [data-mf-path]:hover,.studio-edit-mode [data-mf-drag]:hover{outline:1px solid rgba(91,91,214,.55)!important;outline-offset:2px}.studio-inline-edit{outline:0!important}.studio-inline-edit:focus{outline:1.5px solid #5B5BD6!important}'; d.head.appendChild(s); } catch (_) {} }; cf.addEventListener('load', inject); inject(); }
  setTab(S.etab && S.etab !== 'anchor' ? S.etab : 'prompt');
  ancTabVisible();
}
function editTopBar() {
  const ui = q1('#editModeApp .edit-mode-top .nx-ui'); if (!ui || !P) return;
  const i = studioFrames().findIndex(f => f.id === selectedFrameId);
  const c = chOfP();
  const crumb = inProject() ? `<div class="nx-crumb"><button data-eback2>Frames</button>${I('chev')}<b>Frame ${i + 1}</b></div>`
    : `<div class="nx-crumb"><button data-ehome>Graphics</button>${I('chev')}<button data-ech style="display:inline-flex;align-items:center;gap:6px"><span class="nx-mark">${LOGO[c.id]}</span>${c.name}</button>${I('chev')}<button data-eback2>${E(P.name)}</button>${I('chev')}<b>Frame ${i + 1}</b></div>`;
  ui.innerHTML = `<button class="nx-round" data-eback aria-label="Back to the frames" data-tip="Back to the frames">${I('back')}</button>${crumb}<span class="nx-sp"></span><button class="nx-btn ghost" data-resetall data-tip="Every frame will revert to its original state.">${I('reset')}Reset all</button>${exportSplit()}`;
  ui.onclick = e => {
    const t = e.target;
    if (t.closest('[data-eback],[data-eback2]')) return exitEditMode();
    if (t.closest('[data-ehome]')) return goHomeNx();
    if (t.closest('[data-ech]')) { const id = chOfP().id; exitEditMode().then(() => openChannel(id)); return; }
    if (t.closest('[data-expall]')) return exp();
    if (t.closest('[data-expmenu]')) return menu(t.closest('[data-expmenu]'), [{ label: 'Export this frame', icon: 'frame', run: () => expFrame() }, { label: 'Export all frames', icon: 'frames', run: () => exp() }]);
    if (t.closest('[data-resetall]')) return resetAll();
  };
}
function editCaption() {
  const cap = q1('#nxECap'); if (!cap || !P) return;
  const fs = studioFrames(), i = fs.findIndex(f => f.id === selectedFrameId); if (i < 0) { cap.innerHTML = ''; return; }
  const G = groups(fs.map((f, k) => ({ f, i: k }))), tm = frameTimes(G.list)[i] || {};
  cap.innerHTML = `<b>Frame ${i + 1}</b><span>${[tm.s != null ? `${mmss(tm.s)}${tm.e != null ? '–' + mmss(tm.e) : ''}` : '', frameType(fs[i])].filter(Boolean).join(' · ')}</span>`;
}
function stripDecor() {
  const el = q1('#editFrameStrip'); if (!el || !P) return;
  const fs = studioFrames();
  const G = groups(fs.map((f, k) => ({ f, i: k }))), times = frameTimes(G.list);
  $$('.edit-frame-thumb', el).forEach(t => {
    const i = fs.findIndex(f => f.id === t.dataset.fid), lab = t.querySelector('.mini-label');
    if (lab && i >= 0) lab.textContent = `Frame ${i + 1}${times[i]?.s != null ? ' · ' + mmss(times[i].s) : ''}`;
  });
  if (!el.querySelector('.nx-elh')) { const h = document.createElement('div'); h.className = 'nx-elh nx-ui'; el.insertBefore(h, el.firstChild); }
  el.querySelector('.nx-elh').innerHTML = `<b>Frames</b><small>${fs.findIndex(f => f.id === selectedFrameId) + 1} of ${fs.length}</small>`;
}
function regenWin() {
  const fs = studioFrames(), i = fs.findIndex(f => f.id === selectedFrameId), fid = selectedFrameId; if (i < 0) return;
  win({
    title: `Regenerate frame ${i + 1}`, sub: 'optional', ok: 'Regenerate', text: 'Makes this frame again from scratch. Regenerating will replace all layers and discard your edits to this frame (you can undo it). Say what should change, or leave it empty.',
    body: `<textarea class="nx-field" id="nxRegen" data-enter="1" style="min-height:96px" aria-label="What should change"></textarea>`,
    onOk: async m => {
      const note = m.querySelector('#nxRegen').value.trim();
      setTimeout(async () => { const r = await askFrame(fid, note, { regenerate: true, quiet: true }); if (r?.ok) toast(note ? `Frame ${i + 1} is regenerated with your note` : `Frame ${i + 1} is regenerated`, { undo: () => undoFrameEdit() }); else if (r) toast(r.error || 'Regenerate did not work', { err: true }); }, 0);
    },
  });
}
/* Prompt: a chat per frame, bubbles; Done · Undo; Undone */
const nxRFC = function () {
  const host = q1('#frameChatLog'); if (!host || !selectedFrameId) return;
  const log = frameChatLoad();
  if (!log.length) { host.innerHTML = `<div class="nx-chelp"><span class="ic">${I('pencil')}</span><b>Chat with AI to edit anything in this frame</b></div>`; return; }
  host.innerHTML = log.map((m, i) => {
    if (m.role === 'you') return `<div class="fchat-msg you">${E(m.text)}${m.file ? ` <span class="nx-dim">· ${E(m.file)}</span>` : ''}</div>`;
    if (m.pending) return `<div class="fchat-msg claude"><span class="nx-dots"><i></i><i></i><i></i></span></div>`;
    if (m.err) return `<div class="fchat-msg claude" style="color:var(--bad)!important">${E(m.text)}</div>`;
    if (m.undone || /\(undone\)$/.test(m.text)) return `<div class="fchat-msg claude">Undone</div>`;
    return `<div class="fchat-msg claude"><b style="font-weight:500">Done</b>${m.undo ? ` · <button onclick="undoFrameChat(${i})">Undo</button>` : ''}</div>`;
  }).join('');
  host.scrollTop = host.scrollHeight;
};
let _undoFrameChat = null;
const nxUFC = async function (i) { await _undoFrameChat(i); toast('Change undone'); };
/* Anchor frame: On right | On left (Varsity English), and a presenter photo per side for the whole video */
function ancTabVisible() {
  const fr = P?.spec?.frames?.find(f => f.id === selectedFrameId);
  const cam = P?.theme === 'varsity-english' && fr && (fr.mode || 'anchor') !== 'fss';
  const show = cam || (presenterSlots || []).length > 0;
  const t = q1('#nxTabAnc'); if (t) t.hidden = !show;
  if (!show && S.etab === 'anchor') setTab('prompt');
}
const nxRAS = function () {
  const ctl = q1('#anchorFrameCtl'), sec = q1('#secAnchor');
  const fr = P?.spec?.frames?.find(f => f.id === selectedFrameId);
  const cam = P?.theme === 'varsity-english' && fr && (fr.mode || 'anchor') !== 'fss';
  if (ctl) {
    if (cam) {
      const side = String(fr.plate || '').startsWith('anchor_') ? (String(fr.plate).includes('left') ? 'left' : 'right') : (fr.anchor || P.look?.anchor || 'right');
      ctl.innerHTML = `<div class="nx-anc"><div class="hd"><b>This frame</b><div class="nx-seg" role="group"><button class="${side !== 'left' ? 'on' : ''}" onclick="setVeCamera('right')" data-tip="Presenter on the right, graphics on the left">On right</button><button class="${side === 'left' ? 'on' : ''}" onclick="setVeCamera('left')" data-tip="Presenter on the left, graphics on the right" class="tip-l">On left</button></div></div></div>`;
    } else ctl.innerHTML = '';
  }
  if (sec) sec.hidden = !(cam || (presenterSlots || []).length);
  ancTabVisible();
};
const nxRP = function () {
  const block = q1('#presenterBlock'), host = q1('#presenterSlots'); if (!block || !host) return;
  block.hidden = !presenterSlots.length;
  renderAnchorSection();
  const lab = s => { const l = String(s.label || ''); return /right/i.test(l) ? 'Presenter · on right' : /left/i.test(l) ? 'Presenter · on left' : /centre|center/i.test(l) ? 'Presenter · in the centre' : 'Presenter · ' + l.toLowerCase(); };
  host.innerHTML = `<div class="nx-anc">${q1('#anchorFrameCtl')?.innerHTML.trim() ? '<hr style="margin-top:0">' : ''}<div class="hd" style="margin-bottom:0"><b>Presenter photos</b></div><p>Replace the stock photo with a video frame across all instances. The change will apply to all frames.</p>
    ${presenterSlots.map(s => `<div class="nx-prow"><img src="${E(s.src)}" alt="" loading="lazy"><div class="tx"><b>${E(lab(s))}</b><small>${s.count} frame${s.count === 1 ? '' : 's'}</small></div>
      <label class="nx-tbtn" style="cursor:pointer">Change<input type="file" accept="image/*" hidden data-still="${E(s.slot)}"></label>${s.custom ? `<button class="nx-tbtn grey" data-stundo="${E(s.slot)}">Undo</button>` : ''}</div>`).join('')}</div>`;
  host.onchange = async e => {
    const i = e.target.closest('[data-still]'); if (!i) return;
    const f = i.files[0]; if (!f) return;
    if (!/^image\//.test(f.type)) { i.value = ''; return toast("That file couldn't be used (an image only)", { err: true }); }
    const s = presenterSlots.find(x => x.slot === i.dataset.still);
    await uploadPresenter(i.dataset.still, i);
    if ((presenterSlots.find(x => x.slot === s?.slot) || {}).custom) toast(`${lab(s).replace('Presenter · ', 'Presenter ')} now uses your still`);
  };
  host.onclick = async e => { const u = e.target.closest('[data-stundo]'); if (u) { await resetPresenter(u.dataset.stundo); toast('The kit photo is back'); } };
};
/* keyboard with a layer picked: typing goes into Edit with AI; Delete removes it; Esc deselects */
addEventListener('keydown', e => {
  if (!editModeOpen || q1('.nx-modal')) return;
  const a = document.activeElement; if (a && (a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) || a.tagName === 'IFRAME')) return;
  if (!selectedCanvasLayer) return;
  if (e.key === 'Escape') { selectedCanvasLayer = null; S.noAutoPick = true; lastCanvasChipSig = ''; renderParentCanvasChips(lastCanvasLayers); syncIframeLayerSelect(); renderCanvasLayerList(); S.noAutoPick = false; return; }
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'c') { const s = q1('.nx-ls.open'); if (s) { e.preventDefault(); copyLayer(layerOf(s)); } return; }
  if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); const s = q1('.nx-ls.open'); if (s) layerDelete(layerOf(s)); return; }
  if (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey) { setTab('layers'); const ta = q1('.nx-ls.open [data-ai]'); if (ta) { ta.focus(); } }
});

document.addEventListener('paste', async e => {
  if (!editModeOpen || q1('.nx-modal')) return;
  const a = document.activeElement; if (a && (a.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName))) return;
  const f = [...(e.clipboardData?.files || [])].find(x => /^image\//.test(x.type));
  if (f) { e.preventDefault(); attachToChat(f); return toast('Picture attached to the prompt'); }
  const tx = (e.clipboardData?.getData('text') || '').trim(), c = clipGet();
  if (c && (!tx || tx.startsWith('[Graphics layer]'))) { e.preventDefault(); return pasteLayer(); }
  if (tx) { e.preventDefault(); addTextWin(tx.slice(0, 500)); }
});

/* ---------------- LA Studio project step (B16) ---------------- */
function laProjectStart() {
  const ch = chById(LA.channel);
  const formKit = c => c?.id === 'zero1' ? (LA.form === 'sf' ? 'zero1-reel-graphics' : 'zero1-hindi-graphics') : null;
  const create = async theme => {
    const p = await api('/api/la/link', { method: 'POST', body: JSON.stringify({ la_project: LA.id, la_name: LA.name, name: LA.name || 'Graphics', theme }) });
    await open_(p.id);
  };
  loadingView('', 'Getting Graphics ready…');
  bindTop(main());
  if (ch && kitsOf(ch).length === 1) return create(kitsOf(ch)[0]).catch(e => toast(e.message, { err: true }));
  if (ch && formKit(ch) && kitsOf(ch).includes(formKit(ch))) return create(formKit(ch)).catch(e => toast(e.message, { err: true }));
  const w = win({
    title: ch ? 'Pick a kit' : 'Pick a channel and kit', ok: 'Start',
    text: ch ? `${E(ch.name)} has more than one kit. Pick the one for this project.` : 'This project has no channel yet. Pick the one its graphics are for.',
    body: '<div id="nxPkPick"></div>',
    onOk: async () => { const st = read(); if (!st) return false; await create(st.kit); },
    onClose: () => laPost('stage', { stage: 'start' }).catch(() => {}),
  });
  const read = chKitPicker(w.el.querySelector('#nxPkPick'), { ch: ch?.id || null, fixedCh: !!ch });
}
function projectStepsEmpty() { return `<div class="nx-steps">${['Graphics', 'Layers', 'Animate', 'Edit on video'].map((l, i) => `<button class="nx-step${i === 0 ? ' on' : ''}" data-stage="${['graphics', 'psd', 'animate', 'video'][i]}"><i>${i + 1}</i>${l}</button>${i < 3 ? I('chev') : ''}`).join('')}</div>`; }

/* ---------------- take over from index.html ---------------- */
/* ---------------- Toolkit (ZO Product): ready-made frames instead of generating ----------------
   The kit's toolkit is a hidden project whose frames are the templates (made and edited in the normal editor).
   A video copies a template for the script lines picked (no Claude call); "Generate the rest" asks Claude only for
   the lines no toolkit frame covers. */
const TK_THEMES = ['zo-product-graphics', 'zo-ipo-graphics'];
const tkKit = () => !!P && TK_THEMES.includes(P.theme) && !P.look?.toolkit;
const isTkProject = () => !!P?.look?.toolkit;
let TK = null;
async function tkLoad(theme, force) {
  if (!force && TK && TK.theme === theme && Date.now() - TK.at < 30000) return TK;
  const r = await api(`/api/toolkit?theme=${encodeURIComponent(theme)}`);
  TK = { theme, pid: r.pid, templates: r.templates || [], v: Math.round(r.updated_at || 0), at: Date.now() };
  return TK;
}
async function openToolkit(theme) {
  try { const t = await tkLoad(theme, true); S.picked.clear(); await openVideo(t.pid); } catch (e) { toast(e.message || String(e), { err: true }); }
}
function tkLines() {
  if (!scriptOn() && !(episodeTranscript?.segments?.length) && pdfOn() && S.pdfLines?.pid === P.id) return { src: 'pdf', list: S.pdfLines.lines.map(t => ({ t: null, text: t })) };
  if (scriptOn()) { let cum = 0; return { src: 'script', list: scriptLines(P.script).map(ln => { const t = cum / 2.6; cum += words(ln); return { t, text: ln }; }) }; }
  const segs = episodeTranscript?.segments;
  if (segs?.length) return { src: 'vo', list: segs.map(s => ({ t: Number(s.start), text: (s.text || '').trim() })) };
  return { src: '', list: [] };
}
const tkFrames = () => studioFrames().filter(f => f.tk_from && Array.isArray(f.lines));
function tkOwner(n) {
  const own = new Array(n).fill(null);
  studioFrames().forEach(f => { if (Array.isArray(f.lines)) for (let j = f.lines[0]; j <= Math.min(n - 1, f.lines[1]); j++) own[j] = f; });
  return own;
}
function tkSkip() {          // lines marked "no frame needed" (for the source they were marked on)
  const sp = P?.spec || {};
  return new Set(Array.isArray(sp.tk_skip) && sp.tk_skip_src === tkLines().src ? sp.tk_skip : []);
}
async function tkSetSkip(a, b, on) {
  const L = tkLines(), s = tkSkip();
  for (let j = a; j <= b; j++) { if (on) s.add(j); else s.delete(j); }
  const spec = { ...P.spec, tk_skip: [...s].sort((x, y) => x - y), tk_skip_src: L.src };
  P.spec = spec; render();
  try { const r = await api(`/api/projects/${P.id}`, { method: 'PUT', body: JSON.stringify({ spec }) }); if (r?.spec) P.spec = { ...r.spec }; updateDock(); }
  catch (e) { toast(e.message || String(e), { err: true }); }
  if (on) toast(`${b - a + 1} line${a === b ? '' : 's'} marked: no frame needed`, { undo: () => tkSetSkip(a, b, false) });
}
function tkFreeLines() {      // lines no toolkit frame covers (what "Generate the rest" makes frames for)
  const L = tkLines(), cov = tkSkip(); tkFrames().forEach(f => { for (let j = f.lines[0]; j <= f.lines[1]; j++) cov.add(j); });
  return L.list.filter((l, j) => l.text.trim() && !cov.has(j)).length;
}
function tkGroups(its) {
  const L = tkLines(), n = L.list.length, own = new Array(n).fill(null);
  const setOwn = x => { for (let j = x.f.lines[0]; j <= Math.min(n - 1, x.f.lines[1]); j++) own[j] = x.f.id; };
  const withL = its.filter(x => x.f && Array.isArray(x.f.lines));
  withL.filter(x => !x.f.tk_from).forEach(setOwn); withL.filter(x => x.f.tk_from).forEach(setOwn);   // toolkit frames keep their lines
  const lost = withL.filter(x => !x.f.tk_from && !own.includes(x.f.id)), fixes = {};
  if (lost.length) {     // a generated frame that landed on a toolkit frame's lines (older runs): give it the free line it is about
    const sk = tkSkip(), wd = t => String(t || '').toLowerCase().replace(/[^a-z0-9₹%\s]/g, ' ').split(/\s+/).filter(w => w.length > 2);
    lost.forEach(x => {
      const vw = new Set(wd(x.f.vo)), free = L.list.map((l, j) => j).filter(j => own[j] == null && L.list[j].text.trim() && !sk.has(j));
      if (!free.length) return;
      let best = 0, at = null;
      free.forEach(j => { const sc = wd(L.list[j].text).filter(w => vw.has(w)).length; if (sc > best) { best = sc; at = j; } });
      if (at == null) at = free[0];
      let e = at; while (e + 1 < n && own[e + 1] == null && !sk.has(e + 1) && free.includes(e + 1)) e++;
      x.f.lines = [at, e]; setOwn(x); fixes[x.f.id] = [at, e];
    });
    if (Object.keys(fixes).length) { const pid = P.id; setTimeout(async () => { if (P?.id !== pid) return; const spec = { ...P.spec, frames: P.spec.frames.map(f => fixes[f.id] ? { ...f, lines: fixes[f.id] } : f) }; try { const r = await api(`/api/projects/${pid}`, { method: 'PUT', body: JSON.stringify({ spec }) }); if (P?.id === pid && r?.spec) P.spec = r.spec; } catch (_) {} }, 0); }
  }
  const loose = its.filter(x => x.f && !Array.isArray(x.f.lines));
  if (loose.length && L.src === 'script') { const sa = assignScriptRanges(P.script, loose.map(x => x.f), P.storyboard); Object.entries(sa.lineToFrame).forEach(([j, fid]) => { if (own[+j] == null) own[+j] = fid; }); }
  const byId = new Map(its.filter(x => x.f).map(x => [x.f.id, x])), out = [], skip = tkSkip();
  let cur = null;
  L.list.forEach((l, j) => {
    if (!l.text.trim()) return;
    const o = own[j], key = o ? 'f:' + o : skip.has(j) ? 'skip' : 'todo';
    if (!cur || cur.key !== key) { cur = { key, x: o ? byId.get(o) : key === 'skip' ? { todo: true, skip: true } : { todo: true }, lines: [], a: j, b: j }; out.push(cur); }
    cur.lines.push({ t: l.t, text: l.text.trim(), j }); cur.b = j;
  });
  its.forEach(x => { const k = x.ph ? 'ph' + x.k : 'f:' + x.f.id; if (!out.some(g => g.key === k)) out.push({ key: k, x, lines: [] }); });
  return { kind: L.src === 'vo' ? 'transcript' : 'script', list: out, tk: true };
}
function tkTimes(G, its) {
  return its.map(x => { const g = G.list.find(g => g.x === x && g.lines.length); return { s: g ? g.lines[0].t : null, e: g ? g.lines[g.lines.length - 1].t + 4 : null }; });
}
const tkOpen = new Set();     // long "no frame" groups the user expanded (by first line)
function tkTodoHTML(g) {
  const n = g.lines.length, ln = l => `<p class="nx-ln"><time>${l.t != null ? mmss(l.t) : ''}</time><span>${E(l.text)}</span></p>`;
  if (g.x.skip) return `<div class="nx-tkskip" data-tkunskip="${g.a}-${g.b}" data-tip="Click to give these lines a frame again"><span class="ic">${I('skip')}</span><span class="tx"><b>No frame needed</b> · ${E(g.lines[0].text)}${n > 1 ? ` <i>+${n - 1}</i>` : ''}</span><span class="un">Undo</span></div>`;
  const open = n <= 4 || tkOpen.has(g.a), shown = open ? g.lines : g.lines.slice(0, 3);
  return `<div class="nx-grp todo nx-tkfree"><div class="nx-gh"><span class="nx-tkplus">${I('plus')}</span><b>No frame</b><span class="nx-tkn2">${n} line${n === 1 ? '' : 's'}</span><span class="nx-sp"></span><button class="nx-tbtn" data-tkpick="${g.a}-${g.b}">Pick from toolkit</button><button class="nx-ib sm" data-tkskip="${g.a}-${g.b}" data-tip="No frame needed for these lines" class="tip-l" aria-label="No frame needed">${I('skip')}</button></div>${shown.map(ln).join('')}${n > 4 ? `<button class="nx-tkmore" data-tkexp="${g.a}">${open ? 'Show less' : `Show ${n - 3} more line${n - 3 === 1 ? '' : 's'}`}</button>` : ''}</div>`;
}

/* the picker: script lines on the left (click a line, shift-click to stretch), templates on the right */
async function tkPdfLoad() {
  if (!pdfOn() || (S.pdfLines?.pid === P.id && !S.pdfLines.loading)) return;
  if (S.pdfLines?.pid === P.id && S.pdfLines.loading) { while (S.pdfLines?.loading) await new Promise(r => setTimeout(r, 150)); return; }
  const pid = P.id; S.pdfLines = { pid, lines: [], loading: true };
  try { const r = await api(`/api/projects/${pid}/pdf-lines`); S.pdfLines = { pid, lines: r.lines || [] }; } catch (_) { S.pdfLines = { pid, lines: [] }; }
}
function tkPdfNote() {   // a PDF video with toolkit frames: Claude is told which storyboard parts are already done
  const f = tkFrames().filter(x => x.lines_src === 'pdf'), L = tkLines(), sk = L.src === 'pdf' ? [...tkSkip()].map(j => L.list[j]?.text).filter(Boolean) : [];
  const no = sk.length ? ' No frame is needed at all for these storyboard lines: ' + sk.map(t => `"${String(t).replace(/\s+/g, ' ').slice(0, 120)}"`).join('; ') + '.' : '';
  if (!f.length) return no.trim();
  return no.trim() + (no ? ' ' : '') + 'These parts of the storyboard already have a frame picked from the team toolkit; do NOT make frames for them: ' + f.map(x => `"${String(x.vo || '').replace(/\s+/g, ' ').slice(0, 160)}"`).join('; ') + '.';
}
async function stopGen() {
  const g = S.gen; if (!g) return;
  g.stopped = true; S.gen = null;
  try { await api(`/api/projects/${g.pid}/stop`, { method: 'POST', body: '{}' }); } catch (_) {}
  if (P?.id === g.pid) { try { P = await api(`/api/projects/${g.pid}`); P.look = normLook(P.look); frameHistInit(); } catch (_) {} selectedFrameId = studioFrames()[0]?.id || null; S.phSel = null; render(); }
  loadList();
  toast('Stopped. Nothing from that run is kept.');
}
async function tkPicker(pre) {
  if (!scriptOn() && pdfOn()) await tkPdfLoad();
  if (!tkLines().list.length && P.has_episode_transcript && !episodeTranscript?.segments) { try { episodeTranscript = await api(`/api/projects/${P.id}/episode-transcript`); } catch (_) {} }
  const L = tkLines();
  if (!L.list.some(l => l.text.trim())) return toast('Add the script, a voice-over or a storyboard PDF with text first: a toolkit frame is picked for some of its lines.', { err: true });
  let T; try { T = await tkLoad(P.theme); } catch (e) { return toast(e.message || String(e), { err: true }); }
  if (!T.templates.length) return win({ title: 'The toolkit is empty', text: 'Make templates first: open <b>Toolkit</b> on the ZO page, start one on a kit photo, import a PSD, or use <b>Save to toolkit</b> on a frame.', ok: 'Open the toolkit', onOk: () => openToolkit(P.theme) });
  const own = tkOwner(L.list.length);
  let a = pre?.a ?? null, b = pre?.b ?? null, tpl = null;
  const lineRows = () => L.list.map((l, j) => !l.text.trim() ? '' : `<button type="button" class="nx-tkl${a != null && j >= a && j <= b ? ' on' : ''}${own[j]?.tk_from ? ' used' : ''}" data-j="${j}"${own[j]?.tk_from ? ` data-tip="Already in a toolkit frame"` : ''}><time>${l.t != null ? mmss(l.t) : ''}</time><span>${E(l.text.trim())}</span></button>`).join('');
  const body = `<div class="nx-tkp"><div class="nx-tkp-l"><small>1 · Lines this frame is for <i>(click, shift-click to add more)</i></small><div class="nx-tkls" id="nxTkLs">${lineRows()}</div></div>
    <div class="nx-tkp-r"><small>2 · Template</small><div class="nx-tkts">${T.templates.map(t => `<button type="button" class="nx-tkt" data-t="${E(t.fid)}"><img loading="lazy" alt="" src="${thumbUrl(T.pid, t.fid, T.v, 320)}"><span>${E(t.name)}</span></button>`).join('')}</div></div></div>`;
  const w = win({ title: 'Pick from toolkit', sub: 'No generating: the template is copied, then edit its text and layers as usual.', body, ok: 'Add frame', wide: true,
    onOk: async () => {
      if (a == null) { toast('Choose the lines this frame is for', { err: true }); return false; }
      if (!tpl) { toast('Choose a template', { err: true }); return false; }
      const text = L.list.slice(a, b + 1).map(l => l.text.trim()).filter(Boolean).join('\n');
      const r = await api(`/api/projects/${P.id}/toolkit-frame`, { method: 'POST', body: JSON.stringify({ tk_fid: tpl, lines: [a, b], text, src: L.src }) });
      P = r; P.look = normLook(P.look); frameHistInit(); selectedFrameId = r.new_fid; S.phSel = null;
      render(); loadList();
      toast('Toolkit frame added. Edit layers to put in this video’s words.');
    } });
  const el = w.el; el.querySelector('.nx-win').classList.add('nx-tkwin');
  const draw = () => { el.querySelector('#nxTkLs').innerHTML = lineRows(); };
  el.querySelector('#nxTkLs').addEventListener('click', e => {
    const r = e.target.closest('[data-j]'); if (!r) return; const j = +r.dataset.j;
    if (e.shiftKey && a != null) { a = Math.min(a, j); b = Math.max(b, j); }
    else if (a === j && b === j) { a = b = null; }
    else { a = b = j; }
    draw();
  });
  el.querySelector('.nx-tkts').addEventListener('click', e => {
    const t = e.target.closest('[data-t]'); if (!t) return; tpl = t.dataset.t;
    el.querySelectorAll('.nx-tkt').forEach(x => x.classList.toggle('on', x === t));
  });
  el.querySelector('.nx-tkl.on')?.scrollIntoView({ block: 'center' });
}

async function genRest() {
  const pid = P.id, L = tkLines(), free = tkFreeLines();
  if (!free) return toast('Every line already has a toolkit frame');
  const nTk = tkFrames().length, others = studioFrames().length - nTk;
  const go = async () => {
    const tok = S.gen = { pid, kind: 'rest', n0: nTk, count: Math.max(1, Math.round(free / Math.max(1, L.list.filter(l => l.text.trim()).length) * (estFrames() || 6))), msg: 'Writing frames for the lines without a toolkit frame…' };
    P.spec = { ...P.spec, frames: (P.spec.frames || []).filter(f => f.tk_from) };
    render(); pollGen(pid);
    try {
      const r = await api(`/api/projects/${pid}/storyboard`, { method: 'POST', body: JSON.stringify({ script: P.script || '', look: lookPayload('script'), notes: '', rest: { lines: L.list.map(l => l.text), src: L.src, skip: [...tkSkip()] } }) });
      if (tok.stopped || r.stopped) return;
      S.gen = null;
      if (P?.id === pid) { P = r; P.look = normLook(P.look); frameVer = {}; frameHistInit(); selectedFrameId = studioFrames()[0]?.id || null; S.phSel = null; render(); }
      loadList();
      toast(`${(r.spec?.frames || []).filter(f => !f.tk_from).length} frames generated around ${nTk} toolkit frame${nTk === 1 ? '' : 's'}`);
    } catch (e) { if (tok.stopped) return; S.gen = null; if (P?.id === pid) { try { P = await api(`/api/projects/${pid}`); P.look = normLook(P.look); } catch (_) {} render(); } toast(e.message || String(e), { err: true }); }
  };
  if (others) win({ title: 'Generate the rest again?', text: `The ${others} generated frame${others === 1 ? ' is' : 's are'} made again for the lines without a toolkit frame. Toolkit frames stay as they are.`, ok: 'Generate the rest', onOk: go });
  else go();
}

async function saveToToolkit() {
  const f = studioFrames().find(x => x.id === selectedFrameId); if (!f) return;
  win({ title: 'Save to toolkit', sub: 'A copy of this frame becomes a template every ZO video can use.', body: `<label class="nx-fl">Template name<input id="nxTkName" value="${E(f.name || '')}" placeholder="e.g. Anchor right · heading + 3 points"></label>`, ok: 'Save to toolkit',
    onOk: async m => { const name = m.querySelector('#nxTkName').value.trim(); await api('/api/toolkit/save', { method: 'POST', body: JSON.stringify({ pid: P.id, fid: f.id, name }) }); TK = null; toast('Saved to the toolkit'); } });
}

/* the toolkit itself: its templates as cards */
function toolkitView() {
  const m = main(), fs = studioFrames(), ver = id => frameVer[id] || 0;
  const plates = [['m2_right', 'Presenter on the right'], ['m2_left', 'Presenter on the left'], ['m2_centre', 'Presenter in the centre'], ['m1_close_left', 'Close, presenter on the left'], ['fss', 'Full screen (no presenter)']];
  m.innerHTML = `<div class="nx-top">${topLeftHTML()}<span class="nx-sp"></span><button class="nx-btn ghost" data-tkpsd>${I('upload')}Import PSD</button><button class="nx-btn primary" data-tknew>${I('plus')}New template</button></div>
  <div class="nx-box"><div class="nx-tkh"><b>${fs.length} template${fs.length === 1 ? '' : 's'}</b><span>Ready-made frames ZO videos can use instead of generating one. Click a template to edit it like any frame: text, layers, presenter photo.</span></div>
  ${fs.length ? `<div class="nx-cards">${fs.map(f => `<div class="nx-card nx-tkc" data-tkf="${E(f.id)}" tabindex="0"><span class="nx-tkim"><img loading="lazy" alt="" src="${thumbUrl(P.id, f.id, ver(f.id) + '_' + Math.round(P.updated_at || 0), 480)}" onerror="this.style.visibility='hidden'"></span><div class="nx-tkn"><b>${E(f.name || 'Template')}</b><button class="nx-ib" data-tkmore="${E(f.id)}" aria-label="More" data-tip="More">${I('more')}</button></div></div>`).join('')}</div>`
    : `<div class="nx-empty"><b>No templates yet</b>Start one on a kit photo, import a layered PSD, or open any ZO video and use <i>Save to toolkit</i> on a frame.<button class="nx-btn primary" data-tknew>${I('plus')}New template</button></div>`}</div>
  <input type="file" id="nxTkPsd" accept=".psd" hidden>`;
  bindTop(m);
  const after = async (r, msg) => { TK = null; P = await api(`/api/projects/${P.id}`); P.look = normLook(P.look); frameVer = {}; frameHistInit(); render(); toast(msg); return r; };
  m.onclick = e => {
    const t = e.target;
    if (t.closest('[data-tknew]')) return menu(t.closest('[data-tknew]'), plates.map(([k, l]) => ({ label: l, icon: 'frame', run: async () => { try { const r = await api('/api/toolkit/blank', { method: 'POST', body: JSON.stringify({ theme: P.theme, plate: k }) }); await after(r, 'New template added'); } catch (er) { toast(er.message, { err: true }); } } })));
    if (t.closest('[data-tkpsd]')) return q1('#nxTkPsd').click();
    const mo = t.closest('[data-tkmore]');
    if (mo) { const fid = mo.dataset.tkmore, f = fs.find(x => x.id === fid); return menu(mo, [
      { label: 'Edit', icon: 'pencil', run: () => { selectedFrameId = fid; openEditMode(fid); } },
      { label: 'Rename', icon: 'pencil', run: () => win({ title: 'Rename template', body: `<label class="nx-fl">Name<input id="nxTkRn" value="${E(f.name || '')}"></label>`, ok: 'Rename', onOk: async m2 => { const nm = m2.querySelector('#nxTkRn').value.trim(); if (!nm) return false; await putFrames({ [fid]: { ...f, name: nm } }, 'template renamed'); TK = null; render(); } }) },
      '-', { label: 'Delete template', icon: 'trash', red: true, run: () => win({ title: 'Delete this template?', text: 'Videos that already used it keep their frame.', ok: 'Delete', onOk: async () => { await api(`/api/projects/${P.id}`, { method: 'PUT', body: JSON.stringify({ spec: { ...P.spec, frames: P.spec.frames.filter(x => x.id !== fid) } }) }); await after(null, 'Template deleted'); } }) }]); }
    const c = t.closest('[data-tkf]'); if (c) { selectedFrameId = c.dataset.tkf; return openEditMode(c.dataset.tkf); }
  };
  q1('#nxTkPsd').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    const fd = new FormData(); fd.append('theme', P.theme); fd.append('file', f);
    toast(`Reading ${f.name}…`);
    try { const r = await fetch('/api/toolkit/psd', { method: 'POST', body: fd }); const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.detail || 'That PSD could not be read'); await after(j, `Template made from ${f.name}`); }
    catch (er) { toast(er.message || String(er), { err: true }); }
  };
}

window.nxBoot = async function () {
  shell();
  render = render2;
  _setEditLoading = setEditLoading; setEditLoading = on => { if (nxLayerBusy && on) return; _setEditLoading(on); };
  _renderCanvasLayerList = renderCanvasLayerList; renderCanvasLayerList = nxRCL;
  canvasLayerAction = nxCLA; renderFrameChat = nxRFC;
  _undoFrameChat = undoFrameChat; undoFrameChat = nxUFC;
  renderAnchorSection = nxRAS; renderPresenter = nxRP;
  appendParentLayerActionChip = function (host, L, top, left, w, h) {
    const chip = document.createElement('div');
    chip.className = 'canvas-parent-chip nx-lbar';
    const mf = L.mfPath ? ` data-mf-path="${E(L.mfPath)}"` : '';
    const B = (act, tip, icon) => `<button type="button" data-act="${act}" data-idx="${L.idx}"${mf} title="${tip}"><svg viewBox="0 0 16 16">${IC[icon]}</svg></button>`;
    chip.innerHTML = `<span class="cl">${E(layerKind(L.label).name || 'Layer')}</span><span class="ca">${B('edit', 'Edit this layer with AI', 'pencil')}${B('replace', 'Replace with an image', 'regen')}${B('copy', 'Copy this layer (⌘C)', 'copy')}${B('delete', 'Delete this layer', 'trash')}</span>`;
    let y = top - 40; if (y < 4) y = top + Math.max(20, h) + 8;
    chip.style.top = y + 'px'; chip.style.left = Math.max(4, left) + 'px';
    host.appendChild(chip);
  };
  renderHomeMain = () => { if (!P) renderList(); };
  renderSidebar = () => {};
  goHome = goHomeNx;
  newProject = newVideo;
  renameProject = () => P && renameVideo({ id: P.id, name: P.name });
  deleteProject = () => P && delVideos([P.id]);
  laStartPanel = laProjectStart;
  frameLabel = fid => 'Frame ' + (Math.max(0, studioFrames().findIndex(f => f.id === fid)) + 1);
  selectFrame = fid => { selectedFrameId = fid; S.phSel = null; render(); };
  setWorkspaceLoading = (on, msg) => { S.bg = on ? (msg || 'Working…') : ''; if (P && !editModeOpen) updateDock(); };
  showBg = s => { S.bg = s.state === 'running' ? (s.msg || 'Working…') : ''; if (P && !editModeOpen) updateDock(); };
  hideBg = () => { S.bg = ''; if (P && !editModeOpen) updateDock(); };
  const _bump = bumpFrame;
  bumpFrame = fid => { _bump(fid); if (P && !editModeOpen && selectedFrameId === fid) { const f = q1('#nxBigFr'); if (f) f.src = `/preview/${P.id}/${encodeURIComponent(fid)}?v=${frameVer[fid]}`; } };
  const _list = list;
  list = async () => { loadList().then(() => { allProjects = S.list || []; if (!P && !editModeOpen) renderList(); }); };
  const _open = openEditMode;
  openEditMode = fid => { S.etab = (isTkProject() || studioFrames().find(x => x.id === fid)?.tk_from) ? 'layers' : 'prompt'; window.nxZoom = 1; selectedCanvasLayer = null; _open(fid); decorateEdit(); editCaption(); stripDecor(); };
  const _sel = selectEditFrame;
  selectEditFrame = fid => { selectedCanvasLayer = null; _sel(fid); if (q1('#editModeApp .nx-ui')) { editTopBar(); editCaption(); stripDecor(); ancTabVisible(); if (S.etab === 'script') scriptTab(); } };
  const _strip = buildEditFrameStrip;
  buildEditFrameStrip = () => { _strip(); stripDecor(); };
  const _exit = exitEditMode;
  exitEditMode = async () => { window.nxZoom = 1; await _exit(); };
  const _fit = fitCanvasEdit;
  fitCanvasEdit = function () {
    _fit();
    const tb = q1('#editModeApp .nx-etools'), vp = q1('#canvasEditViewport');
    if (tb && vp) tb.style.top = Math.max(10, vp.offsetTop + stageView.oy - tb.offsetHeight - 12) + 'px';
  };
  void _list;

  try { themes = await api('/api/themes'); } catch (e) { S.err = e.message; }
  try { themeMeta = await api('/api/theme-meta'); } catch (_) {}
  if (EMBED && LA.id) {
    const done = () => document.documentElement.classList.remove('la-boot'); setTimeout(done, 10000);
    try {
      loadingView('', 'Opening this project’s graphics…');
      document.documentElement.classList.remove('la-boot');
      const r = await api('/api/la/project/' + encodeURIComponent(LA.id)).catch(() => ({}));
      loadList();
      if (r && r.project_id) { try { await open_(r.project_id); return; } catch (_) {} }
      laProjectStart();
    } finally { done(); }
    return;
  }
  document.documentElement.classList.remove('la-boot');
  renderList();
  await loadList();
  allProjects = S.list || [];
  if (!P) renderList();
};
})();
