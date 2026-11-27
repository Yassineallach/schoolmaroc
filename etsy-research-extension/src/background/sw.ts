/**
 * Background service worker. It stores what content scripts read from pages the
 * user opened. It makes no network requests of its own.
 */
import * as repo from '../core/storage/repo';
import { analyseKeyword, analyseListing, analyseShop, peerRatios, PanelSummary } from '../core/summaries';
import { estimateListingSales } from '../core/sales';
import { getSettings, saveSettings } from '../shared/settings';
import type { LookupEntry, Message, PageResponse, TabState } from '../shared/messages';
import type { PageResult } from '../shared/types';

const tabKey = (id: number) => `tab:${id}`;

async function summarise(result: PageResult): Promise<PanelSummary | undefined> {
  const x = result.extraction;
  if (!x) return undefined;
  const settings = await getSettings();
  if (x.type === 'search') {
    const term = repo.termKey(x.query);
    return { kind: 'search', term, analysis: term ? await analyseKeyword(term, settings) : undefined };
  }
  if (x.type === 'listing') return { kind: 'listing', id: x.listingId, analysis: await analyseListing(x.listingId, settings) };
  return { kind: 'shop', name: x.shopName, analysis: await analyseShop(x.shopName) };
}

async function handle(msg: Message, sender: chrome.runtime.MessageSender): Promise<unknown> {
  switch (msg.type) {
    case 'page': {
      const settings = await getSettings();
      if (!settings.pageReading) return { ok: false, error: 'Page reading is turned off in Settings.' } satisfies PageResponse;
      if (msg.result.extraction) await repo.ingest(msg.result.extraction);
      const summary = await summarise(msg.result);
      if (sender.tab?.id !== undefined) {
        const state: TabState = { result: msg.result, summary };
        await chrome.storage.session.set({ [tabKey(sender.tab.id)]: state });
      }
      return { ok: true, summary } satisfies PageResponse;
    }
    case 'lookup': {
      const settings = await getSettings();
      const ratios = await peerRatios(settings);
      const out: Record<string, LookupEntry> = {};
      for (const id of msg.listingIds.slice(0, 200)) {
        const l = await repo.listing(id);
        if (!l?.detailed) continue;
        const shop = l.shopName ? await repo.shop(l.shopName) : undefined;
        const est = estimateListingSales(l, await repo.listingSnaps(id), shop, l.shopName ? await repo.shopSnaps(l.shopName) : [], {
          fallbackSalesPerReview: settings.fallbackSalesPerReview, minShopReviewsForCalibration: settings.minShopReviewsForCalibration, peerRatios: ratios,
        });
        out[id] = { detailed: true, grade: est.available ? est.grade : undefined, monthly: est.perDay ? est.perDay.mid * 30.44 : undefined };
      }
      return out;
    }
    case 'autocomplete': {
      const settings = await getSettings();
      if (settings.pageReading) await repo.recordAutocomplete(msg.items.slice(0, 20));
      return { ok: true };
    }
    case 'tabState': {
      let id = msg.tabId;
      if (id === undefined) {
        const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
        id = tab?.id;
      }
      if (id === undefined) return {};
      const r = await chrome.storage.session.get(tabKey(id));
      return (r[tabKey(id)] ?? {}) as TabState;
    }
    case 'openDashboard': {
      await chrome.tabs.create({ url: chrome.runtime.getURL(`dashboard.html${msg.route ? `#${msg.route}` : ''}`) });
      return { ok: true };
    }
    case 'track':
      await repo.setShopTracked(msg.shopName, msg.tracked);
      return { ok: true };
    case 'saveKeyword':
      await repo.saveKeyword(msg.term);
      return { ok: true };
    case 'saveListing': {
      const cols = await repo.collections();
      let fav = cols.find((c) => c.id === 'saved-products');
      if (!fav) {
        fav = { id: 'saved-products', name: 'Saved products', kind: 'products', items: [], createdAt: Date.now() };
        await repo.saveCollection(fav);
      }
      await repo.addToCollection(fav.id, msg.listingId);
      return { ok: true };
    }
  }
  return { ok: false, error: 'Unknown message' };
}

chrome.runtime.onMessage.addListener((msg: Message, sender, sendResponse) => {
  // only accept messages from this extension's own pages and content scripts
  if (sender.id !== chrome.runtime.id) return false;
  handle(msg, sender).then(sendResponse, (e) => sendResponse({ ok: false, error: String(e?.message ?? e) }));
  return true;
});

chrome.tabs.onRemoved.addListener((id) => {
  chrome.storage.session.remove(tabKey(id));
});

chrome.runtime.onInstalled.addListener(async (d) => {
  if (d.reason === 'install') {
    await saveSettings({});
    await chrome.tabs.create({ url: chrome.runtime.getURL('dashboard.html#welcome') });
  }
  // Chrome only: open the side panel from the toolbar is not forced; the popup stays the default action.
});
