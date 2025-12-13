"""
Edge case tests for real-world data scenarios.

These tests verify the code handles edge cases that commonly appear
in real Google Sheets data but might not be covered by basic tests.
"""

import pytest
import sys
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from models import ProviderRow, NewOrderRow
from helpers import status_to_color, normalize_name, normalize_address, normalize_phone, safe_int, safe_int_list


# =============================================================================
# STATUS EDGE CASES
# =============================================================================

class TestStatusEdgeCases:
    """Test status_to_color handles all real-world status variations"""

    def test_status_with_trailing_spaces(self):
        """Status values might have trailing/leading spaces from copy-paste"""
        assert status_to_color("Successful Order ") == "#ffff00"
        assert status_to_color(" Successful Order") == "#ffff00"
        assert status_to_color("  Successful Order  ") == "#ffff00"

    def test_status_with_mixed_case(self):
        """Status values might have inconsistent case"""
        assert status_to_color("SUCCESSFUL ORDER") == "#ffff00"
        assert status_to_color("successful order") == "#ffff00"
        assert status_to_color("Successful order") == "#ffff00"
        assert status_to_color("sUcCeSsFuL oRdEr") == "#ffff00"

    def test_status_empty_variations(self):
        """Various empty/null values should return white"""
        assert status_to_color("") == "#ffffff"
        assert status_to_color(None) == "#ffffff"
        assert status_to_color("   ") == "#ffffff"  # Just spaces

    def test_status_unknown_value(self):
        """Unknown status values should default to white"""
        assert status_to_color("Some Random Status") == "#ffffff"
        assert status_to_color("Callback") == "#ffffff"
        assert status_to_color("Follow up") == "#ffffff"

    def test_status_partial_match_not_accepted(self):
        """Partial matches should NOT work (exact match only)"""
        # These should NOT match
        assert status_to_color("Successful") != "#ffff00"
        assert status_to_color("Order") != "#ffff00"
        assert status_to_color("Success") != "#ffff00"
        assert status_to_color("Voicemail") != "#ff00ff"  # Missing "/No Answer"

    def test_status_with_extra_text_not_accepted(self):
        """Status with extra text appended should NOT match"""
        assert status_to_color("Successful Order - paid") == "#ffffff"
        assert status_to_color("Not interested - closed") == "#ffffff"
        assert status_to_color("Voicemail/No Answer x3") == "#ffffff"


# =============================================================================
# PHONE NUMBER EDGE CASES
# =============================================================================

class TestPhoneEdgeCases:
    """Test phone number normalization handles various formats"""

    def test_phone_standard_formats(self):
        """Standard US phone formats"""
        assert normalize_phone("555-123-4567") == "5551234567"
        assert normalize_phone("(555) 123-4567") == "5551234567"
        assert normalize_phone("555.123.4567") == "5551234567"
        assert normalize_phone("555 123 4567") == "5551234567"

    def test_phone_with_country_code(self):
        """Phones with country code prefix - code gets stripped (last 10 digits kept)"""
        # normalize_phone keeps last 10 digits, stripping country code
        assert normalize_phone("+1 555-123-4567") == "5551234567"
        assert normalize_phone("1-555-123-4567") == "5551234567"

    def test_phone_with_extension(self):
        """Phones with extensions - extension should be stripped"""
        assert normalize_phone("555-123-4567 ext 100") == "5551234567"
        assert normalize_phone("555-123-4567 x200") == "5551234567"
        assert normalize_phone("555-123-4567 Ext. 300") == "5551234567"
        assert normalize_phone("555-123-4567 extension 400") == "5551234567"

    def test_phone_with_nonbreaking_space(self):
        """Phones with non-breaking space (\\xa0) should normalize correctly"""
        # Real data case: phone number followed by non-breaking space
        assert normalize_phone("(424) 203-0488\xa0") == "4242030488"
        assert normalize_phone("\xa0(555) 123-4567") == "5551234567"
        assert normalize_phone("555\xa0123\xa04567") == "5551234567"

    def test_phone_empty_values(self):
        """Empty phone values"""
        assert normalize_phone("") == ""
        assert normalize_phone(None) == ""
        assert normalize_phone("   ") == ""

    def test_phone_short_numbers(self):
        """Short/incomplete phone numbers"""
        assert normalize_phone("555") == "555"
        assert normalize_phone("555-1234") == "5551234"


