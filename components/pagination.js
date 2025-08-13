// components/pagination.js
document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("pagination");
  const frame = document.getElementById("newsFrame");

  if (!container || !frame) return;

  const totalPages = 10; // 🛠️ 修改为你实际分页总数

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.textContent = `Page ${i}`;
    btn.style.margin = "4px";
    btn.onclick = () => {
      frame.src = `posts/page${i}.html`;
    };
    container.appendChild(btn);
  }
});
