// Grims Studio — mobile nav + search / category / status filters,
// magnetic buttons, spotlight borders, staggered bento entrance.
// Progressive enhancement; guards for pages without filter controls.
(function () {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.getElementById('primary-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  }

  // ---------- magnetic buttons (pull toward the cursor) ----------
  const reducedMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const finePointer = !window.matchMedia || window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const magnets = Array.from(document.querySelectorAll('.btn-magnet, .magnet-target'));
  if (magnets.length && finePointer && !reducedMotion) {
    const state = magnets.map((el) => ({ el, x: 0, y: 0, cx: 0, cy: 0 }));
    let mx = window.innerWidth / 2, my = window.innerHeight / 2, raf = 0;

    const measure = () => {
      state.forEach((s) => {
        const r = s.el.getBoundingClientRect();
        // remove the current offset so the base centre stays stable
        s.cx = r.left + r.width / 2 - s.x;
        s.cy = r.top + r.height / 2 - s.y;
      });
    };

    const step = () => {
      state.forEach((s) => {
        const dx = mx - s.cx;
        const dy = my - s.cy;
        const near = Math.max(0, 1 - Math.hypot(dx, dy) / 280);
        const tx = dx * 0.10 * near;
        const ty = dy * 0.16 * near;
        s.x += (tx - s.x) * 0.16;
        s.y += (ty - s.y) * 0.16;
        s.el.style.transform = `translate(${s.x.toFixed(2)}px, ${s.y.toFixed(2)}px)`;
      });
      raf = 0;
    };

    measure();
    window.addEventListener('resize', measure);
    document.addEventListener('pointermove', (e) => {
      mx = e.clientX; my = e.clientY;
      if (!raf) raf = requestAnimationFrame(step);
    }, { passive: true });
  }

  // ---------- spotlight borders (glow near nearby cards) ----------
  const spotlight = document.createElement('div');
  spotlight.className = 'spotlight';
  document.body.appendChild(spotlight);
  const tiles = Array.from(document.querySelectorAll('.card, .bento-tile, .bento-banner'));
  if (tiles.length) {
    const feed = (e) => {
      spotlight.style.left = e.clientX + 'px';
      spotlight.style.top = e.clientY + 'px';
      spotlight.style.opacity = '1';
      tiles.forEach((t) => {
        const r = t.getBoundingClientRect();
        const d = Math.hypot(e.clientX - (r.left + r.width / 2), e.clientY - (r.top + r.height / 2));
        const near = 1 - Math.min(d / (r.width * 0.7), 1);
        if (near > 0.22) t.classList.add('spot');
        else if (d > r.width || d > r.height) t.classList.remove('spot');
      });
    };
    document.addEventListener('pointermove', feed);
    document.addEventListener('mouseleave', () => { spotlight.style.opacity = '0'; });
  }

  // ---------- mouse-glow attractor ----------
  const glow = document.createElement('div');
  glow.className = 'mouse-glow';
  document.body.appendChild(glow);
  document.addEventListener('pointermove', (e) => {
    glow.style.left = e.clientX + 'px';
    glow.style.top = e.clientY + 'px';
    glow.classList.remove('off');
  });
  window.addEventListener('mouseleave', () => glow.classList.add('off'));

  // ---------- staggered bento entrance ----------
  const entranceTiles = Array.from(document.querySelectorAll('.bento-tile'));
  if (entranceTiles.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add('is-visible'); });
    }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });
    entranceTiles.forEach((t) => io.observe(t));
  }

  // ---------- scroll-reveal ----------
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io2 = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-visible'); io2.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach((el) => io2.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-visible'));
  }

  // ---------- sticky header depth ----------
  const header = document.querySelector('.site-header');
  if (header) {
    const onScroll = () => { header.classList.toggle('scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ---------- nav / filters ----------
  const search = document.getElementById('app-search');
  const buttons = Array.from(document.querySelectorAll('.filter-btn'));
  const cards = Array.from(document.querySelectorAll('.project-card'));
  const empty = document.getElementById('no-results');
  const count = document.getElementById('result-count');
  const clear = document.getElementById('clear-filters');
  let activeCategory = 'all';
  let activeStatus = 'all';

  function apply() {
    const q = (search ? search.value : '').trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const hay = (card.dataset.search || '').toLowerCase();
      const cat = card.dataset.category || '';
      const st = card.dataset.status || '';
      const matchQ = !q || hay.includes(q);
      const matchC = activeCategory === 'all' || cat === activeCategory;
      const matchS = activeStatus === 'all' || st === activeStatus;
      const show = matchQ && matchC && matchS;
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (empty) empty.classList.toggle('show', visible === 0);
    if (count) count.textContent = visible + ' of ' + cards.length + ' shown';
  }

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const f = btn.dataset.filter || 'all';
      if (f.startsWith('cat:')) { activeCategory = f.slice(4) || 'all'; }
      else if (f.startsWith('status:')) { activeStatus = f.slice(7) || 'all'; }
      else { activeCategory = 'all'; activeStatus = 'all'; }
      buttons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
      apply();
    });
  });

  if (search) search.addEventListener('input', apply);
  if (clear) clear.addEventListener('click', () => {
    if (search) search.value = '';
    activeCategory = 'all';
    activeStatus = 'all';
    buttons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.filter === 'all')));
    apply();
    if (search) search.focus();
  });

  apply();
  document.querySelectorAll('.footer .quiet').forEach((el) => {
    el.textContent = '© ' + new Date().getFullYear() + ' Grims Studio · Static site';
  });

  // ---------- inner-page reveal system ----------
  // The class is only added when this script runs, so content is never hidden
  // for a visitor without JS. Stagger index comes from sibling order.
  if (!reducedMotion && 'IntersectionObserver' in window) {
    const selectors = [
      '.block .section-head', '.block .controls', '.block .prose',
      '.block .card', '.mini', '.spec', '.faq-item', '.download-hero-top',
      '.nf-stage'
    ];
    const seen = new Set();
    const targets = [];
    selectors.forEach((sel) => {
      document.querySelectorAll(sel).forEach((el) => {
        if (seen.has(el)) return;
        seen.add(el);
        targets.push(el);
      });
    });
    targets.forEach((el) => {
      let i = 0;
      let sib = el;
      while ((sib = sib.previousElementSibling)) {
        if (sib.classList.contains('will-reveal')) i += 1;
      }
      el.style.setProperty('--i', String(Math.min(i, 6)));
      el.classList.add('will-reveal');
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add('in');
        io.unobserve(e.target);
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -8% 0px' });
    targets.forEach((el) => io.observe(el));
  }
})();
