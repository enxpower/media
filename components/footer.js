const footer = document.createElement("footer");
footer.innerHTML = `
  <div style="text-align:center;color:#888;font-size:0.8rem;margin-top:2rem;padding:2rem 1rem;border-top:1px solid #ddd;">
    <p>This site aggregates news articles related to the energy and power industry.</p>
    <p>All content belongs to their original authors. We do not modify or store any original content.</p>
    <p>© 2025 Energize Solutions Inc. – All rights reserved.</p>
    <p>Powered by GitHub Pages | Contact: <a href="mailto:info@energizeos.com">info@energizeos.com</a></p>
    <div class="social-icons" style="margin-top: 0.5rem;">
      <a href="https://www.linkedin.com/in/gongtiejing" target="_blank" aria-label="LinkedIn" style="margin: 0 0.5rem;">
        <i class="fab fa-linkedin fa-lg"></i>
      </a>
      <a href="https://github.com/enxpower" target="_blank" aria-label="GitHub" style="margin: 0 0.5rem;">
        <i class="fab fa-github fa-lg"></i>
      </a>
    </div>
  </div>
`;
document.body.appendChild(footer);
