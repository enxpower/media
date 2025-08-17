// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';
  const LIST_ID = 'newsContainer';   // 内容容器，用来监听“翻页后列表变化”

  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  const listEl = document.getElementById(LIST_ID);
  if (!topEl || !bottomEl || !listEl) return;

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

  // 把顶部分页的当前 DOM 克隆到底部
  function renderBottom() {
    if (!topEl.innerHTML || !topEl.innerHTML.trim()) return;
    bottomEl.className = topEl.className ? topEl.className + ' pagination--bottom' : 'pagination--bottom';
    bottomEl.innerHTML = topEl.innerHTML;
  }

  // 监听顶部分页更新（翻页后文本会变），同步到底部
  new MutationObserver(renderBottom)
    .observe(topEl, { childList: true, subtree: true, characterData: true });

  // —— 关键：只要“底部触发了翻页”，等列表 DOM 发生变化后把页面滚到顶部 —— //
  let needScrollToTop = false;
  new MutationObserver(() => {
    if (!needScrollToTop) return;
    // 新页内容已渲染到 DOM，立刻回到顶部（想要平滑滚动把 'auto' 改成 'smooth'）
    window.scrollTo({ top: 0, behavior: 'auto' });
    needScrollToTop = false;
  }).observe(listEl, { childList: true, subtree: false });

  // 底部分页的事件代理：触发同一套分页逻辑，并标记 needScrollToTop
  bottomEl.addEventListener('click', (e) => {
    const n = e.target.closest('a,button');
    if (!n) return;
    e.preventDefault();
    e.stopImmediatePropagation();

    const s = norm(txt(n));
    let topBtn = null;
    if (hasAny(s, ['prev','previous','上一页','上一頁','上一步'])) {
      topBtn = findTopPrev();
    } else if (hasAny(s, ['next','下一页','下一頁','下一步'])) {
      topBtn = findTopNext();
    } else {
      const num = parseInt((txt(n) || '').replace(/[^\d]/g, ''), 10);
      if (!Number.isNaN(num)) topBtn = findTopPage(num);
    }
    if (!topBtn || topBtn.disabled) return;

    // 触发顶部分页的同一段 JS 逻辑（合成事件，不产生默认滚动）
    const ev = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
    needScrollToTop = true;            // 标记：下一次列表变更后滚到顶部
    topBtn.dispatchEvent(ev);
  });

  // 首次克隆
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderBottom);
  } else {
    renderBottom();
  }
})();
