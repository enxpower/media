// components/pagination-dup.js
(function () {
  const TOP_ID = 'pagination';
  const BOTTOM_ID = 'pagination-bottom';

  const topEl = document.getElementById(TOP_ID);
  const bottomEl = document.getElementById(BOTTOM_ID);
  if (!topEl || !bottomEl) return;

  // 找“上一页 / 下一页 / 页码”的通用方法
  function getText(n){ return (n?.textContent || '').trim(); }
  function findBtn(container, which) {
    const isPrev = which === 'prev';
    const txtRe = isPrev ? /^(prev|previous|上一[页頁])$/i : /^(next|下一[页頁])$/i;

    // 先按常见 class
    let el = container.querySelector(isPrev ? 'a.prev,button.prev' : 'a.next,button.next');
    if (el) return el;

    // 再找 aria-label
    el = Array.from(container.querySelectorAll('a[aria-label],button[aria-label]'))
      .find(n => txtRe.test((n.getAttribute('aria-label')||'').trim()));
    if (el) return el;

    // 最后按可见文本
    el = Array.from(container.querySelectorAll('a,button')).find(n => txtRe.test(getText(n)));
    return el || null;
  }

  function findPageBtnByNumber(container, num) {
    return Array.from(container.querySelectorAll('a,button'))
      .find(n => getText(n) === String(num)) || null;
  }

  // 同步渲染 bottom
  function renderBottom() {
    const html = topEl.innerHTML;
    if (!html || !html.trim()) return;

    // 复制内容 & 类名，尽量复用顶部样式
    bottomEl.className = topEl.className ? topEl.className + ' pagination--bottom' : 'pagination--bottom';
    bottomEl.innerHTML = html;

    // 事件委托：任何点击都映射到顶部对应元素
    bottomEl.addEventListener('click', function (e) {
      const t = e.target.closest('a,button');
      if (!t) return;

      e.preventDefault();
      e.stopPropagation();

      const txt = getText(t).toLowerCase();
      let targetTop;

      if (/^(prev|previous|上一[页頁])$/.test(txt)) {
        targetTop = findBtn(topEl, 'prev');
      } else if (/^(next|下一[页頁])$/.test(txt)) {
        targetTop = findBtn(topEl, 'next');
      } else {
        // 页码
        const n = parseInt(txt.replace(/[^\d]/g, ''), 10);
        if (!isNaN(n)) targetTop = findPageBtnByNumber(topEl, n);
      }

      if (targetTop) {
        targetTop.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      }
    }, { once: true }); // 渲染一次绑定一次（后续变更会重新渲染并重新绑定）
  }

  // 1) 轮询等待顶部真正渲染完成
  let tries = 0;
  const timer = setInterval(() => {
    tries++;
    if (topEl.innerHTML && topEl.innerHTML.trim()) {
      clearInterval(timer);
      renderBottom();
    }
    if (tries > 60) clearInterval(timer); // 最多 ~12 秒
  }, 200);

  // 2) 监听顶部变化（翻页后会变化），自动同步到底部
  const obs = new MutationObserver(renderBottom);
  obs.observe(topEl, { childList: true, subtree: true, characterData: true });

  // 3) 浏览器往返缓存恢复时同步一次
  window.addEventListener('pageshow', renderBottom);
})();
