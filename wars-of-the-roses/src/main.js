/* Scene registry + compositor. window.renderFrame(t) draws one frame for time t (seconds).
   Scene timing, cues and on-screen text come from data/scenes.json. */
(function () {
  const { W } = window;
  const registry = {};
  /** register a scene implementation: draw(ctx, t, S) where S is the scenes.json entry */
  W.scene = (id, impl) => { registry[id] = typeof impl === 'function' ? { draw: impl } : impl; };

  let DATA = null, canvas = null, ctx = null;

  W.chapterAt = (t) => DATA.chapters.find((c) => t >= c.start && t < c.end) || null;

  function camera(ctx, t, S) {
    const cam = S.camera || {};
    const p = W.E.inOutSine(W.clamp((t - S.start) / Math.max(0.01, S.end - S.start)));
    const z = cam.z ? W.lerp(cam.z[0], cam.z[1], p) : 1;
    const x = cam.x ? W.lerp(cam.x[0], cam.x[1], p) : 0;
    const y = cam.y ? W.lerp(cam.y[0], cam.y[1], p) : 0;
    ctx.translate(W.W / 2 + x, W.H / 2 + y);
    ctx.scale(z, z);
    ctx.translate(-W.W / 2, -W.H / 2);
  }

  window.renderFrame = (t) => {
    const scenes = DATA.scenes;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
    ctx.filter = 'none';

    // current scene + atmosphere
    let i = scenes.findIndex((s) => t >= s.start && t < s.end);
    if (i < 0) i = t < scenes[0].start ? 0 : scenes.length - 1;
    const S = scenes[i];
    const impl = registry[S.id] || {};
    W.background(ctx, t, impl.bg ? impl.bg(t, S) : {});

    const drawScene = (k, alpha) => {
      const s = scenes[k], r = registry[s.id];
      if (!r || alpha <= 0.001) return;
      ctx.save();
      ctx.globalAlpha = alpha;
      camera(ctx, t, s);
      r.draw(ctx, t, s);
      ctx.restore();
    };

    // transitions: the incoming scene owns the transition (type + dur)
    const tr = S.transition || { type: 'cut', dur: 0 };
    const pin = tr.dur > 0 ? W.E.inOutSine(W.clamp((t - S.start) / tr.dur)) : 1;
    if (i > 0 && pin < 1 && tr.type !== 'cut' && tr.type !== 'fade-from-black') {
      drawScene(i - 1, tr.type === 'match' ? 1 - W.E.inQuad(pin) : 1 - pin);
    }
    drawScene(i, tr.type === 'cut' ? 1 : pin);

    // editorial frame + chapter header
    const ch = W.chapterAt(t);
    const frameA = t < 1.2 ? W.p(t, 0.2, 1) : 1;
    W.frame(ctx, t, ch ? { ...ch, p: W.p(t, ch.start + 0.4, 1.0) * (1 - W.p(t, ch.end - 0.5, 0.5)) } : null, frameA * (S.id === 'endcard' ? 1 - W.p(t, S.start, 1) : 1));
    // chapter cards (when a scene declares a "card" cue on its chapter's first scene)
    if (ch && S.cues && S.cues.card != null && S.chapter === ch.id) {
      W.chapterCard(ctx, t, S.cues.card, 2.1, `— ${ch.num} —`, ch.title, ch.years);
    }
    W.dust(ctx, t, impl.dust == null ? 26 : impl.dust, 0.8);
    W.vignette(ctx, 0.78);

    // global fades
    const fin = W.p(t, 0, 0.9, W.E.inOutSine);
    const fout = 1 - W.p(t, DATA.meta.duration - 1.0, 1.0, W.E.inOutSine);
    const black = 1 - Math.min(fin, fout);
    if (black > 0) { ctx.fillStyle = `rgba(0,0,0,${black})`; ctx.fillRect(0, 0, W.W, W.H); }
  };

  async function loadFonts() {
    const specs = [
      [`700 64px "${W.F.title}"`, 'حروب الوردتين 1455'],
      [`400 64px "${W.F.title}"`, 'حروب الوردتين'],
      [`400 32px "${W.F.label}"`, 'لانكاستر يورك'],
      [`500 32px "${W.F.label}"`, 'لانكاستر يورك'],
      [`700 32px "${W.F.label}"`, 'لانكاستر'],
      [`600 64px "${W.F.latin}"`, '1455 THE WARS'],
      [`400 64px "${W.F.latin}"`, '1455 THE WARS'],
    ];
    await Promise.all(specs.map(([f, s]) => document.fonts.load(f, s)));
    await document.fonts.ready;
  }

  W.boot = async () => {
    canvas = document.getElementById('c');
    ctx = canvas.getContext('2d');
    const res = await fetch('../data/scenes.json');
    DATA = await res.json();
    W.DATA = DATA;
    await loadFonts();
    const missing = DATA.scenes.filter((s) => !registry[s.id]).map((s) => s.id);
    if (missing.length) console.warn('scenes without implementation:', missing.join(', '));
    window.__ready = true;
    const params = new URLSearchParams(location.search);
    if (params.has('dev')) devPlayer(params);
    else if (params.has('thumb')) W.drawThumbnail(ctx);
    else if (params.has('t')) window.renderFrame(parseFloat(params.get('t')));
  };

  // ---- dev player: plays narration and renders in real time ------------------------
  function devPlayer(params) {
    document.body.classList.add('dev');
    const audio = new Audio('../input/narration_main.wav');
    const bar = document.getElementById('bar');
    const lab = document.getElementById('lab');
    bar.max = DATA.meta.duration;
    let t = parseFloat(params.get('t') || '0');
    audio.currentTime = t;
    bar.oninput = () => { t = parseFloat(bar.value); audio.currentTime = Math.min(t, audio.duration || t); };
    document.getElementById('play').onclick = () => (audio.paused ? audio.play() : audio.pause());
    window.addEventListener('keydown', (e) => {
      if (e.code === 'Space') { e.preventDefault(); audio.paused ? audio.play() : audio.pause(); }
      if (e.code === 'ArrowRight') audio.currentTime += 2;
      if (e.code === 'ArrowLeft') audio.currentTime -= 2;
    });
    const loop = () => {
      if (!audio.paused) t = audio.currentTime;
      bar.value = t;
      const s = DATA.scenes.find((x) => t >= x.start && t < x.end);
      lab.textContent = `${t.toFixed(2)}s  ${s ? s.id : ''}`;
      window.renderFrame(t);
      requestAnimationFrame(loop);
    };
    loop();
  }
})();
