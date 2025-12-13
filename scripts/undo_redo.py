"""
Undo/Redo system for EOY Cleanup Tool

Manages action stack, state restoration, and progress calculation.
"""

from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from helpers import status_to_color

if TYPE_CHECKING:
    from state import AppState


def add_to_undo_stack(state: AppState, action_type: str, description: str,
                      before_state: Any, after_state: Any = None):
    """Add action to undo stack"""
    action = {
        'id': len(state.undo_stack) + 1,
        'timestamp': datetime.now().isoformat(),
        'action_type': action_type,
        'description': description,
        'before_state': before_state,
        'after_state': after_state
    }

    state.undo_stack.append(action)
    state.redo_stack.clear()  # Clear redo stack when new action added

    # Keep only last 50 actions
    if len(state.undo_stack) > 50:
        state.undo_stack.pop(0)

    # Save to disk
    save_undo_log(state)


def save_undo_log(state: AppState):
    """Save undo stack to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Save to data/undo-logs folder
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'undo-logs')
    os.makedirs(log_dir, exist_ok=True)
    filename = os.path.join(log_dir, f"eoy_undo_log_{timestamp}.json")

    with open(filename, 'w') as f:
        json.dump({
            'actions': state.undo_stack,
            'current_position': len(state.undo_stack)
        }, f, indent=2)


def save_progress(state: AppState) -> str:
    """Save current progress to JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eoy_progress_{timestamp}.json"

    progress = state.to_dict()
    progress['saved_at'] = timestamp

    with open(filename, 'w') as f:
        json.dump(progress, f, indent=2)

    print(f"Progress saved to {filename}")
    return filename


def calculate_progress(state: AppState) -> Dict:
    """
    Calculate progress counts by urgency level.
    Returns dict with counts for critical, review, verify, and resolved.
    """
    # Define urgency levels
    CRITICAL = {'exact_dupes', 'yellow_low', 'orphan_no', 'red_invalid'}
    REVIEW = {'networks', 'fuzzy_dupes', 'yellow_80', 'green_sent', 'not_interested_invalid',
              'address_cluster', 'notes_archive_ni'}  # Address clusters and NI reasons need review
    VERIFY = {'yellow_95', 'fuschia_vm', 'manual_review',
              'notes_remove', 'notes_transform', 'notes_fix_semicolons'}  # Auto-fix note patterns

    counts = {
        'critical_total': 0,
        'critical_resolved': 0,
        'review_total': 0,
        'review_resolved': 0,
        'verify_total': 0,
        'verify_resolved': 0,
    }

    # Track which rows we've already counted (for multi-category rows)
    # Use highest urgency for each row
    row_urgency = {}  # row_num -> urgency level

    for cat in state.categories:
        if cat.id in CRITICAL:
            urgency = 'critical'
            priority = 3
        elif cat.id in REVIEW:
            urgency = 'review'
            priority = 2
        elif cat.id in VERIFY:
            urgency = 'verify'
            priority = 1
        else:
            continue  # Unknown category

        for row_num in cat.row_nums:
            # Only count in highest urgency category
            current = row_urgency.get(row_num)
            if current is None or priority > current[1]:
                row_urgency[row_num] = (urgency, priority)

    # Now count by urgency
    for row_num, (urgency, _) in row_urgency.items():
        counts[f'{urgency}_total'] += 1

        # Check if resolved (has action taken)
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.action:
            counts[f'{urgency}_resolved'] += 1

    # Calculate totals and percentages
    total = counts['critical_total'] + counts['review_total'] + counts['verify_total']
    resolved = counts['critical_resolved'] + counts['review_resolved'] + counts['verify_resolved']

    counts['total'] = total
    counts['resolved'] = resolved
    counts['percent'] = round((resolved / total * 100) if total > 0 else 0, 1)

    # Calculate segment widths for the progress bar
    if total > 0:
        counts['critical_width'] = round(counts['critical_total'] / total * 100, 1)
        counts['review_width'] = round(counts['review_total'] / total * 100, 1)
        counts['verify_width'] = round(counts['verify_total'] / total * 100, 1)
    else:
        counts['critical_width'] = 0
        counts['review_width'] = 0
        counts['verify_width'] = 0

    return counts


