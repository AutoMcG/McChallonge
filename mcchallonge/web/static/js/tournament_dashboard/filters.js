/**
 * Filtering logic for matches and participants.
 */

import { activeMatchSearchChips, activeMatchSearchMode, activeTournamentIds, activeMatchStates, activeBrackets } from './state.js';
import { getAllMatches, getAllParticipants, getAllParticipantMap } from './data.js';
import { getRoundMetadata, getBracketForMatch } from './round-metadata.js';
import { getById } from './helpers.js';

export function doesMatchPassSearchChips(match, participantsById) {
    if (!activeMatchSearchChips.length) {
        return true;
    }

    const haystack = getMatchSearchHaystack(match, participantsById);
    if (activeMatchSearchMode === 'any') {
        return activeMatchSearchChips.some(chip => haystack.includes(chip.toLowerCase()));
    }
    return activeMatchSearchChips.every(chip => haystack.includes(chip.toLowerCase()));
}

export function getMatchSearchHaystack(match, participantsById) {
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

export function getFilteredParticipants() {
    const all = getAllParticipants();
    const query = (getById('participant-name-filter')?.value || '').trim().toLowerCase();
    return all.filter(p => {
        const matchesTournament = !activeTournamentIds || activeTournamentIds.has(p._tournament_key);
        const matchesName = !query || (p.name || '').toLowerCase().includes(query);
        return matchesTournament && matchesName;
    });
}

export function getFilteredMatches() {
    const participantsById = getAllParticipantMap();
    return getAllMatches().filter(m => {
        const matchesTournament = !activeTournamentIds || activeTournamentIds.has(m._tournament_key);
        const matchesState = activeMatchStates.has((m.state || '').toLowerCase());
        const matchesText = doesMatchPassSearchChips(m, participantsById);
        const bracket = getBracketForMatch(m);
        const matchesBracket = !bracket || activeBrackets.has(bracket);
        return matchesTournament && matchesState && matchesText && matchesBracket;
    });
}
