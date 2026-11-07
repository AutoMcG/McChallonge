/**
 * API calls and data loading.
 */

import { config } from './state.js';
import { setCachedData, setActiveTournamentIds } from './state.js';
import { dashboardEvents, DASHBOARD_EVENT } from './events.js';

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

function emitDashboardDataLoaded(data) {
    dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.DATA_LOADED, {
        detail: { data },
    }));
}

function emitStatus(message, level) {
    dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.STATUS, {
        detail: { message, level },
    }));
}

function emitDashboardDataLoadedAndResetSelection(data) {
    setActiveTournamentIds(null);
    emitDashboardDataLoaded(data);
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
            emitDashboardDataLoaded(data);
            emitStatus('', 'info');
            return;
        }

        const response = await fetch(config.apiCacheUrl, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`Failed to load cache: ${response.statusText}`);
        }
        const data = await response.json();
        emitDashboardDataLoaded(data);
        emitStatus('', 'info');
    } catch (error) {
        emitStatus(error.message, 'warning');
    }
}

export async function updateLocalCache() {
    if (config.clientDataMode === 'fixed') {
        emitStatus('Static mode is read-only. Data updates come from Lambda publishing /data/*.json.', 'info');
        return;
    }

    dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.ACTION_STARTED, {
        detail: { action: 'update-cache' },
    }));

    try {
        const response = await fetch(config.apiCacheUrl, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`Failed to load cache: ${response.statusText}`);
        }
        const data = await response.json();
        emitDashboardDataLoadedAndResetSelection(data);
        emitStatus('', 'info');
    } catch (error) {
        emitStatus(error.message, 'danger');
    } finally {
        dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.ACTION_FINISHED, {
            detail: { action: 'update-cache' },
        }));
    }
}

export function clearLocalCache() {
    setCachedData(null);
    setActiveTournamentIds(null);
    dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.DATA_CLEARED));
    emitStatus('Display cleared.', 'info');
}

export async function syncFromChallonge() {
    dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.ACTION_STARTED, {
        detail: { action: 'sync-challonge' },
    }));

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
        emitDashboardDataLoadedAndResetSelection(data);
        if (config.underwaySourceMode === 'cache') {
            emitStatus('Synced from Challonge. Underway flags were preserved from server cache mode.', 'success');
            return;
        }
        emitStatus('Synced from Challonge successfully.', 'success');
    } catch (error) {
        emitStatus(error.message, 'danger');
    } finally {
        dashboardEvents.dispatchEvent(new CustomEvent(DASHBOARD_EVENT.ACTION_FINISHED, {
            detail: { action: 'sync-challonge' },
        }));
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
    emitDashboardDataLoadedAndResetSelection(data);
    emitStatus('Match marked as underway.', 'success');
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
    emitDashboardDataLoadedAndResetSelection(data);
    emitStatus('Underway status cleared.', 'success');
}
