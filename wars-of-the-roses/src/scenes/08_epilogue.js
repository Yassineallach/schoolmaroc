/* Epilogue — winners and losers, the seasons of power, end card */
(function () {
  const { W } = window;
  const { p, E } = W;

  function block(ctx, x, base, w, h, col, a = 1) {
    if (h === 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.fillStyle = W.rgba(col, 0.85);
    ctx.fillRect(x - w / 2, h > 0 ? base - h : base, w, Math.abs(h));
    ctx.restore();
  }

  // ---------------------------------------------------------------- decisive
  W.scene('decisive', {
    bg: () => ({ glow: '#26211c', glowA: 0.45 }),
    dust: 12,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const base = 600;
      W.hairline(ctx, W.W / 2, base, 1000, p(t, c.imagine, 1.2, E.inOut), W.rgba(W.C.ivory, 0.6), 2);
      W.text(ctx, T.q, W.W / 2, 220, { size: 60, color: W.C.ivory, reveal: p(t, c.decisive, 0.9) });
      const wh = 260 * p(t, c.win, 0.9, E.outExpo), lh = -200 * p(t, c.lose, 0.9, E.outExpo);
      block(ctx, 1180, base - 2, 180, wh, W.C.crimsonBright);
      block(ctx, 740, base + 2, 180, lh, W.C.ivory, 0.55);
      W.text(ctx, T.w, 1180, base - wh - 50, { size: 46, color: W.C.ivory, alpha: p(t, c.win + 0.2, 0.6) });
      W.text(ctx, T.l, 740, base - lh + 50, { size: 46, color: W.C.ivoryDim, alpha: p(t, c.lose + 0.2, 0.6) });
    },
  });

  // ---------------------------------------------------------------- seasons
  W.scene('seasons', {
    bg: () => ({ glow: '#2a2119', glowA: 0.5 }),
    dust: 30,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      // the winner/loser binary becomes a see-saw: victory is relative
      const tilt = p(t, c.wotr, 1.4, E.inOut);
      const ang = Math.sin((t - c.wotr) * 0.9) * 0.16 * tilt;
      const px = W.W / 2, py = 560, half = 420;
      ctx.save();
      ctx.translate(px, py);
      ctx.rotate(ang);
      ctx.strokeStyle = W.rgba(W.C.ivory, 0.7); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(-half, 0); ctx.lineTo(half, 0); ctx.stroke();
      const shrink = 1 - p(t, S.start, 1.2, E.inOut) * 0.55;
      block(ctx, 220, -2, 120, 260 * shrink * 0.6 + 40, W.C.crimsonBright);
      block(ctx, -220, -2, 120, 200 * shrink * 0.6 + 40, W.C.ivory, 0.7);
      ctx.restore();
      ctx.fillStyle = W.rgba(W.C.ivory, 0.7);
      ctx.beginPath(); ctx.moveTo(px, py + 4); ctx.lineTo(px - 18, py + 40); ctx.lineTo(px + 18, py + 40); ctx.closePath(); ctx.fill();
      // the crown of power dissolves like falling leaves
      const dis = p(t, c.power + 0.3, 2.4, E.inOut);
      W.alpha(ctx, p(t, c.story, 1.0) * (1 - dis), () => W.crown(ctx, W.W / 2, 250, 64, { color: W.C.gold, width: 2.4, fill: 0.2, glow: 'rgba(201,164,92,0.35)' }));
      if (dis > 0) {
        for (let i = 0; i < 70; i++) {
          const r = W.rng(700 + i);
          const delay = r() * 0.4, q = W.clamp((dis - delay) / (1 - delay));
          if (q <= 0) continue;
          const x0 = W.W / 2 + (r() - 0.5) * 140, y0 = 250 + (r() - 0.5) * 90;
          const x = x0 + q * (120 + r() * 380) + Math.sin(q * 6 + i) * 30, y = y0 + q * (200 + r() * 420);
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(q * 6 * (r() - 0.5) + i);
          ctx.globalAlpha *= (1 - q) * 0.9;
          ctx.fillStyle = [W.C.gold, W.C.crimsonBright, W.C.ivory][i % 3];
          ctx.beginPath(); ctx.ellipse(0, 0, 7, 3.5, 0, 0, Math.PI * 2); ctx.fill();
          ctx.restore();
        }
      }
      W.text(ctx, T.a, W.W / 2, 750, { size: 52, color: W.C.ivory, reveal: p(t, c.relative, 0.8) });
      W.text(ctx, T.b, W.W / 2, 830, { size: 52, color: W.C.ivory, reveal: p(t, c.alliances, 0.8) });
      W.text(ctx, T.c, W.W / 2, 915, { size: 56, color: W.C.gold, reveal: p(t, c.power, 1.2) });
    },
  });

  // ---------------------------------------------------------------- endcard
  W.scene('endcard', {
    bg: () => ({ glow: '#33261a', glowA: 0.55 }),
    dust: 30,
    draw(ctx, t, S) {
      const T = S.text;
      W.rose(ctx, W.W / 2, 400, 120, { kind: 'tudor', bloom: p(t, S.start, 1.6, E.out), spin: (t - S.start) * 0.03 });
      W.text(ctx, T.title, W.W / 2, 650, { size: 120, color: W.C.ivory, reveal: p(t, S.start + 0.4, 1.2) });
      W.hairline(ctx, W.W / 2, 745, 520, p(t, S.start + 0.8, 1.2, E.inOut), W.rgba(W.C.gold, 0.6));
      W.text(ctx, T.years, W.W / 2, 800, { size: 30, fam: W.F.latin, weight: 400, color: W.C.gold, dir: 'ltr', tracking: 8, alpha: p(t, S.start + 1.0, 1) });
    },
  });
})();
