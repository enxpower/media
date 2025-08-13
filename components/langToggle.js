document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("langToggle");
  let isChinese = false;

  toggleBtn.addEventListener("click", () => {
    const summaries = document.querySelectorAll(".summary");
    summaries.forEach(p => {
      if (isChinese) {
        p.textContent = p.dataset.summaryEn || p.textContent;
      } else {
        p.textContent = p.dataset.summaryZh || p.textContent;
      }
    });
    isChinese = !isChinese;
    toggleBtn.textContent = isChinese ? "English" : "中文";
  });
});
