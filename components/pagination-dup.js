// components/pagination-dup.js
(function () {
  const el = document.getElementById('pagination-bottom');
  if (!el) return;

  function state() {
    const P = window.Pager;
    if (!P) return { current: 1, total: 1 };
    return { current: Number(P.current) || 1, total: Number(P.total) || 1 };
  }

  function render() {
    const { current, total } = state();
    el.innerHTML = '';

    const prev = document.createElement('button');
    prev.type = 'button';
    prev.textContent = '← Prev';
    prev.disabled = current <= 1;
    prev.addEventListener('click', (e) => { e.preventDefault(); window.Pager?.prev(); });

    const info = document.createElement('span');
    info.className = 'page-info';
    info.textContent = `Page ${current} of ${total}`;

    const next = document.createElement('button');
    next.type = 'button';
    next.textContent = 'Next →';
    next.disabled = current >= total;
    next.addEventListener('click', (e) => { e.preventDefault(); window.Pager?.next(); });

    el.append(prev, info, next);
  }

  // 初次渲染（等 Pager 初始化完）
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(render, 0));
  } else {
    setTimeout(render, 0);
  }

  // 监听顶部翻页完成后的事件，保持底部同步
  document.addEventListener('pager:update', render);
})();
