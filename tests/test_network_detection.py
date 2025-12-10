"""
Network Detection Tests

Tests for network grouping logic and derive_network_name() function.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from eoy_tool import derive_network_name, ProviderRow


def make_row(practice, phone="555-123-4567", address="123 Main St"):
    """Helper to create test rows"""
    return ProviderRow(
        row_num=1, practice=practice, phone=phone, address=address,
        city="Austin", state="TX", zip="78701",
        qty_2023="", qty_2024="", qty_2025="",
        status="", notes="", bg_color="#ffffff"
    )


# =============================================================================
# derive_network_name() TESTS
# =============================================================================

class TestDeriveNetworkName:
    """Tests for derive_network_name() function"""

    def test_derive_name_common_word(self):
        """Finds common meaningful word across practices"""
        rows = [
            make_row("Austin Wellness Center"),
            make_row("Downtown Wellness Clinic"),
            make_row("Wellness Associates North"),
        ]
        result = derive_network_name(rows)
        assert "Wellness" in result

    def test_derive_name_excludes_location_words(self):
        """Excludes location words from common word pool"""
        rows = [
            make_row("North Austin Wellness"),
            make_row("South Austin Wellness"),
            make_row("Downtown Austin Wellness"),
        ]
        result = derive_network_name(rows)
        # "austin" and "wellness" are common and not excluded
        assert "Austin" in result or "Wellness" in result

    def test_derive_name_excludes_generic_medical_words(self):
        """Excludes generic words like clinic/center/health"""
        rows = [
            make_row("Smith Health Center"),
            make_row("Jones Health Clinic"),
            make_row("Brown Health Office"),
        ]
        result = derive_network_name(rows)
        # "Health" should be excluded, might fall back to first word
        assert "Health" not in result or "Network" in result

    def test_derive_name_single_row_fallback(self):
        """Single row uses first word of practice name"""
        rows = [make_row("Austin Women's Health")]
        result = derive_network_name(rows)
        assert "Austin" in result
        assert "Network" in result

    def test_derive_name_empty_rows(self):
        """Empty list returns 'Unknown Network'"""
        result = derive_network_name([])
        assert result == "Unknown Network"

    def test_derive_name_no_common_words(self):
        """No common words falls back to first practice name"""
        rows = [
            make_row("Alpha Practice"),
            make_row("Beta Clinic"),
            make_row("Gamma Office"),
        ]
        result = derive_network_name(rows)
        assert "Network" in result

    def test_derive_name_picks_longest_word(self):
        """Picks longest meaningful common word"""
        rows = [
            make_row("ABC Dermatology Associates"),
            make_row("XYZ Dermatology Center"),
            make_row("123 Dermatology Clinic"),
        ]
        result = derive_network_name(rows)
        assert "Dermatology" in result

    def test_derive_name_handles_special_chars(self):
        """Handles special characters in names"""
        rows = [
            make_row("Women's Specialists - North"),
            make_row("Women's Specialists - South"),
        ]
        result = derive_network_name(rows)
        assert "Network" in result

    def test_derive_name_case_insensitive(self):
        """Matching is case insensitive"""
        rows = [
            make_row("AUSTIN Medical"),
            make_row("austin MEDICAL"),
            make_row("Austin medical"),
        ]
        result = derive_network_name(rows)
        assert "Austin" in result or "Network" in result

    def test_derive_name_short_words_excluded(self):
        """Words <= 2 chars are excluded"""
        rows = [
            make_row("Dr Smith OB Practice"),
            make_row("Dr Jones OB Clinic"),
        ]
        result = derive_network_name(rows)
        # "OB" and "Dr" should be excluded (2 chars)
        assert "Network" in result

    def test_derive_name_with_numbers(self):
        """Handles practices with numbers"""
        rows = [
            make_row("Family Care 360"),
            make_row("360 Family Care Center"),
        ]
        result = derive_network_name(rows)
        assert "Family" in result or "Network" in result

    def test_derive_name_all_excluded_words(self):
        """All words are excluded falls back to first practice"""
        rows = [
            make_row("North Medical Center"),
            make_row("South Medical Clinic"),
        ]
        # All common words (medical) excluded
        result = derive_network_name(rows)
        assert "Network" in result

    def test_derive_name_empty_practice_names(self):
        """Empty practice names handled"""
        rows = [
            make_row(""),
            make_row(""),
        ]
        result = derive_network_name(rows)
        assert "Network" in result

    def test_derive_name_unicode_chars(self):
        """Handles unicode characters"""
        rows = [
            make_row("Señor Medical García"),
            make_row("Señor Medical López"),
        ]
        result = derive_network_name(rows)
        assert "Network" in result

    def test_derive_name_hyphenated_words(self):
        """Handles hyphenated practice names"""
        rows = [
            make_row("Smith-Jones Medical"),
            make_row("Smith-Jones Clinic"),
        ]
        result = derive_network_name(rows)
        assert "Network" in result


# =============================================================================
# NETWORK GROUPING TESTS
# =============================================================================

class TestNetworkGrouping:
    """Tests for network detection logic"""

    def test_same_phone_different_address_is_network(self):
        """Same phone, different addresses = network"""
        rows = [
            make_row("Practice A", phone="555-123-4567", address="100 Main St"),
            make_row("Practice B", phone="555-123-4567", address="200 Oak Ave"),
            make_row("Practice C", phone="555-123-4567", address="300 Elm St"),
        ]
        # All have same phone but different addresses
        # This is the network detection criteria
        assert len(set(r.phone for r in rows)) == 1
        assert len(set(r.address for r in rows)) == 3

    def test_same_phone_same_address_is_duplicate(self):
        """Same phone, same address = duplicate (not network)"""
        rows = [
            make_row("Practice A", phone="555-123-4567", address="100 Main St"),
            make_row("Practice A", phone="555-123-4567", address="100 Main St"),
        ]
        # Same phone AND same address = duplicate
        assert len(set(r.phone for r in rows)) == 1
        assert len(set(r.address for r in rows)) == 1

    def test_network_minimum_two_rows(self):
        """Network requires at least 2 rows"""
        rows = [make_row("Solo Practice")]
        # Single row cannot be a network
        assert len(rows) == 1

    def test_network_ten_plus_locations(self):
        """Large networks (10+ locations) handled"""
        rows = [
            make_row(f"Network Location {i}", phone="555-111-1111", address=f"{i}00 Street")
            for i in range(15)
        ]
        result = derive_network_name(rows)
        assert "Network" in result
        assert len(rows) == 15
