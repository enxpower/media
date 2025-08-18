// components/nativeAds.js
// Native sponsor cards with GA4 tracking (view_promotion/select_promotion),
// WebP→JPG fallback, and responsive images via srcset/sizes.
// Works with your pager: re-inserts ads on `pager:update`.
//
// Requirements:
// 1) Config at /static/data/ads.json -> { native_ads: { enabled, shuffle, positions, cards:[...] } }
//    Each card may include: id, brand, title, href, img, img_fallback, img_alt, srcset, sizes, text, target
// 2) CSS has .news-post styles; we add .news-post.sponsor specific tweaks in main.css

(function () {
  const ADS_URL    = '/static/data/ads.json';
  const LIST_ID    = 'newsContainer';
  const CARD_CLASS = 'news-post';
  const SP_ATTR    = 'data-sponsor';
  const CFG_KEY    = 'native_ads';
  const IS_DEBUG   = new URLSearchParams(location.search).has('debug');

  const list = document.getElementById(LIST_ID);
  if (!list) return;

  // ---------- GA4 helpers ----------
  function ga(eventName, payload) {
    try {
      if (typeof gtag === 'function') {
        gtag('event', eventName, { ...payload, debug_mode: IS_DEBUG });
      }
    } catch (_) {}
  }
  // Use GA4 recommended promo events
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

  // ---------- Load config ----------
  let adsCfg = null;
  let adQueue = []; // simple round-robin

  function isNativeCard(x) {
    // 关键：过滤掉 Google 卡，且仅保留启用的原生卡
    return x && x.google !== true && x.enabled !== false;
  }

  async function loadCfg() {
    try {
      const r = await fetch(ADS_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('ads.json ' + r.status);
      const json = await r.json();
      adsCfg = json && json[CFG_KEY];
      if (!adsCfg || adsCfg.enabled === false) return;

      // 只取“非 google”的原生卡
      adQueue = Array.isArray(adsCfg.cards) ? adsCfg.cards.filter(isNativeCard) : [];
      if (!adQueue.length) return;
      if (adsCfg.shuffle) adQueue.sort(() => Math.random() - 0.5);
    } catch (_) {}
  }

  function getPositions() {
    if (adsCfg && Array.isArray(adsCfg.positions) && adsCfg.positions.length) {
      return adsCfg.positions.map(n => parseInt(n, 10)).filter(n => n > 0);
    }
    return [3]; // default: insert after 3rd item
  }
  function pickCard() {
    if (!adQueue.length) return null;
    const ad = adQueue.shift();
    adQueue.push(ad);
    return ad;
  }

  // ---------- Build card ----------
  function makeCard(ad) {
    const el = document.createElement('article');
    el.className = CARD_CLASS + ' sponsor';
    el.setAttribute(SP_ATTR, 'true');
    el.setAttribute('data-category', 'Sponsor');

    // Title (clickable; visual style toned down via CSS)
    const h = document.createElement('h3');
    const a = document.createElement('a');
    a.className = 'news-link';
    a.href = ad.href || '#';
    a.target = ad.target || '_blank';
    a.rel = 'sponsored nofollow noopener noreferrer';
    a.textContent = ad.title || '';
    h.appendChild(a);
    el.appendChild(h);

    // Image (with WebP→JPG fallback & responsive srcset/sizes)
    if (ad.img) {
      const link = document.createElement('a');
      link.href = a.href;
      link.target = a.target;
      link.rel = a.rel;

      const img = document.createElement('img');
      img.className = 'sponsor-img';
      img.loading = 'lazy';
      img.alt = ad.img_alt || ad.title || 'sponsor';

      // Bind fallback FIRST, then set sources to avoid race with cached 404
      img.onerror = () => {
        if (!img.dataset.fallbackTried) {
          img.dataset.fallbackTried = '1';
          const fb = ad.img_fallback || (ad.img || '').replace(/\.webp($|\?)/i, '.jpg$1');
          if (fb && fb !== img.currentSrc && fb !== img.src) img.src = fb;
        }
      };

      if (ad.srcset) img.srcset = ad.srcset;   // ← 支持 srcset
      if (ad.sizes)  img.sizes  = ad.sizes;    // ← 支持 sizes
      img.src = ad.img;

      link.appendChild(img);
      el.appendChild(link);
    }

    // Description
    if (ad.text) {
      const p = document.createElement('p');
      p.className = 'preview';
      p.textContent = ad.text;
      el.appendChild(p);
    }

    // Sponsor tag (same visual style as other tags)
    const tag = document.createElement('span');
    tag.className = 'tags';
    tag.textContent = '#Sponsor';
    el.appendChild(tag);

    // Click tracking (delegate any link inside the card)
    el.addEventListener('click', (e) => {
      const t = e.target.closest('a');
      if (!t) return;
      sendClick({
        id: el.dataset.spId,
        title: el.dataset.spTitle,
        brand: el.dataset.spBrand,
        slot: el.dataset.spSlot
      });
    });

    return el;
  }

  // ---------- Impression tracking ----------
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
              id: el.dataset.spId,
              title: el.dataset.spTitle,
              brand: el.dataset.spBrand,
              slot: el.dataset.spSlot
            });
            io.unobserve(el);
          }
        });
      }, { threshold: [0.5] });
    }
    io.observe(cardEl);
  }

  function clearOld() {
    list.querySelectorAll('[' + SP_ATTR + ']').forEach(n => n.remove());
  }

  function insertAdsOnce() {
    if (!adsCfg || adsCfg.enabled === false) return;
    if (!adQueue.length) return;

    clearOld();

    const cards = list.querySelectorAll('.' + CARD_CLASS + ':not([' + SP_ATTR + '])');
    if (!cards.length) return;

    const pos = getPositions();
    pos.forEach(idx => {
      const ad = pickCard();
      if (!ad) return;

      const cardEl = makeCard(ad);
      // Attach meta for GA
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

  // ---------- Init & hooks ----------
  (async function init() {
    await loadCfg();
    // First try after config is ready
    insertAdsOnce();

    // Re-insert after each page change (your pager dispatches this)
    document.addEventListener('pager:update', () => {
      setTimeout(insertAdsOnce, 0); // allow DOM render
    });

    // Fallback initial try if DOM was already ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(insertAdsOnce, 0));
    }
  })();
})();
