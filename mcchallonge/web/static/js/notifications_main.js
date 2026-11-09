const config = window.__MCC_NOTIFICATIONS_CONFIG || {};

const STORAGE_SUBSCRIPTIONS = 'mcchallonge-notification-subscriptions-v1';
const STORAGE_READ_IDS = 'mcchallonge-notification-read-v1';

function getById(id) {
    return document.getElementById(id);
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value ?? '';
    return div.innerHTML;
}

function setStatus(message, level = 'info') {
    const box = getById('status-message');
    if (!box) return;
    if (!message) {
        box.style.display = 'none';
        box.className = 'alert status-message';
        box.textContent = '';
        return;
    }
    box.style.display = 'block';
    box.className = `alert status-message alert-${level}`;
    box.textContent = message;
}

function loadSet(storageKey) {
    try {
        const raw = window.localStorage.getItem(storageKey);
        if (!raw) return new Set();
        const values = JSON.parse(raw);
        if (!Array.isArray(values)) return new Set();
        return new Set(values.map(String));
    } catch {
        return new Set();
    }
}

function saveSet(storageKey, valueSet) {
    window.localStorage.setItem(storageKey, JSON.stringify(Array.from(valueSet)));
}

function loadSubscriptions() {
    return loadSet(STORAGE_SUBSCRIPTIONS);
}

function saveSubscriptions(subscriptions) {
    saveSet(STORAGE_SUBSCRIPTIONS, subscriptions);
}

function loadReadIds() {
    return loadSet(STORAGE_READ_IDS);
}

function saveReadIds(readIds) {
    saveSet(STORAGE_READ_IDS, readIds);
}

function typeLabel(notificationType) {
    if (notificationType === 'queue_call') return 'Queue Attempt';
    if (notificationType === 'eo_summon') return 'Report to EO';
    return notificationType || 'Notification';
}

async function fetchRobotDirectory() {
    const response = await fetch(config.apiNotificationsRobotsUrl, { cache: 'no-store' });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Failed to load robots.');
    }
    const payload = await response.json();
    return Array.isArray(payload.robots) ? payload.robots : [];
}

async function fetchSubscribedNotifications(robotKeys) {
    const response = await fetch(config.apiNotificationsSubscribedUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ robot_keys: robotKeys }),
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Failed to load notifications.');
    }
    const payload = await response.json();
    return Array.isArray(payload.notifications) ? payload.notifications : [];
}

async function sendNotification(robotKey, notificationType) {
    const response = await fetch(config.apiNotificationsSendUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            robot_key: robotKey,
            type: notificationType,
        }),
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Failed to create notification.');
    }
    const payload = await response.json();
    return payload.notification;
}

async function fetchAuditNotifications() {
    const response = await fetch(config.apiNotificationsAuditUrl, { cache: 'no-store' });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'Failed to load audit notifications.');
    }
    const payload = await response.json();
    return Array.isArray(payload.notifications) ? payload.notifications : [];
}

function renderSubscriptions(robots) {
    const root = getById('subscriptions-robot-groups');
    if (!root) return;

    const subscriptions = loadSubscriptions();
    if (!robots.length) {
        root.innerHTML = '<p class="empty-state mb-0">No robots available in local cache.</p>';
        return;
    }

    const grouped = new Map();
    robots.forEach((robot) => {
        const key = robot.competition_name || 'Unspecified Competition';
        if (!grouped.has(key)) grouped.set(key, []);
        grouped.get(key).push(robot);
    });

    root.innerHTML = Array.from(grouped.entries()).map(([competitionName, group]) => `
        <div class="mb-3">
            <h6 class="fw-bold">${escapeHtml(competitionName)}</h6>
            <div class="table-responsive">
                <table class="table table-sm align-middle">
                    <thead>
                    <tr>
                        <th>Subscribe</th>
                        <th>Robot</th>
                        <th>Team</th>
                    </tr>
                    </thead>
                    <tbody>
                    ${group.map((robot) => {
                        const checked = subscriptions.has(robot.robot_key) ? 'checked' : '';
                        return `
                            <tr>
                                <td>
                                    <input type="checkbox" class="form-check-input robot-subscription-checkbox"
                                           data-robot-key="${escapeHtml(robot.robot_key)}" ${checked}>
                                </td>
                                <td>${escapeHtml(robot.bot_name || '')}</td>
                                <td>${escapeHtml(robot.team_name || '')}</td>
                            </tr>
                        `;
                    }).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `).join('');

    root.querySelectorAll('.robot-subscription-checkbox').forEach((checkbox) => {
        checkbox.addEventListener('change', () => {
            const robotKey = checkbox.dataset.robotKey;
            if (!robotKey) return;
            if (checkbox.checked) {
                subscriptions.add(robotKey);
            } else {
                subscriptions.delete(robotKey);
            }
            saveSubscriptions(subscriptions);
            setStatus('Subscriptions updated.', 'success');
            const pageMode = String(config.mode || '');
            if (pageMode === 'subscriptions') {
                // Keep summary in sync for users who navigate quickly between pages.
                renderInboxSubscriptionSummary(robots);
            }
        });
    });
}

