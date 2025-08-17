<script type="module">
// /components/ops.js
async function hydrateOps() {
  try {
    const res = await fetch('/static/data/ads.json', { cache: 'no-store' });
    if (!res.ok) return;
    const cfg = await res.json();

    // 顶部横幅
    const top = document.querySelector('#top-banner');
    if (top && cfg.top_banner?.enabled) {
      top.innerHTML = `
        <a href="${cfg.top_banner.href}">
          <strong>${cfg.top_banner.title}</strong>
          <span>${cfg.top_banner.subtitle || ''}</span>
        </a>
      `;
      top.style.display = 'block';
    }

    // 侧栏赞助
    const side = document.querySelector('#side-sponsors');
    if (side && Array.isArray(cfg.side_sponsors)) {
      side.innerHTML = cfg.side_sponsors.map(s =>
        `<li><a href="${s.href}" target="_blank" rel="noopener">${s.label}</a></li>`
      ).join('');
    }

    // 底部 CTA
    const footer = document.querySelector('#footer-cta');
    if (footer && cfg.footer_cta?.enabled) {
      footer.innerHTML = `<a href="${cfg.footer_cta.href}">${cfg.footer_cta.text}</a>`;
      footer.style.display = 'block';
    }
  } catch (e) {
    console.warn('Ops config load failed:', e);
  }
}
hydrateOps();
</script>