# =============================================================================
# NAME NORMALIZATION EDGE CASES
# =============================================================================

class TestNameNormalizationEdgeCases:
    """Test practice name normalization"""

    def test_name_with_business_suffixes(self):
        """Business suffixes should be removed"""
        assert "llc" not in normalize_name("Women's Health LLC")
        assert "pc" not in normalize_name("Austin OBGYN PC")
        assert "pllc" not in normalize_name("Family Practice PLLC")

    def test_name_with_medical_titles(self):
        """Medical titles should be removed"""
        assert "dr" not in normalize_name("Dr. Smith's Practice")
        assert "md" not in normalize_name("Smith MD")
        assert "do" not in normalize_name("Jones DO")

    def test_name_ampersand_normalization(self):
        """Ampersands should become 'and'"""
        result = normalize_name("Smith & Jones")
        assert "&" not in result
        assert "and" in result

    def test_name_plus_sign_normalization(self):
        """Plus signs should become 'and'"""
        result = normalize_name("OB + GYN Associates")
        assert "+" not in result
        assert "and" in result

    def test_name_empty_values(self):
        """Empty name values"""
        assert normalize_name("") == ""
        assert normalize_name(None) == ""

    def test_name_special_characters(self):
        """Names with special characters"""
        # Apostrophes should be preserved
        result = normalize_name("Women's Health Center")
        assert "women's" in result.lower() or "womens" in result.lower()


# =============================================================================
# ADDRESS NORMALIZATION EDGE CASES
# =============================================================================

class TestAddressNormalizationEdgeCases:
    """Test address normalization"""

    def test_address_street_type_abbreviations(self):
        """Street types should be abbreviated"""
        assert "st" in normalize_address("123 Main Street")
        assert "ave" in normalize_address("456 Oak Avenue")
        assert "blvd" in normalize_address("789 Central Boulevard")
        assert "dr" in normalize_address("100 Medical Drive")

    def test_address_suite_removal(self):
        """Suite/unit numbers should be removed or normalized"""
        result = normalize_address("123 Main St Suite 200")
        # Suite should be abbreviated
        assert "suite" not in result.lower()

    def test_address_empty_values(self):
        """Empty address values"""
        assert normalize_address("") == ""
        assert normalize_address(None) == ""

    def test_address_case_normalization(self):
        """Addresses should be lowercased"""
        result = normalize_address("123 MAIN STREET")
        assert result == result.lower()


# =============================================================================
# NOTES EDGE CASES
# =============================================================================

class TestNotesEdgeCases:
    """Test notes handling edge cases"""

    def test_notes_semicolon_splitting(self):
        """Notes with semicolons should split correctly"""
        notes = "vm x2; callback 1/5; sent email"
        chunks = [c.strip() for c in notes.split(';') if c.strip()]
        assert len(chunks) == 3
        assert chunks[0] == "vm x2"
        assert chunks[1] == "callback 1/5"
        assert chunks[2] == "sent email"

    def test_notes_empty_chunks(self):
        """Empty chunks should be filtered out"""
        notes = "vm;;sent;"
        chunks = [c.strip() for c in notes.split(';') if c.strip()]
        assert len(chunks) == 2
        assert "vm" in chunks
        assert "sent" in chunks

    def test_notes_only_semicolons(self):
        """Notes with only semicolons"""
        notes = ";;;"
        chunks = [c.strip() for c in notes.split(';') if c.strip()]
        assert len(chunks) == 0

    def test_notes_with_special_characters(self):
        """Notes might contain quotes or special chars"""
        notes = "caller said \"not interested\""
        chunks = [c.strip() for c in notes.split(';') if c.strip()]
        assert len(chunks) == 1
        assert '"not interested"' in chunks[0]

    def test_notes_with_dates(self):
        """Notes often contain dates in various formats"""
        notes = "vm 1/5/24; callback 01-05-2024; follow up 2024/01/05"
        chunks = [c.strip() for c in notes.split(';') if c.strip()]
        assert len(chunks) == 3


