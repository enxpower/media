<!-- /components/adslot-google.js -->
<script>
(function () {
  if (window.__adslot_google_init__) return;
  window.__adslot_google_init__ = true;

  const JSON_URL = '/static/data/ads.json';          // 你的配置
  const CONTAINER_ID = 'newsContainer';
  const CARD_SELECTOR = '.news-post';
  const SPONSOR_CLASS = 'sponsor';
  const MIN_CONTENT_HEIGHT = 120;
  const EXTRA_PADDING_EST = 24;

  function log(){ try{ console.log.apply(console, ['[adslot]'].concat([].slice.call(arguments))); }catch(e){} }

  async function fetchJSON(u){
    const r = await fetch(u, { cache:'no-store' });
    if (!r.ok) throw new Error('HTTP '+r.status);
    return r.json();
  }

  function medianHeight(nodes){
    const hs = nodes.map(n => n.getBoundingClientRect().height).filter(h => h>0).sort((a,b)=>a-b);
    if (!hs.length) return 220;
    const m = Math.floor(hs.length/2);
    return hs.length%2? hs[m] : Math.round((hs[m-1]+hs[m])/2);
  }

  // 依据容器宽度选定“固定像素”的矩形
  function chooseFixedRect(container){
    const w = container.getBoundingClientRect().width || 0;
    if (w >= 336) return { w: 336, h: 280 };
    if (w >= 300) return { w: 300, h: 250 };
    // 超窄时给一个最小矩形（不常见）
    return { w: 250, h: 200 };
  }

  function buildAdCard(baseContentHeight, slotConf, container){
    const card = document.createElement('div');
    card.className = `news-post ${SPONSOR_CLASS}`;
    card.dataset.category = 'General';

    const h3 = document.createElement('h3');
    const a = document.createElement('a');
    a.className = 'news-link';
    a.href = 'javascript:void(0)';
    a.setAttribute('aria-label', 'Sponsored');
    a.textContent = 'Sponsored';
    h3.appendChild(a);

    const meta = document.createElement('div');
    meta.className = 'meta';
    const badge = document.createElement('span');
    badge.className = 'source-badge';
    badge.textContent = 'Sponsored';
    meta.appendChild(badge);

    const summary = document.createElement('div');
    summary.className = 'summary';
    // 居中容器
    summary.style.display = 'flex';
    summary.style.justifyContent = 'center';
    summary.style.alignItems = 'center';

    const headH = Math.round((h3.getBoundingClientRect().height||0) + (meta.getBoundingClientRect().height||0) + EXTRA_PADDING_EST);
    const targetContentH = Math.max(MIN_CONTENT_HEIGHT, baseContentHeight - headH);

    const box = chooseFixedRect(container);
    const finalContentH = Math.max(targetContentH, box.h);
    summary.style.minHeight = finalContentH + 'px';

    const ins = document.createElement('ins');
    ins.className = 'adsbygoogle';
    // 关键：固定像素宽高 + inline-block，确保是标准矩形
    ins.style.cssText = `display:inline-block;width:${box.w}px;height:${box.h}px`;
    ins.setAttribute('data-ad-client', slotConf.client);
    ins.setAttribute('data-ad-slot', String(slotConf.slot));
    ins.setAttribute('data-full-width-responsive', 'false');
    if (slotConf.adtest === true) ins.setAttribute('data-adtest', 'on');

    summary.appendChild(ins);
    card.appendChild(h3);
    card.appendChild(meta);
    card.appendChild(summary);

    return { card, ins };
  }

  function insertAfterIndex(container, node, index){
    const cards = container.querySelectorAll(CARD_SELECTOR);
    if (!cards.length) { container.appendChild(node); return; }
    const i = Math.max(0, Math.min(index, cards.length - 1));
    cards[i].after(node);
  }

  function ensureAdSense(client, cb){
    if (window.adsbygoogle && window.adsbygoogle.push) return cb();
    const existed = Array.from(document.scripts).some(s => (s.src||'').includes('pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'));
    const srcUrl = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='+encodeURIComponent(client);
    if (existed) {
      if (document.readyState === 'complete') cb();
      else window.addEventListener('load', cb, { once:true });
      return;
    }
    const s = document.createElement('script');
    s.async = true;
    s.src = srcUrl;
    s.crossOrigin = 'anonymous';
    s.onload = cb;
    document.head.appendChild(s);
  }

  async function main(){
    try{
      const cfg = await fetchJSON(JSON_URL);
      const na = cfg && cfg.native_ads;
      if (!na || na.enabled !== true) return;

      // 在 cards 里找 google=true 的条目
      const items = (Array.isArray(na.cards) ? na.cards : [])
        .filter(x => x && x.enabled === true && x.google === true && x.client && x.slot);

      if (!items.length) return;

      const container = document.getElementById(CONTAINER_ID) || document.body;
      const baseH = medianHeight(Array.from(container.querySelectorAll(`${CARD_SELECTOR}:not(.${SPONSOR_CLASS})`)));

      const client = items[0].client; // 载入一次脚本即可
      ensureAdSense(client, function(){
        items.forEach(item => {
          const after = Number.isFinite(item.insert_after) ? item.insert_after
                        : (item.insert_after ? parseInt(item.insert_after, 10) : 4);
          const { card, ins } = buildAdCard(baseH, item, container);
          insertAfterIndex(container, card, after);
          try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch(e){ log('push err', e); }
        });
      });
    }catch(e){
      log('err', e);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', main);
  else main();
  window.addEventListener('load', () => setTimeout(main, 50), { once:true });
})();
</script>
