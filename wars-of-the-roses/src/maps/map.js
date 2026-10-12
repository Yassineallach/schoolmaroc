/* Animated engraved-style map: projection, land masses, markers, routes. */
(function () {
  const { W } = window;
  const COSLAT = Math.cos((53.5 * Math.PI) / 180);

  /** view: {lon, lat, k}  k = pixels per degree of latitude */
  W.proj = (view, ll) => [W.W / 2 + (ll[0] - view.lon) * COSLAT * view.k, W.H / 2 - (ll[1] - view.lat) * view.k];
  W.lerpView = (a, b, p) => ({ lon: W.lerp(a.lon, b.lon, p), lat: W.lerp(a.lat, b.lat, p), k: W.lerp(a.k, b.k, p) });
  W.VIEWS = {
    england: { lon: -2.2, lat: 53.0, k: 175 },
    englandTight: { lon: -1.6, lat: 52.7, k: 230 },
    north: { lon: -1.6, lat: 53.6, k: 300 },
    south: { lon: -1.4, lat: 51.9, k: 300 },
    isles: { lon: -4.2, lat: 53.6, k: 118 },
    channel: { lon: -2.4, lat: 51.0, k: 120 },
    wide: { lon: -3.0, lat: 52.6, k: 92 },
  };
  const P = (view, k) => W.proj(view, W.PLACES[k].ll);
  W.place = P;

  function path(ctx, view, pts, close = true) {
    ctx.beginPath();
    pts.forEach((ll, i) => {
      const [x, y] = W.proj(view, ll);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    if (close) ctx.closePath();
  }

  /**
   * o.reveal 0..1 draws the coastlines progressively
   * o.ireland, o.continent booleans (or 0..1 opacity)
   * o.tint {region:'england'|'france', color, a}
   */
  W.drawMap = (ctx, t, view, o = {}) => {
    const reveal = o.reveal == null ? 1 : o.reveal;
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    // engraved sea hatching
    ctx.strokeStyle = 'rgba(239,230,210,0.035)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let y = 4; y < W.H; y += 9) { ctx.moveTo(0, y); ctx.lineTo(W.W, y); }
    ctx.stroke();
    // graticule
    ctx.strokeStyle = 'rgba(239,230,210,0.05)';
    ctx.setLineDash([2, 6]);
    ctx.beginPath();
    for (let lon = -12; lon <= 10; lon += 2) { const [x1, y1] = W.proj(view, [lon, 44]); const [x2, y2] = W.proj(view, [lon, 61]); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); }
    for (let lat = 46; lat <= 60; lat += 2) { const [x1, y1] = W.proj(view, [-14, lat]); const [x2, y2] = W.proj(view, [12, lat]); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); }
    ctx.stroke();
    ctx.setLineDash([]);

    const masses = [['britain', 1], ['anglesey', 1], ['wight', 1]];
    if (o.ireland) masses.push(['ireland', o.ireland === true ? 1 : o.ireland]);
    if (o.continent) masses.push(['continent', o.continent === true ? 1 : o.continent]);

    const fillA = W.clamp(reveal * 1.4 - 0.4);
    for (const [name, ma] of masses) {
      const pts = W.GEO[name];
      ctx.save();
      ctx.globalAlpha *= ma;
      // coastal ripple lines in the sea (engraving)
      if (fillA > 0) {
        for (const [w, al] of [[22, 0.03], [12, 0.045], [5, 0.07]]) {
          path(ctx, view, pts);
          ctx.strokeStyle = `rgba(239,230,210,${al * fillA})`;
          ctx.lineWidth = w;
          ctx.stroke();
        }
        path(ctx, view, pts);
        const g = ctx.createLinearGradient(0, 0, 0, W.H);
        g.addColorStop(0, '#221e19');
        g.addColorStop(1, '#17140f');
        ctx.fillStyle = g;
        ctx.globalAlpha *= fillA;
        ctx.fill();
        ctx.globalAlpha /= fillA || 1;
      }
      // coastline line-draw
      const scr = pts.map((ll) => W.proj(view, ll));
      scr.push(scr[0]);
      W.strokePoly(ctx, scr, reveal, { color: 'rgba(239,230,210,0.72)', width: 1.6 });
      ctx.restore();
    }
    if (o.tint) {
      for (const tn of [].concat(o.tint)) {
        if (!tn || tn.a <= 0) continue;
        ctx.save();
        path(ctx, view, W.GEO[tn.region === 'france' ? 'continent' : tn.region === 'ireland' ? 'ireland' : 'britain']);
        ctx.clip();
        const c = tn.at ? W.proj(view, tn.at) : [W.W / 2, W.H / 2];
        const g = ctx.createRadialGradient(c[0], c[1], 0, c[0], c[1], tn.r || 600);
        g.addColorStop(0, W.rgba(tn.color || W.C.crimson, 0.42 * tn.a));
        g.addColorStop(1, W.rgba(tn.color || W.C.crimson, 0));
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W.W, W.H);
        ctx.restore();
      }
    }
    if (fillA > 0 && o.borders !== false) {
      for (const b of ['scotBorder', 'walesBorder']) {
        ctx.save();
        ctx.globalAlpha *= fillA * 0.5;
        path(ctx, view, W.GEO[b], false);
        ctx.setLineDash([3, 7]);
        ctx.strokeStyle = 'rgba(239,230,210,0.35)';
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.restore();
      }
    }
    if (o.regionLabels) {
      const lab = (txt, ll, al) => {
        const [x, y] = W.proj(view, ll);
        W.text(ctx, txt, x, y, { size: 30, fam: W.F.label, weight: 400, color: 'rgba(239,230,210,0.32)', alpha: al * fillA });
      };
      lab('إنجلترا', [-1.2, 52.25], 1);
      lab('ويلز', [-3.7, 52.3], 0.8);
      lab('اسكتلندا', [-3.9, 56.6], 0.8);
      if (o.ireland) lab('إيرلندا', [-8.3, 52.6], o.ireland === true ? 1 : o.ireland);
      if (o.continent) lab('فرنسا', [0.8, 48.3], o.continent === true ? 1 : o.continent);
      if (o.channel) lab('القناة الإنجليزية', [-2.0, 50.15], o.channel);
    }
    ctx.restore();
  };

  /** City / event marker with leader-line label. kind: 'city' | 'battle' | 'pulse' */
  W.marker = (ctx, x, y, t, t0, o = {}) => {
    const p = W.p(t, t0, 0.7, W.E.out);
    if (p <= 0) return;
    const a = (o.alpha == null ? 1 : o.alpha);
    const col = o.color || W.C.ivory;
    ctx.save();
    ctx.globalAlpha *= a;
    // expanding pulse rings
    const pt = t - t0;
    for (let i = 0; i < (o.rings == null ? 2 : o.rings); i++) {
      const q = ((pt * 0.6 + i * 0.5) % 1 + 1) % 1;
      ctx.strokeStyle = W.rgba(col.startsWith('#') ? col : W.C.ivory, (1 - q) * 0.5 * p);
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(x, y, 8 + q * 34, 0, Math.PI * 2); ctx.stroke();
    }
    if (o.kind === 'battle') {
      W.crossedSwords(ctx, x, y, 16 * W.E.outBack(p), { color: col, width: 2, fill: 0.25 });
    } else {
      ctx.fillStyle = W.C.bg;
      ctx.beginPath(); ctx.arc(x, y, 9 * p, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = col; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(x, y, 9 * p, 0, Math.PI * 2); ctx.stroke();
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.arc(x, y, 4 * p, 0, Math.PI * 2); ctx.fill();
    }
    if (o.label) {
      const side = o.side || 'right'; // label to the right or left of the point
      const dx = side === 'right' ? 1 : -1;
      const lp = W.p(t, t0 + 0.15, 0.6);
      const lx = x + dx * (o.dist || 70), ly = y + (o.dy || 0);
      ctx.strokeStyle = W.rgba(W.C.ivory, 0.45);
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x + dx * 14, y); ctx.lineTo(W.lerp(x + dx * 14, lx - dx * 8, lp), W.lerp(y, ly, lp)); ctx.stroke();
      const align = side === 'right' ? 'left' : 'right';
      W.text(ctx, o.label, lx, ly - (o.sub ? 14 : 0), { size: o.size || 34, fam: W.F.title, weight: 700, color: o.labelColor || W.C.ivory, align, reveal: lp, alpha: lp });
      if (o.sub) W.text(ctx, o.sub, lx, ly + 22, { size: o.subSize || 24, fam: W.F.label, weight: 400, color: o.subColor || W.C.gold, align, reveal: W.p(t, t0 + 0.35, 0.6), alpha: W.p(t, t0 + 0.35, 0.6) });
    }
    ctx.restore();
  };

  /** Animated route between screen points: dashes flow along the line, arrow at the head. */
  W.route = (ctx, pts, t, p, o = {}) => {
    if (p <= 0) return;
    const col = o.color || W.C.ivory;
    W.strokePoly(ctx, pts, p, { color: W.rgba(col.startsWith('#') ? col : W.C.ivory, 0.25), width: (o.width || 3) + 4 });
    const head = W.strokePoly(ctx, pts, p, { color: col, width: o.width || 3, dash: [14, 10], dashOffset: -t * 40 });
    if (o.arrow !== false && head && p > 0.02) {
      const part = W.polyPart(pts, p);
      const from = part[Math.max(0, part.length - 3)];
      W.arrowHead(ctx, head, from, 18, col);
    }
  };
})();
