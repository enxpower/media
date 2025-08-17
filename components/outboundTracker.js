// components/outboundTracker.js  (v2)
// 目标：稳定记录 sponsor/outbound 点击到 GA4；事件名 sponsor_click，附带详细参数；
// 同时兼容普通外链，事件名 outbound_click。
// 在 GA4 DebugView 中强制可见（debug_mode: true）。

(function () {
  function onReady(fn){ 
    if (document.readyState!=='loading') fn(); 
    else document.addEventListener('DOMContentLoaded', fn);
  }

  function isExternal(a) {
    try {
      const u = new URL(a.href, location.href);
      return u.origin !== location.origin;
    } catch { return false; }
  }

  function sendGA(eventName, params) {
    // 强制进入 DebugView
    params = Object.assign({ debug_mode: true }, params || {});
    if (typeof window.gtag === 'function') {
      // 发送 GA4 事件
      window.gtag('event', eventName, params);
    } else {
      // 控制台兜底，方便排查
      console.log('[GA4 Fallback]', eventName, params);
    }
  }

  onReady(() => {
    document.body.addEventListener('click', (e) => {
      const a = e.target.closest('a[href]');
      if (!a) return;

      // 只记录外链
      if (!isExternal(a)) return;

      // Sponsor 卡（.news-post.sponsor）单独记 sponsor_click
      const sponsor = a.closest('.news-post.sponsor');
      if (sponsor) {
        const params = {
          link_url: a.href,
          link_domain: (new URL(a.href)).hostname,
          link_text: (a.textContent || '').trim().slice(0, 100),
          sp_id: sponsor.getAttribute('data-sp-id') || '',
          sp_title: sponsor.getAttribute('data-sp-title') || '',
          sp_brand: sponsor.getAttribute('data-sp-brand') || '',
          sp_slot: sponsor.getAttribute('data-sp-slot') || '',
        };
        sendGA('sponsor_click', params);   // ← 在 GA4 里搜这个事件名
        return;
      }

      // 其它普通外链（非 sponsor 卡）也记录一下
      const params2 = {
        link_url: a.href,
        link_domain: (new URL(a.href)).hostname,
        link_text: (a.textContent || '').trim().slice(0, 100),
        outbound: true
      };
      sendGA('outbound_click', params2);
    }, true); // capture 提高命中率
  });
})();
