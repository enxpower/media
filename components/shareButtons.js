document.addEventListener("DOMContentLoaded", () => {
  const posts = document.querySelectorAll(".news-post");

  posts.forEach(post => {
    const link = post.querySelector(".news-link")?.href;
    const title = post.querySelector(".news-link")?.textContent;

    if (!link || !title) return;

    const encodedTitle = encodeURIComponent(title);
    const encodedLink = encodeURIComponent(link + "?utm_source=share&utm_medium=social&utm_campaign=share_button");

    const buttonsHTML = `
      <div class="share-buttons">
        <a href="https://twitter.com/intent/tweet?url=${encodedLink}&text=${encodedTitle}" target="_blank" title="Share on Twitter">
          <i class="fab fa-twitter"></i>
        </a>
        <a href="https://www.linkedin.com/shareArticle?mini=true&url=${encodedLink}&title=${encodedTitle}" target="_blank" title="Share on LinkedIn">
          <i class="fab fa-linkedin"></i>
        </a>
        <a href="https://wa.me/?text=${encodedTitle}%20${encodedLink}" target="_blank" title="Share on WhatsApp">
          <i class="fab fa-whatsapp"></i>
        </a>
        <a href="https://www.reddit.com/submit?url=${encodedLink}&title=${encodedTitle}" target="_blank" title="Share on Reddit">
          <i class="fab fa-reddit"></i>
        </a>
      </div>
    `;

    post.insertAdjacentHTML("beforeend", buttonsHTML);
  });
});
