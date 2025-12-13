"""
Test undo/redo state management system

Tests the undo stack, redo stack, and state snapshot functionality.
Critical for allowing users to safely experiment and roll back changes.
"""

import pytest
from datetime import datetime

# Import from modules
from models import ProviderRow
from state import AppState, state
from eoy_tool import add_to_undo_stack  # Uses wrapper that passes state


class TestUndoStackBasics:
    """Test basic undo stack functionality"""

    def test_add_to_undo_stack_creates_action(self):
        """Adding action should create action record"""
        # Clear global state
        state.undo_stack = []
        state.redo_stack = []

        before = {'row_num': 45, 'status': 'Successful Order'}
        after = {'row_num': 45, 'status': 'Not interested'}

        add_to_undo_stack(
            action_type='edit',
            description='Changed status',
            before_state=before,
            after_state=after
        )

        assert len(state.undo_stack) == 1
        action = state.undo_stack[0]

        assert action['action_type'] == 'edit'
        assert action['description'] == 'Changed status'
        assert action['before_state'] == before
        assert action['after_state'] == after
        assert 'timestamp' in action
        assert 'id' in action

    def test_undo_stack_assigns_sequential_ids(self):
        """Actions should get sequential IDs"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack('edit', 'Action 1', {}, {})
        add_to_undo_stack('edit', 'Action 2', {}, {})
        add_to_undo_stack('edit', 'Action 3', {}, {})

        assert state.undo_stack[0]['id'] == 1
        assert state.undo_stack[1]['id'] == 2
        assert state.undo_stack[2]['id'] == 3

    def test_undo_stack_has_timestamp(self):
        """Actions should have ISO format timestamp"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack('edit', 'Test action', {}, {})

        timestamp_str = state.undo_stack[0]['timestamp']

        # Should be ISO format (parseable)
        timestamp = datetime.fromisoformat(timestamp_str)
        assert isinstance(timestamp, datetime)

    def test_new_action_clears_redo_stack(self):
        """Adding new action should clear redo stack"""
        state.undo_stack = []
        state.redo_stack = [
            {'id': 1, 'action_type': 'edit', 'description': 'Old action'},
            {'id': 2, 'action_type': 'edit', 'description': 'Old action 2'}
        ]

        # Add new action
        add_to_undo_stack('edit', 'New action', {}, {})

        # Redo stack should be cleared
        assert len(state.redo_stack) == 0


class TestUndoStackLimits:
    """Test undo stack size limits"""

    def test_undo_stack_keeps_last_50_actions(self):
        """Undo stack should only keep last 50 actions"""
        state.undo_stack = []
        state.redo_stack = []

        # Add 60 actions
        for i in range(60):
            add_to_undo_stack('edit', f'Action {i}', {'num': i}, {'num': i+1})

        # Should only keep last 50
        assert len(state.undo_stack) <= 50

        # Should have actions 10-59 (oldest 0-9 dropped)
        if len(state.undo_stack) == 50:
            # First action should be action 10
            assert state.undo_stack[0]['before_state']['num'] >= 10

    def test_undo_stack_oldest_dropped_first(self):
        """When exceeding limit, oldest actions should be dropped"""
        state.undo_stack = []
        state.redo_stack = []

        # Add 55 actions
        for i in range(55):
            add_to_undo_stack('edit', f'Action {i}', {'num': i}, {'num': i+1})

        # Last action should still be present
        last_action = state.undo_stack[-1]
        assert last_action['before_state']['num'] == 54


class TestUndoStackStateSerialization:
    """Test state serialization for undo"""

    def test_undo_stack_in_state_dict(self):
        """State.to_dict() should include undo_stack"""
        state = AppState()
        state.undo_stack = [
            {'id': 1, 'action_type': 'edit', 'description': 'Test', 'before_state': {}, 'after_state': {}}
        ]
        state.redo_stack = []
        state.wl_rows = []
        state.no_rows = []
        state.categories = []
        state.invalid_reasons = set()

        state_dict = state.to_dict()

        assert 'undo_stack' in state_dict
        assert len(state_dict['undo_stack']) == 1

    def test_state_dict_limits_undo_to_50(self):
        """State.to_dict() should only include last 50 undo actions"""
        state = AppState()
        state.undo_stack = [
            {'id': i, 'action_type': 'edit', 'description': f'Action {i}'}
            for i in range(60)
        ]
        state.redo_stack = []
        state.wl_rows = []
        state.no_rows = []
        state.categories = []
        state.invalid_reasons = set()

        state_dict = state.to_dict()

        # Should only include last 50
        assert len(state_dict['undo_stack']) == 50


