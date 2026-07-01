document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", () => {
  const items = document.querySelectorAll(".reveal");
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  if (reduceMotion || !("IntersectionObserver" in window)) {
    items.forEach((item) => item.classList.add("in"));
    return;
  }

  const inView = (element) => {
    const rect = element.getBoundingClientRect();
    return rect.top < window.innerHeight && rect.bottom > 0;
  };

  items.forEach((item) => {
    if (inView(item)) item.classList.add("in");
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
  );

  items.forEach((item) => observer.observe(item));
});
