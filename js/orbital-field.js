(() => {
  const field = document.querySelector('[data-orbital-field]');
  if (!field) return;

  const canvas = field.querySelector('canvas');
  const context = canvas?.getContext('2d');
  if (!canvas || !context) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(pointer: fine)').matches;
  const nameNode = field.querySelector('[data-orbital-name]');
  const detailNode = field.querySelector('[data-orbital-detail]');
  const controls = [...field.querySelectorAll('[data-orbital-mode]')];

  const modes = [
    { label: 'Ψ 1S / VOID CLOUD', detail: 'ISOTROPIC · GROUND STATE' },
    { label: 'Ψ 2P / DIVIDED FIELD', detail: 'DIPOLE · PHASE REVERSAL' },
    { label: 'Ψ 3D / HERESY CLOVER', detail: 'QUADRUPOLE · OPEN SHELL' }
  ];

  const pointer = { x: 0, y: 0, targetX: 0, targetY: 0, active: false };
  let mode = 0;
  let width = 0;
  let height = 0;
  let dpr = 1;
  let particles = [];
  let pulse = 0;
  let frame = 0;
  let running = true;
  let dragStart = null;

  const random = (seed) => {
    const value = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
    return value - Math.floor(value);
  };

  const buildParticles = () => {
    const count = width < 480 ? 360 : 620;
    particles = Array.from({ length: count }, (_, index) => {
      const a = random(index + 1);
      const b = random(index + 101);
      const c = random(index + 211);
      const d = random(index + 307);
      return { a, b, c, d, phase: random(index + 401) * Math.PI * 2 };
    });
  };

  const resize = () => {
    const rect = field.getBoundingClientRect();
    width = Math.max(1, rect.width);
    height = Math.max(1, rect.height);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    buildParticles();
    draw(performance.now());
  };

  const orbitalPosition = (particle, index, time) => {
    const tau = Math.PI * 2;
    const drift = reduceMotion ? 0 : Math.sin(time * 0.00024 + particle.phase) * 0.018;
    let x = 0;
    let y = 0;
    let z = 0;

    if (mode === 0) {
      const radius = Math.pow(particle.a, 1.85) * 0.46 + drift;
      const theta = particle.b * tau;
      const phi = Math.acos(2 * particle.c - 1);
      x = radius * Math.sin(phi) * Math.cos(theta);
      y = radius * Math.sin(phi) * Math.sin(theta);
      z = radius * Math.cos(phi);
    } else if (mode === 1) {
      const side = particle.a > 0.5 ? 1 : -1;
      const longitudinal = (0.12 + Math.pow(particle.b, 0.72) * 0.34) * side;
      const spread = Math.pow(particle.c, 1.6) * (0.2 - Math.abs(longitudinal) * 0.16);
      const angle = particle.d * tau;
      x = longitudinal + drift * side;
      y = Math.cos(angle) * spread;
      z = Math.sin(angle) * spread;
    } else {
      const lobe = Math.floor(particle.a * 4);
      const angle = lobe * Math.PI / 2 + (particle.b - 0.5) * 0.5;
      const radius = 0.15 + Math.pow(particle.c, 0.74) * 0.3 + drift;
      const spread = (particle.d - 0.5) * 0.12;
      x = Math.cos(angle) * radius + Math.cos(angle + Math.PI / 2) * spread;
      y = Math.sin(angle) * radius + Math.sin(angle + Math.PI / 2) * spread;
      z = (random(index + 911) - 0.5) * 0.2;
    }

    return { x, y, z };
  };

  const rotate = (point) => {
    const yaw = pointer.x * 0.58 + mode * 0.16;
    const pitch = -pointer.y * 0.46 + 0.18;
    const cosY = Math.cos(yaw);
    const sinY = Math.sin(yaw);
    const cosX = Math.cos(pitch);
    const sinX = Math.sin(pitch);

    const x1 = point.x * cosY - point.z * sinY;
    const z1 = point.x * sinY + point.z * cosY;
    const y1 = point.y * cosX - z1 * sinX;
    const z2 = point.y * sinX + z1 * cosX;
    return { x: x1, y: y1, z: z2 };
  };

  const draw = (time = 0) => {
    context.clearRect(0, 0, width, height);
    const centerX = width / 2;
    const centerY = height / 2;
    const scale = Math.min(width, height) * (0.92 + pulse * 0.025);

    pointer.x += (pointer.targetX - pointer.x) * 0.075;
    pointer.y += (pointer.targetY - pointer.y) * 0.075;
    pulse *= 0.93;

    context.globalCompositeOperation = 'lighter';

    particles.forEach((particle, index) => {
      const rotated = rotate(orbitalPosition(particle, index, time));
      const perspective = 1 / (1.45 - rotated.z * 0.58);
      let screenX = centerX + rotated.x * scale * perspective;
      let screenY = centerY + rotated.y * scale * perspective;

      if (pointer.active && finePointer) {
        const pointerX = centerX + pointer.x * width * 0.34;
        const pointerY = centerY + pointer.y * height * 0.34;
        const deltaX = screenX - pointerX;
        const deltaY = screenY - pointerY;
        const distance = Math.hypot(deltaX, deltaY);
        const radius = Math.min(width, height) * 0.18;
        if (distance > 0 && distance < radius) {
          const force = Math.pow(1 - distance / radius, 2) * 18;
          screenX += deltaX / distance * force;
          screenY += deltaY / distance * force;
        }
      }

      const depth = Math.max(0.2, Math.min(1, (rotated.z + 0.55) / 1.1));
      const phaseWarm = mode === 1 ? particle.a > 0.5 : (mode === 2 ? Math.floor(particle.a * 4) % 2 === 0 : true);
      const alpha = 0.15 + depth * 0.65;
      const size = (0.55 + particle.d * 1.3 + depth * 0.8) * (1 + pulse * 0.4);

      context.beginPath();
      context.fillStyle = phaseWarm
        ? `rgba(255, 98, 56, ${alpha})`
        : `rgba(220, 214, 202, ${alpha * 0.72})`;
      context.arc(screenX, screenY, size, 0, Math.PI * 2);
      context.fill();
    });

    context.globalCompositeOperation = 'source-over';

    if (!reduceMotion && running) {
      frame = window.requestAnimationFrame(draw);
    }
  };

  const updateMode = (nextMode, shouldPulse = true) => {
    mode = (nextMode + modes.length) % modes.length;
    field.dataset.state = String(mode);
    nameNode.textContent = modes[mode].label;
    detailNode.textContent = modes[mode].detail;
    controls.forEach((control, index) => {
      const selected = index === mode;
      control.classList.toggle('is-active', selected);
      control.setAttribute('aria-selected', String(selected));
      control.tabIndex = selected ? 0 : -1;
    });
    if (shouldPulse) pulse = 1;
    if (reduceMotion) draw(performance.now());
  };

  const setPointer = (event) => {
    const rect = field.getBoundingClientRect();
    pointer.targetX = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    pointer.targetY = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    pointer.active = true;
    field.style.setProperty('--pointer-x', pointer.targetX.toFixed(3));
    field.style.setProperty('--pointer-y', pointer.targetY.toFixed(3));
    if (reduceMotion) {
      pointer.x = pointer.targetX;
      pointer.y = pointer.targetY;
      draw(performance.now());
    }
  };

  field.addEventListener('pointermove', setPointer);
  field.addEventListener('pointerleave', () => {
    pointer.targetX = 0;
    pointer.targetY = 0;
    pointer.active = false;
    field.style.setProperty('--pointer-x', '0');
    field.style.setProperty('--pointer-y', '0');
  });

  field.addEventListener('pointerdown', (event) => {
    dragStart = { x: event.clientX, y: event.clientY, time: performance.now() };
  });

  field.addEventListener('pointerup', (event) => {
    if (!dragStart || event.target.closest('[data-orbital-mode]')) return;
    const deltaX = event.clientX - dragStart.x;
    const deltaY = event.clientY - dragStart.y;
    const elapsed = performance.now() - dragStart.time;
    dragStart = null;

    if (Math.abs(deltaX) > 44 && Math.abs(deltaX) > Math.abs(deltaY) && elapsed < 650) {
      updateMode(mode + (deltaX < 0 ? 1 : -1));
    } else if (Math.abs(deltaX) < 8 && Math.abs(deltaY) < 8) {
      updateMode(mode + 1);
    }
  });

  field.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      updateMode(mode + 1);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      updateMode(mode - 1);
    } else if (event.key === ' ' || event.key === 'Enter') {
      event.preventDefault();
      updateMode(mode + 1);
    }
  });

  controls.forEach((control, index) => {
    control.addEventListener('click', (event) => {
      event.stopPropagation();
      updateMode(index);
    });
  });

  const visibilityObserver = 'IntersectionObserver' in window
    ? new IntersectionObserver(([entry]) => {
        running = entry.isIntersecting;
        if (running && !reduceMotion) {
          window.cancelAnimationFrame(frame);
          frame = window.requestAnimationFrame(draw);
        } else {
          window.cancelAnimationFrame(frame);
        }
      }, { threshold: 0.05 })
    : null;

  visibilityObserver?.observe(field);

  if ('ResizeObserver' in window) {
    new ResizeObserver(resize).observe(field);
  } else {
    window.addEventListener('resize', resize, { passive: true });
  }

  updateMode(0, false);
  resize();
})();
