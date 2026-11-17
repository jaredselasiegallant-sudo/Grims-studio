// Grims Studio — mobile nav toggle + search / category / status filters.
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
      if (f.startsWith('cat:')) {
        activeCategory = f.slice(4) || 'all';
      } else if (f.startsWith('status:')) {
        activeStatus = f.slice(7) || 'all';
      } else {
        activeCategory = 'all';
        activeStatus = 'all';
      }
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
  document.querySelectorAll('.footer .quiet').forEach(function (el) {
    el.textContent = '© ' + new Date().getFullYear() + ' Grims Studio · Static site';
  });

  // Scroll-reveal for below-the-fold sections (no-op if no IntersectionObserver).
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  // Sticky header gets extra depth once the user scrolls.
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () { header.classList.toggle('scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // Fade-up reveal for standard blocks (skip the hero download zone).
  document.querySelectorAll('.block:not(.download-hero)').forEach(function (el) {
    el.classList.add('reveal');
  });
})();
