/* Original vector symbol set. All symbols are drawn in a unit box (≈ -1..1) and share
   one stroke language: hairline ivory/gold outlines, flat restrained fills.
   o.p   = line-draw progress (0..1)   o.fill = fill opacity (0..1)   o.color = stroke colour */
(function () {
  const { W } = window;

  function stroked(ctx, x, y, s, o, build, len = 14) {
    const p = o.p == null ? 1 : o.p;
    if (p <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    if (o.rot) ctx.rotate(o.rot);
    ctx.scale(s, s);
    const path = new Path2D();
    build(path);
    if (o.fill && o.fill > 0) {
      ctx.save();
      ctx.globalAlpha *= o.fill;
      ctx.fillStyle = o.fillColor || o.color || W.C.ivory;
      ctx.fill(path, 'evenodd');
      ctx.restore();
    }
    ctx.strokeStyle = o.color || W.C.ivory;
    ctx.lineWidth = (o.width || 2) / s;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.glowBlur || 18; }
    if (p < 1) ctx.setLineDash([len * p, len]);
    ctx.stroke(path);
    ctx.restore();
  }

  // ---- crown ------------------------------------------------------------------
  W.crown = (ctx, x, y, s, o = {}) => {
    const rec = W.IMG && W.IMG.crown;
    if (rec) {
      // real crown (Crown of Princess Blanche): fades and settles in as it "draws"
      const p = o.p == null ? 1 : W.clamp(o.p);
      if (p <= 0) return;
      const w = 2.3 * s, h = w * (rec.img.height / rec.img.width);
      ctx.save();
      ctx.globalAlpha *= W.clamp(p * 1.4);
      ctx.translate(x, y - 0.22 * s + (1 - W.E.out(p)) * 0.25 * s);
      if (o.rot) ctx.rotate(o.rot);
      const sc = 0.92 + 0.08 * W.E.out(p);
      ctx.scale(sc, sc);
      if (o.glow) { ctx.shadowColor = 'rgba(160,110,30,0.55)'; ctx.shadowBlur = 0.35 * s; }
      ctx.globalCompositeOperation = rec.blend || 'source-over';
      ctx.drawImage(rec.img, -w / 2, -h / 2, w, h);
      ctx.restore();
      return;
    }
    return W.crownDrawn(ctx, x, y, s, o);
  };
  W.crownDrawn = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(-0.95, 0.55); P.lineTo(0.95, 0.55); P.lineTo(0.95, 0.32); P.lineTo(-0.95, 0.32); P.closePath();
      P.moveTo(-0.95, 0.32); P.lineTo(-1.05, -0.42); P.lineTo(-0.52, 0.02); P.lineTo(0, -0.66);
      P.lineTo(0.52, 0.02); P.lineTo(1.05, -0.42); P.lineTo(0.95, 0.32);
      for (const [cx, cy, r] of [[-1.05, -0.5, 0.08], [0, -0.74, 0.08], [1.05, -0.5, 0.08]]) {
        P.moveTo(cx + r, cy); P.arc(cx, cy, r, 0, Math.PI * 2);
      }
      P.moveTo(0, -0.82); P.lineTo(0, -1.06); P.moveTo(-0.1, -0.95); P.lineTo(0.1, -0.95);
      for (const gx of [-0.6, 0, 0.6]) { P.moveTo(gx + 0.07, 0.435); P.arc(gx, 0.435, 0.07, 0, Math.PI * 2); }
    }, 16);

  // ---- heraldic rose ------------------------------------------------------------
  /** kind: 'york' (white) | 'lancaster' (red) | 'tudor' (red outer, white inner)
      o.bloom 0..1 opens the petals; o.spin small rotation */
  W.rose = (ctx, x, y, s, o = {}) => {
    const bloom = o.bloom == null ? 1 : o.bloom;
    if (bloom <= 0) return;
    const kind = o.kind || 'york';
    // real heraldic artwork when supplied (rose_york / rose_lancaster / rose_tudor)
    const rec = W.IMG && W.IMG['rose_' + kind];
    if (rec) {
      const d = 2.05 * s * (0.55 + 0.45 * W.E.out(W.clamp(bloom)));
      ctx.save();
      ctx.globalAlpha *= (o.alpha == null ? 1 : o.alpha) * W.clamp(bloom * 1.6);
      ctx.translate(x, y);
      ctx.rotate((o.spin || 0) + (1 - W.clamp(bloom)) * -0.6);
      ctx.drawImage(rec.img, -d / 2, -d / 2, d, d);
      ctx.restore();
      return;
    }
    const outer = kind === 'york' ? W.C.rose : W.C.crimson;
    const inner = kind === 'lancaster' ? W.C.crimsonBright : W.C.rose;
    const edge = 'rgba(42,31,22,0.75)';
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((o.spin || 0) - Math.PI / 2);
    ctx.globalAlpha *= o.alpha == null ? 1 : o.alpha;
    const petal = (ang, dist, r, col, pp) => {
      if (pp <= 0) return;
      ctx.save();
      ctx.rotate(ang);
      ctx.translate(dist * s * pp, 0);
      ctx.scale(pp, pp);
      ctx.beginPath();
      // heart-shaped lobe: two arcs meeting at an outer notch
      const R = r * s;
      ctx.moveTo(-R * 0.9, 0);
      ctx.bezierCurveTo(-R * 0.6, -R * 1.25, R * 1.15, -R * 1.25, R * 1.05, -R * 0.08);
      ctx.lineTo(R * 0.86, 0);
      ctx.lineTo(R * 1.05, R * 0.08);
      ctx.bezierCurveTo(R * 1.15, R * 1.25, -R * 0.6, R * 1.25, -R * 0.9, 0);
      ctx.closePath();
      ctx.fillStyle = col;
      ctx.fill();
      ctx.strokeStyle = edge;
      ctx.lineWidth = Math.max(1, s * 0.018);
      ctx.stroke();
      ctx.restore();
    };
    // barbs (sepals) between outer petals
    for (let i = 0; i < 5; i++) {
      const pp = W.clamp(bloom * 1.4 - 0.15);
      if (pp <= 0) continue;
      ctx.save();
      ctx.rotate(((i + 0.5) / 5) * Math.PI * 2);
      ctx.beginPath();
      ctx.moveTo(0.55 * s, -0.09 * s);
      ctx.quadraticCurveTo(0.95 * s * pp, -0.03 * s, 1.08 * s * pp, 0);
      ctx.quadraticCurveTo(0.95 * s * pp, 0.03 * s, 0.55 * s, 0.09 * s);
      ctx.fillStyle = o.barb || '#6f6a3e';
      ctx.fill();
      ctx.restore();
    }
    for (let i = 0; i < 5; i++) petal((i / 5) * Math.PI * 2, 0.46, 0.5, outer, W.clamp(bloom * 1.25 - i * 0.04));
    for (let i = 0; i < 5; i++) petal(((i + 0.5) / 5) * Math.PI * 2, 0.24, 0.3, inner, W.clamp(bloom * 1.5 - 0.35 - i * 0.03));
    // seeded centre
    const cp = W.clamp(bloom * 2 - 1);
    if (cp > 0) {
      ctx.beginPath();
      ctx.arc(0, 0, 0.17 * s * cp, 0, Math.PI * 2);
      ctx.fillStyle = W.C.gold;
      ctx.fill();
      ctx.fillStyle = 'rgba(60,40,10,0.6)';
      for (let i = 0; i < 7; i++) {
        const a = (i / 7) * Math.PI * 2;
        ctx.beginPath();
        ctx.arc(Math.cos(a) * 0.09 * s * cp, Math.sin(a) * 0.09 * s * cp, 0.022 * s, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.restore();
  };

  // ---- sword ---------------------------------------------------------------------
  W.sword = (ctx, x, y, s, o = {}) => {
    const rec = W.IMG && W.IMG.sword;
    if (rec) {
      // engraved sword image (pommel up, point down in the file); rot = 0 means point up, as before
      const p = o.p == null ? 1 : W.clamp(o.p);
      if (p <= 0) return;
      const h = 2.25 * s, w = h * (rec.img.width / rec.img.height);
      ctx.save();
      ctx.globalAlpha *= W.clamp(p * 1.3);
      ctx.translate(x, y - 0.05 * s);
      ctx.rotate((o.rot || 0) + Math.PI);
      ctx.beginPath(); ctx.rect(-w / 2 - 4, -h / 2 - 4, w + 8, (h + 8) * W.E.inOut(p)); ctx.clip();
      ctx.drawImage(rec.img, -w / 2, -h / 2, w, h);
      ctx.restore();
      return;
    }
    return W.swordDrawn(ctx, x, y, s, o);
  };
  W.swordDrawn = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(0, -1.15); P.lineTo(0.07, -1.0); P.lineTo(0.07, 0.42); P.lineTo(-0.07, 0.42); P.lineTo(-0.07, -1.0); P.closePath();
      P.moveTo(-0.38, 0.42); P.lineTo(0.38, 0.42); P.lineTo(0.38, 0.5); P.lineTo(-0.38, 0.5); P.closePath();
      P.moveTo(-0.045, 0.5); P.lineTo(0.045, 0.5); P.lineTo(0.045, 0.85); P.lineTo(-0.045, 0.85); P.closePath();
      P.moveTo(0.1, 0.94); P.arc(0, 0.94, 0.1, 0, Math.PI * 2);
      P.moveTo(0, -0.92); P.lineTo(0, 0.3);
    }, 9);

  W.crossedSwords = (ctx, x, y, s, o = {}) => {
    W.sword(ctx, x, y, s, { ...o, rot: Math.PI / 4 });
    W.sword(ctx, x, y, s, { ...o, rot: -Math.PI / 4 });
  };

  // ---- shield (heater) ----------------------------------------------------------
  W.shield = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(-0.8, -0.85); P.lineTo(0.8, -0.85); P.lineTo(0.8, -0.1);
      P.bezierCurveTo(0.8, 0.5, 0.35, 0.85, 0, 1.05);
      P.bezierCurveTo(-0.35, 0.85, -0.8, 0.5, -0.8, -0.1); P.closePath();
      if (o.quartered) { P.moveTo(0, -0.85); P.lineTo(0, 1.05); P.moveTo(-0.8, 0.0); P.lineTo(0.8, 0.0); }
    }, 7);

  // ---- banner on a pole, cloth waves with time -------------------------------------
  W.banner = (ctx, x, y, s, t, o = {}) => {
    const p = o.p == null ? 1 : o.p;
    if (p <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.globalAlpha *= p;
    ctx.strokeStyle = o.pole || W.C.mute;
    ctx.lineWidth = 2 / s;
    ctx.beginPath(); ctx.moveTo(0, 1.2); ctx.lineTo(0, -1.2); ctx.stroke();
    const dir = o.flip ? -1 : 1;
    const N = 18;
    const top = [], bot = [];
    for (let i = 0; i <= N; i++) {
      const u = i / N, xx = dir * u * 1.5 * W.E.out(p);
      const wv = Math.sin(u * 4 - t * 2.2 + (o.phase || 0)) * 0.08 * u;
      top.push([xx, -1.15 + wv]);
      bot.push([xx, -0.15 + wv - (i === N ? 0 : 0)]);
    }
    ctx.beginPath();
    top.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])));
    // swallow tail
    const tl = top[N], bl = bot[N];
    ctx.lineTo(tl[0] - dir * 0.35, (tl[1] + bl[1]) / 2);
    ctx.lineTo(bl[0], bl[1]);
    for (let i = N; i >= 0; i--) ctx.lineTo(bot[i][0], bot[i][1]);
    ctx.closePath();
    ctx.fillStyle = o.color || W.C.crimson;
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.35)';
    ctx.lineWidth = 1.2 / s;
    ctx.stroke();
    ctx.restore();
  };

  // ---- castle / tower silhouette --------------------------------------------------
  // window positions (fraction of the image) for the princes' lights
  W.TOWER_WINDOWS = [[0.475, 0.52], [0.505, 0.52]];
  W.castle = (ctx, x, y, s, o = {}) => {
    const rec = W.IMG && W.IMG.tower;
    if (rec) {
      const p = o.p == null ? 1 : W.clamp(o.p);
      if (p <= 0) return null;
      const w = 2.9 * s, h = w * (rec.img.height / rec.img.width);
      const left = x - w / 2, top = y + 1.0 * s - h;
      ctx.save();
      ctx.globalAlpha *= W.clamp(p * 1.3);
      ctx.globalCompositeOperation = 'multiply';
      ctx.beginPath(); ctx.rect(left - 4, top + h * (1 - W.E.inOut(p)) - 4, w + 8, h + 8); ctx.clip();
      ctx.drawImage(rec.img, left, top, w, h);
      ctx.restore();
      return { left, top, w, h };
    }
    W.castleDrawn(ctx, x, y, s, o);
    return null;
  };
  W.castleDrawn = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      const crenel = (x0, x1, yTop, n) => {
        const w = (x1 - x0) / (n * 2 - 1);
        P.lineTo(x0, yTop);
        for (let i = 0; i < n; i++) {
          const a = x0 + i * 2 * w;
          P.lineTo(a, yTop - 0.12); P.lineTo(a + w, yTop - 0.12); P.lineTo(a + w, yTop);
          if (i < n - 1) P.lineTo(a + 2 * w, yTop);
        }
        P.lineTo(x1, yTop);
      };
      P.moveTo(-1.2, 1); P.lineTo(-1.2, -0.2);
      crenel(-1.2, -0.62, -0.2, 3);
      P.lineTo(-0.62, -0.05); P.lineTo(-0.42, -0.05); P.lineTo(-0.42, -0.75);
      crenel(-0.42, 0.42, -0.75, 4);
      P.lineTo(0.42, -0.05); P.lineTo(0.62, -0.05); P.lineTo(0.62, -0.2);
      crenel(0.62, 1.2, -0.2, 3);
      P.lineTo(1.2, 1); P.closePath();
      // gate + windows
      P.moveTo(-0.18, 1); P.lineTo(-0.18, 0.62); P.arc(0, 0.62, 0.18, Math.PI, 0); P.lineTo(0.18, 1);
      for (const wx of [-0.15, 0.15]) { P.moveTo(wx - 0.05, -0.25); P.lineTo(wx - 0.05, -0.45); P.arc(wx, -0.45, 0.05, Math.PI, 0); P.lineTo(wx + 0.05, -0.25); P.closePath(); }
    }, 16);

  // ---- royal seal with ridged edge & tails ----------------------------------------
  W.seal = (ctx, x, y, s, o = {}) => {
    const p = o.p == null ? 1 : o.p;
    if (p <= 0) return;
    const sc = 1 + (1 - W.E.outBack(W.clamp(p))) * 0.5;
    const rec = W.IMG && W.IMG[o.emblem === false ? 'seal_red' : 'seal'];
    if (rec) {
      // stamped in: drops from slightly larger with a little rotation, casts a soft shadow
      ctx.save();
      ctx.globalAlpha *= W.clamp(p * 2);
      ctx.translate(x, y);
      ctx.rotate((1 - W.clamp(p)) * -0.3 + (o.emblem === false ? -0.12 : 0));
      ctx.scale(sc, sc);
      ctx.shadowColor = 'rgba(40,20,10,0.45)'; ctx.shadowBlur = 0.25 * s; ctx.shadowOffsetY = 0.08 * s;
      ctx.drawImage(rec.img, -s, -s, 2 * s, 2 * s);
      ctx.restore();
      return;
    }
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(sc, sc);
    ctx.globalAlpha *= W.clamp(p * 2);
    const col = o.color || W.C.crimson;
    // ribbon tails
    ctx.fillStyle = W.mixColor(col.length === 7 ? col : '#a3192a', '#000000', 0.25);
    for (const d of [-1, 1]) {
      ctx.beginPath();
      ctx.moveTo(d * 0.25 * s, 0.6 * s); ctx.lineTo(d * 0.55 * s, 1.5 * s); ctx.lineTo(d * 0.35 * s, 1.35 * s);
      ctx.lineTo(d * 0.22 * s, 1.55 * s); ctx.lineTo(d * 0.02 * s, 0.7 * s); ctx.closePath(); ctx.fill();
    }
    ctx.beginPath();
    const N = 36;
    for (let i = 0; i <= N * 2; i++) {
      const a = (i / (N * 2)) * Math.PI * 2, r = (i % 2 ? 0.93 : 1) * s;
      i ? ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.moveTo(r, 0);
    }
    ctx.closePath();
    ctx.fillStyle = col;
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.35)';
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(0, 0, 0.74 * s, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,230,210,0.25)';
    ctx.beginPath(); ctx.arc(0, 0, 0.68 * s, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
    if (o.emblem !== false) W.crown(ctx, x, y - 0.02 * s, 0.36 * s * sc, { color: 'rgba(255,235,220,0.75)', width: 2, fill: 0.15 });
  };

  // ---- small Latin cross for deaths ------------------------------------------------
  W.dagger = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(0, -1); P.lineTo(0, 1); P.moveTo(-0.45, -0.45); P.lineTo(0.45, -0.45);
    }, 4);

  // ---- sun in splendour (badge of Edward IV) ----------------------------------------
  W.sun = (ctx, x, y, s, t, o = {}) => {
    const p = o.p == null ? 1 : o.p;
    if (p <= 0) return;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(t * 0.05);
    ctx.globalAlpha *= p;
    ctx.strokeStyle = o.color || W.C.gold;
    ctx.lineWidth = 2;
    for (let i = 0; i < 16; i++) {
      const a = (i / 16) * Math.PI * 2;
      const r0 = 0.45 * s, r1 = (i % 2 ? 0.85 : 1.1) * s * W.E.out(p);
      ctx.save();
      ctx.rotate(a);
      ctx.beginPath();
      if (i % 2) {
        ctx.moveTo(r0, 0);
        for (let k = 1; k <= 10; k++) ctx.lineTo(W.lerp(r0, r1, k / 10), Math.sin(k * 1.5) * 0.04 * s);
      } else { ctx.moveTo(r0, -0.04 * s); ctx.lineTo(r1, 0); ctx.lineTo(r0, 0.04 * s); }
      ctx.stroke();
      ctx.restore();
    }
    ctx.beginPath(); ctx.arc(0, 0, 0.38 * s, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
  };

  // ---- interlinked rings (marriage) ------------------------------------------------
  W.rings = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(0.1, 0); P.arc(-0.35, 0, 0.45, 0, Math.PI * 2);
      P.moveTo(0.8, 0); P.arc(0.35, 0, 0.45, 0, Math.PI * 2);
    }, 6);

  // ---- ice crystal & dragon wing (for the cold open) -----------------------------
  W.crystal = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2, c = Math.cos(a), sn = Math.sin(a);
        P.moveTo(0, 0); P.lineTo(c, sn);
        for (const f of [0.45, 0.72]) {
          const bx = c * f, by = sn * f, l = 0.24 * (1.1 - f);
          for (const d of [-1, 1]) {
            const a2 = a + d * 0.75;
            P.moveTo(bx, by); P.lineTo(bx + Math.cos(a2) * l, by + Math.sin(a2) * l);
          }
        }
      }
      for (let i = 0; i <= 6; i++) {
        const a = (i / 6) * Math.PI * 2;
        i ? P.lineTo(Math.cos(a) * 0.22, Math.sin(a) * 0.22) : P.moveTo(0.22, 0);
      }
    }, 22);

  W.wing = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(-1, 0.25);
      P.quadraticCurveTo(-0.3, -0.25, 0.15, -0.95); // leading edge
      P.quadraticCurveTo(0.45, -0.6, 1.05, -0.7);
      // scalloped trailing edge between finger bones
      const tips = [[1.05, -0.7], [0.9, -0.2], [0.6, 0.18], [0.2, 0.42], [-0.3, 0.5], [-1, 0.25]];
      for (let i = 1; i < tips.length; i++) {
        const [ax, ay] = tips[i - 1], [bx, by] = tips[i];
        P.quadraticCurveTo((ax + bx) / 2 - 0.12, (ay + by) / 2 - 0.12, bx, by);
      }
      for (const [bx, by] of tips.slice(1, 5)) { P.moveTo(0.15, -0.95); P.lineTo(bx, by); }
    }, 14);

  // ---- fleur-de-lis (France) -------------------------------------------------------
  W.fleur = (ctx, x, y, s, o = {}) =>
    stroked(ctx, x, y, s, o, (P) => {
      P.moveTo(0, -1); P.bezierCurveTo(0.35, -0.6, 0.3, -0.1, 0, 0.25); P.bezierCurveTo(-0.3, -0.1, -0.35, -0.6, 0, -1);
      for (const d of [-1, 1]) {
        P.moveTo(d * 0.12, 0.05);
        P.bezierCurveTo(d * 0.5, -0.55, d * 1.05, -0.25, d * 0.8, 0.05);
        P.bezierCurveTo(d * 0.65, -0.1, d * 0.45, 0.0, d * 0.3, 0.3);
      }
      P.moveTo(-0.45, 0.3); P.lineTo(0.45, 0.3); P.lineTo(0.45, 0.42); P.lineTo(-0.45, 0.42); P.closePath();
      P.moveTo(0, 0.42); P.bezierCurveTo(0.15, 0.6, 0.25, 0.75, 0.15, 0.95); P.moveTo(0, 0.42); P.bezierCurveTo(-0.15, 0.6, -0.25, 0.75, -0.15, 0.95);
    }, 11);

  // ---- formation node (person) used in diagrams ----------------------------------
  /** A person node: ring + inner disc, optional crown on top. */
  W.node = (ctx, x, y, r, o = {}) => {
    const p = o.p == null ? 1 : o.p;
    if (p <= 0) return;
    const sc = 0.6 + 0.4 * W.E.outBack(W.clamp(p));
    ctx.save();
    ctx.globalAlpha *= W.clamp(p * 1.6) * (o.alpha == null ? 1 : o.alpha);
    ctx.translate(x, y);
    ctx.scale(sc, sc);
    const col = o.color || W.C.ivory;
    if (o.halo) {
      const g = ctx.createRadialGradient(0, 0, r * 0.5, 0, 0, r * 3.2);
      g.addColorStop(0, W.rgba(o.halo, 0.35)); g.addColorStop(1, W.rgba(o.halo, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r * 3.2, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = W.C.bg;
    ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = col; ctx.lineWidth = o.width || 2.5;
    ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke();
    if (o.filled !== false) { ctx.fillStyle = col; ctx.beginPath(); ctx.arc(0, 0, r * 0.55, 0, Math.PI * 2); ctx.fill(); }
    if (o.dead) {
      ctx.strokeStyle = W.C.bg; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(0, -r * 0.42); ctx.lineTo(0, r * 0.42); ctx.moveTo(-r * 0.24, -r * 0.14); ctx.lineTo(r * 0.24, -r * 0.14); ctx.stroke();
    }
    ctx.restore();
    if (o.crown) W.crown(ctx, x, y - r * 1.9 * sc, r * 0.72, { color: o.crownColor || W.C.gold, width: 2, fill: 0.2, p: o.crown === true ? 1 : o.crown });
  };
})();
