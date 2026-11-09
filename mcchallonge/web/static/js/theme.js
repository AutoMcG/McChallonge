const THEME_STORAGE_KEY = 'mcchallonge-theme-v1';
const DARK_THEME = 'dark';
const LIGHT_THEME = 'light';

function preferredTheme() {
    try {
        const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
        if (stored === DARK_THEME || stored === LIGHT_THEME) {
            return stored;
        }
    } catch {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
            ? DARK_THEME
            : LIGHT_THEME;
    }

    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? DARK_THEME
        : LIGHT_THEME;
}

function applyTheme(theme) {
    const body = document.body;
    if (!body) return;
    body.classList.toggle('theme-dark', theme === DARK_THEME);
}

function persistTheme(theme) {
    try {
        window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
        // Keep runtime-only behavior when storage is blocked.
    }
}

function initializeThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    const activeTheme = preferredTheme();
    applyTheme(activeTheme);
    toggle.checked = activeTheme === DARK_THEME;

    toggle.addEventListener('change', () => {
        const nextTheme = toggle.checked ? DARK_THEME : LIGHT_THEME;
        applyTheme(nextTheme);
        persistTheme(nextTheme);
    });
}

function initializeTheme() {
    applyTheme(preferredTheme());
    initializeThemeToggle();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTheme);
} else {
    initializeTheme();
}
