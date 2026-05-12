/**
 * Shared dashboard lifecycle event bus.
 */

export const DASHBOARD_EVENT = {
    DATA_LOADED: 'dashboard:data-loaded',
    DATA_CLEARED: 'dashboard:data-cleared',
    STATUS: 'dashboard:status',
    ACTION_STARTED: 'dashboard:action-started',
    ACTION_FINISHED: 'dashboard:action-finished',
};

export const dashboardEvents = new EventTarget();
