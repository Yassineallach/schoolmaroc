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
    // tide-marks and stains
    for (let i = 0; i < 140; i++) {
      const px = r() * 960, py = r() * 540, rad = 15 + r() * 110;
      const g = x.createRadialGradient(px, py, 0, px, py, rad);
      g.addColorStop(0, `rgba(120,80,30,${0.02 + r() * 0.035})`);
      g.addColorStop(0.8, `rgba(120,80,30,${0.01 + r() * 0.02})`);
      g.addColorStop(1, 'rgba(120,80,30,0)');
      x.fillStyle = g;
      x.fillRect(px - rad, py - rad, rad * 2, rad * 2);
    }
    // foxing spots
    for (let i = 0; i < 70; i++) {
      x.fillStyle = `rgba(110,60,20,${0.05 + r() * 0.12})`;
      x.beginPath(); x.arc(r() * 960, r() * 540, 0.6 + r() * 2.2, 0, Math.PI * 2); x.fill();
    }
    // fibres and laid lines
    x.strokeStyle = 'rgba(90,60,30,0.05)';
    for (let i = 0; i < 1400; i++) {
      const px = r() * 960, py = r() * 540, a = r() * Math.PI, l = 3 + r() * 14;
      x.beginPath(); x.moveTo(px, py); x.lineTo(px + Math.cos(a) * l, py + Math.sin(a) * l); x.stroke();
    }
    x.strokeStyle = 'rgba(90,60,30,0.025)';
    for (let y = 0; y < 540; y += 4) { x.beginPath(); x.moveTo(0, y); x.lineTo(960, y + (r() - 0.5) * 2); x.stroke(); }
    return c;
  }

  /** parchment page; o.glow is ignored in this theme (kept for scene compatibility) */
  W.background = (ctx, t, o = {}) => {
    if (!paper) paper = buildPaper();
    const g = ctx.createRadialGradient(W.W * 0.5, W.H * 0.45, 100, W.W * 0.5, W.H * 0.5, W.W * 0.75);
    g.addColorStop(0, '#efe4cb');
    g.addColorStop(0.6, '#e6d7b7');
    g.addColorStop(1, '#cfb88c');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W.W, W.H);
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.drawImage(paper, 0, 0, 1920, 1080);
    ctx.restore();
  };

  /** a few specks of dust settling on the page */
  W.dust = (ctx, t, n = 40, a = 1) => {
    ctx.save();
    const m = Math.min(n, 14);
    for (let i = 0; i < m; i++) {
      const x = (W.hash(i * 3.1) * W.W + t * (4 + W.hash(i) * 6)) % W.W;
      const y = (W.hash(i * 7.7) * W.H + t * 3) % W.H;
      ctx.fillStyle = `rgba(60,40,20,${0.12 * a})`;
      ctx.beginPath(); ctx.arc(x, y, 0.8 + W.hash(i * 9.1), 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  };

  /** darkened, worn page edges */
  W.vignette = (ctx, strength = 0.75) => {
    const g = ctx.createRadialGradient(W.W / 2, W.H / 2, W.H * 0.42, W.W / 2, W.H / 2, W.W * 0.66);
    g.addColorStop(0, 'rgba(90,55,20,0)');
    g.addColorStop(1, `rgba(90,55,20,${strength * 0.55})`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W.W, W.H);
  };

  /** manuscript frame: ink rule + red rubric rule, gold corner fleurons, chapter header */
  W.frame = (ctx, t, ch, a = 1) => {
    if (a <= 0.001) return;
    ctx.save();
    ctx.globalAlpha *= a;
    const m = 34;
    ctx.strokeStyle = 'rgba(42,31,22,0.55)';
    ctx.lineWidth = 1.6;
    ctx.strokeRect(m, m, W.W - 2 * m, W.H - 2 * m);
    ctx.strokeStyle = W.rgba(W.C.crimson, 0.55);
    ctx.lineWidth = 1;
    ctx.strokeRect(m + 8, m + 8, W.W - 2 * m - 16, W.H - 2 * m - 16);
    for (const [x, y] of [[m + 4, m + 4], [W.W - m - 4, m + 4], [m + 4, W.H - m - 4], [W.W - m - 4, W.H - m - 4]]) {
      W.diamond(ctx, x, y, 9, W.C.gold);
      W.diamond(ctx, x, y, 4, W.C.crimson);
    }
    if (ch) {
      const hp = W.clamp(ch.p == null ? 1 : ch.p);
      const y = m + 36;
      W.text(ctx, ch.title, W.W - m - 50, y, { size: 26, fam: W.F.title, weight: 700, color: W.rgba(W.C.ivory, 0.75), align: 'right', alpha: hp });
      const tw = W.measure(ctx, ch.title, { size: 26, fam: W.F.title, weight: 700 });
      W.text(ctx, ch.num, W.W - m - 50 - tw - 24, y + 1, { size: 22, fam: W.F.latin, weight: 600, color: W.C.crimson, align: 'right', dir: 'ltr', alpha: hp });
      if (ch.years) W.text(ctx, ch.years, m + 50, y + 1, { size: 20, fam: W.F.latin, weight: 400, color: W.rgba(W.C.ivory, 0.6), align: 'left', dir: 'ltr', alpha: hp, tracking: 3 });
    }
    ctx.restore();
  };

  /** full-screen chapter card overlay (used at chapter openings) */
  W.chapterCard = (ctx, t, t0, dur, num, title, sub) => {
    const e = W.env(t, t0, t0 + dur, 0.5, 0.6);
    if (e <= 0) return;
    ctx.save();
    ctx.globalAlpha *= e;
    ctx.fillStyle = 'rgba(233,221,194,0.9)';
    ctx.fillRect(0, 0, W.W, W.H);
    const lp = W.p(t, t0, 1.2, W.E.inOut);
    W.hairline(ctx, W.W / 2, W.H / 2 + 6, 720, lp, W.rgba(W.C.gold, 0.6));
    W.diamond(ctx, W.W / 2, W.H / 2 + 6, 6 * lp, W.C.gold);
    W.text(ctx, num, W.W / 2, W.H / 2 - 120, { size: 30, fam: W.F.latin, weight: 600, color: W.C.crimson, dir: 'ltr', tracking: 10, alpha: W.p(t, t0 + 0.1, 0.6) });
    W.text(ctx, title, W.W / 2, W.H / 2 - 50, { size: 92, color: W.C.ivory, reveal: W.p(t, t0 + 0.2, 1.0), rise: 14 });
    if (sub) W.text(ctx, sub, W.W / 2, W.H / 2 + 60, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: W.p(t, t0 + 0.5, 0.8) });
    ctx.restore();
  };
})();
