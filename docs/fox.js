// Grims Studio — Kit the fox mascot rig (Anime.js v4, vendored locally).
//
// Progressive enhancement by design:
//   - No JS / anime failed to load -> the fox renders as a complete static illustration.
//   - prefers-reduced-motion      -> static fox, no motion at all.
//   - Touch devices               -> tap reactions instead of cursor tracking.
//
// The fox is inline SVG with a layered rig (.fx-* groups). CSS owns the
// transform-origins (see style.css); this file owns the choreography.
//
// Architecture note: pointer "look" is driven by one rAF loop that writes
// transforms to .fx-neck + pupils only. Anime.js drives loops on separate
// groups (.fx-head tilt, .fx-tail, .fx-body), so the two systems never
// fight over the same element.
(function () {
  'use strict';

  var fox = document.querySelector('.fox');
  if (!fox || typeof window.anime === 'undefined' || !window.anime.animate) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var animate = window.anime.animate;
  var timeline = window.anime.createTimeline;
  var stagger = window.anime.stagger;

  function q(sel) { return fox.querySelector(sel); }
  function qa(sel) { return Array.prototype.slice.call(fox.querySelectorAll(sel)); }
  function rnd(min, max) { return min + Math.random() * (max - min); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  var root = fox;              // whole fox (hop / pet-bounce target)
  var neck = q('.fx-neck');    // JS-driven look layer
  var head = q('.fx-head');    // anime-driven tilt layer
  var tail = q('.fx-tail');
  var body = q('.fx-body');
  var paws = q('.fx-paws');
  var ears = qa('.fx-ear');
  var eyes = q('.fx-eyes');
  var squint = q('.fx-squint');
  var pupils = qa('.fx-pupil');
  var stage = fox.parentElement; // .fox-stage / .fox-corner / .nf-stage
  var anims = {};                // ambient animation handles

  function setStyle(el, props) {
    if (!el) return;
    for (var k in props) el.style[k] = props[k];
  }

  // If anything throws mid-entrance, fall back to the fully visible fox.
  function restoreStatic() {
    [neck, head, tail, body, paws].forEach(function (el) {
      if (el) el.style.transform = '';
    });
    [body, head, paws].forEach(function (el) {
      if (el) el.style.opacity = '1';
    });
    ears.forEach(function (el) {
      el.style.transform = '';
      el.style.opacity = '1';
    });
  }

  // ---- headline letters (Home hero) ---------------------------------------
  function splitLetters(el) {
    var text = el.textContent;
    el.textContent = '';
    el.setAttribute('aria-label', text);
    var holder = document.createElement('span');
    holder.setAttribute('aria-hidden', 'true');
    text.split(/(\s+)/).forEach(function (tok) {
      if (!tok) return;
      if (/^\s+$/.test(tok)) { holder.appendChild(document.createTextNode(' ')); return; }
      var w = document.createElement('span');
      w.className = 'word';
      for (var i = 0; i < tok.length; i++) {
        var ch = document.createElement('span');
        ch.className = 'ch';
        ch.textContent = tok[i];
        w.appendChild(ch);
      }
      holder.appendChild(w);
    });
    el.appendChild(holder);
    animate(el.querySelectorAll('.ch'), {
      translateY: ['0.9em', '0em'],
      opacity: [0, 1],
      duration: 620,
      delay: stagger(26, { start: 140 }),
      ease: 'out(3)'
    });
  }

  // ---- entrance ------------------------------------------------------------
  try {
    setStyle(body, { transform: 'translateY(46px)', opacity: '0' });
    setStyle(head, { transform: 'translateY(30px) scale(.72)', opacity: '0' });
    setStyle(paws, { transform: 'translateY(12px)', opacity: '0' });
    setStyle(tail, { transform: 'rotate(-24deg)' });
    ears.forEach(function (ear) { setStyle(ear, { transform: 'scaleY(.25)' }); });

    var heroTitle = document.querySelector('.fox-hero h1');
    if (heroTitle && window.anime.stagger) splitLetters(heroTitle);

    timeline({ defaults: { ease: 'out(3)', duration: 720 } })
      .add(body, { translateY: 0, opacity: 1 }, 120)
      .add(tail, { rotate: 0, duration: 900, ease: 'outBack(1.2)' }, 260)
      .add(head, { translateY: 0, scale: 1, opacity: 1, duration: 800, ease: 'outBack(1.4)' }, 380)
      .add(ears, { scaleY: 1, duration: 620, ease: 'outBack(2)' }, 640)
      .add(paws, { translateY: 0, opacity: 1, duration: 480 }, 800)
      .then(function () { startAmbient(); startReactive(); });
  } catch (err) {
    restoreStatic();
    return;
  }

  // ---- ambient loops ("playful & alive") -----------------------------------
  function ambientTail() {
    return animate(tail, {
      rotate: 9, duration: 2600, ease: 'inOutSine', loop: true, alternate: true
    });
  }

  function startAmbient() {
    anims.tail = ambientTail();
    animate(body, { scaleY: 1.02, duration: 3400, ease: 'inOutSine', loop: true, alternate: true });
    scheduleBlink();
    scheduleTwitch();
    scheduleTilt();
    buildParticles();
  }

  function scheduleBlink() {
    setTimeout(function () {
      blink();
      scheduleBlink();
    }, rnd(2200, 5600));
  }

  function blink() {
    animate(eyes, {
      scaleY: [{ to: 0.06, duration: 80 }, { to: 1, duration: 150 }],
      ease: 'inOutQuad'
    });
  }

  function scheduleTwitch() {
    setTimeout(function () {
      var ear = ears[Math.floor(Math.random() * ears.length)];
      if (ear) {
        animate(ear, {
          rotate: [{ to: -13, duration: 130 }, { to: 4, duration: 120 }, { to: 0, duration: 160 }],
          ease: 'outQuad'
        });
      }
      scheduleTwitch();
    }, rnd(3800, 9000));
  }

  function scheduleTilt() {
    setTimeout(function () {
      var side = Math.random() > 0.5 ? 5 : -5;
      animate(head, {
        rotate: [
          { to: side, duration: 500, ease: 'inOutSine' },
          { to: side, duration: 380 },
          { to: 0, duration: 500, ease: 'inOutSine' }
        ]
      });
      scheduleTilt();
    }, rnd(8000, 16000));
  }

  function buildParticles() {
    if (!stage || stage.classList.contains('fox-corner')) return;
    var colors = ['rgba(14,124,107,.5)', 'rgba(255,138,61,.6)', 'rgba(18,20,23,.22)'];
    for (var i = 0; i < 12; i++) {
      var d = document.createElement('span');
      d.className = 'dot';
      var s = rnd(4, 9);
      d.style.width = s + 'px';
      d.style.height = s + 'px';
      d.style.left = rnd(4, 94) + '%';
      d.style.top = rnd(6, 90) + '%';
      d.style.background = colors[i % colors.length];
      stage.appendChild(d);
      animate(d, {
        translateY: [-rnd(10, 22), rnd(6, 18)],
        duration: rnd(2400, 5200),
        delay: rnd(0, 2200),
        loop: true,
        alternate: true,
        ease: 'inOutSine'
      });
    }
  }

  // ---- reactive layer ------------------------------------------------------
  var lookX = 0, lookY = 0, curX = 0, curY = 0;      // pointer look
  var glanceX = 0, dartX = 0, scrollBias = 0;        // decaying bias terms
  var foxRect = null, lastScrollY = window.scrollY || 0;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function measure() { foxRect = fox.getBoundingClientRect(); }

  function startReactive() {
    measure();
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
    if (fine) document.addEventListener('pointermove', onPointer);
    document.addEventListener('pointerdown', onDocPress);
    document.addEventListener('keydown', onKey);
    bindCards();
    requestAnimationFrame(tick);
  }

  function onPointer(e) {
    if (!foxRect) measure();
    lookX = clamp((e.clientX - (foxRect.left + foxRect.width / 2)) / (window.innerWidth * 0.55), -1, 1);
    lookY = clamp((e.clientY - (foxRect.top + foxRect.height / 2)) / (window.innerHeight * 0.55), -1, 1);
  }

  function onScroll() {
    var y = window.scrollY || 0;
    scrollBias = clamp(scrollBias + clamp((y - lastScrollY) * 0.004, -0.5, 0.5), -0.6, 0.6);
    lastScrollY = y;
  }

  function tick() {
    curX += (lookX - curX) * 0.085;
    curY += (lookY + scrollBias - curY) * 0.085;
    glanceX *= 0.93;
    dartX *= 0.90;
    scrollBias *= 0.94;
    if (neck) {
      var hx = curX * 7 + glanceX * 5;
      var hy = curY * 5;
      var hr = (curX + glanceX) * 3;
      neck.style.transform = 'translate(' + hx.toFixed(2) + 'px,' + hy.toFixed(2) +
        'px) rotate(' + hr.toFixed(2) + 'deg)';
    }
    var px = curX * 5 + dartX * 6 + glanceX * 2;
    var py = curY * 3.5;
    pupils.forEach(function (p) {
      p.style.transform = 'translate(' + px.toFixed(2) + 'px,' + py.toFixed(2) + 'px)';
    });
    requestAnimationFrame(tick);
  }

  // clicks / taps: pet the fox, or glance toward the point
  function onDocPress(e) {
    if (e.target.closest && e.target.closest('.fox')) { petFox(); return; }
    if (e.target.closest && e.target.closest('a, button, input, summary, label')) return;
    if (!foxRect) measure();
    var side = e.clientX < foxRect.left + foxRect.width / 2 ? -1 : 1;
    glanceX = clamp(side * 0.9, -1, 1);
    perkEar(side);
  }

  function perkEar(side) {
    var ear = q(side < 0 ? '.fx-ear-l' : '.fx-ear-r');
    if (ear) {
      animate(ear, {
        rotate: [{ to: side * -12, duration: 140, ease: 'out' }, { to: 0, duration: 260, ease: 'outQuad' }]
      });
    }
  }

  var petLock = false;
  function petFox() {
    if (petLock) return;
    petLock = true;
    setStyle(squint, { opacity: '1' });
    animate(eyes, { scaleY: 0.12, duration: 140, ease: 'out' });
    wagTail();
    spawnHearts();
    animate(root, {
      translateY: [{ to: -8, duration: 160, ease: 'out' }, { to: 0, duration: 300, ease: 'outQuad' }]
    });
    setTimeout(function () {
      animate(eyes, { scaleY: 1, duration: 320, ease: 'outQuad' });
      setStyle(squint, { opacity: '0' });
      petLock = false;
    }, 780);
  }

  function wagTail() {
    if (anims.tail) anims.tail.cancel();
    animate(tail, {
      rotate: [
        { to: -24, duration: 140, ease: 'outQuad' },
        { to: 18, duration: 150 },
        { to: -14, duration: 150 },
        { to: 10, duration: 140 },
        { to: 0, duration: 170, ease: 'inOutQuad' }
      ],
      onComplete: function () { anims.tail = ambientTail(); }
    });
  }

  function spawnHearts() {
    if (!stage) return;
    var rect = fox.getBoundingClientRect();
    var glyphs = ['\u2665', '\u2665', '\u2726'];
    for (var i = 0; i < 3; i++) {
      (function (i) {
        var h = document.createElement('span');
        h.className = 'heart';
        h.textContent = glyphs[i] || '\u2665';
        h.style.left = rnd(rect.width * 0.25, rect.width * 0.75) + 'px';
        h.style.top = rnd(rect.height * 0.1, rect.height * 0.38) + 'px';
        stage.appendChild(h);
        animate(h, {
          translateY: -rnd(38, 66),
          opacity: [{ to: 1, duration: 100 }, { to: 0, duration: 600, delay: 250 }],
          scale: [{ to: 1.2, duration: 200 }, { to: 0.8, duration: 600 }],
          duration: 850,
          ease: 'out',
          onComplete: function () { h.remove(); }
        });
      })(i);
    }
  }

  // keyboard: ears perk + pupils dart on typing; hop on Enter/Space
  var lastKey = 0;
  function onKey(e) {
    if (e.target && e.target.closest && e.target.closest('input, textarea, select, [contenteditable]')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var now = Date.now();
    if (e.key === 'Enter' || e.key === ' ') {
      if (now - lastKey < 350) return;
      lastKey = now;
      hop();
    } else {
      if (now - lastKey < 160) return;
      lastKey = now;
      perkEar(Math.random() > 0.5 ? -1 : 1);
      dartX = rnd(-1, 1);
    }
  }

  function hop() {
    animate(root, {
      translateY: [{ to: -18, duration: 220, ease: 'out' }, { to: 0, duration: 380, ease: 'outBounce' }],
      scaleY: [{ to: 0.94, duration: 110 }, { to: 1.05, duration: 140 }, { to: 1, duration: 320 }],
      ease: 'outQuad'
    });
  }

  // hovering an app card makes Kit glance at it
  function bindCards() {
    var cards = document.querySelectorAll('.project-card');
    if (!cards.length || !fine) return;
    cards.forEach(function (card) {
      card.addEventListener('mouseenter', function () {
        if (!foxRect) measure();
        var cr = card.getBoundingClientRect();
        glanceX = clamp(
          ((cr.left + cr.width / 2) - (foxRect.left + foxRect.width / 2)) / (window.innerWidth * 0.5),
          -1, 1
        ) * 0.8;
      });
    });
  }
})();
