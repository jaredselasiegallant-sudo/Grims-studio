// Grims Studio — mobile nav toggle + search/category filters.
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

  function apply() {
    const q = (search ? search.value : '').trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const hay = (card.dataset.search || '').toLowerCase();
      const cat = card.dataset.category || '';
      const matchQ = !q || hay.includes(q);
      const matchC = activeCategory === 'all' || cat === activeCategory;
      const show = matchQ && matchC;
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (empty) empty.classList.toggle('show', visible === 0);
    if (count) count.textContent = visible + ' of ' + cards.length + ' shown';
  }

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      activeCategory = btn.dataset.filter || 'all';
      buttons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
      apply();
    });
  });

  if (search) search.addEventListener('input', apply);
  if (clear) clear.addEventListener('click', () => {
    if (search) search.value = '';
    activeCategory = 'all';
    buttons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.filter === 'all')));
    apply();
    if (search) search.focus();
  });

  apply();
})();
