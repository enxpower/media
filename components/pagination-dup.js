// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';

  function $(sel, root = document) { return root.querySelector(sel); }
  function text(el) { return (el?.textContent || '').trim(); }

  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  if (!topEl || !bottomEl) return;

  // 找按钮的通用方法（尽量兼容不同写法）
  function findBtn(container, which) {
    const txt = which === 'prev'
      ? /^(prev|previous|上一页|上一頁)$/i
      : /^(next|下一页|下一頁)$/i;

    // 优先按 class
    let el = container.querySelector(which === 'prev'
      ? 'a.prev,button.prev'
      : 'a.next,button.next');

    if (el) return el;

    // 退而求其次：找 a/button，看可见文本
    el = Array.from(container.querySelectorAll('a,button')).find(n => txt.test(text(n)));
    if (el) return el;

    // 再次尝试：按 aria-label
    el = Array.from(container.querySelectorAll('a[aria-label],button[aria-label]'))
      .find(n => txt.test(n.getAttribute('aria-label') || ''));
    return el || null;
  }

  // 克隆顶部分页到底部，并设置事件转发（仅当顶部不是 <a href> 时才拦截）
  function renderBottom() {
    const html = topEl.innerHTML;
    if (!html || !html.trim()) return;

    bottomEl.innerHTML = html;

    // 事件转发（顶部分页如果是纯<a>，直接自然跳转；如果是JS按钮，这里兜底）
    const topPrev = findBtn(topEl, 'prev');
    const topNext = findBtn(topEl, 'next');
    const bottomPrev = findBtn(bottomEl, 'prev');
    const bottomNext = findBtn(bottomEl, 'next');

    function forward(bottomBtn, topBtn) {
      if (!bottomBtn || !topBtn) return;
      // 如果底部就是 <a href>，不需要拦截
      const isAnchor = bottomBtn.tagName === 'A' && bottomBtn.getAttribute('href');
      if (isAnchor) return;
      bottomBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        topBtn.click();
      });
    }

    forward(bottomPrev, topPrev);
    forward(bottomNext, topNext);
  }

  // 1) 轮询等待顶部分页出现一次
  let tries = 0;
  const timer = setInterval(() => {
    tries++;
    if (topEl.innerHTML && topEl.innerHTML.trim()) {
      clearInterval(timer);
      renderBottom();
    }
    if (tries > 50) clearInterval(timer); // 最多10秒
  }, 200);

  // 2) 监听顶部分页变化（比如翻页后）
  const obs = new MutationObserver(() => renderBottom());
  obs.observe(topEl, { childList: true, subtree: true, characterData: true });

  // 3) 页面恢复（Back/Forward 缓存）
  window.addEventListener('pageshow', renderBottom);
})();
