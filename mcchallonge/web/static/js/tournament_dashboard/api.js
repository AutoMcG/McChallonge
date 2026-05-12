/**
 * API calls and data loading.
 */

import { config } from './state.js';
import { setCachedData, setActiveTournamentIds } from './state.js';
import { renderDashboard } from './dashboard.js';
import { getById, setStatusMessage } from './helpers.js';

const FIXED_TOURNAMENT_URL = '/data/tournament.json';
const FIXED_PARTICIPANTS_URL = '/data/participants.json';
const FIXED_MATCHES_URL = '/data/matches.json';
const FIXED_MANIFEST_URL = '/data/manifest.json';
const CACHED_TOURNAMENT_FETCH_OPTIONS = { cache: 'force-cache' };
const UNCACHED_FETCH_OPTIONS = { cache: 'no-store' };

function normaliseByTournament(payload, valueSelector) {
    if (!payload || typeof payload !== 'object') {
        return {};
    }

    const source = payload.tournaments;
    if (!source || typeof source !== 'object') {
        return {};
    }

    const result = {};
    Object.entries(source).forEach(([key, value]) => {
        result[String(key)] = valueSelector(value);
    });
    return result;
}

function composeCachePayloadFromFixedFiles(tournamentPayload, participantsPayload, matchesPayload, manifestPayload) {
    const tournamentsById = normaliseByTournament(tournamentPayload, value => value);
    const participantsById = normaliseByTournament(participantsPayload, value => Array.isArray(value) ? value : []);
    const matchesById = normaliseByTournament(matchesPayload, value => Array.isArray(value) ? value : []);
    const manifestById = normaliseByTournament(manifestPayload, value => value || {});

    const allTournamentIds = new Set([
        ...Object.keys(tournamentsById),
        ...Object.keys(participantsById),
        ...Object.keys(matchesById),
        ...Object.keys(manifestById),
    ]);

    const merged = {};
    allTournamentIds.forEach(tournamentId => {
        merged[tournamentId] = {
            tournament: tournamentsById[tournamentId] || { id: tournamentId, name: `Tournament ${tournamentId}` },
            participants: participantsById[tournamentId] || [],
            matches: matchesById[tournamentId] || [],
            meta: manifestById[tournamentId] || {},
        };
    });

    return { tournaments: merged };
}

function renderDashboardAndResetSelection(data) {
    setActiveTournamentIds(null);
    renderDashboard(data);
}

export async function loadLocalCache() {
    try {
        if (config.clientDataMode === 'fixed') {
            const [tournamentPayload, participantsPayload, matchesPayload, manifestPayload] = await Promise.all([
                fetch(FIXED_TOURNAMENT_URL, CACHED_TOURNAMENT_FETCH_OPTIONS).then(r => r.json()),
                fetch(FIXED_PARTICIPANTS_URL, UNCACHED_FETCH_OPTIONS).then(r => r.json()),
                fetch(FIXED_MATCHES_URL, UNCACHED_FETCH_OPTIONS).then(r => r.json()),
                fetch(FIXED_MANIFEST_URL, UNCACHED_FETCH_OPTIONS).then(r => r.json()),
            ]);
            const data = composeCachePayloadFromFixedFiles(tournamentPayload, participantsPayload, matchesPayload, manifestPayload);
            renderDashboard(data);
            setStatusMessage('', 'info');
            return;
        }

        const response = await fetch(config.apiCacheUrl, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`Failed to load cache: ${response.statusText}`);
        }
        const data = await response.json();
        renderDashboard(data);
        setStatusMessage('', 'info');
    } catch (error) {
        setStatusMessage(error.message, 'warning');
    }
}

export async function updateLocalCache() {
    if (config.clientDataMode === 'fixed') {
        setStatusMessage('Static mode is read-only. Data updates come from Lambda publishing /data/*.json.', 'info');
        return;
    }

    const button = getById('refresh-cache-btn');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Loading...';
    }

    try {
        const response = await fetch(config.apiCacheUrl, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`Failed to load cache: ${response.statusText}`);
        }
        const data = await response.json();
        renderDashboardAndResetSelection(data);
        setStatusMessage('', 'info');
    } catch (error) {
        setStatusMessage(error.message, 'danger');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Update Local Cache';
        }
    }
}

export function clearLocalCache() {
    setCachedData(null);
    setActiveTournamentIds(null);
    const bracketFilters = getById('match-bracket-filters');
    if (bracketFilters) bracketFilters.innerHTML = '';
    const stateFilters = getById('match-state-filters');
    if (stateFilters) stateFilters.innerHTML = '';
    const tournFilters = getById('tournament-filters');
    if (tournFilters) tournFilters.innerHTML = '';
    const cacheMeta = getById('cache-meta');
    if (cacheMeta) cacheMeta.textContent = 'Local cache has not been loaded yet.';
    setStatusMessage('Display cleared.', 'info');
}

export async function syncFromChallonge() {
    const button = getById('sync-challonge-btn');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Syncing...';
    }

    try {
        const response = await fetch(config.apiCacheUpdateUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                underway_source_mode: config.underwaySourceMode || 'challonge',
            }),
        });

        if (!response.ok) {
            const payload = await response.json();
            throw new Error(payload.error || 'Failed to sync from Challonge.');
        }

        const data = await response.json();
        renderDashboardAndResetSelection(data);
        if (config.underwaySourceMode === 'cache') {
            setStatusMessage('Synced from Challonge. Underway flags were preserved from server cache mode.', 'success');
            return;
        }
        setStatusMessage('Synced from Challonge successfully.', 'success');
    } catch (error) {
        setStatusMessage(error.message, 'danger');
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-cloud-download-alt me-1"></i> Sync from Challonge';
        }
    }
}


export async function setMatchUnderway(tournamentKey, matchId) {
    if (!tournamentKey || matchId == null) {
        throw new Error('Missing tournament key or match id.');
    }

    const response = await fetch('/api/cache/match/underway', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tournament_key: String(tournamentKey),
            match_id: String(matchId),
        }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Failed to mark match as underway.');
    }

    const data = await response.json();
    renderDashboardAndResetSelection(data);
    setStatusMessage('Match marked as underway.', 'success');
}


export async function clearMatchUnderway(tournamentKey, matchId) {
    if (!tournamentKey || matchId == null) {
        throw new Error('Missing tournament key or match id.');
    }

    const response = await fetch('/api/cache/match/underway/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tournament_key: String(tournamentKey),
            match_id: String(matchId),
        }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Failed to clear underway status.');
    }

    const data = await response.json();
    renderDashboardAndResetSelection(data);
    setStatusMessage('Underway status cleared.', 'success');
}
