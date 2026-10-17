/* Act I — the roots: Edward III, the succession, the two roses, Henry IV, Henry VI */
(function () {
  const { W } = window;
  const { p, E } = W;

  // ---------------------------------------------------------------- edward3
  W.scene('edward3', {
    bg: () => ({ glow: '#33281a', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      const death = p(t, c.death, 1.6, E.inOut);
      const col = W.mixColor(W.C.gold, W.C.mute, death);
      if (W.hasPortrait('p_edward3')) {
        W.portrait(ctx, 'p_edward3', W.W / 2, 300, 170, { shape: 'oval', ry: 215, p: p(t, 31.2, 1.6), dead: death > 0.5 });
      } else W.crown(ctx, W.W / 2, 330 + death * 14, 120, { p: p(t, 31.4, 1.8, E.inOut), color: col, width: 2.6, fill: 0.16 * (1 - death * 0.6), glow: death < 0.5 ? 'rgba(201,164,92,0.35)' : null });
      W.text(ctx, T.name, W.W / 2, 610, { size: 96, color: W.C.ivory, reveal: p(t, c.name - 0.1, 1.1), rise: 14 });
      W.year(ctx, T.year, W.W / 2, 760, t, c.year, { size: 130, color: W.C.gold });
      W.text(ctx, T.sub, W.W / 2, 880, { size: 30, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.death, 0.9) });
      W.dagger(ctx, W.W / 2 + W.measure(ctx, T.name, { size: 104 }) / 2 + 60, 585, 26, { p: p(t, c.death + 0.2, 0.8), color: W.C.ivoryDim, width: 2 });
    },
  });

  // ---------------------------------------------------------------- succession_tree
  const X = { bp: 1560, li: 1260, jg: 960, el: 660, tw: 360 };
  W.scene('succession_tree', {
    bg: () => ({ glow: '#2c241b', glowA: 0.5 }),
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      // local camera: settle on the two decisive branches
      const fz = p(t, c.gen, 3.5, E.inOut);
      ctx.save();
      ctx.translate(W.W / 2, W.H / 2);
      ctx.scale(1 + fz * 0.07, 1 + fz * 0.07);
      ctx.translate(-W.W / 2 + fz * 150, -W.H / 2 + fz * -100);

      const relevant = (id) => (id === 'jg' || id === 'el' ? 1 : 1 - p(t, c.disputes, 1.2) * 0.75);
      const yS = 490;
      const lanP = p(t, c.lan, 1.0), yorkP = p(t, c.york, 1.0);
      const nodes = {
        e3: { x: 960, y: 250, label: null, portrait: 'p_edward3', pr: 48, t: c.e3, r: 18, color: W.C.gold, alpha: 1 - p(t, c.disputes, 1.2) * 0.5, labelGap: 30 },
        bp: { x: X.bp, y: yS, label: T.bp, sub: T.bpSub, t: c.sons, dead: t > c.bpDead + 0.3, alpha: (t > c.bpDead ? 0.55 : 1) * relevant('bp'), color: W.C.ivoryDim },
        li: { x: X.li, y: yS, label: T.li, sub: T.liSub, t: c.sons + 0.15, dead: true, alpha: 0.45 * relevant('li'), color: W.C.ivoryDim },
        jg: { x: X.jg, y: yS, label: T.jg, sub: T.jgSub, t: c.sons + 0.3, color: W.mixColor(W.C.ivory, W.C.crimsonBright, lanP), halo: t > c.three ? (lanP > 0 ? W.C.crimson : W.C.ivory) : null },
        el: { x: X.el, y: yS, label: T.el, sub: T.elSub, t: c.sons + 0.45, color: W.C.ivory, halo: t > c.three ? W.C.ivory : null },
        tw: { x: X.tw, y: yS, label: T.tw, sub: T.twSub, t: c.sons + 0.6, alpha: relevant('tw'), halo: t > c.three && t < c.disputes ? W.C.ivory : null },
        r2: { x: X.bp, y: 770, label: T.r2, sub: T.r2Sub, t: c.grandson, r: 13, color: W.C.ivory, alpha: relevant('r2') },
        lan: { x: X.jg, y: 830, t: c.branches, r: 0.01, alpha: 0 },
        york: { x: X.el, y: 830, t: c.branches + 0.3, r: 0.01, alpha: 0 },
      };
      const edges = [
        ...['bp', 'li', 'jg', 'el', 'tw'].map((k, i) => ({ a: 'e3', b: k, t: c.sons + i * 0.15, mid: 0.45, alpha: k === 'li' ? 0.45 * relevant(k) : k === 'jg' || k === 'el' ? 1 : relevant(k) * (k === 'bp' && t > c.bpDead ? 0.6 : 1) })),
        { a: 'bp', b: 'r2', t: c.grandson - 0.3, alpha: relevant('r2') },
      ];
      W.tree(ctx, t, nodes, edges);
      W.text(ctx, T.e3, W.hasPortrait('p_edward3') ? 1030 : 990, 250, { size: 36, color: W.C.ivory, align: 'left', alpha: p(t, c.e3 + 0.2, 0.7) * nodes.e3.alpha });

      // the crown passes from Edward III to his grandson, skipping a generation
      const cp = p(t, c.crown, 1.4, E.inOut);
      const contest = p(t, c.disputes, 1.6, E.inOut);
      let crx = W.lerp(960, X.bp, cp), cry = W.lerp(180, 712, cp) - Math.sin(cp * Math.PI) * 120;
      crx = W.lerp(crx, 810, contest) + Math.sin((t - c.disputes) * 2.4) * 70 * contest;
      cry = W.lerp(cry, 715, contest);
      W.crown(ctx, crx, cry, 34, { p: p(t, c.e3, 1.0), color: W.C.gold, width: 2.2, fill: 0.25, glow: 'rgba(201,164,92,0.4)' });

      // "bypassing three living sons"
      const bk = p(t, c.three, 0.9, E.inOut);
      if (bk > 0) {
        const a = 1 - p(t, c.disputes, 0.8);
        W.alpha(ctx, a, () => {
          ctx.strokeStyle = W.rgba(W.C.gold, 0.7); ctx.lineWidth = 1.5;
          const y = 625, x0 = X.tw - 60, x1 = X.jg + 60, mid = (x0 + x1) / 2, h = (x1 - x0) / 2 * bk;
          ctx.beginPath(); ctx.moveTo(mid - h, y - 12); ctx.lineTo(mid - h, y); ctx.lineTo(mid + h, y); ctx.lineTo(mid + h, y - 12); ctx.stroke();
          W.text(ctx, T.living, mid, y + 40, { size: 32, fam: W.F.label, weight: 500, color: W.C.gold, reveal: p(t, c.three + 0.2, 0.8) });
        });
      }
      // generation-skip arrow over the sons' row
      const by = p(t, c.bypass, 1.0, E.inOut);
      W.alpha(ctx, 1 - p(t, c.three + 1, 0.8), () => W.route(ctx, W.arcPts([1000, 220], [X.bp - 40, 705], -0.25, 40), t, by, { color: W.C.gold, width: 2 }));

      // the two houses descend from the 3rd and 4th sons
      for (const [k, x, col, txt, kind, cue] of [['lan', X.jg, W.C.crimsonBright, T.lan, 'lancaster', c.lan], ['york', X.el, W.C.ivory, T.york, 'york', c.york]]) {
        const dp = p(t, c.branches + (k === 'york' ? 0.3 : 0), 1.0, E.inOut);
        W.strokePoly(ctx, [[x, 595], [x, 800]], dp, { color: W.rgba(k === 'lan' ? W.C.crimsonBright : W.C.ivory, 0.6), width: 2.5 });
        W.rose(ctx, x, 835, 36, { kind, bloom: p(t, cue - 0.2, 1.2) });
        W.text(ctx, txt, x, 910, { size: 46, color: col, reveal: p(t, cue, 0.9), rise: 10 });
      }
      // dispute sparks between the two branches
      if (t > c.disputes) {
        const sa = p(t, c.disputes, 0.6) * (1 - p(t, c.lan - 0.6, 0.6)) * 0.8;
        for (let i = 0; i < 3; i++) {
          const ph = (t * 1.3 + i * 0.33) % 1;
          W.alpha(ctx, sa * (1 - ph), () => {
            ctx.strokeStyle = W.C.crimsonBright; ctx.lineWidth = 1.5;
            ctx.beginPath(); ctx.arc(810, 715, 40 + ph * 90, 0, Math.PI * 2); ctx.stroke();
          });
        }
      }
      ctx.restore();
    },
  });

  // ---------------------------------------------------------------- roses
  W.scene('roses', {
    bg: () => ({ glow: '#2e2219', glowA: 0.55 }),
    dust: 34,
    draw(ctx, t, S) {
      const c = S.cues, T = S.text;
      W.text(ctx, 'رمزا العائلتين', W.W / 2, 175, { size: 32, fam: W.F.label, weight: 500, color: W.C.gold, reveal: p(t, c.name + 0.2, 0.9) });
      W.strokePoly(ctx, [[W.W / 2, 260], [W.W / 2, 860]], p(t, c.name, 1.6, E.inOut), { color: W.rgba(W.C.ivory, 0.3), width: 1.2 });
      for (const [x, kind, cue, title, sub, col] of [[560, 'york', c.white, T.w, T.wSub, W.C.ivory], [1360, 'lancaster', c.red, T.r, T.rSub, W.C.crimsonBright]]) {
        // ring placeholder, then bloom
        const ring = p(t, c.name + (kind === 'york' ? 0.5 : 0.8), 1.2, E.inOut);
        ctx.save();
        ctx.strokeStyle = W.rgba(W.C.ivory, 0.25);
        ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.arc(x, 470, 230, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * ring); ctx.stroke();
        ctx.restore();
        const b = p(t, cue - 0.25, 2.0, E.out);
        W.rose(ctx, x, 470, 175, { kind, bloom: b, spin: (t - cue) * 0.02 });
        W.text(ctx, title, x, 790, { size: 64, color: col, reveal: p(t, cue + 0.1, 0.9), rise: 12 });
        W.text(ctx, sub, x, 860, { size: 32, fam: W.F.label, weight: 400, color: W.C.ivoryDim, reveal: p(t, cue + 0.5, 0.8) });
      }
    },
  });

  // ---------------------------------------------------------------- henry4 & henry6_infant (shared timeline)
  const TL = (t, events, t0) => W.timeline(ctx_, t, { x0: 260, x1: 1660, y: 870, from: 1370, to: 1430, t0, dur: 1.8, ticks: 5, events });
  let ctx_ = null;
  const tlEvents = (T1, T2) => [
    { year: 1377, t: 67.6, label: T1, color: W.C.ivory, size: 26 },
    { year: 1399, t: 72.94, label: T2, color: W.C.crimsonBright, size: 26 },
  ];

  W.scene('henry4', {
    bg: () => ({ glow: '#2e1d18', glowA: 0.55 }),
    draw(ctx, t, S) {
      ctx_ = ctx;
      const c = S.cues, T = S.text;
      W.text(ctx, 'آل لانكاستر يستولون على العرش', W.W / 2, 175, { size: 34, fam: W.F.label, weight: 500, color: W.C.gold, reveal: p(t, c.seize, 1.0) });
      const dep = p(t, c.r2 + 0.3, 1.4, E.inOut);
      const nodes = {
        r2: { x: 1300, y: 430, label: T.r2, sub: dep > 0.5 ? T.deposed : null, subColor: W.C.crimsonBright, t: 66.5, r: 18, color: W.mixColor(W.C.ivory, W.C.mute, dep), alpha: 1 - dep * 0.35 },
        h4: { x: 620, y: 430, label: T.h4, sub: T.h4Sub, subColor: W.C.crimsonBright, t: c.h4, r: 18, color: W.C.crimsonBright, halo: dep > 0.6 ? W.C.crimson : null },
      };
      W.tree(ctx, t, nodes, [{ a: 'r2', b: 'h4', t: c.r2, style: 'marriage', color: W.rgba(W.C.ivory, 0.4) }]);
      W.text(ctx, 'ابنا عمّ', 960, 405, { size: 24, fam: W.F.label, weight: 400, color: W.C.ivoryDim, alpha: p(t, c.r2 + 0.4, 0.6) });
      // crown transfer
      const x = W.lerp(1300, 620, dep), y = 345 - Math.sin(dep * Math.PI) * 110;
      W.crown(ctx, x, y, 40, { p: p(t, 66.6, 1.2), color: W.mixColor(W.C.gold, W.C.crimsonBright, dep), width: 2.4, fill: 0.25, glow: 'rgba(201,164,92,0.35)' });
      TL(t, tlEvents(T.ev1, T.ev2), 66.9);
    },
  });

  W.scene('henry6_infant', {
    bg: () => ({ glow: '#2a1a16', glowA: 0.55 }),
    draw(ctx, t, S) {
      ctx_ = ctx;
      const c = S.cues, T = S.text;
      const prev = W.DATA.scenes.find((s) => s.id === 'henry4').text;
      TL(t, [...tlEvents(prev.ev1, prev.ev2), { year: 1422, t: c.year, label: T.ev, color: W.C.crimsonBright, size: 26 }], 0);
      // three Lancastrian kings
      const kings = [
        { x: 1400, name: 'هنري الرابع', yrs: '1399 — 1413', t: c.unrest },
        { x: 960, name: T.h5, yrs: '1413 — 1422', t: c.stable },
      ];
      kings.forEach((k, i) => {
        const shake = i === 0 ? Math.sin(t * 14) * 4 * (p(t, c.unrest, 0.3) - p(t, c.stable, 0.6)) : 0;
        const dead = i === 1 ? p(t, c.h5, 1.0) : 0;
        W.crown(ctx, k.x + shake, 330, 46, { p: p(t, k.t, 1.1, E.inOut), color: W.mixColor(W.C.crimsonBright, W.C.mute, dead * 0.7), width: 2.3, fill: 0.2 });
        W.text(ctx, k.name, k.x, 430, { size: 40, color: W.C.ivory, reveal: p(t, k.t + 0.2, 0.8), alpha: 1 - dead * 0.35 });
        W.text(ctx, k.yrs, k.x, 480, { size: 22, fam: W.F.latin, weight: 400, color: W.C.ivoryDim, dir: 'ltr', alpha: p(t, k.t + 0.5, 0.8) });
      });
      // Henry V falls on campaign: broken sword
      const sw = p(t, c.h5, 1.2, E.inOut);
      if (sw > 0) {
        W.alpha(ctx, sw, () => {
          W.sword(ctx, 960 + 140, 355 - sw * 8, 46, { color: W.C.ivoryDim, width: 2, rot: 0.5 + sw * 0.25 });
          ctx.save(); ctx.translate(960 + 152, 330); ctx.rotate(-0.4 - sw * 0.6);
          ctx.strokeStyle = W.C.bg; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-14, 0); ctx.lineTo(14, 4); ctx.stroke(); ctx.restore();
        });
        W.text(ctx, 'في حملة عسكرية بفرنسا', 960, 530, { size: 24, fam: W.F.label, weight: 400, color: W.C.crimsonBright, alpha: p(t, c.campaign, 0.8) });
      }
      // the infant king: a tiny node under a crown far too large
      const ip = p(t, c.infant, 1.0, E.out);
      W.node(ctx, 520, 470, 7, { p: ip, color: W.C.crimsonBright });
      W.crown(ctx, 520, 330 - (1 - ip) * 40, 74, { p: p(t, c.infant + 0.2, 1.4, E.inOut), color: W.C.gold, width: 2.4, fill: 0.2, glow: 'rgba(201,164,92,0.4)' });
      W.text(ctx, T.h6, 520, 525, { size: 44, color: W.C.ivory, reveal: p(t, c.h6, 0.8) });
      W.text(ctx, T.h6Sub, 520, 575, { size: 24, fam: W.F.label, weight: 400, color: W.C.gold, alpha: p(t, c.h6 + 0.5, 0.8) });
      W.text(ctx, 'استقرار حكم لانكاستر', W.W / 2, 175, { size: 34, fam: W.F.label, weight: 500, color: W.C.gold, reveal: p(t, c.stable, 1.0), alpha: 1 - p(t, c.h5 - 0.5, 0.6) });
    },
  });
})();
