/**
 * Undo/Redo System - Persistent across sessions
 */

async function undo() {
    try {
        const response = await fetch('/api/undo', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            // Just reload - no annoying notifications
            location.reload();
        }
    } catch (error) {
        console.error('Undo error:', error);
    }
}

async function redo() {
    try {
        const response = await fetch('/api/redo', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            location.reload();
        }
    } catch (error) {
        console.error('Redo error:', error);
    }
}
