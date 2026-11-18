/**
 * Grims Studio — page transitions.
 *
 * Enter: the document starts hidden via the `js-fade` class that build.py adds
 * with an inline <head> script (so a no-JS visitor still sees the page). This
 * file flips it to `page-ready`, letting CSS fade the body in.
 *
 * Exit: internal page links fade the body out for ~220 ms before navigating,
 * so moving between the story and an inner page reads as one world shifting.
 *
 * prefers-reduced-motion: no enter fade, no exit fade, no interception.
 * The inline head script also carries a 1.6 s failsafe in case this file
 * never runs.
 */
(function () {
  "use strict";

  var doc = document.documentElement;
  var reduced = !!(window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function ready() {
    doc.classList.add("page-ready");
  }

  // ---- enter ---------------------------------------------------------------
  if (doc.classList.contains("js-fade")) {
    if (reduced) {
      ready(); // show immediately; no transition
    } else {
      // Two frames: guarantees the opacity:0 state is painted first.
      requestAnimationFrame(function () {
        requestAnimationFrame(ready);
      });
    }
  }

  // Returning via bfcache: drop any stale exit state.
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    doc.classList.remove("page-leaving");
    ready();
  });

  // ---- exit ----------------------------------------------------------------
  if (reduced) return;

  function isInternalPageLink(a) {
    if (!a || !a.href) return false;
    if (a.target === "_blank") return false;
    if (a.hasAttribute("download") || a.hasAttribute("data-no-fade")) return false;
    var url;
    try { url = new URL(a.href, window.location.href); } catch (err) { return false; }
    if (url.origin !== window.location.origin) return false;
    if (url.hash && url.pathname === window.location.pathname) return false; // in-page anchor
    return /\.html?$/.test(url.pathname) || url.pathname.slice(-1) === "/";
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented) return;
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest("a[href]") : null;
    if (!a || !isInternalPageLink(a)) return;

    var url = new URL(a.href, window.location.href);
    if (url.pathname === window.location.pathname && url.hash) return;

    e.preventDefault();
    doc.classList.add("page-leaving");
    setTimeout(function () {
      window.location.assign(url.href);
    }, 220);
  });
})();
