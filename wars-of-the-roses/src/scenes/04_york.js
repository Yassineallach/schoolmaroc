/* Act III — the rise of York: St Albans & the Act of Accord, Wakefield, Edward IV, Towton */
(function () {
  const { W } = window;
  const { p, E } = W;

  /** small disclaimer used under every abstract battle diagram */
  W.illustrative = (ctx, a = 1) =>
    W.text(ctx, 'رسم توضيحي — المواقع والتشكيلات تقريبية', W.W - 110, W.H - 92, { size: 20, fam: W.F.label, weight: 400, color: W.rgba(W.C.ivory, 0.4), align: 'right', alpha: a });

  // ---------------------------------------------------------------- st_albans
  W.scene('st_albans', {
    bg: () => ({ glow: '#241d17', glowA: 0.45 }),
    dust: 14,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const view = W.lerpView({ lon: -1.7, lat: 52.2, k: 260 }, { lon: -1.3, lat: 52.0, k: 300 }, p(t, S.start, S.end - S.start, E.inOutSine));
      const mapA = 1 - p(t, c.noThrone - 0.2, 0.9) * 0.78;
      W.alpha(ctx, mapA, () => {
        W.drawMap(ctx, t, view, { reveal: p(t, S.start + 0.3, 1.8, E.inOut), regionLabels: false, continent: true });
        const L = W.place(view, 'london'), SA = W.place(view, 'stalbans'), LU = W.place(view, 'ludlow');
        W.marker(ctx, L[0], L[1], t, 141.0, { label: 'لندن', side: 'right', dist: 50, rings: 0, size: 28 });
        W.marker(ctx, LU[0], LU[1], t, 140.9, { label: 'لودلو', side: 'left', dist: 50, rings: 0, size: 28 });
        // York's new army marches on the king's party
        W.route(ctx, W.arcPts(LU, SA, -0.08, 40), t, p(t, c.army - 0.4, 1.8, E.inOut), { color: W.C.ivory, width: 4 });
        W.route(ctx, W.arcPts(L, SA, 0.25, 20), t, p(t, c.army + 0.2, 1.0, E.inOut), { color: W.C.crimsonBright, width: 3 });
        W.marker(ctx, SA[0], SA[1], t, c.army + 1.0, { kind: 'battle', label: T.sa, sub: T.saSub, side: 'right', dist: 90, dy: -80, color: W.C.ivory, size: 44, subSize: 28 });
      });
      // the throne remains out of reach
      const ta = W.env(t, c.noThrone, S.end + 1, 0.5, 0.5);
      W.alpha(ctx, ta, () => {
        const hover = Math.sin(t * 1.4) * 6;
        W.crown(ctx, W.W / 2, 300 + hover, 70, { p: p(t, c.noThrone, 1.2, E.inOut), color: W.C.gold, width: 2.4, fill: 0.2, glow: 'rgba(201,164,92,0.4)' });
        const reach = p(t, c.noThrone + 0.3, 1.4, E.inOut) * 0.8;
        W.strokePoly(ctx, [[W.W / 2, 600], [W.W / 2, W.lerp(600, 390, reach)]], 1, { color: W.rgba(W.C.ivory, 0.6), width: 2, dash: [4, 7] });
        W.node(ctx, W.W / 2, 620, 16, { p: p(t, c.noThrone, 0.7), color: W.C.ivory });
        W.text(ctx, T.reach, W.W / 2 + 60, 470, { size: 32, fam: W.F.label, weight: 400, color: W.C.ivoryDim, align: 'left', alpha: p(t, c.noThrone + 0.4, 0.8) * (1 - p(t, c.forced, 0.6)) });
        // Act of Accord: the royal seal
        W.seal(ctx, W.W / 2 + 330, 560, 70, { p: p(t, c.forced, 0.6), color: W.C.crimson });
        W.text(ctx, T.acc, W.W / 2, 790, { size: 54, color: W.C.ivory, reveal: p(t, c.forced + 0.2, 0.9) });
        W.text(ctx, T.heir, W.W / 2, 860, { size: 32, fam: W.F.label, weight: 400, color: W.C.gold, reveal: p(t, c.heir, 0.9) });
      });
    },
  });

  // ---------------------------------------------------------------- wakefield
  W.scene('wakefield', {
    bg: () => ({ glow: '#2a1514', glowA: 0.5 }),
    dust: 10,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const fade = 1 - p(t, c.head - 0.2, 1.0) * 0.82;
      W.alpha(ctx, fade, () => {
        W.terrain(ctx, t, 6, 1);
        const conv = p(t, 149.6, 2.2, E.inOut);
        const br = p(t, c.killed, 1.6, E.out);
        W.formation(ctx, 820, 560, t, { cols: 6, rows: 3, color: W.C.ivory, scatter: br, retreat: -1, seed: 3 });
        W.text(ctx, T.york, 820, 470 - br * 30, { size: 36, color: W.C.ivory, alpha: p(t, 149.2, 0.6) * (1 - br * 0.6) });
        const blocks = [[[1480, 360], [1010, 430], 0.2], [[1520, 760], [1030, 690], -0.2], [[1600, 560], [1060, 560], 0], [[560, 230], [700, 420], 0.6]];
        blocks.forEach(([a, b, ang], i) => {
          const x = W.lerp(a[0], b[0], conv), y = W.lerp(a[1], b[1], conv);
          W.formation(ctx, x, y, t, { cols: 7, rows: 3, color: W.C.crimsonBright, angle: ang, seed: 20 + i, alpha: p(t, 149.0 + i * 0.15, 0.6) });
          if (i < 3) W.bigArrow(ctx, [a[0] - 60, a[1]], [x - 80, y], p(t, 149.4 + i * 0.1, 1.6), { color: W.C.crimsonBright, width: 18 });
        });
        W.text(ctx, T.lan, 1520, 880, { size: 32, fam: W.F.label, weight: 500, color: W.C.crimsonBright, alpha: p(t, c.queen, 0.7) });
        W.caption(ctx, 1760, 200, t, c.tragic, { kicker: T.btSub, title: T.bt, size: 54 });
        W.illustrative(ctx, p(t, 149.5, 1));
      });
      // aftermath: a lone spike with a paper crown at Micklegate Bar
      const hp = p(t, c.head, 1.4, E.inOut);
      if (hp > 0) {
        const top = W.lerp(900, 330, hp);
        W.strokePoly(ctx, [[W.W / 2, 900], [W.W / 2, top]], 1, { color: W.rgba(W.C.ivory, 0.8), width: 2.5 });
        W.crown(ctx, W.W / 2, top - 34, 26, { p: p(t, c.head + 0.8, 0.9), color: W.C.ivoryDim, width: 1.6, fill: 0 });
        W.text(ctx, T.mick, W.W / 2, 950, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.head + 0.6, 0.8) });
      }
    },
  });

  // ---------------------------------------------------------------- edward4
  W.scene('edward4', {
    bg: () => ({ glow: '#3a2c18', glowA: 0.6 }),
    dust: 36,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const sp = p(t, c.son - 0.3, 2.0, E.out);
      const hasBadge = W.IMG && W.IMG.rose_en_soleil;
      if (hasBadge) {
        // Edward IV's badge: the white rose en soleil, slowly turning
        const D = 400 * (0.7 + 0.3 * sp);
        ctx.save(); ctx.globalAlpha *= W.clamp(sp * 1.4); ctx.translate(W.W / 2, 400); ctx.rotate((t - c.son) * 0.04);
        ctx.drawImage(W.IMG.rose_en_soleil.img, -D / 2, -D / 2, D, D); ctx.restore();
      } else W.sun(ctx, W.W / 2, 360, 230, t, { p: sp, color: W.rgba(W.C.gold, 0.7) });
      const d = p(t, c.crowned, 1.0, E.out);
      W.crown(ctx, W.W / 2, hasBadge ? W.lerp(40, 150, d) : W.lerp(120, 360, d), hasBadge ? 56 : 68, { p: p(t, c.claim, 1.2, E.inOut), color: W.C.gold, width: 3, fill: 0.35 });
      W.text(ctx, T.name, W.W / 2, 690, { size: 104, color: W.C.ivory, reveal: p(t, c.crowned + 0.3, 1.0), rise: 14 });
      W.year(ctx, T.year, W.W / 2, 815, t, c.crowned + 0.7, { size: 84, color: W.C.gold });
      W.text(ctx, T.sub, W.W / 2, 900, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.name, 0.7) });
    },
  });

  // ---------------------------------------------------------------- towton
  W.scene('towton', {
    bg: () => ({ glow: '#1f1d1c', glowA: 0.45 }),
    dust: 14,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const view = W.lerpView({ lon: -1.7, lat: 53.6, k: 300 }, { lon: -1.4, lat: 52.3, k: 165 }, p(t, c.h6 - 0.4, 2.4, E.inOut));
      W.drawMap(ctx, t, view, { reveal: p(t, S.start, 1.4, E.inOut), continent: true, regionLabels: true, channel: p(t, c.fled, 1) });
      const TW = W.place(view, 'towton'), L = W.place(view, 'london'), Y = W.place(view, 'york');
      W.marker(ctx, Y[0], Y[1], t, S.start + 0.4, { label: 'يورك', side: 'right', dist: 46, rings: 0, size: 26 });
      // Lancastrian army breaks
      W.formation(ctx, TW[0] + 70, TW[1] + 20, t, { cols: 6, rows: 2, gap: 12, unit: 7, color: W.C.crimsonBright, scatter: p(t, c.lan - 0.4, 1.4), seed: 8, alpha: 1 - p(t, c.h6, 0.8) });
      W.marker(ctx, TW[0], TW[1], t, c.vic, { kind: 'battle', label: T.tow, sub: T.towSub, side: 'left', dist: 80, color: W.C.ivory, size: 44, subSize: 26 });
      // Henry VI captured and taken to the Tower
      const hp = p(t, c.h6, 1.8, E.inOut);
      const from = W.proj(view, [-2.39, 53.87]);
      if (hp > 0) {
        const pts = W.arcPts(from, L, 0.12, 40);
        W.route(ctx, pts, t, hp, { color: W.C.crimsonBright, width: 2.5 });
        const h = W.polyPart(pts, hp).pop();
        W.node(ctx, h[0], h[1], 10, { color: W.C.crimsonBright, crown: 0.9, crownColor: W.C.gold, portrait: 'p_henry6', pr: 26 });
      }
      W.marker(ctx, L[0], L[1], t, c.h6 + 1.5, { label: T.h6, sub: T.h6Sub, side: 'left', dist: 70, color: W.C.crimsonBright, size: 34 });
      // Margaret and her son to exile
      const ep = p(t, c.fled, 2.0, E.inOut);
      const ex = [W.proj(view, [-1.6, 54.7]), W.proj(view, [1.2, 54.0]), W.proj(view, [2.2, 52.0]), W.proj(view, [1.9, 50.6])];
      const exs = [...W.arcPts(ex[0], ex[1], 0.1, 15), ...W.arcPts(ex[1], ex[2], 0.1, 15).slice(1), ...W.arcPts(ex[2], ex[3], 0.05, 15).slice(1)];
      W.route(ctx, exs, t, ep, { color: W.C.crimsonBright, width: 2.5 });
      W.caption(ctx, 1760, 210, t, c.exile - 0.6, { kicker: 'المنفى', title: T.exile, size: 40, alpha: p(t, c.exile - 0.6, 0.6) });
    },
  });
})();