class TestRedoStack:
    """Test redo stack management"""

    def test_undo_moves_action_to_redo_stack(self):
        """Undo should move action from undo to redo stack"""
        state = AppState()
        state.undo_stack = [
            {'id': 1, 'action_type': 'edit', 'description': 'Test action',
             'before_state': {'status': 'old'}, 'after_state': {'status': 'new'},
             'timestamp': datetime.now().isoformat()}
        ]
        state.redo_stack = []

        # Simulate undo (Flask route would do this)
        action = state.undo_stack.pop()
        state.redo_stack.append(action)

        # Should move to redo stack
        assert len(state.undo_stack) == 0
        assert len(state.redo_stack) == 1
        assert state.redo_stack[0]['description'] == 'Test action'

    def test_redo_moves_action_back_to_undo_stack(self):
        """Redo should move action from redo to undo stack"""
        state = AppState()
        state.undo_stack = []
        state.redo_stack = [
            {'id': 1, 'action_type': 'edit', 'description': 'Test action',
             'before_state': {'status': 'old'}, 'after_state': {'status': 'new'},
             'timestamp': datetime.now().isoformat()}
        ]

        # Simulate redo (Flask route would do this)
        action = state.redo_stack.pop()
        state.undo_stack.append(action)

        # Should move back to undo stack
        assert len(state.redo_stack) == 0
        assert len(state.undo_stack) == 1
        assert state.undo_stack[0]['description'] == 'Test action'

    def test_multiple_undo_redo_cycle(self):
        """Should support multiple undo/redo operations"""
        state = AppState()
        state.undo_stack = [
            {'id': 1, 'action_type': 'edit', 'description': 'Action 1',
             'before_state': {}, 'after_state': {}, 'timestamp': datetime.now().isoformat()},
            {'id': 2, 'action_type': 'edit', 'description': 'Action 2',
             'before_state': {}, 'after_state': {}, 'timestamp': datetime.now().isoformat()},
            {'id': 3, 'action_type': 'edit', 'description': 'Action 3',
             'before_state': {}, 'after_state': {}, 'timestamp': datetime.now().isoformat()}
        ]
        state.redo_stack = []

        # Undo twice
        state.redo_stack.append(state.undo_stack.pop())  # Action 3
        state.redo_stack.append(state.undo_stack.pop())  # Action 2

        assert len(state.undo_stack) == 1
        assert len(state.redo_stack) == 2

        # Redo once
        state.undo_stack.append(state.redo_stack.pop())  # Action 2

        assert len(state.undo_stack) == 2
        assert len(state.redo_stack) == 1

        # Undo all
        state.redo_stack.append(state.undo_stack.pop())  # Action 2
        state.redo_stack.append(state.undo_stack.pop())  # Action 1

        assert len(state.undo_stack) == 0
        assert len(state.redo_stack) == 3


class TestActionTypes:
    """Test different action types"""

    def test_edit_action_type(self):
        """Edit actions should store field changes"""
        state.undo_stack = []
        state.redo_stack = []

        before = {
            'row_num': 45,
            'status': 'Successful Order',
            'notes': 'ordered 2025'
        }
        after = {
            'row_num': 45,
            'status': 'Not interested',
            'notes': 'ordered 2025; not interested'
        }

        add_to_undo_stack('edit', 'Changed status to Not interested', before, after)

        action = state.undo_stack[0]
        assert action['action_type'] == 'edit'
        assert action['before_state']['status'] != action['after_state']['status']

    def test_delete_action_type(self):
        """Delete actions should store deleted row state"""
        state.undo_stack = []
        state.redo_stack = []

        deleted_row = {
            'row_num': 100,
            'practice': 'Test Practice',
            'status': 'Duplicate'
        }

        add_to_undo_stack('delete', 'Deleted duplicate row 100', deleted_row, None)

        action = state.undo_stack[0]
        assert action['action_type'] == 'delete'
        assert action['before_state'] == deleted_row
        assert action['after_state'] is None

    def test_batch_action_type(self):
        """Batch actions should store multiple row changes"""
        state.undo_stack = []
        state.redo_stack = []

        before = [
            {'row_num': 45, 'status': 'Successful Order'},
            {'row_num': 67, 'status': 'Successful Order'},
            {'row_num': 89, 'status': 'Successful Order'}
        ]
        after = [
            {'row_num': 45, 'status': 'Not interested'},
            {'row_num': 67, 'status': 'Not interested'},
            {'row_num': 89, 'status': 'Not interested'}
        ]

        add_to_undo_stack('batch_edit', 'Batch changed 3 rows to Not interested', before, after)

        action = state.undo_stack[0]
        assert action['action_type'] == 'batch_edit'
        assert len(action['before_state']) == 3
        assert len(action['after_state']) == 3


