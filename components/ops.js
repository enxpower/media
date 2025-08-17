<script type="module">
// components/ops.js
// 读取 /static/data/ads.json（由私库 content-ops/json/ads.json 同步而来）
// 根据 enabled 与字段内容，自动填充并显示挂钩位；否则保持 hidden。

const ADS_JSON_URL = '/static/data/ads.json';

async function fetchJSON(url) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`[ops] ${url} ${res.status}`);
  return res.json();
}

function show(el) {
  if (!el) return;
  // 同时兼容 hidden 属性与行内 display:none 两种隐藏方式
  el.removeAttribute('hidden');
  if (el.style && el.style.display === 'none') el.style.display = '';
}

function isDesktop() {
  return matchMedia('(min-width: 1024px)').matches;
}

function escapeHTML(str = '') {
  return String(str)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderTopBanner(cfg) {
  const el = document.querySelector('#top-banner');
  if (!el || !cfg?.top_banner?.enabled) return;

  const t = escapeHTML(cfg.top_banner.title || '');
  const s = escapeHTML(cfg.top_banner.subtitle || '');
  const href = cfg.top_banner.href || '#';

  if (!t || !href) return; // 关键字段缺失则不显示

  el.innerHTML = `
    <a href="${href}">
      <strong>${t}</strong>
      ${s ? `<span style="margin-left:.5rem;opacity:.85">${s}</span>` : ''}
    </a>
  `;
  show(el);
}

function renderSideSponsors(cfg) {
  // 仅桌面端显示侧栏（如果你的页面没有侧栏容器，此函数会直接返回，不影响）
  if (!isDesktop()) return;
  const el = document.querySelector('#side-sponsors');
  if (!el || !Array.isArray(cfg?.side_sponsors)) return;

  const items = cfg.side_sponsors
    .filter(x => x && x.href && x.label)
    .map(x => {
      const label = escapeHTML(x.label);
      const href = x.href;
      return `<li><a href="${href}" target="_blank" rel="noopener">${label}</a></li>`;
    });

  if (items.length === 0) return;
  el.innerHTML = items.join('');
  show(el);
}

function renderDownloads(cfg) {
  if (!isDesktop()) return;
  const el = document.querySelector('#side-downloads');
  if (!el || !Array.isArray(cfg?.downloads)) return;

  const items = cfg.downloads
    .filter(x => x && x.href && x.name)
    .map(x => {
      const name = escapeHTML(x.name);
      const href = x.href;
      return `<li><a href="${href}" download>${name}</a></li>`;
    });

  if (items.length === 0) return;
  el.innerHTML = items.join('');
  show(el);
}

function renderRecommended(cfg) {
  if (!isDesktop()) return;
  const el = document.querySelector('#side-recos');
  if (!el || !Array.isArray(cfg?.recommended)) return;

  const items = cfg.recommended
    .filter(x => x && x.href && x.title)
    .map(x => {
      const title = escapeHTML(x.title);
      const href = x.href;
      return `<li><a href="${href}" target="_blank" rel="noopener">${title}</a></li>`;
    });

  if (items.length === 0) return;
  el.innerHTML = items.join('');
  show(el);
}

function renderFooterCTA(cfg) {
  const el = document.querySelector('#footer-cta');
  if (!el || !cfg?.footer_cta?.enabled) return;

  const text = escapeHTML(cfg.footer_cta.text || '');
  const href = cfg.footer_cta.href || '#';
  if (!text || !href) return;

  // 桌面端大按钮；移动端小按钮
  const cls = isDesktop() ? 'btn btn-primary' : 'btn btn-small';
  el.innerHTML = `<a class="${cls}" href="${href}">${text}</a>`;
  show(el);
}

(async () => {
  try {
    const cfg = await fetchJSON(ADS_JSON_URL);

    // 顶部横幅
    renderTopBanner(cfg);

    // 右侧栏（如果页面没有对应容器，函数内会自动返回，不报错）
    renderSideSponsors(cfg);
    renderDownloads(cfg);
    renderRecommended(cfg);

    // 底部 CTA
    renderFooterCTA(cfg);
  } catch (err) {
    // 沉默失败：不打扰用户、不破坏现有布局
    console.warn('[ops] config load skipped:', err?.message || err);
  }
})();
</script>
