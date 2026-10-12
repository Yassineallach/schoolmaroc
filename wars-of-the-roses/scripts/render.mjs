#!/usr/bin/env node
/* Deterministic frame renderer: headless Chromium draws each frame via window.renderFrame(t),
   frames are streamed as JPEG into FFmpeg, then audio is mixed and the final MP4 encoded.

   node scripts/render.mjs                          full documentary  -> output/final_video.mp4
   node scripts/render.mjs --preview                preview reel      -> output/preview.mp4
   node scripts/render.mjs --ranges 30-40 --out output/test.mp4
   node scripts/render.mjs --stills 3.5,24.6,60     PNG stills        -> output/stills/
   node scripts/render.mjs --thumbnail              YouTube thumbnail -> output/thumbnail.png
   options: --workers N (default 4)  --no-music  --no-grain
*/
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'output');
const BUILD = path.join(OUT, 'build');
fs.mkdirSync(BUILD, { recursive: true });

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const flag = (k) => args.includes(`--${k}`);
const DATA = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/scenes.json'), 'utf8'));
const FPS = DATA.meta.fps, DUR = DATA.meta.duration;
const WORKERS = parseInt(opt('workers', '4'), 10);

// the preview reel uses two real stretches of the narration
const PREVIEW = [[0, 36.2], [111.9, 133.6]];

// ---- static server --------------------------------------------------------------
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.woff2': 'font/woff2', '.wav': 'audio/wav' };
function serve() {
  return new Promise((res) => {
    const srv = http.createServer((req, resp) => {
      const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
      if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { resp.writeHead(404); return resp.end(); }
      resp.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
      fs.createReadStream(p).pipe(resp);
    });
    srv.listen(0, '127.0.0.1', () => res(srv));
  });
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', (m) => { if (m.type() === 'warning' || m.type() === 'error') console.log('[page]', m.text(), m.location().url || ''); });
  page.on('pageerror', (e) => console.log('[page error]', e.message));
  await page.goto(`http://127.0.0.1:${port}/src/index.html`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  const cdp = await page.context().newCDPSession(page);
  return { page, cdp };
}

async function grab({ page, cdp }, t, format = 'jpeg') {
  await page.evaluate((tt) => window.renderFrame(tt), t);
  const r = await cdp.send('Page.captureScreenshot', format === 'png' ? { format: 'png' } : { format: 'jpeg', quality: 94, optimizeForSpeed: true });
  return Buffer.from(r.data, 'base64');
}

function ffmpeg(argv) {
  const p = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...argv], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => p.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));
  return { p, done };
}

