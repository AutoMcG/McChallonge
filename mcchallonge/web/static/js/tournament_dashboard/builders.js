/**
 * Filter UI builders.
 */

import { getById, escapeHtml } from './helpers.js';
import { activeBrackets, activeMatchStates, activeTournamentIds } from './state.js';
import { getAllTournamentEntries } from './data.js';
import { renderMatches } from './renderers.js';
import { renderParticipantsTable } from './renderers.js';
import { renderTournamentSection } from './renderers.js';
import { getFilteredMatches, getFilteredParticipants } from './filters.js';

function renderCheckboxFilters(container, rows, inputClass, onChange) {
    container.innerHTML = rows.map(row => {
        const checked = row.checked ? 'checked' : '';
        return `
            <div class="form-check form-check-inline mb-0">
                <input class="form-check-input ${inputClass}" type="checkbox"
                       id="${row.id}" value="${row.value}" ${checked}>
                <label class="form-check-label" for="${row.id}">${row.label}</label>
            </div>
        `;
    }).join('');

    container.querySelectorAll(`.${inputClass}`).forEach(cb => {
        cb.addEventListener('change', onChange);
    });
}

export function buildBracketFilters() {
    const container = getById('match-bracket-filters');
    if (!container) return;

    const brackets = [
        { value: 'upper', label: 'Upper Bracket' },
        { value: 'lower', label: 'Lower Bracket' },
    ];

    const rows = brackets.map(bracket => ({
        id: `filter-bracket-${bracket.value}`,
        value: bracket.value,
        label: bracket.label,
        checked: activeBrackets.has(bracket.value),
    }));

    renderCheckboxFilters(container, rows, 'match-bracket-checkbox', e => {
        if (e.target.checked) {
            activeBrackets.add(e.target.value);
        } else {
            activeBrackets.delete(e.target.value);
        }
        renderMatches(getFilteredMatches());
    });
}

export function buildMatchStateFilters(matches) {
    const container = getById('match-state-filters');
    if (!container) return;

    const states = [...new Set((matches || []).map(m => (m.state || 'pending').toLowerCase()))].sort();

    const rows = states.map(state => ({
        id: `filter-state-${escapeHtml(state)}`,
        value: escapeHtml(state),
        label: escapeHtml(state.charAt(0).toUpperCase() + state.slice(1)),
        checked: activeMatchStates.has(state),
    }));

    renderCheckboxFilters(container, rows, 'match-state-checkbox', e => {
        if (e.target.checked) {
            activeMatchStates.add(e.target.value);
        } else {
            activeMatchStates.delete(e.target.value);
        }
        renderMatches(getFilteredMatches());
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

    const rows = entries.map(([key, entry]) => {
        const name = entry.tournament?.name || key;
        return {
            id: `filter-tournament-${escapeHtml(key)}`,
            value: escapeHtml(key),
            label: escapeHtml(name),
            checked: !activeTournamentIds || activeTournamentIds.has(key),
        };
    });

    renderCheckboxFilters(container, rows, 'tournament-filter-checkbox', e => {
        if (e.target.checked) {
            activeTournamentIds.add(e.target.value);
        } else {
            activeTournamentIds.delete(e.target.value);
        }
        renderTournamentSection();
        renderParticipantsTable(getFilteredParticipants());
        renderMatches(getFilteredMatches());
    });
}
