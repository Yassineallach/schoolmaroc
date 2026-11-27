// Builds the extension for Opera and Chrome into dist/<target>/ and zips each one.
import { build } from 'esbuild';
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';

const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
const watch = process.argv.includes('--dev');

function manifest(target) {
  const m = {
    manifest_version: 3,
    name: 'Shoplens Research',
    short_name: 'Shoplens',
    version: pkg.version,
    description: 'Research workspace for Etsy sellers: products, keywords, competitors, SEO and trends. Local-only, no AI.',
    icons: { 16: 'icons/icon-16.png', 32: 'icons/icon-32.png', 48: 'icons/icon-48.png', 128: 'icons/icon-128.png' },
    action: { default_popup: 'popup.html', default_title: 'Shoplens Research', default_icon: { 16: 'icons/icon-16.png', 32: 'icons/icon-32.png' } },
    background: { service_worker: 'background.js', type: 'module' },
    content_scripts: [{ matches: ['https://www.etsy.com/*', 'https://etsy.com/*'], js: ['content.js'], run_at: 'document_idle' }],
    permissions: ['storage', 'unlimitedStorage'],
    host_permissions: ['https://www.etsy.com/*', 'https://etsy.com/*'],
    options_ui: { page: 'dashboard.html', open_in_tab: true },
    minimum_chrome_version: '116',
  };
  if (target === 'opera') {
    m.sidebar_action = { default_panel: 'sidebar.html', default_title: 'Shoplens Research', default_icon: 'icons/icon-32.png' };
  } else {
    m.permissions.push('sidePanel');
    m.side_panel = { default_path: 'sidebar.html' };
  }
  return m;
}

const entries = {
  background: 'src/background/sw.ts',
  content: 'src/content/main.ts',
  dashboard: 'src/ui/dashboard/main.ts',
  popup: 'src/ui/popup/main.ts',
};

for (const target of ['opera', 'chrome']) {
  const out = join('dist', target);
  rmSync(out, { recursive: true, force: true });
  mkdirSync(join(out, 'styles'), { recursive: true });
  for (const [name, entry] of Object.entries(entries)) {
    await build({
      entryPoints: [entry],
      outfile: join(out, `${name}.js`),
      bundle: true,
      format: name === 'content' ? 'iife' : 'esm',
      target: ['chrome116'],
      loader: { '.css': 'text' },
      minify: !watch,
      sourcemap: watch ? 'inline' : false,
      legalComments: 'none',
      logLevel: 'warning',
    });
  }
  cpSync('static', out, { recursive: true });
  cpSync('src/ui/styles', join(out, 'styles'), { recursive: true });
  writeFileSync(join(out, 'manifest.json'), JSON.stringify(manifest(target), null, 2));
  const zipPath = join('dist', `shoplens-research-${target}-${pkg.version}.zip`);
  if (existsSync(zipPath)) rmSync(zipPath);
  try {
    execFileSync('zip', ['-qr', join('..', `shoplens-research-${target}-${pkg.version}.zip`), '.'], { cwd: out });
  } catch {
    console.warn('zip not available: skipped packaging');
  }
  console.log(`built ${out}`);
}
