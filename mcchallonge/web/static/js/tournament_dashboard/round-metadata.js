/**
 * Round metadata and bracket determination.
 */

export function getRoundMetadata(roundValue) {
    if (roundValue === null || roundValue === undefined || roundValue === '') {
        return {
            label: 'No Round',
            aliases: ['no round', 'round none', 'unassigned round'],
        };
    }

    const raw = String(roundValue).trim();
    const cleaned = raw
        .replace(/\s+/g, ' ')
        .trim();

    if (cleaned) {
        const roundNumber = Number(cleaned);
        if (!Number.isNaN(roundNumber)) {
            // Preserve negative round numbers (lower bracket)
            const isBracketLabel = roundNumber < 0 ? 'Lower' : roundNumber > 0 ? 'Upper' : '';
            const bracketPrefix = isBracketLabel ? `${isBracketLabel} ` : '';
            return {
                label: `${bracketPrefix}Round ${Math.abs(roundNumber)}`,
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

export function getBracketForMatch(match) {
    const round = match.round;
    if (round === null || round === undefined || round === '') {
        return null;
    }
    const roundNum = Number(round);
    if (Number.isNaN(roundNum)) {
        return null;
    }
    return roundNum > 0 ? 'upper' : roundNum < 0 ? 'lower' : null;
}
