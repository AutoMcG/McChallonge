/**
 * Rendering functions for dashboard sections.
 */

import { getById, escapeHtml, escapeAttribute } from './helpers.js';
import { cachedData, activeTournamentIds, config } from './state.js';
import { getAllTournamentEntries, getAllParticipantMap } from './data.js';
import { getRoundMetadata, getBracketForMatch } from './round-metadata.js';
import { getFilteredMatches, getFilteredParticipants } from './filters.js';

function renderParticipantThumb(imgUrl, altText, extraClass = '') {
    if (!imgUrl) {
        return '<span class="bot-thumb bot-thumb-placeholder" aria-hidden="true"><i class="fas fa-robot"></i></span>';
    }
    return `<img class="bot-thumb ${extraClass}" src="${escapeAttribute(imgUrl)}" alt="${escapeAttribute(altText)}" loading="lazy">`;
}

export function renderTournamentSection() {
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
            name.textContent = tournament.name || 'Tournament Name';
        } else {
            name.textContent = `${selectedEntries.length || allEntries.length} Tournament(s)`;
        }
    }

    if (id) {
        id.textContent = single
            ? `Tournament ID: ${tournament.id ?? 'Unknown'}`
            : `${selectedEntries.length || allEntries.length} tournament(s) loaded`;
    }

    if (status) {
        if (single) {
            status.classList.remove('status-underway', 'status-completed');
            status.classList.add(tournament.state === 'completed' ? 'status-completed' : 'status-underway');
            status.textContent = tournament.state ? tournament.state.charAt(0).toUpperCase() + tournament.state.slice(1) : 'Unknown';
        } else {
            status.textContent = 'Multi-Tournament';
        }
    }

    if (cacheMeta) {
        const times = allEntries.map(([, e]) => e.meta?.cached_at).filter(Boolean);
        const latestTime = times.sort().pop();
        cacheMeta.textContent = latestTime
            ? `Local cache updated at ${latestTime}`
            : 'Local cache has not been loaded yet.';
    }

    // Event Details panel
    const detailsContainer = getById('event-details-container');
    if (detailsContainer) {
        if (selectedEntries.length === 0) {
            detailsContainer.innerHTML = '<p class="empty-state">No event data loaded.</p>';
        } else {
            const multi = selectedEntries.length > 1;
            detailsContainer.innerHTML = selectedEntries.map(([, entry], idx) => {
                const t = entry.tournament || {};
                const slug = t.url || '';
                const matchCount = (entry.matches || []).length;
                const participantCount = (entry.participants || []).length;
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
                    <p><strong>Matches:</strong> ${matchCount}</p>
                    <p><strong>Participants:</strong> ${participantCount}</p>
                `;
            }).join('');
        }
    }
}

export function renderParticipantsTable(participants) {
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
            const participantName = participant.name || 'Unknown';
            return `
                <tr>
                    <td>${index + 1}</td>
                    <td>
                        <span class="participant-name-cell">
                            ${renderParticipantThumb(participant.img, participantName)}
                            <span>${escapeHtml(participantName)}</span>
                        </span>
                    </td>
                    ${tournamentCell}
                    <td>${wins}</td>
                    <td>${losses}</td>
                    <td>${winRate}</td>
                </tr>
            `;
        })
        .join('');
}

export function renderMatches(matches) {
    const container = getById('matches-container');
    if (!container) return;

    const multiTournament = getAllTournamentEntries().length > 1;

    if (!matches || matches.length === 0) {
        container.innerHTML = '<div class="empty-state">No matches in local cache.</div>';
        return;
    }

    const participantsById = getAllParticipantMap();
    const getSuggestedOrder = (match) => {
        const parsed = Number(match.suggested_play_order);
        return Number.isNaN(parsed) ? Number.POSITIVE_INFINITY : parsed;
    };

    const getRoundSort = (match) => {
        const parsed = Number(match.round);
        return Number.isNaN(parsed) ? Number.POSITIVE_INFINITY : Math.abs(parsed);
    };

    const getBracketRank = (match) => {
        const bracket = getBracketForMatch(match);
        if (bracket === 'upper') return 0;
        if (bracket === 'lower') return 1;
        return 2;
    };

    const groups = new Map();
    matches.forEach(match => {
        const bracket = getBracketForMatch(match);
        const roundSort = getRoundSort(match);
        const roundLabel = Number.isFinite(roundSort) ? `Round ${roundSort}` : 'No Round';
        const bracketLabel = bracket === 'upper' ? 'Upper' : bracket === 'lower' ? 'Lower' : 'Unassigned';
        const tournamentName = match._tournament_name || 'Unknown Tournament';
        const key = `${bracket || 'none'}|${Number.isFinite(roundSort) ? roundSort : 'none'}|${match._tournament_key || tournamentName}`;

        if (!groups.has(key)) {
            groups.set(key, {
                bracketRank: getBracketRank(match),
                roundSort,
                tournamentName,
                title: `${bracketLabel} ${roundLabel} - ${tournamentName}`,
                matches: [],
            });
        }

        groups.get(key).matches.push(match);
    });

    const sortedGroups = Array.from(groups.values()).sort((a, b) => {
        if (a.bracketRank !== b.bracketRank) return a.bracketRank - b.bracketRank;
        if (a.roundSort !== b.roundSort) return a.roundSort - b.roundSort;
        return a.tournamentName.localeCompare(b.tournamentName);
    });

    const tournamentToneByName = new Map(
        getAllTournamentEntries()
            .map(([key, entry]) => entry.tournament?.name || key)
            .sort((a, b) => a.localeCompare(b))
            .map((name, index) => [name, index % 6])
    );

    const renderedGroups = sortedGroups.map(group => {
        const renderedMatches = [...group.matches]
            .sort((a, b) => {
                const orderDiff = getSuggestedOrder(a) - getSuggestedOrder(b);
                if (orderDiff !== 0) return orderDiff;
                return Number(a.id || 0) - Number(b.id || 0);
            })
            .map((match) => {
                const player1Data = participantsById.get(match.player1_id) || {};
                const player2Data = participantsById.get(match.player2_id) || {};
                const player1 = player1Data.name || 'Player 1';
                const player2 = player2Data.name || 'Player 2';
                const roundMeta = getRoundMetadata(match.round);
                const isPlayer1Winner = match.winner_id && match.winner_id === match.player1_id;
                const isPlayer2Winner = match.winner_id && match.winner_id === match.player2_id;
                const state = (match.state || 'pending').toLowerCase();
                const isUnderway = Boolean(match.underway_at);
                const canSetUnderway = config.adminEnabled
                    && config.showOnly === 'queue'
                    && state !== 'complete'
                    && !isUnderway;
                const canClearUnderway = config.adminEnabled
                    && config.showOnly === 'queue'
                    && isUnderway;
                const tournamentBadge = multiTournament
                    ? `<span class="tournament-badge">${escapeHtml(match._tournament_name || '')}</span>`
                    : '';
                const tournamentKey = String(match._tournament_key || match.tournament_id || '');
                const underwayButton = canSetUnderway
                    ? `<button type="button" class="btn btn-sm btn-outline-warning match-underway-btn"
                         data-tournament-key="${escapeAttribute(tournamentKey)}"
                         data-match-id="${escapeAttribute(match.id)}">
                        <i class="fas fa-play me-1"></i>Set Underway
                    </button>`
                    : '';
                const clearUnderwayButton = canClearUnderway
                    ? `<button type="button" class="btn btn-sm btn-outline-secondary match-clear-underway-btn"
                         data-tournament-key="${escapeAttribute(tournamentKey)}"
                         data-match-id="${escapeAttribute(match.id)}">
                        <i class="fas fa-times me-1"></i>Clear Underway
                    </button>`
                    : '';
                return `
                    <div class="match">
                        <div class="players">
                            <div class="player ${isPlayer1Winner ? 'winner' : ''}">
                                ${renderParticipantThumb(player1Data.img, player1, 'bot-thumb-sm')}
                                <span>${escapeHtml(player1)}</span>
                            </div>
                            <div class="vs">VS</div>
                            <div class="player ${isPlayer2Winner ? 'winner' : ''}">
                                ${renderParticipantThumb(player2Data.img, player2, 'bot-thumb-sm')}
                                <span>${escapeHtml(player2)}</span>
                            </div>
                        </div>
                        <div class="match-info">
                            ${match.round != null && String(match.round).trim() !== '' ? `<span class="round">${escapeHtml(roundMeta.label)}</span>` : ''}
                            <span class="state ${state === 'complete' ? 'state-complete' : 'state-pending'}">
                                ${escapeHtml(state.charAt(0).toUpperCase() + state.slice(1))}
                            </span>
                            ${match.completed_at ? `<span class="date">${escapeHtml(match.completed_at)}</span>` : ''}
                            ${tournamentBadge}
                            ${underwayButton}
                            ${clearUnderwayButton}
                        </div>
                    </div>
                `;
            })
            .join('');

        const tone = tournamentToneByName.get(group.tournamentName) ?? 0;

        return `
            <div class="mb-3 tournament-group tournament-tone-${tone}">
                <div class="small text-uppercase text-muted fw-semibold px-2 mb-2">${escapeHtml(group.title)}</div>
                ${renderedMatches}
            </div>
        `;
    });

    container.innerHTML = renderedGroups.join('');
}
