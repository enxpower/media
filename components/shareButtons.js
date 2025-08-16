// components/shareButtons.js
document.addEventListener("DOMContentLoaded", () => {
  const posts = document.querySelectorAll(".news-post");

  posts.forEach(post => {
    const linkEl = post.querySelector(".news-link");
    if (!linkEl) return;

    const link = linkEl.href;
    const title = linkEl.textContent;
    const encodedTitle = encodeURIComponent(title);
    const encodedLink = encodeURIComponent(link + "?utm_source=social&utm_medium=share&utm_campaign=share_button");

    const buttonsHTML = `
      <div class="share-buttons">
        <a href="https://twitter.com/intent/tweet?url=${encodedLink}&text=${encodedTitle}" target="_blank" title="Share on Twitter" class="share-link" data-platform="Twitter">
          <i class="fab fa-twitter"></i>
        </a>
        <a href="https://www.linkedin.com/shareArticle?mini=true&url=${encodedLink}&title=${encodedTitle}" target="_blank" title="Share on LinkedIn" class="share-link" data-platform="LinkedIn">
          <i class="fab fa-linkedin"></i>
        </a>
        <a href="https://wa.me/?text=${encodedTitle}%20${encodedLink}" target="_blank" title="Share on WhatsApp" class="share-link" data-platform="WhatsApp">
          <i class="fab fa-whatsapp"></i>
        </a>
        <a href="https://www.reddit.com/submit?url=${encodedLink}&title=${encodedTitle}" target="_blank" title="Share on Reddit" class="share-link" data-platform="Reddit">
          <i class="fab fa-reddit"></i>
        </a>
      </div>
    `;

    post.insertAdjacentHTML("beforeend", buttonsHTML);
  });
});