class TestEdgeCases:
    """Test edge cases in undo/redo"""

    def test_empty_undo_stack_cannot_undo(self):
        """Cannot undo when stack is empty"""
        state.undo_stack = []
        state.redo_stack = []

        # Should not be able to pop from empty stack
        can_undo = len(state.undo_stack) > 0
        assert can_undo is False

    def test_empty_redo_stack_cannot_redo(self):
        """Cannot redo when stack is empty"""
        state.undo_stack = []
        state.redo_stack = []

        # Should not be able to pop from empty stack
        can_redo = len(state.redo_stack) > 0
        assert can_redo is False

    def test_undo_without_after_state(self):
        """Some actions may not have after_state (e.g., delete)"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack('delete', 'Deleted row', {'row_num': 100}, None)

        action = state.undo_stack[0]
        assert action['after_state'] is None

    def test_action_description_required(self):
        """All actions should have human-readable description"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack('edit', 'User-friendly description', {}, {})

        action = state.undo_stack[0]
        assert action['description'] == 'User-friendly description'
        assert len(action['description']) > 0


class TestStateRestoration:
    """Test state restoration logic (when implemented)"""

    def test_restoration_structure_before_state(self):
        """Before_state should have structure for restoration"""
        # This tests the data structure, not restoration logic itself
        before = {
            'row_num': 45,
            'practice': "Women's Health Specialists",
            'status': 'Successful Order',
            'notes': 'ordered 2025',
            'qty_2025': '50',
            'bg_color': '#ffff00'
        }

        # Should have all necessary fields for restoration
        assert 'row_num' in before  # Which row to restore
        assert 'status' in before   # What values to restore
        assert 'notes' in before
        assert 'qty_2025' in before

    def test_restoration_structure_after_state(self):
        """After_state should have structure for redo"""
        after = {
            'row_num': 45,
            'status': 'Not interested',
            'notes': 'ordered 2025; not interested',
            'qty_2025': '0',
            'bg_color': '#ffffff'
        }

        # Should have all necessary fields for redo
        assert 'row_num' in after
        assert 'status' in after
        assert 'notes' in after
        assert 'qty_2025' in after


class TestUndoRedoWithRealData:
    """Test undo/redo with realistic data from fixtures"""

    def test_undo_status_change(self, undo_test_state):
        """Test undo of status change using fixture data"""
        state.undo_stack = []
        state.redo_stack = []

        before = undo_test_state['before']
        after = undo_test_state['after_edit']

        add_to_undo_stack('edit', 'Changed status to Not interested', before, after)

        # Should record the change
        action = state.undo_stack[0]
        assert action['before_state']['status'] == 'Successful Order'
        assert action['after_state']['status'] == 'Not interested'

        # Undo would restore before_state
        assert action['before_state']['qty_2025'] == '50'
        assert action['after_state']['qty_2025'] == '0'

    def test_undo_preserves_all_fields(self):
        """Undo should preserve all modified fields"""
        state.undo_stack = []
        state.redo_stack = []

        before = {
            'row_num': 45,
            'practice': "Women's Health Specialists",
            'phone': '555-123-4567',
            'address': '123 Main St Suite 200',
            'city': 'Austin',
            'state': 'TX',
            'zip': '78701',
            'qty_2023': '50',
            'qty_2024': '50',
            'qty_2025': '50',
            'status': 'Successful Order',
            'notes': 'ordered 2025',
            'bg_color': '#ffff00'
        }

        after = dict(before)
        after['status'] = 'Not interested'
        after['notes'] = 'ordered 2025; not interested'
        after['qty_2025'] = '0'
        after['bg_color'] = '#ffffff'

        add_to_undo_stack('edit', 'Status change', before, after)

        action = state.undo_stack[0]

        # All fields should be preserved
        assert action['before_state']['practice'] == "Women's Health Specialists"
        assert action['before_state']['phone'] == '555-123-4567'
        assert action['after_state']['status'] == 'Not interested'


