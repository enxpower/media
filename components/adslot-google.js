/*!
 * Google ad card injector for DEV-UI
 * Controlled by /static/data/ads.json
 * - Inserts <div class="news-post sponsor"> cards that visually match news cards
 * - Toggle via ads.json (enabled/google/client/slot/insert_after/adtest)
 */
(function () {
  if (window.__adslot_google_init__) return;
  window.__adslot_google_init__ = true;

  const JSON_URL = "/static/data/ads.json";
  const CONTAINER_ID = "newsContainer";
  const CARD_SELECTOR = ".news-post";
  const SPONSOR_CLASS = "sponsor";
  const MIN_CONTENT_HEIGHT = 120;
  const EXTRA_PADDING_EST = 24;

  async function loadConfig() {
    try {
      const resp = await fetch(JSON_URL, { cache: "no-store" });
      if (!resp.ok) return null;
      return await resp.json();
    } catch {
      return null;
    }
  }

  function medianHeight(nodes) {
    const hs = nodes
      .map((n) => n.getBoundingClientRect().height)
      .filter((h) => h && h > 0)
      .sort((a, b) => a - b);
    if (!hs.length) return 220; // fallback
    const mid = Math.floor(hs.length / 2);
    return hs.length % 2 ? hs[mid] : Math.round((hs[mid - 1] + hs[mid]) / 2);
  }

  // Prefer 336x280 > 300x250; keep container stable
  function chooseAdBoxSize(container) {
    const w = container.getBoundingClientRect().width || 0;
    if (w >= 336) return { w: 336, h: 280 };
    if (w >= 300) return { w: 300, h: 250 };
    return { w: Math.max(250, Math.floor(w)), h: 200 };
  }

  function buildAdCard(baseContentHeight, slotConf, container) {
    const card = document.createElement("div");
    card.className = `news-post ${SPONSOR_CLASS}`;
    card.dataset.category = "General";

    const h3 = document.createElement("h3");
    const a = document.createElement("a");
    a.className = "news-link";
    a.href = "javascript:void(0)";
    a.setAttribute("aria-label", "Sponsored");
    a.textContent = "Sponsored";
    h3.appendChild(a);

    const meta = document.createElement("div");
    meta.className = "meta";
    const badge = document.createElement("span");
    badge.className = "source-badge";
    badge.textContent = "Sponsored";
    meta.appendChild(badge);

    const summary = document.createElement("div");
    summary.className = "summary";

    // Estimate header/meta take-up even before mount
    const headH =
      Math.round(
        (h3.getBoundingClientRect().height || 0) +
          (meta.getBoundingClientRect().height || 0)
      ) + EXTRA_PADDING_EST;

    const targetContentH = Math.max(MIN_CONTENT_HEIGHT, baseContentHeight - headH);
    const box = chooseAdBoxSize(container);
    const finalContentH = Math.max(targetContentH, box.h);
    summary.style.minHeight = finalContentH + "px";

    const ins = document.createElement("ins");
    ins.className = "adsbygoogle";
    ins.style.cssText = `display:block;width:100%;height:${box.h}px`;
    ins.setAttribute("data-ad-client", slotConf.client);
    ins.setAttribute("data-ad-slot", String(slotConf.slot));
    ins.setAttribute("data-full-width-responsive", "false");
    if (slotConf.adtest === true) ins.setAttribute("data-adtest", "on");

    summary.appendChild(ins);
    card.appendChild(h3);
    card.appendChild(meta);
    card.appendChild(summary);

    return { card };
  }

  function insertAfterIndex(container, node, index) {
    const cards = container.querySelectorAll(CARD_SELECTOR);
    if (!cards.length) { container.appendChild(node); return; }
    const i = Math.max(0, Math.min(index, cards.length - 1));
    const ref = cards[i];
    ref && ref.after(node);
  }

  function ensureAdSense(client, cb) {
    if (window.adsbygoogle && window.adsbygoogle.push) return cb();
    const srcUrl =
      "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" +
      encodeURIComponent(client);
    const existed = Array.from(document.scripts).some((s) =>
      (s.src || "").includes("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js")
    );
    if (existed) {
      if (document.readyState === "complete") return cb();
      window.addEventListener("load", cb, { once: true });
      return;
    }
    const s = document.createElement("script");
    s.async = true;
    s.src = srcUrl;
    s.crossOrigin = "anonymous";
    s.onload = cb;
    document.head.appendChild(s);
  }

  async function main() {
    const cfg = await loadConfig();
    if (!cfg || !cfg.native_ads || cfg.native_ads.enabled !== true) return;

    // Read from native_ads.cards (你的现有结构)，兼容 positions.cards
    const itemsRaw =
      (Array.isArray(cfg?.native_ads?.cards) && cfg.native_ads.cards) ||
      (cfg?.native_ads?.positions?.cards || []);
    const items = itemsRaw.filter(
      (x) => x && x.enabled === true && x.google === true && x.client && x.slot
    );
    if (!items.length) return;

    const container = document.getElementById(CONTAINER_ID) || document.body;
    const normalCards = Array.from(
      container.querySelectorAll(`${CARD_SELECTOR}:not(.${SPONSOR_CLASS})`)
    );
    const baseH = medianHeight(normalCards);

    const client = items[0].client; // load once
    ensureAdSense(client, function () {
      items.forEach((item) => {
        const after = Number.isFinite(item.insert_after)
          ? item.insert_after
          : item.insert_after
          ? parseInt(item.insert_after, 10)
          : 4; // default
        const { card } = buildAdCard(baseH, item, container);
        insertAfterIndex(container, card, after);
        try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) {}
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
  window.addEventListener("load", () => setTimeout(main, 50), { once: true });
})();
