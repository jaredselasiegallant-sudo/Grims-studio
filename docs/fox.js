// Grims Studio — Kit the fox mascot rig (state machine, Anime.js v4).
// Progressive enhancement by design:
//   - No JS / anime failed to load -> the fox renders as a complete static illustration.
//   - prefers-reduced-motion      -> static fox, no motion at all.
//   - Touch devices               -> tap reactions instead of cursor tracking.
//
// Layers of the rig (they never fight over the same element):
//   /look/   rAF-driven neck + pupils follow the pointer (cursor tracking).
//   /ambient/ anime.js loops: tail sway, body breathe, blink, twitch, tilt, particles.
//   /reaction/ perks the ears and widens the eyes when a card is hovered.
//   /easter/ on a long tap / click: goggles + ripple + floating pill + hearts.
//   /dock/   scrolls the fox down and resizes it onto the featured card.
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

  var root = fox;
  var neck = q('.fx-neck');
  var head = q('.fx-head');
  var tail = q('.fx-tail');
  var body = q('.fx-body');
  var paws = q('.fx-paws');
  var ears = qa('.fx-ear');
  var eyes = q('.fx-eyes');
  var squint = q('.fx-squint');
  var pupils = qa('.fx-pupil');
  var stage = fox.parentElement; // .fox-stage / .fox-corner / .nf-stage
  var appCards = document.querySelectorAll('.project-card');

  var lookX = 0, lookY = 0, curX = 0, curY = 0;
  var glanceX = 0, dartX = 0, scrollBias = 0;
  var foxRect = null, lastScrollY = window.scrollY || 0;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var easterCooldown = 0;
  var petLock = false;

  function setStyle(el, props) { for (var k in props) el.style[k] = props[k]; }

  function restoreStatic() {
    [neck, head, tail, body, paws].forEach(function (el) { if (el) el.style.transform = ''; });
    [body, head, paws].forEach(function (el) { if (el) el.style.opacity = '1'; });
    ears.forEach(function (el) { el.style.transform = ''; el.style.opacity = '1'; });
  }

  // ---- entrance ------------------------------------------------------------
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

  function startAmbient() {
    anims = {};
    anims.tail = ambientTail();
    anims.breathe = animate(body, {
      scaleY: [1.0, 1.04], duration: 3600, ease: 'inOutSine', loop: true, alternate: true
    });
    scheduleBlink();
    scheduleTwitch();
    scheduleTilt();
    scheduleEaster();
    buildParticles();
  }

  var anims = {};

  function ambientTail() {
    return animate(tail, { rotate: 9, duration: 2600, ease: 'inOutSine', loop: true, alternate: true });
  }

  // ---- ambient loops -------------------------------------------------------
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
      if (ear) animate(ear, { rotate: [{ to: -13, duration: 130 }, { to: 4, duration: 120 }, { to: 0, duration: 160 }], ease: 'outQuad' });
      scheduleTwitch();
    }, rnd(3800, 9000));
  }
  function scheduleTilt() {
    setTimeout(function () {
      var side = Math.random() > 0.5 ? 5 : -5;
      animate(head, { rotate: [{ to: side, duration: 500, ease: 'inOutSine' }, { to: side, duration: 380 }, { to: 0, duration: 500, ease: 'inOutSine' }] });
      scheduleTilt();
    }, rnd(8000, 16000));
  }
  function scheduleEaster() {
    setTimeout(function () {
      if (!fox || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      easterCooldown = 4000;
      easterEgg();
      scheduleEaster();
    }, rnd(12000, 28000));
  }

  // ---- idle physics extras (chest rise) ------------------------------------
  function idleChest() {
    animate(body, { scaleX: [1.0, 1.018], duration: 3400, ease: 'inOutSine', loop: true, alternate: true });
  }

  // ---- reaction layer ------------------------------------------------------
  function startReactive() {
    measure();
    window.addEventListener('resize', measure);
    window.addEventListener('scroll', measure, { passive: true });
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
    applyDock();
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
      neck.style.transform = 'translate(' + hx.toFixed(2) + 'px,' + hy.toFixed(2) + 'px) rotate(' + hr.toFixed(2) + 'deg)';
    }
    var px = curX * 5 + dartX * 6 + glanceX * 2;
    var py = curY * 3.5;
    pupils.forEach(function (p) { p.style.transform = 'translate(' + px.toFixed(2) + 'px,' + py.toFixed(2) + 'px)'; });
    requestAnimationFrame(tick);
  }

  function applyDock() {
    var docked = window.scrollY > 420;
    if (stage) stage.classList.toggle('docked', docked);
    if (fox && docked) {
      fox.style.transform = 'scale(0.62) translate(40px, -10px)';
      fox.style.opacity = '0.92';
    } else if (fox) {
      fox.style.transform = '';
      fox.style.opacity = '1';
    }
  }

  function bindCards() {
    if (!fine) return;
    var ready = function () { measure(); };
    appCards.forEach(function (card) {
      card.addEventListener('mouseenter', function () {
        if (!foxRect) measure();
        var cr = card.getBoundingClientRect();
        glanceX = clamp(((cr.left + cr.width / 2) - (foxRect.left + foxRect.width / 2)) / (window.innerWidth * 0.5), -1, 1) * 0.8;
        perkEars(Math.random() > 0.5 ? -1 : 1);
        widenEyes(1.4);
      });
      card.addEventListener('mouseleave', function () {
        perkEars(0);
        widenEyes(1);
      });
    });
  }

  function perkEars(side) {
    if (!ears.length) return;
    if (side === 0) { ears.forEach(function (e) { setStyle(e, { scaleY: 1 }); }); return; }
    var ear = ears[side < 0 ? 0 : 1];
    if (!ear) return;
    animate(ear, { scaleY: [1, 1.08, 1.12, 1.06, 1], duration: 360, ease: 'outQuad' });
  }

  function widenEyes(v) {
    var target = v;
    if (eyes) {
      var cur = 1;
      animate(eyes, { scaleX: [1, target * 0.99, 1], duration: 340, ease: 'outQuad' });
      animate(pupils, { scaleX: [1, target * 0.98, 1], duration: 340, ease: 'outQuad' });
      animate(pupils, { scaleY: [1, target * 0.98, 1], duration: 340, ease: 'outQuad' });
    }
  }

  // ---- easter egg ----------------------------------------------------------
  function spawnGoggles() {
    var g = document.createElement('div');
    g.className = 'goggles';
    g.innerHTML = '<i style="position:absolute;left:0;right:0;top:6px;height:2px;background:#fff;border-radius:2px"></i><i style="position:absolute;left:14px;top:0;bottom:0;background:#fff;border-radius:2px"></i><i style="position:absolute;left:0;right:0;bottom:6px;background:#fff;border-radius:2px"></i>';
    g.style.left = '50%';
    g.style.top = '50%';
    g.style.width = '56%';
    g.style.height = '40%';
    g.style.transform = 'translate(-50%,-50%) scale(0.3)';
    g.style.opacity = '0';
    fox.appendChild(g);
    animate(g, {
      opacity: 1, scaleX: 1, scaleY: 1, duration: 220, ease: 'outQuad',
      onComplete: function () { animate(g, { scaleX: 1.15, scaleY: 0.8, duration: 520, ease: 'outQuad' }); }
    });
  }

  function spawnPill() {
    var p = document.createElement('div');
    p.className = 'pill-float';
    p.textContent = '✚';
    p.style.left = rnd(10, 86) + '%';
    p.style.top = rnd(10, 70) + '%';
    p.style.color = '#00E5A0';
    p.style.fontSize = (rnd(22, 34)) + 'px';
    p.style.opacity = '0';
    p.style.transform = 'rotate(-12deg)';
    fox.appendChild(p);
    animate(p, {
      opacity: 1, y: -rnd(40, 70), x: rnd(-20, 20), rotate: rnd(-20, 20),
      duration: rnd(1600, 2400), ease: 'easeOutExpo',
      onComplete: function () { p.style.opacity = '0'; }
    });
    // a small "purr" ripple
    (function (ripple) {
      var r = document.createElement('div');
      r.className = 'ripple-wave';
      r.style.position = 'absolute';
      r.style.left = ripple + '%';
      r.style.top = ripple + '%';
      r.style.width = '10px';
      r.style.height = '10px';
      r.style.borderRadius = '50%';
      r.style.background = 'rgba(0,229,160,0.4)';
      r.style.transform = 'scale(0.6)';
      r.style.opacity = '0.8';
      fox.appendChild(r);
      animate(r, {
        width: '180px', height: '180px', scaleX: 1, scaleY: 1, opacity: 0,
        duration: rnd(600, 900), ease: 'easeOutExpo',
        onComplete: function () { r.remove(); }
      });
    })(rnd(5, 90));
  }

  function easterEgg() {
    if (easterCooldown > 0) return;
    easterCooldown = 5000;
    spawnGoggles();
    spawnPill();
    spawnHearts();
    animate(root, { scaleY: [1, 0.96, 1], translateY: -10, duration: 360, ease: 'outQuad' });
    setTimeout(function () {
      animate(root, { translateY: 0 });
    }, 350);
    setStyle(squint, { opacity: '1' });
    animate(eyes, { scaleY: 0.16, duration: 130, ease: 'out', onComplete: function () { animate(eyes, { scaleY: 1, duration: 300, ease: 'outQuad' }); } });
    setTimeout(function () { setStyle(squint, { opacity: '0' }); }, 780);
  }

  var petLock = false;
  function petFox() {
    if (petLock) return;
    petLock = true;
    setStyle(squint, { opacity: '1' });
    animate(eyes, { scaleY: 0.12, duration: 130, ease: 'out' });
    wagTail();
    spawnHearts();
    animate(root, { translateY: [{ to: -8, duration: 160, ease: 'out' }, { to: 0, duration: 300, ease: 'outQuad' }] });
    setTimeout(function () {
      animate(eyes, { scaleY: 1, duration: 300, ease: 'outQuad' });
      setStyle(squint, { opacity: '0' });
      petLock = false;
    }, 780);
  }

  function wagTail() {
    if (anims.tail) anims.tail.cancel();
    animate(tail, { rotate: [{ to: -24, duration: 140, ease: 'outQuad' }, { to: 18, duration: 150 }, { to: -14, duration: 150 }, { to: 10, duration: 140 }, { to: 0, duration: 170, ease: 'inOutQuad' }], onComplete: function () { anims.tail = ambientTail(); } });
  }

  function spawnHearts() {
    if (!stage) return;
    var glyphs = ['\u2665', '\u2665', '\u2726'];
    for (var i = 0; i < 3; i++) {
      (function (i) {
        var h = document.createElement('span');
        h.className = 'heart';
        h.textContent = glyphs[i] || '\u2665';
        h.style.left = rnd(foxRect ? foxRect.width * 0.25 : 20, foxRect ? foxRect.width * 0.75 : 80) + 'px';
        h.style.top = rnd(foxRect ? foxRect.height * 0.1 : 10, foxRect ? foxRect.height * 0.38 : 30) + 'px';
        stage.appendChild(h);
        animate(h, {
          translateY: -rnd(38, 66), opacity: [{ to: 1, duration: 100 }, { to: 0, duration: 600, delay: 250 }], scale: [{ to: 1.2, duration: 200 }, { to: 0.8, duration: 600 }],
          duration: 850, ease: 'out', onComplete: function () { h.remove(); }
        });
      })(i);
    }
  }

  // ---- keyboard ------------------------------------------------------------
  var lastKey = 0;
  function onKey(e) {
    if (e.target && e.target.closest && e.target.closest('input, textarea, select, [contenteditable]')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'Enter' || e.key === ' ') {
      if (Date.now() - lastKey < 350) return;
      lastKey = Date.now();
      hop();
    } else {
      if (Date.now() - lastKey < 160) return;
      lastKey = Date.now();
      perkEars(Math.random() > 0.5 ? -1 : 1);
      dartX = rnd(-1, 1);
    }
  }

  function hop() {
    animate(root, { translateY: [{ to: -18, duration: 220, ease: 'out' }, { to: 0, duration: 380, ease: 'outBounce' }], scaleY: [{ to: 0.94, duration: 110 }, { to: 1.05, duration: 140 }, { to: 1, duration: 320 }], ease: 'outQuad' });
  }

  function measure() { foxRect = fox.getBoundingClientRect(); }

  // ---- entrance ------------------------------------------------------------
  try {
    setStyle(body, { transform: 'translateY(46px)', opacity: '0' });
    setStyle(head, { transform: 'translateY(30px) scale(.72)', opacity: '0' });
    setStyle(paws, { transform: 'translateY(12px)', opacity: '0' });
    setStyle(tail, { transform: 'rotate(-24deg)' });
    ears.forEach(function (ear) { setStyle(ear, { scaleY: '.25' }); });

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
})();
