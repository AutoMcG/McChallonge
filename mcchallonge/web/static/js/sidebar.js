const STORAGE_KEY = 'mcchallonge-sidebar-compact-v1';

function applyCompactState(compact) {
    const shell = document.querySelector('.app-shell');
    if (!shell) return;
    shell.classList.toggle('sidebar-compact', compact);
    const toggle = document.getElementById('sidebar-collapse-toggle');
    if (toggle) {
        const title = compact ? 'Expand sidebar' : 'Collapse sidebar';
        toggle.setAttribute('aria-label', title);
        toggle.setAttribute('title', title);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    let compact = false;
    try {
        compact = window.localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
        compact = false;
    }
    applyCompactState(compact);

    const toggle = document.getElementById('sidebar-collapse-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', () => {
        compact = !compact;
        applyCompactState(compact);
        try {
            window.localStorage.setItem(STORAGE_KEY, compact ? 'true' : 'false');
        } catch {
            // Ignore storage failures and keep in-memory behavior.
        }
    });
});
