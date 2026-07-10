(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const reveals = [...document.querySelectorAll('.reveal')];

  if (reduceMotion || !('IntersectionObserver' in window)) {
    reveals.forEach((node) => node.classList.add('in'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    reveals.forEach((node) => observer.observe(node));
    window.setTimeout(() => reveals.forEach((node) => node.classList.add('in')), 1800);
  }

  const sections = [...document.querySelectorAll('main section[id]')];
  const navLinks = [...document.querySelectorAll('.site-nav a')];
  if (sections.length && navLinks.length && 'IntersectionObserver' in window) {
    const sectionObserver = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      navLinks.forEach((link) => link.classList.toggle('active', link.hash === `#${visible.target.id}`));
    }, { threshold: [0.25, 0.5, 0.75] });
    sections.forEach((section) => sectionObserver.observe(section));
  }

  const parallax = document.querySelector('[data-parallax]');
  if (parallax && !reduceMotion && matchMedia('(pointer:fine)').matches) {
    const visual = parallax.parentElement;
    visual.addEventListener('pointermove', (event) => {
      const rect = visual.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * 10;
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * 10;
      parallax.style.transform = `perspective(900px) rotateX(${-y * 0.35}deg) rotateY(${x * 0.35}deg) translate3d(${x}px, ${y}px, 0)`;
    });
    visual.addEventListener('pointerleave', () => { parallax.style.transform = ''; });
  }
})();