function renderInboxSubscriptionSummary(robots) {
    const root = getById('inbox-subscriptions-summary');
    if (!root) return;

    const subscriptions = loadSubscriptions();
    if (!subscriptions.size) {
        root.innerHTML = '<p class="empty-state mb-0">You are not subscribed to any robots yet. Visit the Subscriptions page to opt in.</p>';
        return;
    }

    const byRobotKey = new Map((robots || []).map((robot) => [robot.robot_key, robot]));
    const labels = Array.from(subscriptions)
        .map((robotKey) => {
            const robot = byRobotKey.get(robotKey);
            if (!robot) return null;
            const competition = robot.competition_name || 'Unknown Competition';
            const team = robot.team_name || 'Unknown Team';
            return {
                robotKey,
                text: `${robot.bot_name} (${team}) — ${competition}`,
            };
        })
        .filter(Boolean)
        .sort((a, b) => a.text.localeCompare(b.text));

    if (!labels.length) {
        root.innerHTML = '<p class="empty-state mb-0">You have subscriptions saved, but those robots are not in the current local cache.</p>';
        return;
    }

    root.innerHTML = `
        <div class="small fw-semibold text-muted mb-2">Subscribed robots (${labels.length})</div>
        <div class="d-flex flex-wrap gap-2">
            ${labels.map((label) => `<span class="badge rounded-pill bg-primary-subtle text-primary-emphasis subscription-pill">${escapeHtml(label.text)}</span>`).join('')}
        </div>
    `;
}

