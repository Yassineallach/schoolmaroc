/* Act VI — the united rose: Henry Tudor, the landing, Bosworth, the Tudor rose */
(function () {
  const { W } = window;
  const { p, E } = W;

  // ---------------------------------------------------------------- channel
  W.scene('channel', {
    bg: () => ({ glow: '#1e1b1a', glowA: 0.45 }),
    dust: 12,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const view = W.lerpView({ lon: -2.4, lat: 51.4, k: 110 }, { lon: -2.6, lat: 50.6, k: 125 }, p(t, S.start, 4, E.inOutSine));
      const pulse = p(t, c.danger, 1.0) * (0.75 + 0.25 * Math.sin(t * 3.2));
      W.drawMap(ctx, t, view, {
        reveal: p(t, S.start + 0.2, 1.6, E.inOut), continent: true, ireland: true, regionLabels: true, channel: p(t, c.channel, 0.8),
        tint: [{ region: 'france', at: [-2.5, 48.3], r: 380, color: W.C.crimson, a: pulse }],
      });
      const B = W.place(view, 'brittany');
      W.marker(ctx, B[0], B[1], t, c.danger, { label: 'بريتاني', side: 'left', dist: 60, color: W.C.crimsonBright, size: 32 });
      W.text(ctx, T.danger, W.W / 2, 930, { size: 56, color: W.C.ivory, reveal: p(t, c.danger + 0.3, 0.9) });
    },
  });

  // ---------------------------------------------------------------- tudor
  W.scene('tudor', {
    bg: () => ({ glow: '#2a1a17', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const phaseB = p(t, c.split - 0.6, 1.0, E.inOut);
      // lineage: John of Gaunt -> Beauforts -> Margaret Beaufort -> Henry Tudor
      W.alpha(ctx, 1 - phaseB, () => {
        const chain = [
          { y: 200, label: T.jg, sub: 'آل لانكاستر', r: 14, col: W.C.crimsonBright, size: 40 },
          { y: 345, label: 'جون بوفورت', r: 7, col: W.C.ivoryDim, size: 28 },
          { y: 470, label: 'جون بوفورت، دوق سومرست', r: 7, col: W.C.ivoryDim, size: 28 },
          { y: 595, label: 'مارغريت بوفورت', sub: 'والدته', r: 9, col: W.C.ivoryDim, size: 30 },
        ];
        const lp = p(t, c.desc, 1.6, E.inOut); // drawn upward from Henry to Gaunt
        W.strokePoly(ctx, [[960, 730], [960, 214]], lp, { color: W.rgba(W.C.crimsonBright, 0.55), width: 2, dash: [3, 7] });
        chain.forEach((n, i) => {
          const np = p(t, c.desc + (3 - i) * 0.3, 0.7);
          const pk = i === 0 ? 'p_gaunt' : null, pad = W.hasPortrait(pk) ? 52 : n.r;
          W.node(ctx, 960, n.y, n.r, { p: np, color: n.col, halo: i === 0 && t > c.lan ? W.C.crimson : null, portrait: pk, pr: 44 });
          W.text(ctx, n.label, 930 - pad, n.y, { size: n.size, color: i === 0 ? W.C.crimsonBright : W.C.ivory, align: 'right', alpha: i === 0 ? p(t, c.lan, 0.7) : np * 0.85 });
          if (n.sub) W.text(ctx, n.sub, 1000 + (i === 0 && W.hasPortrait('p_gaunt') ? 30 : 0), n.y, { size: 24, fam: W.F.label, weight: 400, color: W.C.ivoryDim, align: 'left', alpha: i === 0 ? p(t, c.lan + 0.3, 0.7) : np * 0.85 });
        });
        W.node(ctx, 960, 760, 20, { p: p(t, c.ht, 0.8), color: W.C.crimsonBright, halo: W.C.crimson });
        W.text(ctx, T.ht, 960, 840, { size: 64, color: W.C.ivory, reveal: p(t, c.ht + 0.1, 0.9) });
        W.text(ctx, T.htSub, 960, 905, { size: 26, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.lan, 0.8) });
        W.caption(ctx, 1700, 760, t, c.exile, { kicker: '1471 — 1485', title: T.exile, sub: 'في بريتاني وفرنسا', size: 44, align: 'right' });
      });
      if (phaseB <= 0) return;
      // York divided: the white rose splits, supporters drift to Henry
      W.alpha(ctx, phaseB, () => {
        const rx = 620, ry = 470, s = 150;
        const sp = p(t, c.split, 1.4, E.out);
        const L = 420;
        const [cv, lx] = W.layer('rose', L, L);
        W.rose(lx, L / 2, L / 2, s, { kind: 'york', spin: 0 });
        for (const side of [-1, 1]) {
          ctx.save();
          ctx.translate(rx + side * sp * 40, ry + sp * 10);
          ctx.rotate(side * sp * 0.12);
          ctx.beginPath();
          // jagged split line
          const pts = []; for (let k = 0; k <= 8; k++) pts.push([(W.hash(k * 3.3) - 0.5) * 26, -L / 2 + (k / 8) * L]);
          ctx.moveTo(side * L / 2, -L / 2);
          pts.forEach((q) => ctx.lineTo(q[0], q[1]));
          ctx.lineTo(side * L / 2, L / 2);
          ctx.closePath();
          ctx.clip();
          ctx.drawImage(cv, -L / 2, -L / 2);
          ctx.restore();
        }
        W.text(ctx, T.split, rx, 700, { size: 52, color: W.C.ivory, reveal: p(t, c.split + 0.3, 0.9) });
        const hx = 1350;
        W.node(ctx, hx, ry, 22, { p: phaseB, color: W.C.crimsonBright, halo: W.C.crimson, crown: p(t, c.sup + 0.8, 1), crownColor: W.C.gold });
        W.text(ctx, T.ht, hx, ry + 70, { size: 50, color: W.C.ivory, alpha: phaseB });
        for (let i = 0; i < 8; i++) {
          const r = W.rng(50 + i);
          const sx = rx + (r() - 0.5) * 260, sy = ry + (r() - 0.5) * 260;
          const ang = (i / 8) * Math.PI * 2;
          const tx = hx + Math.cos(ang) * 95, ty = ry + Math.sin(ang) * 95;
          const m = p(t, c.sup + i * 0.1, 1.6, E.inOut);
          W.node(ctx, W.lerp(sx, tx, m), W.lerp(sy, ty, m), 7, { p: p(t, c.york + i * 0.05, 0.5), color: W.mixColor(W.C.ivory, W.C.crimsonBright, m * 0.4), width: 1.6 });
        }
        W.text(ctx, T.sup, hx, ry + 140, { size: 30, fam: W.F.label, weight: 500, color: W.C.gold, alpha: p(t, c.sup + 0.5, 0.8) });
      });
    },
  });

  // ---------------------------------------------------------------- landing
  W.scene('landing', {
    bg: () => ({ glow: '#1f1c1a', glowA: 0.45 }),
    dust: 10,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const view = W.lerpView({ lon: -2.6, lat: 50.6, k: 125 }, { lon: -3.0, lat: 51.9, k: 175 }, p(t, c.year - 0.3, 2.4, E.inOut));
      W.drawMap(ctx, t, view, { reveal: 1, continent: true, ireland: true, regionLabels: true, channel: 1 - p(t, c.year, 1) });
      const H = W.place(view, 'harfleur'), M = W.place(view, 'milford'), B = W.place(view, 'bosworth');
      W.marker(ctx, H[0], H[1], t, c.army + 0.2, { label: T.dep, sub: '1 أغسطس 1485', side: 'right', dist: 60, color: W.C.crimsonBright, size: 32 });
      const sea = [[0.2, 49.51], [-1.5, 50.05], [-3.8, 49.9], [-5.6, 49.75], [-6.2, 50.4], [-5.7, 51.25], [-5.03, 51.71]].map((ll) => W.proj(view, ll));
      const seaS = []; for (let i = 0; i < sea.length - 1; i++) seaS.push(...W.arcPts(sea[i], sea[i + 1], 0.05, 12).slice(i ? 1 : 0));
      W.route(ctx, seaS, t, p(t, c.fr, 2.2, E.inOut), { color: W.C.crimsonBright, width: 3 });
      W.marker(ctx, M[0], M[1], t, c.year, { label: T.land, sub: T.landSub, side: 'left', dist: 70, color: W.C.crimsonBright, size: 36 });
      const land = [M, W.proj(view, [-3.9, 52.4]), W.proj(view, [-2.75, 52.71]), B];
      const landS = []; for (let i = 0; i < land.length - 1; i++) landS.push(...W.arcPts(land[i], land[i + 1], 0.06, 12).slice(i ? 1 : 0));
      W.route(ctx, landS, t, p(t, c.year + 0.4, 1.8, E.inOut), { color: W.C.crimsonBright, width: 4 });
      W.marker(ctx, B[0], B[1], t, c.year + 1.9, { kind: 'battle', label: T.bos, side: 'right', dist: 60, color: W.C.ivory, size: 40 });
    },
  });

  // ---------------------------------------------------------------- bosworth
  W.scene('bosworth', {
    bg: () => ({ glow: '#2c1715', glowA: 0.5 }),
    dust: 8,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      W.terrain(ctx, t, 11, 1);
      const conv = p(t, S.start, 1.2, E.inOut), br = p(t, c.r3 + 0.2, 1.2, E.out);
      W.formation(ctx, W.lerp(1420, 1080, conv), 470, t, { cols: 8, rows: 3, color: W.C.ivory, scatter: br, retreat: 1, seed: 41 });
      W.formation(ctx, W.lerp(1440, 1100, conv), 690, t, { cols: 6, rows: 3, color: W.C.ivory, scatter: br, retreat: 1, seed: 42 });
      W.formation(ctx, W.lerp(480, 830, conv), 580, t, { cols: 8, rows: 3, color: W.C.crimsonBright, seed: 43 });
      W.bigArrow(ctx, [420, 580], [W.lerp(560, 900, conv), 580], p(t, S.start, 1.0), { color: W.C.crimsonBright, width: 22 });
      W.text(ctx, T.ht, 640, 470, { size: 36, color: W.C.crimsonBright, alpha: p(t, S.start + 0.2, 0.5) });
      W.text(ctx, T.r3, 1300, 360, { size: 36, color: W.C.ivory, alpha: p(t, S.start + 0.2, 0.5) * (1 - br * 0.5) });
      // Richard's crown falls
      const fall = p(t, c.r3 + 0.3, 1.3, E.inCubic);
      const cx = W.lerp(1230, 1300, fall), cy = W.lerp(300, 830, fall);
      W.alpha(ctx, 1 - p(t, c.quick, 0.6), () => W.crown(ctx, cx, cy, 34, { color: W.C.gold, width: 2.2, fill: 0.25, rot: fall * 2.4 }));
      W.caption(ctx, 1760, 200, t, S.start, { kicker: T.btSub, title: T.bt, size: 54 });
      W.illustrative(ctx, p(t, S.start + 0.3, 0.6));
    },
  });

  // ---------------------------------------------------------------- tudor_rose
  W.scene('tudor_rose', {
    bg: () => ({ glow: '#3a2a1b', glowA: 0.6 }),
    dust: 40,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const up = p(t, c.unite - 0.4, 1.2, E.inOut); // nodes move up to make room for the rose
      const ny = W.lerp(480, 240, up);
      W.node(ctx, 1250, ny, 18, { p: p(t, c.wed, 0.7), color: W.C.crimsonBright, crown: 1, crownColor: W.C.gold });
      W.text(ctx, T.h7, 1250, ny + 62, { size: 44, color: W.C.ivory, alpha: p(t, c.wed + 0.2, 0.7) });
      W.node(ctx, 670, ny, 16, { p: p(t, c.eliz, 0.7), color: W.C.ivory });
      W.text(ctx, T.eliz, 670, ny + 62, { size: 44, color: W.C.ivory, alpha: p(t, c.eliz + 0.2, 0.7) });
      W.text(ctx, T.elizSub, 670, ny + 108, { size: 26, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.sister, 0.7) * (1 - up) });
      W.strokePoly(ctx, [[1220, ny], [700, ny]], p(t, c.eliz + 0.3, 1.0, E.inOut), { color: W.rgba(W.C.gold, 0.7), width: 1.8 });
      W.rings(ctx, 960, ny - 40, 24, { p: p(t, c.eliz + 0.6, 1.0), color: W.C.gold, width: 2 });
      W.text(ctx, T.wed, 960, ny + 30, { size: 30, fam: W.F.latin, weight: 600, color: W.C.gold, dir: 'ltr', alpha: p(t, c.eliz + 1.0, 0.7) });
      // the two roses travel inwards and merge into the Tudor rose
      const m = p(t, c.unite, 1.6, E.inOut);
      const merged = p(t, c.roses + 0.6, 1.4, E.out);
      W.alpha(ctx, 1 - merged, () => {
        W.rose(ctx, W.lerp(1250, 960, m), 600, W.lerp(80, 150, m), { kind: 'lancaster', bloom: p(t, c.unite - 0.6, 1), spin: m * 0.6 });
        W.rose(ctx, W.lerp(670, 960, m), 600, W.lerp(80, 82, m), { kind: 'york', bloom: p(t, c.unite - 0.4, 1), spin: -m * 0.6 });
      });
      if (merged > 0) {
        const g = ctx.createRadialGradient(960, 600, 0, 960, 600, 330);
        g.addColorStop(0, W.rgba(W.C.gold, 0.25 * merged)); g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g; ctx.fillRect(560, 200, 800, 800);
        W.rose(ctx, 960, 600, 150, { kind: 'tudor', bloom: merged, spin: (t - c.roses) * 0.03, alpha: merged });
      }
      W.text(ctx, T.tudor, 960, 815, { size: 56, color: W.C.ivory, reveal: p(t, c.roses + 1.0, 0.9) });
      W.text(ctx, T.end, 960, 885, { size: 34, fam: W.F.label, weight: 400, color: W.C.ivoryDim, reveal: p(t, c.end, 0.9) });
      W.text(ctx, '1399 — 1485', 960, 940, { size: 26, fam: W.F.latin, weight: 400, color: W.C.gold, dir: 'ltr', tracking: 6, alpha: p(t, c.end + 0.6, 0.8) });
    },
  });
})();
