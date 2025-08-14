document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("langToggle");
  let isChinese = false;

  toggleBtn.addEventListener("click", () => {
    const summaries = document.querySelectorAll(".summary");

    summaries.forEach(el => {
      el.textContent = isChinese ? (el.dataset.summaryEn || "") : (el.dataset.summaryZh || el.dataset.summaryEn || "");
    });

    isChinese = !isChinese;
    toggleBtn.textContent = isChinese ? "English" : "中文";
  });
});
