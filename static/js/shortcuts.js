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
            if (document.getElementById('searchModal') && document.getElementById('searchModal').style.display === 'block') {
                closeSearchModal();
            } else if (typeof clearSelection === 'function') {
                clearSelection();
            }
        }

        // Delete - Delete selected rows
        if (e.key === 'Delete') {
            if (typeof deleteSelected === 'function') {
                deleteSelected();
            }
        }

        // Ctrl+F - Search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            showSearchModal();
        }

        // Ctrl+E - Export to CSV
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            exportCategory();
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

// Search Modal Functions
function showSearchModal() {
    let modal = document.getElementById('searchModal');
    if (!modal) {
        console.error('Search modal not found');
        return;
    }
    modal.style.display = 'block';
    document.getElementById('searchInput').focus();
}

function closeSearchModal() {
    let modal = document.getElementById('searchModal');
    if (modal) {
        modal.style.display = 'none';
        // Do NOT reset search filter or input
        // This allows users to see the filtered results after closing the modal
    }
}

function performSearch(query) {
    const rows = document.querySelectorAll('.data-row');
    const lowerQuery = query.toLowerCase();

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const rowNum = row.dataset.rowNum;
        const detailRow = document.getElementById(`detail-${rowNum}`);

        if (text.includes(lowerQuery)) {
            row.style.display = '';
            // Show detail row only if it was explicitly expanded
            if (detailRow && detailRow.dataset.wasVisible === 'true') {
                detailRow.style.display = 'table-row';
            }
        } else {
            row.style.display = 'none';
            // Always hide detail row when parent is hidden
            if (detailRow) {
                // Remember if it was visible before hiding
                if (detailRow.style.display === 'table-row') {
                    detailRow.dataset.wasVisible = 'true';
                }
                detailRow.style.display = 'none';
            }
        }
    });
}

// Export Function
function exportCategory() {
    const allRows = document.querySelectorAll('.data-row');
    // Only export visible rows (respect search filter)
    const rows = Array.from(allRows).filter(row => row.style.display !== 'none');

    if (rows.length === 0) {
        alert('No data to export');
        return;
    }

    let csvContent = "data:text/csv;charset=utf-8,";

    // Headers
    const headers = ["Row", "Practice", "Phone", "Address", "City", "State", "QTY 2025", "Status", "Notes"];
    csvContent += headers.join(",") + "\r\n";

    // Rows
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        // Skip checkbox (0) and expand icon (1)
        const rowData = [
            cells[2].textContent.trim(), // Row
            `"${cells[3].textContent.trim().replace(/"/g, '""')}"`, // Practice
            `"${cells[4].textContent.trim()}"`, // Phone
            `"${cells[5].textContent.trim().replace(/"/g, '""')}"`, // Address
            `"${cells[6].textContent.trim()}"`, // City
            `"${cells[7].textContent.trim()}"`, // State
            `"${cells[8].textContent.trim()}"`, // QTY
            `"${cells[9].textContent.trim()}"`, // Status
            `"${cells[10].textContent.trim().replace(/"/g, '""')}"` // Notes
        ];
        csvContent += rowData.join(",") + "\r\n";
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    const categoryName = document.querySelector('.category-title h2')?.textContent.trim() || 'export';
    link.setAttribute("download", `${categoryName}_export.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Prevent default browser back button behavior
// Instead, use back/forward for sidebar navigation history
window.addEventListener('popstate', (e) => {
    // Browser back/forward will navigate between categories naturally
    // No special handling needed
});