class TestRestoreState:
    """Test the actual state restoration logic"""

    def test_restore_state_edit_field_undo(self):
        """Undo should restore field to before_state value"""
        from undo_redo import restore_state

        # Create a test state with a row
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=45, practice="Test Practice", phone="555-123-4567",
                address="123 Main St", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="50",
                status="Not interested",  # Current state
                notes="changed", bg_color="#ffffff"
            )
        ]

        action = {
            'action_type': 'edit_field',
            'before_state': {
                'row_num': 45,
                'field': 'status',
                'old_value': 'Successful Order'  # What to restore to
            },
            'after_state': {
                'row_num': 45,
                'field': 'status',
                'new_value': 'Not interested'
            }
        }

        # Perform undo
        success = restore_state(test_state, action, 'undo')
        assert success is True

        # Verify the row was actually updated
        row = test_state.wl_rows[0]
        assert row.status == 'Successful Order', f"Expected 'Successful Order', got '{row.status}'"

    def test_restore_state_edit_field_redo(self):
        """Redo should restore field to after_state value"""
        from undo_redo import restore_state

        # Create a test state with a row
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=45, practice="Test Practice", phone="555-123-4567",
                address="123 Main St", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="50",
                status="Successful Order",  # Before state (after undo)
                notes="original", bg_color="#ffff00"
            )
        ]

        action = {
            'action_type': 'edit_field',
            'before_state': {
                'row_num': 45,
                'field': 'status',
                'old_value': 'Successful Order'
            },
            'after_state': {
                'row_num': 45,
                'field': 'status',
                'new_value': 'Not interested'  # What to restore to on redo
            }
        }

        # Perform redo
        success = restore_state(test_state, action, 'redo')
        assert success is True

        # Verify the row was actually updated
        row = test_state.wl_rows[0]
        assert row.status == 'Not interested', f"Expected 'Not interested', got '{row.status}'"

    def test_restore_state_bulk_action_undo(self):
        """Undo of bulk action should restore all affected rows"""
        from undo_redo import restore_state

        # Create a test state with multiple rows
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Practice 1", phone="555-111-1111",
                address="123 Main St", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="",
                status="Not interested", notes="", bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2, practice="Practice 2", phone="555-222-2222",
                address="456 Oak Ave", city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="",
                status="Not interested", notes="", bg_color="#ffffff"
            ),
        ]
        # Set current action state
        test_state.wl_rows[0].action = 'accepted'
        test_state.wl_rows[1].action = 'accepted'

        action = {
            'action_type': 'accept_all',
            'before_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': None}},
                    {'row_num': 2, 'fields': {'action': None}}
                ]
            },
            'after_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': 'accepted'}},
                    {'row_num': 2, 'fields': {'action': 'accepted'}}
                ]
            }
        }

        # Perform undo
        success = restore_state(test_state, action, 'undo')
        assert success is True

        # Verify both rows were restored
        assert test_state.wl_rows[0].action is None, f"Row 1 action should be None, got {test_state.wl_rows[0].action}"
        assert test_state.wl_rows[1].action is None, f"Row 2 action should be None, got {test_state.wl_rows[1].action}"

    def test_restore_state_updates_bg_color_on_status_change(self):
        """Changing status should also update bg_color"""
        from undo_redo import restore_state

        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=45, practice="Test Practice", phone="555-123-4567",
                address="123 Main St", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="",
                status="Not interested", notes="", bg_color="#ffffff"
            )
        ]

        action = {
            'action_type': 'edit_field',
            'before_state': {
                'row_num': 45,
                'field': 'status',
                'old_value': 'Successful Order'
            },
            'after_state': {
                'row_num': 45,
                'field': 'status',
                'new_value': 'Not interested'
            }
        }

        # Undo to restore "Successful Order" status
        success = restore_state(test_state, action, 'undo')
        assert success is True

        row = test_state.wl_rows[0]
        assert row.status == 'Successful Order'
        # bg_color should also be updated to yellow
        assert row.bg_color == '#ffff00', f"Expected yellow (#ffff00), got {row.bg_color}"

    def test_restore_state_row_not_found(self):
        """restore_state should handle missing rows gracefully"""
        from undo_redo import restore_state

        test_state = AppState()
        test_state.wl_rows = []  # Empty - row won't be found

        action = {
            'action_type': 'edit_field',
            'before_state': {
                'row_num': 999,  # Doesn't exist
                'field': 'status',
                'old_value': 'Successful Order'
            },
            'after_state': {}
        }

        # Should not crash, just return True (graceful handling)
        success = restore_state(test_state, action, 'undo')
        assert success is True  # Doesn't crash
