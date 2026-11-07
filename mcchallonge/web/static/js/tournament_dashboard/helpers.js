/**
 * Utility helper functions.
 */

export function getById(id) {
    return document.getElementById(id);
}

export function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

export function escapeAttribute(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

export function setStatusMessage(message, level) {
    const status = getById('status-message');
    if (!status) return;
    if (!message) {
        status.style.display = 'none';
        status.className = 'alert status-message';
        status.textContent = '';
        return;
    }
    status.style.display = 'block';
    status.className = `alert status-message alert-${level}`;
    status.textContent = message;
}
