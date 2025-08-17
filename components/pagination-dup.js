// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';
  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  if (!topEl || !bottomEl) return;

  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const txt = (n) => (n?.textContent || '').trim();
  const norm = (s='') =>
    s.toLowerCase().replace(/[\u2190\u2192]/g,'').replace(/\s+/g,'').replace(/[^a-z\u4e00-\u9fa5\d]/g,'');

  const hasAny = (s, arr) => arr.some(w => s.includes(w));

  // 把顶部分页克隆到底部
  function renderBottom() {
    if (!topEl.innerHTML || !topEl.innerHTML.trim()) return;
    bottomEl.className = topEl.className ? topEl.className + ' pagination--bottom' : 'pagination--bottom';
    bottomEl.innerHTML = topEl.innerHTML;
  }

  // 顶部分页变化时，同步到底部
  new MutationObserver(renderBottom)
    .observe(topEl, { childList: true, subtree: true, characterData: true });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderBottom);
  } else {
    renderBottom();
  }

  // 兜底：在顶部分页里找 Prev/Next 按钮
  function findTopPrev() {
    return topEl.querySelector('button, a'); // 你的顶部只有两个按钮：prev / next
  }
  function findTopNext() {
    const btns = $$('.page-info ~ button, .page-info ~ a', topEl);
    return btns[0] || null;
  }

  // 底部点击 → 直接走同一套翻页逻辑（优先用 Pager）
  bottomEl.addEventListener('click', (e) => {
    const n = e.target.closest('a,button');
    if (!n) return;
    e.preventDefault();
    e.stopImmediatePropagation();

    const s = norm(txt(n));

    // 1) 优先用 window.Pager（你当前 pagination.js 已暴露它）
    if (window.Pager && typeof window.Pager.goto === 'function') {
      if (hasAny(s, ['prev','previous','上一页','上一頁','上一步'])) { window.Pager.prev(); return; }
      if (hasAny(s, ['next','下一页','下一頁','下一步']))         { window.Pager.next(); return; }
      const num = parseInt((txt(n) || '').replace(/[^\d]/g,''), 10);
      if (!Number.isNaN(num)) { window.Pager.goto(num); return; }
    }

    // 2) 没有 Pager（基本用不到）：给顶部分页按钮派发“合成点击”（不会聚焦，不会把视口滚到它）
    let target = null;
    if (hasAny(s, ['prev','previous','上一页','上一頁','上一步'])) target = findTopPrev();
    else if (hasAny(s, ['next','下一页','下一頁','下一步']))     target = findTopNext();
    if (!target || target.disabled) return;
    target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
  });
})();
