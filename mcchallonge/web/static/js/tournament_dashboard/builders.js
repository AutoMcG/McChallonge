/**
 * Filter UI builders.
 */

import { getById, escapeHtml } from './helpers.js';
import { activeBrackets, activeMatchStates, activeTournamentIds, setActiveBrackets, setActiveMatchStates, setActiveTournamentIds } from './state.js';
import { getAllTournamentEntries, getAllMatches } from './data.js';
import { renderMatches } from './renderers.js';
import { renderParticipantsTable } from './renderers.js';
import { renderTournamentSection } from './renderers.js';
import { getFilteredMatches, getFilteredParticipants } from './filters.js';

export function buildBracketFilters(matches) {
    const container = getById('match-bracket-filters');
    if (!container) return;

    const brackets = [
        { value: 'upper', label: 'Upper Bracket' },
        { value: 'lower', label: 'Lower Bracket' },
    ];

    container.innerHTML = brackets.map(bracket => {
        const checked = activeBrackets.has(bracket.value) ? 'checked' : '';
        return `
            <div class="form-check form-check-inline mb-0">
                <input class="form-check-input match-bracket-checkbox" type="checkbox"
                       id="filter-bracket-${bracket.value}" value="${bracket.value}" ${checked}>
                <label class="form-check-label" for="filter-bracket-${bracket.value}">${bracket.label}</label>
            </div>
        `;
    }).join('');

    container.querySelectorAll('.match-bracket-checkbox').forEach(cb => {
        cb.addEventListener('change', e => {
            if (e.target.checked) {
                activeBrackets.add(e.target.value);
            } else {
                activeBrackets.delete(e.target.value);
            }
            renderMatches(getFilteredMatches());
        });
    });
}

export function buildMatchStateFilters(matches) {
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

export function buildTournamentFilters() {
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
