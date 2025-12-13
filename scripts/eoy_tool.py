"""
EOY Cleanup Tool - Flask Web Application
Healthcare Provider Data Cleanup for End of Year Reset

Architecture: Flask backend + HTML/CSS/JS frontend
Design: "Data Atelier" - Refined craftsmanship aesthetic

Core logic is organized in modules:
- models.py: Data models (ProviderRow, NewOrderRow, etc.)
- helpers.py: Utility functions (safe_int, normalizers, status_to_color)
- state.py: Application state management
- loading.py: Google Sheets data loading
- validation.py: Validation pipeline
- undo_redo.py: Undo/redo system
"""

from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from typing import Dict, Any
import csv
import io
import os
import re
from datetime import datetime
from collections import defaultdict
import webbrowser
import threading
import argparse
from rapidfuzz import fuzz

# Import from modular components
from models import ProviderRow, NewOrderRow, InvalidRow, ReviewCategory
from helpers import safe_int, safe_int_list, status_to_color, normalize_name, normalize_address, normalize_phone
from state import AppState, state
from validation import run_validations
# Note: loading module imported lazily in load() to avoid gspread import during tests
from undo_redo import (
    add_to_undo_stack as _add_to_undo_stack,
    save_progress as _save_progress,
    calculate_progress as _calculate_progress,
    restore_state as _restore_state
)