# =============================================================================
# QTY FIELD EDGE CASES
# =============================================================================

class TestQtyFieldEdgeCases:
    """Test quantity field handling"""

    def test_qty_numeric_values(self):
        """Normal numeric values"""
        row = ProviderRow(
            row_num=1, practice="Test", phone="", address="", city="", state="",
            zip="", qty_2023="50", qty_2024="100", qty_2025="25", status="",
            notes="", bg_color="#ffffff"
        )
        assert row.qty_2025 == "25"

    def test_qty_empty_values(self):
        """Empty qty values"""
        row = ProviderRow(
            row_num=1, practice="Test", phone="", address="", city="", state="",
            zip="", qty_2023="", qty_2024="", qty_2025="", status="",
            notes="", bg_color="#ffffff"
        )
        assert row.qty_2025 == ""

    def test_qty_zero_value(self):
        """Zero qty (common for 'not interested')"""
        row = ProviderRow(
            row_num=1, practice="Test", phone="", address="", city="", state="",
            zip="", qty_2023="50", qty_2024="0", qty_2025="0", status="Not interested",
            notes="", bg_color="#ffffff"
        )
        assert row.qty_2025 == "0"


# =============================================================================
# ROW NUMBER TYPE HANDLING
# =============================================================================

class TestRowNumberTypes:
    """Test that row numbers are handled correctly as integers"""

    def test_row_num_is_integer(self):
        """Row numbers should be integers"""
        row = ProviderRow(
            row_num=45, practice="Test", phone="", address="", city="", state="",
            zip="", qty_2023="", qty_2024="", qty_2025="", status="",
            notes="", bg_color="#ffffff"
        )
        assert isinstance(row.row_num, int)
        assert row.row_num == 45

    def test_row_num_comparison(self):
        """Row number comparisons should work correctly"""
        rows = [
            ProviderRow(row_num=10, practice="A", phone="", address="", city="", state="",
                       zip="", qty_2023="", qty_2024="", qty_2025="", status="", notes="", bg_color="#ffffff"),
            ProviderRow(row_num=5, practice="B", phone="", address="", city="", state="",
                       zip="", qty_2023="", qty_2024="", qty_2025="", status="", notes="", bg_color="#ffffff"),
            ProviderRow(row_num=15, practice="C", phone="", address="", city="", state="",
                       zip="", qty_2023="", qty_2024="", qty_2025="", status="", notes="", bg_color="#ffffff"),
        ]

        # Finding by row_num should work
        found = next((r for r in rows if r.row_num == 10), None)
        assert found is not None
        assert found.practice == "A"

        # Sorting should work
        sorted_rows = sorted(rows, key=lambda r: r.row_num)
        assert sorted_rows[0].row_num == 5
        assert sorted_rows[1].row_num == 10
        assert sorted_rows[2].row_num == 15


# =============================================================================
# JSON SERIALIZATION EDGE CASES
# =============================================================================

class TestJsonSerialization:
    """Test that data serializes correctly to JSON"""

    def test_provider_row_to_dict(self):
        """ProviderRow should serialize to dict correctly"""
        row = ProviderRow(
            row_num=45,
            practice="Women's Health \"Special\" Center",
            phone="555-123-4567",
            address="123 Main St; Suite 200",  # Note semicolon
            city="Austin",
            state="TX",
            zip="78701",
            qty_2023="50",
            qty_2024="",
            qty_2025="25",
            status="Successful Order",
            notes="vm; sent; ordered",
            bg_color="#ffff00"
        )

        d = row.to_dict()

        assert d['row_num'] == 45
        assert d['practice'] == "Women's Health \"Special\" Center"
        assert d['notes'] == "vm; sent; ordered"
        assert d['bg_color'] == "#ffff00"

    def test_new_order_row_to_dict(self):
        """NewOrderRow should serialize to dict correctly"""
        row = NewOrderRow(
            row_num=10,
            practice="Test Practice",
            address="123 Main St",
            city="Austin",
            state="TX",
            zip="78701",
            qty_2025="100"
        )

        d = row.to_dict()

        assert d['row_num'] == 10
        assert d['practice'] == "Test Practice"
        assert d['qty_2025'] == "100"


