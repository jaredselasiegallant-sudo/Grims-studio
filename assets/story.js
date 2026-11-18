/**
 * Grims Studio — Story engine (Kit the fox).
 * Scroll-driven storytelling. Zero dependencies.
 *
 * What it does
 *   1. Scrubs the hero fox with scroll position: asleep -> waking -> stretch
 *      -> awake idle. Scrolling back puts him back to sleep (fully reversible).
 *   2. Wakes the foxes of later chapters when their chapter enters the viewport,
 *      and lets the last one point toward the closing CTA.
 *   3. Drives parallax scenes (data-parallax) and the pointer glow (data-glow).
 *   4. Reveals [.reveal] elements once they enter the viewport (staggered via
 *      the --i CSS variable set in build.py).
 *   5. Makes the progress markers real navigation (smooth scroll).
 *   6. Re-measures chapter offsets on resize so parallax/markers never drift.
 *   7. Respects prefers-reduced-motion: one static, fully visible frame.
 *
 * Edit these first:
 *   HERO_KEYS  : the scrubbed pose keyframes (at = 0..1 of the hero scroll)
 *   WAKE_AT    : hero progress where the eyes open
 *   SETTLE_AT  : hero progress where the stretch finishes (idle takes over)
 *   REVEAL_*   : when [.reveal] elements trigger
 */
