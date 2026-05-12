/**
 * Main initialization and event listeners.
 */

import { initializeConfig, config, activeMatchSearchMode, setActiveMatchSearchMode, setActiveMatchStates } from './state.js';
import { loadMatchSearchChips, renderMatchSearchChips, clearAllMatchSearchChips, addMatchSearchChip } from './search-chips.js';
import { loadMatchSearchMode, saveMatchSearchMode } from './search-mode.js';
import { getById, setStatusMessage } from './helpers.js';
import { loadLocalCache, updateLocalCache, clearLocalCache, syncFromChallonge, setMatchUnderway, clearMatchUnderway } from './api.js';
import { renderDashboard } from './dashboard.js';
import { dashboardEvents, DASHBOARD_EVENT } from './events.js';
import { getFilteredMatches, getFilteredParticipants } from './filters.js';
import { renderMatches, renderParticipantsTable } from './renderers.js';

document.addEventListener('DOMContentLoaded', () => {
    initializeConfig();

    const actionButtons = {
        'update-cache': {
            id: 'refresh-cache-btn',
            busyHtml: '<i class="fas fa-spinner fa-spin me-1"></i> Loading...',
            idleHtml: '<i class="fas fa-sync-alt me-1"></i> Update Local Cache',
        },
        'sync-challonge': {
            id: 'sync-challonge-btn',
            busyHtml: '<i class="fas fa-spinner fa-spin me-1"></i> Syncing...',
            idleHtml: '<i class="fas fa-cloud-download-alt me-1"></i> Sync from Challonge',
        },
    };

    function setActionButtonBusy(action, isBusy) {
        const meta = actionButtons[action];
        if (!meta) return;
        const button = getById(meta.id);
        if (!button) return;
        button.disabled = isBusy;
        button.innerHTML = isBusy ? meta.busyHtml : meta.idleHtml;
    }

    dashboardEvents.addEventListener(DASHBOARD_EVENT.DATA_LOADED, (event) => {
        const data = event?.detail?.data;
        if (!data) return;
        renderDashboard(data);
    });

    dashboardEvents.addEventListener(DASHBOARD_EVENT.DATA_CLEARED, () => {
        const bracketFilters = getById('match-bracket-filters');
        if (bracketFilters) bracketFilters.innerHTML = '';
        const stateFilters = getById('match-state-filters');
        if (stateFilters) stateFilters.innerHTML = '';
        const tournFilters = getById('tournament-filters');
        if (tournFilters) tournFilters.innerHTML = '';
        const cacheMeta = getById('cache-meta');
        if (cacheMeta) cacheMeta.textContent = 'Local cache has not been loaded yet.';
    });

    dashboardEvents.addEventListener(DASHBOARD_EVENT.STATUS, (event) => {
        setStatusMessage(event?.detail?.message, event?.detail?.level || 'info');
    });

    dashboardEvents.addEventListener(DASHBOARD_EVENT.ACTION_STARTED, (event) => {
        setActionButtonBusy(event?.detail?.action, true);
    });

    dashboardEvents.addEventListener(DASHBOARD_EVENT.ACTION_FINISHED, (event) => {
        setActionButtonBusy(event?.detail?.action, false);
    });

    // Queue view defaults to open matches only (Complete unchecked by default).
    if (config.showOnly === 'queue') {
        setActiveMatchStates(new Set(['open']));
    }

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

    const matchesContainer = getById('matches-container');
    if (matchesContainer) {
        matchesContainer.addEventListener('click', async (event) => {
            const button = event.target.closest('.match-underway-btn, .match-clear-underway-btn');
            if (!button) return;

            const tournamentKey = button.dataset.tournamentKey;
            const matchId = button.dataset.matchId;
            if (!tournamentKey || !matchId) {
                setStatusMessage('Unable to mark match underway: missing identifiers.', 'warning');
                return;
            }

            button.disabled = true;
            const original = button.innerHTML;
            const isClearAction = button.classList.contains('match-clear-underway-btn');
            button.innerHTML = isClearAction
                ? '<i class="fas fa-spinner fa-spin me-1"></i>Clearing...'
                : '<i class="fas fa-spinner fa-spin me-1"></i>Setting...';
            try {
                if (isClearAction) {
                    await clearMatchUnderway(tournamentKey, matchId);
                } else {
                    await setMatchUnderway(tournamentKey, matchId);
                }
            } catch (error) {
                setStatusMessage(error.message || 'Failed to update underway status.', 'danger');
            } finally {
                button.disabled = false;
                button.innerHTML = original;
            }
        });
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
            setStatusMessage('Server cache mode selected. Sync will preserve current underway flags from cache.', 'info');
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
