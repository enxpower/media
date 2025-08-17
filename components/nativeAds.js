// components/nativeAds.js
(function () {
  const ADS_URL = '/static/data/ads.json';
  const LIST_ID = 'newsContainer';
  const CARD_CLASS = 'news-post';
  const SP_ATTR = 'data-sponsor';     // 标记已插入的赞助卡
  const CFG_KEY = 'native_ads';

  const list = document.getElementById(LIST_ID);
  if (!list) return;

  let adsCfg = null;
  let adQueue = [];

  function log(...a){ try{console.log('[nativeAds]', ...a);}catch(e){} }

  async function loadCfg() {
    try {
      const r = await fetch(ADS_URL, { cache: 'no-store' });
      if (!r.ok) throw new Error('ads.json ' + r.status);
      const json = await r.json();
      adsCfg = json && json[CFG_KEY];
      if (!adsCfg || adsCfg.enabled === false) {
        log('disabled or no cfg');
        return;
      }
      adQueue = Array.isArray(adsCfg.cards) ? adsCfg.cards.slice() : [];
      if (!adQueue.length) return;
      if (adsCfg.shuffle) adQueue.sort(() => Math.random() - 0.5);
      log('cfg ok; cards:', adQueue.length);
    } catch (e) {
      log('load cfg failed:', e);
    }
  }

  function pickCard() {
    if (!adQueue.length) return null;
    // 轮换使用，确保同一页多位置不重复
    const ad = adQueue.shift();
    adQueue.push(ad);
    return ad;
  }

  function makeCard(ad) {
    // 结构与 .news-post 对齐
    const el = document.createElement('article');
    el.className = CARD_CLASS + ' sponsor';
    el.setAttribute(SP_ATTR, 'true');
    el.setAttribute('data-category', 'Sponsor'); // 继承你的分类色条机制（如需）
    // 标题
    const h = document.createElement('h3');
    const a = document.createElement('a');
    a.className = 'news-link';
    a.target = ad.target || '_blank';
    a.rel = 'sponsored nofollow noopener';
    a.href = ad.href || '#';
    a.textContent = ad.title || '';
    h.appendChild(a);

    // 元信息（左侧 #Sponsor 徽标 + 品牌）
    const meta = document.createElement('div');
    meta.className = 'meta';
    const badge = document.createElement('span');
    badge.className = 'source sponsor-badge';
    badge.textContent = '# Sponsor';
    meta.appendChild(badge);
    if (ad.brand) {
      const brand = document.createElement('span');
      brand.className = 'brand';
      brand.textContent = ad.brand;
      meta.appendChild(brand);
    }

    // 媒体（可选）
    let media = null;
    if (ad.img) {
      media = document.createElement('a');
      media.href = ad.href || '#';
      media.target = a.target;
      media.rel = a.rel;
      const img = document.createElement('img');
      img.src = ad.img;
      img.alt = ad.img_alt || ad.title || 'sponsor';
      img.loading = 'lazy';
      img.className = 'sponsor-img';
      media.appendChild(img);
    }

    // 文本（可选）
    let desc = null;
    if (ad.text) {
      desc = document.createElement('p');
      desc.className = 'preview';
      desc.textContent = ad.text;
    }

    el.append(h, meta);
    if (media) el.appendChild(media);
    if (desc) el.appendChild(desc);

    // 可选：点击埋点（GA4）
    try {
      el.addEventListener('click', (e) => {
        const t = e.target.closest('a');
        if (!t) return;
        if (typeof gtag === 'function') {
          gtag('event', 'sponsor_click', {
            event_category: 'sponsor',
            event_label: ad.id || ad.title || ad.href,
            value: 1
          });
        }
      });
    } catch (_) {}

    return el;
  }

  function clearOld() {
    list.querySelectorAll('['+SP_ATTR+']').forEach(n => n.remove());
  }

  function getPositions() {
    // 优先 positions；否则每页默认在第 4 个后面插入一个
    if (adsCfg && Array.isArray(adsCfg.positions) && adsCfg.positions.length) {
      // 只接受正整数（基于卡片 1-based 序）
      return adsCfg.positions.map(n => parseInt(n, 10)).filter(n => n > 0);
    }
    return [4];
  }

  function insertAdsOnce() {
    if (!adsCfg || adsCfg.enabled === false) return;
    if (!adQueue.length) return;

    clearOld();

    const cards = list.querySelectorAll('.' + CARD_CLASS + ':not(['+SP_ATTR+'])');
    if (!cards.length) return;

    const pos = getPositions();
    let inserted = 0;

    pos.forEach(idx => {
      const ad = pickCard();
      if (!ad) return;
      const cardEl = makeCard(ad);
      if (!cardEl) return;

      // 目标位置：在第 idx 个“新闻卡”之后插入赞助卡
      const anchor = cards[idx - 1]; // idx 基于 1
      if (anchor && anchor.parentNode) {
        anchor.insertAdjacentElement('afterend', cardEl);
        inserted++;
      } else {
        // 不够长则尾部附加
        list.appendChild(cardEl);
        inserted++;
      }
    });

    log('inserted:', inserted);
  }

  // 首次加载配置
  loadCfg();

  // 首屏：等待 pagination 首次渲染完会触发 pager:update
  document.addEventListener('pager:update', insertAdsOnce);
  // 兜底：如果 pager:update 没来（极小概率），DOMContentLoaded 后也尝试一次
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(insertAdsOnce, 0));
  } else {
    setTimeout(insertAdsOnce, 0);
  }
})();
