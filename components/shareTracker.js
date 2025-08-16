// components/shareTracker.js
document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("click", (e) => {
    const link = e.target.closest(".share-link");
    if (!link) return;

    const platform = link.dataset.platform || "unknown";
    const title = link.closest(".news-post")?.dataset.title || "unknown";

    if (window.gtag) {
      gtag("event", "share_click", {
        event_category: "Social Share",
        event_label: `${platform}: ${title}`,
        transport_type: "beacon"
      });
    }
  });
});
