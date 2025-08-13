// components/langToggle.js
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("langToggle");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const items = document.querySelectorAll(".summary");
    const toZh = btn.innerText.trim() === "中文";

    items.forEach((el) => {
      el.textContent = toZh ? el.dataset.summaryZh : el.dataset.summaryEn;
    });

    btn.innerText = toZh ? "English" : "中文";
  });
});
