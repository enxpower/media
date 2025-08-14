document.addEventListener("DOMContentLoaded", () => {
  const langBtn = document.getElementById("langToggle");
  let currentLang = "en";

  langBtn.onclick = () => {
    currentLang = currentLang === "en" ? "zh" : "en";
    window.postMessage(`switch-lang-${currentLang}`);
    langBtn.textContent = currentLang === "en" ? "中文" : "English";
  };
});
