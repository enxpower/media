// components/pagination.js
document.addEventListener("DOMContentLoaded", () => {
  const paginationContainer =
    document.getElementById("pagination");
  const newsContainer =
    document.getElementById("newsContainer") || document.getElementById("news");

  let currentPage = 1;
  let totalPages = 1;
  let lastLoadToken = 0;

  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

  async function headExists(path) {
    try {
      const res = await fetch(path, { method: "HEAD", cache: "no-store" });
      return res.ok;
    } catch {
      return false;
    }
  }

  // 自动检测 posts 目录下有多少页（最多探测 200 页，避免死循环）
  async function detectTotalPages(maxProbe = 200) {
    let i = 1;
    for (; i <= maxProbe; i++) {
      const ok = await headExists(`posts/page${i}.html`);
      if (!ok) break;
    }
    totalPages = Math.max(1, i - 1);
  }

  function setUrlParam(page) {
    try {
      const u = new URL(location.href);
      u.searchParams.set("p", String(page));
      history.replaceState(null, "", u.toString());
    } catch {}
  }

  function updatePaginationUI() {
    if (!paginationContainer) return;

    paginationContainer.innerHTML = "";

    const prevBtn = document.createElement("button");
    prevBtn.textContent = "← Prev";
    prevBtn.disabled = currentPage <= 1;
    prevBtn.addEventListener("click", () => goToPage(currentPage - 1));

    const pageLabel = document.createElement("span");
    pageLabel.className = "page-info";
    pageLabel.textContent = `Page ${currentPage} of ${totalPages}`;

    const nextBtn = document.createElement("button");
    nextBtn.textContent = "Next →";
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.addEventListener("click", () => goToPage(currentPage + 1));

    paginationContainer.append(prevBtn, pageLabel, nextBtn);
  }

  // 重新执行注入 HTML 中的 <script>（保证页内脚本生效）
  function reExecuteScripts(root) {
    if (!root) return;
    const scripts = root.querySelectorAll("script");
    scripts.forEach((old) => {
      const s = document.createElement("script");
      for (const a of old.attributes) s.setAttribute(a.name, a.value);
      s.textContent = old.textContent || "";
      old.replaceWith(s);
    });
  }

  async function loadPage(page) {
    const token = ++lastLoadToken;
    const url = `posts/page${page}.html`;
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const html = await res.text();

      // 忽略过期的并发请求结果
      if (token !== lastLoadToken) return;

      if (newsContainer) {
        newsContainer.innerHTML = html;
        reExecuteScripts(newsContainer);
      }
      try {
        window.scrollTo({ top: 0, behavior: "instant" });
      } catch {
        window.scrollTo(0, 0);
      }
    } catch (err) {
      console.error("[pagination] load failed:", url, err);
      if (newsContainer) {
        newsContainer.innerHTML =
          `<div style="padding:12px;border:1px solid #f99;border-radius:8px;background:#fff6f6">
             Failed to load ${url}. ${err.message}
           </div>`;
      }
    }
  }

  async function goToPage(page) {
    page = clamp(page, 1, totalPages);
    if (page === currentPage) return;
    currentPage = page;
    setUrlParam(currentPage);
    updatePaginationUI();
    await loadPage(currentPage);
  }

  // 初始化：默认跳转到“最新页”（最大 N）；若有 ?p= 则按参数直达
  async function init() {
    await detectTotalPages(200);

    const p = parseInt(new URLSearchParams(location.search).get("p"), 10);
    currentPage = Number.isFinite(p) && p >= 1 ? clamp(p, 1, totalPages) : totalPages;

    updatePaginationUI();
    await loadPage(currentPage);

    // 键盘 ← / → 翻页（输入框内不触发）
    document.addEventListener("keydown", (e) => {
      const t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      if (e.key === "ArrowLeft") goToPage(currentPage - 1);
      if (e.key === "ArrowRight") goToPage(currentPage + 1);
    });
  }

  init();
});