/** render frames [f0, f1) of one range into a lossless-ish segment */
async function renderSegment(browser, port, a, f0, f1, file, progress) {
  const ctx = await openPage(browser, port);
  const enc = ffmpeg(['-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '10', '-pix_fmt', 'yuv420p', file]);
  for (let f = f0; f < f1; f++) {
    const buf = await grab(ctx, a + f / FPS);
    if (!enc.p.stdin.write(buf)) await new Promise((r) => enc.p.stdin.once('drain', r));
    progress();
  }
  enc.p.stdin.end();
  await enc.done;
  await ctx.page.close();
}

async function renderRanges(ranges, name) {
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb', '--font-render-hinting=none'] });
  const jobs = [];
  ranges.forEach(([a, b], ri) => {
    const n = Math.round((b - a) * FPS);
    const per = Math.ceil(n / WORKERS);
    for (let w = 0; w < WORKERS; w++) {
      const f0 = w * per, f1 = Math.min(n, (w + 1) * per);
      if (f1 > f0) jobs.push({ a, f0, f1, file: path.join(BUILD, `${name}_r${ri}_w${w}.mp4`) });
    }
  });
  const total = jobs.reduce((s, j) => s + j.f1 - j.f0, 0);
  let done = 0, last = 0;
  const t0 = Date.now();
  const progress = () => {
    done++;
    if (Date.now() - last > 5000) {
      last = Date.now();
      const el = (Date.now() - t0) / 1000;
      console.log(`  ${done}/${total} frames  ${(done / el).toFixed(1)} fps  eta ${((total - done) / (done / el)).toFixed(0)}s`);
    }
  };
  // run WORKERS jobs at a time
  const queue = jobs.slice();
  await Promise.all(Array.from({ length: WORKERS }, async () => {
    while (queue.length) { const j = queue.shift(); await renderSegment(browser, port, j.a, j.f0, j.f1, j.file, progress); }
  }));
  await browser.close();
  srv.close();
  console.log(`  rendered ${total} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  return jobs.map((j) => j.file);
}

function concat(files, out) {
  const list = path.join(BUILD, path.basename(out) + '.txt');
  fs.writeFileSync(list, files.map((f) => `file '${f}'`).join('\n'));
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' });
  if (r.status) throw new Error('concat failed');
}

/** narration (+ optional score) for the given ranges, concatenated */
function buildAudio(ranges, out, music) {
  const narr = path.join(ROOT, DATA.meta.audio);
  const score = path.join(BUILD, 'score.wav');
  if (music && !fs.existsSync(score)) {
    const r = spawnSync('python3', [path.join(ROOT, 'scripts/make_score.py'), score], { stdio: 'inherit' });
    if (r.status) throw new Error('score generation failed');
  }
  const parts = ranges.map(([a, b], i) => {
    const f = path.join(BUILD, `aud_${i}.wav`);
    const nd = Math.max(0, Math.min(b, DATA.meta.narration_duration) - a);
    const filt = [`[0:a]atrim=${a}:${a + nd},asetpts=PTS-STARTPTS,aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur=${b - a}[v]`];
    const inputs = ['-i', narr];
    if (music) {
      inputs.push('-i', score);
      filt.push(`[1:a]atrim=${a}:${b},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[m]`);
      filt.push('[v]asplit=2[v1][v2]', '[m][v2]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=600[md]');
      filt.push('[v1][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[o]');
    } else filt.push('[v]alimiter=limit=0.89:level=false[o]');
    const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...inputs, '-filter_complex', filt.join(';'), '-map', '[o]', '-t', String(b - a), '-c:a', 'pcm_s16le', f], { stdio: 'inherit' });
    if (r.status) throw new Error('audio build failed');
    return f;
  });
  const list = path.join(BUILD, 'aud.txt');
  fs.writeFileSync(list, parts.map((f) => `file '${f}'`).join('\n'));
  spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' });
}

async function stills(times) {
  const dir = path.join(OUT, 'stills');
  fs.mkdirSync(dir, { recursive: true });
  const srv = await serve();
  const browser = await chromium.launch();
  const ctx = await openPage(browser, srv.address().port);
  for (const t of times) {
    const buf = await grab(ctx, t, 'png');
    const f = path.join(dir, `t${t.toFixed(2).padStart(7, '0')}.png`);
    fs.writeFileSync(f, buf);
    console.log(f);
  }
  await browser.close();
  srv.close();
}

async function thumbnail() {
  const srv = await serve();
  const browser = await chromium.launch();
  const ctx = await openPage(browser, srv.address().port);
  await ctx.page.evaluate(() => W.drawThumbnail(document.getElementById('c').getContext('2d')));
  const r = await ctx.cdp.send('Page.captureScreenshot', { format: 'png' });
  const big = path.join(BUILD, 'thumb_1080.png');
  fs.writeFileSync(big, Buffer.from(r.data, 'base64'));
  spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', big, '-vf', 'scale=1280:720', path.join(OUT, 'thumbnail.png')], { stdio: 'inherit' });
  await browser.close();
  srv.close();
  console.log('wrote', path.join(OUT, 'thumbnail.png'));
}

async function main() {
  if (flag('thumbnail')) return thumbnail();
  if (opt('stills')) return stills(opt('stills').split(',').map(Number));
  const preview = flag('preview');
  const ranges = opt('ranges') ? opt('ranges').split(',').map((r) => r.split('-').map(Number)) : preview ? PREVIEW : [[0, DUR]];
  const out = path.resolve(ROOT, opt('out', preview ? 'output/preview.mp4' : 'output/final_video.mp4'));
  const name = path.basename(out, '.mp4');
  console.log(`rendering ${name}: ${ranges.map((r) => r.join('–')).join(', ')}  (${WORKERS} workers)`);
  const segs = await renderRanges(ranges, name);
  const silent = path.join(BUILD, `${name}_video.mp4`);
  concat(segs, silent);
  const audio = path.join(BUILD, `${name}_audio.wav`);
  buildAudio(ranges, audio, !flag('no-music'));
  const vf = flag('no-grain') ? 'null' : 'noise=alls=3:allf=t,format=yuv420p';
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', silent, '-i', audio, '-vf', vf,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '14M', '-bufsize', '28M', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', out], { stdio: 'inherit' });
  if (r.status) throw new Error('final encode failed');
  segs.forEach((f) => fs.rmSync(f, { force: true }));
  console.log('wrote', out);
}

main().catch((e) => { console.error(e); process.exit(1); });
