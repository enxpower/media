document.getElementById("langToggle").addEventListener("click", function () {
  const isEnglish = this.textContent === "中文";
  this.textContent = isEnglish ? "English" : "中文";
  document.querySelectorAll(".summary").forEach(el => {
    el.textContent = isEnglish ? el.dataset.summaryZh : el.dataset.summaryEn;
  });
});
