document.getElementById("searchBox").addEventListener("input", function () {
  const keyword = this.value.toLowerCase();
  document.querySelectorAll(".news-post").forEach(post => {
    const title = post.dataset.title.toLowerCase();
    const summary = post.dataset.summary.toLowerCase();
    post.style.display = (title.includes(keyword) || summary.includes(keyword)) ? "block" : "none";
  });
});
