// components/outboundTracker.js
document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("click", function (e) {
    const target = e.target.closest("a[href^='http']");
    if (!target) return;

    const href = target.href;
    const hostname = location.hostname;

    if (!href.includes(hostname)) {
      // 外链点击，发送 GA 事件
      if (typeof gtag === "function") {
        gtag("event", "click", {
          event_category: "outbound",
          event_label: href,
          transport_type: "beacon",
        });
      }
    }
  });
});
