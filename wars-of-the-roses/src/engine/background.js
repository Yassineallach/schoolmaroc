/* Persistent atmosphere: warm ink background, slow light, paper texture, dust, vignette,
   and the editorial frame (chapter header). Grain is added at encode time by FFmpeg. */
(function () {
  const { W } = window;
  let paper = null;

  function buildPaper() {
    const c = document.createElement('canvas');
    c.width = 960; c.height = 540;
    const x = c.getContext('2d');
    const r = W.rng(1455);
    // soft blotches
    for (let i = 0; i < 260; i++) {
      const px = r() * 960, py = r() * 540, rad = 20 + r() * 120;
      const g = x.createRadialGradient(px, py, 0, px, py, rad);
      const v = r() > 0.5 ? 255 : 0;
      g.addColorStop(0, `rgba(${v},${v * 0.92},${v * 0.8},${0.018 + r() * 0.02})`);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = g;
      x.fillRect(px - rad, py - rad, rad * 2, rad * 2);
    }
    // fibres
    x.strokeStyle = 'rgba(239,230,210,0.025)';
    for (let i = 0; i < 900; i++) {
      const px = r() * 960, py = r() * 540, a = r() * Math.PI, l = 4 + r() * 18;
      x.beginPath(); x.moveTo(px, py); x.lineTo(px + Math.cos(a) * l, py + Math.sin(a) * l); x.stroke();
    }
    return c;
  }

  /** o.glow: colour of the key light, o.lx/o.ly light position (0..1), o.dust density */
  W.background = (ctx, t, o = {}) => {
    if (!paper) paper = buildPaper();
    ctx.fillStyle = W.C.bg;
    ctx.fillRect(0, 0, W.W, W.H);
    // key light drifting slowly
    const lx = (o.lx == null ? 0.5 : o.lx) * W.W + Math.sin(t * 0.05) * 120;
    const ly = (o.ly == null ? 0.42 : o.ly) * W.H + Math.cos(t * 0.04) * 60;
    const g = ctx.createRadialGradient(lx, ly, 0, lx, ly, 1250);
    g.addColorStop(0, W.rgba(o.glow || '#3a2c1e', o.glowA == null ? 0.55 : o.glowA));
    g.addColorStop(0.55, W.rgba(o.glow || '#3a2c1e', 0.12));
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W.W, W.H);
    // paper texture with very slow drift
    ctx.save();
    ctx.globalAlpha = 0.9;
    ctx.globalCompositeOperation = 'screen';
    const dx = (t * 3) % 960;
    ctx.drawImage(paper, -dx * 2, 0, 1920, 1080);
    ctx.drawImage(paper, 1920 - dx * 2, 0, 1920, 1080);
    ctx.restore();
  };

  W.dust = (ctx, t, n = 40, a = 1) => {
    ctx.save();
    for (let i = 0; i < n; i++) {
      const sx = W.hash(i * 3.1) * W.W, sy = W.hash(i * 7.7) * W.H;
      const sp = 6 + W.hash(i * 1.3) * 14;
      const x = (sx + t * sp + Math.sin(t * 0.3 + i) * 30) % (W.W + 40) - 20;
      const y = (sy - t * sp * 0.35 + W.H * 4) % (W.H + 40) - 20;
      const tw = 0.5 + 0.5 * Math.sin(t * (0.6 + W.hash(i) * 0.8) + i);
      ctx.fillStyle = `rgba(239,225,195,${(0.05 + 0.18 * tw) * a})`;
      ctx.beginPath();
      ctx.arc(x, y, 0.8 + W.hash(i * 9.1) * 1.6, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  };

  W.vignette = (ctx, strength = 0.75) => {
    const g = ctx.createRadialGradient(W.W / 2, W.H / 2, W.H * 0.35, W.W / 2, W.H / 2, W.W * 0.72);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, `rgba(0,0,0,${strength})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W.W, W.H);
  };

  /** editorial frame: thin margins, chapter numeral + title (top right), years (top left) */
  W.frame = (ctx, t, ch, a = 1) => {
    if (a <= 0.001) return;
    ctx.save();
    ctx.globalAlpha *= a;
    const m = 56;
    ctx.strokeStyle = 'rgba(239,230,210,0.14)';
    ctx.lineWidth = 1;
    // corner ticks
    const tk = 26;
    for (const [x, y, sx, sy] of [[m, m, 1, 1], [W.W - m, m, -1, 1], [m, W.H - m, 1, -1], [W.W - m, W.H - m, -1, -1]]) {
      ctx.beginPath(); ctx.moveTo(x, y + sy * tk); ctx.lineTo(x, y); ctx.lineTo(x + sx * tk, y); ctx.stroke();
    }
    if (ch) {
      const hp = W.clamp(ch.p == null ? 1 : ch.p);
      W.text(ctx, ch.title, W.W - m - 40, m + 8, { size: 26, fam: W.F.label, weight: 500, color: W.rgba(W.C.ivory, 0.6), align: 'right', alpha: hp });
      const tw = W.measure(ctx, ch.title, { size: 26, fam: W.F.label, weight: 500 });
      W.text(ctx, ch.num, W.W - m - 40 - tw - 26, m + 9, { size: 22, fam: W.F.latin, weight: 600, color: W.rgba(W.C.gold, 0.8), align: 'right', dir: 'ltr', alpha: hp });
      if (ch.years) W.text(ctx, ch.years, m + 40, m + 9, { size: 20, fam: W.F.latin, weight: 400, color: W.rgba(W.C.ivory, 0.45), align: 'left', dir: 'ltr', alpha: hp, tracking: 3 });
      ctx.strokeStyle = `rgba(239,230,210,${0.12 * hp})`;
      ctx.beginPath(); ctx.moveTo(m + 40, m + 34); ctx.lineTo(W.W - m - 40, m + 34); ctx.stroke();
    }
    ctx.restore();
  };

  /** full-screen chapter card overlay (used at chapter openings) */
  W.chapterCard = (ctx, t, t0, dur, num, title, sub) => {
    const e = W.env(t, t0, t0 + dur, 0.5, 0.6);
    if (e <= 0) return;
    ctx.save();
    ctx.globalAlpha *= e;
    ctx.fillStyle = 'rgba(8,7,6,0.55)';
    ctx.fillRect(0, 0, W.W, W.H);
    const lp = W.p(t, t0, 1.2, W.E.inOut);
    W.hairline(ctx, W.W / 2, W.H / 2 + 6, 720, lp, W.rgba(W.C.gold, 0.6));
    W.diamond(ctx, W.W / 2, W.H / 2 + 6, 6 * lp, W.C.gold);
    W.text(ctx, num, W.W / 2, W.H / 2 - 120, { size: 30, fam: W.F.latin, weight: 600, color: W.C.gold, dir: 'ltr', tracking: 10, alpha: W.p(t, t0 + 0.1, 0.6) });
    W.text(ctx, title, W.W / 2, W.H / 2 - 50, { size: 92, color: W.C.ivory, reveal: W.p(t, t0 + 0.2, 1.0), rise: 14 });
    if (sub) W.text(ctx, sub, W.W / 2, W.H / 2 + 60, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: W.p(t, t0 + 0.5, 0.8) });
    ctx.restore();
  };
})();
