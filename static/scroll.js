// Improved parallax based on element position in viewport
(function(){
  const parallaxEls = Array.from(document.querySelectorAll('.parallax'));
  const textEls = Array.from(document.querySelectorAll('.parallax-text'));

  function update(){
    const vh = window.innerHeight;
    parallaxEls.forEach(el => {
      const speed = parseFloat(el.dataset.speed || '0.2');
      const rect = el.getBoundingClientRect();
      // distance from center
      const dist = rect.top + rect.height/2 - vh/2;
      // translate proportionally, clamp for stability
      const y = Math.max(-200, Math.min(200, -dist * speed * 0.12));
      el.style.transform = `translate3d(0, ${y}px, 0)`;
    });

    textEls.forEach(el => {
      const speed = parseFloat(el.dataset.speed || '-0.2');
      const rect = el.getBoundingClientRect();
      const dist = rect.top + rect.height/2 - vh/2;
      const y = Math.max(-200, Math.min(200, -dist * speed * 0.12));
      el.style.transform = `translate3d(0, ${y}px, 0)`;
    });
  }

  let rafId = null;
  function onScroll(){
    if(rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(update);
  }

  window.addEventListener('scroll', onScroll, {passive: true});
  window.addEventListener('resize', onScroll);
  // initial
  update();
})();

// Reveal-on-scroll using IntersectionObserver
(function(){
  const revealSelector = '.reveal-on-scroll';
  const revealEls = Array.from(document.querySelectorAll(revealSelector));
  if (!revealEls.length) return;

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in-view');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  revealEls.forEach(el => observer.observe(el));
})();