# Configure Flask to look for templates/static in parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(parent_dir, 'templates')
static_dir = os.path.join(parent_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-prod')


# Wrapper functions that pass global state to module functions
def add_to_undo_stack(action_type: str, description: str, before_state: Any, after_state: Any = None):
    """Add action to undo stack (wrapper for undo_redo module)"""
    _add_to_undo_stack(state, action_type, description, before_state, after_state)

def save_progress():
    """Save current progress (wrapper for undo_redo module)"""
    return _save_progress(state)

def calculate_progress() -> Dict:
    """Calculate progress counts (wrapper for undo_redo module)"""
    return _calculate_progress(state)

def restore_state(action: Dict, direction: str = 'undo') -> bool:
    """Restore state for undo/redo (wrapper for undo_redo module)"""
    return _restore_state(state, action, direction)


# NOTE: The following sections have been moved to separate modules:
# - DATA MODELS -> models.py
# - GLOBAL STATE -> state.py
# - HELPER FUNCTIONS -> helpers.py
# - PHASE 1: DATA LOADING -> loading.py
# - PHASE 2: VALIDATION LOGIC -> validation.py
# - UNDO/REDO SYSTEM -> undo_redo.py
#
# Models, state, and functions are imported at the top of this file.
# Routes remain here as they require the Flask app object.


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page - always show load screen"""
    return render_template('index.html')

@app.route('/load', methods=['POST'])
def load():
    """Load data and run validations"""
    # Lazy import to avoid gspread loading during tests
    from loading import load_data, validate_stats_color_counts

    try:
        year = int(request.form.get('year', 2025))
        state.year = year

        # Load data from Google Sheets
        wl_rows, no_rows, invalid_rows, invalid_reasons, stats_sheet = load_data(year)

        # Validate Status-derived colors against STATS sheet
        if not validate_stats_color_counts(wl_rows, stats_sheet, year, assume_yes=True):
            return jsonify({'success': False, 'error': 'Status/color mismatch - check console'}), 500

        # Run validation pipeline
        categories = run_validations(wl_rows, no_rows, invalid_rows, invalid_reasons)

        # Store in app state
        state.wl_rows = wl_rows
        state.no_rows = no_rows
        state.invalid_rows = invalid_rows
        state.invalid_reasons = invalid_reasons
        state.categories = categories
        state.loaded = True
        state.current_category_id = state.categories[0].id if state.categories else None

        return jsonify({
            'success': True,
            'total_rows': len(state.wl_rows),
            'categories_count': len(state.categories)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/categories')
def categories():
    """Redirect to first category"""
    if not state.loaded:
        return redirect(url_for('index'))

    # Redirect to first category
    if state.categories:
        return redirect(url_for('category', category_id=state.categories[0].id))
    else:
        return "No categories found", 404

@app.route('/category/<category_id>')
def category(category_id):
    """View specific category"""
    if not state.loaded:
        return redirect(url_for('index'))

    cat = next((c for c in state.categories if c.id == category_id), None)
    if not cat:
        return "Category not found", 404

    state.current_category_id = category_id

    # Get rows for this category
    rows = [r for r in state.wl_rows if r.row_num in cat.row_nums]

    return render_template('category.html',
                         category=cat,
                         rows=rows,
                         categories=state.categories,
                         progress=calculate_progress(),
                         state=state)

@app.route('/api/save_progress', methods=['POST'])
def api_save_progress():
    """API endpoint to save progress"""
    try:
        filename = save_progress()
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get_progress')
def api_get_progress():
    """Get current progress by urgency level"""
    return jsonify(calculate_progress())


def get_action_taken(row) -> str:
    """
    Derive action taken label for a row based on its action and field_edits.
    Returns standard action labels for export.

    Priority order (highest to lowest):
    1. DELETED - row will be removed
    2. MERGED - row absorbed into another
    3. MOVED_TO_INVALID - moved to invalid list
    4. CONVERTED - status changed (e.g., to not interested)
    5. NETWORK_CONFIRMED - marked as network
    6. VERIFIED - confirmed/accepted
    7. EDITED - fields modified (lowest priority)
    """
    if not row.action and not row.field_edits:
        return ''

    action = (row.action or '').lower()

    # Check in priority order - most impactful changes first
    # 1. Deletion (highest priority)
    if 'deleted' in action:
        return 'DELETED'

    # 2. Merged into another row
    if 'merged_into' in action or 'merged' in action:
        return 'MERGED'

    # 3. Moved to invalid list
    if 'moved_to_invalid' in action or 'invalid' in action:
        return 'MOVED_TO_INVALID'

    # 4. Status conversion
    if 'converted' in action:
        return 'CONVERTED'

    # 5. Network confirmed
    if 'network_confirmed' in action or 'network' in action:
        return 'NETWORK_CONFIRMED'

    # 6. Verified/accepted/reviewed
    if any(x in action for x in ['accepted', 'verified', 'marked_reviewed', 'matched', 'reviewed']):
        return 'VERIFIED'

    # 7. Field edits only (lowest priority)
    if row.field_edits:
        return 'EDITED'

    # Has some action but not mapped
    if action:
        return 'MODIFIED'

    return ''


@app.route('/api/export')
def api_export():
    """
    Export all rows as CSV.
    Query params:
    - mode: 'download' (file) or 'clipboard' (json with CSV text)
    - include_deleted: 'true' or 'false' (default true)
    """
    mode = request.args.get('mode', 'clipboard')
    include_deleted = request.args.get('include_deleted', 'true').lower() == 'true'

    # Filter rows
    rows = state.wl_rows
    if not include_deleted:
        rows = [r for r in rows if 'deleted' not in (r.action or '').lower()]

    # Sort by row_num
    rows = sorted(rows, key=lambda r: r.row_num)

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    for row in rows:
        # Clean notes (replace newlines with space)
        notes = (row.notes or '').replace('\n', ' ').replace('\r', ' ')

        # Get action taken
        action_taken = get_action_taken(row)

        # Write row: practice, phone, address, city, state, zip, qty_2023, qty_2024, qty_2025, status, notes, action_taken
        writer.writerow([
            row.practice,
            row.phone,
            row.address,
            row.city,
            row.state,
            row.zip,
            row.qty_2023,
            row.qty_2024,
            row.qty_2025,
            row.status,
            notes,
            action_taken
        ])

    csv_text = output.getvalue()

    if mode == 'download':
        # Return as downloadable file
        filename = f'eoy_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return Response(
            csv_text,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    else:
        # Return as JSON for clipboard copy
        return jsonify({
            'success': True,
            'csv': csv_text,
            'row_count': len(rows)
        })


@app.route('/api/undo', methods=['POST'])
def api_undo():
    """API endpoint to undo last action"""
    if not state.undo_stack:
        return jsonify({'success': False, 'error': 'Nothing to undo'}), 400

    action = state.undo_stack.pop()

    # Apply undo (restore before_state)
    success = restore_state(action, 'undo')

    if success:
        state.redo_stack.append(action)

    return jsonify({
        'success': success,
        'action': action['description'],
        'can_undo': len(state.undo_stack) > 0,
        'can_redo': len(state.redo_stack) > 0
    })

@app.route('/api/redo', methods=['POST'])
def api_redo():
    """API endpoint to redo last undone action"""
    if not state.redo_stack:
        return jsonify({'success': False, 'error': 'Nothing to redo'}), 400

    action = state.redo_stack.pop()

    # Apply redo (restore after_state)
    success = restore_state(action, 'redo')

    if success:
        state.undo_stack.append(action)

    return jsonify({
        'success': success,
        'action': action['description'],
        'can_undo': len(state.undo_stack) > 0,
        'can_redo': len(state.redo_stack) > 0
    })


@app.route('/api/delete_note_chunk', methods=['POST'])
def api_delete_note_chunk():
    """API endpoint to delete a note chunk"""
    data = request.get_json()
    row_num = safe_int(data.get('row_num'), allow_zero=False)
    chunk_index = safe_int(data.get('chunk_index'), allow_zero=True)

    # Find row
    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
    if not row:
        return jsonify({'success': False, 'error': 'Row not found'}), 404

    # Save before state for undo
    before_notes = row.notes
    before_action = row.action

    # Check if notes exist
    if not row.notes:
        return jsonify({'success': False, 'error': 'No notes to delete from'}), 400

    # Delete chunk
    chunks = [c.strip() for c in row.notes.split(';') if c.strip()]
    if 0 <= chunk_index < len(chunks):
        chunk_text = chunks[chunk_index]
        del chunks[chunk_index]
        row.notes = '; '.join(chunks)
        row.field_edits['notes'] = row.notes
        row.action = 'edited'

        # Add to undo stack
        add_to_undo_stack(
            action_type='delete_note_chunk',
            description=f"Deleted note chunk '{chunk_text}' from row {row_num}",
            before_state={'row_num': row_num, 'notes': before_notes, 'action': before_action},
            after_state={'row_num': row_num, 'notes': row.notes, 'action': 'edited'}
        )

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Chunk index out of range'}), 400

@app.route('/api/delete_rows', methods=['POST'])
def api_delete_rows():
    """API endpoint to delete selected rows"""
    data = request.get_json()
    row_nums = safe_int_list(data.get('row_nums', []))

    if not row_nums:
        return jsonify({'success': False, 'error': 'No rows specified'}), 400

    # Store before states for undo
    before_states = []
    deleted_count = 0

    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Store full state for proper undo restoration
            before_states.append({
                'row_num': row_num,
                'fields': {'action': row.action}
            })
            row.action = 'deleted'
            deleted_count += 1

    # Add to undo stack with proper before_state structure
    add_to_undo_stack(
        action_type='delete_rows',
        description=f"Deleted {deleted_count} rows",
        before_state={'rows': before_states},
        after_state={'rows': [{'row_num': r['row_num'], 'fields': {'action': 'deleted'}} for r in before_states]}
    )

    return jsonify({'success': True, 'count': deleted_count})

@app.route('/api/keep_first_delete_rest', methods=['POST'])
def api_keep_first_delete_rest():
    """Keep first occurrence of each duplicate group, delete rest"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Group rows by duplicate_group_id
    groups = defaultdict(list)

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.duplicate_group_id:
            groups[row.duplicate_group_id].append(row)

    # Keep first, delete rest - collect before states
    before_states = []
    after_states = []
    deleted_count = 0

    for group_id, rows in groups.items():
        if len(rows) > 1:
            # Keep first (lowest row number)
            rows.sort(key=lambda r: r.row_num)
            for row in rows[1:]:  # Delete rest
                before_states.append({
                    'row_num': row.row_num,
                    'fields': {'action': row.action}
                })
                row.action = 'deleted'
                after_states.append({
                    'row_num': row.row_num,
                    'fields': {'action': 'deleted'}
                })
                deleted_count += 1

    if deleted_count > 0:
        add_to_undo_stack(
            action_type='keep_first_delete_rest',
            description=f"Kept first of {len(groups)} duplicate groups, deleted {deleted_count} rows",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': deleted_count})

@app.route('/api/accept_all_matches', methods=['POST'])
def api_accept_all_matches():
    """Accept all yellow matches in category"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Mark all rows as accepted - collect before states
    before_states = []
    after_states = []
    count = 0

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row.row_num,
                'fields': {'action': row.action}
            })
            row.action = 'accepted'
            after_states.append({
                'row_num': row.row_num,
                'fields': {'action': 'accepted'}
            })
            count += 1

    if count > 0:
        add_to_undo_stack(
            action_type='accept_all',
            description=f"Accepted {count} matches in {category.name}",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/convert_to_not_interested', methods=['POST'])
def api_convert_to_not_interested():
    """Convert green 'sent' rows to Not Interested"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Convert all rows - collect before states
    before_states = []
    after_states = []
    count = 0

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Store before state
            before_states.append({
                'row_num': row.row_num,
                'fields': {
                    'status': row.status,
                    'qty_2025': row.qty_2025,
                    'bg_color': row.bg_color,
                    'notes': row.notes,
                    'action': row.action
                }
            })

            # Apply changes
            row.status = "Not Interested"
            row.qty_2025 = "0"
            row.bg_color = "#ffffff"

            # Remove 'sent' from notes, add 'not interested'
            notes = re.sub(r':?sent', '', row.notes or '', flags=re.IGNORECASE).strip()
            if not notes or 'not interested' not in notes.lower():
                row.notes = f"{notes}; not interested" if notes else "not interested"
            else:
                row.notes = notes

            # Clean up extra semicolons
            row.notes = re.sub(r'\s*;\s*;', ';', row.notes).strip(';').strip()
            row.action = 'converted_to_not_interested'

            # Store after state
            after_states.append({
                'row_num': row.row_num,
                'fields': {
                    'status': row.status,
                    'qty_2025': row.qty_2025,
                    'bg_color': row.bg_color,
                    'notes': row.notes,
                    'action': row.action
                }
            })
            count += 1

    if count > 0:
        add_to_undo_stack(
            action_type='change_to_white',
            description=f"Converted {count} rows to Not Interested",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/move_to_invalid', methods=['POST'])
def api_move_to_invalid():
    """Move rows to Invalid/Inactive List"""
    data = request.get_json()
    category_id = data.get('category_id')
    reason = data.get('reason', 'INVALID')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Mark all rows for move to invalid - collect before states
    before_states = []
    after_states = []
    count = 0

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row.row_num,
                'fields': {
                    'action': row.action,
                    'field_edits': dict(row.field_edits)
                }
            })
            row.action = 'move_to_invalid'
            row.field_edits['invalid_reason'] = reason
            after_states.append({
                'row_num': row.row_num,
                'fields': {
                    'action': 'move_to_invalid',
                    'field_edits': dict(row.field_edits)
                }
            })
            count += 1

    if count > 0:
        add_to_undo_stack(
            action_type='mass_invalid',
            description=f"Marked {count} rows for move to Invalid ({reason})",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/fix_qty_mismatches', methods=['POST'])
def api_fix_qty_mismatches():
    """Update qty_2025 in WL rows to match NO rows"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Fix qty mismatches - collect before states
    before_states = []
    after_states = []
    count = 0

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.matched_no_row:
            # Find matching NO row
            no_row = next((n for n in state.no_rows if n.row_num == row.matched_no_row), None)
            if no_row and row.qty_2025 != no_row.qty_2025:
                # Store before state
                before_states.append({
                    'row_num': row.row_num,
                    'fields': {
                        'qty_2025': row.qty_2025,
                        'action': row.action
                    }
                })
                # Update qty to match NO row
                row.qty_2025 = no_row.qty_2025
                row.field_edits['qty_2025'] = no_row.qty_2025
                row.action = 'qty_fixed'
                # Store after state
                after_states.append({
                    'row_num': row.row_num,
                    'fields': {
                        'qty_2025': row.qty_2025,
                        'action': 'qty_fixed'
                    }
                })
                count += 1

    if count > 0:
        add_to_undo_stack(
            action_type='batch_action',
            description=f"Fixed {count} QTY mismatches",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/mark_not_found', methods=['POST'])
def api_mark_not_found():
    """Add 'not found in new orders' note to yellow rows"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Mark as not found
    count = 0
    before_states = []

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Add note
            existing_notes = row.notes if row.notes else ""
            note_to_add = "not found in new orders"

            # Only add if not already present
            if note_to_add not in existing_notes.lower():
                # Save before state
                before_states.append({
                    'row_num': row_num,
                    'fields': {'notes': row.notes, 'action': row.action}
                })

                if existing_notes and not existing_notes.endswith(';'):
                    existing_notes += '; '
                elif existing_notes:
                    existing_notes += ' '
                new_notes = existing_notes + note_to_add + ';'
                row.notes = new_notes  # Update actual field
                row.field_edits['notes'] = new_notes  # Track change
                row.action = 'edit'
                count += 1

    if count > 0:
        add_to_undo_stack(
            action_type='batch_action',
            description=f"Marked {count} rows as 'not found'",
            before_state={'rows': before_states},
            after_state={'rows': [{'row_num': s['row_num'], 'fields': {'notes': next((r for r in state.wl_rows if r.row_num == s['row_num']), None).notes, 'action': 'edit'}} for s in before_states]}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/add_vm_note', methods=['POST'])
def api_add_vm_note():
    """Parse and increment voicemail counter in notes"""
    data = request.get_json()
    category_id = data.get('category_id')
    row_nums = safe_int_list(data.get('row_nums', []))  # Specific rows if provided

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Use provided row_nums or all in category
    target_rows = row_nums if row_nums else category.row_nums

    count = 0
    before_states = []

    for row_num in target_rows:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Save before state
            before_states.append({
                'row_num': row_num,
                'fields': {'notes': row.notes, 'action': row.action}
            })

            notes = row.notes if row.notes else ""

            # Parse existing vm count: "vm x2" or "vm x3"
            vm_match = re.search(r'vm x(\d+)', notes, re.IGNORECASE)
            if vm_match:
                # Increment counter
                current_count = int(vm_match.group(1))
                new_count = current_count + 1
                new_notes = re.sub(r'vm x\d+', f'vm x{new_count}', notes, flags=re.IGNORECASE)
            else:
                # Add new vm x2 (assuming this is 2nd attempt)
                if notes and not notes.endswith(';'):
                    notes += '; '
                elif notes:
                    notes += ' '
                new_notes = notes + 'vm x2;'

            row.notes = new_notes  # Update actual field
            row.field_edits['notes'] = new_notes  # Track change
            row.action = 'edit'
            count += 1

    if count > 0:
        add_to_undo_stack(
            action_type='batch_action',
            description=f"Added VM notes to {count} rows",
            before_state={'rows': before_states},
            after_state={'rows': [{'row_num': s['row_num'], 'fields': {'notes': next((r for r in state.wl_rows if r.row_num == s['row_num']), None).notes, 'action': 'edit'}} for s in before_states]}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/change_status', methods=['POST'])
def api_change_status():
    """Change status and derive bg_color"""
    data = request.get_json()
    category_id = data.get('category_id')
    row_nums = safe_int_list(data.get('row_nums', []))
    new_status = data.get('status')

    if not new_status:
        return jsonify({'success': False, 'error': 'Status required'}), 400

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Use provided row_nums or all in category
    target_rows = row_nums if row_nums else category.row_nums

    count = 0
    before_states = []
    for row_num in target_rows:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {'status': row.status, 'bg_color': row.bg_color, 'action': row.action}
            })
            # Update status - both actual field and tracking
            new_color = status_to_color(new_status)
            row.status = new_status
            row.bg_color = new_color
            row.field_edits['status'] = new_status
            row.field_edits['bg_color'] = new_color
            row.action = 'edit'
            count += 1

    if before_states:
        add_to_undo_stack(
            'change_status',
            f'Changed status to "{new_status}" on {count} row(s)',
            {'rows': before_states, 'new_status': new_status}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/change_to_white', methods=['POST'])
def api_change_to_white():
    """Change status to 'Not interested' (white)"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    count = 0
    before_states = []
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {
                    'status': row.status, 'bg_color': row.bg_color,
                    'qty_2025': row.qty_2025, 'notes': row.notes, 'action': row.action
                }
            })
            # Update actual fields
            row.status = 'Not interested'
            row.bg_color = '#ffffff'
            row.qty_2025 = '0'
            row.field_edits['status'] = 'Not interested'
            row.field_edits['bg_color'] = '#ffffff'
            row.field_edits['qty_2025'] = '0'

            # Add "not interested" to notes if not present
            notes = row.notes if row.notes else ""
            if 'not interested' not in notes.lower():
                if notes and not notes.endswith(';'):
                    notes += '; '
                elif notes:
                    notes += ' '
                new_notes = notes + 'not interested;'
                row.notes = new_notes
                row.field_edits['notes'] = new_notes

            row.action = 'edit'
            count += 1

    if before_states:
        add_to_undo_stack(
            'change_to_white',
            f'Changed {count} row(s) to Not Interested',
            {'rows': before_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/remove_sent', methods=['POST'])
def api_remove_sent():
    """Remove 'sent' from notes column"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    count = 0
    before_states = []
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.notes:
            # Remove "sent" (case-insensitive)
            new_notes = re.sub(r'\bsent\b', '', row.notes, flags=re.IGNORECASE)
            # Clean up extra semicolons and spaces
            new_notes = re.sub(r';\s*;', ';', new_notes)
            new_notes = re.sub(r'^\s*;\s*', '', new_notes)
            new_notes = re.sub(r'\s*;\s*$', '', new_notes)
            new_notes = re.sub(r'\s+', ' ', new_notes).strip()

            if new_notes != row.notes:
                before_states.append({
                    'row_num': row_num,
                    'fields': {'notes': row.notes, 'action': row.action}
                })
                row.notes = new_notes  # Update actual field
                row.field_edits['notes'] = new_notes  # Track change
                row.action = 'edit'
                count += 1

    if before_states:
        add_to_undo_stack(
            'remove_sent',
            f'Removed "sent" from {count} row(s)',
            {'rows': before_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/mass_invalid', methods=['POST'])
def api_mass_invalid():
    """Mark all rows in network as invalid"""
    data = request.get_json()
    category_id = data.get('category_id')
    reason = data.get('reason', 'INVALID - Network closed')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    count = 0
    before_states = []
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {'action': row.action}
            })
            row.action = 'move_to_invalid'
            row.field_edits['invalid_reason'] = reason
            count += 1

    if before_states:
        add_to_undo_stack(
            'mass_invalid',
            f'Marked {count} row(s) as invalid',
            {'rows': before_states, 'reason': reason}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/get_duplicate_group', methods=['POST'])
def api_get_duplicate_group():
    """Get all rows in a duplicate group for merge UI"""
    data = request.get_json()
    group_id = safe_int(data.get('group_id'), allow_zero=False)
    row_num = safe_int(data.get('row_num'), allow_zero=False)

    # Find group_id from row_num if not provided
    if not group_id and row_num:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            group_id = row.duplicate_group_id

    if not group_id:
        return jsonify({'success': False, 'error': 'No duplicate group specified'}), 400

    # Get all rows in this group
    group_rows = [r for r in state.wl_rows if r.duplicate_group_id == group_id]

    if len(group_rows) < 2:
        return jsonify({'success': False, 'error': 'Not enough rows in group'}), 400

    return jsonify({
        'success': True,
        'group_id': group_id,
        'rows': [r.to_dict() for r in group_rows]
    })

@app.route('/api/merge_rows', methods=['POST'])
def api_merge_rows():
    """
    Merge duplicate rows into a survivor.
    - survivor_row_num: Row that will keep existing
    - other_row_nums: Rows to merge into survivor then delete
    - merge_fields: Optional dict of field -> row_num to take value from
    """
    data = request.get_json()
    survivor_row_num = safe_int(data.get('survivor_row_num'), allow_zero=False)
    other_row_nums = safe_int_list(data.get('other_row_nums', []))
    merge_fields = {k: safe_int(v, allow_zero=False) for k, v in data.get('merge_fields', {}).items() if safe_int(v, allow_zero=False) is not None}

    if not survivor_row_num:
        return jsonify({'success': False, 'error': 'No survivor row specified'}), 400

    if not other_row_nums:
        return jsonify({'success': False, 'error': 'No rows to merge'}), 400

    # Find survivor row
    survivor = next((r for r in state.wl_rows if r.row_num == survivor_row_num), None)
    if not survivor:
        return jsonify({'success': False, 'error': 'Survivor row not found'}), 404

    # Find other rows
    others = [r for r in state.wl_rows if r.row_num in other_row_nums]
    if not others:
        return jsonify({'success': False, 'error': 'No other rows found'}), 404

    # Store before states for undo
    before_states = [{
        'row_num': survivor.row_num,
        'fields': {
            'practice': survivor.practice, 'phone': survivor.phone,
            'address': survivor.address, 'city': survivor.city,
            'state': survivor.state, 'zip': survivor.zip,
            'notes': survivor.notes, 'action': survivor.action
        }
    }]
    for other in others:
        before_states.append({
            'row_num': other.row_num,
            'fields': {'action': other.action}
        })

    # Apply field merges from specific rows
    for field, source_row_num in merge_fields.items():
        source = next((r for r in state.wl_rows if r.row_num == source_row_num), None)
        if source and hasattr(survivor, field):
            value = getattr(source, field, '')
            setattr(survivor, field, value)
            survivor.field_edits[field] = value

    # Merge notes from all rows (combine unique chunks)
    all_notes = set()
    if survivor.notes:
        all_notes.update(c.strip() for c in survivor.notes.split(';') if c.strip())
    for other in others:
        if other.notes:
            all_notes.update(c.strip() for c in other.notes.split(';') if c.strip())

    if all_notes:
        merged_notes = '; '.join(sorted(all_notes))
        survivor.notes = merged_notes
        survivor.field_edits['notes'] = merged_notes

    survivor.action = 'merged_survivor'

    # Mark others as deleted
    for other in others:
        other.action = 'merged_deleted'

    add_to_undo_stack(
        'merge_rows',
        f'Merged {len(others) + 1} rows (survivor: #{survivor_row_num})',
        {'rows': before_states, 'survivor_row_num': survivor_row_num, 'other_row_nums': other_row_nums}
    )

    return jsonify({
        'success': True,
        'survivor_row_num': survivor_row_num,
        'deleted_count': len(others)
    })

@app.route('/api/get_network_group', methods=['POST'])
def api_get_network_group():
    """Get all rows in a network for confirm_network UI"""
    data = request.get_json()
    row_num = safe_int(data.get('row_num'), allow_zero=False)

    if not row_num:
        return jsonify({'success': False, 'error': 'No row number provided'}), 400

    # Find the row and its network_name
    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
    if not row or not row.network_name:
        return jsonify({'success': False, 'error': 'Row is not part of a network'}), 400

    network_name = row.network_name

    # Get all rows with the same network_name
    network_rows = [r for r in state.wl_rows if r.network_name == network_name]

    # Auto-derive a better network name from common words
    suggested_name = derive_network_name(network_rows)

    return jsonify({
        'success': True,
        'network_name': network_name,
        'suggested_name': suggested_name,
        'rows': [r.to_dict() for r in network_rows]
    })

def derive_network_name(rows):
    """
    Derive a readable network name from common practice name words.
    E.g., "Downtown Medical", "Uptown Medical" -> "Medical"
    """
    if not rows:
        return "Unknown Network"

    # Get words from all practice names, excluding common suffixes
    exclude_words = {'the', 'of', 'and', 'at', 'in', 'for', 'a', 'an',
                     'north', 'south', 'east', 'west', 'downtown', 'uptown',
                     'medical', 'clinic', 'center', 'office', 'health',
                     'healthcare', 'care', 'group', 'associates', 'llc', 'pc', 'md'}

    word_lists = []
    for r in rows:
        words = set(w.lower() for w in re.split(r'\W+', r.practice) if len(w) > 2)
        word_lists.append(words)

    # Find common words across all practices
    if word_lists:
        common = word_lists[0].copy()
        for wl in word_lists[1:]:
            common &= wl

        # Remove excluded words
        meaningful = common - exclude_words

        if meaningful:
            # Return the longest meaningful word, capitalized
            best_word = max(meaningful, key=len)
            return best_word.title() + " Network"

    # Fallback: use first practice name
    first_name = rows[0].practice.split()[0] if rows[0].practice else "Unknown"
    return first_name + " Network"

@app.route('/api/confirm_network', methods=['POST'])
def api_confirm_network():
    """
    Confirm rows as a network.
    - network_name: The name for this network
    - row_nums: Rows to include in the network (or use category_id)
    - category_id: Alternative to row_nums - get all rows from category
    - add_note: Optional note to add to all rows
    """
    data = request.get_json()
    network_name = data.get('network_name', 'Confirmed Network')
    row_nums = safe_int_list(data.get('row_nums', []))
    category_id = data.get('category_id')
    add_note = data.get('add_note', '')

    # If category_id provided, get row_nums from category
    if not row_nums and category_id:
        category = next((c for c in state.categories if c.id == category_id), None)
        if category:
            row_nums = category.row_nums

    if not row_nums:
        return jsonify({'success': False, 'error': 'No rows specified'}), 400

    count = 0
    before_states = []

    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {
                    'network_name': row.network_name,
                    'notes': row.notes,
                    'action': row.action
                }
            })

            # Update network name
            row.network_name = network_name
            row.field_edits['network_name'] = network_name

            # Add note if provided
            if add_note:
                current_notes = row.notes or ""
                if add_note.lower() not in current_notes.lower():
                    if current_notes and not current_notes.endswith(';'):
                        current_notes += '; '
                    elif current_notes:
                        current_notes += ' '
                    row.notes = current_notes + add_note
                    row.field_edits['notes'] = row.notes

            row.action = 'network_confirmed'
            count += 1

    # Remove from networks category since confirmed
    networks_cat = next((c for c in state.categories if c.id == 'networks'), None)
    if networks_cat:
        for row_num in row_nums:
            if row_num in networks_cat.row_nums:
                networks_cat.row_nums.remove(row_num)

    if before_states:
        add_to_undo_stack(
            'confirm_network',
            f'Confirmed {count} row(s) as "{network_name}"',
            {'rows': before_states, 'network_name': network_name}
        )

    return jsonify({
        'success': True,
        'count': count,
        'network_name': network_name
    })

@app.route('/api/send_to_manual_review', methods=['POST'])
def api_send_to_manual_review():
    """Send row(s) to Manual Review category for closer inspection"""
    data = request.get_json()
    row_nums = safe_int_list(data.get('row_nums', []))
    reason = data.get('reason', 'Needs manual review')

    if not row_nums:
        return jsonify({'success': False, 'error': 'No row numbers provided'}), 400

    # Find or create manual_review category
    manual_review_cat = next((c for c in state.categories if c.id == 'manual_review'), None)
    if not manual_review_cat:
        # Create it if it doesn't exist (e.g., was filtered out as empty)
        manual_review_cat = ReviewCategory(
            id="manual_review",
            name="Manual Review",
            description="Complex cases requiring engineer judgment",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["edit", "delete", "change_status", "move_to_invalid",
                             "merge", "add_vm_note", "mark_reviewed", "keep_as_is"]
        )
        state.categories.append(manual_review_cat)

    count = 0
    before_states = []
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row_num not in manual_review_cat.row_nums:
            before_states.append({
                'row_num': row_num,
                'fields': {'practice': row.practice, 'status': row.status, 'notes': row.notes}
            })
            manual_review_cat.row_nums.append(row_num)
            # Add issue to row
            row.issues.append({
                'category': 'manual_review',
                'severity': 'review',
                'message': reason
            })
            count += 1

    manual_review_cat.row_nums.sort()

    if before_states:
        add_to_undo_stack(
            'send_to_manual_review',
            f'Sent {count} row(s) to Manual Review',
            {'rows': before_states, 'reason': reason}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/mark_reviewed', methods=['POST'])
def api_mark_reviewed():
    """Mark row as reviewed (no changes needed) for progress tracking"""
    data = request.get_json()
    row_nums = safe_int_list(data.get('row_nums', []))

    if not row_nums:
        return jsonify({'success': False, 'error': 'No row numbers provided'}), 400

    count = 0
    before_states = []
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {'action': row.action}
            })
            row.action = 'reviewed_no_change'
            count += 1

    if before_states:
        add_to_undo_stack(
            'mark_reviewed',
            f'Marked {count} row(s) as reviewed',
            {'rows': before_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/edit_field', methods=['POST'])
def api_edit_field():
    """
    Edit a single field of a row.
    Used for inline editing (double-click to edit).
    """
    data = request.get_json()
    row_num = safe_int(data.get('row_num'), allow_zero=False)
    field = data.get('field')
    value = data.get('value', '')

    if not row_num or not field:
        return jsonify({'success': False, 'error': 'Missing row_num or field'}), 400

    # Find the row
    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
    if not row:
        return jsonify({'success': False, 'error': 'Row not found'}), 404

    # Editable fields
    editable_fields = ['practice', 'phone', 'address', 'city', 'state', 'zip', 'status', 'notes', 'qty_2025']

    if field not in editable_fields:
        return jsonify({'success': False, 'error': f'Field {field} is not editable'}), 400

    # Store before state for undo
    old_value = getattr(row, field, '')
    before_state = {
        'row_num': row_num,
        'field': field,
        'old_value': old_value
    }

    # Update the field
    setattr(row, field, value)

    # If status changed, update bg_color
    if field == 'status':
        row.bg_color = status_to_color(value)

    # Track field edit
    row.field_edits[field] = value
    row.action = 'edited'

    add_to_undo_stack(
        'edit_field',
        f'Changed {field} on row #{row_num}',
        before_state,
        {'row_num': row_num, 'field': field, 'new_value': value}
    )

    return jsonify({
        'success': True,
        'row_num': row_num,
        'field': field,
        'value': value,
        'bg_color': row.bg_color if field == 'status' else None
    })

@app.route('/api/match_orphan_to_invalid', methods=['POST'])
def api_match_orphan_to_invalid():
    """
    Match an orphan New Order row against the Invalid/Inactive List.
    Returns match info if found (≥80% confidence) or suggests manual review.
    """
    data = request.get_json()
    row_num = safe_int(data.get('row_num'), allow_zero=False)

    if not row_num:
        return jsonify({'success': False, 'error': 'No row number provided'}), 400

    # Find the orphan NO row
    no_row = next((r for r in state.no_rows if r.row_num == row_num and r.is_orphan), None)
    if not no_row:
        return jsonify({'success': False, 'error': 'Orphan row not found'}), 404

    # Fuzzy match against Invalid/Inactive List
    best_match = None
    best_score = 0.0

    for inv_row in state.invalid_rows:
        # Skip if different state
        if inv_row.state and no_row.state and inv_row.state.lower() != no_row.state.lower():
            continue

        # Calculate weighted match score (70% name, 30% address)
        name_score = fuzz.token_set_ratio(
            normalize_name(no_row.practice),
            normalize_name(inv_row.practice)
        ) / 100.0

        address_score = fuzz.token_set_ratio(
            normalize_address(no_row.address + ' ' + no_row.city),
            normalize_address(inv_row.address + ' ' + inv_row.city)
        ) / 100.0

        combined_score = (name_score * 0.7) + (address_score * 0.3)

        if combined_score > best_score:
            best_score = combined_score
            best_match = inv_row

    result = {
        'orphan_row': no_row.to_dict(),
        'match_found': best_score >= 0.80,
        'match_confidence': round(best_score * 100, 1)
    }

    if best_match and best_score >= 0.80:
        result['matched_invalid'] = best_match.to_dict()
        result['recommendation'] = 'confirm_match'
        result['message'] = f"Matches invalid provider: {best_match.practice}. Reason: {best_match.reason or 'Not specified'}"
    else:
        result['recommendation'] = 'manual_review'
        result['message'] = "No match found in Invalid/Inactive List. Send to Manual Review."

    return jsonify({'success': True, **result})

@app.route('/api/process_orphan_batch', methods=['POST'])
def api_process_orphan_batch():
    """
    Process all orphan NO rows at once, matching against Invalid List.
    Returns categorized results for bulk handling.
    """
    # Get all orphan rows
    orphan_rows = [r for r in state.no_rows if r.is_orphan]

    results = {
        'matched': [],      # Found in Invalid List (≥80% match)
        'unmatched': [],    # No match - need manual review
        'total': len(orphan_rows)
    }

    for no_row in orphan_rows:
        best_match = None
        best_score = 0.0

        for inv_row in state.invalid_rows:
            # Skip if different state
            if inv_row.state and no_row.state and inv_row.state.lower() != no_row.state.lower():
                continue

            # Calculate weighted match score
            name_score = fuzz.token_set_ratio(
                normalize_name(no_row.practice),
                normalize_name(inv_row.practice)
            ) / 100.0

            address_score = fuzz.token_set_ratio(
                normalize_address(no_row.address + ' ' + no_row.city),
                normalize_address(inv_row.address + ' ' + inv_row.city)
            ) / 100.0

            combined_score = (name_score * 0.7) + (address_score * 0.3)

            if combined_score > best_score:
                best_score = combined_score
                best_match = inv_row

        if best_match and best_score >= 0.80:
            results['matched'].append({
                'orphan': no_row.to_dict(),
                'invalid_match': best_match.to_dict(),
                'confidence': round(best_score * 100, 1)
            })
        else:
            results['unmatched'].append({
                'orphan': no_row.to_dict(),
                'best_score': round(best_score * 100, 1) if best_score > 0 else 0
            })

    return jsonify({'success': True, **results})

@app.route('/api/confirm_orphan_match', methods=['POST'])
def api_confirm_orphan_match():
    """
    Confirm that an orphan NO row matches an Invalid List entry.
    Marks the orphan as resolved (explained by invalid provider).
    """
    data = request.get_json()
    orphan_row_num = safe_int(data.get('orphan_row_num'), allow_zero=False)
    invalid_row_num = safe_int(data.get('invalid_row_num'), allow_zero=False)
    action = data.get('action', 'confirm')  # 'confirm' or 'reject'

    if not orphan_row_num:
        return jsonify({'success': False, 'error': 'No orphan row number provided'}), 400

    # Find the orphan
    no_row = next((r for r in state.no_rows if r.row_num == orphan_row_num), None)
    if not no_row:
        return jsonify({'success': False, 'error': 'Orphan row not found'}), 404

    if action == 'confirm':
        # Mark orphan as resolved (matched to invalid)
        no_row.is_orphan = False  # No longer orphan - explained
        inv_row = next((r for r in state.invalid_rows if r.row_num == invalid_row_num), None)
        reason = inv_row.reason if inv_row else 'Matched to Invalid List'

        # Remove from orphan_no category
        orphan_cat = next((c for c in state.categories if c.id == 'orphan_no'), None)
        if orphan_cat and orphan_row_num in orphan_cat.row_nums:
            orphan_cat.row_nums.remove(orphan_row_num)

        add_to_undo_stack(
            'confirm_orphan_match',
            f'Confirmed orphan #{orphan_row_num} matches invalid provider',
            {'orphan_row_num': orphan_row_num, 'invalid_row_num': invalid_row_num}
        )

        return jsonify({
            'success': True,
            'message': f'Confirmed match. Reason: {reason}'
        })
    else:
        # Reject match - send to manual review
        manual_review_cat = next((c for c in state.categories if c.id == 'manual_review'), None)
        if manual_review_cat and orphan_row_num not in manual_review_cat.row_nums:
            manual_review_cat.row_nums.append(orphan_row_num)
            manual_review_cat.row_nums.sort()

        return jsonify({
            'success': True,
            'message': 'Sent to Manual Review for further investigation'
        })

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def open_browser():
    """Open browser after short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EOY Cleanup Tool')
    parser.add_argument('--assume-yes', action='store_true', help='Automatically answer yes to prompts')
    args = parser.parse_args()

    print("\n" + "="*80)
    print("EOY Cleanup Tool - Starting...")
    if args.assume_yes:
        print("Mode: AUTOMATED (Input prompts disabled)")
    print("="*80)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Flask app
    app.run(debug=True, use_reloader=False, port=5000)
