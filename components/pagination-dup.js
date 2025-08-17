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
    s.toLowerCase()
     .replace(/[\u2190\u2192]/g, '')   // ← →
     .replace(/\s+/g, '')
     .replace(/[^a-z\u4e00-\u9fa5\d]/g, '');

  const hasAny = (s, arr) => arr.some(w => s.includes(w));

  function findTopPrev() {
    return topEl.querySelector('a.prev,button.prev,[aria-label*="prev" i],[aria-label*="上一"]')
        || $$('a,button', topEl).find(n => hasAny(norm(txt(n)), ['prev','previous','上一页','上一頁','上一步']))
        || null;
  }
  function findTopNext() {
    return topEl.querySelector('a.next,button.next,[aria-label*="next" i],[aria-label*="下一"]')
        || $$('a,button', topEl).find(n => hasAny(norm(txt(n)), ['next','下一页','下一頁','下一步']))
        || null;
  }
  function findTopPage(num) {
    return $$('a,button', topEl).find(n => txt(n) === String(num)) || null;
  }

  // 把顶部分页克隆到底部
  function renderBottom() {
    if (!topEl.innerHTML || !topEl.innerHTML.trim()) return;
    bottomEl.className = topEl.className ? topEl.className + ' pagination--bottom' : 'pagination--bottom';
    bottomEl.innerHTML = topEl.innerHTML;
  }

  // 同步：顶部分页变化时，底部一起更新
  new MutationObserver(renderBottom)
    .observe(topEl, { childList: true, subtree: true, characterData: true });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderBottom);
  } else {
    renderBottom();
  }

  // 底部点击：调用同一套翻页逻辑（优先用 Pager），否则把点击派发给顶部分页按钮
  bottomEl.addEventListener('click', (e) => {
    const n = e.target.closest('a,button');
    if (!n) return;
    e.preventDefault();
    e.stopImmediatePropagation();

    const s = norm(txt(n));

    // 1) 若你用了我之前给的 pagination.js（已暴露 window.Pager），直接调用更稳，不会提前滚动
    if (window.Pager && typeof window.Pager.goto === 'function') {
      if (hasAny(s, ['prev','previous','上一页','上一頁','上一步'])) {
        window.Pager.prev();
        return;
      }
      if (hasAny(s, ['next','下一页','下一頁','下一步'])) {
        window.Pager.next();
        return;
      }
      const num = parseInt((txt(n) || '').replace(/[^\d]/g, ''), 10);
      if (!Number.isNaN(num)) {
        window.Pager.goto(num);
        return;
      }
    }

    // 2) 兜底：没有 Pager 时，派发合成 click 到顶部分页按钮（不聚焦、不触发默认导航）
    let target = null;
    if (hasAny(s, ['prev','previous','上一页','上一頁','上一步'])) {
      target = findTopPrev();
    } else if (hasAny(s, ['next','下一页','下一頁','下一步'])) {
      target = findTopNext();
    } else {
      const num = parseInt((txt(n) || '').replace(/[^\d]/g, ''), 10);
      if (!Number.isNaN(num)) target = findTopPage(num);
    }
    if (!target || target.disabled) return;

    target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
  });
})();
