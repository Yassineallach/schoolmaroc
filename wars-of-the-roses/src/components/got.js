/* "Ice & fire" kit for the opening: an original homage to the look of Game of Thrones —
   frost, a frost creature, a dragon, embers, hanging house banners, a bronze clockwork map,
   an astrolabe, gears, metallic type and a throne of swords. All procedural vector art. */
(function () {
  const { W } = window;
  const B = (W.BRONZE = { dark: '#2e2111', mid: '#8a6a3c', light: '#d6b47a', hi: '#f6e3b4', shadow: '#140d05' });
  W.ICE = { core: '#e8f8ff', glow: '#7fd0ff', deep: '#0b1a26' };

  // ---- frost -------------------------------------------------------------------
  let FROST = null;
  function buildFrost() {
    const r = W.rng(77), segs = [];
    const seeds = [];
    const edge = (n, f) => { for (let i = 0; i < n; i++) seeds.push(f(i / n + r() / n)); };
    edge(12, (u) => [0, u * W.H, 0]);
    edge(12, (u) => [W.W, u * W.H, Math.PI]);
    edge(16, (u) => [u * W.W, 0, Math.PI / 2]);
    edge(16, (u) => [u * W.W, W.H, -Math.PI / 2]);
    const grow = (x, y, ang, depth, dist) => {
      if (depth > 3) return;
      const len = (34 - depth * 6) * (0.7 + r() * 0.5);
      const n = depth === 0 ? 9 : 5 - depth;
      let cx = x, cy = y, d = dist;
      for (let k = 0; k < n; k++) {
        const nx = cx + Math.cos(ang) * len, ny = cy + Math.sin(ang) * len;
        segs.push({ a: [cx, cy], b: [nx, ny], d0: d, d1: d + len, depth });
        // ice branches at +-60 degrees, mirrored like a fern
        if (depth < 3) for (const sgn of [-1, 1]) if (r() < 0.8) grow(nx, ny, ang + sgn * Math.PI / 3, depth + 1, d + len);
        cx = nx; cy = ny; d += len;
      }
    };
    for (const [x, y, a] of seeds) grow(x, y, a + (r() - 0.5) * 0.6, 0, r() * 60);
    return segs;
  }
  /** g: 0..1 growth;  a: alpha */
  W.frost = (ctx, g, a = 1) => {
    if (g <= 0 || a <= 0) return;
    if (!FROST) FROST = buildFrost();
    const D = g * 420;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.lineCap = 'round';
    for (const pass of [0, 1]) {
      ctx.beginPath();
      for (const s of FROST) {
        if (s.d0 > D) continue;
        const f = W.clamp((D - s.d0) / (s.d1 - s.d0));
        ctx.moveTo(s.a[0], s.a[1]);
        ctx.lineTo(W.lerp(s.a[0], s.b[0], f), W.lerp(s.a[1], s.b[1], f));
      }
      ctx.strokeStyle = pass ? 'rgba(230,248,255,0.7)' : 'rgba(140,210,255,0.10)';
      ctx.lineWidth = pass ? 1.0 : 5;
      ctx.stroke();
    }
    // frosted edge haze
    const g2 = ctx.createRadialGradient(W.W / 2, W.H / 2, W.H * 0.25, W.W / 2, W.H / 2, W.W * 0.7);
    g2.addColorStop(0, 'rgba(120,190,240,0)');
    g2.addColorStop(1, `rgba(150,210,255,${0.22 * g})`);
    ctx.fillStyle = g2;
    ctx.fillRect(0, 0, W.W, W.H);
    ctx.restore();
  };

  // ---- frost creature (silhouette with an ice crown and burning blue eyes) ---------
  W.frostCreature = (ctx, x, y, s, t, o = {}) => {
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.translate(x, y);
    ctx.scale(s, s);
    const P = new Path2D();
    // shoulders & neck
    P.moveTo(-520, 560); P.bezierCurveTo(-470, 330, -260, 270, -120, 230);
    P.bezierCurveTo(-80, 200, -70, 150, -66, 110);
    // head (left side), crown of ice spikes over the top, right side
    P.bezierCurveTo(-112, 70, -118, -40, -100, -100);
    const spikes = [[-100, -100], [-150, -205], [-74, -140], [-92, -260], [-38, -165], [-30, -300], [0, -172], [32, -300], [40, -165], [94, -262], [76, -140], [152, -205], [100, -100]];
    spikes.forEach(([sx, sy]) => P.lineTo(sx, sy));
    P.bezierCurveTo(118, -40, 112, 70, 66, 110);
    P.bezierCurveTo(70, 150, 80, 200, 120, 230);
    P.bezierCurveTo(260, 270, 470, 330, 520, 560);
    P.closePath();
    if (o.fill) ctx.fillStyle = o.fill;
    else {
      const g = ctx.createLinearGradient(0, -300, 0, 560);
      g.addColorStop(0, '#1a2a36'); g.addColorStop(0.5, '#0a1218'); g.addColorStop(1, '#05080b');
      ctx.fillStyle = g;
    }
    ctx.fill(P);
    ctx.shadowColor = o.rim ? 'transparent' : 'rgba(140,210,255,0.8)';
    ctx.shadowBlur = 30 / s;
    ctx.strokeStyle = o.rim || 'rgba(170,225,255,0.55)';
    ctx.lineWidth = (o.rim ? 3 : 2.5) / s;
    ctx.stroke(P);
    ctx.shadowBlur = 0;
    // cheekbone highlights
    ctx.strokeStyle = o.rim ? W.rgba('#2a1f16', 0.5) : 'rgba(170,225,255,0.18)';
    ctx.lineWidth = 2 / s;
    ctx.beginPath(); ctx.moveTo(-80, 20); ctx.quadraticCurveTo(-55, 55, -30, 70); ctx.moveTo(80, 20); ctx.quadraticCurveTo(55, 55, 30, 70); ctx.stroke();
    // eyes
    const e = o.eyes == null ? 1 : o.eyes;
    if (e > 0 && o.inkEyes) {
      ctx.fillStyle = W.rgba('#1f4f8a', e);
      for (const ex of [-40, 40]) { ctx.beginPath(); ctx.ellipse(ex, -8, 16, 7, 0, 0, Math.PI * 2); ctx.fill(); }
    } else if (e > 0) {
      ctx.globalCompositeOperation = 'lighter';
      for (const ex of [-40, 40]) {
        const fl = 0.9 + 0.1 * Math.sin(t * 13 + ex);
        const gg = ctx.createRadialGradient(ex, -8, 0, ex, -8, 90);
        gg.addColorStop(0, `rgba(230,250,255,${e * fl})`);
        gg.addColorStop(0.12, `rgba(130,215,255,${0.9 * e * fl})`);
        gg.addColorStop(0.4, `rgba(60,150,255,${0.25 * e})`);
        gg.addColorStop(1, 'rgba(0,80,200,0)');
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(ex, -8, 90, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = `rgba(240,252,255,${e})`;
        ctx.beginPath(); ctx.ellipse(ex, -8, 15, 6, 0, 0, Math.PI * 2); ctx.fill();
      }
    }
    ctx.restore();
  };

  // ---- dragon ------------------------------------------------------------------
  /** silhouette facing right. flap -1..1 */
  W.dragon = (ctx, x, y, s, t, o = {}) => {
    const flap = o.flap == null ? Math.sin(t * 5) : o.flap;
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.translate(x, y);
    ctx.scale(s * (o.flip ? -1 : 1), s);
    ctx.rotate(o.tilt || 0);
    const body = o.color || '#0d0605';
    const rim = o.rim || 'rgba(255,140,60,0.75)';
    const wing = (k, far) => {
      // raised bat wing, rotated about the shoulder for the flap
      const sh = [10, -22];
      const th = (1 - (0.5 + 0.5 * k)) * 1.5; // 0 = fully raised, 1.5 rad = down-stroke
      const R2 = ([px, py]) => { const dx = px - sh[0], dy = py - sh[1], c = Math.cos(-th), sn = Math.sin(-th); return [sh[0] + dx * c - dy * sn, sh[1] + dx * sn + dy * c]; };
      const wr = R2([-30, -260]);
      const tips = [[-40, -440], [-230, -360], [-350, -220], [-360, -70]].map(R2);
      const att = [-150, 12];
      const P = new Path2D();
      P.moveTo(sh[0], sh[1]);
      P.lineTo(wr[0], wr[1]);
      P.lineTo(tips[0][0], tips[0][1]);
      const seq = [...tips, att];
      for (let i = 1; i < seq.length; i++) {
        const a = seq[i - 1], b = seq[i];
        const cx = W.lerp((a[0] + b[0]) / 2, wr[0], 0.32), cy = W.lerp((a[1] + b[1]) / 2, wr[1], 0.32);
        P.quadraticCurveTo(cx, cy, b[0], b[1]);
      }
      P.closePath();
      ctx.fillStyle = far ? (o.farColor || '#160805') : body;
      ctx.fill(P);
      ctx.strokeStyle = rim; ctx.lineWidth = 2.2 / s; ctx.stroke(P);
      ctx.strokeStyle = o.bone || 'rgba(255,150,80,0.4)'; ctx.lineWidth = (o.bone ? 1.6 : 3.5) / s;
      ctx.beginPath();
      ctx.moveTo(sh[0], sh[1]); ctx.lineTo(wr[0], wr[1]);
      for (const f of tips) { ctx.moveTo(wr[0], wr[1]); ctx.lineTo(f[0], f[1]); }
      ctx.stroke();
      // thumb claw
      ctx.fillStyle = body; ctx.beginPath(); ctx.moveTo(wr[0], wr[1]); ctx.lineTo(wr[0] + 14, wr[1] - 22); ctx.lineTo(wr[0] + 8, wr[1] + 4); ctx.fill();
    };
    // far wing (offset, phase-shifted)
    ctx.save(); ctx.translate(40, -14); ctx.scale(0.8, 0.86); wing(Math.sin(t * 6.5 - 0.5), true); ctx.restore();
    // body: tail -> torso -> neck -> head along a spine with a width profile
    const spine = [[-380, 70], [-300, 55], [-220, 30], [-140, 12], [-60, 4], [20, -6], [70, -30], [115, -58], [150, -74], [190, -78]];
    const wid = [1, 5, 11, 22, 40, 42, 22, 15, 13, 12];
    const L = [], R = [];
    spine.forEach((q, i) => {
      const nx = spine[Math.min(i + 1, spine.length - 1)], pv = spine[Math.max(i - 1, 0)];
      const ang = Math.atan2(nx[1] - pv[1], nx[0] - pv[0]) + Math.PI / 2;
      L.push([q[0] + Math.cos(ang) * wid[i], q[1] + Math.sin(ang) * wid[i]]);
      R.push([q[0] - Math.cos(ang) * wid[i], q[1] - Math.sin(ang) * wid[i]]);
    });
    const P = new Path2D();
    L.forEach((q, i) => (i ? P.lineTo(q[0], q[1]) : P.moveTo(q[0], q[1])));
    // head: snout, jaw, horns
    P.lineTo(235, -70); P.lineTo(250, -62); P.lineTo(228, -55); P.lineTo(245, -46); P.lineTo(200, -52);
    for (let i = R.length - 1; i >= 0; i--) P.lineTo(R[i][0], R[i][1]);
    P.closePath();
    P.moveTo(178, -86); P.lineTo(140, -118); P.lineTo(170, -88); // horn
    P.moveTo(186, -84); P.lineTo(160, -126); P.lineTo(180, -86);
    // legs tucked
    P.moveTo(-40, 28); P.lineTo(-70, 70); P.lineTo(-50, 72); P.lineTo(-20, 32);
    P.moveTo(20, 20); P.lineTo(10, 64); P.lineTo(28, 62); P.lineTo(36, 18);
    // spines on the back
    for (let i = 2; i < 8; i++) { const q = L[i]; P.moveTo(q[0] - 8, q[1]); P.lineTo(q[0] - 2, q[1] - 16); P.lineTo(q[0] + 6, q[1]); }
    ctx.fillStyle = body; ctx.fill(P);
    ctx.strokeStyle = rim; ctx.lineWidth = 2 / s; ctx.stroke(P);
    wing(flap, false);
    // ember eye
    ctx.fillStyle = o.eye || '#ffb347'; ctx.beginPath(); ctx.arc(205, -72, 3.2, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    // mouth position in screen space (for fire breath)
    const m = [x + (o.flip ? -1 : 1) * 248 * s, y - 56 * s];
    return m;
  };

  /** cone of dragon fire from mouth m toward angle ang; p = intensity 0..1 */
  W.fireBreath = (ctx, m, ang, len, t, p) => {
    if (p <= 0) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < 260; i++) {
      const u = W.hash(i * 1.7);
      const life = (t * 1.6 + u) % 1;
      const d = life * len * p;
      const spread = (W.hash(i * 3.1) - 0.5) * 0.45 * (0.3 + life);
      const a = ang + spread + Math.sin(t * 7 + i) * 0.04;
      const x = m[0] + Math.cos(a) * d, y = m[1] + Math.sin(a) * d - life * life * 40;
      const r = 10 + life * 70 * (0.5 + W.hash(i * 5.3));
      const col = life < 0.25 ? [255, 240, 190] : life < 0.6 ? [255, 150, 50] : [200, 50, 20];
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(${col[0]},${col[1]},${col[2]},${0.5 * (1 - life) * p})`);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.fillRect(x - r, y - r, r * 2, r * 2);
    }
    ctx.restore();
  };

  /** rising embers; density n, intensity a */
  W.embers = (ctx, t, n = 80, a = 1, warm = true) => {
    if (a <= 0) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < n; i++) {
      const sp = 40 + W.hash(i * 2.3) * 90;
      const x = (W.hash(i * 9.7) * W.W + Math.sin(t * 0.8 + i) * 40 + t * 12) % W.W;
      const y = W.H + 20 - ((t * sp + W.hash(i * 4.1) * W.H * 1.3) % (W.H * 1.3));
      const fl = 0.5 + 0.5 * Math.sin(t * (3 + W.hash(i) * 4) + i);
      const r = 1 + W.hash(i * 6.6) * 2.4;
      ctx.fillStyle = warm ? `rgba(255,${120 + Math.floor(fl * 90)},40,${(0.35 + 0.6 * fl) * a})` : `rgba(200,235,255,${(0.3 + 0.5 * fl) * a})`;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  };

  // ---- great hanging house banner ------------------------------------------------
  W.houseBanner = (ctx, x, y, w, h, t, o = {}) => {
    const a = o.alpha == null ? 1 : o.alpha;
    const drop = o.drop == null ? 1 : o.drop; // unfurl 0..1
    if (a <= 0 || drop <= 0) return;
    const rec = W.IMG && W.IMG[o.sigil === 'york' ? 'banner_york' : 'banner_lancaster'];
    if (rec) {
      // real banner image: unrolls from the rod, sways gently; the sigil rose is placed on it
      // fit inside the slot height (h) without exceeding the slot width
      let ih = h * 1.12, iw = ih * (rec.img.width / rec.img.height);
      if (iw > w * 1.15) { iw = w * 1.15; ih = iw * (rec.img.height / rec.img.width); }
      const sway = Math.sin(t * 1.1 + (o.phase || 0)) * 0.012;
      ctx.save();
      ctx.globalAlpha *= a;
      ctx.translate(x, y - 20);
      ctx.rotate(sway);
      ctx.beginPath(); ctx.rect(-iw / 2 - 10, -10, iw + 20, (ih + 20) * W.E.out(drop)); ctx.clip();
      ctx.drawImage(rec.img, -iw / 2, 0, iw, ih);
      if (o.sigil && drop > 0.5) W.rose(ctx, 0, ih * 0.42, Math.min(w * 0.34, iw * 0.34), { kind: o.sigil, bloom: W.clamp((drop - 0.5) * 2) });
      ctx.restore();
      return;
    }
    const hh = h * W.E.out(drop);
    const col = o.color || W.C.crimson;
    ctx.save();
    ctx.globalAlpha *= a;
    // cross-bar + finials
    ctx.fillStyle = B.mid;
    ctx.fillRect(x - w / 2 - 30, y - 10, w + 60, 12);
    for (const d of [-1, 1]) { ctx.beginPath(); ctx.arc(x + d * (w / 2 + 34), y - 4, 11, 0, Math.PI * 2); ctx.fill(); }
    ctx.fillStyle = B.hi; ctx.fillRect(x - w / 2 - 30, y - 10, w + 60, 2);
    // cloth as vertical strips with wave + shading
    const N = 40;
    const tip = 70; // pointed bottom
    for (let i = 0; i < N; i++) {
      const u0 = i / N, u1 = (i + 1) / N;
      const wave = (u) => Math.sin(u * 7 + t * 1.6 + (o.phase || 0)) * 0.5 + 0.5;
      const shade = 0.72 + 0.4 * wave((u0 + u1) / 2);
      const x0 = x - w / 2 + u0 * w, x1 = x - w / 2 + u1 * w + 0.6;
      const bot = (u) => y + hh - tip * (1 - Math.abs(u - 0.5) * 2) * 0 + tip * (1 - Math.abs(u - 0.5) * 2) * drop;
      const sway = (yy) => Math.sin(t * 1.3 + yy / 180 + (o.phase || 0)) * 6 * ((yy - y) / h);
      ctx.beginPath();
      ctx.moveTo(x0, y); ctx.lineTo(x1, y);
      ctx.lineTo(x1 + sway(y + hh), bot(u1)); ctx.lineTo(x0 + sway(y + hh), bot(u0));
      ctx.closePath();
      ctx.fillStyle = W.mixColor('#000000', col, Math.min(1, shade));
      ctx.fill();
    }
    // ink outline
    ctx.strokeStyle = 'rgba(42,31,22,0.7)'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(x - w / 2, y); ctx.lineTo(x - w / 2, y + hh); ctx.lineTo(x, y + hh + 70 * drop); ctx.lineTo(x + w / 2, y + hh); ctx.lineTo(x + w / 2, y); ctx.stroke();
    // gold trim
    ctx.strokeStyle = W.rgba(B.light, 0.85);
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x - w / 2 + 14, y + 4);
    ctx.lineTo(x - w / 2 + 14, y + hh - 6);
    ctx.lineTo(x, y + hh + 70 * drop - 22);
    ctx.lineTo(x + w / 2 - 14, y + hh - 6);
    ctx.lineTo(x + w / 2 - 14, y + 4);
    ctx.stroke();
    ctx.restore();
    // sigil
    if (o.sigil && drop > 0.5) {
      const sp = W.clamp((drop - 0.5) * 2);
      const sy = y + hh * 0.42;
      W.rose(ctx, x + Math.sin(t * 1.3 + (o.phase || 0) + sy / 180) * 3, sy, w * 0.32, { kind: o.sigil, bloom: sp, alpha: a });
    }
  };

  // ---- bronze clockwork -----------------------------------------------------------
  W.gear = (ctx, x, y, r, teeth, rot, o = {}) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    ctx.beginPath();
    const tooth = r * 0.14;
    for (let i = 0; i < teeth * 2; i++) {
      const a0 = (i / (teeth * 2)) * Math.PI * 2, a1 = ((i + 1) / (teeth * 2)) * Math.PI * 2;
      const rr = i % 2 ? r : r + tooth;
      ctx.arc(0, 0, rr, a0, a1);
    }
    ctx.closePath();
    ctx.moveTo(r * 0.32, 0); ctx.arc(0, 0, r * 0.32, 0, Math.PI * 2, true);
    const g = ctx.createLinearGradient(-r, -r, r, r);
    g.addColorStop(0, B.light); g.addColorStop(0.45, B.mid); g.addColorStop(1, B.dark);
    ctx.fillStyle = g;
    ctx.fill('evenodd');
    ctx.strokeStyle = W.rgba(B.hi, 0.35); ctx.lineWidth = 1.2; ctx.stroke();
    // spokes
    ctx.strokeStyle = W.rgba(B.shadow, 0.55); ctx.lineWidth = r * 0.08;
    ctx.beginPath();
    for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2; ctx.moveTo(Math.cos(a) * r * 0.36, Math.sin(a) * r * 0.36); ctx.lineTo(Math.cos(a) * r * 0.8, Math.sin(a) * r * 0.8); }
    ctx.stroke();
    ctx.restore();
  };

  /** ground-plane perspective camera for the clockwork map */
  W.groundCam = (c) => (ll) => {
    const k = c.k || 170;
    const gx = (ll[0] - c.lon) * 0.6 * k, gz = (ll[1] - c.lat) * k;
    const depth = c.dist + gz;
    const sc = c.dist / Math.max(depth, 60);
    return [W.W / 2 + (gx + (c.panX || 0)) * sc, c.horizon + c.height * sc, sc];
  };

  W.bronzeMap = (ctx, t, cam, o = {}) => {
    const pr = W.groundCam(cam);
    const a = o.alpha == null ? 1 : o.alpha;
    ctx.save();
    ctx.globalAlpha *= a;
    // plate grid (engraved)
    ctx.strokeStyle = W.rgba(B.light, 0.12);
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let lon = -12; lon <= 8; lon += 1) { const p1 = pr([lon, 48]), p2 = pr([lon, 60]); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); }
    for (let lat = 48; lat <= 60; lat += 0.5) { const p1 = pr([-12, lat]), p2 = pr([8, lat]); ctx.moveTo(p1[0], p1[1]); ctx.lineTo(p2[0], p2[1]); }
    ctx.stroke();
    for (const name of ['britain', 'ireland', 'anglesey', 'wight']) {
      const pts = W.GEO[name].map(pr);
      const path = () => { ctx.beginPath(); pts.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath(); };
      // extruded edge (thickness)
      ctx.save(); ctx.translate(0, 14); path(); ctx.fillStyle = B.shadow; ctx.fill(); ctx.restore();
      ctx.save(); ctx.translate(0, 7); path(); ctx.fillStyle = B.dark; ctx.fill(); ctx.restore();
      path();
      const g = ctx.createLinearGradient(0, cam.horizon, 0, W.H);
      g.addColorStop(0, '#5b4222'); g.addColorStop(0.5, B.mid); g.addColorStop(1, '#a7854e');
      ctx.fillStyle = g;
      ctx.fill();
      ctx.strokeStyle = W.rgba(B.hi, 0.7); ctx.lineWidth = 1.5; ctx.stroke();
    }
    // light sweep across the metal
    const sx = ((t * 0.12) % 1.6 - 0.3) * W.W;
    const sw = ctx.createLinearGradient(sx - 300, 0, sx + 300, 0);
    sw.addColorStop(0, 'rgba(255,230,170,0)'); sw.addColorStop(0.5, 'rgba(255,230,170,0.10)'); sw.addColorStop(1, 'rgba(255,230,170,0)');
    ctx.globalCompositeOperation = 'lighter';
    ctx.fillStyle = sw; ctx.fillRect(0, cam.horizon, W.W, W.H);
    ctx.restore();
    return pr;
  };

  /** a castle tower rising out of the map on its gear */
  W.risingTower = (ctx, base, t, rise, o = {}) => {
    if (rise <= 0) return;
    const [x, y, sc] = base;
    const s = (o.size || 120) * sc;
    ctx.save();
    // ground hole + gear
    W.gear(ctx, x, y, s * 0.55, 14, t * (o.dir || 1) * 0.8, { alpha: Math.min(1, rise * 2) });
    ctx.beginPath(); ctx.rect(x - s * 2, y - s * 4, s * 4, s * 4); ctx.clip();
    const lift = W.E.out(rise) * s * 1.9;
    ctx.translate(x, y + s * 1.9 - lift);
    const P = new Path2D();
    const wTop = s * 0.55, wBot = s * 0.7;
    P.moveTo(-wBot, 0); P.lineTo(-wTop, -s * 1.6);
    for (let i = 0; i < 4; i++) { const xx = -wTop + (i * 2 * wTop) / 3.5; P.lineTo(xx, -s * 1.78); P.lineTo(xx + wTop * 0.3, -s * 1.78); P.lineTo(xx + wTop * 0.3, -s * 1.6); }
    P.lineTo(wTop, -s * 1.6); P.lineTo(wBot, 0); P.closePath();
    const g = ctx.createLinearGradient(-wBot, 0, wBot, 0);
    g.addColorStop(0, B.dark); g.addColorStop(0.35, B.light); g.addColorStop(0.6, B.mid); g.addColorStop(1, B.shadow);
    ctx.fillStyle = g; ctx.fill(P);
    ctx.strokeStyle = W.rgba(B.hi, 0.5); ctx.lineWidth = 1.2; ctx.stroke(P);
    // window + banner
    ctx.fillStyle = 'rgba(255,190,110,0.85)';
    ctx.fillRect(-s * 0.08, -s * 1.15, s * 0.16, s * 0.3);
    ctx.strokeStyle = B.mid; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, -s * 1.78); ctx.lineTo(0, -s * 2.5); ctx.stroke();
    ctx.fillStyle = o.flag || W.C.crimson;
    const wv = Math.sin(t * 4) * s * 0.05;
    ctx.beginPath(); ctx.moveTo(0, -s * 2.5); ctx.lineTo(s * 0.6, -s * 2.38 + wv); ctx.lineTo(0, -s * 2.18); ctx.closePath(); ctx.fill();
    ctx.restore();
  };

  /** astrolabe: three engraved rings turning about different axes around a sun */
  W.astrolabe = (ctx, x, y, R, t, o = {}) => {
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0) return;
    ctx.save();
    ctx.globalAlpha *= a;
    // sun
    const g = ctx.createRadialGradient(x, y, 0, x, y, R * 0.6);
    g.addColorStop(0, 'rgba(255,236,190,1)'); g.addColorStop(0.25, 'rgba(255,190,90,0.9)'); g.addColorStop(1, 'rgba(255,150,40,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, R * 0.6, 0, Math.PI * 2); ctx.fill();
    const rings = [[R, 0.3, 0.55, 0.0], [R * 0.86, -0.5, 0.8, 1.2], [R * 0.72, 0.9, 1.1, 2.1]];
    rings.forEach(([r, tilt, sp, ph], i) => {
      const squash = Math.cos(t * sp * 0.6 + ph);
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(tilt + t * 0.05 * (i % 2 ? -1 : 1));
      ctx.scale(1, Math.abs(squash) * 0.85 + 0.15);
      ctx.lineWidth = 9;
      ctx.strokeStyle = B.mid;
      ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
      ctx.lineWidth = 1.5; ctx.strokeStyle = W.rgba(B.hi, 0.75);
      ctx.beginPath(); ctx.arc(0, 0, r - 4, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = W.rgba(B.shadow, 0.8); ctx.lineWidth = 1.2;
      ctx.beginPath();
      for (let k = 0; k < 48; k++) { const aa = (k / 48) * Math.PI * 2 + t * sp * 0.2; ctx.moveTo(Math.cos(aa) * (r - 4), Math.sin(aa) * (r - 4)); ctx.lineTo(Math.cos(aa) * (r + 4), Math.sin(aa) * (r + 4)); }
      ctx.stroke();
      ctx.restore();
    });
    ctx.restore();
  };

  /** metallic bronze text */
  W.metalText = (ctx, str, x, y, o = {}) => {
    const size = o.size || 160;
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0) return;
    const fam = o.fam || W.F.title;
    const dir = /[؀-ۿ]/.test(str) ? 'rtl' : 'ltr';
    ctx.save();
    ctx.globalAlpha *= a;
    ctx.font = W.font(size, fam, o.weight || 700);
    ctx.direction = dir;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if ('letterSpacing' in ctx) ctx.letterSpacing = o.tracking ? `${o.tracking}px` : '0px';
    // drop shadow / emboss
    ctx.fillStyle = 'rgba(0,0,0,0.75)';
    ctx.fillText(str, x + size * 0.02, y + size * 0.04);
    ctx.fillStyle = B.dark; ctx.fillText(str, x, y + size * 0.02);
    const g = ctx.createLinearGradient(0, y - size * 0.55, 0, y + size * 0.55);
    g.addColorStop(0, B.hi); g.addColorStop(0.38, B.light); g.addColorStop(0.52, B.mid); g.addColorStop(0.62, '#f0d79c'); g.addColorStop(1, B.dark);
    ctx.fillStyle = g;
    ctx.fillText(str, x, y);
    // moving glint, clipped to the glyphs via source-atop on a layer
    if (o.glint != null) {
      const w = ctx.measureText(str).width;
      const [c2, x2] = W.layer('glint', Math.ceil(w + size), Math.ceil(size * 2));
      x2.font = ctx.font; x2.direction = dir; x2.textAlign = 'center'; x2.textBaseline = 'middle';
      if ('letterSpacing' in x2) x2.letterSpacing = ctx.letterSpacing;
      x2.fillStyle = '#fff'; x2.fillText(str, c2.width / 2, c2.height / 2);
      x2.globalCompositeOperation = 'source-in';
      const gx = W.lerp(-0.2, 1.2, o.glint) * c2.width;
      const gg = x2.createLinearGradient(gx - 120, 0, gx + 120, 0);
      gg.addColorStop(0, 'rgba(255,250,230,0)'); gg.addColorStop(0.5, 'rgba(255,250,230,0.85)'); gg.addColorStop(1, 'rgba(255,250,230,0)');
      x2.fillStyle = gg; x2.fillRect(0, 0, c2.width, c2.height);
      ctx.drawImage(c2, x - c2.width / 2, y - c2.height / 2);
    }
    ctx.restore();
  };

  /** throne of swords: a seat with a fan of blades behind it. rise 0..1 */
  W.swordThrone = (ctx, x, y, s, t, rise = 1) => {
    if (rise <= 0) return;
    const r = W.rng(1461);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.globalAlpha *= W.clamp(rise * 1.5);
    const blade = (len, wdt, hilt = true) => {
      ctx.beginPath();
      ctx.moveTo(-wdt, 0); ctx.lineTo(-wdt * 0.8, -len); ctx.lineTo(0, -len - wdt * 4); ctx.lineTo(wdt * 0.8, -len); ctx.lineTo(wdt, 0); ctx.closePath();
      const g = ctx.createLinearGradient(-wdt, 0, wdt, 0);
      g.addColorStop(0, '#202125'); g.addColorStop(0.45, '#a9abb2'); g.addColorStop(0.55, '#5d5f66'); g.addColorStop(1, '#141518');
      ctx.fillStyle = g; ctx.fill();
      if (hilt) {
        ctx.fillStyle = '#4a3f2e'; ctx.fillRect(-wdt * 3.4, -2, wdt * 6.8, wdt * 1.3);
        ctx.fillStyle = '#2a2219'; ctx.fillRect(-wdt * 0.8, wdt * 1.3 - 2, wdt * 1.6, wdt * 4.5);
      }
    };
    // back: dense crest of near-vertical blades, tallest at the centre
    const n = 54;
    const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => Math.abs(b - n / 2) - Math.abs(a - n / 2));
    for (const i of order) {
      const u = i / (n - 1), c = Math.abs(u - 0.5) * 2;
      const grow = W.E.out(W.clamp(rise * 1.4 - c * 0.4));
      const len = (260 + r() * 260) * (1 - c * 0.55) * grow;
      const xb = W.lerp(-170, 170, u) + (r() - 0.5) * 14;
      const ang = (u - 0.5) * 0.7 + (r() - 0.5) * 0.18;
      ctx.save();
      ctx.translate(xb, -150 + c * 30);
      ctx.rotate(ang);
      if (len > 6) blade(len, 3 + r() * 2.6, r() > 0.3);
      ctx.restore();
    }
    // seat block with blade armrests
    const g = ctx.createLinearGradient(-170, 0, 170, 0);
    g.addColorStop(0, '#0e0e10'); g.addColorStop(0.5, '#3c3d42'); g.addColorStop(1, '#09090a');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(-160, -160); ctx.lineTo(160, -160); ctx.lineTo(150, -40); ctx.lineTo(-150, -40); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fillRect(-120, -150, 240, 60);
    for (const d of [-1, 1]) for (let k = 0; k < 7; k++) {
      ctx.save(); ctx.translate(d * (150 + k * 4), -70 - k * 7); ctx.rotate(d * (1.48 + (k - 3) * 0.04)); blade(80 + k * 9, 2.6, false); ctx.restore();
    }
    // steps
    ctx.fillStyle = '#16161a'; ctx.fillRect(-210, -40, 420, 22);
    ctx.fillStyle = '#0f0f12'; ctx.fillRect(-270, -18, 540, 26);
    ctx.strokeStyle = 'rgba(200,205,215,0.25)'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(-210, -40); ctx.lineTo(210, -40); ctx.moveTo(-270, -18); ctx.lineTo(270, -18); ctx.stroke();
    ctx.restore();
  };
})();

/* metallic longsword planted point-down (used between the house banners) */
(function () {
  const { W } = window;
  W.longsword = (ctx, x, y, s, t) => {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    // glow
    const gl = ctx.createRadialGradient(0, 0, 0, 0, 0, 420);
    gl.addColorStop(0, 'rgba(255,215,160,0.18)'); gl.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gl; ctx.fillRect(-420, -420, 840, 840);
    // blade (point down)
    ctx.beginPath();
    ctx.moveTo(-18, -250); ctx.lineTo(18, -250); ctx.lineTo(14, 300); ctx.lineTo(0, 350); ctx.lineTo(-14, 300); ctx.closePath();
    const g = ctx.createLinearGradient(-18, 0, 18, 0);
    g.addColorStop(0, '#3b3d43'); g.addColorStop(0.48, '#e7e9ee'); g.addColorStop(0.52, '#8b8e96'); g.addColorStop(1, '#25262a');
    ctx.fillStyle = g; ctx.fill();
    ctx.strokeStyle = 'rgba(30,30,34,0.8)'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, -240); ctx.lineTo(0, 320); ctx.stroke();
    // glint travelling down the blade
    const gy = -250 + ((t * 0.35) % 1) * 600;
    const gg = ctx.createLinearGradient(0, gy - 60, 0, gy + 60);
    gg.addColorStop(0, 'rgba(255,255,255,0)'); gg.addColorStop(0.5, 'rgba(255,255,255,0.55)'); gg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = gg; ctx.fillRect(-16, gy - 60, 32, 120);
    // crossguard, grip, pommel in bronze
    const B = W.BRONZE;
    const gb = ctx.createLinearGradient(0, -280, 0, -250);
    gb.addColorStop(0, B.hi); gb.addColorStop(1, B.dark);
    ctx.fillStyle = gb;
    ctx.beginPath(); ctx.moveTo(-120, -262); ctx.quadraticCurveTo(0, -282, 120, -262); ctx.lineTo(112, -248); ctx.quadraticCurveTo(0, -262, -112, -248); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#2b1d10'; ctx.fillRect(-11, -370, 22, 110);
    ctx.strokeStyle = B.mid; ctx.lineWidth = 2;
    for (let k = 0; k < 8; k++) { ctx.beginPath(); ctx.moveTo(-11, -365 + k * 13); ctx.lineTo(11, -358 + k * 13); ctx.stroke(); }
    const gp = ctx.createRadialGradient(-6, -392, 2, 0, -388, 26);
    gp.addColorStop(0, B.hi); gp.addColorStop(1, B.dark);
    ctx.fillStyle = gp; ctx.beginPath(); ctx.arc(0, -388, 24, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  };
})();
