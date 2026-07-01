(() => {
  const reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const items = document.querySelectorAll(".reveal");

  const reveal = (element) => element.classList.add("in");

  if (reduceMotion || !("IntersectionObserver" in window)) {
    items.forEach(reveal);
    return;
  }

  const inView = (element) => {
    const rect = element.getBoundingClientRect();
    return rect.top < window.innerHeight && rect.bottom > 0;
  };

  items.forEach((element) => {
    if (inView(element)) reveal(element);
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          reveal(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
  );

  items.forEach((element) => observer.observe(element));

  // Fail open if a browser delays observer callbacks.
  window.setTimeout(() => items.forEach(reveal), 1600);
})();
