/* Progressive enhancement only. All music, artwork, lyrics and links are static HTML. */
(() => {
  'use strict';
  const header = document.querySelector('.masthead');
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-nav');
  if (header && menu && nav) {
    const close = (restoreFocus = false) => {
      nav.classList.remove('is-open');
      menu.setAttribute('aria-expanded', 'false');
      menu.textContent = 'Menu';
      if (restoreFocus) menu.focus();
    };
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      nav.classList.toggle('is-open', open);
      menu.setAttribute('aria-expanded', String(open));
      menu.textContent = open ? 'Close' : 'Menu';
    });
    nav.addEventListener('click', event => { if (event.target.closest('a')) close(); });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') close(true);
    });
    document.addEventListener('click', event => { if (!header.contains(event.target)) close(); });
    window.matchMedia('(max-width: 780px)').addEventListener('change', () => close());
    header.classList.add('js-menu');
  }
  const filters = document.querySelector('.filters');
  if (filters) {
    const buttons = [...filters.querySelectorAll('[data-filter]')];
    const cards = [...document.querySelectorAll('[data-release]')];
    const groups = [...document.querySelectorAll('[data-group]')];
    const status = document.querySelector('[data-catalog-count]');
    buttons.forEach(button => button.addEventListener('click', () => {
      const kind = button.dataset.filter;
      buttons.forEach(other => other.setAttribute('aria-pressed', String(other === button)));
      groups.forEach(group => { group.hidden = kind !== 'all' && group.dataset.group !== kind; });
      const count = cards.filter(card => kind === 'all' || card.dataset.kind === kind).length;
      if (status) status.textContent = `${count} ${kind === 'all' ? 'releases' : kind + (count === 1 ? '' : 's')}`;
    }));
    filters.hidden = false;
  }
  // Deep links open native lyric disclosures without making reading depend on JS.
  function openTrack() {
    let id;
    try { id = decodeURIComponent(window.location.hash.slice(1)); } catch { return; }
    if (!id.startsWith('track-')) return;
    const target = document.getElementById(id);
    const details = target && target.querySelector('details');
    if (details) {
      details.open = true;
      window.requestAnimationFrame(() => target.scrollIntoView({block:'start', behavior:'instant'}));
    }
  }
  window.addEventListener('hashchange', openTrack);
  openTrack();
})();
