/**
 * Selection Management - Shift/Ctrl multi-select like Google Sheets
 */

// Auto-save before leaving (silently)
window.addEventListener('beforeunload', async (e) => {
    if (typeof saveProgress === 'function') {
        // Trigger save silently (async, may not complete before close)
        fetch('/api/save_progress', { method: 'POST', keepalive: true });
    }
});
