/* YouTube thumbnail (1920x1080, exported as 1280x720): same design system as the film.
   Rendered by: node scripts/render.mjs --thumbnail */
(function () {
  const { W } = window;
  W.drawThumbnail = (ctx) => {
    const t = 30;
    W.background(ctx, t, { glow: '#2b1a15', glowA: 0.6 });
    // crimson / ivory halves split by a blade of light
    const gR = ctx.createLinearGradient(W.W / 2, 0, W.W, 0);
    gR.addColorStop(0, W.rgba(W.C.crimson, 0.1)); gR.addColorStop(1, W.rgba(W.C.crimson, 0.55));
    ctx.fillStyle = gR; ctx.fillRect(W.W / 2, 0, W.W / 2, W.H);
    const gL = ctx.createLinearGradient(W.W / 2, 0, 0, 0);
    gL.addColorStop(0, W.rgba(W.C.ivory, 0.02)); gL.addColorStop(1, W.rgba(W.C.ivory, 0.16));
    ctx.fillStyle = gL; ctx.fillRect(0, 0, W.W / 2, W.H);
    ctx.save();
    ctx.strokeStyle = 'rgba(255,240,215,0.9)'; ctx.shadowColor = 'rgba(255,240,215,1)'; ctx.shadowBlur = 30; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(W.W / 2, 0); ctx.lineTo(W.W / 2, W.H); ctx.stroke();
    ctx.restore();
    W.rose(ctx, 1520, 400, 230, { kind: 'lancaster', spin: 0.2 });
    W.rose(ctx, 400, 400, 230, { kind: 'york', spin: -0.2 });
    // cracked crown at the centre
    W.shatter(ctx, W.W / 2, 250, 190, 0.18, (lx, x, y) => W.crown(lx, x, y, 130, { color: W.C.gold, width: 5, fill: 0.3 }), 9);
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(0, 640, W.W, 440);
    W.text(ctx, 'حروب الوردتين', W.W / 2, 790, { size: 230, color: W.C.ivory, glow: 'rgba(0,0,0,0.9)', glowBlur: 30 });
    W.text(ctx, 'الصراع الذي ألهم «صراع العروش»', W.W / 2, 960, { size: 64, fam: W.F.label, weight: 700, color: W.C.gold });
    W.vignette(ctx, 0.7);
  };
})();
