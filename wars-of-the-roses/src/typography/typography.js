/* Kinetic Arabic typography.
   Arabic must never be letter-spaced or split inside a word (it breaks the joining), so all
   reveals work on whole words or with soft masks over complete shaped strings. */
(function () {
  const { W } = window;

  const setFont = (ctx, o) => {
    ctx.font = W.font(o.size || 64, o.fam || W.F.title, o.weight || 700);
    ctx.direction = o.dir || 'rtl';
    ctx.textBaseline = o.baseline || 'middle';
    if ('letterSpacing' in ctx) ctx.letterSpacing = o.tracking ? `${o.tracking}px` : '0px';
  };
  W.measure = (ctx, str, o = {}) => {
    ctx.save();
    setFont(ctx, o);
    const w = ctx.measureText(str).width;
    ctx.restore();
    return w;
  };

  /**
   * Draw a single string.
   * o: size fam weight color align('center'|'left'|'right') dir alpha
   *    reveal (0..1 feathered wipe in reading direction) rise (px slide while revealing)
   *    blur (px) shadow glow tracking (latin only)
   */
  // keep numeric ranges ("1455 — 1487") left-to-right inside Arabic lines
  const isolate = (s) => (/[\u0600-\u06FF]/.test(s) ? s.replace(/(\d+(?:\s*[—–-]\s*\d+)+)/g, '\u2066$1\u2069') : s);
  W.text = (ctx, str, x, y, o = {}) => {
    const a = o.alpha == null ? 1 : o.alpha;
    if (a <= 0.001 || !str) return;
    str = isolate(String(str));
    const reveal = o.reveal == null ? 1 : W.clamp(o.reveal);
    if (reveal <= 0) return;
    const dir = o.dir || (/[؀-ۿ]/.test(str) ? 'rtl' : 'ltr');
    const oo = { ...o, dir };
    const size = o.size || 64;
    const w = W.measure(ctx, str, oo);
    const align = o.align || 'center';
    const left = align === 'center' ? x - w / 2 : align === 'left' ? x : x - w;
    const rise = (o.rise || 0) * (1 - reveal);

    if (reveal >= 1 && !o.blur) {
      ctx.save();
      ctx.globalAlpha *= a;
      setFont(ctx, oo);
      ctx.textAlign = 'left';
      ctx.fillStyle = o.color || W.C.ivory;
      if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.glowBlur || 24; }
      if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.strokeWidth || 2; ctx.strokeText(str, left, y + rise); }
      if (!o.outlineOnly) ctx.fillText(str, left, y + rise);
      ctx.restore();
      return w;
    }
    // feathered reveal through an offscreen mask
    const pad = Math.ceil(size * 0.9);
    const lw = Math.ceil(w + pad * 2), lh = Math.ceil(size * 2.4);
    const [c, x2] = W.layer('text', lw, lh);
    setFont(x2, oo);
    x2.textAlign = 'left';
    x2.fillStyle = o.color || W.C.ivory;
    if (o.glow) { x2.shadowColor = o.glow; x2.shadowBlur = o.glowBlur || 24; }
    if (o.stroke) { x2.strokeStyle = o.stroke; x2.lineWidth = o.strokeWidth || 2; x2.strokeText(str, pad, lh / 2); }
    if (!o.outlineOnly) x2.fillText(str, pad, lh / 2);
    x2.shadowBlur = 0;
    if (reveal < 1) {
      const feather = Math.max(40, w * 0.25);
      const span = w + feather;
      x2.globalCompositeOperation = 'destination-in';
      let g;
      if (dir === 'rtl') {
        const front = pad + w - span * reveal + feather; // moving right -> left
        g = x2.createLinearGradient(front - feather, 0, front, 0);
        g.addColorStop(0, 'rgba(0,0,0,0)');
        g.addColorStop(1, 'rgba(0,0,0,1)');
      } else {
        const front = pad + span * reveal - feather;
        g = x2.createLinearGradient(front, 0, front + feather, 0);
        g.addColorStop(0, 'rgba(0,0,0,1)');
        g.addColorStop(1, 'rgba(0,0,0,0)');
      }
      x2.fillStyle = g;
      x2.fillRect(0, 0, lw, lh);
    }
    ctx.save();
    ctx.globalAlpha *= a;
    if (o.blur) ctx.filter = `blur(${o.blur}px)`;
    ctx.drawImage(c, left - pad, y + rise - lh / 2);
    ctx.restore();
    return w;
  };

  /**
   * Word-by-word kinetic line, laid out right-to-left manually.
   * times: array of start times per word (or a single start + o.step).
   */
  W.words = (ctx, str, x, y, t, times, o = {}) => {
    const words = str.split(' ');
    const sp = W.measure(ctx, ' ', o) * 1.05;
    const ws = words.map((s) => W.measure(ctx, s, o));
    const total = ws.reduce((a, b) => a + b, 0) + sp * (words.length - 1);
    const align = o.align || 'center';
    let cursor = align === 'center' ? x + total / 2 : align === 'right' ? x : x + total;
    const dur = o.dur || 0.55;
    words.forEach((s, i) => {
      const t0 = Array.isArray(times) ? times[Math.min(i, times.length - 1)] : times + i * (o.step || 0.12);
      const p = W.p(t, t0, dur, W.E.out);
      const col = o.colors && o.colors[i] ? o.colors[i] : o.color;
      W.text(ctx, s, cursor, y + (1 - p) * (o.rise == null ? 18 : o.rise), {
        ...o, color: col, align: 'right', alpha: p * (o.alpha == null ? 1 : o.alpha), blur: p < 1 ? (1 - p) * 6 : 0,
      });
      cursor -= ws[i] + sp;
    });
    return total;
  };

  /** Large Latin numerals that roll into place digit by digit */
  W.year = (ctx, str, x, y, t, t0, o = {}) => {
    const size = o.size || 180;
    const fam = o.fam || W.F.latin;
    const digits = String(str).split('');
    const dw = digits.map((d) => W.measure(ctx, d, { size, fam, weight: o.weight || 600, dir: 'ltr', tracking: o.tracking || 6 }));
    const total = dw.reduce((a, b) => a + b, 0);
    let cx = x - total / 2;
    ctx.save();
    digits.forEach((d, i) => {
      const p = W.p(t, t0 + i * (o.step || 0.09), o.dur || 0.9, W.E.outExpo);
      if (p > 0) {
        const off = (1 - p) * size * 0.6;
        ctx.save();
        ctx.beginPath();
        ctx.rect(cx - 10, y - size * 0.62, dw[i] + 20, size * 1.24);
        ctx.clip();
        W.text(ctx, d, cx, y + off, { size, fam, weight: o.weight || 600, color: o.color || W.C.ivory, align: 'left', dir: 'ltr', alpha: (o.alpha == null ? 1 : o.alpha) * Math.min(1, p * 1.5), tracking: o.tracking || 6, glow: o.glow });
        ctx.restore();
      }
      cx += dw[i];
    });
    ctx.restore();
    return total;
  };

  /** Editorial caption block: small kufi kicker + headline + hairline */
  W.caption = (ctx, x, y, t, t0, o) => {
    const p1 = W.p(t, t0, 0.7), p2 = W.p(t, t0 + 0.15, 0.9), p3 = W.p(t, t0 + 0.05, 1.1, W.E.inOut);
    const a = o.alpha == null ? 1 : o.alpha;
    const align = o.align || 'right';
    if (o.kicker) W.text(ctx, o.kicker, x, y - (o.size || 56) * 0.95, { size: o.kickerSize || 26, fam: W.F.label, weight: 500, color: o.kickerColor || W.C.gold, align, alpha: a * p1, reveal: p1 });
    W.text(ctx, o.title, x, y, { size: o.size || 56, color: o.color || W.C.ivory, align, alpha: a * p2, reveal: p2, rise: 10 });
    if (o.line !== false) {
      const lw = o.lineW || 220;
      ctx.save();
      ctx.globalAlpha *= a;
      ctx.strokeStyle = o.lineColor || W.C.goldDim;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      const ly = y + (o.size || 56) * 0.78;
      if (align === 'right') { ctx.moveTo(x, ly); ctx.lineTo(x - lw * p3, ly); }
      else if (align === 'left') { ctx.moveTo(x, ly); ctx.lineTo(x + lw * p3, ly); }
      else { ctx.moveTo(x - (lw / 2) * p3, ly); ctx.lineTo(x + (lw / 2) * p3, ly); }
      ctx.stroke();
      ctx.restore();
    }
    if (o.sub) W.text(ctx, o.sub, x, y + (o.size || 56) * 1.35, { size: o.subSize || 28, fam: W.F.label, weight: 400, color: o.subColor || W.C.ivoryDim, align, alpha: a * W.p(t, t0 + 0.35, 0.8), reveal: W.p(t, t0 + 0.35, 1) });
  };

  /** strike-through line drawn across a text width */
  W.strike = (ctx, x, y, w, p, color = W.C.crimsonBright, width = 4) => {
    if (p <= 0) return;
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(x + w / 2, y);
    ctx.lineTo(x + w / 2 - w * p, y);
    ctx.stroke();
    ctx.restore();
  };
})();
