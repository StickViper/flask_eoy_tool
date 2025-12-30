/**
 * Category Page - Main functionality
 * Extracted from category.html for better maintainability
 */

// =============================================================================
// SELECTION STATE & CORE VARIABLES
// =============================================================================

let selectedRows = new Set();
let lastSelectedRow = null;
let currentNoteChunkContext = null;
let currentEditingCell = null;
let sortDirection = {};
let isActionInProgress = false;  // Prevent double-clicks

// Merge/Network modal state
let mergeGroupRows = [];
let selectedSurvivor = null;
let networkGroupRows = [];

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Escape HTML special characters to prevent XSS attacks
 */
function escapeHtml(text) {
    if (text == null) return '';
    const str = String(text);
    const htmlEscapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, char => htmlEscapes[char]);
}
let selectedNetworkRows = new Set();

// Status options for dropdown
const STATUS_OPTIONS = [
    '',
    'Successful Order',
    'Voicemail/No Answer',
    'Requested Email',
    'Potentially Invalid',
    'Not interested'
];

// Field to column index mapping
const FIELD_MAP = {
    'practice': 3,
    'phone': 4,
    'address': 5,
    'city': 6,
    'state': 7,
    'qty_2025': 8,
    'status': 9,
    'notes': 10
};

// =============================================================================
// DETAIL ROW TOGGLE
// =============================================================================

function toggleDetailRow(rowNum) {
    const detailRow = document.getElementById(`detail-${rowNum}`);
    const expandIcon = document.getElementById(`expand-${rowNum}`);

    if (detailRow.style.display === 'none') {
        detailRow.style.display = 'table-row';
        if (expandIcon) expandIcon.textContent = '\u25BC';
    } else {
        detailRow.style.display = 'none';
        if (expandIcon) expandIcon.textContent = '\u25B6';
    }
}

function expandAllDetails() {
    document.querySelectorAll('.detail-row').forEach(row => {
        row.style.display = 'table-row';
    });
    document.querySelectorAll('.expand-icon').forEach(icon => {
        icon.textContent = '\u25BC';
    });
}

function collapseAllDetails() {
    document.querySelectorAll('.detail-row').forEach(row => {
        row.style.display = 'none';
    });
    document.querySelectorAll('.expand-icon').forEach(icon => {
        icon.textContent = '\u25B6';
    });
}

// =============================================================================
// ROW SELECTION
// =============================================================================

function handleRowClick(event, rowElement) {
    const rowNum = rowElement.dataset.rowNum;
    const checkbox = rowElement.querySelector('.row-checkbox');

    if (event.shiftKey && lastSelectedRow) {
        // Shift-click: toggle range from last selected row
        const allRows = Array.from(document.querySelectorAll('.data-row'));
        const startIdx = allRows.findIndex(r => r.dataset.rowNum === lastSelectedRow);
        const endIdx = allRows.findIndex(r => r.dataset.rowNum === rowNum);
        const [min, max] = [Math.min(startIdx, endIdx), Math.max(startIdx, endIdx)];
        const shouldDeselect = selectedRows.has(rowNum);

        for (let i = min; i <= max; i++) {
            const row = allRows[i];
            const rowCheckbox = row.querySelector('.row-checkbox');
            if (shouldDeselect) {
                row.classList.remove('selected');
                rowCheckbox.checked = false;
                selectedRows.delete(row.dataset.rowNum);
            } else {
                row.classList.add('selected');
                rowCheckbox.checked = true;
                selectedRows.add(row.dataset.rowNum);
            }
        }
        lastSelectedRow = shouldDeselect ? null : rowNum;
    } else if (event.ctrlKey || event.metaKey) {
        // Ctrl-click: toggle single row
        if (selectedRows.has(rowNum)) {
            selectedRows.delete(rowNum);
            rowElement.classList.remove('selected');
            checkbox.checked = false;
            lastSelectedRow = selectedRows.size > 0 ?
                Array.from(selectedRows)[selectedRows.size - 1] : null;
        } else {
            selectedRows.add(rowNum);
            rowElement.classList.add('selected');
            checkbox.checked = true;
            lastSelectedRow = rowNum;
        }
    } else {
        // Regular click
        if (selectedRows.has(rowNum) && selectedRows.size === 1) {
            clearSelection();
            lastSelectedRow = null;
        } else {
            clearSelection();
            selectedRows.add(rowNum);
            rowElement.classList.add('selected');
            checkbox.checked = true;
            lastSelectedRow = rowNum;
        }
    }
    updateSelectionBar();
}

