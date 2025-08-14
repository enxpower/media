const footer = document.createElement("footer");
footer.innerHTML = `
  <div class="disclaimer">
    <p>This site aggregates news articles related to the energy and power industry.<br>
    All content belongs to their original authors. We do not modify or store any original content.</p>
  </div>
  <div class="copyright">
    <p>© 2025 Energize Solutions Inc. – All rights reserved.</p>
    <p>Powered by GitHub Pages | Contact: <a href="mailto:info@energizeos.com">info@energizeos.com</a></p>
  </div>
  <div class="social-icons">
    <a href="https://www.linkedin.com/in/gongtiejing" target="_blank" aria-label="LinkedIn">
      <i class="fab fa-linkedin fa-lg"></i>
    </a>
    <a href="https://github.com/enxpower" target="_blank" aria-label="GitHub">
      <i class="fab fa-github fa-lg"></i>
    </a>
  </div>
`;
document.body.appendChild(footer);
