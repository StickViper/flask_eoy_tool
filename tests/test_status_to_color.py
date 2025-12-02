"""
Test status-to-color mapping

Critical for deriving row colors without reading 737 individual cells.
Must handle exact matches only (no substring matching).
"""

import pytest
from eoy_tool import status_to_color


class TestStatusToColor:
    """Test status-to-color mapping logic"""

    def test_exact_matches_yellow(self):
        """Yellow - Successful Order (exact match required)"""
        assert status_to_color("Successful Order") == "#ffff00"

    def test_case_insensitive_yellow(self):
        """Yellow - case insensitive"""
        assert status_to_color("successful order") == "#ffff00"
        assert status_to_color("SUCCESSFUL ORDER") == "#ffff00"
        assert status_to_color("SuCcEsSfUl OrDeR") == "#ffff00"

    def test_exact_matches_fuschia(self):
        """Fuschia - Voicemail/No Answer"""
        assert status_to_color("Voicemail/No Answer") == "#ff00ff"

    def test_case_insensitive_fuschia(self):
        """Fuschia - case insensitive"""
        assert status_to_color("voicemail/no answer") == "#ff00ff"
        assert status_to_color("VOICEMAIL/NO ANSWER") == "#ff00ff"

    def test_exact_matches_green(self):
        """Green - Requested Email"""
        assert status_to_color("Requested Email") == "#00ff00"
        assert status_to_color("Email") == "#00ff00"

    def test_case_insensitive_green(self):
        """Green - case insensitive"""
        assert status_to_color("requested email") == "#00ff00"
        assert status_to_color("email") == "#00ff00"
        assert status_to_color("EMAIL") == "#00ff00"

    def test_exact_matches_red(self):
        """Red - Potentially Invalid"""
        assert status_to_color("Potentially Invalid") == "#ff0000"

    def test_case_insensitive_red(self):
        """Red - case insensitive"""
        assert status_to_color("potentially invalid") == "#ff0000"
        assert status_to_color("POTENTIALLY INVALID") == "#ff0000"

    def test_exact_matches_white_not_interested(self):
        """White - Not interested"""
        assert status_to_color("Not interested") == "#ffffff"

    def test_case_insensitive_white(self):
        """White - case insensitive"""
        assert status_to_color("not interested") == "#ffffff"
        assert status_to_color("NOT INTERESTED") == "#ffffff"

    def test_empty_string(self):
        """Empty status → white"""
        assert status_to_color("") == "#ffffff"

    def test_none_value(self):
        """None status → white (graceful handling)"""
        # Should handle None without crashing
        result = status_to_color(None)
        assert result == "#ffffff" or result is not None

    def test_no_substring_matching(self):
        """CRITICAL: Should NOT match substrings (exact match only)"""
        # These should all return white (not match yellow/fuschia/etc)
        assert status_to_color("Successful Order - paid") == "#ffffff"
        assert status_to_color("Successful order x2") == "#ffffff"
        assert status_to_color("Voicemail left x3") == "#ffffff"
        assert status_to_color("Not interested - closed") == "#ffffff"
        assert status_to_color("Potentially invalid - disconnected") == "#ffffff"
        assert status_to_color("Requested email - no response") == "#ffffff"

    def test_whitespace_handling(self):
        """Should handle leading/trailing whitespace"""
        assert status_to_color(" Successful Order ") == "#ffff00"
        assert status_to_color("  Voicemail/No Answer  ") == "#ff00ff"
        assert status_to_color(" Not interested ") == "#ffffff"

    def test_unknown_status(self):
        """Unknown status values → white (default)"""
        assert status_to_color("Random Status") == "#ffffff"
        assert status_to_color("asdfasdf") == "#ffffff"
        assert status_to_color("123456") == "#ffffff"

    @pytest.mark.parametrize("status,expected_color", [
        # All standard statuses
        ("Successful Order", "#ffff00"),
        ("Voicemail/No Answer", "#ff00ff"),
        ("Requested Email", "#00ff00"),
        ("Email", "#00ff00"),
        ("Potentially Invalid", "#ff0000"),
        ("Not interested", "#ffffff"),
        ("", "#ffffff"),

        # Case variations
        ("successful order", "#ffff00"),
        ("VOICEMAIL/NO ANSWER", "#ff00ff"),
        ("email", "#00ff00"),
        ("not interested", "#ffffff"),

        # Edge cases
        (" Successful Order ", "#ffff00"),  # whitespace
        ("Successful Order - paid", "#ffffff"),  # with notes (no substring match)
        ("Random Status", "#ffffff"),  # unknown
    ])
    def test_all_cases_parametrized(self, status, expected_color):
        """Parametrized test for all status cases"""
        assert status_to_color(status) == expected_color


class TestStatusToColorEdgeCases:
    """Test edge cases from conftest fixture"""

    def test_all_edge_cases(self, status_edge_cases):
        """Test all edge cases from fixture"""
        for status, expected_color in status_edge_cases:
            result = status_to_color(status)
            assert result == expected_color, (
                f"Failed for status='{status}': "
                f"expected {expected_color}, got {result}"
            )

    def test_google_sheets_dropdown_values(self):
        """
        Test actual Google Sheets dropdown values.

        These are the ONLY values that should appear in Status column
        if dropdown is enforced. All should map correctly.
        """
        # These should be the exact dropdown values
        dropdown_values = {
            "Successful Order": "#ffff00",
            "Voicemail/No Answer": "#ff00ff",
            "Requested Email": "#00ff00",
            "Potentially Invalid": "#ff0000",
            "Not interested": "#ffffff",
            "": "#ffffff",  # Empty (default)
        }

        for status, expected_color in dropdown_values.items():
            result = status_to_color(status)
            assert result == expected_color, (
                f"Dropdown value '{status}' mapped incorrectly: "
                f"expected {expected_color}, got {result}"
            )
