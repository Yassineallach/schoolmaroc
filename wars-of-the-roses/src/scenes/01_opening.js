/* Act 0 — the opening as a manuscript page: an engraved map of England whose margins hold
   bestiary drawings of a frost creature and a dragon (crossed out in red ink), the two houses
   under their banners, and an illuminated title page. */
(function () {
  const { W } = window;
  const { p, E } = W;

  /** reveal a drawing as if inked from top to bottom */
  function inked(ctx, cx, cy, w, h, q, fn) {
    if (q <= 0) return;
    ctx.save();
    ctx.beginPath();
    ctx.rect(cx - w / 2, cy - h / 2, w, h * W.E.inOut(q));
    ctx.clip();
    fn();
    ctx.restore();
  }
  /** a hand-drawn red ink cross */
  function redCross(ctx, cx, cy, r, q) {
    const a = [[cx - r, cy - r * 0.9], [cx + r, cy + r * 0.9]], b = [[cx + r, cy - r * 0.9], [cx - r, cy + r * 0.9]];
    W.strokePoly(ctx, a, p(q, 0, 0.5), { color: W.rgba(W.C.crimson, 0.85), width: 7 });
    W.strokePoly(ctx, b, p(q, 0.4, 0.5), { color: W.rgba(W.C.crimson, 0.85), width: 7 });
  }

  // ---------------------------------------------------------------- opening_myth
  W.scene('opening_myth', {
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const view = { lon: -2.2, lat: 53.6, k: 132 };
      W.drawMap(ctx, t, view, { reveal: p(t, 0.2, 3.4, E.inOut), borders: true, regionLabels: true });
      W.text(ctx, 'إنجلترا في العصور الوسطى', W.W / 2, 985, { size: 38, color: W.C.crimson, reveal: p(t, 1.2, 1.2) });
      // bestiary drawings in the margins of the map
      const fx = 1545, fy = 400, dx = 430, dy = 430;
      // the Night King: real ink drawing (falls back to the engraved version if missing)
      const nk = p(t, c.crystal - 0.4, 1.4);
      if (!W.image(ctx, 'night_king', fx, fy + 30, 560, { reveal: nk, zoom: 1 + 0.04 * p(t, c.crystal, 4) }))
        inked(ctx, fx, fy + 60, 520, 640, nk, () => W.frostKing(ctx, fx, fy, 0.6, t, { eyes: p(t, c.crystal + 0.5, 0.6) }));
      W.text(ctx, T.a, fx, 760, { size: 50, color: W.C.ivory, reveal: p(t, c.crystal + 0.1, 0.8) });
      // the dragon: real pencil drawing (falls back to the engraved version if missing)
      const dr = p(t, c.wing - 0.3, 1.1);
      if (!W.image(ctx, 'dragon', dx, dy - 10, 540, { reveal: dr, zoom: 1 + 0.04 * p(t, c.wing, 3) }))
        inked(ctx, dx, dy, 700, 620, dr, () =>
          W.bestiaryDragon(ctx, dx + 40, dy + 110, 0.56, t, { flap: 0.15 + 0.12 * Math.sin(t * 2.2), fire: p(t, c.wing + 0.4, 0.6) }));
      W.text(ctx, T.b, dx, 760, { size: 50, color: W.C.ivory, reveal: p(t, c.wing + 0.1, 0.8) });
      // refuted in red ink
      redCross(ctx, fx, fy + 40, 175, (t - c.strike) / 0.9);
      redCross(ctx, dx, dy, 200, (t - c.strike - 0.2) / 0.9);
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
    ctx.fillStyle = col;
    ctx.beginPath(); ctx.arc(0, -46, 9, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-8, -34); ctx.lineTo(8, -34); ctx.lineTo(19, 0); ctx.lineTo(-19, 0); ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  W.scene('two_houses', {
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      W.sword(ctx, 960, 540, 300, { rot: Math.PI, p: p(t, 7.6, 1.6, E.inOut), color: W.C.ivory, width: 2.4, fill: 0.12 });
      W.houseBanner(ctx, 1440, 90, 360, 590, t, { color: W.C.crimson, sigil: 'lancaster', drop: p(t, c.split, 1.6), phase: 0 });
      W.houseBanner(ctx, 480, 90, 360, 590, t, { color: '#f3ead6', sigil: 'york', drop: p(t, c.split + 0.35, 1.6), phase: 1.7 });
      W.text(ctx, T.lan, 1440, 820, { size: 60, color: W.C.crimson, reveal: p(t, c.families, 0.9), rise: 10 });
      W.text(ctx, T.york, 480, 820, { size: 60, color: W.C.ivory, reveal: p(t, c.families + 0.6, 0.9), rise: 10 });
      FIG.forEach((f, i) => {
        const q = p(t, c.people + (i % 14) * 0.06, 0.6, E.out);
        if (q <= 0) return;
        const fp = f.fickle ? p(t, c.allegiance + W.hash(i) * 0.8, 1.4, E.inOut) : 0;
        const sw = f.fickle ? 0.5 + 0.5 * Math.sin((t - c.allegiance) * (2 + W.hash(i * 2) * 2) + i) : 0;
        const k = f.side === 0 ? sw * fp : 1 - sw * fp;
        W.alpha(ctx, q, () => figure(ctx, f.x + (f.fickle ? Math.sin(t * 0.8 + i) * 30 * fp : 0), 965, f.h, W.mixColor(W.C.crimson, W.C.ivory, k)));
      });
      const out = 1 - p(t, c.allegiance - 0.6, 0.5);
      W.words(ctx, T.a, W.W / 2, 150, t, [8.56, 9.06, 9.84, 9.98], { size: 52, color: W.C.ivory, alpha: out });
      W.words(ctx, T.c, W.W / 2, 150, t, [c.allegiance, c.allegiance + 0.5], { size: 52, color: W.C.crimson, alpha: 1 - p(t, S.end - 0.7, 0.6) });
    },
  });

  // ---------------------------------------------------------------- title (illuminated title page)
  function border(ctx, q, t) {
    if (q <= 0) return;
    const x0 = 230, y0 = 120, x1 = W.W - 230, y1 = W.H - 120;
    const rect = [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]];
    W.strokePoly(ctx, rect, q, { color: W.C.gold, width: 5, cap: 'butt' });
    const inner = [[x0 + 16, y0 + 16], [x1 - 16, y0 + 16], [x1 - 16, y1 - 16], [x0 + 16, y1 - 16], [x0 + 16, y0 + 16]];
    W.strokePoly(ctx, inner, q, { color: W.C.crimson, width: 1.6, cap: 'butt' });
    // vine scroll along the top and bottom
    for (const yy of [y0 + 42, y1 - 42]) {
      const pts = [];
      for (let x = x0 + 60; x <= x1 - 60; x += 8) pts.push([x, yy + Math.sin((x - x0) / 38) * 9]);
      W.strokePoly(ctx, pts, q, { color: W.rgba(W.C.ivory, 0.55), width: 1.4 });
      for (let x = x0 + 90, k = 0; x < x1 - 60; x += 119, k++) {
        const lp = W.clamp(q * 1.4 - (x - x0) / (x1 - x0) * 0.4);
        if (lp > 0) W.rose(ctx, x, yy + Math.sin((x - x0) / 38) * 9, 11, { kind: k % 2 ? 'york' : 'lancaster', bloom: lp });
      }
    }
    for (const [x, y, k] of [[x0, y0, 'lancaster'], [x1, y0, 'york'], [x0, y1, 'york'], [x1, y1, 'lancaster']]) {
      W.rose(ctx, x, y, 26, { kind: k, bloom: W.clamp(q * 1.5 - 0.3) });
    }
  }

  W.scene('title', {
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const cx = W.W / 2;
      border(ctx, p(t, 19.5, 3.2, E.inOut), t);
      // the Iron Throne, faint behind the title: the drama these wars inspired
      if (!W.image(ctx, 'iron_throne', cx, 520, 660, { alpha: 0.13 * p(t, 21.6, 2.4), tint: 'sepia(0.7)', zoom: 1 + 0.03 * p(t, 21.6, 8) }))
        W.alpha(ctx, 0.16, () => W.crossedSwords(ctx, cx, 560, 300, { p: p(t, 21.6, 2.4, E.inOut), color: W.C.ivory, width: 2 }));
      W.crown(ctx, cx, 330, 64, { p: p(t, 20.2, 2.0, E.inOut), color: W.C.gold, width: 3, fill: 0.35 * p(t, 21.6, 1) });
      W.rose(ctx, 1500, 560, 74, { kind: 'lancaster', bloom: p(t, 20.6, 2) });
      W.rose(ctx, 420, 560, 74, { kind: 'york', bloom: p(t, 21.0, 2) });
      // rubricated title: "حروب" in ink, "الوردتين" in red
      W.words(ctx, T.title, cx, 545, t, [c.title - 0.1, c.title + 0.3], { size: 168, colors: [W.C.ivory, W.C.crimson], rise: 14, dur: 1.0 });
      const lp = p(t, c.title + 0.4, 1.4, E.inOut);
      W.hairline(ctx, cx - 250, 668, 380, lp, W.C.gold, 2);
      W.hairline(ctx, cx + 250, 668, 380, lp, W.C.gold, 2);
      W.diamond(ctx, cx, 668, 8 * lp, W.C.crimson);
      W.text(ctx, T.latin, cx, 724, { size: 34, fam: W.F.latin, weight: 600, color: W.C.ivory, dir: 'ltr', tracking: 12, alpha: p(t, c.title + 0.8, 1) });
      W.text(ctx, T.years, cx, 778, { size: 28, fam: W.F.latin, weight: 600, color: W.C.crimson, dir: 'ltr', tracking: 6, alpha: p(t, c.title + 1.1, 1) });
      W.text(ctx, T.note, cx, 880, { size: 34, fam: W.F.title, weight: 400, color: W.C.ivoryDim, reveal: p(t, c.drama, 1.0), alpha: 1 - p(t, S.end - 0.9, 0.7) });
    },
  });
})();
