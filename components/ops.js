// components/ops.js
const ADS_JSON_URL = '/static/data/ads.json';

function log(...a){ try{console.log('[ops]', ...a);}catch(e){} }
function fetchJSON(url){
  return fetch(url, { cache: 'no-store' }).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  });
}
function show(el){ if (!el) return; el.removeAttribute('hidden'); if (el.style && el.style.display === 'none') el.style.display = ''; }
function isDesktop(){ return matchMedia('(min-width:1024px)').matches; }
function esc(s=''){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
function enabled(obj){ return !!(obj && (obj.enabled ?? obj.enable)); }

async function init(){
  try{
    const cfg = await fetchJSON(ADS_JSON_URL);
    log('cfg loaded');

    renderTop(cfg);
    renderSide(cfg);
    renderFooter(cfg);
  }catch(e){
    log('load failed:', e);
  }
}

function renderTop(cfg){
  const el = document.querySelector('#top-banner');
  const tb = cfg && cfg.top_banner;
  if (!el || !enabled(tb)) return;

  const t = esc(tb.title || '');
  const s = esc(tb.subtitle || '');
  const href = tb.href || '#';
  if (!t || !href) return;

  el.innerHTML = `<a href="${href}"><strong>${t}</strong>${s ? ` <span style="opacity:.85">${s}</span>` : ''}</a>`;
  show(el);
}

function renderFooter(cfg){
  const el = document.querySelector('#footer-cta');
  const fc = cfg && cfg.footer_cta;
  if (!el || !enabled(fc)) return;

  const text = esc(fc.text || '');
  const href  = fc.href || '#';
  if (!text || !href) return;

  const cls = isDesktop() ? 'btn btn-primary' : 'btn btn-small';
  el.innerHTML = `<a class="${cls}" href="${href}">${text}</a>`;
  show(el);
}

function renderSide(cfg){
  if (!isDesktop()) return;

  const sponsors = document.querySelector('#side-sponsors');
  if (sponsors && Array.isArray(cfg?.side_sponsors)) {
    sponsors.innerHTML = cfg.side_sponsors
      .filter(x => x && x.href && x.label)
      .map(x => `<li><a href="${x.href}" target="_blank" rel="noopener">${esc(x.label)}</a></li>`)
      .join('');
    if (sponsors.innerHTML) show(sponsors);
  }

  const downloads = document.querySelector('#side-downloads');
  if (downloads && Array.isArray(cfg?.downloads)) {
    downloads.innerHTML = cfg.downloads
      .filter(x => x && x.href && x.name)
      .map(x => `<li><a href="${x.href}" download>${esc(x.name)}</a></li>`)
      .join('');
    if (downloads.innerHTML) show(downloads);
  }

  const recos = document.querySelector('#side-recos');
  if (recos && Array.isArray(cfg?.recommended)) {
    recos.innerHTML = cfg.recommended
      .filter(x => x && x.href && x.title)
      .map(x => `<li><a href="${x.href}" target="_blank" rel="noopener">${esc(x.title)}</a></li>`)
      .join('');
    if (recos.innerHTML) show(recos);
  }
}

init();
log('loaded');
