// components/outboundTracker.js
// Track outbound link clicks in GA4, but ignore native sponsor ads to avoid double-counting.
// Also handles middle-click (open in new tab). Add ?debug=1 to enable GA4 debug_mode.

(function () {
  const IS_DEBUG = new URLSearchParams(location.search).has('debug');

  function isHttp(href) {
    return /^https?:/i.test(href || '');
  }

  function isExternal(href) {
    try {
      const u = new URL(href, location.href);
      return u.hostname !== location.hostname;
    } catch {
      return false;
    }
  }

  function findTrackableLink(event) {
    const a = event.target && event.target.closest && event.target.closest('a[href]');
    if (!a) return null;
    if (!isHttp(a.getAttribute('href'))) return null;           // skip mailto/tel/javascript
    if (a.closest('[data-sponsor]')) return null;               // ✅ ignore native sponsor links
    if (a.hasAttribute('data-no-track')) return null;           // optional opt-out
    return a;
  }

  function trackOutbound(href) {
    try {
      if (typeof gtag !== 'function') return;
      gtag('event', 'click', {
        event_category: 'outbound',
        event_label: href,
        transport_type: 'beacon',
        debug_mode: IS_DEBUG
      });
    } catch (_) {}
  }

  function handle(event) {
    const link = findTrackableLink(event);
    if (!link) return;
    const href = link.href;
    if (!isExternal(href)) return;
    trackOutbound(href);
  }

  // Left-click
  document.addEventListener('click', handle, false);
  // Middle-click (auxclick with button===1)
  document.addEventListener('auxclick', (e) => {
    if (e.button === 1) handle(e);
  }, false);
})();
