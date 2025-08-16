document.addEventListener("DOMContentLoaded", () => {
  const paginationContainer = document.getElementById("pagination");
  const newsContainer = document.getElementById("newsContainer");

  let currentPage = 1;
  let totalPages = 1;

  // -------- utils --------
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

  function getPageFromURL() {
    // 支持 ?page= 和 #page=
    const s = new URLSearchParams(window.location.search);
    if (s.has("page")) {
      const n = parseInt(s.get("page"), 10);
      if (!Number.isNaN(n)) return n;
    }
    const m = window.location.hash.match(/page=(\d+)/i);
    if (m) {
      const n = parseInt(m[1], 10);
      if (!Number.isNaN(n)) return n;
    }
    return null;
  }

  function setURLPage(page) {
    // 统一使用 ?page=，同时清掉 hash，避免浏览器保留旧的 #page=3
    const url = new URL(window.location.href);
    url.searchParams.set("page", String(page));
    url.hash = "";
    window.history.replaceState({}, "", url.toString());
  }

  // -------- discovery --------
  async function detectTotalPages() {
    let i = 1;
    // HEAD 探测 pageN.html 是否存在
    while (true) {
      const res = await fetch(`posts/page${i}.html`, { method: "HEAD", cache: "no-store" });
      if (!res.ok) break;
      i++;
      // 防守：最多探测 500 页
      if (i > 500) break;
    }
    totalPages = i - 1;
    if (totalPages < 1) totalPages = 1;
  }

  // -------- render/load --------
  async function loadPage(page) {
    const url = `posts/page${page}.html?v=${Date.now()}`; // cache-bust
    const res = await fetch(url);
    if (!res.ok) {
      newsContainer.innerHTML = `<p style="text-align:center;color:#888;">Page ${page} not found.</p>`;
      return;
    }
    const html = await res.text();
    newsContainer.innerHTML = html;
    window.scrollTo(0, 0);
  }

  function renderPagination() {
    paginationContainer.innerHTML = "";

    const prevBtn = document.createElement("button");
    prevBtn.textContent = "← Prev";
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => goTo(currentPage - 1);

    const pageLabel = document.createElement("span");
    pageLabel.className = "page-info";
    pageLabel.textContent = `Page ${currentPage} of ${totalPages}`;

    const nextBtn = document.createElement("button");
    nextBtn.textContent = "Next →";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => goTo(currentPage + 1);

    paginationContainer.appendChild(prevBtn);
    paginationContainer.appendChild(pageLabel);
    paginationContainer.appendChild(nextBtn);
  }

  async function goTo(page) {
    currentPage = clamp(page, 1, totalPages);
    setURLPage(currentPage);   // 同步地址栏
    await loadPage(currentPage);
    renderPagination();
  }

  // -------- init --------
  (async function init() {
    await detectTotalPages();

    // 只有当 URL 显式带了 page 参数时才用它，否则**强制**回到第一页
    const requested = getPageFromURL();
    currentPage = clamp(requested ?? 1, 1, totalPages);

    // 如果没有 page 参数（或是无效参数），把 ?page=1 写回地址栏
    if (requested == null) setURLPage(currentPage);

    await loadPage(currentPage);
    renderPagination();

    // 监听 hash 变化（例如外部手动改 #page=2）
    window.addEventListener("hashchange", () => {
      const p = getPageFromURL();
      if (p != null && p !== currentPage) goTo(p);
    });

    // 监听浏览器前进后退
    window.addEventListener("popstate", () => {
      const p = getPageFromURL();
      goTo(p == null ? 1 : p);
    });
  })();
});
