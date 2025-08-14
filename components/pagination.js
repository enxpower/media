document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("pagination");
  const frame = document.getElementById("newsFrame");

  if (!container || !frame) return;

  const totalPages = 10; // update as needed

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.textContent = `Page ${i}`;
    btn.dataset.page = i;
    btn.onclick = () => {
      frame.src = `posts/page${i}.html`;
      document.querySelectorAll("#pagination button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    };
    if (i === 1) btn.classList.add("active");
    container.appendChild(btn);
  }
});
