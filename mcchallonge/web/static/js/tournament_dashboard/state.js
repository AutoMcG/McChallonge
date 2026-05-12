/**
 * Shared state and configuration for the tournament dashboard.
 */

export const config = {
    apiCacheUrl: '/api/cache',
    apiCacheUpdateUrl: '/api/cache/update',
    apiCacheClearUrl: '/api/cache/clear',
    underwaySourceMode: 'challonge',
    clientDataMode: 'api',
    clientDataRoot: '/data',
    adminEnabled: true,
    showOnly: '',
};

// Initialize from window config if present
export function initializeConfig() {
    const cfg = window.__MCC_DASHBOARD_CONFIG || {};
    config.apiCacheUrl = cfg.apiCacheUrl || '/api/cache';
    config.apiCacheUpdateUrl = cfg.apiCacheUpdateUrl || '/api/cache/update';
    config.apiCacheClearUrl = cfg.apiCacheClearUrl || '/api/cache/clear';
    config.underwaySourceMode = cfg.underwaySourceMode || 'challonge';
    config.clientDataMode = cfg.clientDataMode || 'api';
    config.clientDataRoot = cfg.clientDataRoot || '/data';
    config.adminEnabled = cfg.adminEnabled !== false;
    config.showOnly = cfg.showOnly || '';
}

// Cached tournament data
export let cachedData = null;

export function setCachedData(data) {
    cachedData = data;
}

// Filter state
export let activeMatchStates = new Set(['complete', 'open']);
export let activeMatchSearchChips = [];
export let activeMatchSearchMode = 'all';
export let activeTournamentIds = null;
export let activeBrackets = new Set(['upper', 'lower']);

export function setActiveMatchStates(states) {
    activeMatchStates = states;
}

export function setActiveMatchSearchChips(chips) {
    activeMatchSearchChips = chips;
}

export function setActiveMatchSearchMode(mode) {
    activeMatchSearchMode = mode;
}

export function setActiveTournamentIds(ids) {
    activeTournamentIds = ids;
}
