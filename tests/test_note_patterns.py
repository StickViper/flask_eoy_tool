"""
Test note pattern detection for batch note handling

Tests the pattern matching logic that identifies common notes
that can be batch-processed (removed, transformed, or archived).
"""

import pytest
import sys
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from note_patterns import (
    detect_patterns_in_note,
    split_notes,
    suggest_semicolon_insertion,
    get_ni_archive_text,
    COMMON_PATTERNS
)
from models import ProviderRow
from validation import detect_common_notes


class TestPatternDefinitions:
    """Test pattern definitions are complete"""

    def test_patterns_have_required_fields(self):
        """Each pattern should have id, regex, action, description"""
        for pattern in COMMON_PATTERNS:
            assert pattern.id, f"Pattern missing id: {pattern}"
            assert pattern.regex, f"Pattern {pattern.id} missing regex"
            assert pattern.action in ['remove', 'transform', 'archive_ni'], \
                f"Pattern {pattern.id} has invalid action: {pattern.action}"
            assert pattern.description, f"Pattern {pattern.id} missing description"

    def test_pattern_count(self):
        """Should have at least 10 patterns defined"""
        assert len(COMMON_PATTERNS) >= 10


class TestRemovePatterns:
    """Test patterns that mark notes for removal"""

    @pytest.mark.parametrize("note,expected_pattern", [
        ("Ask for Dr. Smith", "ask_for"),
        ("vm x3", "vm"),
        ("Call back tomorrow", "call_back"),
        ("Office closed for holiday", "office_closed"),
        ("Impossible to reach", "impossible_reach"),
        ("Number out of service", "number_out_of_service"),
        ("updated # try again", "updated_number"),
        ("gave my #", "gave_my_number"),
        ("john@example.com:sent", "email_sent"),
    ])
    def test_remove_patterns_match(self, note, expected_pattern):
        """Test each remove pattern matches correctly"""
        matches = detect_patterns_in_note(note)
        assert len(matches) >= 1, f"No match for '{note}'"
        pattern_ids = [m[0].id for m in matches]
        assert expected_pattern in pattern_ids, \
            f"Expected {expected_pattern} in {pattern_ids} for '{note}'"

    def test_vm_case_insensitive(self):
        """VM should match case-insensitively"""
        for note in ["VM", "vm", "Vm", "vM"]:
            matches = detect_patterns_in_note(note)
            assert any(m[0].id == 'vm' for m in matches), f"VM not matched: {note}"


class TestTransformPatterns:
    """Test patterns that transform notes"""

    def test_same_network_pattern(self):
        """'Same network - multiple locations' should match"""
        matches = detect_patterns_in_note("Same network - multiple locations")
        assert any(m[0].id == 'same_network' for m in matches)

    def test_same_network_variations(self):
        """Various network note formats should match"""
        variations = [
            "same network-multiple locations",
            "Same Network – Multiple Locations",
            "SAME NETWORK - MULTIPLE LOCATION",
        ]
        for note in variations:
            matches = detect_patterns_in_note(note)
            assert any(m[0].id == 'same_network' for m in matches), \
                f"No match for: {note}"


class TestArchiveNIPatterns:
    """Test patterns for Not Interested archiving"""

    def test_ni_already_pattern(self):
        """'Not interested: Already works' should match"""
        matches = detect_patterns_in_note("Not interested: Already works with someone")
        assert any(m[0].id == 'ni_already' for m in matches)

    def test_ni_dont_do_pattern(self):
        """'Not interested: Don't do OB' should match"""
        matches = detect_patterns_in_note("Not interested: Don't do OB anymore")
        assert any(m[0].id == 'ni_dont_do' for m in matches)

    def test_ni_enough_pattern(self):
        """'Not interested: Enough pamphlets' should match"""
        matches = detect_patterns_in_note("Not interested: Enough pamphlets")
        assert any(m[0].id == 'ni_enough' for m in matches)


