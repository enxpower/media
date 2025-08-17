// components/nativeAds.js
(function () {
  const ADS_URL   = '/static/data/ads.json';
  const LIST_ID   = 'newsContainer';
  const CARD_CLASS= 'news-post';
  const SP_ATTR   = 'data-sponsor';
  const CFG_KEY   = 'native_ads';
  const IS_DEBUG  = new URLSearchParams(location.search).has('debug');

  const list = document.getElementById(LIST_ID);
  if (!list) return;

  // ---- GA4 helpers ----
  function ga(eventName, payload) {
    try { if (typeof gtag === 'function') gtag('event', eventName, { ...payload, debug_mode: IS_DEBUG }); } catch(_) {}
  }
  function sendImpression(d) {
    ga('view_promotion', {
      promotion_id:   d.id || '',
      promotion_name: d.title || '',
      creative_name:  d.brand || 'sponsor',
      creative_slot:  String(d.slot || ''),
      page_number:    window.Pager?.current || 1,
      language:       document.documentElement.lang || 'en'
    });
  }
  function sendClick(d) {
    ga('select_promotion', {
      promotion_id:   d.id || '',
      promotion_name: d.title || '',
      creative_name:  d.brand || 'sponsor',
      creative_slot:  String(d.slot || ''),
      page_number:    window.Pager?.current || 1,
      language:       document.documentElement.lang || 'en'
    });
  }

  let adsCfg = null;
  let adQueue = [];

  async function loadCfg() {
    try {
      const r = await fetch(ADS_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('ads.json ' + r.status);
      const json = await r.json();
      adsCfg = json && json[CFG_KEY];
      if (!adsCfg || adsCfg.enabled === false) return;
      adQueue = Array.isArray(adsCfg.cards) ? adsCfg.cards.slice() : [];
      if (!adQueue.length) return;
      if (adsCfg.shuffle) adQueue.sort(() => Math.random() - 0.5);
    } catch (_) {}
  }

  function getPositions() {
    if (adsCfg && Array.isArray(adsCfg.positions) && adsCfg.positions.length) {
      return adsCfg.positions.map(n => parseInt(n, 10)).filter(n => n > 0);
    }
    return [3]; // 默认第3条后
  }
  function pickCard() {
    if (!adQueue.length) return null;
    const ad = adQueue.shift(); adQueue.push(ad); return ad;
  }

  // 生成“与新闻一致”的 Sponsor 卡
  function makeCard(ad) {
    const el = document.createElement('article');
    el.className = CARD_CLASS + ' sponsor';
    el.setAttribute(SP_ATTR, 'true');
    el.setAttribute('data-category', 'Sponsor');

    // 标题（可点击；样式在 CSS 中弱化为普通标题色）
    const h = document.createElement('h3');
    const a = document.createElement('a');
    a.className = 'news-link';
    a.target = ad.target || '_blank';
    a.rel = 'sponsored nofollow noopener';
    a.href = ad.href || '#';
    a.textContent = ad.title || '';
    h.appendChild(a);
    el.appendChild(h);

    // 图片（支持 WebP → JPG 回退）
    if (ad.img) {
      const link = document.createElement('a');
      link.href = ad.href || '#';
      link.target = a.target;
      link.rel = a.rel;

      const img = document.createElement('img');
      img.src = ad.img;
      img.alt = ad.img_alt || ad.title || 'sponsor';
      img.loading = 'lazy';
      img.className = 'sponsor-img';

      img.onerror = () => {
        if (!img.dataset.fallbackTried) {
          img.dataset.fallbackTried = '1';
          const fb = ad.img_fallback || ad.img.replace(/\.webp$/i, '.jpg');
          img.src = fb;
        }
      };

      link.appendChild(img);
      el.appendChild(link);
    }

    // 描述（可选）
    if (ad.text) {
      const p = document.createElement('p');
      p.className = 'preview';
      p.textContent = ad.text;
      el.appendChild(p);
    }

    // ✅ Sponsor 标签与其它分类标签一致：用 .tags 放在卡片底部
    const tag = document.createElement('span');
    tag.className = 'tags';
    tag.textContent = '#Sponsor';
    el.appendChild(tag);

    // 点击埋点
    el.addEventListener('click', (e) => {
      const t = e.target.closest('a');
      if (!t) return;
      sendClick({
        id: el.dataset.spId, title: el.dataset.spTitle,
        brand: el.dataset.spBrand, slot: el.dataset.spSlot
      });
    });

    return el;
  }

  // 曝光统计：元素进入视口 ≥50% 只记一次
  let io;
  function observeImpression(cardEl) {
    if (!('IntersectionObserver' in window)) return;
    if (!io) {
      io = new IntersectionObserver((entries) => {
        entries.forEach(en => {
          const el = en.target;
          if (en.isIntersecting && en.intersectionRatio >= 0.5 && !el.dataset.spSeen) {
            el.dataset.spSeen = '1';
            sendImpression({
              id: el.dataset.spId, title: el.dataset.spTitle,
              brand: el.dataset.spBrand, slot: el.dataset.spSlot
            });
            io.unobserve(el);
          }
        });
      }, { threshold: [0.5] });
    }
    io.observe(cardEl);
  }

  function clearOld() {
    list.querySelectorAll('['+SP_ATTR+']').forEach(n => n.remove());
  }

  function insertAdsOnce() {
    if (!adsCfg || adsCfg.enabled === false) return;
    if (!adQueue.length) return;

    clearOld();

    const cards = list.querySelectorAll('.' + CARD_CLASS + ':not(['+SP_ATTR+'])');
    if (!cards.length) return;

    const pos = getPositions();
    pos.forEach(idx => {
      const ad = pickCard();
      if (!ad) return;

      const cardEl = makeCard(ad);
      // 埋点所需元数据
      cardEl.dataset.spSlot  = String(idx);
      cardEl.dataset.spId    = ad.id || '';
      cardEl.dataset.spTitle = ad.title || '';
      cardEl.dataset.spBrand = ad.brand || '';

      const anchor = cards[idx - 1]; // 1-based
      if (anchor && anchor.parentNode) {
        anchor.insertAdjacentElement('afterend', cardEl);
      } else {
        list.appendChild(cardEl);
      }
      observeImpression(cardEl);
    });
  }

  loadCfg();
  document.addEventListener('pager:update', insertAdsOnce);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(insertAdsOnce, 0));
  } else {
    setTimeout(insertAdsOnce, 0);
  }
})();
