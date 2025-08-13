// components/langToggle.js
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("langToggle");
  if (!btn) return;

  let isZh = false;

  btn.addEventListener("click", () => {
    isZh = !isZh;
    const message = isZh ? "switch-lang-zh" : "switch-lang-en";
    const iframe = document.getElementById("newsFrame");
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage(message, "*");
    }

    btn.innerText = isZh ? "English" : "中文";
  });
});