(function () {
  "use strict";

  var root = document.querySelector(".story-page");
  if (!root) return;

  var reduced = !!(window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  var chaptersEls = Array.prototype.slice.call(root.querySelectorAll("[data-chapter]"));
  var heroChapter = root.querySelector(".chapter--hero");
  var heroStage = heroChapter ? heroChapter.querySelector(".fox-stage") : null;
  var heroFox = heroStage ? heroStage.querySelector(".fox") : null;
  var lastChapter = chaptersEls[chaptersEls.length - 1];

  // ---- scrub tuning --------------------------------------------------------
  var WAKE_AT = 0.22;    // eyes open
  var SETTLE_AT = 0.74;  // stretch done, idle breathing begins

  // One pose per keyframe. `at` is hero scroll progress (0 = top of page).
  // headR/headY: head rotation + lift. bodyY/bodyS: body lift + stretch.
  // ear: ear rotation. tail: tail rotation. pawY: paws reach down.
  var HERO_KEYS = [
    { at: 0.00, headR: -6, headY: 8, ear: -16, bodyY: 3, bodyS: 0.985, tail: 6, pawY: 0 },
    { at: 0.30, headR: 0, headY: 1, ear: 0, bodyY: 1, bodyS: 0.995, tail: 0, pawY: 0 },
    { at: 0.52, headR: -3, headY: -9, ear: 9, bodyY: -7, bodyS: 1.05, tail: -10, pawY: 14 },
    { at: 0.74, headR: 3, headY: -1, ear: 4, bodyY: 0, bodyS: 1.02, tail: 5, pawY: 0 },
    { at: 1.00, headR: 0, headY: 0, ear: 0, bodyY: 0, bodyS: 1, tail: 0, pawY: 0 }
  ];

  var REVEAL_THRESHOLD = 0.15;
  var REVEAL_MARGIN = "0px 0px -8% 0px";

  // ---- state ---------------------------------------------------------------
  var chapterTops = [];
  var heroTop = 0;
  var progressEnd = 1;
  var rafId = null;
  var heroParts = null;

  // ---------- helpers -------------------------------------------------------
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function raf(fn) {
    return (window.requestAnimationFrame ||
      function (cb) { return setTimeout(function () { cb(Date.now()); }, 16); })(fn);
  }

  function smoothstep(t) { return t * t * (3 - 2 * t); }

  function sampleHero(p) {
    var i = 0;
    while (i < HERO_KEYS.length - 2 && p > HERO_KEYS[i + 1].at) i++;
    var a = HERO_KEYS[i];
    var b = HERO_KEYS[i + 1];
    var t = smoothstep(clamp((p - a.at) / Math.max(b.at - a.at, 0.0001), 0, 1));
    return {
      headR: lerp(a.headR, b.headR, t),
      headY: lerp(a.headY, b.headY, t),
      ear: lerp(a.ear, b.ear, t),
      bodyY: lerp(a.bodyY, b.bodyY, t),
      bodyS: lerp(a.bodyS, b.bodyS, t),
      tail: lerp(a.tail, b.tail, t),
      pawY: lerp(a.pawY, b.pawY, t)
    };
  }

  function heroRig() {
    if (heroParts || !heroFox) return heroParts;
    heroParts = {
      head: heroFox.querySelector(".fx-head"),
      ears: Array.prototype.slice.call(heroFox.querySelectorAll(".fx-ear")),
      body: heroFox.querySelector(".fx-body"),
      tail: heroFox.querySelector(".fx-tail"),
      paws: heroFox.querySelector(".fx-paws")
    };
    return heroParts;
  }

  function measure() {
    progressEnd = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
    chapterTops = chaptersEls.map(function (el) {
      var r = el.getBoundingClientRect();
      return { el: el, top: r.top + window.pageYOffset, height: r.height || 1 };
    });
    heroTop = chapterTops.length ? chapterTops[0].top : 0;
  }

  // ---------- hero fox: scrubbed wake + stretch -----------------------------
  function heroProgress(scrollY) {
    if (!heroChapter) return 1;
    // The wake + stretch plays across the hero's scrollable range (the chapter
    // is taller than the viewport and pins its content). Scrolling back
    // reverses the whole performance.
    var range = Math.max(
      heroChapter.offsetHeight - window.innerHeight,
      window.innerHeight * 0.6
    );
    return clamp((scrollY - heroTop) / range, 0, 1);
  }

  function applyHero(p, time) {
    var rig = heroRig();
    if (!rig) return;
    var k = sampleHero(p);
    var awake = clamp((p - SETTLE_AT) / (1 - SETTLE_AT), 0, 1);

    // Idle life once the stretch has settled.
    var breath = Math.sin(time * 0.0015) * 1.4 * awake;
    var sway = Math.sin(time * 0.0011) * 6 * awake;

    if (rig.head) {
      rig.head.style.transform =
        "translateY(" + (k.headY + breath * 0.4).toFixed(2) + "px) rotate(" +
        k.headR.toFixed(2) + "deg)";
    }
    rig.ears.forEach(function (ear) {
      ear.style.transform = "rotate(" + k.ear.toFixed(2) + "deg)";
    });
    if (rig.body) {
      rig.body.style.transform =
        "translateY(" + (k.bodyY - breath * 0.6).toFixed(2) + "px) scaleY(" +
        (k.bodyS + awake * 0.008).toFixed(4) + ")";
    }
    if (rig.tail) {
      rig.tail.style.transform = "rotate(" + (k.tail + sway).toFixed(2) + "deg)";
    }
    if (rig.paws) {
      rig.paws.style.transform = "translateY(" + k.pawY.toFixed(2) + "px)";
    }
    if (heroStage) {
      heroStage.classList.toggle("is-sleeping", p < WAKE_AT);
      heroStage.classList.toggle("is-awake", p >= SETTLE_AT - 0.06);
    }
  }

  // ---------- chapter foxes -------------------------------------------------
  function initChapterFoxes() {
    var others = chaptersEls.filter(function (el) { return el !== heroChapter; });

    function wake(ch) {
      var fox = ch.querySelector(".fox");
      if (!fox) return;
      fox.classList.add("fox--awake");
      if (ch === lastChapter) fox.classList.add("fox--point");
    }

    if (reduced || !("IntersectionObserver" in window)) {
      others.forEach(wake);
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        wake(e.target);
        io.unobserve(e.target);
      });
    }, { threshold: 0.35 });
    others.forEach(function (ch) { io.observe(ch); });
  }

  // ---------- markers -------------------------------------------------------
  function updateMarkers(scrollY) {
    if (!chapterTops.length) return;
    var activeIndex = 0;
    var bestDist = Infinity;
    chapterTops.forEach(function (c, i) {
      var center = c.top + c.height / 2;
      var d = Math.abs(scrollY + window.innerHeight / 2 - center);
      if (d < bestDist) { bestDist = d; activeIndex = i; }
    });
    var markers = root.querySelectorAll(".marker");
    markers.forEach(function (m, i) {
      var on = i === activeIndex;
      m.classList.toggle("active", on);
      if (on) { m.setAttribute("aria-current", "true"); }
      else { m.removeAttribute("aria-current"); }
    });
  }

  function initMarkers() {
    root.querySelectorAll(".marker").forEach(function (m) {
      var id = m.getAttribute("data-marker");
      var target = id && document.getElementById(id);
      if (!target) return;
      m.addEventListener("click", function () {
        var top = target.getBoundingClientRect().top + window.pageYOffset;
        window.scrollTo({ top: top, behavior: reduced ? "auto" : "smooth" });
      });
    });
  }

  // ---------- reveals -------------------------------------------------------
  function initReveals() {
    var els = Array.prototype.slice.call(root.querySelectorAll(".reveal"));
    if (!els.length) return;
    if (reduced || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("in");
        io.unobserve(e.target);
      });
    }, { threshold: REVEAL_THRESHOLD, rootMargin: REVEAL_MARGIN });
    els.forEach(function (el) { io.observe(el); });
  }

  // ---------- pointer glow --------------------------------------------------
  function initGlow() {
    var scenes = root.querySelectorAll("[data-glow]");
    if (!scenes.length) return;

    function set(x, y) {
      scenes.forEach(function (s) {
        s.style.setProperty("--glow-x", x.toFixed(1) + "%");
        s.style.setProperty("--glow-y", y.toFixed(1) + "%");
      });
    }
    if (!window.matchMedia("(pointer: fine)").matches) return;
    window.addEventListener("pointermove", function (e) {
      set((e.clientX / window.innerWidth) * 100, (e.clientY / window.innerHeight) * 100);
    }, { passive: true });
    window.addEventListener("mouseleave", function () { set(50, 50); });
  }

  // ---------- main loop -----------------------------------------------------
  function tick(time) {
    var sy = window.pageYOffset || document.documentElement.scrollTop || 0;

    // Scenes: scrubbed horizontal drift, one speed per layer.
    root.querySelectorAll(".scene[data-parallax]").forEach(function (scene) {
      var speed = parseFloat(scene.getAttribute("data-parallax")) || 0;
      var top = scene.parentElement.getBoundingClientRect().top + sy;
      var dx = (sy - top) * speed * 0.18;
      scene.style.transform = "translateX(" + dx.toFixed(1) + "px)";
    });

    if (heroFox) applyHero(heroProgress(sy), time || 0);
    updateMarkers(sy);

    if (!reduced) rafId = raf(tick);
  }

  // ---------- init ----------------------------------------------------------
  function init() {
    measure();
    initGlow();
    initMarkers();
    initReveals();
    initChapterFoxes();

    if (reduced) {
      applyHero(1, 0);          // static, awake, fully visible
      updateMarkers(window.pageYOffset || 0);
      return;
    }

    rafId = raf(tick);

    var resizeTimer = null;
    function remeasure() {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        measure();
        tick(performance.now ? performance.now() : Date.now());
      }, 180);
    }
    window.addEventListener("resize", remeasure);
    window.addEventListener("orientationchange", function () {
      setTimeout(remeasure, 260);
    });
  }

  if (document.readyState !== "loading") {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
