// End-to-end test: loads the built extension in Chromium, serves synthetic Etsy
// fixtures for www.etsy.com URLs (no real Etsy traffic), and drives every view.
// Usage: node tests/e2e/run.mjs [chrome|opera]   (after `npm run build`)
import { createRequire } from 'node:module';
// Uses the project's playwright if installed, otherwise a globally installed one.
const { chromium } = createRequire(import.meta.url)('playwright');
import { mkdirSync, readFileSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const target = process.argv[2] ?? 'chrome';
const ext = resolve('dist', target);
const shots = resolve('test-results', target);
mkdirSync(shots, { recursive: true });
const profile = join(tmpdir(), `shoplens-e2e-${Date.now()}`);
const fixture = (n) => readFileSync(resolve('tests/fixtures', n), 'utf8');

const errors = [];
const failures = [];
let passed = 0;
const check = (cond, msg) => { if (cond) passed++; else { failures.push(msg); console.log(`  ✗ ${msg}`); } };

const ctx = await chromium.launchPersistentContext(profile, {
  headless: true,
  channel: 'chromium', // full Chromium in new headless mode: the headless shell cannot load extensions
  args: [`--disable-extensions-except=${ext}`, `--load-extension=${ext}`],
  viewport: { width: 1280, height: 900 },
});

// Serve fixtures instead of Etsy; block everything else on etsy.com.
await ctx.route(/https:\/\/(www\.)?etsy\.com\/.*/, (route) => {
  const u = new URL(route.request().url());
  let body = '<!doctype html><title>not found</title>';
  if (u.pathname.startsWith('/search')) body = fixture('search.html');
  else if (u.pathname.startsWith('/listing/1001')) body = fixture('listing.html');
  else if (u.pathname.startsWith('/shop/MugMakerCo')) body = fixture('shop.html');
  route.fulfill({ status: 200, contentType: 'text/html', body });
});
await ctx.route(/https:\/\/i\.etsystatic\.com\/.*/, (r) => r.fulfill({ status: 204 }));

const watch = (page, label) => {
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`${label}: ${m.text()}`); });
  page.on('pageerror', (e) => errors.push(`${label}: ${e.message}`));
};

let [sw] = ctx.serviceWorkers();
if (!sw) sw = await ctx.waitForEvent('serviceworker');
const id = new URL(sw.url()).host;
console.log(`extension ${target} loaded: ${id}`);

// onInstalled opens the welcome page
await new Promise((r) => setTimeout(r, 800));
const dash = ctx.pages().find((p) => p.url().includes('dashboard.html')) ?? await ctx.newPage();
watch(dash, 'dashboard');
await dash.goto(`chrome-extension://${id}/dashboard.html#welcome`);
await dash.waitForSelector('text=Turn on page reading');
await dash.screenshot({ path: join(shots, 'welcome.png') });
await dash.check('#pr');
await dash.click('button:has-text("Continue")');
await dash.waitForSelector('h1:has-text("Overview")');
check(true, 'onboarding');

// Browse "Etsy"
const etsy = await ctx.newPage();
watch(etsy, 'etsy');
const visit = async (url, name) => {
  await etsy.goto(url);
  await etsy.waitForSelector('#shoplens-research-root', { state: 'attached', timeout: 5000 });
  await etsy.waitForTimeout(600);
  await etsy.mouse.click(1280 - 36, 900 - 36); // launcher (closed shadow root)
  await etsy.waitForTimeout(300);
  await etsy.screenshot({ path: join(shots, `etsy-${name}.png`) });
  await etsy.keyboard.press('Escape');
};
await visit('https://www.etsy.com/search?q=personalized+mug', 'search');
await visit('https://www.etsy.com/listing/1001/custom-name-mug', 'listing');
await visit('https://www.etsy.com/shop/MugMakerCo', 'shop');
// Etsy page must keep its own layout: the host is fixed and out of flow
const hostBox = await etsy.evaluate(() => { const r = document.getElementById('shoplens-research-root').getBoundingClientRect(); return { w: r.width, h: r.height, pos: getComputedStyle(document.getElementById('shoplens-research-root')).position }; });
check(hostBox.pos === 'fixed', 'in-page host is position:fixed');
// Return to search: badge chip appears on the analysed listing
await etsy.goto('https://www.etsy.com/search?q=personalized+mug');
await etsy.waitForSelector('[data-shoplens-badge="1001"]', { timeout: 5000 }).then(() => check(true, 'badge'), () => check(false, 'estimate chip shown on analysed search card'));

// Dashboard views
const views = [
  ['overview', 'Overview'], ['products', 'Products'], ['products/1001', 'Custom Name Mug'], ['keywords', 'Keywords'],
  ['keywords/personalized%20mug', 'personalized mug'], ['competitors', 'Competitors'], ['competitors/MugMakerCo', 'MugMakerCo'],
  ['seo/audit/1001', 'SEO tools'], ['seo/title', 'SEO tools'], ['seo/tags', 'SEO tools'], ['seo/description', 'SEO tools'], ['seo/compare', 'SEO tools'],
  ['trends', 'Trends'], ['saved', 'Saved'], ['history', 'History'], ['settings', 'Settings'], ['diagnostics', 'Page diagnostics'],
];
for (const [route, heading] of views) {
  await dash.goto(`chrome-extension://${id}/dashboard.html#${route}`);
  await dash.waitForTimeout(250);
  const ok = await dash.locator('h1', { hasText: heading }).count();
  check(ok > 0, `view ${route} renders "${heading}"`);
  const bad = await dash.locator('.notice.warn:has-text("could not be displayed")').count();
  check(bad === 0, `view ${route} has no render error`);
  await dash.screenshot({ path: join(shots, `dash-${route.replace(/[/%]/g, '_')}.png`), fullPage: true });
}

