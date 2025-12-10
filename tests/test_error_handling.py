"""
Error Handling Tests

Tests for proper error responses and edge case handling.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from eoy_tool import app, state, ProviderRow, safe_int, safe_int_list


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def minimal_state():
    """Set up minimal state"""
    state.wl_rows = [
        ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )
    ]
    state.categories = []
    state.undo_stack = []
    state.redo_stack = []

    yield state

    state.wl_rows = []
    state.categories = []


# =============================================================================
# INVALID INPUT TESTS (Parameterized)
# =============================================================================

class TestInvalidRowNumInputs:
    """Tests for various invalid row_num inputs"""

    @pytest.mark.parametrize("invalid_value,description", [
        (None, "null row_num"),
        ("", "empty string row_num"),
        ("abc", "non-numeric string"),
        (0, "zero row_num"),
        ([], "array row_num"),
        ({}, "object row_num"),
        ("  ", "whitespace only"),
    ])
    def test_edit_field_invalid_row_num(self, client, minimal_state, invalid_value, description):
        """Edit field with invalid row_num: {description}"""
        response = client.post('/api/edit_field',
            data=json.dumps({
                'row_num': invalid_value,
                'field': 'notes',
                'value': 'test'
            }),
            content_type='application/json')

        # Should return 400 for invalid input or 200 with success: false
        if response.status_code == 200:
            data = response.get_json()
            assert data.get('success') is False, f"Failed for: {description}"
        else:
            assert response.status_code == 400, f"Failed for: {description}"

    @pytest.mark.parametrize("invalid_list,description", [
        (None, "null list"),
        ([None], "list with null"),
        ([""], "list with empty string"),
        ([1, "abc", 2], "list with non-numeric"),
        ("not a list", "string instead of list"),
    ])
    def test_delete_rows_invalid_list(self, client, minimal_state, invalid_list, description):
        """Delete rows with invalid list: {description}"""
        response = client.post('/api/delete_rows',
            data=json.dumps({'row_nums': invalid_list}),
            content_type='application/json')

        # Should either return 400 or handle gracefully
        assert response.status_code in [200, 400], f"Failed for: {description}"


# =============================================================================
# MISSING REQUIRED FIELDS
# =============================================================================

class TestMissingRequiredFields:
    """Tests for missing required request fields"""

    def test_edit_field_missing_row_num(self, client, minimal_state):
        """Edit field without row_num"""
        response = client.post('/api/edit_field',
            data=json.dumps({'field': 'notes', 'value': 'test'}),
            content_type='application/json')

        assert response.status_code == 400

    def test_edit_field_missing_field(self, client, minimal_state):
        """Edit field without field name"""
        response = client.post('/api/edit_field',
            data=json.dumps({'row_num': 10, 'value': 'test'}),
            content_type='application/json')

        assert response.status_code == 400

    def test_merge_rows_missing_survivor(self, client, minimal_state):
        """Merge without survivor_row_num"""
        response = client.post('/api/merge_rows',
            data=json.dumps({'other_row_nums': [11]}),
            content_type='application/json')

        assert response.status_code == 400

    def test_delete_note_chunk_missing_index(self, client, minimal_state):
        """Delete note chunk without index"""
        response = client.post('/api/delete_note_chunk',
            data=json.dumps({'row_num': 10}),
            content_type='application/json')

        # chunk_index of None should return error
        assert response.status_code == 400


# =============================================================================
# ERROR RESPONSE FORMAT
# =============================================================================

class TestErrorResponseFormat:
    """Tests for consistent error response format"""

    def test_error_returns_json(self, client, minimal_state):
        """Error responses are JSON"""
        response = client.post('/api/edit_field',
            data=json.dumps({'row_num': 9999, 'field': 'notes', 'value': 'test'}),
            content_type='application/json')

        assert response.content_type.startswith('application/json')

    def test_error_has_success_false(self, client, minimal_state):
        """Error responses have success: false"""
        response = client.post('/api/edit_field',
            data=json.dumps({'row_num': 9999, 'field': 'notes', 'value': 'test'}),
            content_type='application/json')

        data = response.get_json()
        assert data['success'] is False

    def test_error_has_message(self, client, minimal_state):
        """Error responses have error message"""
        response = client.post('/api/edit_field',
            data=json.dumps({'row_num': 9999, 'field': 'notes', 'value': 'test'}),
            content_type='application/json')

        data = response.get_json()
        assert 'error' in data


# =============================================================================
# ROW NOT FOUND ERRORS
# =============================================================================

class TestRowNotFound:
    """Tests for row not found scenarios"""

    def test_edit_nonexistent_row(self, client, minimal_state):
        """Edit row that doesn't exist returns error"""
        response = client.post('/api/edit_field',
            data=json.dumps({'row_num': 9999, 'field': 'notes', 'value': 'test'}),
            content_type='application/json')

        # May return 400, 404, or 200 with success: false
        if response.status_code == 200:
            data = response.get_json()
            assert data.get('success') is False
        else:
            assert response.status_code in [400, 404]

    def test_delete_note_nonexistent_row(self, client, minimal_state):
        """Delete note from nonexistent row returns error"""
        response = client.post('/api/delete_note_chunk',
            data=json.dumps({'row_num': 9999, 'chunk_index': 0}),
            content_type='application/json')

        # May return 400, 404, or 200 with success: false
        if response.status_code == 200:
            data = response.get_json()
            assert data.get('success') is False
        else:
            assert response.status_code in [400, 404]

    def test_get_duplicate_group_nonexistent(self, client, minimal_state):
        """Get duplicate group for nonexistent row"""
        response = client.post('/api/get_duplicate_group',
            data=json.dumps({'row_num': 9999}),
            content_type='application/json')

        assert response.status_code == 400


# =============================================================================
# INVALID JSON
# =============================================================================

class TestInvalidJSON:
    """Tests for invalid JSON handling"""

    def test_malformed_json(self, client, minimal_state):
        """Malformed JSON body"""
        response = client.post('/api/edit_field',
            data='{invalid json',
            content_type='application/json')

        assert response.status_code == 400

    def test_empty_body(self, client, minimal_state):
        """Empty request body"""
        response = client.post('/api/edit_field',
            data='',
            content_type='application/json')

        assert response.status_code == 400


# =============================================================================
# SAFE_INT HELPER TESTS
# =============================================================================

class TestSafeIntEdgeCases:
    """Additional edge cases for safe_int helpers"""

    def test_safe_int_very_large_number(self):
        """Very large numbers handled"""
        result = safe_int(999999999999)
        assert result == 999999999999

    def test_safe_int_negative(self):
        """Negative numbers handled"""
        result = safe_int(-5)
        assert result == -5

    def test_safe_int_string_with_spaces(self):
        """String with spaces"""
        result = safe_int("  123  ")
        # Should either strip and convert or return None
        assert result in [123, None]

    def test_safe_int_list_preserves_order(self):
        """safe_int_list preserves order"""
        result = safe_int_list([3, 1, 2])
        assert result == [3, 1, 2]

    def test_safe_int_list_large(self):
        """Large list handled"""
        large_list = list(range(1, 1001))
        result = safe_int_list(large_list)
        assert len(result) == 1000