function handleRowRightClick(event, rowElement) {
    event.preventDefault();
    event.stopPropagation();
    const rowNum = rowElement.dataset.rowNum;

    if (!selectedRows.has(rowNum)) {
        clearSelection();
        selectedRows.add(rowNum);
        rowElement.classList.add('selected');
        rowElement.querySelector('.row-checkbox').checked = true;
        lastSelectedRow = rowNum;
        updateSelectionBar();
    }

    const menu = document.getElementById('rowContextMenu');
    menu.style.display = 'block';
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
}

function clearSelection() {
    selectedRows.clear();
    document.querySelectorAll('.data-row').forEach(row => {
        row.classList.remove('selected');
        row.querySelector('.row-checkbox').checked = false;
    });
    document.getElementById('selectAllCheckbox').checked = false;
    updateSelectionBar();
}

function selectAll() {
    document.querySelectorAll('.data-row').forEach(row => {
        selectedRows.add(row.dataset.rowNum);
        row.classList.add('selected');
        row.querySelector('.row-checkbox').checked = true;
    });
    document.getElementById('selectAllCheckbox').checked = true;
    updateSelectionBar();
}

function toggleSelectAll(checkbox) {
    checkbox.checked ? selectAll() : clearSelection();
}

function updateSelectionBar() {
    const count = selectedRows.size;
    const bar = document.getElementById('selectionBar');
    document.getElementById('selectionCount').textContent = count;
    bar.classList.toggle('active', count > 0);
}

// =============================================================================
// NOTE CHUNK CONTEXT MENU
// =============================================================================

function showNoteChunkMenu(event, rowNum, chunkIndex, chunkText) {
    event.preventDefault();
    event.stopPropagation();
    const menu = document.getElementById('noteChunkContextMenu');
    menu.style.display = 'block';
    menu.style.left = event.pageX + 'px';
    menu.style.top = event.pageY + 'px';
    currentNoteChunkContext = { rowNum, chunkIndex, chunkText };
}

function deleteNoteChunk() {
    if (!currentNoteChunkContext) return;
    const { rowNum, chunkIndex, chunkText } = currentNoteChunkContext;

    if (confirm(`Delete note chunk "${chunkText}"?`)) {
        fetch('/api/delete_note_chunk', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_num: rowNum, chunk_index: chunkIndex })
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                response.json().then(data => {
                    showNotification(data.error || 'Failed to delete chunk', 'error');
                });
            }
        }).catch(error => {
            showNotification(`Error: ${error}`, 'error');
        });
    }
}

function editNoteChunk() {
    if (!currentNoteChunkContext) return;
    const { rowNum, chunkIndex, chunkText } = currentNoteChunkContext;
    const newValue = prompt(`Edit note chunk:`, chunkText);
    if (newValue === null) return;

    const rowElement = document.querySelector(`tr[data-row-num="${rowNum}"]`);
    if (!rowElement) return;

    const notesCell = rowElement.querySelector('.notes-cell');
    const chunks = Array.from(notesCell.querySelectorAll('.note-chunk'))
        .map(c => c.textContent.trim());

    if (chunkIndex < chunks.length) {
        chunks[chunkIndex] = newValue.trim();
    }
    const newNotes = chunks.filter(c => c).join('; ');

    fetch('/api/edit_field', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ row_num: parseInt(rowNum), field: 'notes', value: newNotes })
    }).then(response => response.json())
      .then(result => {
          if (result.success) {
              location.reload();
          } else {
              showNotification(result.error || 'Failed to edit chunk', 'error');
          }
      }).catch(error => {
          showNotification(`Error: ${error}`, 'error');
      });
}

// =============================================================================
// SAVE PROGRESS
// =============================================================================

async function saveProgress() {
    const statusEl = document.getElementById('saveStatus');
    statusEl.textContent = 'Saving...';
    statusEl.style.color = 'var(--color-accent)';

    try {
        const response = await fetch('/api/save_progress', { method: 'POST' });
        const result = await response.json();

        if (result.success) {
            const timeStr = new Date().toLocaleTimeString('en-US', {
                hour: '2-digit', minute: '2-digit'
            });
            statusEl.textContent = `Last saved: ${timeStr}`;
            statusEl.style.color = 'var(--color-success)';
            setTimeout(() => {
                statusEl.style.color = 'var(--color-text-tertiary)';
            }, 2000);
        } else {
            statusEl.textContent = 'Save failed';
            statusEl.style.color = 'var(--color-error)';
        }
    } catch (error) {
        statusEl.textContent = 'Save failed';
        statusEl.style.color = 'var(--color-error)';
    }
}