# =============================================================================
# SPECIAL CHARACTER ESCAPING
# =============================================================================

class TestSpecialCharacterHandling:
    """Test that special characters are handled safely"""

    def test_practice_with_quotes(self):
        """Practice names with quotes"""
        row = ProviderRow(
            row_num=1, practice="The \"Best\" Practice", phone="", address="",
            city="", state="", zip="", qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )
        assert '"' in row.practice

    def test_notes_with_quotes(self):
        """Notes with quotes"""
        notes = "caller said \"not interested\"; 'no thanks'"
        assert '"' in notes
        assert "'" in notes

    def test_practice_with_ampersand(self):
        """Practice names with ampersand"""
        row = ProviderRow(
            row_num=1, practice="Smith & Jones", phone="", address="",
            city="", state="", zip="", qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )
        assert '&' in row.practice

    def test_address_with_hash(self):
        """Addresses with # for unit numbers"""
        row = ProviderRow(
            row_num=1, practice="Test", phone="", address="123 Main St #200",
            city="", state="", zip="", qty_2023="", qty_2024="", qty_2025="",
            status="", notes="", bg_color="#ffffff"
        )
        assert '#' in row.address


# =============================================================================
# SAFE INT CONVERSION TESTS
# =============================================================================

class TestSafeIntConversion:
    """Test safe_int handles all JSON edge cases from API requests"""

    def test_safe_int_normal_int(self):
        """Normal integer value"""
        assert safe_int(123) == 123
        assert safe_int(0) == 0

    def test_safe_int_string_number(self):
        """String representation of number (common from JSON)"""
        assert safe_int("123") == 123
        assert safe_int("0") == 0

    def test_safe_int_none(self):
        """None value returns None"""
        assert safe_int(None) is None

    def test_safe_int_empty_string(self):
        """Empty string returns None (not ValueError)"""
        assert safe_int("") is None
        assert safe_int("  ") is None  # Whitespace only

    def test_safe_int_invalid_string(self):
        """Invalid string returns None (not ValueError)"""
        assert safe_int("abc") is None
        assert safe_int("12.34") is None  # Float string

    def test_safe_int_allow_zero_false(self):
        """When allow_zero=False, 0 returns None (for row_num validation)"""
        assert safe_int(0, allow_zero=False) is None
        assert safe_int("0", allow_zero=False) is None
        assert safe_int(1, allow_zero=False) == 1


class TestSafeIntListConversion:
    """Test safe_int_list handles all JSON array edge cases"""

    def test_safe_int_list_normal(self):
        """Normal list of integers"""
        assert safe_int_list([1, 2, 3]) == [1, 2, 3]

    def test_safe_int_list_string_numbers(self):
        """List of string numbers (common from JSON)"""
        assert safe_int_list(["1", "2", "3"]) == [1, 2, 3]

    def test_safe_int_list_mixed(self):
        """Mixed valid and invalid values - invalid filtered out"""
        assert safe_int_list([1, "2", None, "", "abc", 3]) == [1, 2, 3]

    def test_safe_int_list_empty(self):
        """Empty list returns empty list"""
        assert safe_int_list([]) == []

    def test_safe_int_list_none(self):
        """None returns empty list"""
        assert safe_int_list(None) == []

    def test_safe_int_list_filters_zero(self):
        """Zeros are filtered (row_nums start at 2)"""
        assert safe_int_list([0, 1, 2]) == [1, 2]
        assert safe_int_list(["0", "1", "2"]) == [1, 2]
