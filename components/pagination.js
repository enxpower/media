// components/pagination.js
document.addEventListener("DOMContentLoaded", () => {
  const paginationContainer = document.getElementById("pagination");
  const newsContainer = document.getElementById("newsContainer");

  let currentPage = 1;
  let totalPages = 1;

  // ---- URL helpers ----
  function getPageFromURL() {
    const usp = new URLSearchParams(location.search);
    const n = parseInt(usp.get("page"), 10);
    return Number.isFinite(n) && n > 0 ? n : 1;
  }

  // page === 1 时移除参数，保持根路径干净
  function writePageToURL(page, { replace = false } = {}) {
    const url = new URL(location.href);
    if (page === 1) url.searchParams.delete("page");
    else url.searchParams.set("page", String(page));
    history[replace ? "replaceState" : "pushState"]({}, "", url);
  }

  // ---- Detect how many pages exist (HEAD即可) ----
  async function detectTotalPages() {
    let i = 1;
    while (true) {
      try {
        const res = await fetch(`posts/page${i}.html`, { method: "HEAD", cache: "no-store" });
        if (!res.ok) break;
        i++;
      } catch {
        break;
      }
    }
    totalPages = Math.max(1, i - 1);
  }

  // ---- Load a page ----
  async function loadPage(page) {
    const res = await fetch(`posts/page${page}.html`, { cache: "no-store" });
    const html = await res.text();
    newsContainer.innerHTML = html;

    // 关键：内容渲染 -> 下一帧再回到最顶（一次性、无平滑）
    requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "auto" });
    });
  }

  // ---- Render pager (顶部) ----
  function renderPagination() {
    paginationContainer.innerHTML = "";

    const prevBtn = document.createElement("button");
    prevBtn.type = "button";
    prevBtn.textContent = "← Prev";
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => goto(currentPage - 1);

    const info = document.createElement("span");
    info.className = "page-info";
    info.textContent = `Page ${currentPage} of ${totalPages}`;

    const nextBtn = document.createElement("button");
    nextBtn.type = "button";
    nextBtn.textContent = "Next →";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => goto(currentPage + 1);

    paginationContainer.append(prevBtn, info, nextBtn);
  }

  // ---- Navigate ----
  async function goto(page, { updateURL = true, replace = false } = {}) {
    currentPage = Math.min(Math.max(1, page), totalPages);
    await loadPage(currentPage);
    renderPagination();
    if (updateURL) writePageToURL(currentPage, { replace });

    // 派发一次事件，给底部控件同步
    document.dispatchEvent(new CustomEvent("pager:update", {
      detail: { current: currentPage, total: totalPages }
    }));
  }

  // 支持浏览器前进/后退
  window.addEventListener("popstate", () => {
    const p = getPageFromURL();
    goto(p, { updateURL: false });
  });

  // 全局接口（底部直接用它翻页）
  window.Pager = {
    get current() { return currentPage; },
    get total() { return totalPages; },
    goto,
    next: () => goto(currentPage + 1),
    prev: () => goto(currentPage - 1)
  };

  // ---- Init ----
  (async function init() {
    await detectTotalPages();
    currentPage = Math.min(getPageFromURL(), totalPages);
    await goto(currentPage, { replace: true });
  })();
});
