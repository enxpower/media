// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';

  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  if (!topEl || !bottomEl) return;

  const $all = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const txt  = (n) => (n?.textContent || '').trim();
  const has  = (s, needles) => needles.some(w => s.includes(w));
  const norm = (s) =>
    (s || '')
      .toLowerCase()
      .replace(/[\u2190\u2192]/g, '')       // ← →
      .replace(/\s+/g, '')
      .replace(/[^a-z\u4e00-\u9fa5\d]/g, ''); // 仅字母数字与中文

  function findTopPrev() {
    return topEl.querySelector('a.prev,button.prev,[aria-label*="prev" i],[aria-label*="上一"]')
      || $all('a,button', topEl).find(n => has(norm(txt(n)), ['prev','previous','上一页','上一頁','上一步']))
      || null;
  }
  function findTopNext() {
    return topEl.querySelector('a.next,button.next,[aria-label*="next" i],[aria-label*="下一"]')
      || $all('a,button', topEl).find(n => has(norm(txt(n)), ['next','下一页','下一頁','下一步']))
      || null;
  }
  function findTopPage(num) {
    return $all('a,button', topEl).find(n => txt(n) === String(num)) || null;
  }

  // 只派发“合成点击”，不聚焦、不调用 .click()，因此不会触发任何滚动到视口的行为
  function forwardToTop(targetTop) {
    if (!targetTop || targetTop.disabled) return;
    const ev = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
    targetTop.dispatchEvent(ev);
  }

  function bindDelegation() {
    bottomEl.onclick = (e) => {
      const t = e.target.closest('a,button');
      if (!t) return;

      // 阻止默认与冒泡，避免锚点/按钮默认行为造成页面位置变化
      e.preventDefault();
      e.stopImmediatePropagation();

      const s = norm(txt(t));
      let topBtn = null;

      if (has(s, ['prev','previous','上一页','上一頁','上一步'])) {
        topBtn = findTopPrev();
      } else if (has(s, ['next','下一页','下一頁','下一步'])) {
        topBtn = findTopNext();
      } else {
        const n = parseInt((txt(t) || '').replace(/[^\d]/g, ''), 10);
        if (!isNaN(n)) topBtn = findTopPage(n);
      }

      forwardToTop(topBtn);
    };
  }

  function renderBottom() {
    if (!topEl.innerHTML || !topEl.innerHTML.trim()) return;
    bottomEl.className = topEl.className
      ? topEl.className + ' pagination--bottom'
      : 'pagination--bottom';
    bottomEl.innerHTML = topEl.innerHTML;
    bindDelegation(); // 每次重渲染都重新绑定
  }

  // 等待顶部分页出现
  let tries = 0;
  const poll = setInterval(() => {
    tries++;
    if (topEl.innerHTML && topEl.innerHTML.trim()) {
      clearInterval(poll);
      renderBottom();
    }
    if (tries > 60) clearInterval(poll); // ~12s
  }, 200);

  // 顶部分页变化时同步到底部
  new MutationObserver(renderBottom)
    .observe(topEl, { childList: true, subtree: true, characterData: true });

  // 往返缓存恢复时同步一次
  window.addEventListener('pageshow', renderBottom);
})();
