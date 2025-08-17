// components/pagination-bottom.js
(function () {
  const el = document.getElementById('pagination-bottom');
  if (!el) return;

  function hrefFor(page) {
    // page=1 用根路径，不带 ?page
    const url = new URL(location.href);
    if (page <= 1) {
      url.searchParams.delete('page');
    } else {
      url.searchParams.set('page', String(page));
    }
    // 只返回 path+search，避免跨域问题
    return url.pathname + (url.search ? url.search : '');
  }

  function render(current, total) {
    el.innerHTML = '';

    const prev = document.createElement('a');
    prev.textContent = '← Prev';
    prev.className = 'pager-prev';
    if (current > 1) {
      prev.href = hrefFor(current - 1);  // 真实链接，整页刷新
    } else {
      prev.setAttribute('aria-disabled', 'true');
      prev.style.pointerEvents = 'none';
      prev.style.opacity = '0.45';
    }

    const info = document.createElement('span');
    info.className = 'page-info';
    info.textContent = `Page ${current} of ${total}`;

    const next = document.createElement('a');
    next.textContent = 'Next →';
    next.className = 'pager-next';
    if (current < total) {
      next.href = hrefFor(current + 1);
    } else {
      next.setAttribute('aria-disabled', 'true');
      next.style.pointerEvents = 'none';
      next.style.opacity = '0.45';
    }

    el.append(prev, info, next);
  }

  // 等 Pager 初始化好后渲染一次；之后监听更新事件重渲染
  function initOnce() {
    const P = window.Pager;
    if (!P || !Number.isFinite(Number(P.current)) || !Number.isFinite(Number(P.total))) {
      return false;
    }
    render(Number(P.current), Number(P.total));
    return true;
  }

  // 1) 首次初始化（最多等 2 秒）
  let tries = 0;
  const t = setInterval(() => {
    if (initOnce() || ++tries > 20) clearInterval(t);
  }, 100);

  // 2) 顶部翻页完成后同步状态
  document.addEventListener('pager:update', (e) => {
    const { current, total } = e.detail || {};
    if (Number.isFinite(current) && Number.isFinite(total)) {
      render(current, total);
    }
  });
})();
