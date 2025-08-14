document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchBox");
  const newsFrame = document.getElementById("newsFrame");
  const filterButtons = document.querySelectorAll(".filter-button");

  // Handle search
  searchInput.addEventListener("input", () => {
    const keyword = searchInput.value.toLowerCase();
    newsFrame.contentWindow.postMessage({ type: "search", keyword }, "*");
  });

  // Handle category filter
  filterButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      filterButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const category = btn.dataset.filter;
      newsFrame.contentWindow.postMessage({ type: "filter", category }, "*");
    });
  });

  // Toggle AI summary/preview on click
  window.addEventListener("message", (event) => {
    if (event.data === "attachToggle") {
      const frameDoc = newsFrame.contentDocument || newsFrame.contentWindow.document;
      const posts = frameDoc.querySelectorAll(".news-post");
      posts.forEach(post => {
        const summary = post.querySelector(".summary");
        const preview = post.querySelector(".preview");

        if (summary && preview) {
          summary.style.cursor = "pointer";
          preview.style.cursor = "pointer";

          summary.addEventListener("click", () => {
            preview.style.display = preview.style.display === "none" ? "block" : "none";
          });
          preview.addEventListener("click", () => {
            summary.style.display = summary.style.display === "none" ? "block" : "none";
          });
        }
      });
    }
  });

  // Reload toggle after iframe loads
  newsFrame.addEventListener("load", () => {
    newsFrame.contentWindow.postMessage("attachToggle", "*");
  });
});
