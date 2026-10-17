/* Act II — the weak king: Henry VI, Margaret, the court, Ireland, the Protectorate */
(function () {
  const { W } = window;
  const { p, E } = W;

  /** draw content into a layer, then render it broken into shards (p = 0 intact .. 1 scattered) */
  W.shatter = (ctx, cx, cy, size, sp, drawFn, seed = 5) => {
    const L = size * 2;
    const [cv, lx] = W.layer('shatter', L, L);
    drawFn(lx, L / 2, L / 2);
    if (sp <= 0.001) { ctx.drawImage(cv, cx - L / 2, cy - L / 2); return; }
    const r = W.rng(seed);
    const cuts = [-0.62, -0.22, 0.2, 0.58].map((u) => u * size);
    const xs = [-size, ...cuts, size];
    const jag = (x) => { const pts = []; for (let k = 0; k <= 6; k++) pts.push([x + (W.hash(x * 0.37 + k * 13.1) - 0.5) * size * 0.16, -size + (k / 6) * size * 2]); return pts; };
    const lines = xs.map((x, i) => (i === 0 || i === xs.length - 1 ? [[x, -size], [x, size]] : jag(x)));
    for (let i = 0; i < xs.length - 1; i++) {
      const a = lines[i], b = lines[i + 1];
      const dir = (i - (xs.length - 2) / 2);
      const ox = dir * 46 * sp + (r() - 0.5) * 30 * sp, oy = (r() * 70 + 20) * sp, rot = (r() - 0.5) * 0.5 * sp;
      ctx.save();
      ctx.translate(cx + ox, cy + oy);
      ctx.rotate(rot);
      ctx.beginPath();
      a.forEach((q, k) => (k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])));
      for (let k = b.length - 1; k >= 0; k--) ctx.lineTo(b[k][0], b[k][1]);
      ctx.closePath();
      ctx.clip();
      ctx.globalAlpha *= 1 - sp * 0.35;
      ctx.drawImage(cv, -L / 2, -L / 2);
      ctx.restore();
    }
  };

  // ---------------------------------------------------------------- weak_king
  W.scene('weak_king', {
    bg: () => ({ glow: '#2a1c17', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const pull = p(t, c.adv, 1.2);
      const hx = 900 + Math.sin(t * 1.3) * 16 * pull, hy = 600 + Math.sin(t * 0.9) * 10 * pull;
      // advisers and their strings
      const adv = [600, 800, 1000, 1200];
      adv.forEach((x, i) => {
        const ap = p(t, c.adv + i * 0.18, 0.8);
        W.node(ctx, x, 250, 10, { p: ap, color: W.C.ivoryDim, filled: false });
        const sp = p(t, c.adv + 0.3 + i * 0.18, 1.0, E.inOut);
        if (sp > 0) {
          const sway = Math.sin(t * 1.6 + i) * 18;
          const pts = []; for (let k = 0; k <= 24; k++) { const u = k / 24; pts.push([W.lerp(x, hx, u) + Math.sin(u * Math.PI) * sway, W.lerp(262, hy - 70, u)]); }
          W.strokePoly(ctx, pts, sp, { color: W.rgba(W.C.ivory, 0.32), width: 1.2 });
        }
      });
      W.text(ctx, T.adv, 900, 190, { size: 28, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.adv + 0.5, 0.8) });
      W.node(ctx, hx, hy, 18, { p: p(t, c.henry, 0.8), color: W.C.crimsonBright, crown: p(t, c.henry + 0.2, 1), crownColor: W.C.gold, portrait: 'p_henry6', pr: 58 });
      const hp6 = W.hasPortrait('p_henry6') ? 40 : 0;
      W.text(ctx, T.h6, hx, hy + 62 + hp6, { size: 46, color: W.C.ivory, reveal: p(t, c.henry + 1.5, 0.8) });
      W.text(ctx, T.weak, hx, hy + 112 + hp6, { size: 28, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.weak + 1.6, 0.8) });
      // Margaret of Anjou, from France
      const mx = 1480, my = 600;
      W.fleur(ctx, mx, my - 110 - (W.hasPortrait('p_margaret') ? 40 : 0), 40, { p: p(t, c.m - 0.3, 1.2, E.inOut), color: W.C.gold, width: 2, fill: 0.15 });
      W.node(ctx, mx, my, 16, { p: p(t, c.m, 0.8), color: W.C.crimsonBright, portrait: 'p_margaret', pr: 58 });
      const mp = W.hasPortrait('p_margaret') ? 40 : 0;
      W.text(ctx, T.m, mx, my + 62 + mp, { size: 46, color: W.C.ivory, reveal: p(t, c.m + 0.1, 0.8) });
      W.text(ctx, T.mSub, mx, my + 112 + mp, { size: 26, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.france - 0.4, 0.8) });
      const lp = p(t, c.m + 0.3, 1.0, E.inOut);
      W.strokePoly(ctx, [[hx + 30, hy], [mx - 30, my]], lp, { color: W.rgba(W.C.gold, 0.6), width: 1.5, dash: [3, 6] });
      W.rings(ctx, (hx + mx) / 2, my - 4, 26, { p: p(t, c.m + 0.8, 1.0), color: W.C.gold, width: 2 });
    },
  });

  // ---------------------------------------------------------------- margaret
  W.scene('margaret', {
    bg: () => ({ glow: '#331617', glowA: 0.55 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const hasM = W.portrait(ctx, 'p_margaret', W.W / 2, 245, 118, { shape: 'oval', ry: 150, p: p(t, 95.0, 1.4) });
      if (!hasM) W.crown(ctx, W.W / 2, 255, 62, { p: p(t, 95.0, 1.4, E.inOut), color: W.C.crimsonBright, width: 2.4, fill: 0.2, glow: 'rgba(207,42,60,0.4)' });
      W.text(ctx, T.m, W.W / 2, hasM ? 480 : 420, { size: 100, color: W.C.ivory, reveal: p(t, c.m, 1.0), rise: 12 });
      W.words(ctx, `${T.w1} · ${T.w2} · ${T.w3}`, W.W / 2, hasM ? 600 : 560, t, [c.w1, c.w2 - 0.2, c.w2, c.w3 - 0.2, c.w3], {
        size: 60, fam: W.F.title, colors: [W.C.ivory, W.C.gold, W.C.ivory, W.C.gold, W.C.crimsonBright],
      });
      // anyone threatening her power
      const xs = [520, 740, 960, 1180, 1400];
      xs.forEach((x, i) => {
        const tp = p(t, c.threat + i * 0.12, 0.6);
        const isYork = i === 2;
        const dim = isYork ? 0 : p(t, c.ry - 0.6, 0.8);
        W.alpha(ctx, 1 - dim * 0.8, () => {
          W.strokePoly(ctx, [[W.W / 2, hasM ? 660 : 300], [x, 800]], tp, { color: W.rgba(W.C.crimsonBright, 0.28), width: 1.2, dash: [4, 6], dashOffset: -t * 20 });
          W.node(ctx, x, 820, isYork ? 16 : 10, { p: tp, color: isYork ? W.C.ivory : W.C.ivoryDim, halo: isYork && t > c.ry ? W.C.ivory : null, portrait: isYork && t > c.ry - 0.3 ? 'p_york' : null, pr: 48 });
        });
      });
      // tension line queen -> York vibrates
      const yp = p(t, c.ry, 0.6);
      if (yp > 0) {
        const pts = []; for (let k = 0; k <= 50; k++) { const u = k / 50; pts.push([960 + Math.sin(u * 30 - t * 18) * 5 * Math.sin(u * Math.PI) * yp, W.lerp(hasM ? 660 : 300, W.hasPortrait('p_york') ? 762 : 800, u)]); }
        W.strokePoly(ctx, pts, yp, { color: W.rgba(W.C.crimsonBright, 0.9), width: 2 });
      }
      W.text(ctx, T.ry, W.W / 2, W.hasPortrait('p_york') ? 922 : 905, { size: 46, color: W.C.ivory, reveal: p(t, c.ry + 0.1, 0.8) });
    },
  });

  // ---------------------------------------------------------------- court
  W.scene('court', {
    bg: () => ({ glow: '#2a2018', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const cx = 960, cy = 560, r1 = 240, r2 = 400;
      const rot = t * 0.06;
      // rings of the court
      for (const [r, d] of [[r1, 0], [r2, 0.3]]) {
        const rp = p(t, 102.5 + d, 1.4, E.inOut);
        ctx.save(); ctx.strokeStyle = W.rgba(W.C.ivory, 0.38); ctx.lineWidth = 1.4; ctx.setLineDash([2, 7]);
        ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * rp); ctx.stroke(); ctx.restore();
      }
      W.text(ctx, 'البلاط', cx + r2 + 20, cy - r2 + 30, { size: 26, fam: W.F.label, weight: 400, color: W.C.ivoryDim, align: 'left', alpha: p(t, 103, 0.8) });
      W.node(ctx, cx, cy, 18, { p: p(t, 102.6, 0.8), color: W.C.crimsonBright, crown: 1, crownColor: W.C.gold, portrait: 'p_henry6', pr: 52 });
      W.text(ctx, T.king, cx, cy + (W.hasPortrait('p_henry6') ? 92 : 58), { size: 34, color: W.C.ivory, alpha: p(t, 102.8, 0.8) });
      // York: from the inner circle out to the margins
      const mv = p(t, c.push, 2.0, E.inOut);
      const ang = W.lerp(-0.4, Math.PI * 0.95, mv) + rot * (1 - mv);
      const rr = W.lerp(r1, r2 + 60, mv);
      const yx = cx + Math.cos(ang) * rr, yy = cy + Math.sin(ang) * rr;
      W.node(ctx, yx, yy, 15, { p: p(t, 102.9, 0.8), color: W.C.ivory, halo: mv < 0.2 ? W.C.ivory : null, portrait: 'p_york', pr: 44 });
      const yo = W.hasPortrait('p_york') ? 34 : 0;
      W.text(ctx, T.ry, yx, yy + 48 + yo, { size: 40, color: W.C.ivory, alpha: p(t, 103.0, 0.8) });
      W.text(ctx, T.role, yx, yy + 92 + yo, { size: 24, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.adviser, 0.8) * (1 - p(t, c.push, 0.6)) });
      W.text(ctx, T.out, yx, yy + 92 + yo, { size: 30, fam: W.F.label, weight: 500, color: W.C.crimsonBright, alpha: p(t, c.push + 1.2, 0.6) });
      // queen's favourites take the inner seats
      for (const [cue, a0, label] of [[c.suf, -0.55, T.suf], [c.som, 0.55, T.som]]) {
        const q = p(t, cue - 0.3, 1.0, E.out);
        const a = a0 + rot * 0.3, R = W.lerp(r2 + 80, r1 * 0.75, q);
        const x = cx + Math.cos(a) * R, y = cy + Math.sin(a) * R;
        W.node(ctx, x, y, 14, { p: q, color: W.C.crimsonBright });
        W.text(ctx, label, x + 34, y, { size: 34, color: W.C.crimsonBright, align: 'left', alpha: p(t, cue, 0.6) });
      }
      W.text(ctx, 'أنصار الملكة', 1500, 700, { size: 26, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.favour, 0.8) * 0 });
    },
  });

  // ---------------------------------------------------------------- ireland (map)
  W.scene('ireland', {
    bg: () => ({ glow: '#1e2224', glowA: 0.45 }),
    dust: 14,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const v0 = { lon: -3.0, lat: 52.2, k: 112 }, v1 = { lon: -4.4, lat: 52.9, k: 128 }, v2 = { lon: -3.0, lat: 52.6, k: 150 };
      let view = W.lerpView(v0, v1, p(t, c.removed, 3.0, E.inOut));
      view = W.lerpView(view, v2, p(t, c.corrupt, 3.5, E.inOut));
      W.drawMap(ctx, t, view, {
        reveal: p(t, S.start, 1.8, E.inOut), ireland: true, continent: true, regionLabels: true,
        tint: [
          { region: 'france', at: [0.5, 49.0], r: 420, color: W.C.crimson, a: p(t, c.fr, 0.8) * (0.75 + 0.25 * Math.sin(t * 4)) * (1 - p(t, c.removed + 0.8, 1)) },
          { region: 'britain', at: [-1.2, 52.4], r: 520, color: W.C.crimson, a: p(t, c.anger - 0.6, 1.2) * (0.7 + 0.3 * Math.sin(t * 3)) * (1 - p(t, c.ret + 1.5, 1.0)) },
        ],
      });
      const L = W.place(view, 'london'), D = W.place(view, 'dublin');
      W.marker(ctx, L[0], L[1], t, S.start + 0.8, { label: 'لندن', side: 'right', dist: 60 });
      // French war losses
      const F = W.proj(view, [0.6, 49.15]);
      W.alpha(ctx, 1 - p(t, c.removed + 0.8, 0.8), () => {
        W.text(ctx, T.fr, F[0], F[1] - 18, { size: 34, color: W.C.ivory, reveal: p(t, c.fr, 0.8) });
        W.text(ctx, T.frSub, F[0], F[1] + 24, { size: 24, fam: W.F.label, weight: 400, color: W.C.crimsonBright, alpha: p(t, c.fr + 0.4, 0.7) });
      });
      // York sent to Ireland
      const out = W.arcPts(L, D, 0.18, 60);
      const op = p(t, c.removed, 2.2, E.inOut);
      W.alpha(ctx, 1 - p(t, c.ret - 0.4, 0.8) * 0.6, () => W.route(ctx, out, t, op, { color: W.C.ivory }));
      if (op > 0 && op < 1) { const h = W.polyPart(out, op).pop(); W.node(ctx, h[0], h[1], 9, { color: W.C.ivory }); }
      W.marker(ctx, D[0], D[1], t, c.ireland, { label: T.exile, side: 'left', dist: 70, color: W.C.ivory });
      // popular anger: unrest pulses over England
      const spots = [[-0.9, 51.3], [0.5, 51.4], [-1.6, 52.4], [-1.1, 53.4], [-2.4, 52.9], [0.9, 52.3], [-2.5, 51.4], [-1.5, 54.4]];
      spots.forEach((ll, i) => {
        const sp = p(t, c.anger + i * 0.12, 0.4) * (1 - p(t, c.ret + 1.5, 0.8));
        if (sp <= 0) return;
        const [x, y] = W.proj(view, ll);
        const q = ((t * 0.9 + i * 0.37) % 1);
        ctx.save();
        ctx.strokeStyle = W.rgba(W.C.crimsonBright, (1 - q) * 0.8 * sp); ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(x, y, 5 + q * 26, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = W.rgba(W.C.crimsonBright, 0.9 * sp); ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
      });
      // return with an army: Dublin -> Anglesey/N. Wales -> Ludlow -> London
      const ret = [D, W.proj(view, [-4.1, 53.27]), W.proj(view, [-3.1, 52.9]), W.place(view, 'ludlow'), W.proj(view, [-1.3, 51.75]), L];
      const smooth = [];
      for (let i = 0; i < ret.length - 1; i++) smooth.push(...W.arcPts(ret[i], ret[i + 1], i === 0 ? 0.12 : 0.04, 20).slice(i ? 1 : 0));
      const rp = p(t, c.ret, 3.2, E.inOut);
      W.route(ctx, smooth, t, rp, { color: W.C.ivory, width: 4 });
      if (rp > 0 && rp < 1) {
        const h = W.polyPart(smooth, rp).pop();
        W.formation(ctx, h[0], h[1] - 28, t, { cols: 5, rows: 2, gap: 9, unit: 5, color: W.C.ivory, frame: false });
      }
      // caption panel (one message at a time)
      const capX = 1760, capY = 230;
      W.alpha(ctx, W.env(t, c.crit, c.removed + 1.4, 0.4, 0.5), () => W.caption(ctx, capX, capY, t, c.crit, { kicker: 'دوق يورك', title: 'ينتقد إدارة الحرب', sub: 'فيُبعد عن البلاط' }));
      W.alpha(ctx, W.env(t, c.anger - 0.2, c.ret, 0.4, 0.5), () => W.caption(ctx, capX, capY, t, c.anger - 0.2, { kicker: 'فساد وإخفاقات عسكرية', title: T.anger }));
      W.alpha(ctx, W.env(t, c.ret, S.end + 1, 0.4, 0.5), () => W.caption(ctx, capX, capY, t, c.ret, { kicker: 'سبتمبر 1450', title: 'العودة بجيش', sub: T.som }));
    },
  });

  // ---------------------------------------------------------------- protector
  W.scene('protector', {
    bg: () => ({ glow: '#2a1b18', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      // crown: Henry VI's authority
      const crack = p(t, c.broke, 0.5);
      const shards = p(t, c.broke + 0.5, 1.6, E.out) * (1 - p(t, c.rec, 1.6, E.inOut));
      const reformed = p(t, c.rec, 1.6, E.inOut);
      const cx = W.lerp(960, 960, reformed), cy = W.lerp(380, 300, reformed);
      const crownAlpha = 1 - shards * 0.55;
      W.alpha(ctx, crownAlpha, () =>
        W.shatter(ctx, cx, cy, 190, shards, (lx, x, y) => {
          W.crown(lx, x, y, 120, { p: p(t, S.start, 1.2, E.inOut), color: W.C.crimsonBright, width: 3, fill: 0.18 });
          if (crack > 0 && shards < 0.05 && reformed < 0.5) {
            const pts = [[x - 30, y - 70], [x - 5, y - 20], [x - 25, y + 10], [x + 8, y + 40], [x - 6, y + 70]];
            W.strokePoly(lx, pts, crack, { color: W.C.ivory, width: 2.5 });
          }
        })
      );
      // failed first attempt
      W.alpha(ctx, W.env(t, c.fail, c.broke, 0.3, 0.5), () => W.text(ctx, T.fail, W.W / 2, 640, { size: 46, color: W.C.ivoryDim, reveal: p(t, c.fail, 0.7) }));
      W.alpha(ctx, W.env(t, c.broke, c.prot, 0.3, 0.5), () => W.text(ctx, T.broke, W.W / 2, 640, { size: 46, color: W.C.ivory, reveal: p(t, c.broke + 0.1, 0.8) }));
      // York becomes Protector: shield rises; later slides away and dims
      const sp = p(t, c.prot, 1.2, E.out), away = p(t, c.rec - 0.3, 1.4, E.inOut), dimS = p(t, c.removed, 1.0);
      const sx = W.lerp(960, 520, away), sy = W.lerp(560 + (1 - sp) * 80, 600, away);
      W.alpha(ctx, sp * (1 - dimS * 0.55), () => {
        W.shield(ctx, sx, sy, W.lerp(95, 70, away), { p: p(t, c.prot, 1.6, E.inOut), color: W.C.ivory, width: 2.5, fill: 0.12 });
        W.rose(ctx, sx, sy - 6, W.lerp(38, 28, away), { kind: 'york', bloom: p(t, c.prot + 0.5, 1.2) });
        W.text(ctx, T.prot, sx, sy + W.lerp(170, 130, away), { size: W.lerp(84, 52, away), color: W.C.ivory, reveal: p(t, c.prot + 0.2, 0.9) });
        W.text(ctx, T.protSub, sx, sy + W.lerp(240, 182, away), { size: 34, fam: W.F.latin, weight: 600, color: W.C.gold, dir: 'ltr', alpha: p(t, c.year, 0.8) });
      });
      // recovery + reversal
      W.alpha(ctx, W.env(t, c.rec, S.end + 1, 0.4, 0.4), () => W.text(ctx, T.rec, W.W / 2, 470, { size: 40, fam: W.F.label, weight: 500, color: W.C.gold, reveal: p(t, c.rec + 0.3, 0.8) }));
      const items = [T.r1, T.r2, T.r3];
      items.forEach((s, i) => {
        const y = 600 + i * 74, x = 1420;
        const ip = p(t, c.queen + i * 0.18, 0.7);
        W.text(ctx, s, x, y, { size: 40, color: W.C.ivory, alpha: ip * (1 - p(t, c.undo + i * 0.3, 0.6) * 0.5), reveal: ip });
        W.strike(ctx, x, y + 2, W.measure(ctx, s, { size: 40 }) + 30, p(t, c.undo + i * 0.3, 0.45), W.C.crimsonBright, 4);
      });
      W.text(ctx, T.undo, 1420, 530, { size: 26, fam: W.F.label, weight: 500, color: W.C.crimsonBright, alpha: p(t, c.undo, 0.6) });
    },
  });
})();
