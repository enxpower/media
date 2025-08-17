// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';
  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  if (!topEl || !bottomEl) return;

  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const txt = (n) => (n?.textContent || '').trim();
  const norm = (s='') => s.toLowerCase().replace(/[\u2190\u2192]/g,'').replace(/\s+/g,'').replace(/[^a-z\u4e00-\u9fa5\d]/g,'');

  const hasAny = (s, arr) => arr.some(w => s.includes(w));
  const findTopPrev = () =>
    topEl.querySelector('a.prev,button.prev,[aria-label*="prev" i],[aria-label*="上一"]')
    || $$('a,button', topEl).find(n => hasAny(norm(txt(n)), ['prev','previous','上一页','上一頁','上一步'])) || null;
  const findTopNext = () =>
    topEl.querySelector('a.next,button.next,[aria-label*="next" i],[aria-label*="下一"]')
    || $$('a,button', topEl).find(n => hasAny(norm(txt(n)), ['next','下一页','下一頁','下一步'])) || null;
  const findTopPage = (num) =>
    $$('a,button', topEl).find(n => txt(n) === String(num)) || null;

  function renderBottom() {
    if (!topEl.innerHTML || !topEl.innerHTML.trim()) return;
    bottomEl.className = topEl.className ? topEl.className + ' pagination--bottom' : 'pagination--bottom';
    bottomEl.innerHTML = topEl.innerHTML;
  }

  // 同步顶部分页到底部
  new MutationObserver(renderBottom)
    .observe(topEl, { childList: true, subtree: true, characterData: true });
  (document.readyState === 'loading') ? document.addEventListener('DOMContentLoaded', renderBottom) : renderBottom();

  // 底部点击 -> 标记“不滚动” -> 触发顶部分页的同一段 JS 逻辑
  bottomEl.addEventListener('click', (e) => {
    const n = e.target.closest('a,button');
    if (!n) return;
    e.preventDefault();
    e.stopImmediatePropagation();

    let target = null;
    const s = norm(txt(n));
    if (hasAny(s, ['prev','previous','上一页','上一頁','上一步'])) {
      target = findTopPrev();
    } else if (hasAny(s, ['next','下一页','下一頁','下一步'])) {
      target = findTopNext();
    } else {
      const num = parseInt((txt(n) || '').replace(/[^\d]/g, ''), 10);
      if (!Number.isNaN(num)) target = findTopPage(num);
    }
    if (!target || target.disabled) return;

    // 关键：告诉顶层“这次来自底部”，从而跳过任何滚动代码
    window.__fromBottomPager = true;

    // 用“可取消的合成 click”触发同一段监听器（不聚焦，不触发默认导航）
    target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
  });
})();
