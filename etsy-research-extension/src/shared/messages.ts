import type { PageResult } from './types';
import type { PanelSummary } from '../core/summaries';

export type Message =
  | { type: 'page'; result: PageResult }
  | { type: 'lookup'; listingIds: string[] }
  | { type: 'autocomplete'; items: string[] }
  | { type: 'tabState'; tabId?: number }
  | { type: 'openDashboard'; route?: string }
  | { type: 'track'; shopName: string; tracked: boolean }
  | { type: 'saveKeyword'; term: string }
  | { type: 'saveListing'; listingId: string };

export interface LookupEntry {
  monthly?: number;
  grade?: string;
  detailed: boolean;
}

export interface PageResponse {
  ok: boolean;
  error?: string;
  summary?: PanelSummary;
}

export interface TabState {
  result?: PageResult;
  summary?: PanelSummary;
}

export function send<T = unknown>(msg: Message): Promise<T> {
  return chrome.runtime.sendMessage(msg) as Promise<T>;
}
