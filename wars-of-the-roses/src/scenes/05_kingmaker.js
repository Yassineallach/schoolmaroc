/* Act IV — the kingmaker: Edward's marriage, Warwick's defection, the readeption and 1471 */
(function () {
  const { W } = window;
  const { p, E } = W;

  // ---------------------------------------------------------------- marriage
  W.scene('marriage', {
    bg: () => ({ glow: '#2c2219', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const ex = 960, ey = 540;
      W.text(ctx, T.err, W.W / 2, 200, { size: 40, fam: W.F.label, weight: 500, color: W.C.crimsonBright, reveal: p(t, c.err, 0.9) });
      W.node(ctx, ex, ey, 18, { p: p(t, 170.9, 0.8), color: W.C.ivory, crown: 1, crownColor: W.C.ivory });
      W.text(ctx, T.e4, ex, ey + 62, { size: 46, color: W.C.ivory, alpha: p(t, 171.0, 0.8) });
      // planned French match, then cut
      const fx = 1460;
      const cut = p(t, c.cancel, 0.6, E.out);
      W.alpha(ctx, 1 - cut * 0.55, () => {
        W.fleur(ctx, fx, ey - 110, 38, { p: p(t, 171.3, 1.0), color: W.C.gold, width: 2, fill: 0.12 });
        W.node(ctx, fx, ey, 14, { p: p(t, 171.3, 0.8), color: W.C.ivoryDim });
        W.text(ctx, T.fp, fx, ey + 58, { size: 40, color: W.C.ivory, alpha: p(t, c.fp - 0.8, 0.7) });
        W.text(ctx, T.fpSub, fx, ey + 102, { size: 24, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.fp - 0.5, 0.7) });
      });
      const lp = p(t, 171.6, 0.9, E.inOut);
      const midx = (ex + fx) / 2, gap = cut * 70;
      W.strokePoly(ctx, [[ex + 34, ey], [midx - gap, ey]], lp, { color: W.rgba(W.C.gold, 0.7), width: 1.8, dash: [6, 7] });
      W.strokePoly(ctx, [[fx - 30, ey], [midx + gap, ey]], lp, { color: W.rgba(W.C.gold, 0.7 * (1 - cut * 0.6)), width: 1.8, dash: [6, 7] });
      if (cut > 0 && cut < 1) {
        for (let i = 0; i < 10; i++) {
          const a = (i / 10) * Math.PI * 2, r = cut * 60;
          ctx.fillStyle = W.rgba(W.C.gold, 1 - cut);
          ctx.fillRect(midx + Math.cos(a) * r, ey + Math.sin(a) * r, 3, 3);
        }
      }
      // secret marriage to Elizabeth Woodville
      const wx = 460;
      W.node(ctx, wx, ey, 14, { p: p(t, c.secret, 0.8), color: W.C.ivory });
      W.text(ctx, T.ew, wx, ey + 58, { size: 40, color: W.C.ivory, reveal: p(t, c.secret + 0.2, 0.8) });
      W.text(ctx, T.ewSub, wx, ey + 102, { size: 24, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.widow, 0.7) });
      W.strokePoly(ctx, [[ex - 34, ey], [wx + 30, ey]], p(t, c.secret + 0.2, 1.0, E.inOut), { color: W.rgba(W.C.ivory, 0.8), width: 2 });
      W.rings(ctx, (ex + wx) / 2, ey - 50, 26, { p: p(t, c.secret + 0.5, 1.0), color: W.C.gold, width: 2 });
      W.text(ctx, T.secret, (ex + wx) / 2, ey - 110, { size: 28, fam: W.F.label, weight: 500, color: W.C.gold, alpha: p(t, c.secret + 0.8, 0.8) });
    },
  });

  // ---------------------------------------------------------------- warwick
  W.scene('warwick', {
    bg: () => ({ glow: '#291a17', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const sp = p(t, S.start, 1.2, E.inOut);
      // two camps
      ctx.save();
      const gR = ctx.createLinearGradient(W.W / 2, 0, W.W, 0);
      gR.addColorStop(0, W.rgba(W.C.crimson, 0)); gR.addColorStop(1, W.rgba(W.C.crimson, 0.18 * sp));
      ctx.fillStyle = gR; ctx.fillRect(W.W / 2, 0, W.W / 2, W.H);
      ctx.restore();
      W.strokePoly(ctx, [[W.W / 2, 130], [W.W / 2, 980]], sp, { color: W.rgba(W.C.ivory, 0.3), width: 1.2, dash: [3, 8] });
      W.text(ctx, T.york, 480, 190, { size: 40, color: W.C.ivory, alpha: sp });
      W.text(ctx, T.lan, 1440, 190, { size: 40, color: W.C.crimsonBright, alpha: sp });
      // Edward
      W.node(ctx, 400, 520, 18, { p: sp, color: W.C.ivory, crown: 1, crownColor: W.C.ivory });
      W.text(ctx, T.e4, 400, 582, { size: 38, color: W.C.ivory, alpha: sp });
      // Lancastrian camp
      W.node(ctx, 1640, 520, 16, { p: p(t, c.ally - 0.4, 0.8), color: W.C.crimsonBright, crown: 1, crownColor: W.C.gold });
      W.text(ctx, 'مارغريت أنجو', 1640, 582, { size: 34, color: W.C.crimsonBright, alpha: p(t, c.ally - 0.2, 0.7) });
      // Warwick: link snaps, then crosses over
      const mv = p(t, c.turn + 0.4, 1.8, E.inOut);
      const wx = W.lerp(760, 1180, mv), wy = 520 - Math.sin(mv * Math.PI) * 60;
      const snap = p(t, c.turn, 0.5, E.out);
      const linkEnd = W.lerp(wx - 30, 590, snap);
      W.strokePoly(ctx, [[434, 520], [W.lerp(wx - 30, 520, snap), 520]], 1, { color: W.rgba(W.C.ivory, 0.75 * (1 - snap)), width: 2.5 });
      W.strokePoly(ctx, [[linkEnd, 520], [wx - 30, wy]], 1, { color: W.rgba(W.C.ivory, 0.75 * (1 - snap)), width: 2.5 });
      W.strokePoly(ctx, [[wx + 30, wy], [1610, 520]], p(t, c.ally, 0.9, E.inOut), { color: W.rgba(W.C.crimsonBright, 0.8), width: 2.5 });
      const wcol = W.mixColor(W.C.ivory, W.C.crimsonBright, mv);
      W.node(ctx, wx, wy, 17, { p: p(t, c.wa - 0.8, 0.8), color: wcol, halo: t > c.wa && t < c.turn ? W.C.ivory : null });
      W.text(ctx, T.wa, wx, wy + 62, { size: 36, color: W.C.ivory, reveal: p(t, c.wa, 0.8) });
      W.text(ctx, T.waSub, wx, wy + 104, { size: 26, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.wa + 0.4, 0.7) });
      // George, the jealous brother, follows
      const gm = p(t, c.gName - 0.2, 1.6, E.inOut);
      const gx = W.lerp(520, 1180, gm), gy = 800;
      W.node(ctx, gx, gy, 14, { p: p(t, c.g - 0.3, 0.8), color: W.mixColor(W.C.ivory, W.C.crimsonBright, gm * 0.5) });
      W.text(ctx, T.g, gx, gy + 54, { size: 32, color: W.C.ivory, alpha: p(t, c.g, 0.7) });
      W.text(ctx, T.gSub, gx, gy + 94, { size: 24, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.g + 0.3, 0.7) });
      W.strokePoly(ctx, [[wx, wy + 130], [gx, gy - 30]], p(t, c.g, 1.0, E.inOut), { color: W.rgba(W.C.crimsonBright, 0.6), width: 1.6, dash: [5, 7], dashOffset: -t * 20 });
    },
  });

  // ---------------------------------------------------------------- readeption
  W.scene('readeption', {
    bg: () => ({ glow: '#24201b', glowA: 0.45 }),
    dust: 16,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const phaseA = 1 - p(t, c.back - 0.5, 0.8);
      // the crown flips back to Lancaster
      W.alpha(ctx, phaseA, () => {
        const f = p(t, c.rest + 0.2, 1.0, E.inOut);
        ctx.save();
        ctx.translate(W.W / 2, 400);
        ctx.scale(Math.abs(Math.cos(f * Math.PI)) * 0.98 + 0.02, 1);
        ctx.translate(-W.W / 2, -400);
        W.crown(ctx, W.W / 2, 400, 110, { color: f < 0.5 ? W.C.ivory : W.C.crimsonBright, width: 3, fill: 0.2 });
        ctx.restore();
        W.text(ctx, T.rest, W.W / 2, 640, { size: 64, color: W.C.ivory, reveal: p(t, c.rest + 0.9, 0.9) });
        W.text(ctx, 'بدعم من وارويك', W.W / 2, 720, { size: 30, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.rest + 1.3, 0.8) });
      });
      // 1471: Barnet, Tewkesbury, the Tower
      const mb = p(t, c.back - 0.6, 0.9);
      if (mb <= 0) return;
      W.alpha(ctx, mb, () => {
        const view = W.lerpView({ lon: -1.3, lat: 52.0, k: 250 }, { lon: -1.0, lat: 51.85, k: 290 }, p(t, c.back, 7, E.inOutSine));
        W.drawMap(ctx, t, view, { reveal: p(t, c.back - 0.6, 1.4, E.inOut), continent: true, regionLabels: false });
        const B = W.place(view, 'barnet'), TK = W.place(view, 'tewkesbury'), L = W.place(view, 'london');
        W.marker(ctx, B[0], B[1], t, c.back + 0.2, { kind: 'battle', label: T.bar, sub: T.barSub, side: 'right', dist: 70, dy: -30, color: W.C.ivory, size: 40 });
        W.marker(ctx, TK[0], TK[1], t, c.prince, { kind: 'battle', label: T.tew, sub: T.tewSub, side: 'left', dist: 80, color: W.C.ivory, size: 40 });
        // Henry VI in the Tower: his node fades
        const d = p(t, c.h6, 1.4);
        W.node(ctx, L[0] + 2, L[1] + 40, 11, { p: p(t, c.back, 0.6), color: W.mixColor(W.C.crimsonBright, '#3a3430', d), dead: d > 0.5 });
        W.text(ctx, 'هنري السادس', L[0] + 30, L[1] + 40, { size: 28, color: W.C.crimsonBright, align: 'left', alpha: p(t, c.back + 0.3, 0.6) * (1 - d * 0.5) });
        W.caption(ctx, 1760, 220, t, c.h6, { kicker: T.h6Sub, title: T.h6, size: 44, alpha: p(t, c.h6, 0.6) });
      });
    },
  });
})();