// =============================================================================
// ROW ACTIONS
// =============================================================================

function googleSearchSelected() {
    if (selectedRows.size === 0) {
        showNotification('No rows selected', 'warning');
        return;
    }
    if (selectedRows.size > 5 && !confirm(`Open ${selectedRows.size} Google search tabs?`)) {
        return;
    }

    selectedRows.forEach(rowNum => {
        const row = document.querySelector(`tr[data-row-num="${rowNum}"]`);
        if (row) {
            const cells = row.querySelectorAll('td');
            const query = [
                cells[3]?.textContent || '',
                cells[5]?.textContent || '',
                cells[6]?.textContent || '',
                cells[7]?.textContent || ''
            ].join(' ').trim();
            window.open(`https://www.google.com/search?q=${encodeURIComponent(query)}`, '_blank');
        }
    });
}

async function deleteSelected() {
    if (selectedRows.size === 0) {
        showNotification('No rows selected', 'warning');
        return;
    }
    if (!confirm(`Delete ${selectedRows.size} selected row(s)?`)) return;

    try {
        const response = await fetch('/api/delete_rows', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_nums: Array.from(selectedRows) })
        });
        const result = await response.json();

        if (result.success) {
            selectedRows.forEach(rowNum => {
                const row = document.querySelector(`tr[data-row-num="${rowNum}"]`);
                if (row) {
                    row.classList.add('row-deleted');
                }
            });
            clearSelection();
            showNotification(`Marked ${result.count} row(s) for deletion`, 'info');
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error deleting rows: ${error}`, 'error');
    }
}

async function sendToManualReview() {
    if (selectedRows.size === 0) {
        showNotification('No rows selected', 'warning');
        return;
    }
    const reason = prompt('Reason for manual review (optional):', 'Needs closer inspection');
    if (reason === null) return;

    try {
        const response = await fetch('/api/send_to_manual_review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                row_nums: Array.from(selectedRows).map(n => parseInt(n)),
                reason: reason || 'Needs manual review'
            })
        });
        const result = await response.json();

        if (result.success) {
            clearSelection();
            showNotification(`Sent ${result.count} row(s) to Manual Review`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function markAsReviewed() {
    if (selectedRows.size === 0) {
        showNotification('No rows selected', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/mark_reviewed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_nums: Array.from(selectedRows).map(n => parseInt(n)) })
        });
        const result = await response.json();

        if (result.success) {
            selectedRows.forEach(rowNum => {
                const row = document.querySelector(`tr[data-row-num="${rowNum}"]`);
                if (row) {
                    row.style.backgroundColor = 'var(--color-bg-tertiary)';
                    row.classList.add('reviewed');
                }
            });
            clearSelection();
            showNotification(`Marked ${result.count} row(s) as reviewed`, 'info');
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

// Context menu helpers
function googleSearchFromMenu() {
    document.getElementById('rowContextMenu').style.display = 'none';
    googleSearchSelected();
}

function deleteSelectedFromMenu() {
    document.getElementById('rowContextMenu').style.display = 'none';
    deleteSelected();
}

// =============================================================================
// INLINE EDITING
// =============================================================================

function startInlineEdit(row, cell, field, rowNum) {
    if (currentEditingCell) cancelInlineEdit();
    currentEditingCell = { row, cell, field, rowNum };

    let currentValue;
    if (field === 'notes') {
        const chunks = cell.querySelectorAll('.note-chunk');
        currentValue = chunks.length > 0
            ? Array.from(chunks).map(c => c.textContent.trim()).join('; ')
            : cell.textContent.trim();
    } else {
        currentValue = cell.textContent.trim();
    }

    cell.dataset.originalContent = cell.innerHTML;
    cell.dataset.originalValue = currentValue;

    if (field === 'status') {
        const select = document.createElement('select');
        select.className = 'inline-edit-select';
        select.style.cssText = 'width: 100%; padding: 4px; font-size: 0.8125rem; border: 2px solid var(--color-accent); border-radius: 4px;';

        STATUS_OPTIONS.forEach(opt => {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt || '(empty)';
            if (opt.toLowerCase() === currentValue.toLowerCase() ||
                (opt === '' && currentValue === '\u2014')) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        select.addEventListener('change', () => saveInlineEdit(select.value));
        select.addEventListener('keydown', handleEditKeydown);
        select.addEventListener('blur', () => saveInlineEdit(select.value));

        cell.innerHTML = '';
        cell.appendChild(select);
        select.focus();
    } else {
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentValue === '\u2014' ? '' : currentValue;
        input.className = 'inline-edit-input';
        input.style.cssText = 'width: 100%; padding: 4px; font-size: 0.8125rem; border: 2px solid var(--color-accent); border-radius: 4px; box-sizing: border-box;';

        input.addEventListener('keydown', handleEditKeydown);
        input.addEventListener('blur', () => saveInlineEdit(input.value));

        cell.innerHTML = '';
        cell.appendChild(input);
        input.focus();
        input.select();
    }
    cell.classList.add('editing');
}

function handleEditKeydown(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        saveInlineEdit(e.target.value);
    } else if (e.key === 'Escape') {
        e.preventDefault();
        cancelInlineEdit();
    } else if (e.key === 'Tab') {
        e.preventDefault();
        saveInlineEdit(e.target.value);
    }
}

async function saveInlineEdit(newValue) {
    if (!currentEditingCell) return;
    const { row, cell, field, rowNum } = currentEditingCell;
    const originalValue = cell.dataset.originalValue;

    if (newValue === originalValue || (newValue === '' && originalValue === '\u2014')) {
        cancelInlineEdit();
        return;
    }

    try {
        const response = await fetch('/api/edit_field', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_num: parseInt(rowNum), field, value: newValue })
        });
        const result = await response.json();

        if (result.success) {
            cell.classList.remove('editing');

            if (field === 'notes' && newValue) {
                const chunks = newValue.split(';').filter(c => c.trim());
                if (chunks.length > 0) {
                    const chunkDiv = document.createElement('div');
                    chunkDiv.className = 'note-chunks';
                    chunks.forEach((chunk, idx) => {
                        const span = document.createElement('span');
                        span.className = 'note-chunk';
                        span.dataset.chunkIndex = idx;
                        span.textContent = chunk.trim();
                        span.oncontextmenu = (e) => {
                            showNoteChunkMenu(e, rowNum, idx, chunk.trim());
                            return false;
                        };
                        chunkDiv.appendChild(span);
                    });
                    cell.innerHTML = '';
                    cell.appendChild(chunkDiv);
                } else {
                    cell.innerHTML = '<span class="text-tertiary">\u2014</span>';
                }
            } else {
                cell.textContent = newValue || '\u2014';
            }

            cell.style.backgroundColor = '#d4edda';
            setTimeout(() => { cell.style.backgroundColor = ''; }, 500);

            if (field === 'status' && result.bg_color) {
                updateRowColor(row, result.bg_color);
            }
            row.classList.add('edited');
            currentEditingCell = null;
            updateProgressBar();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
            cancelInlineEdit();
        }
    } catch (error) {
        showNotification(`Error saving: ${error}`, 'error');
        cancelInlineEdit();
    }
}

function cancelInlineEdit() {
    if (!currentEditingCell) return;
    const { cell } = currentEditingCell;
    cell.classList.remove('editing');
    cell.innerHTML = cell.dataset.originalContent;
    currentEditingCell = null;
}

function updateRowColor(row, bgColor) {
    row.classList.remove('row-yellow', 'row-green', 'row-red', 'row-fuschia');
    const colorLower = bgColor.toLowerCase();
    if (colorLower.includes('ffff00') || colorLower.includes('ffff01')) {
        row.classList.add('row-yellow');
    } else if (colorLower.includes('00ff00')) {
        row.classList.add('row-green');
    } else if (colorLower.includes('ff0000')) {
        row.classList.add('row-red');
    } else if (colorLower.includes('ff00ff')) {
        row.classList.add('row-fuschia');
    }
}

// =============================================================================
// UNDO/REDO
// =============================================================================

async function undo() {
    if (isActionInProgress) return;
    isActionInProgress = true;
    try {
        const response = await fetch('/api/undo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();

        if (result.success) {
            showNotification(`Undone: ${result.action}`, 'info');
            location.reload();
        } else {
            showNotification(result.error || 'Nothing to undo', 'warning');
        }
    } catch (error) {
        showNotification(`Undo failed: ${error}`, 'error');
    } finally {
        isActionInProgress = false;
    }
}

async function redo() {
    if (isActionInProgress) return;
    isActionInProgress = true;
    try {
        const response = await fetch('/api/redo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();

        if (result.success) {
            showNotification(`Redone: ${result.action}`, 'info');
            location.reload();
        } else {
            showNotification(result.error || 'Nothing to redo', 'warning');
        }
    } catch (error) {
        showNotification(`Redo failed: ${error}`, 'error');
    } finally {
        isActionInProgress = false;
    }
}

async function updateUndoRedoStatus() {
    try {
        const response = await fetch('/api/undo_status');
        const status = await response.json();

        const undoBtn = document.getElementById('undoBtn');
        const redoBtn = document.getElementById('redoBtn');

        if (undoBtn) {
            if (status.can_undo && status.undo_description) {
                const shortDesc = status.undo_description.length > 20
                    ? status.undo_description.substring(0, 20) + '...'
                    : status.undo_description;
                undoBtn.innerHTML = `↶ Undo: ${escapeHtml(shortDesc)}`;
                undoBtn.title = `Undo: ${status.undo_description} (Ctrl+Z)`;
                undoBtn.disabled = false;
            } else {
                undoBtn.innerHTML = '↶ Undo';
                undoBtn.title = 'Nothing to undo';
                undoBtn.disabled = true;
            }
        }

        if (redoBtn) {
            if (status.can_redo && status.redo_description) {
                const shortDesc = status.redo_description.length > 20
                    ? status.redo_description.substring(0, 20) + '...'
                    : status.redo_description;
                redoBtn.innerHTML = `↷ Redo: ${escapeHtml(shortDesc)}`;
                redoBtn.title = `Redo: ${status.redo_description} (Ctrl+Y)`;
                redoBtn.disabled = false;
            } else {
                redoBtn.innerHTML = '↷ Redo';
                redoBtn.title = 'Nothing to redo';
                redoBtn.disabled = true;
            }
        }
    } catch (error) {
        console.error('Failed to update undo/redo status:', error);
    }
}

// Update undo/redo status on page load
document.addEventListener('DOMContentLoaded', updateUndoRedoStatus);

// =============================================================================
// NOTIFICATIONS
// =============================================================================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    const colors = {
        error: { bg: '#f8d7da', color: '#721c24', border: '#f5c6cb' },
        warning: { bg: '#fff3cd', color: '#856404', border: '#ffeeba' },
        info: { bg: '#d1ecf1', color: '#0c5460', border: '#bee5eb' }
    };
    const c = colors[type] || colors.info;
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px; padding: 12px 20px;
        border-radius: 8px; background: ${c.bg}; color: ${c.color};
        border: 1px solid ${c.border}; z-index: 9999;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

async function updateProgressBar() {
    try {
        const response = await fetch('/api/get_progress');
        const progress = await response.json();

        const progressText = document.querySelector('.progress-section .progress-text');
        if (progressText) {
            progressText.textContent = `${progress.resolved}/${progress.total} rows resolved (${progress.percent}%)`;
        }

        const urgencyBar = document.querySelector('.urgency-bar');
        if (urgencyBar) {
            urgencyBar.innerHTML = '';
            if (progress.critical_width > 0) {
                const pct = progress.critical_total > 0 ?
                    (progress.critical_resolved / progress.critical_total * 100) : 0;
                urgencyBar.innerHTML += `<div class="urgency-segment critical" style="width: ${progress.critical_width}%;" title="Critical: ${progress.critical_resolved}/${progress.critical_total}"><div class="urgency-fill" style="width: ${pct}%;"></div></div>`;
            }
            if (progress.review_width > 0) {
                const pct = progress.review_total > 0 ?
                    (progress.review_resolved / progress.review_total * 100) : 0;
                urgencyBar.innerHTML += `<div class="urgency-segment review" style="width: ${progress.review_width}%;" title="Review: ${progress.review_resolved}/${progress.review_total}"><div class="urgency-fill" style="width: ${pct}%;"></div></div>`;
            }
            if (progress.verify_width > 0) {
                const pct = progress.verify_total > 0 ?
                    (progress.verify_resolved / progress.verify_total * 100) : 0;
                urgencyBar.innerHTML += `<div class="urgency-segment verify" style="width: ${progress.verify_width}%;" title="Verify: ${progress.verify_resolved}/${progress.verify_total}"><div class="urgency-fill" style="width: ${pct}%;"></div></div>`;
            }
        }
    } catch (error) {
        console.error('Failed to update progress bar:', error);
    }
}

// =============================================================================
// MERGE MODAL
// =============================================================================

async function openMergeModal(rowNum) {
    try {
        const response = await fetch('/api/get_duplicate_group', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_num: rowNum })
        });
        const result = await response.json();

        if (!result.success) {
            showNotification(result.error || 'Could not load duplicate group', 'error');
            return;
        }

        mergeGroupRows = result.rows;
        selectedSurvivor = null;
        renderMergeModal();
        document.getElementById('mergeModal').style.display = 'block';
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

function renderMergeModal() {
    const container = document.getElementById('mergeRowsContainer');
    container.innerHTML = '';

    mergeGroupRows.forEach(row => {
        const card = document.createElement('div');
        card.className = 'merge-card' + (selectedSurvivor === row.row_num ? ' selected' : '');
        card.style.cssText = `
            flex: 1; min-width: 280px; max-width: 400px;
            border: 2px solid ${selectedSurvivor === row.row_num ? 'var(--color-accent)' : 'var(--border-color)'};
            border-radius: 8px; padding: 1rem;
            background: ${selectedSurvivor === row.row_num ? 'var(--color-bg-secondary)' : 'white'};
            cursor: pointer; transition: all 0.2s ease;
        `;
        card.onclick = () => selectSurvivor(row.row_num);
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 600; color: var(--color-primary);">Row #${row.row_num}</span>
                <input type="radio" name="survivor" value="${row.row_num}" ${selectedSurvivor === row.row_num ? 'checked' : ''} style="width: 18px; height: 18px;">
            </div>
            <div style="font-size: 0.875rem; line-height: 1.6;">
                <div><strong>Practice:</strong> ${escapeHtml(row.practice) || '\u2014'}</div>
                <div><strong>Phone:</strong> ${escapeHtml(row.phone) || '\u2014'}</div>
                <div><strong>Address:</strong> ${escapeHtml(row.address) || '\u2014'}</div>
                <div><strong>City/State:</strong> ${escapeHtml(row.city) || '\u2014'}, ${escapeHtml(row.state) || '\u2014'}</div>
                <div><strong>Status:</strong> ${escapeHtml(row.status) || '\u2014'}</div>
                <div><strong>Notes:</strong> <span style="color: var(--color-text-secondary);">${escapeHtml(row.notes) || '\u2014'}</span></div>
            </div>
        `;
        container.appendChild(card);
    });

    document.getElementById('mergeConfirmBtn').disabled = !selectedSurvivor;
}

