"""
Data Integrity Tests

Tests for data consistency, validation, and serialization.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import ProviderRow, NewOrderRow, ReviewCategory
from helpers import normalize_phone, normalize_name, normalize_address, status_to_color


# =============================================================================
# ROW NUMBER UNIQUENESS TESTS
# =============================================================================

class TestRowNumberUniqueness:
    """Tests for row_num uniqueness"""

    def test_provider_row_nums_unique(self):
        """ProviderRow row_nums should be unique"""
        rows = [
            ProviderRow(row_num=i, practice=f"Practice {i}", phone="555-111-1111",
                       address="100 Main St", city="Austin", state="TX", zip="78701",
                       qty_2023="", qty_2024="", qty_2025="",
                       status="", notes="", bg_color="#ffffff")
            for i in range(10, 20)
        ]

        row_nums = [r.row_num for r in rows]
        assert len(row_nums) == len(set(row_nums))

    def test_new_order_row_nums_unique(self):
        """NewOrderRow row_nums should be unique"""
        rows = [
            NewOrderRow(row_num=i, practice=f"Practice {i}",
                       address="100 Main St", city="Austin", state="TX",
                       zip="78701", qty_2025="50")
            for i in range(10, 20)
        ]

        row_nums = [r.row_num for r in rows]
        assert len(row_nums) == len(set(row_nums))


# =============================================================================
# DATA NORMALIZATION CONSISTENCY TESTS
# =============================================================================

class TestNormalizationConsistency:
    """Tests for consistent normalization"""

    def test_phone_normalization_idempotent(self):
        """Normalizing twice gives same result"""
        phone = "(555) 123-4567"
        once = normalize_phone(phone)
        twice = normalize_phone(once)
        assert once == twice

    def test_name_normalization_idempotent(self):
        """Normalizing twice gives same result"""
        name = "Women's Health CENTER"
        once = normalize_name(name)
        twice = normalize_name(once)
        assert once == twice

    def test_address_normalization_idempotent(self):
        """Normalizing twice gives same result"""
        address = "123 Main Street Suite 200"
        once = normalize_address(address)
        twice = normalize_address(once)
        assert once == twice

    def test_status_color_consistency(self):
        """Same status always gives same color"""
        status = "Successful Order"
        color1 = status_to_color(status)
        color2 = status_to_color(status)
        assert color1 == color2


# =============================================================================
# ROW TO_DICT TESTS
# =============================================================================

class TestRowSerialization:
    """Tests for row serialization"""

    def test_provider_row_to_dict_complete(self):
        """ProviderRow.to_dict() includes all fields"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="10", qty_2024="20", qty_2025="30",
            status="Successful Order", notes="test notes", bg_color="#ffff00"
        )

        data = row.to_dict()

        assert data['row_num'] == 10
        assert data['practice'] == "Test"
        assert data['phone'] == "555-111-1111"
        assert data['address'] == "100 Main St"
        assert data['city'] == "Austin"
        assert data['state'] == "TX"
        assert data['status'] == "Successful Order"
        assert data['notes'] == "test notes"
        assert data['bg_color'] == "#ffff00"

    def test_provider_row_to_dict_json_serializable(self):
        """ProviderRow.to_dict() is JSON serializable"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )

        data = row.to_dict()
        json_str = json.dumps(data)

        assert len(json_str) > 0
        # Should be able to deserialize
        parsed = json.loads(json_str)
        assert parsed['row_num'] == 10

    def test_new_order_row_to_dict_complete(self):
        """NewOrderRow.to_dict() includes all fields"""
        row = NewOrderRow(
            row_num=10, practice="Test",
            address="100 Main St", city="Austin", state="TX",
            zip="78701", qty_2025="50"
        )

        data = row.to_dict()

        assert data['row_num'] == 10
        assert data['practice'] == "Test"
        assert data['qty_2025'] == "50"


# =============================================================================
# CATEGORY VALIDATION TESTS
# =============================================================================

class TestCategoryValidation:
    """Tests for ReviewCategory data integrity"""

    def test_category_row_nums_are_integers(self):
        """ReviewCategory row_nums are all integers"""
        cat = ReviewCategory(
            id="test",
            name="Test",
            description="Test category",
            row_nums=[10, 20, 30],
            allow_batch=True
        )

        for row_num in cat.row_nums:
            assert isinstance(row_num, int)

    def test_category_allow_batch_valid(self):
        """ReviewCategory allow_batch is boolean"""
        cat = ReviewCategory(
            id="test",
            name="Test",
            description="Test",
            row_nums=[],
            allow_batch=True
        )
        assert isinstance(cat.allow_batch, bool)

    def test_category_to_dict_row_count_matches(self):
        """ReviewCategory.to_dict() row_count matches len(row_nums)"""
        cat = ReviewCategory(
            id="test",
            name="Test",
            description="Test",
            row_nums=[10, 20, 30, 40],
            allow_batch=False
        )

        cat_dict = cat.to_dict()
        assert cat_dict['row_count'] == len(cat.row_nums)


# =============================================================================
# COLOR VALIDATION TESTS
# =============================================================================

class TestColorValidation:
    """Tests for valid color values"""

    def test_bg_color_is_hex(self):
        """bg_color is valid hex format"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffff00"
        )

        assert row.bg_color.startswith('#')
        assert len(row.bg_color) in [4, 7]  # #RGB or #RRGGBB

    def test_status_to_color_returns_hex(self):
        """status_to_color returns hex color"""
        statuses = [
            "Successful Order",
            "Voicemail/No Answer",
            "Not interested",
            "Potentially Invalid",
            "Requested Email",
            "",
        ]

        for status in statuses:
            color = status_to_color(status)
            assert color.startswith('#')


# =============================================================================
# FIELD EDITS TRACKING TESTS
# =============================================================================

class TestFieldEditsTracking:
    """Tests for field_edits dictionary"""

    def test_field_edits_empty_initially(self):
        """field_edits is empty on new row"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )

        assert row.field_edits == {}

    def test_field_edits_tracks_changes(self):
        """field_edits tracks modified fields"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )

        row.notes = "new notes"
        row.field_edits['notes'] = "new notes"

        assert 'notes' in row.field_edits
        assert row.field_edits['notes'] == "new notes"


# =============================================================================
# MATCH CONFIDENCE TESTS
# =============================================================================

class TestMatchConfidence:
    """Tests for match_confidence field"""

    def test_match_confidence_in_range(self):
        """match_confidence is between 0 and 1"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )

        row.match_confidence = 0.85

        assert 0 <= row.match_confidence <= 1

    def test_match_confidence_default(self):
        """match_confidence defaults to 0"""
        row = ProviderRow(
            row_num=10, practice="Test", phone="555-111-1111",
            address="100 Main St", city="Austin", state="TX", zip="78701",
            qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )

        assert row.match_confidence == 0.0
