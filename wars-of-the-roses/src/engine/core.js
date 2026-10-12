/* Core of the motion system: constants, palette, easing, timing and drawing helpers.
   Everything is a pure function of time t (seconds) so any frame can be rendered in isolation. */
(function () {
  const W = (window.W = {});
  W.W = 1920;
  W.H = 1080;

  // ---- visual identity -------------------------------------------------------------
  W.C = {
    bg: '#0d0c0b',
    bgWarm: '#1c1712',
    ivory: '#efe6d2',
    ivoryDim: 'rgba(239,230,210,0.55)',
    ivoryFaint: 'rgba(239,230,210,0.16)',
    crimson: '#a3192a',
    crimsonBright: '#cf2a3c',
    crimsonDeep: '#5c0d16',
    gold: '#c9a45c',
    goldDim: 'rgba(201,164,92,0.55)',
    mute: '#8a7f70',
    land: '#1b1814',
    landEdge: '#2a251f',
    ink: '#0d0c0b',
  };
  W.F = {
    title: 'Amiri', // Naskh serif for headlines and names
    label: 'Reem Kufi', // geometric Kufi for labels, captions, UI
    latin: 'Cinzel', // classical capitals for numerals / Latin subtitles
  };

  // ---- math -----------------------------------------------------------------------
  W.clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  W.lerp = (a, b, p) => a + (b - a) * p;
  W.mix = (p, a, b) => a + (b - a) * p;
  W.map = (v, a, b, c, d) => c + ((v - a) / (b - a)) * (d - c);
  W.E = {
    linear: (x) => x,
    inQuad: (x) => x * x,
    outQuad: (x) => 1 - (1 - x) * (1 - x),
    inOut: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    out: (x) => 1 - Math.pow(1 - x, 3),
    outExpo: (x) => (x === 1 ? 1 : 1 - Math.pow(2, -10 * x)),
    inOutSine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
    inCubic: (x) => x * x * x,
    outBack: (x) => {
      const c1 = 1.25, c3 = c1 + 1;
      return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
    },
  };
  /** progress of t through [a, a+d], eased */
  W.p = (t, a, d = 0.8, ease = W.E.out) => ease(W.clamp((t - a) / d));
  /** envelope: fades in at a over fin, out at b over fout */
  W.env = (t, a, b, fin = 0.6, fout = 0.6) =>
    Math.min(W.p(t, a, fin, W.E.inOutSine), 1 - W.p(t, b - fout, fout, W.E.inOutSine));

  // deterministic random
  W.rng = (seed) => {
    let a = seed >>> 0;
    return () => {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  W.hash = (n) => {
    const s = Math.sin(n * 127.1 + 311.7) * 43758.5453;
    return s - Math.floor(s);
  };
  // smooth value noise (1D)
  W.noise = (x, seed = 0) => {
    const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
    return W.lerp(W.hash(i + seed * 57), W.hash(i + 1 + seed * 57), u);
  };

  // ---- canvas helpers -------------------------------------------------------------
  /** run fn with alpha multiplied (never overriding parent alpha) */
  W.alpha = (ctx, a, fn) => {
    if (a <= 0.001) return;
    ctx.save();
    ctx.globalAlpha *= W.clamp(a);
    fn();
    ctx.restore();
  };
  W.with = (ctx, fn) => { ctx.save(); fn(); ctx.restore(); };
  W.font = (size, fam = W.F.title, weight = 700) => `${weight} ${size}px "${fam}"`;
  W.rgba = (hex, a) => {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  };
  W.mixColor = (h1, h2, p) => {
    const a = parseInt(h1.slice(1), 16), b = parseInt(h2.slice(1), 16);
    const c = (s) => Math.round(W.lerp((a >> s) & 255, (b >> s) & 255, p));
    return `rgb(${c(16)},${c(8)},${c(0)})`;
  };

  // reusable offscreen layers
  const pool = {};
  W.layer = (key, w = W.W, h = W.H) => {
    let c = pool[key];
    if (!c || c.width !== w || c.height !== h) {
      c = pool[key] = document.createElement('canvas');
      c.width = w; c.height = h;
    }
    const x = c.getContext('2d');
    x.setTransform(1, 0, 0, 1, 0, 0);
    x.globalAlpha = 1;
    x.globalCompositeOperation = 'source-over';
    x.filter = 'none';
    x.clearRect(0, 0, w, h);
    return [c, x];
  };

  // ---- lines ----------------------------------------------------------------------
  W.polyLen = (pts) => {
    let L = 0;
    for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    return L;
  };
  /** points of a polyline truncated at fraction p of its length */
  W.polyPart = (pts, p) => {
    if (p >= 1) return pts.slice();
    const L = W.polyLen(pts) * W.clamp(p);
    const out = [pts[0]];
    let acc = 0;
    for (let i = 1; i < pts.length; i++) {
      const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      if (acc + d >= L) {
        const f = d ? (L - acc) / d : 0;
        out.push([W.lerp(pts[i - 1][0], pts[i][0], f), W.lerp(pts[i - 1][1], pts[i][1], f)]);
        return out;
      }
      acc += d;
      out.push(pts[i]);
    }
    return out;
  };
  W.strokePoly = (ctx, pts, p = 1, o = {}) => {
    if (p <= 0 || pts.length < 2) return null;
    const part = W.polyPart(pts, p);
    ctx.save();
    ctx.strokeStyle = o.color || W.C.ivory;
    ctx.lineWidth = o.width || 2;
    ctx.lineCap = o.cap || 'round';
    ctx.lineJoin = 'round';
    if (o.dash) { ctx.setLineDash(o.dash); ctx.lineDashOffset = o.dashOffset || 0; }
    if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.glowBlur || 12; }
    ctx.beginPath();
    part.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])));
    if (o.close && p >= 1) ctx.closePath();
    ctx.stroke();
    ctx.restore();
    return part[part.length - 1];
  };
  /** quadratic curve sampled to points (for routes / arcs) */
  W.arcPts = (a, b, bend = 0.2, n = 48) => {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const cx = mx - dy * bend, cy = my + dx * bend;
    const out = [];
    for (let i = 0; i <= n; i++) {
      const t = i / n, u = 1 - t;
      out.push([u * u * a[0] + 2 * u * t * cx + t * t * b[0], u * u * a[1] + 2 * u * t * cy + t * t * b[1]]);
    }
    return out;
  };
  W.arrowHead = (ctx, tip, from, size = 14, color = W.C.ivory) => {
    const ang = Math.atan2(tip[1] - from[1], tip[0] - from[0]);
    ctx.save();
    ctx.fillStyle = color;
    ctx.translate(tip[0], tip[1]);
    ctx.rotate(ang);
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-size, -size * 0.45);
    ctx.lineTo(-size * 0.7, 0);
    ctx.lineTo(-size, size * 0.45);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  };
  /** thin hairline that grows from its centre */
  W.hairline = (ctx, x, y, w, p, color = W.C.ivoryDim, width = 1.5) => {
    if (p <= 0) return;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.moveTo(x - (w / 2) * p, y);
    ctx.lineTo(x + (w / 2) * p, y);
    ctx.stroke();
    ctx.restore();
  };
  /** small diamond ornament */
  W.diamond = (ctx, x, y, r, color = W.C.gold, fill = true) => {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.closePath();
    if (fill) { ctx.fillStyle = color; ctx.fill(); } else { ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.stroke(); }
    ctx.restore();
  };
})();
