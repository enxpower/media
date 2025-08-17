// components/pagination.js

// 底部分页触发时会把此开关置为 true；未设置过则默认 false（避免覆盖别处已设置）
if (window.__fromBottomPager === undefined) window.__fromBottomPager = false;

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
    if (page === 1) {
      url.searchParams.delete("page");
    } else {
      url.searchParams.set("page", String(page));
    }
    const method = replace ? "replaceState" : "pushState";
    history[method]({}, "", url);
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

    // 仅当不是“底部触发”时才回到顶部；随后无论如何都复位开关
    if (!window.__fromBottomPager) {
      window.scrollTo({ top: 0, behavior: "auto" }); // 保持与原来一致：立即到顶
    }
    window.__fromBottomPager = false; // 每次翻页后复位，避免影响下一次
  }

  // ---- Render pager ----
  function renderPagination() {
    paginationContainer.innerHTML = "";

    const prevBtn = document.createElement("button");
    prevBtn.textContent = "← Prev";
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => goto(currentPage - 1);

    const info = document.createElement("span");
    info.className = "page-info";
    info.textContent = `Page ${currentPage} of ${totalPages}`;

    const nextBtn = document.createElement("button");
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
  }

  // 支持浏览器前进/后退
  window.addEventListener("popstate", () => {
    const p = getPageFromURL();
    goto(p, { updateURL: false });
  });

  // 可选：暴露全局控制（方便以后直接驱动而不依赖点击）
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
    // 初始化时：如果本来没有 ?page，就不要新增；如果本来有，就规范化
    await goto(currentPage, { replace: true });
  })();
});
