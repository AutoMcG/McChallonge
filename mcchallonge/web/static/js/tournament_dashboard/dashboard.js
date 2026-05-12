/**
 * Dashboard orchestration - main rendering controller.
 */

import { setCachedData, setActiveTournamentIds, activeTournamentIds } from './state.js';
import { renderTournamentSection, renderParticipantsTable, renderMatches } from './renderers.js';
import { buildBracketFilters, buildMatchStateFilters, buildTournamentFilters } from './builders.js';
import { getFilteredMatches, getFilteredParticipants } from './filters.js';
import { getAllTournamentEntries, getAllMatches } from './data.js';

export function renderDashboard(data) {
    setCachedData(data);
    if (activeTournamentIds === null) {
        setActiveTournamentIds(new Set(Object.keys(data.tournaments || {})));
    }
    const allMatches = getAllMatches();
    renderTournamentSection();
    buildTournamentFilters();
    buildBracketFilters(allMatches);
    buildMatchStateFilters(allMatches);
    renderParticipantsTable(getFilteredParticipants());
    renderMatches(getFilteredMatches());
}
