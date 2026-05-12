/**
 * Main initialization and event listeners.
 */

import { initializeConfig, config, activeMatchSearchMode, setActiveMatchSearchMode } from './state.js';
import { loadMatchSearchChips, renderMatchSearchChips, clearAllMatchSearchChips, addMatchSearchChip } from './search-chips.js';
import { loadMatchSearchMode, saveMatchSearchMode } from './search-mode.js';
import { getById } from './helpers.js';
import { loadLocalCache, updateLocalCache, clearLocalCache, syncFromChallonge } from './api.js';
import { getFilteredMatches, getFilteredParticipants } from './filters.js';
import { renderMatches, renderParticipantsTable } from './renderers.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeConfig();

    initializeUnderwaySourceControl();
    
    loadMatchSearchChips();
    const savedMode = loadMatchSearchMode();
    setActiveMatchSearchMode(savedMode);
    renderMatchSearchChips();
    syncMatchSearchModeControl();

    // Reload and Clear are available to everyone (no Challonge API calls involved).
    const refreshButton = getById('refresh-cache-btn');
    if (refreshButton) {
        if (config.clientDataMode === 'fixed') {
            refreshButton.style.display = 'none';
        } else {
            refreshButton.addEventListener('click', updateLocalCache);
        }
    }

    const clearButton = getById('clear-cache-btn');
    if (clearButton) {
        if (config.clientDataMode === 'fixed') {
            clearButton.style.display = 'none';
        } else {
            clearButton.addEventListener('click', clearLocalCache);
        }
    }

    // Sync from Challonge is admin-only (loopback); backend enforces this independently.
    const syncButton = getById('sync-challonge-btn');
    if (syncButton) {
        if (config.adminEnabled && config.clientDataMode !== 'fixed') {
            syncButton.style.display = '';
            syncButton.addEventListener('click', syncFromChallonge);
        }
    }

    const nameFilter = getById('participant-name-filter');
    if (nameFilter) {
        nameFilter.addEventListener('input', () => {
            renderParticipantsTable(getFilteredParticipants());
        });
    }

    const matchFilterInput = getById('match-text-filter-input');
    const matchFilterAddButton = getById('match-text-filter-add');
    const matchFilterModeAll = getById('match-text-mode-all');
    const matchFilterModeAny = getById('match-text-mode-any');
    const matchFilterClearAllButton = getById('match-text-filter-clear-all');

    const addMatchChipFromInput = () => {
        if (!matchFilterInput) return;
        addMatchSearchChip(matchFilterInput.value);
        matchFilterInput.value = '';
        matchFilterInput.focus();
    };

    if (matchFilterAddButton) {
        matchFilterAddButton.addEventListener('click', addMatchChipFromInput);
    }

    if (matchFilterInput) {
        matchFilterInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                addMatchChipFromInput();
            }
        });
    }

    if (matchFilterModeAll) {
        matchFilterModeAll.addEventListener('change', () => {
            if (!matchFilterModeAll.checked) return;
            setActiveMatchSearchMode('all');
            saveMatchSearchMode();
            renderMatches(getFilteredMatches());
        });
    }

    if (matchFilterModeAny) {
        matchFilterModeAny.addEventListener('change', () => {
            if (!matchFilterModeAny.checked) return;
            setActiveMatchSearchMode('any');
            saveMatchSearchMode();
            renderMatches(getFilteredMatches());
        });
    }

    if (matchFilterClearAllButton) {
        matchFilterClearAllButton.addEventListener('click', clearAllMatchSearchChips);
    }

    loadLocalCache();
});

function initializeUnderwaySourceControl() {
    const sourceSelect = getById('underway-source-mode');
    if (!sourceSelect) return;

    const validModes = new Set(['challonge', 'cache']);
    const savedMode = window.localStorage.getItem('mcchallonge-underway-source-mode');
    const initialMode = validModes.has(savedMode) ? savedMode : config.underwaySourceMode;

    config.underwaySourceMode = validModes.has(initialMode) ? initialMode : 'challonge';
    sourceSelect.value = config.underwaySourceMode;

    sourceSelect.addEventListener('change', () => {
        const selectedMode = validModes.has(sourceSelect.value) ? sourceSelect.value : 'challonge';
        config.underwaySourceMode = selectedMode;
        window.localStorage.setItem('mcchallonge-underway-source-mode', selectedMode);

        if (selectedMode === 'cache') {
            setStatusMessage('Server cache override mode selected. Match-level underway override is not wired yet.', 'info');
            return;
        }
        setStatusMessage('', 'info');
    });
}

function syncMatchSearchModeControl() {
    const allMode = getById('match-text-mode-all');
    const anyMode = getById('match-text-mode-any');
    if (allMode) allMode.checked = activeMatchSearchMode === 'all';
    if (anyMode) anyMode.checked = activeMatchSearchMode === 'any';
}
