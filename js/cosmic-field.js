(() => {
  const field = document.querySelector('[data-cosmic-field]');
  if (!field) return;

  const canvas = field.querySelector('canvas');
  const context = canvas.getContext('2d');
  if (!context) return;

  const buttons = [...field.querySelectorAll('[data-cosmic-mode]')];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarsePointer = window.matchMedia('(pointer: coarse)').matches;

  const modes = [
    { arms:4, twist:8.2, rotation:.0012, scale:1, haze:1.1, coreDensity:160, eccentricity:.50, pulse:.9 },
    { arms:2, twist:5.6, rotation:.0009, scale:1.08, haze:1.22, coreDensity:190, eccentricity:.42, pulse:.75 },
    { arms:5, twist:10.2, rotation:.00155, scale:1.12, haze:1.34, coreDensity:210, eccentricity:.56, pulse:1.08 }
  ];

  let modeIndex = 0;
  let width = 0;
  let height = 0;
  let centerX = 0;
  let centerY = 0;
  let radius = 0;
  let time = 0;
  let pointerX = 0;
  let pointerY = 0;
  let pointerActive = false;
  let tiltX = 0;
  let tiltY = 0;
  let targetTiltX = 0;
  let targetTiltY = 0;
  let touchStartX = null;
  let visible = true;
  let stars = [];
  let coreParticles = [];

  const clamp = (value, minimum, maximum) => Math.min(maximum, Math.max(minimum, value));
  const lerp = (start, end, amount) => start + (end - start) * amount;
  const random = (minimum, maximum) => minimum + Math.random() * (maximum - minimum);
  const rainbow = (hue, alpha = 1) => `hsla(${hue},92%,68%,${alpha})`;

  function resize() {
    const rect = field.getBoundingClientRect();
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

    canvas.width = Math.round(rect.width * pixelRatio);
    canvas.height = Math.round(rect.height * pixelRatio);
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;

    context.setTransform(1, 0, 0, 1, 0, 0);
    context.scale(pixelRatio, pixelRatio);

    width = rect.width;
    height = rect.height;
    centerX = width / 2;
    centerY = height / 2;
    radius = Math.min(width, height) / 2;
    buildParticles();
  }

  function buildParticles() {
    stars = [];
    coreParticles = [];

    const mode = modes[modeIndex];
    const starCount = coarsePointer ? 560 : 820;

    for (let index = 0; index < starCount; index += 1) {
      const arm = index % mode.arms;
      const branch = Math.PI * 2 * arm / mode.arms;
      const distance = Math.pow(Math.random(), .76);
      const angle = branch
        + distance * mode.twist
        + random(-.55, .55) * (.15 + distance * 1.8);

      stars.push({
        distance,
        angle,
        spin:random(-.0007, .0007),
        jitter:random(.25, 1.8),
        size:random(.6, 2.8) * mode.scale,
        alpha:random(.25, .95),
        hue:random(0, 360),
        depth:random(-1, 1)
      });
    }

    for (let index = 0; index < mode.coreDensity; index += 1) {
      coreParticles.push({
        distance:Math.pow(Math.random(), 1.7) * radius * .16,
        angle:Math.random() * Math.PI * 2,
        orbit:random(-.0035, .0035),
        size:random(1.2, 4.4),
        alpha:random(.35, .95),
        hue:random(0, 360)
      });
    }
  }

  function setMode(index) {
    modeIndex = (index + modes.length) % modes.length;

    buttons.forEach((button, buttonIndex) => {
      const active = buttonIndex === modeIndex;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
      button.tabIndex = active ? 0 : -1;
    });

    buildParticles();
  }

  function applyPointer(clientX, clientY) {
    const rect = field.getBoundingClientRect();
    pointerX = clientX - rect.left;
    pointerY = clientY - rect.top;
    pointerActive = true;

    targetTiltX = clamp((pointerX / rect.width - .5) * 16, -9, 9);
    targetTiltY = clamp((pointerY / rect.height - .5) * -16, -9, 9);
  }

  function clearPointer() {
    pointerActive = false;
    targetTiltX = 0;
    targetTiltY = 0;
  }

  function displaceFromPointer(x, y, reach, strength) {
    if (!pointerActive || reduceMotion) return { x, y };

    const deltaX = x - pointerX;
    const deltaY = y - pointerY;
    const distance = Math.hypot(deltaX, deltaY);
    const influence = Math.max(0, 1 - distance / reach);

    if (!influence) return { x, y };

    const force = influence * influence * strength;
    return {
      x:x + (deltaX / (distance || 1)) * force,
      y:y + (deltaY / (distance || 1)) * force
    };
  }

  function drawBackgroundGlow(mode) {
    const outerGlow = context.createRadialGradient(
      centerX, centerY, radius * .02,
      centerX, centerY, radius * .9
    );
    outerGlow.addColorStop(0, 'rgba(255,255,255,.22)');
    outerGlow.addColorStop(.08, 'rgba(255,133,235,.18)');
    outerGlow.addColorStop(.16, 'rgba(96,230,255,.14)');
    outerGlow.addColorStop(.34, 'rgba(110,133,255,.10)');
    outerGlow.addColorStop(.64, 'rgba(255,215,108,.04)');
    outerGlow.addColorStop(1, 'rgba(7,7,9,0)');

    context.fillStyle = outerGlow;
    context.beginPath();
    context.arc(centerX, centerY, radius * .92, 0, Math.PI * 2);
    context.fill();

    const innerGlow = context.createRadialGradient(
      centerX, centerY, radius * .01,
      centerX, centerY, radius * (mode.haze * .36)
    );
    innerGlow.addColorStop(0, 'rgba(255,255,255,.82)');
    innerGlow.addColorStop(.08, 'rgba(255,218,112,.58)');
    innerGlow.addColorStop(.18, 'rgba(255,78,201,.25)');
    innerGlow.addColorStop(.28, 'rgba(92,224,255,.22)');
    innerGlow.addColorStop(1, 'rgba(255,255,255,0)');

    context.fillStyle = innerGlow;
    context.beginPath();
    context.arc(centerX, centerY, radius * (mode.haze * .36), 0, Math.PI * 2);
    context.fill();
  }

  function drawOuterField(mode, swirl) {
    for (const star of stars) {
      const angle = star.angle + swirl + star.spin * time * .4;
      const distance = Math.max(.01, star.distance);
      const curve = angle + distance * .18;

      let x = centerX + Math.cos(curve) * distance * radius * .8;
      let y = centerY + Math.sin(curve) * distance * radius * mode.eccentricity;

      y += Math.sin(time * .01 * star.jitter + distance * 12)
        * (2.5 + distance * 10) * .18;
      x += Math.cos(time * .006 * star.jitter + distance * 8)
        * (1.8 + distance * 8) * .16;

      ({ x, y } = displaceFromPointer(x, y, radius * .24, 16));

      const size = Math.max(
        .4,
        star.size * (1 + star.depth * .05) * (.7 + (1 - distance) * .75)
      );
      const alpha = Math.max(
        .05,
        star.alpha * (.35 + (1 - distance) * .85)
      );
      const hue = (star.hue + time * (.08 + distance * .22)) % 360;

      context.fillStyle = rainbow(hue, alpha);
      context.beginPath();
      context.arc(x, y, size, 0, Math.PI * 2);
      context.fill();
    }
  }

  function drawDenseCore(mode, swirl) {
    context.save();
    context.globalCompositeOperation = 'screen';

    for (const particle of coreParticles) {
      const angle = particle.angle + swirl * 1.8 + particle.orbit * time;
      let x = centerX + Math.cos(angle) * particle.distance;
      let y = centerY + Math.sin(angle) * particle.distance
        * (.94 + Math.sin(time * .003 + particle.distance) * .04);

      ({ x, y } = displaceFromPointer(x, y, radius * .18, 8));

      const pulse = 1
        + Math.sin(time * .012 + particle.distance * .08)
        * .16 * mode.pulse;
      const hue = (particle.hue + time * .22) % 360;

      context.fillStyle = rainbow(hue, particle.alpha);
      context.beginPath();
      context.arc(x, y, particle.size * pulse, 0, Math.PI * 2);
      context.fill();
    }

    const nucleusGlow = context.createRadialGradient(
      centerX, centerY, 0,
      centerX, centerY, radius * .12
    );
    nucleusGlow.addColorStop(0, 'rgba(255,255,255,.85)');
    nucleusGlow.addColorStop(.12, 'rgba(255,229,112,.42)');
    nucleusGlow.addColorStop(.28, 'rgba(255,89,199,.22)');
    nucleusGlow.addColorStop(.46, 'rgba(92,224,255,.18)');
    nucleusGlow.addColorStop(1, 'rgba(255,255,255,0)');

    context.fillStyle = nucleusGlow;
    context.beginPath();
    context.arc(centerX, centerY, radius * .14, 0, Math.PI * 2);
    context.fill();
    context.restore();
  }

  function drawGuideRings(swirl) {
    context.save();
    context.globalCompositeOperation = 'screen';
    context.strokeStyle = 'rgba(255,255,255,.05)';
    context.lineWidth = 1;

    for (let ring = .22; ring <= .76; ring += .18) {
      context.beginPath();
      context.ellipse(
        centerX,
        centerY,
        radius * ring,
        radius * ring * .62,
        swirl * 8,
        0,
        Math.PI * 2
      );
      context.stroke();
    }

    context.restore();
  }

  function render() {
    window.requestAnimationFrame(render);
    if (!visible) return;

    const mode = modes[modeIndex];
    time += reduceMotion ? 0 : 1;

    tiltX = lerp(tiltX, targetTiltX, .08);
    tiltY = lerp(tiltY, targetTiltY, .08);
    field.style.setProperty('--tilt-x', `${tiltX}deg`);
    field.style.setProperty('--tilt-y', `${tiltY}deg`);

    context.clearRect(0, 0, width, height);
    drawBackgroundGlow(mode);

    const swirl = time * mode.rotation;
    drawOuterField(mode, swirl);
    drawDenseCore(mode, swirl);
    drawGuideRings(swirl);
  }

  field.addEventListener('pointermove', (event) => {
    if (!reduceMotion) applyPointer(event.clientX, event.clientY);
  });
  field.addEventListener('pointerleave', clearPointer);

  field.addEventListener('touchstart', (event) => {
    if (event.touches.length) touchStartX = event.touches[0].clientX;
  }, { passive:true });

  field.addEventListener('touchmove', (event) => {
    if (event.touches.length && !reduceMotion) {
      applyPointer(event.touches[0].clientX, event.touches[0].clientY);
    }
  }, { passive:true });

  field.addEventListener('touchend', (event) => {
    if (touchStartX !== null) {
      const deltaX = event.changedTouches[0].clientX - touchStartX;
      if (Math.abs(deltaX) > 45) {
        setMode(modeIndex + (deltaX < 0 ? 1 : -1));
      }
    }

    touchStartX = null;
    clearPointer();
  });

  buttons.forEach((button, index) => {
    button.addEventListener('click', () => setMode(index));
  });

  field.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      setMode(modeIndex + 1);
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      setMode(modeIndex - 1);
    }
  });

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      visible = entries.some((entry) => entry.isIntersecting);
    }, { threshold:.05 });
    observer.observe(field);
  }

  window.addEventListener('resize', resize);
  resize();
  setMode(0);
  render();
})();