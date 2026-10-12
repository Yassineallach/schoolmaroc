/* Act 0 — cold open in an "ice & fire" style: the frost creature and the dragon that never came,
   the two great houses under their banners, and a clockwork-map title homage. */
(function () {
  const { W } = window;
  const { p, E } = W;

  // ---------------------------------------------------------------- opening_myth
  W.scene('opening_myth', {
    bg: () => ({ glow: '#1b2a36', glowA: 0.0 }),
    dust: 0,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const fire = p(t, 5.8, 1.0, E.inOut);
      // cold light, then fire light
      const gl = ctx.createRadialGradient(960, 420, 0, 960, 420, 1100);
      gl.addColorStop(0, `rgba(40,80,110,${0.55 * (1 - fire)})`); gl.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = gl; ctx.fillRect(0, 0, W.W, W.H);
      const gf = ctx.createRadialGradient(1300, 250, 0, 1300, 250, 1300);
      gf.addColorStop(0, `rgba(255,110,30,${0.42 * fire})`); gf.addColorStop(0.5, `rgba(120,30,10,${0.25 * fire})`); gf.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = gf; ctx.fillRect(0, 0, W.W, W.H);

      // medieval England, faint, beneath the frost
      W.drawMap(ctx, t, { lon: -2.4, lat: 53.4, k: 135 }, { reveal: p(t, 0.2, 3.2, E.inOut), alpha: 0.38 * (1 - p(t, 3.0, 1.5)), borders: false });
      W.text(ctx, 'إنجلترا · العصور الوسطى', W.W / 2, 965, { size: 30, fam: W.F.label, weight: 400, color: 'rgba(200,230,250,0.7)', reveal: p(t, 1.4, 1.2), alpha: 1 - p(t, 3.4, 0.5) });

      // frost creeps in, then melts in the dragon fire
      W.frost(ctx, p(t, 0.2, 5.4, E.inOut), 1 - p(t, 6.1, 1.1));
      // the frost creature: eyes ignite on "كائنات جليدية"
      W.frostCreature(ctx, 960, 470, 0.95, t, { alpha: p(t, 2.4, 1.6, E.inOut) * (1 - p(t, 6.2, 0.9)), eyes: p(t, c.crystal, 0.5) * (1 - p(t, 6.0, 0.8)) });

      // the dragon sweeps in breathing fire
      const fp = p(t, 5.55, 1.5, E.inOut);
      if (fp > 0) {
        const dx = W.lerp(-520, 1260, fp), dy = W.lerp(260, 330, fp) + Math.sin(t * 4) * 10;
        // fire-lit sky behind the silhouette
        const sky = ctx.createRadialGradient(dx - 60, dy - 120, 0, dx - 60, dy - 120, 520);
        sky.addColorStop(0, `rgba(255,150,60,${0.55 * p(t, 5.7, 0.6)})`); sky.addColorStop(1, 'rgba(255,90,20,0)');
        ctx.fillStyle = sky; ctx.fillRect(0, 0, W.W, W.H);
        const m = W.dragon(ctx, dx, dy + 60, 0.95, t, { flap: Math.sin(t * 6.5), tilt: 0.1 });
        W.fireBreath(ctx, m, 0.5, 700, t, p(t, 6.0, 0.4) * (1 - p(t, 7.2, 0.3)));
      }
      W.embers(ctx, t, 90, p(t, 5.9, 0.8));

      // "no ice creatures ... and no dragons"
      const ty = 975;
      W.text(ctx, T.a, 1250, ty, { size: 60, color: '#dff3ff', reveal: p(t, c.crystal + 0.1, 0.8), rise: 10, glow: 'rgba(120,200,255,0.6)', glowBlur: 18 });
      W.text(ctx, T.b, 660, ty, { size: 60, color: '#ffe2c4', reveal: p(t, c.wing + 0.05, 0.7), rise: 10, glow: 'rgba(255,140,60,0.6)', glowBlur: 18 });
      const wa = W.measure(ctx, T.a, { size: 60 }) + 40, wb = W.measure(ctx, T.b, { size: 60 }) + 40;
      W.strike(ctx, 1250, ty + 2, wa, p(t, c.strike, 0.4), W.C.crimsonBright, 5);
      W.strike(ctx, 660, ty + 2, wb, p(t, c.strike + 0.12, 0.4), W.C.crimsonBright, 5);
    },
  });

  // ---------------------------------------------------------------- two_houses
  const FIG = Array.from({ length: 28 }, (_, i) => {
    const x = 170 + (i / 27) * 1580 + (W.hash(i * 3.3) - 0.5) * 30;
    return { x, side: x > 960 ? 0 : 1, fickle: W.hash(i * 4.7) > 0.5, h: 0.85 + W.hash(i * 1.9) * 0.3 };
  });
  function figure(ctx, x, y, s, col) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = '#0b0908';
    ctx.beginPath(); ctx.arc(0, -46, 10, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-9, -34); ctx.lineTo(9, -34); ctx.lineTo(20, 0); ctx.lineTo(-20, 0); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.shadowColor = col; ctx.shadowBlur = 10;
    ctx.beginPath(); ctx.arc(0, -46, 10, 0, Math.PI * 2); ctx.moveTo(-9, -34); ctx.lineTo(-20, 0); ctx.moveTo(9, -34); ctx.lineTo(20, 0); ctx.stroke();
    ctx.restore();
  }

  W.scene('two_houses', {
    bg: () => ({ glow: '#3a1e12', glowA: 0.55 }),
    dust: 0,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      W.embers(ctx, t, 60, 0.55);
      // the sword planted between the houses
      W.alpha(ctx, p(t, 7.6, 1.2), () => W.longsword(ctx, 960, 560, 1.0, t));
      // great banners unfurl
      W.houseBanner(ctx, 1440, 80, 360, 600, t, { color: W.C.crimson, sigil: 'lancaster', drop: p(t, c.split, 1.6), phase: 0 });
      W.houseBanner(ctx, 480, 80, 360, 600, t, { color: '#cfc3a6', sigil: 'york', drop: p(t, c.split + 0.35, 1.6), phase: 1.7 });
      W.text(ctx, T.lan, 1440, 815, { size: 60, color: W.C.crimsonBright, reveal: p(t, c.families, 0.9), rise: 10, glow: 'rgba(0,0,0,0.9)', glowBlur: 12 });
      W.text(ctx, T.york, 480, 815, { size: 60, color: W.C.ivory, reveal: p(t, c.families + 0.6, 0.9), rise: 10, glow: 'rgba(0,0,0,0.9)', glowBlur: 12 });
      // a crowd of players with shifting loyalties
      FIG.forEach((f, i) => {
        const q = p(t, c.people + (i % 14) * 0.06, 0.6, E.out);
        if (q <= 0) return;
        const fp = f.fickle ? p(t, c.allegiance + W.hash(i) * 0.8, 1.4, E.inOut) : 0;
        const sw = f.fickle ? 0.5 + 0.5 * Math.sin((t - c.allegiance) * (2 + W.hash(i * 2) * 2) + i) : 0;
        const k = f.side === 0 ? sw * fp : 1 - sw * fp;
        const col = W.mixColor(W.C.crimsonBright, W.C.ivory, k);
        W.alpha(ctx, q, () => figure(ctx, f.x + (f.fickle ? Math.sin(t * 0.8 + i) * 30 * fp : 0), 960 + (1 - q) * 20, f.h, col));
      });
      // headline at the top, between the banners
      const out = 1 - p(t, c.allegiance - 0.6, 0.5);
      W.words(ctx, T.a, W.W / 2, 150, t, [8.56, 9.06, 9.84, 9.98], { size: 52, color: W.C.ivory, alpha: out });
      W.words(ctx, T.c, W.W / 2, 150, t, [c.allegiance, c.allegiance + 0.5], { size: 52, color: W.C.ivory, alpha: 1 - p(t, S.end - 0.7, 0.6) });
    },
  });

  // ---------------------------------------------------------------- title (clockwork-map homage)
  W.scene('title', {
    bg: () => ({ glow: '#2e2214', glowA: 0.5, ly: 0.3 }),
    dust: 0,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const k = p(t, S.start, S.end - S.start, E.inOutSine);
      const dim = 1 - p(t, c.title - 0.4, 1.2) * 0.62;
      const cam = { lon: -1.6, lat: W.lerp(52.0, 53.0, k), k: 300, dist: W.lerp(1450, 1250, k), height: 650, horizon: 120, panX: W.lerp(120, -60, k) };
      W.alpha(ctx, p(t, S.start, 1.2) * dim, () => {
        const pr = W.bronzeMap(ctx, t, cam);
        W.risingTower(ctx, pr(W.PLACES.york.ll), t, p(t, 20.1, 1.6), { flag: '#e9e0cb', size: 150 });
        W.risingTower(ctx, pr(W.PLACES.lancaster.ll), t, p(t, 20.7, 1.6), { flag: W.C.crimsonBright, size: 150, dir: -1 });
        W.risingTower(ctx, pr(W.PLACES.london.ll), t, p(t, 21.4, 1.6), { flag: W.C.gold, size: 130 });
      });
      // frame of turning gears
      for (const [x, y, r, n, d] of [[110, 1000, 180, 22, 1], [330, 1060, 110, 14, -1.6], [1810, 1010, 200, 24, -1], [1600, 1070, 105, 13, 1.9], [40, 620, 90, 12, -2]]) {
        W.gear(ctx, x, y, r, n, t * 0.25 * d, { alpha: p(t, S.start + 0.3, 1.2) });
      }
      W.astrolabe(ctx, 960, 190, 160, t, { alpha: p(t, 19.6, 1.4) * (1 - p(t, 26.8, 0.8)) });
      // metal title
      const up = p(t, 27.0, 1.4, E.inOut);
      const ta = p(t, c.title - 0.1, 1.2);
      W.metalText(ctx, T.title, W.W / 2, W.lerp(470, 235, up) + (1 - ta) * 30, { size: W.lerp(176, 118, up), alpha: ta, glint: W.clamp((t - (c.title + 0.4)) / 1.8) });
      W.metalText(ctx, T.latin, W.W / 2, 615, { size: 44, fam: W.F.latin, weight: 600, tracking: 14, alpha: p(t, c.title + 0.8, 1) * (1 - up) });
      W.text(ctx, T.years, W.W / 2, 672, { size: 26, fam: W.F.latin, weight: 400, color: W.BRONZE.light, dir: 'ltr', tracking: 8, alpha: p(t, c.title + 1.1, 1) * (1 - up) });
      // the drama it inspired: a throne of swords
      W.swordThrone(ctx, W.W / 2, 870, 0.82, t, p(t, 27.2, 1.6, E.out));
      W.text(ctx, T.note, W.W / 2, 958, { size: 34, fam: W.F.label, weight: 500, color: W.BRONZE.hi, reveal: p(t, c.got - 0.2, 1.0), alpha: 1 - p(t, S.end - 0.6, 0.5) });
      W.embers(ctx, t, 30, 0.5 * p(t, 27, 1));
    },
  });
})();
