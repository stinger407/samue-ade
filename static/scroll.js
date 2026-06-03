// Lightweight parallax/scroll movement
(function(){
  const parallaxEls = Array.from(document.querySelectorAll('.parallax'));
  const textEls = Array.from(document.querySelectorAll('.parallax-text'));
  let latestScroll = 0;
  let ticking = false;

  function onScroll(){
    latestScroll = window.scrollY || window.pageYOffset;
    if(!ticking){
      ticking = true;
      requestAnimationFrame(update);
    }
  }

  function update(){
    const sc = latestScroll;
    parallaxEls.forEach(el => {
      const speed = parseFloat(el.dataset.speed || '0.2');
      el.style.transform = `translateY(${Math.round(sc * speed)}px)`;
    });
    textEls.forEach(el => {
      const speed = parseFloat(el.dataset.speed || '-0.2');
      el.style.transform = `translateY(${Math.round(sc * speed)}px)`;
    });
    ticking = false;
  }

  document.addEventListener('scroll', onScroll, {passive:true});
  // Initialize positions
  update();
})();