function selectSurvivor(rowNum) {
    selectedSurvivor = rowNum;
    renderMergeModal();
}

function closeMergeModal() {
    document.getElementById('mergeModal').style.display = 'none';
    mergeGroupRows = [];
    selectedSurvivor = null;
}

async function confirmMerge() {
    if (!selectedSurvivor) {
        showNotification('Please select a survivor row', 'warning');
        return;
    }

    const otherRowNums = mergeGroupRows
        .filter(r => r.row_num !== selectedSurvivor)
        .map(r => r.row_num);

    try {
        const response = await fetch('/api/merge_rows', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ survivor_row_num: selectedSurvivor, other_row_nums: otherRowNums })
        });
        const result = await response.json();

        if (result.success) {
            showNotification(`Merged ${result.deleted_count + 1} rows. Survivor: #${result.survivor_row_num}`, 'info');
            closeMergeModal();
            location.reload();
        } else {
            showNotification(result.error || 'Merge failed', 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

// =============================================================================
// NETWORK MODAL
// =============================================================================

async function openNetworkModal(rowNum) {
    try {
        const response = await fetch('/api/get_network_group', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_num: rowNum })
        });
        const result = await response.json();

        if (!result.success) {
            showNotification(result.error || 'Could not load network', 'error');
            return;
        }

        networkGroupRows = result.rows;
        selectedNetworkRows = new Set(result.rows.map(r => r.row_num));
        document.getElementById('networkNameInput').value = result.suggested_name || 'Network';
        document.getElementById('networkNoteInput').value = '';
        renderNetworkModal();
        document.getElementById('networkModal').style.display = 'block';
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

function renderNetworkModal() {
    const container = document.getElementById('networkRowsContainer');
    container.innerHTML = '';

    networkGroupRows.forEach(row => {
        const isSelected = selectedNetworkRows.has(row.row_num);
        const rowEl = document.createElement('div');
        rowEl.style.cssText = `
            display: flex; align-items: center; gap: 0.75rem;
            padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color);
            background: ${isSelected ? 'var(--color-bg-secondary)' : 'white'};
        `;
        rowEl.innerHTML = `
            <input type="checkbox" ${isSelected ? 'checked' : ''} onchange="toggleNetworkRow(${row.row_num})" style="width: 18px; height: 18px;">
            <div style="flex: 1; font-size: 0.875rem;">
                <div style="font-weight: 500;">#${row.row_num}: ${escapeHtml(row.practice) || '\u2014'}</div>
                <div style="color: var(--color-text-secondary);">${escapeHtml(row.address) || '\u2014'}, ${escapeHtml(row.city) || '\u2014'} ${escapeHtml(row.state) || '\u2014'}</div>
            </div>
            <div style="font-size: 0.8125rem; color: var(--color-text-tertiary);">${escapeHtml(row.phone) || '\u2014'}</div>
        `;
        container.appendChild(rowEl);
    });
}

function toggleNetworkRow(rowNum) {
    if (selectedNetworkRows.has(rowNum)) {
        selectedNetworkRows.delete(rowNum);
    } else {
        selectedNetworkRows.add(rowNum);
    }
    renderNetworkModal();
}

function closeNetworkModal() {
    document.getElementById('networkModal').style.display = 'none';
    networkGroupRows = [];
    selectedNetworkRows.clear();
}

async function confirmNetworkAction() {
    const networkName = document.getElementById('networkNameInput').value.trim();
    const addNote = document.getElementById('networkNoteInput').value.trim();

    if (!networkName) {
        showNotification('Please enter a network name', 'warning');
        return;
    }
    if (selectedNetworkRows.size === 0) {
        showNotification('Please select at least one row', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/confirm_network', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                network_name: networkName,
                row_nums: Array.from(selectedNetworkRows),
                add_note: addNote
            })
        });
        const result = await response.json();

        if (result.success) {
            showNotification(`Confirmed ${result.count} rows as "${result.network_name}"`, 'info');
            closeNetworkModal();
            location.reload();
        } else {
            showNotification(result.error || 'Failed to confirm network', 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

// =============================================================================
// CATEGORY-SPECIFIC ACTIONS
// =============================================================================

async function keepFirstDeleteRest() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Keep first of each duplicate group, delete rest? (${allRows.length} total rows)`)) return;

    try {
        const response = await fetch('/api/keep_first_delete_rest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) location.reload();
        else showNotification(`Error: ${result.error}`, 'error');
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function acceptAllMatches() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Accept all ${allRows.length} yellow matches?`)) return;

    try {
        const response = await fetch('/api/accept_all_matches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Accepted ${result.count} matches`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function confirmNetwork() {
    const allRows = document.querySelectorAll('.data-row');
    const networkName = prompt(`Confirm network name for ${allRows.length} locations:`);
    if (!networkName) return;

    try {
        const response = await fetch('/api/confirm_network', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId(), network_name: networkName })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Confirmed network: ${networkName} (${result.count} locations)`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function convertToNotInterested() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Convert all ${allRows.length} green 'sent' rows to 'Not Interested'?`)) return;

    try {
        const response = await fetch('/api/convert_to_not_interested', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Converted ${result.count} rows`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function moveAllToInvalid() {
    const allRows = document.querySelectorAll('.data-row');
    const reason = prompt(`Move all ${allRows.length} rows to Invalid List?\n\nEnter reason:`, 'Potentially Invalid');
    if (!reason) return;

    try {
        const response = await fetch('/api/move_to_invalid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId(), reason })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Moved ${result.count} rows to Invalid List`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function markNotFound() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Mark all ${allRows.length} rows as "not found in new orders"?`)) return;

    try {
        const response = await fetch('/api/mark_not_found', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Marked ${result.count} rows as not found`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function fixQtyMismatches() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Fix QTY mismatches for all ${allRows.length} rows?`)) return;

    try {
        const response = await fetch('/api/fix_qty_mismatches', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Fixed ${result.count} QTY mismatches`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function changeToWhite() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Change all ${allRows.length} rows to "Not Interested" (white)?`)) return;

    try {
        const response = await fetch('/api/change_to_white', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Changed ${result.count} rows to Not Interested`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function massInvalid() {
    const reason = prompt('Enter reason for marking as invalid:', 'INVALID - Network closed');
    if (!reason) return;

    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Mark all ${allRows.length} rows as invalid?`)) return;

    try {
        const response = await fetch('/api/mass_invalid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId(), reason: reason })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Marked ${result.count} rows as invalid`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function removeSent() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Remove "sent" from notes on all ${allRows.length} rows?`)) return;

    try {
        const response = await fetch('/api/remove_sent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Removed "sent" from ${result.count} rows`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function addVmNote() {
    const allRows = document.querySelectorAll('.data-row');
    if (!confirm(`Add/increment VM note on all ${allRows.length} rows?`)) return;

    try {
        const response = await fetch('/api/add_vm_note', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category_id: getCategoryId() })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Added VM notes to ${result.count} rows`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

async function markAllReviewed() {
    const allRows = document.querySelectorAll('.data-row');
    const rowNums = Array.from(allRows).map(r => parseInt(r.dataset.rowNum));

    if (!confirm(`Mark all ${allRows.length} rows as reviewed (no changes needed)?`)) return;

    try {
        const response = await fetch('/api/mark_reviewed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row_nums: rowNums })
        });
        const result = await response.json();
        if (result.success) {
            showNotification(`Marked ${result.count} rows as reviewed`, 'info');
            location.reload();
        } else {
            showNotification(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

function getCategoryId() {
    // Extract category ID from URL
    const path = window.location.pathname;
    const match = path.match(/\/category\/([^\/]+)/);
    return match ? match[1] : '';
}

// =============================================================================
// TABLE SORTING
// =============================================================================

function sortTable(columnIndex) {
    const table = document.getElementById('dataTable');
    const tbody = table.querySelector('tbody');
    const dataRows = Array.from(tbody.querySelectorAll('tr.data-row'));

    const key = `col_${columnIndex}`;
    sortDirection[key] = sortDirection[key] === 'asc' ? 'desc' : 'asc';
    const ascending = sortDirection[key] === 'asc';

    dataRows.sort((a, b) => {
        const aCell = a.cells[columnIndex]?.textContent.trim() || '';
        const bCell = b.cells[columnIndex]?.textContent.trim() || '';
        const aNum = parseFloat(aCell);
        const bNum = parseFloat(bCell);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }
        return ascending ? aCell.localeCompare(bCell) : bCell.localeCompare(aCell);
    });

    dataRows.forEach(dataRow => {
        tbody.appendChild(dataRow);
        const detailRow = document.getElementById(`detail-${dataRow.dataset.rowNum}`);
        if (detailRow) tbody.appendChild(detailRow);
    });
}

// =============================================================================
// EXPORT
// =============================================================================

async function exportToClipboard() {
    const includeDeleted = document.getElementById('includeDeleted').checked;

    try {
        const response = await fetch(`/api/export?mode=clipboard&include_deleted=${includeDeleted}`);
        const result = await response.json();

        if (result.success) {
            await navigator.clipboard.writeText(result.csv);
            showNotification(`Copied ${result.row_count} rows to clipboard!`, 'info');
        } else {
            showNotification(`Export failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification(`Export failed: ${error}`, 'error');
    }
}

function exportToFile() {
    const includeDeleted = document.getElementById('includeDeleted').checked;
    window.location.href = `/api/export?mode=download&include_deleted=${includeDeleted}`;
    showNotification('Download started...', 'info');
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Checkbox change handlers
    document.querySelectorAll('.row-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            const rowNum = checkbox.dataset.rowNum;
            const row = document.querySelector(`tr[data-row-num="${rowNum}"]`);

            if (checkbox.checked) {
                selectedRows.add(rowNum);
                row.classList.add('selected');
            } else {
                selectedRows.delete(rowNum);
                row.classList.remove('selected');
            }
            updateSelectionBar();
        });
    });

    // Inline editing on double-click
    document.querySelectorAll('.data-row').forEach(row => {
        const rowNum = row.dataset.rowNum;
        const cells = row.querySelectorAll('td');

        Object.entries(FIELD_MAP).forEach(([field, colIndex]) => {
            if (cells[colIndex]) {
                cells[colIndex].addEventListener('dblclick', (e) => {
                    e.stopPropagation();
                    startInlineEdit(row, cells[colIndex], field, rowNum);
                });
                cells[colIndex].style.cursor = 'pointer';
                cells[colIndex].title = 'Double-click to edit';
            }
        });
    });

    // Hide context menus on click elsewhere
    document.addEventListener('click', () => {
        document.getElementById('noteChunkContextMenu').style.display = 'none';
        document.getElementById('rowContextMenu').style.display = 'none';
    });

    // Keyboard shortcuts (Escape only - Ctrl+Z/Y handled by shortcuts.js)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeMergeModal();
            closeNetworkModal();
        }
    });
});
