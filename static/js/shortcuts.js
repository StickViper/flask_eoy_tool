/**
 * Keyboard Shortcuts - All the shortcuts you requested
 */

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('keydown', (e) => {
        // Ctrl+S - Save progress
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (typeof saveProgress === 'function') {
                saveProgress();
            }
        }

        // Ctrl+A - Select all
        if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            if (typeof selectAll === 'function') {
                selectAll();
            }
        }

        // Ctrl+D - Deselect all
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            if (typeof clearSelection === 'function') {
                clearSelection();
            }
        }

        // Ctrl+Z - Undo
        if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            if (typeof undo === 'function') {
                undo();
            }
        }

        // Ctrl+Shift+Z or Ctrl+Y - Redo
        if (((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') ||
            ((e.ctrlKey || e.metaKey) && e.key === 'y')) {
            e.preventDefault();
            if (typeof redo === 'function') {
                redo();
            }
        }

        // Escape - Clear selection / close modals
        if (e.key === 'Escape') {
            if (typeof clearSelection === 'function') {
                clearSelection();
            }
        }

        // Delete - Delete selected rows
        if (e.key === 'Delete') {
            if (typeof deleteSelected === 'function') {
                deleteSelected();
            }
        }

        // Ctrl+F - Search (TODO: implement search)
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            // TODO: Open search modal
        }

        // Ctrl+E - Export to CSV
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            // TODO: Export current category
        }

        // Ctrl+G - Google search selected
        if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
            e.preventDefault();
            if (typeof googleSearchSelected === 'function') {
                googleSearchSelected();
            }
        }
    });
});

// Prevent default browser back button behavior
// Instead, use back/forward for sidebar navigation history
window.addEventListener('popstate', (e) => {
    // Browser back/forward will navigate between categories naturally
    // No special handling needed
});
