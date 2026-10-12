/* Family trees, relationship links, battle formations, terrain. */
(function () {
  const { W } = window;

  // ---- dynastic tree --------------------------------------------------------------
  /**
   * nodes: { id: {x, y, label, sub, color, t, r, dead, crown, alpha, labelSize, halo} }
   * edges: [{ a, b, t, dur, color, style: 'elbow'|'straight'|'dash', width, alpha }]
   */
  W.tree = (ctx, t, nodes, edges, o = {}) => {
    for (const e of edges) {
      const A = nodes[e.a], B = nodes[e.b];
      if (!A || !B) continue;
      const p = W.p(t, e.t, e.dur || 0.9, W.E.inOut);
      if (p <= 0) continue;
      const ra = (A.r || 14) + 4, rb = (B.r || 14) + 4;
      let pts;
      if (e.style === 'straight' || e.style === 'dash' || e.style === 'marriage') {
        const ang = Math.atan2(B.y - A.y, B.x - A.x);
        pts = [[A.x + Math.cos(ang) * ra, A.y + Math.sin(ang) * ra], [B.x - Math.cos(ang) * rb, B.y - Math.sin(ang) * rb]];
      } else {
        const my = A.y + (B.y - A.y) * (e.mid || 0.5);
        pts = [[A.x, A.y + ra], [A.x, my], [B.x, my], [B.x, B.y - rb]];
      }
      ctx.save();
      ctx.globalAlpha *= e.alpha == null ? 1 : e.alpha;
      W.strokePoly(ctx, pts, p, {
        color: e.color || W.rgba(W.C.ivory, 0.5), width: e.width || 2,
        dash: e.style === 'dash' ? [6, 8] : e.style === 'marriage' ? [2, 6] : null,
        cap: 'butt',
      });
      ctx.restore();
    }
    for (const id in nodes) {
      const n = nodes[id];
      const p = W.p(t, n.t, 0.8, W.E.out);
      if (p <= 0) continue;
      const a = n.alpha == null ? 1 : n.alpha;
      ctx.save();
      ctx.globalAlpha *= a;
      W.node(ctx, n.x, n.y, n.r || 14, { p, color: n.color, dead: n.dead, crown: n.crown, crownColor: n.crownColor, halo: n.halo, filled: n.filled });
      const lp = W.p(t, n.t + 0.2, 0.7);
      const below = n.labelPos !== 'above';
      const ly = below ? n.y + (n.r || 14) + (n.labelGap || 36) : n.y - (n.r || 14) - (n.crown ? 70 : 34);
      if (n.label) W.text(ctx, n.label, n.x, ly, { size: n.labelSize || 32, fam: W.F.title, weight: 700, color: n.labelColor || W.C.ivory, alpha: lp, reveal: lp });
      if (n.sub) W.text(ctx, n.sub, n.x, ly + (below ? 36 : -36) * (n.labelSize ? n.labelSize / 32 : 1), { size: n.subSize || 22, fam: W.F.label, weight: 400, color: n.subColor || W.C.ivoryDim, alpha: W.p(t, n.t + 0.45, 0.7) });
      ctx.restore();
    }
  };

  // ---- battle diagrams -------------------------------------------------------------
  /** A formation block made of small unit marks. o.scatter 0..1 breaks it apart. */
  W.formation = (ctx, x, y, t, o = {}) => {
    const cols = o.cols || 8, rows = o.rows || 3, gap = o.gap || 16, u = o.unit || 9;
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0) return;
    const rnd = W.rng(o.seed || 1);
    const sc = o.scatter || 0;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.translate(x, y);
    ctx.rotate(o.angle || 0);
    const w = (cols - 1) * gap, h = (rows - 1) * gap;
    if (o.frame !== false) {
      ctx.strokeStyle = W.rgba(o.color || W.C.ivory, 0.35 * (1 - sc));
      ctx.lineWidth = 1;
      ctx.strokeRect(-w / 2 - u * 1.4, -h / 2 - u * 1.4, w + u * 2.8, h + u * 2.8);
    }
    for (let r = 0; r < rows; r++)
      for (let c = 0; c < cols; c++) {
        const jx = (rnd() - 0.5) * 2, jy = (rnd() - 0.5) * 2, jr = rnd();
        const px = -w / 2 + c * gap + jx * sc * 140 * (0.4 + jr) + (o.retreat || 0) * sc * 120;
        const py = -h / 2 + r * gap + jy * sc * 90 * (0.4 + jr);
        const wob = Math.sin(t * 3 + r + c * 0.7) * 0.6;
        ctx.fillStyle = o.color || W.C.ivory;
        ctx.globalAlpha = a * (1 - sc * (0.3 + jr * 0.7));
        ctx.save();
        ctx.translate(px, py + wob);
        ctx.rotate(sc * (jr - 0.5) * 2);
        ctx.fillRect(-u / 2, -u / 2, u, u * 0.62);
        ctx.restore();
      }
    ctx.restore();
  };

  /** contour-line terrain used under battle diagrams */
  W.terrain = (ctx, t, seed = 3, a = 1) => {
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.strokeStyle = 'rgba(239,230,210,0.06)';
    ctx.lineWidth = 1.2;
    for (let k = 0; k < 14; k++) {
      ctx.beginPath();
      for (let x = -20; x <= W.W + 20; x += 20) {
        const y = 120 + k * 72 + (W.noise(x / 260 + k * 0.37, seed) - 0.5) * 120 + Math.sin(x / 400 + k) * 18;
        x === -20 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    ctx.restore();
  };

  /** broad directional arrow for army movement */
  W.bigArrow = (ctx, from, to, p, o = {}) => {
    if (p <= 0) return;
    const col = o.color || W.C.ivory;
    const pts = W.arcPts(from, to, o.bend || 0.08, 30);
    W.strokePoly(ctx, pts, p, { color: W.rgba(col, 0.18), width: o.width || 26, cap: 'butt' });
    const head = W.strokePoly(ctx, pts, p, { color: W.rgba(col, 0.85), width: 3 });
    const part = W.polyPart(pts, p);
    if (head && part.length > 2) W.arrowHead(ctx, head, part[part.length - 3], 22, W.rgba(col, 0.9));
  };
})();
