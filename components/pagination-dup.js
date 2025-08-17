// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';

  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  if (!topEl || !bottomEl) return;

  const $all = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const txt = (n) => (n?.textContent || '').trim();
  const has = (s, needles) => needles.some(w => s.includes(w));

  // 归一化文本：去箭头/符号/空格，仅保留字母与中/英文关键字
  const norm = (s) =>
    (s || '')
      .toLowerCase()
      .replace(/[\u2190\u2192]/g, '')     // ← →
      .replace(/\s+/g, '')
      .replace(/[^a-z\u4e00-\u9fa5\d]/g, ''); // 仅字母数字与中文

  function findTopPrev() {
    return topEl.querySelector('a.prev,button.prev,[aria-label*="prev" i],[aria-label*="上一"]')
      || $all('a,button', topEl).find(n => {
        const s = norm(txt(n));
        return has(s, ['prev', 'previous', '上一页', '上一頁', '上一步']);
      }) || null;
  }
  function findTopNext() {
    return topEl.querySelector('a.next,button.next,[aria-label*="next" i],[aria-label*="下一"]')
      || $all('a,button', topEl).find(n => {
        const s = norm(txt(n));
        return has(s, ['next', '下一页', '下一頁', '下一步']);
      }) || null;
  }
  function findTopPage(num) {
    return $all('a,button', topEl).find(n => txt(n) === String(num)) || null;
  }

  function bindDelegation() {
    bottomEl.onclick = (e) => {
      const t = e.target.closest('a,button');
      if (!t) return;

      const s = norm(txt(t));
      let targetTop = null;

      if (has(s, ['prev', 'previous', '上一页', '上一頁', '上一步'])) {
        targetTop = findTopPrev();
      } else if (has(s, ['next', '下一页', '下一頁', '下一步'])) {
        targetTop = findTopNext();
      } else {
        const n = parseInt((txt(t) || '').replace(/[^\d]/g, ''), 10);
        if (!isNaN(n)) targetTop = findTopPage(n);
      }

      if (targetTop && !targetTop.disabled) {
        e.preventDefault();
        e.stopPropagation();
        targetTop.click();          // 直接触发顶部按钮
      }
    };
  }

  function renderBottom() {
    if (!topEl.innerHTML || !topEl.innerHTML.trim()) return;
    bottomEl.className = topEl.className
      ? topEl.className + ' pagination--bottom'
      : 'pagination--bottom';
    bottomEl.innerHTML = topEl.innerHTML;
    bindDelegation();
  }

  // 等待顶部分页渲染
  let tries = 0;
  const poll = setInterval(() => {
    tries++;
    if (topEl.innerHTML && topEl.innerHTML.trim()) {
      clearInterval(poll);
      renderBottom();
    }
    if (tries > 60) clearInterval(poll); // ~12s 兜底
  }, 200);

  // 顶部分页变化时同步到底部
  new MutationObserver(renderBottom)
    .observe(topEl, { childList: true, subtree: true, characterData: true });

  // 浏览器往返缓存恢复时再同步一次
  window.addEventListener('pageshow', renderBottom);
})();
