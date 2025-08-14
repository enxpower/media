document.addEventListener("DOMContentLoaded", () => {
  const paginationContainer = document.getElementById("pagination");
  const newsContainer = document.getElementById("newsContainer");
  const totalPages = 10; // 更新为实际页数
  let currentPage = 1;

  function loadPage(page) {
    fetch(`posts/page${page}.html`)
      .then(res => res.text())
      .then(html => {
        newsContainer.innerHTML = html;
        window.scrollTo(0, 0);
      });
  }

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
    pageLabel.textContent = ` Page ${currentPage} `;
    pageLabel.style.fontWeight = "bold";
    pageLabel.style.margin = "0 1rem";

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

  loadPage(currentPage);
  renderPagination();
});