def restore_state(state: AppState, action: Dict, direction: str = 'undo') -> bool:
    """
    Restore state based on action type.
    direction: 'undo' restores before_state, 'redo' restores after_state
    Returns True if restoration was successful.
    """
    action_type = action.get('action_type')
    before_state_data = action.get('before_state', {})
    after_state_data = action.get('after_state', {})

    # Choose which state to restore
    target_state = before_state_data if direction == 'undo' else after_state_data

    try:
        if action_type == 'edit_field':
            # Single field edit
            row_num = target_state.get('row_num') if direction == 'undo' else after_state_data.get('row_num')
            row = next((r for r in state.wl_rows if r.row_num == row_num), None)
            if row:
                if direction == 'undo':
                    field = target_state.get('field')
                    old_value = target_state.get('old_value', '')
                    setattr(row, field, old_value)
                    if field == 'status':
                        row.bg_color = status_to_color(old_value)
                else:
                    field = after_state_data.get('field')
                    new_value = after_state_data.get('new_value', '')
                    setattr(row, field, new_value)
                    if field == 'status':
                        row.bg_color = status_to_color(new_value)
            return True

        elif action_type in ['delete', 'delete_rows']:
            # Row deletion - restore or re-delete
            rows_data = before_state_data.get('rows', [])
            for row_data in rows_data:
                row_num = row_data.get('row_num')
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                if row:
                    if direction == 'undo':
                        # Restore deleted row
                        row.action = row_data.get('fields', {}).get('action', None)
                    else:
                        # Re-delete
                        row.action = 'deleted'
            return True

        elif action_type == 'mark_reviewed':
            rows_data = before_state_data.get('rows', [])
            for row_data in rows_data:
                row_num = row_data.get('row_num')
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                if row:
                    if direction == 'undo':
                        # Restore original action
                        row.action = row_data.get('fields', {}).get('action', None)
                    else:
                        row.action = 'reviewed_no_change'
            return True

        elif action_type == 'send_to_manual_review':
            rows_data = before_state_data.get('rows', [])
            manual_review_cat = next((c for c in state.categories if c.id == 'manual_review'), None)

            for row_data in rows_data:
                row_num = row_data.get('row_num')
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)

                if direction == 'undo':
                    # Remove from manual review
                    if manual_review_cat and row_num in manual_review_cat.row_nums:
                        manual_review_cat.row_nums.remove(row_num)
                    # Remove manual_review issue
                    if row:
                        row.issues = [i for i in row.issues if i.get('category') != 'manual_review']
                else:
                    # Re-add to manual review
                    if manual_review_cat and row_num not in manual_review_cat.row_nums:
                        manual_review_cat.row_nums.append(row_num)
            return True

        elif action_type == 'confirm_orphan_match':
            orphan_row_num = before_state_data.get('orphan_row_num')
            no_row = next((r for r in state.no_rows if r.row_num == orphan_row_num), None)
            orphan_cat = next((c for c in state.categories if c.id == 'orphan_no'), None)

            if no_row:
                if direction == 'undo':
                    # Restore orphan status
                    no_row.is_orphan = True
                    if orphan_cat and orphan_row_num not in orphan_cat.row_nums:
                        orphan_cat.row_nums.append(orphan_row_num)
                else:
                    no_row.is_orphan = False
                    if orphan_cat and orphan_row_num in orphan_cat.row_nums:
                        orphan_cat.row_nums.remove(orphan_row_num)
            return True

        elif action_type in ['keep_first_delete_rest', 'accept_all', 'batch_action',
                              'change_status', 'change_to_white', 'remove_sent', 'mass_invalid',
                              'merge_rows', 'confirm_network', 'delete_rows']:
            # Bulk actions - restore all affected rows
            if direction == 'undo':
                rows_data = before_state_data.get('rows', [])
                for row_data in rows_data:
                    row_num = row_data.get('row_num')
                    fields = row_data.get('fields', {})
                    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                    if row:
                        for field, value in fields.items():
                            if hasattr(row, field):
                                setattr(row, field, value)
                        # Clear field_edits that were set by the action
                        row.field_edits = {}
            else:
                # Redo: apply after_state values
                rows_data = after_state_data.get('rows', [])
                for row_data in rows_data:
                    row_num = row_data.get('row_num')
                    fields = row_data.get('fields', {})
                    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                    if row:
                        for field, value in fields.items():
                            if hasattr(row, field):
                                setattr(row, field, value)
                        # Update field_edits to reflect the change
                        row.field_edits.update(fields)
            return True

        else:
            # Unknown action type - log but don't fail
            print(f"[Undo/Redo] Unknown action type: {action_type}")
            return True

    except Exception as e:
        print(f"[Undo/Redo] Error restoring state: {e}")
        return False
