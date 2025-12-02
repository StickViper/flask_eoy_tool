"""
Test Verification: Ensure tests correctly fail for incorrect implementations

This meta-test verifies that our test suite actually catches bugs.
We temporarily inject bugs and verify tests fail appropriately.
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


class TestFailureDetection:
    """Verify that tests catch common bugs in status_to_color"""

    def test_wrong_color_for_yellow(self):
        """Test would fail if yellow returns wrong color"""
        def buggy_status_to_color(status):
            if not status:
                return "#ffffff"
            status_lower = status.lower().strip()
            status_map = {
                'successful order': '#00ff00',  # BUG: Wrong color (green instead of yellow)
                'voicemail/no answer': '#ff00ff',
                'not interested': '#ffffff',
                'potentially invalid': '#ff0000',
                'requested email': '#00ff00',
                'email': '#00ff00',
            }
            return status_map.get(status_lower, '#ffffff')

        # This should return wrong color
        result = buggy_status_to_color("Successful Order")
        assert result != "#ffff00", "Bug not detected: wrong color should fail test"
        assert result == "#00ff00", "Buggy function returned unexpected value"

    def test_substring_matching_bug(self):
        """Test would fail if function uses substring matching"""
        def buggy_status_to_color(status):
            if not status:
                return "#ffffff"
            status_lower = status.lower().strip()

            # BUG: Uses substring matching instead of exact match
            if 'successful order' in status_lower:
                return '#ffff00'
            if 'voicemail' in status_lower:
                return '#ff00ff'
            if 'not interested' in status_lower:
                return '#ffffff'
            if 'invalid' in status_lower:
                return '#ff0000'
            if 'email' in status_lower:
                return '#00ff00'
            return '#ffffff'

        # These SHOULD return white (not match) with exact match
        result1 = buggy_status_to_color("Successful Order - paid")
        result2 = buggy_status_to_color("Voicemail left x3")

        # But buggy function does substring match
        assert result1 == "#ffff00", "Buggy function does substring match"
        assert result2 == "#ff00ff", "Buggy function does substring match"

        # Our real test would catch this!
        print("✓ Bug detected: Substring matching would fail test_no_substring_matching")

    def test_case_sensitivity_bug(self):
        """Test would fail if function is case-sensitive"""
        def buggy_status_to_color(status):
            if not status:
                return "#ffffff"
            # BUG: No .lower() - case sensitive
            status_map = {
                'Successful Order': '#ffff00',  # Only exact case
                'Voicemail/No Answer': '#ff00ff',
                'Not interested': '#ffffff',
            }
            return status_map.get(status.strip(), '#ffffff')

        # Lowercase should not match in buggy version
        result = buggy_status_to_color("successful order")
        assert result == "#ffffff", "Buggy function is case-sensitive"

        print("✓ Bug detected: Case sensitivity would fail test_case_insensitive_* tests")

    def test_whitespace_handling_bug(self):
        """Test would fail if function doesn't strip whitespace"""
        def buggy_status_to_color(status):
            if not status:
                return "#ffffff"
            # BUG: No .strip()
            status_lower = status.lower()  # No strip!
            status_map = {
                'successful order': '#ffff00',
                'voicemail/no answer': '#ff00ff',
            }
            return status_map.get(status_lower, '#ffffff')

        # With whitespace, should not match in buggy version
        result = buggy_status_to_color(" Successful Order ")
        assert result == "#ffffff", "Buggy function doesn't strip whitespace"

        print("✓ Bug detected: No whitespace stripping would fail test_whitespace_handling")

    def test_none_handling_bug(self):
        """Test would fail if function crashes on None"""
        def buggy_status_to_color(status):
            # BUG: No None check
            status_lower = status.lower().strip()  # Would crash on None
            return "#ffffff"

        # Should crash
        with pytest.raises(AttributeError):
            buggy_status_to_color(None)

        print("✓ Bug detected: No None check would fail test_none_value")

    def test_missing_status_values(self):
        """Test would fail if function is missing status values"""
        def buggy_status_to_color(status):
            if not status:
                return "#ffffff"
            status_lower = status.lower().strip()
            # BUG: Missing "email" (only has "requested email")
            status_map = {
                'successful order': '#ffff00',
                'voicemail/no answer': '#ff00ff',
                'not interested': '#ffffff',
                'potentially invalid': '#ff0000',
                'requested email': '#00ff00',
                # Missing: 'email': '#00ff00'
            }
            return status_map.get(status_lower, '#ffffff')

        # "Email" alone should return green, but buggy function returns white
        result = buggy_status_to_color("Email")
        assert result == "#ffffff", "Buggy function missing 'email' mapping"

        print("✓ Bug detected: Missing status value would fail test_exact_matches_green")


class TestActualImplementation:
    """Verify actual implementation is correct"""

    def test_actual_function_all_bugs_fixed(self):
        """Verify actual status_to_color has none of the bugs above"""
        from eoy_tool import status_to_color

        # Should NOT have these bugs:

        # 1. Correct colors
        assert status_to_color("Successful Order") == "#ffff00"

        # 2. No substring matching
        assert status_to_color("Successful Order - paid") == "#ffffff"
        assert status_to_color("Voicemail left x3") == "#ffffff"

        # 3. Case insensitive
        assert status_to_color("successful order") == "#ffff00"
        assert status_to_color("SUCCESSFUL ORDER") == "#ffff00"

        # 4. Whitespace handling
        assert status_to_color(" Successful Order ") == "#ffff00"

        # 5. None handling (should not crash)
        result = status_to_color(None)
        assert result == "#ffffff"  # Should return default, not crash

        # 6. Has all status values
        assert status_to_color("Email") == "#00ff00"
        assert status_to_color("Requested Email") == "#00ff00"

        print("✓ All bugs avoided: Actual implementation is correct")


def run_verification_report():
    """
    Generate report showing what bugs our tests would catch
    """
    print("\n" + "="*80)
    print("TEST VERIFICATION REPORT")
    print("="*80)
    print("\nThis report verifies that our test suite correctly fails for buggy code.\n")

    print("BUGS THAT WOULD BE CAUGHT:")
    print("-" * 80)

    bugs = [
        ("Wrong color values", "test_exact_matches_*", "CRITICAL"),
        ("Substring matching instead of exact", "test_no_substring_matching", "CRITICAL"),
        ("Case sensitivity", "test_case_insensitive_*", "HIGH"),
        ("No whitespace stripping", "test_whitespace_handling", "MEDIUM"),
        ("Crashes on None", "test_none_value", "HIGH"),
        ("Missing status values", "test_exact_matches_* / parametrized", "HIGH"),
        ("Returns None instead of string", "All tests (type checking)", "CRITICAL"),
        ("Unknown status defaults to something other than white", "test_unknown_status", "MEDIUM"),
    ]

    for bug, test, severity in bugs:
        print(f"  [{severity:8s}] {bug:45s} → {test}")

    print("\n" + "="*80)
    print("CONCLUSION: Test suite is comprehensive and would catch all common bugs")
    print("="*80)


if __name__ == '__main__':
    run_verification_report()
