/* Engraved "bestiary" illustrations for the cold open: a heraldic dragon and a frost king.
   Drawn as ink line-work with hatching and a watercolour wash, like a manuscript marginal. */
(function () {
  const { W } = window;
  const INK = '#2a1f16';

  // Catmull-Rom spline through points -> dense polyline
  function spline(pts, seg = 10, closed = false) {
    const P = closed ? [pts[pts.length - 1], ...pts, pts[0], pts[1]] : [pts[0], ...pts, pts[pts.length - 1]];
    const out = [];
    for (let i = 1; i < P.length - 2; i++) {
      const [p0, p1, p2, p3] = [P[i - 1], P[i], P[i + 1], P[i + 2]];
      for (let k = 0; k < seg; k++) {
        const t = k / seg, t2 = t * t, t3 = t2 * t;
        out.push([0, 1].map((d) => 0.5 * (2 * p1[d] + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3)));
      }
    }
    out.push(closed ? pts[0] : pts[pts.length - 1]);
    return out;
  }
  const poly = (ctx, pts, close = true) => {
    ctx.beginPath();
    pts.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])));
    if (close) ctx.closePath();
  };
  const mirror = (pts) => pts.map(([x, y]) => [-x, y]);
  /** parallel hatching inside the current clip */
  function hatch(ctx, x0, y0, x1, y1, step, ang, col, w = 1) {
    ctx.save();
    ctx.strokeStyle = col;
    ctx.lineWidth = w;
    ctx.beginPath();
    const c = Math.cos(ang), s = Math.sin(ang), L = Math.hypot(x1 - x0, y1 - y0);
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    for (let d = -L; d <= L; d += step) {
      ctx.moveTo(cx + c * -L - s * d, cy + s * -L + c * d);
      ctx.lineTo(cx + c * L - s * d, cy + s * L + c * d);
    }
    ctx.stroke();
    ctx.restore();
  }
  /** outline of a tube along a spine with a width profile */
  function tube(spinePts, widthFn) {
    const n = spinePts.length, L = [], R = [];
    for (let i = 0; i < n; i++) {
      const a = spinePts[Math.max(0, i - 1)], b = spinePts[Math.min(n - 1, i + 1)];
      const ang = Math.atan2(b[1] - a[1], b[0] - a[0]) + Math.PI / 2;
      const w = widthFn(i / (n - 1));
      L.push([spinePts[i][0] + Math.cos(ang) * w, spinePts[i][1] + Math.sin(ang) * w]);
      R.push([spinePts[i][0] - Math.cos(ang) * w, spinePts[i][1] - Math.sin(ang) * w]);
    }
    return { L, R, outline: [...L, ...R.reverse()] };
  }

  // =========================================================== heraldic dragon
  /** facing right. o.flap 0..1 (wing raised..lowered), o.wash body colour */
  W.bestiaryDragon = (ctx, x, y, s, t, o = {}) => {
    const wash = o.wash || 'rgba(160,40,30,0.62)';
    const wingWash = o.wingWash || 'rgba(160,40,30,0.38)';
    const belly = 'rgba(205,160,80,0.75)';
    const flap = o.flap == null ? 0.2 : o.flap;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    const lw = (v) => v / s;

    // ---- wing (drawn twice: far wing first, smaller and lagging)
    const wing = (far) => {
      const sh = far ? [70, -10] : [30, 20];
      const lift = far ? flap * 0.8 + 0.1 : flap;
      const rot = -0.35 + lift * 0.9;
      const R = ([px, py]) => {
        const dx = px - sh[0], dy = py - sh[1], c = Math.cos(rot), sn = Math.sin(rot);
        return [sh[0] + dx * c - dy * sn, sh[1] + dx * sn + dy * c];
      };
      const k = far ? 1.05 : 1.35;
      const wr = R([sh[0] - 40 * k, sh[1] - 230 * k]);
      const tips = [[sh[0] + 120 * k, sh[1] - 370 * k], [sh[0] - 90 * k, sh[1] - 400 * k], [sh[0] - 250 * k, sh[1] - 330 * k], [sh[0] - 340 * k, sh[1] - 190 * k]].map(R);
      const att = [far ? -90 : -150, far ? 40 : 70];
      // membrane with concave scallops
      const mem = [sh, wr, tips[0]];
      const seq = [...tips, att];
      for (let i = 1; i < seq.length; i++) {
        const a = seq[i - 1], b = seq[i];
        for (let q = 1; q <= 12; q++) {
          const u = q / 12, bow = Math.sin(u * Math.PI) * (i === seq.length - 1 ? 0.15 : 0.42);
          const mx = W.lerp(a[0], b[0], u), my = W.lerp(a[1], b[1], u);
          mem.push([W.lerp(mx, wr[0], bow), W.lerp(my, wr[1], bow)]);
        }
      }
      poly(ctx, mem);
      ctx.fillStyle = far ? 'rgba(130,35,28,0.35)' : wingWash;
      ctx.fill();
      // membrane fold lines (hatching inside the membrane)
      ctx.save();
      poly(ctx, mem); ctx.clip();
      ctx.strokeStyle = 'rgba(42,31,22,0.28)'; ctx.lineWidth = lw(1);
      for (const f of tips) for (let q = 1; q <= 3; q++) {
        ctx.beginPath();
        const fx = W.lerp(wr[0], f[0], 1), fy = W.lerp(wr[1], f[1], 1);
        ctx.moveTo(wr[0], wr[1]);
        ctx.quadraticCurveTo(W.lerp(wr[0], fx, 0.5) + q * 14, W.lerp(wr[1], fy, 0.5) + q * 22, att[0] * 0.3 + fx * 0.7, att[1] * 0.3 + fy * 0.7 + q * 30);
        ctx.stroke();
      }
      ctx.restore();
      poly(ctx, mem);
      ctx.strokeStyle = INK; ctx.lineWidth = lw(2.2); ctx.stroke();
      // arm + finger bones
      ctx.strokeStyle = INK; ctx.lineWidth = lw(5);
      ctx.beginPath(); ctx.moveTo(sh[0], sh[1]); ctx.quadraticCurveTo(sh[0] + 30, (sh[1] + wr[1]) / 2, wr[0], wr[1]); ctx.stroke();
      ctx.lineWidth = lw(2.6);
      for (const f of tips) { ctx.beginPath(); ctx.moveTo(wr[0], wr[1]); ctx.quadraticCurveTo((wr[0] + f[0]) / 2 + 10, (wr[1] + f[1]) / 2 - 12, f[0], f[1]); ctx.stroke(); }
      // claws at the wrist and tips
      ctx.fillStyle = INK;
      ctx.beginPath(); ctx.moveTo(wr[0], wr[1]); ctx.lineTo(wr[0] + 22, wr[1] - 26); ctx.lineTo(wr[0] + 8, wr[1] + 4); ctx.fill();
    };
    wing(true);

    // ---- body: tail curl -> hips -> belly -> arched neck
    const spinePts = spline([[-470, 150], [-500, 90], [-470, 40], [-410, 40], [-370, 90], [-300, 140], [-200, 135], [-110, 90], [-20, 60], [60, 40], [115, -10], [140, -80], [150, -150], [185, -205], [235, -222]], 10);
    const prof = (u) => (u < 0.25 ? W.lerp(2, 12, u / 0.25) : u < 0.55 ? W.lerp(12, 48, (u - 0.25) / 0.3) : u < 0.72 ? W.lerp(48, 40, (u - 0.55) / 0.17) : W.lerp(40, 20, (u - 0.72) / 0.28));
    const body = tube(spinePts, prof);
    // legs behind the body
    const leg = (hip, knee, foot, far) => {
      const thick = far ? 13 : 17;
      const tb = tube(spline([hip, knee, foot], 8), (u) => W.lerp(thick, 7, u));
      poly(ctx, tb.outline);
      ctx.fillStyle = far ? 'rgba(130,35,28,0.55)' : wash; ctx.fill();
      ctx.strokeStyle = INK; ctx.lineWidth = lw(2); ctx.stroke();
      // claws
      ctx.strokeStyle = INK; ctx.lineWidth = lw(2.4);
      for (let c = -1; c <= 1; c++) { ctx.beginPath(); ctx.moveTo(foot[0], foot[1]); ctx.quadraticCurveTo(foot[0] + 14 + c * 6, foot[1] + 4 + c * 10, foot[0] + 22 + c * 4, foot[1] + 14 + c * 12); ctx.stroke(); }
    };
    leg([-170, 140], [-130, 205], [-175, 250], true);
    leg([50, 50], [80, 120], [55, 175], true);
    poly(ctx, body.outline);
    ctx.fillStyle = wash; ctx.fill();
    // belly band (ochre) = strip between spine and the right-hand edge
    const bandOuter = tube(spinePts, (u) => prof(u)).R.slice().reverse();
    const bandInner = tube(spinePts, (u) => prof(u) * 0.35).R.slice().reverse();
    const band = [...bandOuter.slice(30, spinePts.length - 8), ...bandInner.slice(30, spinePts.length - 8).reverse()];
    poly(ctx, band);
    ctx.fillStyle = belly; ctx.fill();
    ctx.strokeStyle = 'rgba(42,31,22,0.45)'; ctx.lineWidth = lw(1.2);
    for (let i = 30; i < spinePts.length - 8; i += 3) {
      ctx.beginPath(); ctx.moveTo(bandOuter[i][0], bandOuter[i][1]); ctx.lineTo(bandInner[i][0], bandInner[i][1]); ctx.stroke();
    }
    // scale hatching on the back half
    ctx.save();
    poly(ctx, body.outline); ctx.clip();
    const upper = tube(spinePts, (u) => prof(u) * 0.55).L;
    ctx.strokeStyle = 'rgba(42,31,22,0.35)'; ctx.lineWidth = lw(1);
    for (let i = 6; i < spinePts.length - 4; i += 2) {
      const q = upper[i];
      ctx.beginPath(); ctx.arc(q[0], q[1], 7, 0.2, Math.PI - 0.2); ctx.stroke();
    }
    ctx.restore();
    poly(ctx, body.outline);
    ctx.strokeStyle = INK; ctx.lineWidth = lw(2.4); ctx.stroke();
    // dorsal spines along the back edge
    ctx.fillStyle = INK;
    for (let i = 12; i < spinePts.length - 6; i += 5) {
      const a = body.L[i], b = body.L[i + 2] || a;
      const ang = Math.atan2(b[1] - a[1], b[0] - a[0]) - Math.PI / 2;
      const h = 10 + prof(i / spinePts.length) * 0.35;
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo((a[0] + b[0]) / 2 + Math.cos(ang) * h, (a[1] + b[1]) / 2 + Math.sin(ang) * h); ctx.lineTo(b[0], b[1]); ctx.closePath(); ctx.fill();
    }
    // arrow-head tail tip
    const tt = spinePts[0];
    ctx.beginPath(); ctx.moveTo(tt[0] + 6, tt[1] - 4); ctx.lineTo(tt[0] - 18, tt[1] + 26); ctx.lineTo(tt[0] + 22, tt[1] + 14); ctx.closePath();
    ctx.fillStyle = wash; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = lw(2); ctx.stroke();
    // near legs over the body
    leg([-200, 150], [-160, 215], [-210, 262], false);
    leg([70, 55], [115, 120], [95, 180], false);

    // ---- head (open jaws, horns, eye)
    const hx = 235, hy = -222;
    const upperJaw = spline([[hx - 30, hy - 25], [hx + 20, hy - 34], [hx + 70, hy - 26], [hx + 112, hy - 12], [hx + 118, hy - 2], [hx + 60, hy - 4], [hx + 10, hy + 4]], 6);
    const lowerJaw = spline([[hx + 10, hy + 4], [hx + 60, hy + 14], [hx + 100, hy + 30], [hx + 96, hy + 38], [hx + 40, hy + 34], [hx - 20, hy + 22]], 6);
    const head = [...upperJaw, ...lowerJaw, [hx - 34, hy + 10]];
    poly(ctx, head); ctx.fillStyle = wash; ctx.fill();
    // mouth interior + teeth
    poly(ctx, [[hx + 10, hy + 4], [hx + 116, hy - 2], [hx + 96, hy + 30]]); ctx.fillStyle = 'rgba(90,15,10,0.85)'; ctx.fill();
    ctx.fillStyle = '#f4ecd8';
    for (let k = 0; k < 5; k++) {
      const u = 0.2 + k * 0.17, tx = W.lerp(hx + 20, hx + 112, u), ty = W.lerp(hy - 1, hy - 4, u);
      ctx.beginPath(); ctx.moveTo(tx - 4, ty); ctx.lineTo(tx, ty + 10); ctx.lineTo(tx + 4, ty); ctx.fill();
      const by = W.lerp(hy + 10, hy + 30, u);
      ctx.beginPath(); ctx.moveTo(tx - 4, by); ctx.lineTo(tx - 2, by - 9); ctx.lineTo(tx + 3, by); ctx.fill();
    }
    poly(ctx, head); ctx.strokeStyle = INK; ctx.lineWidth = lw(2.4); ctx.stroke();
    // tongue (forked)
    ctx.strokeStyle = W.C.crimson; ctx.lineWidth = lw(3);
    ctx.beginPath(); ctx.moveTo(hx + 50, hy + 14); ctx.quadraticCurveTo(hx + 120, hy + 20, hx + 150, hy + 2); ctx.moveTo(hx + 150, hy + 2); ctx.lineTo(hx + 166, hy - 8); ctx.moveTo(hx + 150, hy + 2); ctx.lineTo(hx + 168, hy + 10); ctx.stroke();
    // horns sweeping back
    for (const [ox, len, cv] of [[-10, 90, -30], [10, 70, -22]]) {
      poly(ctx, spline([[hx + ox - 8, hy - 26], [hx + ox - len * 0.5, hy - 40 + cv], [hx + ox - len, hy - 30 + cv * 1.6], [hx + ox - len * 0.45, hy - 32 + cv * 0.6], [hx + ox + 6, hy - 24]], 5));
      ctx.fillStyle = 'rgba(225,205,160,0.95)'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = lw(1.8); ctx.stroke();
    }
    // eye + brow + nostril + cheek ridge
    ctx.fillStyle = '#e8b13a'; ctx.beginPath(); ctx.ellipse(hx + 30, hy - 14, 9, 6, -0.2, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = INK; ctx.lineWidth = lw(1.8); ctx.stroke();
    ctx.fillStyle = INK; ctx.beginPath(); ctx.ellipse(hx + 31, hy - 14, 2.2, 5, 0, 0, Math.PI * 2); ctx.fill();
    ctx.lineWidth = lw(2.2);
    ctx.beginPath(); ctx.moveTo(hx + 14, hy - 26); ctx.quadraticCurveTo(hx + 34, hy - 32, hx + 50, hy - 22); ctx.stroke();
    ctx.beginPath(); ctx.arc(hx + 104, hy - 16, 3, 0, Math.PI * 2); ctx.stroke();
    ctx.lineWidth = lw(1.2);
    ctx.beginPath(); ctx.moveTo(hx - 20, hy + 6); ctx.quadraticCurveTo(hx + 10, hy + 18, hx + 40, hy + 26); ctx.stroke();
    // flame breath in red & ochre ink tongues
    const fb = o.fire || 0;
    if (fb > 0) {
      for (let k = 0; k < 7; k++) {
        const ph = t * 3 + k * 0.9;
        const len = (230 + 90 * Math.sin(ph)) * fb, ang = 0.18 + (k - 3) * 0.1 + Math.sin(ph * 1.3) * 0.05;
        const bx = hx + 120, by = hy + 6;
        const ex = bx + Math.cos(ang) * len, ey = by + Math.sin(ang) * len;
        const nx = -Math.sin(ang), ny = Math.cos(ang);
        ctx.beginPath();
        ctx.moveTo(bx, by);
        ctx.quadraticCurveTo((bx + ex) / 2 + nx * 34 * (0.6 + 0.4 * Math.sin(ph * 2)), (by + ey) / 2 + ny * 34 * (0.6 + 0.4 * Math.sin(ph * 2)), ex, ey);
        ctx.quadraticCurveTo((bx + ex) / 2 - nx * 22, (by + ey) / 2 - ny * 22, bx, by + 6);
        ctx.fillStyle = k % 2 ? 'rgba(214,140,40,0.75)' : 'rgba(180,38,30,0.7)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(42,31,22,0.6)'; ctx.lineWidth = lw(1.2); ctx.stroke();
      }
    }
    wing(false);
    ctx.restore();
  };

  // =========================================================== frost king (engraved bust)
  W.frostKing = (ctx, x, y, s, t, o = {}) => {
    const skin = o.skin || 'rgba(170,192,212,0.75)';
    const eyes = o.eyes == null ? 1 : o.eyes;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    const lw = (v) => v / s;

    // ---- shoulders: ragged cloak + armour
    const cloakL = [[-58, 150], [-90, 190], [-210, 220], [-300, 280], [-345, 380], [-360, 470], [-320, 455], [-300, 485], [-260, 462], [-230, 492], [-190, 468], [-150, 494], [-100, 470], [-50, 490], [0, 472]];
    const cloak = spline([...cloakL, ...mirror(cloakL).reverse().slice(1)], 6);
    poly(ctx, cloak);
    ctx.fillStyle = 'rgba(60,72,88,0.72)'; ctx.fill();
    ctx.save(); poly(ctx, cloak); ctx.clip();
    hatch(ctx, -380, 150, 380, 500, 9, 0.9, 'rgba(42,31,22,0.28)');
    ctx.restore();
    poly(ctx, cloak); ctx.strokeStyle = INK; ctx.lineWidth = lw(2.2); ctx.stroke();
    // pauldrons
    for (const d of [-1, 1]) {
      for (let k = 0; k < 3; k++) {
        const cx = d * (190 + k * 34), cy = 250 + k * 34, rx = 110 - k * 14, ry = 52 - k * 6;
        ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, d * 0.45, Math.PI, 0); ctx.closePath();
        ctx.fillStyle = 'rgba(115,135,155,0.85)'; ctx.fill();
        ctx.strokeStyle = INK; ctx.lineWidth = lw(2); ctx.stroke();
      }
    }
    // neck
    const neck = [[-52, 110], [-58, 200], [58, 200], [52, 110]];
    poly(ctx, neck); ctx.fillStyle = skin; ctx.fill();
    ctx.save(); poly(ctx, neck); ctx.clip(); hatch(ctx, -60, 110, 60, 200, 6, -0.6, 'rgba(42,31,22,0.35)'); ctx.restore();
    poly(ctx, neck); ctx.strokeStyle = INK; ctx.lineWidth = lw(2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-20, 150); ctx.lineTo(-24, 196); ctx.moveTo(20, 150); ctx.lineTo(24, 196); ctx.lineWidth = lw(1.2); ctx.stroke();

    // ---- crown of ice horns ringing the skull (behind the face outline)
    const horns = [];
    for (let i = 0; i < 11; i++) {
      const u = i / 10, a = W.lerp(-2.55, -0.59, u);
      const bx = Math.cos(a) * 108, by = -70 + Math.sin(a) * 118;
      const len = [58, 74, 86, 70, 92, 104, 92, 70, 86, 74, 58][i];
      const ang = a + (u - 0.5) * 0.25;
      horns.push({ bx, by, tx: bx + Math.cos(ang) * len, ty: by + Math.sin(ang) * len, w: 9 + (1 - Math.abs(u - 0.5)) * 5 });
    }
    for (const h of horns) {
      const nx = -(h.ty - h.by), ny = h.tx - h.bx, nl = Math.hypot(nx, ny);
      const ox = (nx / nl) * h.w, oy = (ny / nl) * h.w;
      ctx.beginPath();
      ctx.moveTo(h.bx - ox, h.by - oy);
      ctx.quadraticCurveTo((h.bx + h.tx) / 2 - ox * 0.6, (h.by + h.ty) / 2 - oy * 0.6 - 6, h.tx, h.ty);
      ctx.quadraticCurveTo((h.bx + h.tx) / 2 + ox * 0.4, (h.by + h.ty) / 2 + oy * 0.4, h.bx + ox, h.by + oy);
      ctx.closePath();
      ctx.fillStyle = 'rgba(214,230,240,0.95)'; ctx.fill();
      ctx.strokeStyle = INK; ctx.lineWidth = lw(1.8); ctx.stroke();
      ctx.strokeStyle = 'rgba(42,31,22,0.35)'; ctx.lineWidth = lw(1);
      ctx.beginPath(); ctx.moveTo(h.bx, h.by); ctx.lineTo(W.lerp(h.bx, h.tx, 0.8), W.lerp(h.by, h.ty, 0.8)); ctx.stroke();
    }

    // ---- face
    const faceL = [[0, -190], [-62, -180], [-102, -138], [-116, -78], [-114, -20], [-104, 30], [-86, 74], [-62, 112], [-32, 140], [0, 150]];
    const face = spline([...faceL, ...mirror(faceL).reverse().slice(1, -1)], 8, true);
    poly(ctx, face); ctx.fillStyle = skin; ctx.fill();
    // shading: one side hatched, cheek hollows, eye sockets
    ctx.save();
    poly(ctx, face); ctx.clip();
    ctx.save(); ctx.beginPath(); ctx.rect(-130, -200, 70, 360); ctx.clip(); hatch(ctx, -130, -200, -60, 160, 6, -0.9, 'rgba(42,31,22,0.32)'); ctx.restore();
    for (const d of [-1, 1]) {
      ctx.save(); ctx.beginPath(); ctx.ellipse(d * 70, 50, 26, 42, d * 0.3, 0, Math.PI * 2); ctx.clip(); hatch(ctx, d * 70 - 30, 0, d * 70 + 30, 100, 5, 0.7 * d, 'rgba(42,31,22,0.45)'); ctx.restore();
      ctx.save(); ctx.beginPath(); ctx.ellipse(d * 42, -30, 34, 22, 0, 0, Math.PI * 2); ctx.clip(); hatch(ctx, d * 42 - 36, -54, d * 42 + 36, -6, 4, 0.2, 'rgba(42,31,22,0.55)'); ctx.restore();
    }
    ctx.restore();
    poly(ctx, face); ctx.strokeStyle = INK; ctx.lineWidth = lw(2.4); ctx.stroke();
    ctx.strokeStyle = INK;
    // brow ridges
    ctx.lineWidth = lw(2.6);
    for (const d of [-1, 1]) { ctx.beginPath(); ctx.moveTo(d * 12, -58); ctx.quadraticCurveTo(d * 44, -70, d * 82, -48); ctx.stroke(); }
    // eyes: burning blue
    for (const d of [-1, 1]) {
      ctx.beginPath(); ctx.moveTo(d * 20, -30); ctx.quadraticCurveTo(d * 42, -44, d * 66, -30); ctx.quadraticCurveTo(d * 42, -20, d * 20, -30); ctx.closePath();
      ctx.fillStyle = W.rgba('#f2f7fb', 1); ctx.fill();
      ctx.fillStyle = `rgba(30,90,190,${0.25 + 0.75 * eyes})`;
      ctx.beginPath(); ctx.arc(d * 43, -31, 8, 0, Math.PI * 2); ctx.fill();
      if (eyes > 0) {
        const g = ctx.createRadialGradient(d * 43, -31, 0, d * 43, -31, 34);
        g.addColorStop(0, `rgba(60,140,230,${0.45 * eyes})`); g.addColorStop(1, 'rgba(60,140,230,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(d * 43, -31, 34, 0, Math.PI * 2); ctx.fill();
      }
      ctx.strokeStyle = INK; ctx.lineWidth = lw(1.8);
      ctx.beginPath(); ctx.moveTo(d * 20, -30); ctx.quadraticCurveTo(d * 42, -44, d * 66, -30); ctx.quadraticCurveTo(d * 42, -20, d * 20, -30); ctx.stroke();
    }
    // nose, nostrils, mouth, chin & cheekbone lines
    ctx.lineWidth = lw(2);
    ctx.beginPath(); ctx.moveTo(-6, -40); ctx.quadraticCurveTo(-12, 0, -14, 32); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(-16, 36); ctx.quadraticCurveTo(0, 46, 16, 36); ctx.stroke();
    ctx.lineWidth = lw(2.4);
    ctx.beginPath(); ctx.moveTo(-34, 86); ctx.quadraticCurveTo(0, 80, 34, 88); ctx.stroke();
    ctx.lineWidth = lw(1.3);
    ctx.beginPath(); ctx.moveTo(-22, 100); ctx.quadraticCurveTo(0, 106, 22, 100); ctx.stroke();
    for (const d of [-1, 1]) { ctx.beginPath(); ctx.moveTo(d * 98, -6); ctx.quadraticCurveTo(d * 78, 20, d * 52, 30); ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(-14, 126); ctx.quadraticCurveTo(0, 132, 14, 126); ctx.stroke();
    // forehead creases
    for (let k = 0; k < 3; k++) { ctx.beginPath(); ctx.moveTo(-40 + k * 4, -102 - k * 14); ctx.quadraticCurveTo(0, -110 - k * 14, 40 - k * 4, -102 - k * 14); ctx.stroke(); }
    ctx.restore();
  };
})();
