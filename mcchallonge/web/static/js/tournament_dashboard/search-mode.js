/**
 * Search mode toggle management and persistence.
 */

import { activeMatchSearchMode } from './state.js';

const SEARCH_MODE_KEY = 'activeMatchSearchMode';

export function loadMatchSearchMode() {
    const stored = localStorage.getItem(SEARCH_MODE_KEY);
    if (stored === 'all' || stored === 'any') {
        return stored;
    }
    return 'all'; // default
}

export function saveMatchSearchMode() {
    localStorage.setItem(SEARCH_MODE_KEY, activeMatchSearchMode);
}