class TestNoteSplitting:
    """Test semicolon-based note splitting"""

    def test_split_simple(self):
        """Split notes by semicolon"""
        chunks = split_notes("vm x2; callback tomorrow; sent email")
        assert len(chunks) == 3
        assert "vm x2" in chunks
        assert "callback tomorrow" in chunks
        assert "sent email" in chunks

    def test_split_empty(self):
        """Empty notes should return empty list"""
        assert split_notes("") == []
        assert split_notes(None) == []

    def test_split_no_semicolons(self):
        """Notes without semicolons should return single chunk"""
        chunks = split_notes("just one note here")
        assert len(chunks) == 1

    def test_split_trailing_semicolon(self):
        """Trailing semicolons should not create empty chunks"""
        chunks = split_notes("note one; note two;")
        assert len(chunks) == 2


class TestSemicolonSuggestion:
    """Test semicolon insertion suggestions"""

    def test_suggest_semicolons_needed(self):
        """Notes with multiple markers should suggest semicolons"""
        note = "vm x2 call back tomorrow sent email"
        suggested = suggest_semicolon_insertion(note)
        assert suggested is not None
        assert ';' in suggested

    def test_no_suggestion_with_semicolons(self):
        """Notes already having semicolons should not get suggestions"""
        note = "vm x2; call back tomorrow"
        suggested = suggest_semicolon_insertion(note)
        assert suggested is None

    def test_no_suggestion_single_item(self):
        """Single-item notes should not get suggestions"""
        note = "just one thing"
        suggested = suggest_semicolon_insertion(note)
        assert suggested is None


class TestNIArchiveText:
    """Test generation of archived NI text"""

    def test_archive_already(self):
        """Already pattern should archive the reason"""
        import re
        pattern = re.compile(r'\bnot\s+interested\s*[:\-]?\s*already\s+(\w+)', re.IGNORECASE)
        match = pattern.search("Not interested: Already works")
        text = get_ni_archive_text('ni_already', match)
        assert "Last time NI:" in text
        assert "Already" in text

    def test_archive_enough(self):
        """Enough pattern should archive simply"""
        import re
        pattern = re.compile(r'\bnot\s+interested\s*[:\-]?\s*enough\b', re.IGNORECASE)
        match = pattern.search("Not interested: enough")
        text = get_ni_archive_text('ni_enough', match)
        assert text == "Last time NI: Enough"


class TestDetectCommonNotesIntegration:
    """Integration tests for detect_common_notes with ProviderRow"""

    def _make_row(self, row_num, notes, status="Successful Order"):
        """Helper to create test rows"""
        return ProviderRow(
            row_num=row_num, practice="Test Practice", phone="555-123-4567",
            address="123 Main St", city="Anytown", state="TX", zip="12345",
            qty_2023="10", qty_2024="15", qty_2025="20",
            notes=notes, status=status, bg_color="#ffff00"
        )

    def test_detect_vm_note(self):
        """Should detect VM notes for removal"""
        rows = [self._make_row(1, "vm x2")]
        detect_common_notes(rows)

        vm_issues = [i for i in rows[0].issues if i.get('category') == 'notes_remove']
        assert len(vm_issues) >= 1

    def test_detect_network_note(self):
        """Should detect network notes for transformation"""
        rows = [self._make_row(1, "Same network - multiple locations")]
        detect_common_notes(rows)

        transform_issues = [i for i in rows[0].issues if i.get('category') == 'notes_transform']
        assert len(transform_issues) >= 1

    def test_detect_ni_note(self):
        """Should detect NI notes for archiving"""
        rows = [self._make_row(1, "Not interested: Already have someone", status="Not interested")]
        detect_common_notes(rows)

        ni_issues = [i for i in rows[0].issues if i.get('category') == 'notes_archive_ni']
        assert len(ni_issues) >= 1

    def test_skip_empty_notes(self):
        """Should skip rows with no notes"""
        rows = [self._make_row(1, ""), self._make_row(2, None)]
        detect_common_notes(rows)

        # No issues should be added for note patterns
        for row in rows:
            note_issues = [i for i in row.issues if i.get('category', '').startswith('notes_')]
            assert len(note_issues) == 0
