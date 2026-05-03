(function () {
    const cfg = window.__MCC_DASHBOARD_CONFIG || {};
    const API_CACHE_URL = cfg.apiCacheUrl || '/cache/data';
    const API_CACHE_UPDATE_URL = cfg.apiCacheUpdateUrl || '/cache/data/update';
    const API_CACHE_CLEAR_URL = cfg.apiCacheClearUrl || '/cache/data/clear';

    const CLIENT_DATA_MODE = cfg.clientDataMode || 'api';
    const CLIENT_DATA_ROOT = cfg.clientDataRoot || '/data';
    const ADMIN_ENABLED = cfg.adminEnabled !== false;  // default true; false hides update/clear controls

    const FIXED_TOURNAMENT_URL = `${CLIENT_DATA_ROOT}/tournament.json`;
    const FIXED_PARTICIPANTS_URL = `${CLIENT_DATA_ROOT}/participants.json`;
    const FIXED_MATCHES_URL = `${CLIENT_DATA_ROOT}/matches.json`;
    const FIXED_MANIFEST_URL = `${CLIENT_DATA_ROOT}/manifest.json`;
    const MATCH_SEARCH_CHIPS_STORAGE_KEY = 'mcchallonge.matchSearchChips.v1';
    const MATCH_SEARCH_MODE_STORAGE_KEY = 'mcchallonge.matchSearchMode.v1';

    const showOnly = cfg.showOnly || '';

    let cachedData = null;
    let activeMatchStates = new Set(['complete', 'open']);
    let activeMatchSearchChips = [];
    let activeMatchSearchMode = 'all';
    // null = not yet initialised; populated with all tournament keys on first load
    let activeTournamentIds = null;

    function getById(id) {
        return document.getElementById(id);
    }

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value ?? '';
        return div.innerHTML;
    }

    // Data helpers

    function getAllTournamentEntries() {
        return Object.entries(cachedData?.tournaments || {});
    }

    function getAllParticipants() {
        return getAllTournamentEntries().flatMap(([key, entry]) => {
            const tName = entry.tournament?.name || key;
            return (entry.participants || []).map(p => ({
                ...p, _tournament_key: key, _tournament_name: tName,
            }));
        });
    }

    function getAllMatches() {
        return getAllTournamentEntries().flatMap(([key, entry]) => {
            const tName = entry.tournament?.name || key;
            return (entry.matches || []).map(m => ({
                ...m, _tournament_key: key, _tournament_name: tName,
            }));
        });
    }

    function getAllParticipantMap() {
        const map = new Map();
        getAllTournamentEntries().forEach(([, entry]) => {
            (entry.participants || []).forEach(p => map.set(p.id, p));
        });
        return map;
    }

    function getFilteredParticipants() {
        const all = getAllParticipants();
        const query = (getById('participant-name-filter')?.value || '').trim().toLowerCase();
        return all.filter(p => {
            const matchesTournament = !activeTournamentIds || activeTournamentIds.has(p._tournament_key);
            const matchesName = !query || (p.name || '').toLowerCase().includes(query);
            return matchesTournament && matchesName;
        });
    }

    function getFilteredMatches() {
        const participantsById = getAllParticipantMap();
        return getAllMatches().filter(m => {
            const matchesTournament = !activeTournamentIds || activeTournamentIds.has(m._tournament_key);
            const matchesState = activeMatchStates.has((m.state || '').toLowerCase());
            const matchesText = doesMatchPassSearchChips(m, participantsById);
            return matchesTournament && matchesState && matchesText;
        });
    }

    function normaliseMatchSearchChip(value) {
        return String(value || '').trim().replace(/\s+/g, ' ');
    }

    function saveMatchSearchChips() {
        try {
            localStorage.setItem(MATCH_SEARCH_CHIPS_STORAGE_KEY, JSON.stringify(activeMatchSearchChips));
        } catch (error) {
            console.warn('Failed to persist match search chips:', error);
        }
    }

    function loadMatchSearchChips() {
        try {
            const raw = localStorage.getItem(MATCH_SEARCH_CHIPS_STORAGE_KEY);
            if (!raw) {
                activeMatchSearchChips = [];
                return;
            }
            const parsed = JSON.parse(raw);
            activeMatchSearchChips = Array.isArray(parsed)
                ? parsed.map(normaliseMatchSearchChip).filter(Boolean)
                : [];
        } catch (error) {
            console.warn('Failed to load match search chips:', error);
            activeMatchSearchChips = [];
        }
    }

    function saveMatchSearchMode() {
        try {
            localStorage.setItem(MATCH_SEARCH_MODE_STORAGE_KEY, activeMatchSearchMode);
        } catch (error) {
            console.warn('Failed to persist match search mode:', error);
        }
    }

    function loadMatchSearchMode() {
        try {
            const raw = (localStorage.getItem(MATCH_SEARCH_MODE_STORAGE_KEY) || '').toLowerCase();
            activeMatchSearchMode = raw === 'any' ? 'any' : 'all';
        } catch (error) {
            console.warn('Failed to load match search mode:', error);
            activeMatchSearchMode = 'all';
        }
    }

    function syncMatchSearchModeControl() {
        const allMode = getById('match-text-mode-all');
        const anyMode = getById('match-text-mode-any');
        if (allMode) allMode.checked = activeMatchSearchMode === 'all';
        if (anyMode) anyMode.checked = activeMatchSearchMode === 'any';
    }

    function getRoundMetadata(roundValue) {
        if (roundValue === null || roundValue === undefined || roundValue === '') {
            return {
                label: 'No Round',
                aliases: ['no round', 'round none', 'unassigned round'],
            };
        }

        const raw = String(roundValue).trim();
        const cleaned = raw
            .replace(/\brount\b/gi, 'round')
            .replace(/[_-]+/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

        const numericMatch = cleaned.match(/-?\d+/);
        if (numericMatch) {
            const roundNumber = Number(numericMatch[0]);
            if (!Number.isNaN(roundNumber)) {
                return {
                    label: `Round ${roundNumber}`,
                    aliases: [
                        `round ${roundNumber}`,
                        `round${roundNumber}`,
                        `r${roundNumber}`,
                        String(roundNumber),
                        raw.toLowerCase(),
                        cleaned.toLowerCase(),
                    ],
                };
            }
        }

        const label = cleaned
            ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
            : 'Unknown Round';

        return {
            label,
            aliases: [raw.toLowerCase(), cleaned.toLowerCase(), label.toLowerCase()],
        };
    }

    function getMatchSearchHaystack(match, participantsById) {
        const player1 = participantsById.get(match.player1_id)?.name || '';
        const player2 = participantsById.get(match.player2_id)?.name || '';
        const roundMeta = getRoundMetadata(match.round);
        return [
            match.id,
            match.identifier,
            match.state,
            match.round,
            ...roundMeta.aliases,
            match.completed_at,
            match.scores_csv,
            match._tournament_name,
            match._tournament_key,
            player1,
            player2,
        ]
            .map(value => String(value || '').toLowerCase())
            .join(' ');
    }

    function doesMatchPassSearchChips(match, participantsById) {
        if (!activeMatchSearchChips.length) {
            return true;
        }

        const haystack = getMatchSearchHaystack(match, participantsById);
        if (activeMatchSearchMode === 'any') {
            return activeMatchSearchChips.some(chip => haystack.includes(chip.toLowerCase()));
        }
        return activeMatchSearchChips.every(chip => haystack.includes(chip.toLowerCase()));
    }

    function renderMatchSearchChips() {
        const container = getById('match-text-filter-chips');
        if (!container) return;

        if (!activeMatchSearchChips.length) {
            container.innerHTML = '<span class="match-filter-chip-empty">No text filters applied.</span>';
            return;
        }

        container.innerHTML = activeMatchSearchChips.map((chip, index) => {
            const escapedChip = escapeHtml(chip);
            return `
                <span class="match-filter-chip">
                    <button type="button" class="match-filter-chip-edit" data-chip-index="${index}" aria-label="Edit filter ${escapedChip}">${escapedChip}</button>
                    <button type="button" class="match-filter-chip-remove" data-chip-index="${index}" aria-label="Remove filter ${escapedChip}">&times;</button>
                </span>
            `;
        }).join('');

        container.querySelectorAll('.match-filter-chip-edit').forEach(button => {
            button.addEventListener('click', () => {
                const index = Number(button.dataset.chipIndex);
                if (Number.isNaN(index) || index < 0 || index >= activeMatchSearchChips.length) {
                    return;
                }

                const current = activeMatchSearchChips[index];
                const updated = window.prompt('Edit match filter chip', current);
                if (updated === null) {
                    return;
                }

                const normalised = normaliseMatchSearchChip(updated);
                if (!normalised) {
                    activeMatchSearchChips.splice(index, 1);
                } else {
                    const duplicateIndex = activeMatchSearchChips.findIndex((chip, idx) => idx !== index && chip.toLowerCase() === normalised.toLowerCase());
                    if (duplicateIndex >= 0) {
                        return;
                    }
                    activeMatchSearchChips[index] = normalised;
                }

                saveMatchSearchChips();
                renderMatchSearchChips();
                renderMatches(getFilteredMatches());
            });
        });

        container.querySelectorAll('.match-filter-chip-remove').forEach(button => {
            button.addEventListener('click', () => {
                const index = Number(button.dataset.chipIndex);
                if (Number.isNaN(index) || index < 0 || index >= activeMatchSearchChips.length) {
                    return;
                }
                activeMatchSearchChips.splice(index, 1);
                saveMatchSearchChips();
                renderMatchSearchChips();
                renderMatches(getFilteredMatches());
            });
        });
    }

    function addMatchSearchChip(chipText) {
        const chip = normaliseMatchSearchChip(chipText);
        if (!chip) {
            return;
        }

        const alreadyExists = activeMatchSearchChips.some(existing => existing.toLowerCase() === chip.toLowerCase());
        if (alreadyExists) {
            return;
        }

        activeMatchSearchChips.push(chip);
        saveMatchSearchChips();
        renderMatchSearchChips();
        renderMatches(getFilteredMatches());
    }

    function clearAllMatchSearchChips() {
        activeMatchSearchChips = [];
        saveMatchSearchChips();
        renderMatchSearchChips();
        renderMatches(getFilteredMatches());
    }

    // Status message

    function setStatusMessage(message, level) {
        const status = getById('status-message');
        if (!status) return;
        if (!message) {
            status.style.display = 'none';
            status.className = 'alert status-message';
            status.textContent = '';
            return;
        }
        status.style.display = 'block';
        status.className = `alert status-message alert-${level}`;
        status.textContent = message;
    }

    // Render functions

    function renderTournamentSection() {
        const allEntries = getAllTournamentEntries();
        const selectedEntries = (activeTournamentIds && activeTournamentIds.size > 0)
            ? allEntries.filter(([key]) => activeTournamentIds.has(key))
            : allEntries;

        const single = selectedEntries.length === 1 ? selectedEntries[0][1] : null;
        const tournament = single?.tournament || {};

        const name = getById('tournament-name');
        const id = getById('tournament-id');
        const status = getById('tournament-status');
        const cacheMeta = getById('cache-meta');

        if (name) {
            if (single) {
                if (showOnly === 'participants') {
                    name.textContent = `${tournament.name || 'Tournament'} - Participants`;
                } else if (showOnly === 'matches') {
                    name.textContent = `${tournament.name || 'Tournament'} - Matches`;
                } else {
                    name.textContent = tournament.name || 'Tournament Dashboard';
                }
            } else {
                const count = selectedEntries.length || allEntries.length;
                name.textContent = showOnly === 'participants' ? 'Participants'
                    : showOnly === 'matches' ? 'Matches'
                        : `Tournament Dashboard (${count} tournaments)`;
            }
        }

        if (id) {
            id.textContent = single
                ? `Tournament ID: ${tournament.id ?? 'Unknown'}`
                : `${selectedEntries.length || allEntries.length} tournament(s) loaded`;
        }

        if (status) {
            if (single) {
                const state = (tournament.state || 'unknown').toLowerCase();
                status.textContent = state.charAt(0).toUpperCase() + state.slice(1);
                status.classList.remove('status-underway', 'status-completed');
                status.classList.add(state === 'completed' ? 'status-completed' : 'status-underway');
                status.style.display = '';
            } else {
                status.style.display = 'none';
            }
        }

        if (cacheMeta) {
            const times = allEntries.map(([, e]) => e.meta?.cached_at).filter(Boolean);
            const latestTime = times.sort().pop();
            cacheMeta.textContent = latestTime
                ? `Local cache updated at ${latestTime}`
                : 'Local cache has not been loaded yet.';
        }

        // Event Details panel - one block per tournament in the current selection
        const detailsContainer = getById('event-details-container');
        if (detailsContainer) {
            if (selectedEntries.length === 0) {
                detailsContainer.innerHTML = '<p class="empty-state">No event data loaded.</p>';
            } else {
                const multi = selectedEntries.length > 1;
                detailsContainer.innerHTML = selectedEntries.map(([, entry], idx) => {
                    const t = entry.tournament || {};
                    const slug = t.url || '';
                    const urlHtml = slug
                        ? `<a href="https://challonge.com/${escapeHtml(slug)}" target="_blank">${escapeHtml(slug)}</a>`
                        : 'Not available';
                    const header = multi
                        ? `<h6 class="fw-bold ${idx > 0 ? 'border-top pt-2 mt-2' : ''}">${escapeHtml(t.name || 'Unknown')}</h6>`
                        : '';
                    return `
                        ${header}
                        <p><strong>Name:</strong> ${escapeHtml(t.name || 'Unknown')}</p>
                        <p><strong>URL:</strong> ${urlHtml}</p>
                        <p><strong>Started:</strong> ${escapeHtml(t.started_at || 'Not started')}</p>
                        <p><strong>Completed:</strong> ${escapeHtml(t.completed_at || 'In progress')}</p>
                    `;
                }).join('');
            }
        }
    }

    function renderParticipantsTable(participants) {
        const table = document.querySelector('.participants-table');
        const body = table?.querySelector('tbody');
        if (!body) return;

        const multiTournament = getAllTournamentEntries().length > 1;
        if (table) table.classList.toggle('multi-tournament', multiTournament);

        if (!participants || participants.length === 0) {
            const cols = multiTournament ? 6 : 5;
            body.innerHTML = `<tr><td colspan="${cols}" class="empty-state">No participants in local cache.</td></tr>`;
            return;
        }

        body.innerHTML = participants
            .map((participant, index) => {
                const wins = Number(participant.wins || 0);
                const losses = Number(participant.losses || 0);
                const total = wins + losses;
                const winRate = total > 0 ? `${Math.round((wins / total) * 100)}%` : 'N/A';
                const tournamentCell = multiTournament
                    ? `<td>${escapeHtml(participant._tournament_name || '')}</td>`
                    : '';
                return `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${escapeHtml(participant.name || 'Unknown')}</td>
                        ${tournamentCell}
                        <td>${wins}</td>
                        <td>${losses}</td>
                        <td>${winRate}</td>
                    </tr>
                `;
            })
            .join('');
    }

    function renderMatches(matches) {
        const container = getById('matches-container');
        if (!container) return;

        const multiTournament = getAllTournamentEntries().length > 1;

        if (!matches || matches.length === 0) {
            container.innerHTML = '<div class="empty-state">No matches in local cache.</div>';
            return;
        }

        const participantsById = getAllParticipantMap();
        container.innerHTML = matches
            .map((match) => {
                const player1 = participantsById.get(match.player1_id)?.name || 'Player 1';
                const player2 = participantsById.get(match.player2_id)?.name || 'Player 2';
                const roundMeta = getRoundMetadata(match.round);
                const isPlayer1Winner = match.winner_id && match.winner_id === match.player1_id;
                const isPlayer2Winner = match.winner_id && match.winner_id === match.player2_id;
                const state = (match.state || 'pending').toLowerCase();
                const tournamentBadge = multiTournament
                    ? `<span class="tournament-badge">${escapeHtml(match._tournament_name || '')}</span>`
                    : '';
                return `
                    <div class="match">
                        <div class="players">
                            <div class="player ${isPlayer1Winner ? 'winner' : ''}">${escapeHtml(player1)}</div>
                            <div class="vs">VS</div>
                            <div class="player ${isPlayer2Winner ? 'winner' : ''}">${escapeHtml(player2)}</div>
                        </div>
                        <div class="match-info">
                            ${match.round != null && String(match.round).trim() !== '' ? `<span class="round">${escapeHtml(roundMeta.label)}</span>` : ''}
                            <span class="state ${state === 'complete' ? 'state-complete' : 'state-pending'}">
                                ${escapeHtml(state.charAt(0).toUpperCase() + state.slice(1))}
                            </span>
                            ${match.completed_at ? `<span class="date">${escapeHtml(match.completed_at)}</span>` : ''}
                            ${tournamentBadge}
                        </div>
                    </div>
                `;
            })
            .join('');
    }

    // Filter builders

    function buildMatchStateFilters(matches) {
        const container = getById('match-state-filters');
        if (!container) return;

        const states = [...new Set((matches || []).map(m => (m.state || 'pending').toLowerCase()))].sort();

        container.innerHTML = states.map(state => {
            const label = escapeHtml(state.charAt(0).toUpperCase() + state.slice(1));
            const checked = activeMatchStates.has(state) ? 'checked' : '';
            return `
                <div class="form-check form-check-inline mb-0">
                    <input class="form-check-input match-state-checkbox" type="checkbox"
                           id="filter-state-${escapeHtml(state)}" value="${escapeHtml(state)}" ${checked}>
                    <label class="form-check-label" for="filter-state-${escapeHtml(state)}">${label}</label>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.match-state-checkbox').forEach(cb => {
            cb.addEventListener('change', e => {
                if (e.target.checked) {
                    activeMatchStates.add(e.target.value);
                } else {
                    activeMatchStates.delete(e.target.value);
                }
                renderMatches(getFilteredMatches());
            });
        });
    }

    function buildTournamentFilters() {
        const container = getById('tournament-filters');
        if (!container) return;

        const entries = getAllTournamentEntries();
        if (entries.length <= 1) {
            container.style.display = 'none';
            return;
        }
        container.style.display = '';

        container.innerHTML = entries.map(([key, entry]) => {
            const name = entry.tournament?.name || key;
            const checked = !activeTournamentIds || activeTournamentIds.has(key) ? 'checked' : '';
            return `
                <div class="form-check form-check-inline mb-0">
                    <input class="form-check-input tournament-filter-checkbox" type="checkbox"
                           id="filter-tournament-${escapeHtml(key)}" value="${escapeHtml(key)}" ${checked}>
                    <label class="form-check-label" for="filter-tournament-${escapeHtml(key)}">${escapeHtml(name)}</label>
                </div>
            `;
        }).join('');

        container.querySelectorAll('.tournament-filter-checkbox').forEach(cb => {
            cb.addEventListener('change', e => {
                if (e.target.checked) {
                    activeTournamentIds.add(e.target.value);
                } else {
                    activeTournamentIds.delete(e.target.value);
                }
                renderTournamentSection();
                renderParticipantsTable(getFilteredParticipants());
                renderMatches(getFilteredMatches());
            });
        });
    }

    // Dashboard orchestration

    function renderDashboard(data) {
        cachedData = data;
        // Initialise tournament filter to all keys on first load.
        if (activeTournamentIds === null) {
            activeTournamentIds = new Set(Object.keys(data.tournaments || {}));
        }
        const allMatches = getAllMatches();
        renderTournamentSection();
        buildTournamentFilters();
        buildMatchStateFilters(allMatches);
        renderParticipantsTable(getFilteredParticipants());
        renderMatches(getFilteredMatches());
    }

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

    // API calls

    async function loadLocalCache() {
        try {
            if (CLIENT_DATA_MODE === 'fixed') {
                const [tournamentResponse, participantsResponse, matchesResponse, manifestResponse] = await Promise.all([
                    fetch(FIXED_TOURNAMENT_URL, { cache: 'no-store' }),
                    fetch(FIXED_PARTICIPANTS_URL, { cache: 'no-store' }),
                    fetch(FIXED_MATCHES_URL, { cache: 'no-store' }),
                    fetch(FIXED_MANIFEST_URL, { cache: 'no-store' }),
                ]);

                if (!tournamentResponse.ok || !participantsResponse.ok || !matchesResponse.ok) {
                    throw new Error('Failed to load static data files from /data.');
                }

                const [tournaments, participants, matches, manifest] = await Promise.all([
                    tournamentResponse.json(),
                    participantsResponse.json(),
                    matchesResponse.json(),
                    manifestResponse.ok ? manifestResponse.json() : Promise.resolve({}),
                ]);

                const data = composeCachePayloadFromFixedFiles(tournaments, participants, matches, manifest);
                renderDashboard(data);
                setStatusMessage('', 'info');
                return;
            }

            const response = await fetch(API_CACHE_URL, { cache: 'no-store' });
            if (!response.ok) {
                const payload = await response.json();
                throw new Error(payload.error || 'Failed to load local cache.');
            }
            const data = await response.json();
            renderDashboard(data);
            setStatusMessage('', 'info');
        } catch (error) {
            setStatusMessage(error.message, 'warning');
        }
    }

    // Reload the server's current JSON cache into the browser display (available to all users).
    async function updateLocalCache() {
        if (CLIENT_DATA_MODE === 'fixed') {
            setStatusMessage('Static mode is read-only. Data updates come from Lambda publishing /data/*.json.', 'info');
            return;
        }

        const button = getById('refresh-cache-btn');
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Loading...';
        }

        try {
            const response = await fetch(API_CACHE_URL, { cache: 'no-store' });
            if (!response.ok) {
                const payload = await response.json();
                throw new Error(payload.error || 'Failed to load local cache.');
            }
            const data = await response.json();
            renderDashboard(data);
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

    // Clear the browser's in-memory display (available to all users, does not touch the server file).
    function clearLocalCache() {
        cachedData = null;
        activeTournamentIds = null;
        renderTournamentSection();
        renderParticipantsTable([]);
        renderMatches([]);
        const stateFilters = getById('match-state-filters');
        if (stateFilters) stateFilters.innerHTML = '';
        const tournFilters = getById('tournament-filters');
        if (tournFilters) tournFilters.innerHTML = '';
        const cacheMeta = getById('cache-meta');
        if (cacheMeta) cacheMeta.textContent = 'Local cache has not been loaded yet.';
        setStatusMessage('Display cleared.', 'info');
    }

    // Pull fresh data from Challonge and update the server's cache file (admin / loopback only).
    async function syncFromChallonge() {
        const button = getById('sync-challonge-btn');
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Syncing...';
        }

        try {
            const response = await fetch(API_CACHE_UPDATE_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });

            if (!response.ok) {
                const payload = await response.json();
                throw new Error(payload.error || 'Failed to sync from Challonge.');
            }

            const data = await response.json();
            // Reset tournament filter so newly added tournaments are visible by default.
            activeTournamentIds = null;
            renderDashboard(data);
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

    // Initialisation

    document.addEventListener('DOMContentLoaded', () => {
        loadMatchSearchChips();
        loadMatchSearchMode();
        renderMatchSearchChips();
        syncMatchSearchModeControl();

        // Reload and Clear are available to everyone (no Challonge API calls involved).
        const refreshButton = getById('refresh-cache-btn');
        if (refreshButton) {
            if (CLIENT_DATA_MODE === 'fixed') {
                refreshButton.style.display = 'none';
            } else {
                refreshButton.addEventListener('click', updateLocalCache);
            }
        }

        const clearButton = getById('clear-cache-btn');
        if (clearButton) {
            if (CLIENT_DATA_MODE === 'fixed') {
                clearButton.style.display = 'none';
            } else {
                clearButton.addEventListener('click', clearLocalCache);
            }
        }

        // Sync from Challonge is admin-only (loopback); backend enforces this independently.
        const syncButton = getById('sync-challonge-btn');
        if (syncButton) {
            if (ADMIN_ENABLED && CLIENT_DATA_MODE !== 'fixed') {
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
                activeMatchSearchMode = 'all';
                saveMatchSearchMode();
                renderMatches(getFilteredMatches());
            });
        }

        if (matchFilterModeAny) {
            matchFilterModeAny.addEventListener('change', () => {
                if (!matchFilterModeAny.checked) return;
                activeMatchSearchMode = 'any';
                saveMatchSearchMode();
                renderMatches(getFilteredMatches());
            });
        }

        if (matchFilterClearAllButton) {
            matchFilterClearAllButton.addEventListener('click', clearAllMatchSearchChips);
        }

        loadLocalCache();
    });
})();
