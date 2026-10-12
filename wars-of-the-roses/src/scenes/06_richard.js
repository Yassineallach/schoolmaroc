/* Act V — Richard III: 1483, the usurpation, the princes in the Tower */
(function () {
  const { W } = window;
  const { p, E } = W;

  // ---------------------------------------------------------------- calm_1483
  W.scene('calm_1483', {
    bg: () => ({ glow: '#211e1a', glowA: 0.45 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const X = W.timeline(ctx, t, {
        x0: 260, x1: 1660, y: 600, from: 1471, to: 1485, t0: 202.4, dur: 2.8, ticks: 1, tickLabels: false,
        events: [
          { year: 1471, t: 202.5, label: 'عودة إدوارد الرابع', color: W.C.ivory, size: 26 },
          { year: 1483, t: c.year, label: T.death, color: W.C.ivory, size: 30 },
        ],
      });
      W.text(ctx, T.peace, X(1477), 520, { size: 44, color: W.C.ivoryDim, alpha: p(t, c.peace, 1.0) * (1 - p(t, c.blood, 0.8) * 0.6) });
      // ink bleeds out from 1483
      const bp = p(t, c.blood - 0.1, 2.2, E.out);
      if (bp > 0) {
        const cx = X(1483), cy = 600;
        ctx.save();
        for (let i = 0; i < 16; i++) {
          const r = W.rng(100 + i);
          const ang = r() * Math.PI * 2, dist = (20 + r() * 130) * bp;
          const bx = cx + Math.cos(ang) * dist * 1.8, by = cy + Math.sin(ang) * dist * 0.5 + bp * r() * 40;
          const rad = (14 + r() * 40) * W.E.out(W.clamp(bp * 1.4 - r() * 0.3));
          if (rad <= 0) continue;
          ctx.beginPath();
          for (let k = 0; k <= 24; k++) {
            const a = (k / 24) * Math.PI * 2;
            const rr = rad * (0.75 + 0.35 * W.noise(k * 0.7 + i * 3, i));
            k ? ctx.lineTo(bx + Math.cos(a) * rr, by + Math.sin(a) * rr) : ctx.moveTo(bx + Math.cos(a) * rr, by + Math.sin(a) * rr);
          }
          ctx.closePath();
          ctx.fillStyle = W.rgba(i % 3 ? W.C.crimson : W.C.crimsonDeep, 0.75);
          ctx.fill();
        }
        // drips
        for (let i = 0; i < 7; i++) {
          const r = W.rng(300 + i);
          const x = cx + (r() - 0.5) * 300 * bp, len = (60 + r() * 160) * W.clamp(bp * 1.2 - 0.2);
          if (len <= 0) continue;
          ctx.strokeStyle = W.rgba(W.C.crimson, 0.8); ctx.lineWidth = 3 + r() * 4; ctx.lineCap = 'round';
          ctx.beginPath(); ctx.moveTo(x, cy + 10); ctx.lineTo(x, cy + 10 + len); ctx.stroke();
          ctx.fillStyle = W.rgba(W.C.crimson, 0.85);
          ctx.beginPath(); ctx.arc(x, cy + 12 + len, 4 + r() * 3, 0, Math.PI * 2); ctx.fill();
        }
        ctx.restore();
      }
      W.text(ctx, T.blood, W.W / 2, 900, { size: 60, color: W.C.ivory, reveal: p(t, c.blood + 0.3, 0.9), rise: 10 });
    },
  });

  // ---------------------------------------------------------------- usurpation
  W.scene('usurpation', {
    bg: () => ({ glow: '#271b18', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const ex = 1300, ey = 470, rx = 620;
      const jail = p(t, c.jail, 1.4, E.inOut);
      // Edward V
      W.alpha(ctx, 1 - jail, () => {
        W.node(ctx, ex, ey, 17, { p: p(t, c.son, 0.8), color: W.C.ivory, halo: t < c.illeg ? W.C.ivory : null });
        W.text(ctx, T.e5, ex, ey + 62, { size: 44, color: W.C.ivory, reveal: p(t, c.son + 0.2, 0.8) });
        W.text(ctx, T.e5Sub, ex, ey + 108, { size: 26, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.heir, 0.7) * (1 - p(t, c.illeg, 0.5)) });
      });
      // illegitimacy stamp
      W.alpha(ctx, 1 - jail, () => {
        W.seal(ctx, ex + 150, ey - 40, 52, { p: p(t, c.illeg, 0.5), color: W.C.crimson, emblem: false });
        W.text(ctx, T.illeg, ex, ey + 108, { size: 36, fam: W.F.label, weight: 700, color: W.C.crimsonBright, alpha: p(t, c.illeg + 0.2, 0.4) });
        W.text(ctx, T.reason, ex, ey + 160, { size: 26, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.reason, 0.7) });
      });
      // Richard III
      W.node(ctx, rx, ey, 18, { p: p(t, c.r3, 0.8), color: W.C.ivory });
      W.text(ctx, T.r3, rx, ey + 62, { size: 46, color: W.C.ivory, reveal: p(t, c.r3 + 0.2, 0.8) });
      W.text(ctx, T.r3Sub, rx, ey + 108, { size: 26, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.r3 + 0.6, 0.7) });
      W.strokePoly(ctx, [[rx + 30, ey], [ex - 30, ey]], p(t, c.r3 + 0.4, 0.9), { color: W.rgba(W.C.ivory, 0.35), width: 1.5, dash: [2, 6] });
      // the crown moves to the uncle
      const cm = p(t, c.took, 1.4, E.inOut);
      W.crown(ctx, W.lerp(ex, rx, cm), ey - 70 - Math.sin(cm * Math.PI) * 90, 36, { p: p(t, c.son, 1.0), color: W.C.gold, width: 2.2, fill: 0.25, glow: 'rgba(201,164,92,0.4)' });
      // the boys in the Tower
      const tx = 1300, ty = 560;
      W.castle(ctx, tx, ty, 120, { p: jail, color: W.C.ivoryDim, width: 2, fill: 0.08 });
      for (const [dx, dy] of [[-0.15, -0.38], [0.15, -0.38]]) {
        W.node(ctx, W.lerp(ex + dx * 400, tx + dx * 120, jail), W.lerp(ey, ty + dy * 120, jail), 6, { p: p(t, c.jail - 0.2, 0.6), color: W.C.ivory, width: 1.5 });
      }
      W.text(ctx, T.tower, tx, ty + 170, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.jail + 0.6, 0.8) });
    },
  });

  // ---------------------------------------------------------------- princes
  W.scene('princes', {
    bg: () => ({ glow: '#161a20', glowA: 0.5, ly: 0.3 }),
    dust: 20,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const s = 260, cx = 960, cy = 600;
      W.castle(ctx, cx, cy, s, { color: W.rgba(W.C.ivory, 0.55), width: 2, fill: 0.16, fillColor: '#000' });
      // two lit windows go dark
      const dark = p(t, c.vanish, 2.0, E.inOut);
      for (const dx of [-0.15, 0.15]) {
        const x = cx + dx * s, y = cy - 0.36 * s;
        const fl = 0.85 + 0.15 * Math.sin(t * 9 + dx * 40);
        const g = ctx.createRadialGradient(x, y, 0, x, y, 60);
        g.addColorStop(0, `rgba(255,196,120,${0.85 * (1 - dark) * fl})`); g.addColorStop(1, 'rgba(255,170,90,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 60, 0, Math.PI * 2); ctx.fill();
      }
      W.text(ctx, T.a, W.W / 2, 190, { size: 54, color: W.C.ivory, reveal: p(t, c.vanish - 0.2, 0.9), alpha: 1 - p(t, c.stable - 0.3, 0.6) });
      W.text(ctx, T.b, W.W / 2, 930, { size: 48, color: W.C.ivory, reveal: p(t, c.unknown, 1.0), alpha: 1 - p(t, c.stable - 0.3, 0.6) });
      // Richard's power: steady, with a faint tremor
      const sp = p(t, c.stable, 0.9);
      const tremor = Math.sin(t * 23) * 1.5 * sp;
      W.crown(ctx, W.W / 2 + tremor, 200, 44, { p: sp, color: W.C.gold, width: 2.2, fill: 0.2 });
      W.text(ctx, T.c, W.W / 2, 930, { size: 48, color: W.C.gold, reveal: p(t, c.stable + 0.3, 0.9) });
    },
  });
})();
