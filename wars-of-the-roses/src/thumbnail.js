/* YouTube thumbnail (1920x1080, exported as 1280x720) in the film's manuscript style.
   Rendered by: node scripts/render.mjs --thumbnail */
(function () {
  const { W } = window;
  W.drawThumbnail = (ctx) => {
    W.background(ctx, 0, {});
    ctx.strokeStyle = W.C.gold; ctx.lineWidth = 8; ctx.strokeRect(60, 60, W.W - 120, W.H - 120);
    ctx.strokeStyle = W.C.crimson; ctx.lineWidth = 3; ctx.strokeRect(84, 84, W.W - 168, W.H - 168);
    W.rose(ctx, 380, 420, 230, { kind: 'york' });
    W.rose(ctx, 1540, 420, 230, { kind: 'lancaster' });
    W.crown(ctx, W.W / 2, 300, 120, { color: W.C.gold, width: 6, fill: 0.4 });
    W.words(ctx, 'حروب الوردتين', W.W / 2, 690, 99, [0, 0], { size: 230, colors: [W.C.ivory, W.C.crimson] });
    W.text(ctx, 'الصراع الذي ألهم «صراع العروش»', W.W / 2, 905, { size: 70, fam: W.F.title, weight: 700, color: W.C.ivory });
    W.vignette(ctx, 0.8);
  };
})();
