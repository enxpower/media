document.addEventListener("DOMContentLoaded", () => {
  const paginationContainer = document.getElementById("pagination");
  const newsContainer = document.getElementById("newsContainer");
  let currentPage = 1;
  let totalPages = 1;

  // 自动检测 posts 目录下有多少页
  async function detectTotalPages() {
    let i = 1;
    while (true) {
      const res = await fetch(`posts/page${i}.html`, { method: "HEAD" });
      if (!res.ok) break;
      i++;
    }
    totalPages = i - 1;
  }

  // 加载当前页 HTML 内容
  function loadPage(page) {
    fetch(`posts/page${page}.html`)
      .then(res => res.text())
      .then(html => {
        newsContainer.innerHTML = html;
        window.scrollTo(0, 0);
      });
  }

  // 渲染分页按钮
  function renderPagination() {
    paginationContainer.innerHTML = "";

    const prevBtn = document.createElement("button");
    prevBtn.textContent = "← Prev";
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => {
      if (currentPage > 1) {
        currentPage--;
        loadPage(currentPage);
        renderPagination();
      }
    };

    const pageLabel = document.createElement("span");
    pageLabel.className = "page-info";
    pageLabel.textContent = `Page ${currentPage} of ${totalPages}`;


    const nextBtn = document.createElement("button");
    nextBtn.textContent = "Next →";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => {
      if (currentPage < totalPages) {
        currentPage++;
        loadPage(currentPage);
        renderPagination();
      }
    };

    paginationContainer.appendChild(prevBtn);
    paginationContainer.appendChild(pageLabel);
    paginationContainer.appendChild(nextBtn);
  }

  // 初始化加载
  async function init() {
    await detectTotalPages();
    loadPage(currentPage);
    renderPagination();
  }

  init();
});
