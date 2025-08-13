// components/langToggle.js
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("langToggle");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const items = document.querySelectorAll(".summary");
    const toZh = btn.innerText.trim() === "中文";

    items.forEach((el) => {
      const zh = el.getAttribute("data-summary-zh");
      const en = el.getAttribute("data-summary-en");
      el.textContent = toZh && zh ? zh : en;
    });

    btn.innerText = toZh ? "English" : "中文";
  });
});
