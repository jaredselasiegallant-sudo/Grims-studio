/**
 * Grims Studio — Story engine (cat the fox).
 * Scroll-driven storytelling. Zero dependencies.
 *
 * What it does
 *   1. Computes global story progress (0..1) from scroll position.
 *   2. Drives the fox: asleep (quiet) -> awake -> pointing (scrubbed).
 *   3. Drives parallax scenes (data-parallax) and the pointer-glow grid.
 *   4. Drives staggered reveals (.reveal -> .is-visible).
 *   5. Smooth-scrolls to chapters (data-launch / marker clicks).
 *   6. Toggles the active progress marker.
 *   7. Respects prefers-reduced-motion with a static fallback.
 *
 * Edit these constants first (they live in style.css as --custom-props too):
 *   --fox-wake-at   : progress where the fox first wakes (default 0.30)
 *   --fox-point-at  : progress where the fox points (default 0.90)
 *   --reveal-offset : viewport fraction to trigger a .reveal (default 0.15)
 *   PROGRESS_END    : total scroll distance of the story (computed at runtime)
 */

(function () {
  "use strict";

  var reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  // Total scroll distance for the full story (5 chapters). 1.0 = end of story.
  var PROGRESS_END = Math.max(
    document.documentElement.scrollHeight - window.innerHeight,
    1
  );

  // Edit thresholds here (fractions of PROGRESS_END).
  var WAKE_AT = 0.30;
  var POINT_AT = 0.90;
  var REVEAL_OFFSET = 0.15;

  // --- references ---
  var fox = document.querySelector(".story-page .fox-stage svg");
  var foxStage = fox ? fox.closest(".fox-stage") : null;

  // Per-chapter progress is computed from the story's markers.
  var chapters = [];
  var rafId = null;

  // ---------- helpers ----------
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

  function raf(fn) {
    return (window.requestAnimationFrame ||
      function (cb) { return setTimeout(cb, 16); })(fn);
  }

  function caf(id) {
    (window.cancelAnimationFrame ||
      function (id) { clearTimeout(id); })(id);
  }

  function tick() {
    var sy = window.pageYOffset || document.documentElement.scrollTop || 0;
    var p = clamp(sy / Math.max(PROGRESS_END, 1), 0, 1);

    story.progress = p;

    // --- scrubbed parallax ---
    var scenes = document.querySelectorAll(".story-page .scene[data-parallax]");
    scenes.forEach(function (scene) {
      var speed = parseFloat(scene.getAttribute("data-parallax")) || 0;
      var top = scene.getBoundingClientRect().top + window.pageYOffset;
      var dx = (sy - top) * speed * 0.18;
      scene.style.transform = "translateX(" + dx.toFixed(1) + "px)";
    });

    // --- pointer glow (lights up the dot-matrix grid near cursor) ---
    var glow = document.querySelector(".story-page [data-glow]");
    if (glow) {
      glow.style.setProperty("--glow-x", ((event ? event.clientX : 0) / window.innerWidth) * 100 + "%");
      glow.style.setProperty("--glow-y", ((event ? event.clientY : 0) / window.innerHeight) * 100 + "%");
    }

    // --- FOX pose: asleep -> awake -> pointing (scrubbed) ---
    if (fox) {
      var walk = Math.min(p, WAKE_AT) * 36;
      var point = Math.max(p - POINT_AT, 0) * 60;
      fox.style.transform = "translateX(" + (walk + point).toFixed(1) + "px)";

      if (p < WAKE_AT) {
        fox.classList.add("fox--sleeping");
        fox.classList.remove("fox--awake", "fox--point");
      } else if (p < POINT_AT) {
        fox.classList.remove("fox--sleeping");
        fox.classList.add("fox--awake");
        fox.classList.remove("fox--point");
      } else {
        fox.classList.remove("fox--sleeping", "fox--awake");
        fox.classList.add("fox--point");
      }

      // keep the fox visible in reduced-motion fallback
      if (reduced) { fox.style.display = "block"; }
    }

    // --- progress markers ---
    if (chapters.length) {
      var active = 0;
      var best = chapters[0];
      chapters.forEach(function (c, i) {
        var center = c.top + c.height / 2;
        if (Math.abs(sy - center) < Math.abs(sy - (best.top + best.height / 2))) {
          best = c;
          active = i;
        }
      });
      document.querySelectorAll(".marker.active").forEach(function (m) { m.classList.remove("active"); });
      var hit = document.querySelector('.marker[data-marker="' + best.id + '"]');
      if (hit) hit.classList.add("active");
    }

    // --- staggered reveals ---
    var reveals = document.querySelectorAll(".story-page .reveal");
    reveals.forEach(function (el) {
      if (el.classList.contains("is-visible")) return;
      var rect = el.getBoundingClientRect();
      if (rect && rect.top < window.innerHeight * REVEAL_OFFSET) {
        el.classList.add("is-visible");
      }
    });

    // --- loop ---
    if (!reduced) {
      rafId = raf(tick);
    }
  }

  // ---------- init ----------
  function init() {
    if (!document.body) return;

    // Cache chapter markers (data-chapter) for navigation + markers.
    chapters = [];
    var marks = document.querySelectorAll(".story-page [data-chapter]");
    marks.forEach(function (m) {
      var top = m.getBoundingClientRect().top + window.pageYOffset;
      chapters.push({ id: m.id, top: top, height: m.getBoundingClientRect().height || 0 });
    });
    if (!chapters.length) {
      chapters.push({ id: "q1-quiet", top: 0, height: window.innerHeight });
    }

    // Pointer glow on the dot-matrix layer.
    var glow = document.querySelector(".story-page [data-glow]");
    if (glow) {
      window.addEventListener("pointermove", function (e) {
        glow.style.setProperty("--glow-x", (e.clientX / window.innerWidth) * 100 + "%");
        glow.style.setProperty("--glow-y", (e.clientY / window.innerHeight) * 100 + "%");
      });
      window.addEventListener("mouseleave", function () {
        glow.style.setProperty("--glow-x", "50%");
        glow.style.setProperty("--glow-y", "50%");
      });
    }

    // Section launches (smooth scroll to a chapter).
    document.querySelectorAll(".story-page [data-launch]").forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        var id = link.getAttribute("data-launch");
        var target = document.getElementById(id);
        if (!target) { window.location.hash = id; return; }
        var top = target.getBoundingClientRect().top + window.pageYOffset - 10;
        window.scrollTo({ top: top, behavior: reduced ? "auto" : "smooth" });
      });
    });

    // Start the loop.
    if (!reduced) {
      rafId = raf(tick);
    } else {
      tick(); // static fallback: fox visible, no parallax, reveals visible.
    }
  }

  // ---------- expose ----------
  var story = {
    progress: 0,
    init: init,
    destroy: function () { if (rafId != null) { caf(rafId); rafId = null; } },
  };

  if (document.readyState !== "loading") {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
