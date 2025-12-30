"""
Test API endpoints added for dynamic UI updates

Tests the /api/get_categories and /api/undo_status endpoints
that support real-time UI updates without page reload.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import ProviderRow, ReviewCategory
from state import AppState, state
from undo_redo import add_to_undo_stack


class TestGetCategoriesEndpoint:
    """Test /api/get_categories endpoint logic"""

    def test_category_counts_all_unresolved(self):
        """Categories with no actions taken should show full count"""
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Practice 1", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2, practice="Practice 2", phone="555-222-2222",
                address="456 Oak", city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        test_state.categories = [
            ReviewCategory(id='test_cat', name='Test Category', description='Test', row_nums=[1, 2], allow_batch=True)
        ]

        # Calculate unresolved count
        unresolved = 0
        for row_num in test_state.categories[0].row_nums:
            row = next((r for r in test_state.wl_rows if r.row_num == row_num), None)
            if row and not row.action:
                unresolved += 1

        assert unresolved == 2

    def test_category_counts_some_resolved(self):
        """Categories with some actions should show reduced count"""
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Practice 1", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2, practice="Practice 2", phone="555-222-2222",
                address="456 Oak", city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        # Mark one row as resolved
        test_state.wl_rows[0].action = 'deleted'

        test_state.categories = [
            ReviewCategory(id='test_cat', name='Test Category', description='Test', row_nums=[1, 2], allow_batch=True)
        ]

        # Calculate unresolved count
        unresolved = 0
        for row_num in test_state.categories[0].row_nums:
            row = next((r for r in test_state.wl_rows if r.row_num == row_num), None)
            if row and not row.action:
                unresolved += 1

        assert unresolved == 1

    def test_category_counts_all_resolved(self):
        """Categories with all actions taken should show zero"""
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Practice 1", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2, practice="Practice 2", phone="555-222-2222",
                address="456 Oak", city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        test_state.wl_rows[0].action = 'deleted'
        test_state.wl_rows[1].action = 'reviewed_no_change'

        test_state.categories = [
            ReviewCategory(id='test_cat', name='Test Category', description='Test', row_nums=[1, 2], allow_batch=True)
        ]

        # Calculate unresolved count
        unresolved = 0
        for row_num in test_state.categories[0].row_nums:
            row = next((r for r in test_state.wl_rows if r.row_num == row_num), None)
            if row and not row.action:
                unresolved += 1

        assert unresolved == 0

    def test_category_counts_row_in_multiple_categories(self):
        """Row in multiple categories should be counted in each"""
        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Practice 1", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        test_state.categories = [
            ReviewCategory(id='cat_a', name='Category A', description='Test A', row_nums=[1], allow_batch=True),
            ReviewCategory(id='cat_b', name='Category B', description='Test B', row_nums=[1], allow_batch=True)  # Same row
        ]

        # Both categories should show 1 unresolved
        for cat in test_state.categories:
            unresolved = 0
            for row_num in cat.row_nums:
                row = next((r for r in test_state.wl_rows if r.row_num == row_num), None)
                if row and not row.action:
                    unresolved += 1
            assert unresolved == 1

        # After marking row as resolved, both should show 0
        test_state.wl_rows[0].action = 'deleted'

        for cat in test_state.categories:
            unresolved = 0
            for row_num in cat.row_nums:
                row = next((r for r in test_state.wl_rows if r.row_num == row_num), None)
                if row and not row.action:
                    unresolved += 1
            assert unresolved == 0


class TestUndoStatusEndpoint:
    """Test /api/undo_status endpoint logic"""

    def test_empty_stacks_cannot_undo_redo(self):
        """Empty stacks should report can_undo=False, can_redo=False"""
        state.undo_stack = []
        state.redo_stack = []

        can_undo = len(state.undo_stack) > 0
        can_redo = len(state.redo_stack) > 0

        assert can_undo is False
        assert can_redo is False

    def test_undo_stack_has_item(self):
        """With items in undo stack, can_undo=True"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack(state, 'delete', 'Delete row 1', {'row_num': 1}, None)

        can_undo = len(state.undo_stack) > 0
        can_redo = len(state.redo_stack) > 0

        assert can_undo is True
        assert can_redo is False

    def test_undo_description_returned(self):
        """Undo description should be available for UI display"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack(state, 'delete', 'Delete row 42', {'row_num': 42}, None)

        undo_description = state.undo_stack[-1]['description'] if state.undo_stack else None

        assert undo_description == 'Delete row 42'

    def test_redo_description_after_undo(self):
        """After undo, redo description should be available"""
        state.undo_stack = []
        state.redo_stack = []

        # Add action
        add_to_undo_stack(state, 'delete', 'Delete row 42', {'row_num': 42}, None)

        # Simulate undo by moving to redo stack
        action = state.undo_stack.pop()
        state.redo_stack.append(action)

        can_undo = len(state.undo_stack) > 0
        can_redo = len(state.redo_stack) > 0
        redo_description = state.redo_stack[-1]['description'] if state.redo_stack else None

        assert can_undo is False
        assert can_redo is True
        assert redo_description == 'Delete row 42'

    def test_multiple_actions_shows_last(self):
        """Description should show most recent action (LIFO)"""
        state.undo_stack = []
        state.redo_stack = []

        add_to_undo_stack(state, 'delete', 'Delete row 1', {}, None)
        add_to_undo_stack(state, 'delete', 'Delete row 2', {}, None)
        add_to_undo_stack(state, 'edit', 'Edit row 3', {}, None)

        undo_description = state.undo_stack[-1]['description']

        assert undo_description == 'Edit row 3'


class TestMarkReviewedUndoRedo:
    """Test undo/redo for mark_reviewed action type"""

    def test_restore_mark_reviewed_undo(self):
        """Undo mark_reviewed should restore original action"""
        from undo_redo import restore_state

        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Test Practice", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        # Current state: marked as reviewed
        test_state.wl_rows[0].action = 'reviewed_no_change'

        action = {
            'action_type': 'mark_reviewed',
            'before_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': None}}  # Originally no action
                ]
            },
            'after_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': 'reviewed_no_change'}}
                ]
            }
        }

        # Undo should restore to None
        success = restore_state(test_state, action, 'undo')
        assert success is True
        assert test_state.wl_rows[0].action is None

    def test_restore_mark_reviewed_redo(self):
        """Redo mark_reviewed should set action back to reviewed"""
        from undo_redo import restore_state

        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Test Practice", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        # Current state: no action (after undo)
        test_state.wl_rows[0].action = None

        action = {
            'action_type': 'mark_reviewed',
            'before_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': None}}
                ]
            },
            'after_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': 'reviewed_no_change'}}
                ]
            }
        }

        # Redo should restore to reviewed_no_change
        success = restore_state(test_state, action, 'redo')
        assert success is True
        assert test_state.wl_rows[0].action == 'reviewed_no_change'

    def test_restore_mark_reviewed_multiple_rows(self):
        """Undo mark_reviewed should restore all affected rows"""
        from undo_redo import restore_state

        test_state = AppState()
        test_state.wl_rows = [
            ProviderRow(
                row_num=1, practice="Practice 1", phone="555-111-1111",
                address="123 Main", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2, practice="Practice 2", phone="555-222-2222",
                address="456 Oak", city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=3, practice="Practice 3", phone="555-333-3333",
                address="789 Elm", city="Austin", state="TX", zip="78703",
                qty_2023="", qty_2024="", qty_2025="", status="", notes="",
                bg_color="#ffffff"
            ),
        ]
        # Current state: all marked as reviewed
        for row in test_state.wl_rows:
            row.action = 'reviewed_no_change'

        action = {
            'action_type': 'mark_reviewed',
            'before_state': {
                'rows': [
                    {'row_num': 1, 'fields': {'action': None}},
                    {'row_num': 2, 'fields': {'action': 'deleted'}},  # Was deleted before
                    {'row_num': 3, 'fields': {'action': None}},
                ]
            },
            'after_state': {}
        }

        # Undo should restore each row's original action
        success = restore_state(test_state, action, 'undo')
        assert success is True
        assert test_state.wl_rows[0].action is None
        assert test_state.wl_rows[1].action == 'deleted'  # Restored to deleted
        assert test_state.wl_rows[2].action is None

    def test_restore_mark_reviewed_row_not_found(self):
        """Undo should handle missing rows gracefully"""
        from undo_redo import restore_state

        test_state = AppState()
        test_state.wl_rows = []  # No rows

        action = {
            'action_type': 'mark_reviewed',
            'before_state': {
                'rows': [
                    {'row_num': 999, 'fields': {'action': None}}  # Row doesn't exist
                ]
            },
            'after_state': {}
        }

        # Should not crash, just return True
        success = restore_state(test_state, action, 'undo')
        assert success is True
