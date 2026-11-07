/**
 * Data access and aggregation functions.
 */

import { cachedData } from './state.js';

export function getAllTournamentEntries() {
    return Object.entries(cachedData?.tournaments || {});
}

export function getAllParticipants() {
    return getAllTournamentEntries().flatMap(([key, entry]) => {
        const tName = entry.tournament?.name || key;
        return (entry.participants || []).map(p => ({
            ...p, _tournament_key: key, _tournament_name: tName,
        }));
    });
}

export function getAllMatches() {
    return getAllTournamentEntries().flatMap(([key, entry]) => {
        const tName = entry.tournament?.name || key;
        return (entry.matches || []).map(m => ({
            ...m, _tournament_key: key, _tournament_name: tName,
        }));
    });
}

export function getAllParticipantMap() {
    const map = new Map();
    getAllTournamentEntries().forEach(([, entry]) => {
        (entry.participants || []).forEach(p => map.set(p.id, p));
    });
    return map;
}
