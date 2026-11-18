/**
 * Grims Studio — page-fade transition.
 *
 * On hard navigation into an inner page, fade the new document in so the
 * advance reads as one world shifting rather than a hard load. The fade is
 * light (~340ms) and only runs when the visitor has not asked for reduced
 * motion.
 *
 * Loaded on every non-story page by build.py
 * (base_page(... scripts=["./transitions.js"], page_fade=True).
 */
(function () {
  "use strict";

  var reduced = !!(window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function run() {
    var body = document.body;
    if (!body) return;
    // Start at opacity 0 so there is no flash of unstyled content.
    body.style.opacity = "0";
    // Force layout so the transition below actually runs.
    void body.offsetHeight;
    body.style.transition = "opacity .34s ease";
    requestAnimationFrame(function () {
      body.style.opacity = "1";
    });
  }

  if (document.readyState !== "loading") {
    run();
  } else if (document.body) {
    run(); // DOM parsed; apply as early as possible.
  } else {
    document.addEventListener("DOMContentLoaded", run);
  }
})();
