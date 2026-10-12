/* Act 0 — cold open, the two houses, main title */
(function () {
  const { W } = window;
  const { p, E } = W;

  // particles that a symbol disintegrates into
  function ash(ctx, t, t0, cx, cy, radius, seed, color) {
    const k = t - t0;
    if (k <= 0) return;
    const r = W.rng(seed);
    for (let i = 0; i < 140; i++) {
      const a = r() * Math.PI * 2, d = Math.sqrt(r()) * radius;
      const delay = r() * 0.5, life = 1.4 + r() * 1.2;
      const q = W.clamp((k - delay) / life);
      if (q <= 0 || q >= 1) continue;
      const x = cx + Math.cos(a) * d + (W.noise(i + k, seed) - 0.5) * 80 * q + q * 60 * (r() - 0.3);
      const y = cy + Math.sin(a) * d - q * (90 + r() * 140);
      ctx.fillStyle = W.rgba(color, (1 - q) * 0.8);
      ctx.fillRect(x, y, 2 + r() * 2, 2 + r() * 2);
    }
  }

  // ---------------------------------------------------------------- opening_myth
  W.scene('opening_myth', {
    bg: (t) => ({ glow: '#1f262b', glowA: 0.6 }),
    draw(ctx, t, S) {
      const c = S.cues;
      // faint England outline: the stage on which the myth is refuted
      const view = { lon: -2.4, lat: 53.6, k: 135 };
      W.drawMap(ctx, t, view, { reveal: p(t, 0.2, 3.4, E.inOut), alpha: 0.5 * (1 - p(t, c.strike, 1.2)), borders: false });
      W.text(ctx, 'إنجلترا · العصور الوسطى', W.W / 2, 950, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, reveal: p(t, 2.1, 1.2), alpha: p(t, 2.1, 1) * (1 - p(t, c.crystal - 0.3, 0.6)) });

      const fade = 1 - p(t, c.ash, 0.9);
      // ice creature
      const cx = 1330, cy = 470;
      W.alpha(ctx, fade, () => {
        W.crystal(ctx, cx, cy, 175, { p: p(t, c.crystal, 1.6, E.inOut), color: '#cfe0e8', width: 2.2, glow: 'rgba(170,210,230,0.6)', rot: t * 0.04 });
        W.text(ctx, S.text.a, cx, cy + 260, { size: 58, color: '#dbe7ec', reveal: p(t, c.crystal + 0.15, 0.9), rise: 12 });
      });
      // dragon
      const dx = 600, dy = 470;
      W.alpha(ctx, fade, () => {
        W.wing(ctx, dx, dy - 10, 210, { p: p(t, c.wing - 0.2, 1.3, E.inOut), color: W.C.ivory, width: 2.2, fill: 0.06 * p(t, c.wing + 0.6, 0.6) });
        W.text(ctx, S.text.b, dx, dy + 260, { size: 58, color: W.C.ivory, reveal: p(t, c.wing + 0.1, 0.8), rise: 12 });
      });
      // the refutation: crimson strike through both
      W.alpha(ctx, fade, () => {
        const sp = p(t, c.strike, 0.45, E.out);
        const sp2 = p(t, c.strike + 0.12, 0.45, E.out);
        const wa = W.measure(ctx, S.text.a, { size: 58 }) + 40, wb = W.measure(ctx, S.text.b, { size: 58 }) + 40;
        W.strike(ctx, cx, cy + 262, wa, sp, W.C.crimsonBright, 5);
        W.strike(ctx, dx, dy + 262, wb, sp2, W.C.crimsonBright, 5);
      });
      ash(ctx, t, c.ash, cx, cy, 170, 11, '#cfe0e8');
      ash(ctx, t, c.ash + 0.1, dx, dy, 190, 12, W.C.ivory);
    },
  });

  // ---------------------------------------------------------------- two_houses
  // procedural lineage strands for each house
  function lineage(x0, y0, side, seed) {
    const r = W.rng(seed), segs = [], leaves = [];
    const grow = (x, y, lvl, spread) => {
      if (lvl > 4) { leaves.push([x, y]); return; }
      const n = lvl === 0 ? 2 : 2;
      for (let i = 0; i < n; i++) {
        const nx = x + (i - (n - 1) / 2) * spread * 2 + (r() - 0.5) * 30;
        const ny = y + 60 + r() * 10;
        segs.push({ a: [x, y], b: [nx, ny], lvl });
        grow(nx, ny, lvl + 1, spread * 0.52);
      }
    };
    grow(x0, y0, 0, 200);
    return { segs, leaves };
  }
  const LIN = { lan: lineage(1440, 560, 1, 7), york: lineage(480, 560, -1, 9) };

  W.scene('two_houses', {
    bg: () => ({ glow: '#2b1a17', glowA: 0.6 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const sp = p(t, c.split - 0.3, 1.4, E.inOut);
      // halves: crimson (right, Lancaster) and ivory (left, York)
      ctx.save();
      const gR = ctx.createLinearGradient(W.W / 2, 0, W.W, 0);
      gR.addColorStop(0, W.rgba(W.C.crimson, 0.0)); gR.addColorStop(0.35, W.rgba(W.C.crimson, 0.16 * sp)); gR.addColorStop(1, W.rgba(W.C.crimsonDeep, 0.25 * sp));
      ctx.fillStyle = gR; ctx.fillRect(W.W / 2, 0, W.W / 2, W.H);
      const gL = ctx.createLinearGradient(W.W / 2, 0, 0, 0);
      gL.addColorStop(0, W.rgba(W.C.ivory, 0.0)); gL.addColorStop(0.35, W.rgba(W.C.ivory, 0.06 * sp)); gL.addColorStop(1, W.rgba(W.C.ivory, 0.09 * sp));
      ctx.fillStyle = gL; ctx.fillRect(0, 0, W.W / 2, W.H);
      ctx.restore();
      // blade of light
      const bp = p(t, c.split - 0.4, 1.1, E.outExpo);
      ctx.save();
      ctx.strokeStyle = W.rgba(W.C.ivory, 0.75);
      ctx.shadowColor = 'rgba(255,240,215,0.9)'; ctx.shadowBlur = 22;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(W.W / 2, 0); ctx.lineTo(W.W / 2, W.H * bp); ctx.stroke();
      ctx.restore();

      // roses
      const rb = p(t, c.split, 1.8, E.out), yb = p(t, c.split + 0.3, 1.8, E.out);
      W.rose(ctx, 1440, 330, 120, { kind: 'lancaster', bloom: rb, spin: t * 0.02 });
      W.rose(ctx, 480, 330, 120, { kind: 'york', bloom: yb, spin: -t * 0.02 });
      W.text(ctx, T.lan, 1440, 495, { size: 52, color: W.C.crimsonBright, reveal: p(t, c.families, 0.9), rise: 10 });
      W.text(ctx, T.york, 480, 495, { size: 52, color: W.C.ivory, reveal: p(t, c.families + 0.6, 0.9), rise: 10 });

      // lineage strands through the generations
      for (const [key, col] of [['lan', W.C.crimsonBright], ['york', W.C.ivory]]) {
        const L = LIN[key];
        for (const s of L.segs) {
          const q = p(t, c.generations + s.lvl * 0.42, 0.6, E.inOut);
          W.strokePoly(ctx, [s.a, s.b], q, { color: W.rgba(col, 0.38 - s.lvl * 0.04), width: 1.6 - s.lvl * 0.2 });
        }
      }
      // many characters with shifting loyalties
      const all = [...LIN.lan.leaves.map((q) => [q, 0]), ...LIN.york.leaves.map((q) => [q, 1])];
      all.forEach(([pt, side], i) => {
        const q = p(t, c.people + (i % 16) * 0.05 + side * 0.08, 0.5, E.outBack);
        if (q <= 0) return;
        const fickle = W.hash(i * 4.7) > 0.55;
        const fp = fickle ? p(t, c.allegiance + W.hash(i) * 0.8, 1.6, E.inOut) : 0;
        const sw = fickle ? 0.5 + 0.5 * Math.sin((t - c.allegiance) * (2 + W.hash(i * 2) * 2) + i) : 0;
        const k = side === 0 ? sw * fp : 1 - sw * fp;
        const col = W.mixColor(W.C.crimsonBright, W.C.ivory, k);
        const drift = fickle ? (side === 0 ? -1 : 1) * fp * 60 * Math.sin(t * 0.7 + i) : 0;
        W.node(ctx, pt[0] + drift, pt[1], 7, { p: q, color: col, width: 1.6 });
      });
      // headline
      const out = 1 - p(t, c.generations + 1.8, 0.8);
      W.words(ctx, T.a, W.W / 2, 980, t, [8.56, 9.06, 9.84, 9.98], { size: 60, color: W.C.ivory, alpha: out });
      W.words(ctx, T.c, W.W / 2, 980, t, [c.allegiance, c.allegiance + 0.5], { size: 60, color: W.C.ivory, alpha: 1 - p(t, S.end - 0.7, 0.6) });
    },
  });

  // ---------------------------------------------------------------- title
  W.scene('title', {
    bg: () => ({ glow: '#3a2a1b', glowA: 0.55, ly: 0.45 }),
    dust: 40,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const cx = W.W / 2;
      // crossed swords watermark
      W.alpha(ctx, 0.14, () => W.crossedSwords(ctx, cx, 560, 330, { p: p(t, 21.6, 2.4, E.inOut), color: W.C.ivory, width: 2 }));
      // crown
      W.crown(ctx, cx, 330, 64, { p: p(t, 20.2, 2.0, E.inOut), color: W.C.gold, width: 2.4, fill: 0.15 * p(t, 22, 1), glow: 'rgba(201,164,92,0.35)' });
      // roses converge to flank the title
      const rp = p(t, 19.6, 4.6, E.inOut);
      W.rose(ctx, W.lerp(1500, 1550, rp), 560, W.lerp(60, 78, rp), { kind: 'lancaster', bloom: p(t, 19.8, 2), spin: t * 0.03 });
      W.rose(ctx, W.lerp(420, 370, rp), 560, W.lerp(60, 78, rp), { kind: 'york', bloom: p(t, 20.3, 2), spin: -t * 0.03 });
      // title
      const tp = p(t, c.title - 0.1, 1.5, E.out);
      W.text(ctx, T.title, cx, 545, { size: 168, color: W.C.ivory, reveal: tp, rise: 16, glow: 'rgba(255,235,205,0.18)', glowBlur: 30 });
      const lp = p(t, c.title + 0.4, 1.4, E.inOut);
      W.hairline(ctx, cx - 250, 668, 380, lp, W.rgba(W.C.gold, 0.6));
      W.hairline(ctx, cx + 250, 668, 380, lp, W.rgba(W.C.gold, 0.6));
      W.diamond(ctx, cx, 668, 7 * lp, W.C.gold);
      W.text(ctx, T.latin, cx, 724, { size: 34, fam: W.F.latin, weight: 400, color: W.rgba(W.C.ivory, 0.75), dir: 'ltr', tracking: 12, alpha: p(t, c.title + 0.8, 1) });
      W.text(ctx, T.years, cx, 776, { size: 26, fam: W.F.latin, weight: 400, color: W.C.gold, dir: 'ltr', tracking: 6, alpha: p(t, c.title + 1.1, 1) });
      // reference note
      W.text(ctx, T.note, cx, 930, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, reveal: p(t, c.drama, 1.0), alpha: 1 - p(t, S.end - 0.9, 0.7) });
    },
  });
})();
