// components/pagination.js

document.addEventListener("DOMContentLoaded", () => {
  const paginationDiv = document.getElementById("pagination");
  if (!paginationDiv) return;

  // 当前页从 URL 中获取 pageX.html 中的 X
  const match = window.location.pathname.match(/page(\d+)\.html/);
  const currentPage = match ? parseInt(match[1]) : 1;

  // 加载总页数
  fetch("../page-count.json")
    .then(res => res.json())
    .then(data => {
      const totalPages = data.total_pages || 1;

      // 构建“上一页”按钮
      const prevBtn = document.createElement("button");
      prevBtn.textContent = "◀️ Prev";
      prevBtn.disabled = currentPage === 1;
      prevBtn.onclick = () => {
        if (currentPage > 1) {
          window.location.href = `page${currentPage - 1}.html`;
        }
      };
      paginationDiv.appendChild(prevBtn);

      // 构建每个页码按钮
      for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement("button");
        btn.textContent = `Page ${i}`;
        if (i === currentPage) {
          btn.classList.add("active");
          btn.disabled = true;
        }
        btn.onclick = () => {
          window.location.href = `page${i}.html`;
        };
        paginationDiv.appendChild(btn);
      }

      // 构建“下一页”按钮
      const nextBtn = document.createElement("button");
      nextBtn.textContent = "Next ▶️";
      nextBtn.disabled = currentPage === totalPages;
      nextBtn.onclick = () => {
        if (currentPage < totalPages) {
          window.location.href = `page${currentPage + 1}.html`;
        }
      };
      paginationDiv.appendChild(nextBtn);
    })
    .catch(err => {
      console.error("Failed to load page-count.json:", err);
    });
});