function renderInbox(notifications) {
    const list = getById('inbox-list');
    if (!list) return;

    const readIds = loadReadIds();
    if (!notifications.length) {
        list.innerHTML = '<p class="empty-state mb-0">No notifications for your current subscriptions.</p>';
        return;
    }

    list.innerHTML = notifications.map((notification) => {
        const isRead = readIds.has(String(notification.id));
        const readBadge = isRead
            ? '<span class="badge bg-secondary">Read</span>'
            : '<span class="badge bg-warning text-dark">Unread</span>';
        const actionLabel = isRead ? 'Mark Unread' : 'Mark Read';
        return `
            <div class="border rounded p-3 mb-2 ${isRead ? 'notification-read' : 'notification-unread'}">
                <div class="d-flex justify-content-between align-items-start gap-2">
                    <div>
                        <div class="fw-semibold">${escapeHtml(typeLabel(notification.type))} — ${escapeHtml(notification.bot_name || '')}</div>
                        <div class="small text-muted">${escapeHtml(notification.team_name || '')} | ${escapeHtml(notification.competition_name || '')}</div>
                        <div class="small text-muted">${escapeHtml(notification.created_at || '')}</div>
                        ${notification.message ? `<div class="mt-1">${escapeHtml(notification.message)}</div>` : ''}
                    </div>
                    <div class="d-flex flex-column align-items-end gap-2">
                        ${readBadge}
                        <button type="button" class="btn btn-sm btn-outline-secondary inbox-read-toggle"
                                data-notification-id="${escapeHtml(notification.id)}">${actionLabel}</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    list.querySelectorAll('.inbox-read-toggle').forEach((button) => {
        button.addEventListener('click', () => {
            const notificationId = String(button.dataset.notificationId || '');
            if (!notificationId) return;
            const nextReadIds = loadReadIds();
            if (nextReadIds.has(notificationId)) {
                nextReadIds.delete(notificationId);
            } else {
                nextReadIds.add(notificationId);
            }
            saveReadIds(nextReadIds);
            renderInbox(notifications);
        });
    });
}

function renderAdminRobotGroups(robots) {
    const root = getById('admin-robot-groups');
    if (!root) return;

    if (!robots.length) {
        root.innerHTML = '<p class="empty-state mb-0">No robots available in local cache.</p>';
        return;
    }

    const grouped = new Map();
    robots.forEach((robot) => {
        const key = robot.competition_name || 'Unspecified Competition';
        if (!grouped.has(key)) grouped.set(key, []);
        grouped.get(key).push(robot);
    });

    root.innerHTML = Array.from(grouped.entries()).map(([competitionName, group]) => `
        <div class="mb-3">
            <h6 class="fw-bold">${escapeHtml(competitionName)}</h6>
            <div class="table-responsive">
                <table class="table table-sm align-middle">
                    <thead>
                    <tr>
                        <th>Robot</th>
                        <th>Team</th>
                        <th>Actions</th>
                    </tr>
                    </thead>
                    <tbody>
                    ${group.map((robot) => `
                        <tr>
                            <td>${escapeHtml(robot.bot_name || '')}</td>
                            <td>${escapeHtml(robot.team_name || '')}</td>
                            <td class="d-flex flex-wrap gap-2">
                                <button type="button" class="btn btn-sm btn-outline-warning admin-notify-btn"
                                        data-robot-key="${escapeHtml(robot.robot_key)}"
                                        data-type="queue_call">Notify Queue Attempt</button>
                                <button type="button" class="btn btn-sm btn-outline-danger admin-notify-btn"
                                        data-robot-key="${escapeHtml(robot.robot_key)}"
                                        data-type="eo_summon">Notify Report to EO</button>
                            </td>
                        </tr>
                    `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `).join('');

    root.querySelectorAll('.admin-notify-btn').forEach((button) => {
        button.addEventListener('click', async () => {
            const robotKey = String(button.dataset.robotKey || '');
            const notificationType = String(button.dataset.type || '');
            if (!robotKey || !notificationType) return;

            const original = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Sending...';

            try {
                await sendNotification(robotKey, notificationType);
                setStatus('Notification sent.', 'success');
                await loadAudit();
            } catch (error) {
                setStatus(error.message || 'Failed to send notification.', 'danger');
            } finally {
                button.disabled = false;
                button.innerHTML = original;
            }
        });
    });
}

async function loadAudit() {
    const tableBody = getById('audit-table-body');
    if (!tableBody) return;

    try {
        const notifications = await fetchAuditNotifications();
        if (!notifications.length) {
            tableBody.innerHTML = '<tr><td colspan="6" class="empty-state">No notifications sent yet.</td></tr>';
            return;
        }
        tableBody.innerHTML = notifications.map((notification) => `
            <tr>
                <td>${escapeHtml(notification.created_at || '')}</td>
                <td>${escapeHtml(typeLabel(notification.type))}</td>
                <td>${escapeHtml(notification.bot_name || '')}</td>
                <td>${escapeHtml(notification.team_name || '')}</td>
                <td>${escapeHtml(notification.competition_name || '')}</td>
                <td>${escapeHtml(notification.message || '')}</td>
            </tr>
        `).join('');
    } catch (error) {
        setStatus(error.message || 'Failed to load audit notifications.', 'danger');
    }
}

async function initializeSubscriptionsPage() {
    try {
        const robots = await fetchRobotDirectory();
        renderSubscriptions(robots);
    } catch (error) {
        setStatus(error.message || 'Failed to load subscriptions.', 'danger');
    }
}

function setInboxLastFetchedNow() {
    const label = getById('inbox-last-fetched');
    if (!label) return;
    label.textContent = `Last fetched: ${new Date().toLocaleTimeString()}`;
}

async function loadInbox(robots) {
    const subscriptions = Array.from(loadSubscriptions());
    const hasRobotsSnapshot = Array.isArray(robots);
    if (!subscriptions.length) {
        if (hasRobotsSnapshot) {
            renderInboxSubscriptionSummary(robots);
        }
        renderInbox([]);
        setStatus('Subscribe to one or more robots to receive notifications.', 'info');
        setInboxLastFetchedNow();
        return;
    }

    try {
        if (hasRobotsSnapshot) {
            renderInboxSubscriptionSummary(robots);
        }
        const notifications = await fetchSubscribedNotifications(subscriptions);
        renderInbox(notifications);
        setStatus('', 'info');
        setInboxLastFetchedNow();
    } catch (error) {
        setStatus(error.message || 'Failed to load inbox notifications.', 'danger');
    }
}

async function refreshInboxData() {
    try {
        const robots = await fetchRobotDirectory();
        await loadInbox(robots);
    } catch {
        const root = getById('inbox-subscriptions-summary');
        if (root) {
            root.innerHTML = '<p class="empty-state mb-0">Unable to load subscribed robot details from cache right now.</p>';
        }
        await loadInbox();
    }
}

function initializeInboxPage() {
    const loadInboxWithGuard = () => refreshInboxData();
    const refreshButton = getById('refresh-inbox');
    if (refreshButton) {
        refreshButton.addEventListener('click', loadInboxWithGuard);
    }
    loadInboxWithGuard();
    window.setInterval(loadInboxWithGuard, 60000);
}

async function initializeAdminPage() {
    try {
        const robots = await fetchRobotDirectory();
        renderAdminRobotGroups(robots);
    } catch (error) {
        setStatus(error.message || 'Failed to load admin robot directory.', 'danger');
    }

    const refreshAuditButton = getById('refresh-audit');
    if (refreshAuditButton) {
        refreshAuditButton.addEventListener('click', () => loadAudit());
    }
    loadAudit();
}

document.addEventListener('DOMContentLoaded', () => {
    if (config.mode === 'subscriptions') {
        initializeSubscriptionsPage();
        return;
    }
    if (config.mode === 'inbox') {
        initializeInboxPage();
        return;
    }
    if (config.mode === 'admin') {
        initializeAdminPage();
    }
});
