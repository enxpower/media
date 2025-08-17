// components/pagination-dup.js
(function () {
  const bottomEl = document.getElementById('pagination-bottom');
  if (!bottomEl) return;

  let lastCurrent = null;
  let lastTotal = null;

  function getPagerState() {
    const P = window.Pager;
    if (!P) return null;
    const current = Number(P.current);
    const total = Number(P.total);
    if (!Number.isFinite(current) || !Number.isFinite(total)) return null;
    return { current, total };
  }

  function render({ current, total }) {
    // 只根据 Pager 状态生成底部控件，不再克隆顶部，样式由 CSS 统一
    bottomEl.innerHTML = '';

    const prev = document.createElement('button');
    prev.textContent = '← Prev';
    prev.disabled = current <= 1;
    prev.dataset.action = 'prev';

    const info = document.createElement('span');
    info.className = 'page-info';
    info.textContent = `Page ${current} of ${total}`;

    const next = document.createElement('button');
    next.textContent = 'Next →';
    next.disabled = current >= total;
    next.dataset.action = 'next';

    bottomEl.append(prev, info, next);
  }

  // 只绑定一次，永不重复绑定
  bottomEl.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();

    const P = window.Pager;
    if (!P) return;

    const act = btn.dataset.action;
    if (act === 'prev') P.prev();
    else if (act === 'next') P.next();
  });

  // 轮询 Pager 状态变更（翻页后会变化），变化时重渲染底部
  function tick() {
    const s = getPagerState();
    if (s && (s.current !== lastCurrent || s.total !== lastTotal)) {
      render(s);
      lastCurrent = s.current;
      lastTotal = s.total;
    }
    setTimeout(tick, 250);
  }

  tick(); // 启动
})();
