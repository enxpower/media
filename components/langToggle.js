document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("langToggle");
  const iframe = document.getElementById("newsFrame");
  let isChinese = false;

  toggleBtn.addEventListener("click", () => {
    if (!iframe || !iframe.contentWindow) return;

    const lang = isChinese ? "switch-lang-en" : "switch-lang-zh";
    iframe.contentWindow.postMessage(lang, "*");

    isChinese = !isChinese;
    toggleBtn.textContent = isChinese ? "English" : "中文";
  });
});