// Data checks
await dash.goto(`chrome-extension://${id}/dashboard.html#products/1001`);
await dash.waitForSelector('text=Sales & revenue estimate');
const detail = await dash.textContent('main');
check(detail.includes('12,345'), 'product detail shows verified shop sales');
check(detail.includes('Estimated'), 'product detail labels estimates');
check(detail.includes('Not available'), 'product detail marks unavailable metrics');
await dash.goto(`chrome-extension://${id}/dashboard.html#keywords/personalized%20mug`);
await dash.waitForSelector('text=Related phrases');
check((await dash.textContent('main')).includes('1,234'), 'keyword shows verified result count');
await dash.goto(`chrome-extension://${id}/dashboard.html#diagnostics`);
await dash.waitForSelector('table.data');
check((await dash.locator('.badge.verified:has-text("yes")').count()) >= 5, 'diagnostics lists found fields');

// Exports
await dash.goto(`chrome-extension://${id}/dashboard.html#products`);
await dash.waitForSelector('table.data');
const [csv] = await Promise.all([dash.waitForEvent('download'), dash.click('button:has-text("Export CSV")')]);
const csvText = readFileSync(await csv.path(), 'utf8');
check(csvText.includes('Custom Name Mug') && csvText.split('\n').length >= 5, 'CSV export contains products');
const [xlsx] = await Promise.all([dash.waitForEvent('download'), dash.click('button:has-text("Export Excel")')]);
check(readFileSync(await xlsx.path()).subarray(0, 2).toString() === 'PK', 'Excel export is a zip package');

// Filtering & sorting
await dash.fill('input[placeholder="title, search or term"]', 'template');
await dash.waitForTimeout(100);
check((await dash.locator('table.data tbody tr').count()) === 1, 'keyword filter narrows the product table');
await dash.click('button:has-text("Reset")');
await dash.waitForTimeout(200);
await dash.click('th button:has-text("Price")');
const firstPrice = await dash.locator('table.data tbody tr').first().locator('td').nth(1).textContent();
check(/4\.99|22/.test(firstPrice ?? ''), `sorting by price works (first row ${firstPrice})`);

// Backup round trip
await dash.goto(`chrome-extension://${id}/dashboard.html#settings`);
const [bk] = await Promise.all([dash.waitForEvent('download'), dash.click('button:has-text("Download backup")')]);
const backup = JSON.parse(readFileSync(await bk.path(), 'utf8'));
check(backup.format === 'shoplens-backup' && backup.data.listings.length >= 4, 'backup contains data');

// Popup & sidebar pages
const pop = await ctx.newPage();
watch(pop, 'popup');
await pop.setViewportSize({ width: 380, height: 600 });
await pop.goto(`chrome-extension://${id}/popup.html`);
await pop.waitForTimeout(300);
check((await pop.textContent('body')).includes('Reading the Etsy pages you open'), 'popup shows status');
await pop.screenshot({ path: join(shots, 'popup.png') });
await pop.goto(`chrome-extension://${id}/sidebar.html`);
await pop.waitForTimeout(300);
await pop.screenshot({ path: join(shots, 'sidebar.png') });

// Small screens: no horizontal overflow
for (const w of [375, 768]) {
  await dash.setViewportSize({ width: w, height: 800 });
  for (const route of ['overview', 'products', 'products/1001', 'keywords/personalized%20mug', 'competitors/MugMakerCo', 'seo/tags', 'trends', 'settings']) {
    await dash.goto(`chrome-extension://${id}/dashboard.html#${route}`);
    await dash.waitForTimeout(200);
    const over = await dash.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check(over <= 1, `no horizontal overflow at ${w}px on ${route} (${over}px)`);
    if (w === 375) await dash.screenshot({ path: join(shots, `mobile-${route.replace(/[/%]/g, '_')}.png`), fullPage: true });
  }
}
await dash.setViewportSize({ width: 1280, height: 900 });
await dash.emulateMedia({ colorScheme: 'dark' });
await dash.goto(`chrome-extension://${id}/dashboard.html#products/1001`);
await dash.waitForTimeout(300);
await dash.screenshot({ path: join(shots, 'dark-product.png'), fullPage: true });

// Turning page reading off removes the panel
await dash.goto(`chrome-extension://${id}/dashboard.html#settings`);
await dash.locator('text=Read Etsy pages I open').click();
await etsy.waitForTimeout(500);
check((await etsy.locator('#shoplens-research-root').count()) === 0, 'panel removed when page reading is turned off');

check(errors.length === 0, `no console errors (${errors.join(' | ')})`);
await ctx.close();
rmSync(profile, { recursive: true, force: true });
console.log(`${passed} checks passed, ${failures.length} failed`);
if (failures.length) process.exit(1);
