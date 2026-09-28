// Shared behaviour for every page: header state, mobile menu,
// scroll reveals, image lightbox and footer year.
(function () {
  document.documentElement.classList.add('js');

  // header border once the page scrolls
  const header = document.querySelector('.site-header');
  const onScroll = () => header && header.classList.toggle('scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // mobile menu
  const menuBtn = document.querySelector('.menu-btn');
  if (menuBtn) {
    menuBtn.addEventListener('click', () => {
      const open = document.body.classList.toggle('menu-open');
      menuBtn.setAttribute('aria-expanded', open);
    });
    document.querySelectorAll('.nav a').forEach(a =>
      a.addEventListener('click', () => {
        document.body.classList.remove('menu-open');
        menuBtn.setAttribute('aria-expanded', false);
      })
    );
  }

  // reveal on scroll
  const items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    items.forEach(el => io.observe(el));
  } else {
    items.forEach(el => el.classList.add('in'));
  }

  // lightbox for any .zoomable figure
  const zoomables = document.querySelectorAll('.zoomable');
  if (zoomables.length) {
    const box = document.createElement('div');
    box.className = 'lightbox';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<button type="button" aria-label="Close">&times;</button><img alt="">';
    document.body.appendChild(box);
    const big = box.querySelector('img');

    const close = () => box.classList.remove('open');
    zoomables.forEach(fig => {
      const img = fig.querySelector('img');
      fig.setAttribute('tabindex', '0');
      const open = () => {
        big.src = img.currentSrc || img.src;
        big.alt = img.alt;
        box.classList.add('open');
      };
      fig.addEventListener('click', open);
      fig.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
      });
    });
    box.addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }

  // semester columns on the home page: preload hover image from data-img
  document.querySelectorAll('.sem-col[data-img]').forEach(col => {
    const layer = col.querySelector('.img');
    if (layer) layer.style.backgroundImage = `url("${col.dataset.img}")`;
  });

  const year = document.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();
})();
