/* Horizontal editorial timeline. Years run right -> left (Arabic reading direction). */
(function () {
  const { W } = window;

  /**
   * o: { x0, x1, y, from, to, t0 (line starts), dur, alpha, ticks (step years),
   *      events: [{ year, t, label, sub, color, up }] }
   * returns a function year -> x
   */
  W.timeline = (ctx, t, o) => {
    const a = o.alpha == null ? 1 : o.alpha;
    const X = (yr) => W.map(yr, o.from, o.to, o.x1, o.x0); // rtl: early years on the right
    if (a <= 0) return X;
    const lp = W.p(t, o.t0, o.dur || 1.6, W.E.inOut);
    ctx.save();
    ctx.globalAlpha *= a;
    // main rule
    ctx.strokeStyle = W.rgba(W.C.ivory, 0.55);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(o.x1, o.y);
    ctx.lineTo(W.lerp(o.x1, o.x0, lp), o.y);
    ctx.stroke();
    // ticks
    const step = o.ticks || 10;
    for (let yr = Math.ceil(o.from / step) * step; yr <= o.to; yr += step) {
      const x = X(yr);
      const tp = W.clamp((W.map(x, o.x1, o.x0, 0, 1) - lp) * -12);
      if (tp <= 0) continue;
      ctx.strokeStyle = W.rgba(W.C.ivory, 0.3 * tp);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, o.y - 7); ctx.lineTo(x, o.y + 7); ctx.stroke();
      if (o.tickLabels !== false && yr % (step * 2) === 0)
        W.text(ctx, String(yr), x, o.y + 30, { size: 18, fam: W.F.latin, weight: 400, color: W.rgba(W.C.ivory, 0.35), alpha: tp, dir: 'ltr' });
    }
    // events
    for (const e of o.events || []) {
      const ep = W.p(t, e.t, 0.7, W.E.outBack);
      if (ep <= 0) continue;
      const x = X(e.year), col = e.color || W.C.ivory;
      const up = e.up !== false;
      const stem = e.stem || 70;
      const sy = up ? o.y - stem : o.y + stem;
      const sp = W.p(t, e.t, 0.5);
      // stem
      ctx.strokeStyle = W.rgba(col.startsWith('#') ? col : W.C.ivory, 0.6);
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(x, o.y); ctx.lineTo(x, W.lerp(o.y, sy, sp)); ctx.stroke();
      // marker
      ctx.save();
      ctx.translate(x, o.y);
      ctx.scale(ep, ep);
      if (e.glow !== false) {
        const g = ctx.createRadialGradient(0, 0, 0, 0, 0, 40);
        g.addColorStop(0, W.rgba(col.startsWith('#') ? col : W.C.ivory, 0.45)); g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, 40, 0, Math.PI * 2); ctx.fill();
      }
      ctx.restore();
      W.diamond(ctx, x, o.y, 10 * ep, col);
      const tp = W.p(t, e.t + 0.15, 0.7);
      const yrY = up ? sy - 22 : sy + 24;
      W.text(ctx, String(e.year), x, yrY, { size: e.yearSize || 40, fam: W.F.latin, weight: 600, color: col, alpha: tp, dir: 'ltr' });
      if (e.label) W.text(ctx, e.label, x, up ? yrY - 48 : yrY + 50, { size: e.size || 32, fam: W.F.title, weight: 700, color: W.C.ivory, alpha: tp, reveal: tp });
      if (e.sub) W.text(ctx, e.sub, x, up ? yrY - 88 : yrY + 88, { size: 22, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: W.p(t, e.t + 0.4, 0.7) });
    }
    ctx.restore();
    return X;
  };
})();
