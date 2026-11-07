/**
 * Search chip management (persistence, rendering, and lifecycle).
 */

import { getById, escapeHtml } from './helpers.js';
import { activeMatchSearchChips, setActiveMatchSearchChips } from './state.js';
import { renderMatches } from './renderers.js';
import { getFilteredMatches } from './filters.js';

const MATCH_SEARCH_CHIPS_STORAGE_KEY = 'mcchallonge.matchSearchChips.v1';

export function normaliseMatchSearchChip(value) {
    return String(value || '').trim().replace(/\s+/g, ' ');
}

export function saveMatchSearchChips() {
    try {
        localStorage.setItem(MATCH_SEARCH_CHIPS_STORAGE_KEY, JSON.stringify(activeMatchSearchChips));
    } catch (error) {
        console.warn('Failed to persist match search chips:', error);
    }
}

export function loadMatchSearchChips() {
    try {
        const raw = localStorage.getItem(MATCH_SEARCH_CHIPS_STORAGE_KEY);
        if (!raw) {
            setActiveMatchSearchChips([]);
            return;
        }
        const parsed = JSON.parse(raw);
        const chips = Array.isArray(parsed)
            ? parsed.map(normaliseMatchSearchChip).filter(Boolean)
            : [];
        setActiveMatchSearchChips(chips);
    } catch (error) {
        console.warn('Failed to load match search chips:', error);
        setActiveMatchSearchChips([]);
    }
}

export function renderMatchSearchChips() {
    const container = getById('match-text-filter-chips');
    if (!container) return;

    if (!activeMatchSearchChips.length) {
        container.innerHTML = '<span class="match-filter-chip-empty">No filters applied yet.</span>';
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
            const updated = window.prompt('Edit match filter', current);
            if (updated === null) {
                return;
            }

            const normalised = normaliseMatchSearchChip(updated);
            if (!normalised) {
                return;
            }

            activeMatchSearchChips[index] = normalised;
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

export function addMatchSearchChip(chipText) {
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

export function clearAllMatchSearchChips() {
    setActiveMatchSearchChips([]);
    saveMatchSearchChips();
    renderMatchSearchChips();
    renderMatches(getFilteredMatches());
}
