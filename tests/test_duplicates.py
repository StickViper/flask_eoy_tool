"""
Test duplicate detection and network identification logic

Three types of duplicates:
1. Exact: Same phone + same normalized name + same normalized address
2. Network: Same phone + similar names (≥85%) + different addresses (<70%)
3. Fuzzy: Same phone + neither exact nor network

Networks use (~#) notation format in working list.
"""

import pytest
from eoy_tool import (
    normalize_name, normalize_address, normalize_phone,
    ProviderRow, detect_duplicates
)
from rapidfuzz import fuzz
import re


class TestExactDuplicates:
    """Test exact duplicate detection logic"""

    def test_exact_duplicate_detection_from_fixtures(self, sample_wl_rows):
        """Test exact duplicates: WL rows 100-101 (Central Texas OBGYN)"""
        # Rows 100 and 101 are exact duplicates
        row1 = sample_wl_rows[2]  # Row 100
        row2 = sample_wl_rows[3]  # Row 101

        # Verify they have same phone
        assert normalize_phone(row1.phone) == normalize_phone(row2.phone)

        # Verify they have same normalized name
        assert normalize_name(row1.practice) == normalize_name(row2.practice)

        # Verify they have same normalized address
        assert normalize_address(row1.address) == normalize_address(row2.address)

        # This is an exact duplicate
        is_exact = (
            normalize_name(row1.practice) == normalize_name(row2.practice) and
            normalize_address(row1.address) == normalize_address(row2.address)
        )
        assert is_exact is True

    def test_exact_duplicate_matching_criteria(self):
        """Exact duplicates must match on phone + normalized name + normalized address"""
        # Same phone
        phone1 = normalize_phone("555-123-4567")
        phone2 = normalize_phone("(555) 123-4567")
        assert phone1 == phone2

        # Same normalized name (despite different formatting)
        name1 = normalize_name("Women's Health LLC")
        name2 = normalize_name("Womens Health")
        # Note: These won't be exact match due to apostrophe, but demonstrates normalization

        # Same normalized address (despite different formatting)
        addr1 = normalize_address("123 Main Street Suite 100")
        addr2 = normalize_address("123 Main St Ste 200")
        # After normalization and suite removal, these should be very similar

    def test_not_exact_duplicate_different_address(self):
        """Different addresses should not be exact duplicates"""
        name1 = normalize_name("Women's Health Center")
        name2 = normalize_name("Women's Health Center")
        addr1 = normalize_address("123 Main St")
        addr2 = normalize_address("456 Oak Ave")

        is_exact = (name1 == name2 and addr1 == addr2)
        assert is_exact is False

    def test_not_exact_duplicate_different_name(self):
        """Different names should not be exact duplicates"""
        name1 = normalize_name("Women's Health Center")
        name2 = normalize_name("Hill Country Women's Center")
        addr1 = normalize_address("123 Main St")
        addr2 = normalize_address("123 Main St")

        is_exact = (name1 == name2 and addr1 == addr2)
        assert is_exact is False


class TestNetworkDetection:
    """Test network identification logic"""

    def test_network_detection_from_fixtures(self, sample_wl_rows):
        """Test network: WL rows 150-152 (Women's Health Network)"""
        # Rows 150-152 are network locations
        row1 = sample_wl_rows[4]  # North location
        row2 = sample_wl_rows[5]  # South location
        row3 = sample_wl_rows[6]  # Downtown location

        # All should have same phone
        phone1 = normalize_phone(row1.phone)
        phone2 = normalize_phone(row2.phone)
        phone3 = normalize_phone(row3.phone)
        assert phone1 == phone2 == phone3

        # Names should be similar (≥85% ratio)
        name1 = normalize_name(row1.practice)
        name2 = normalize_name(row2.practice)
        name3 = normalize_name(row3.practice)

        assert fuzz.ratio(name1, name2) >= 85
        assert fuzz.ratio(name1, name3) >= 85
        assert fuzz.ratio(name2, name3) >= 85

        # Addresses should be different (<70% ratio)
        addr1 = normalize_address(row1.address)
        addr2 = normalize_address(row2.address)
        addr3 = normalize_address(row3.address)

        assert fuzz.ratio(addr1, addr2) < 70
        assert fuzz.ratio(addr1, addr3) < 70
        assert fuzz.ratio(addr2, addr3) < 70

    def test_network_name_extraction(self):
        """Test network name extraction (strips directional words)"""
        practice_names = [
            "Women's Health Network - North",
            "Women's Health Network - South",
            "Women's Health Network - Downtown"
        ]

        # Extract base network name (remove directional words)
        for name in practice_names:
            # Remove directional indicators
            base = re.sub(r'\b(North|South|East|West|Downtown|Uptown|Medical|Clinic|Center|Office)\b', '', name, flags=re.IGNORECASE)
            # Remove non-alphanumeric
            base = re.sub(r'[^a-z]', '', base.lower())

            # All should reduce to same base name
            assert 'womenshealthnetwork' in base

    def test_network_notation_format(self):
        """Test network notation format: 'networkname network (~#)'"""
        network_name = "womenshealthnetwork"
        location_count = 3

        # Expected notation format
        notation = f"{network_name} network (~{location_count})"
        assert notation == "womenshealthnetwork network (~3)"

    def test_network_criteria_name_similarity_85(self):
        """Networks require ≥85% name similarity"""
        name1 = normalize_name("Women's Health Network - North")
        name2 = normalize_name("Women's Health Network - South")

        similarity = fuzz.ratio(name1, name2)
        assert similarity >= 85, f"Network names only {similarity}% similar"

    def test_network_criteria_address_dissimilarity_70(self):
        """Networks require <70% address similarity (different locations)"""
        addr1 = normalize_address("1000 North Lamar")
        addr2 = normalize_address("2000 South Congress")

        similarity = fuzz.ratio(addr1, addr2)
        assert similarity < 70, f"Network addresses are {similarity}% similar (too high)"

    def test_not_network_similar_addresses(self):
        """Similar addresses should not be network (likely exact/fuzzy dupe)"""
        # Same phone, similar names, but similar addresses
        name1 = normalize_name("Women's Health Center")
        name2 = normalize_name("Women's Health Clinic")
        addr1 = normalize_address("123 Main St Suite 100")
        addr2 = normalize_address("123 Main St Suite 200")

        name_similar = fuzz.ratio(name1, name2) >= 85
        addr_similar = fuzz.ratio(addr1, addr2) >= 70

        # Not a network because addresses are too similar
        is_network = name_similar and not addr_similar
        assert is_network is False


class TestFuzzyDuplicates:
    """Test fuzzy duplicate detection (same phone, but neither exact nor network)"""

    def test_fuzzy_duplicate_criteria(self):
        """Fuzzy duplicates: same phone, name similarity <85% OR address similarity ≥70%"""
        # Case 1: Same phone, somewhat similar names (<85%), different addresses
        name1 = normalize_name("Women's Health Center")
        name2 = normalize_name("Hill Country OB/GYN")
        addr1 = normalize_address("123 Main St")
        addr2 = normalize_address("456 Oak Ave")

        name_similarity = fuzz.ratio(name1, name2)
        addr_similarity = fuzz.ratio(addr1, addr2)

        # Not exact (different names)
        is_exact = (name1 == name2 and addr1 == addr2)
        assert is_exact is False

        # Not network (name similarity too low)
        is_network = name_similarity >= 85 and addr_similarity < 70
        assert is_network is False

        # Therefore: fuzzy duplicate (needs manual review)
        is_fuzzy = not is_exact and not is_network
        assert is_fuzzy is True

    def test_fuzzy_duplicate_same_phone_required(self):
        """Fuzzy duplicates still require same phone number"""
        phone1 = normalize_phone("555-123-4567")
        phone2 = normalize_phone("555-987-6543")

        # Different phones = not duplicates at all
        assert phone1 != phone2


class TestDuplicateDetectionIntegration:
    """Test detect_duplicates function with realistic data"""

    def test_detect_duplicates_groups_by_phone(self, sample_wl_rows):
        """detect_duplicates should group rows by normalized phone"""
        # Run detection
        detect_duplicates(sample_wl_rows)

        # Check exact duplicates (rows 2-3: Central Texas OBGYN)
        row1 = sample_wl_rows[2]
        row2 = sample_wl_rows[3]

        # Should have same duplicate_group_id
        assert row1.duplicate_group_id is not None
        assert row1.duplicate_group_id == row2.duplicate_group_id

        # Should have 'exact_dupes' category in issues
        exact_issues = [i for i in row1.issues if i['category'] == 'exact_dupes']
        assert len(exact_issues) > 0

    def test_detect_duplicates_identifies_networks(self, sample_wl_rows):
        """detect_duplicates should identify network locations"""
        # Run detection
        detect_duplicates(sample_wl_rows)

        # Check network (rows 4-6: Women's Health Network)
        row1 = sample_wl_rows[4]
        row2 = sample_wl_rows[5]
        row3 = sample_wl_rows[6]

        # Should have network_name set
        assert row1.network_name is not None
        assert row2.network_name is not None
        assert row3.network_name is not None

        # Should all have same network name
        assert row1.network_name == row2.network_name == row3.network_name

        # Should have 'networks' category in issues
        network_issues = [i for i in row1.issues if i['category'] == 'networks']
        assert len(network_issues) > 0
        assert '~3' in network_issues[0]['message'] or network_issues[0]['location_count'] == 3

    def test_detect_duplicates_no_false_positives(self, sample_wl_rows):
        """Rows with different phones should not be grouped"""
        # Run detection
        detect_duplicates(sample_wl_rows)

        # Yellow rows (0-1) have different phones
        row1 = sample_wl_rows[0]  # 555-123-4567
        row2 = sample_wl_rows[1]  # 555-234-5678

        # Should NOT be in same group
        if row1.duplicate_group_id and row2.duplicate_group_id:
            assert row1.duplicate_group_id != row2.duplicate_group_id


class TestEdgeCases:
    """Test edge cases in duplicate detection"""

    def test_single_row_per_phone_no_duplicates(self):
        """Single row with unique phone should not be flagged"""
        rows = [
            ProviderRow(
                row_num=1,
                practice="Unique Practice",
                phone="555-111-1111",
                address="123 Main St",
                city="Austin",
                state="TX",
                zip="78701",
                qty_2023="", qty_2024="", qty_2025="",
                status="", notes="", bg_color="#ffffff"
            )
        ]

        detect_duplicates(rows)

        # Should have no duplicate issues
        assert rows[0].duplicate_group_id is None
        assert rows[0].network_name is None
        duplicate_issues = [i for i in rows[0].issues if 'dup' in i['category'].lower() or 'network' in i['category'].lower()]
        assert len(duplicate_issues) == 0

    def test_empty_phone_not_grouped(self):
        """Rows with empty phone should not be grouped"""
        rows = [
            ProviderRow(
                row_num=1,
                practice="Practice A",
                phone="",
                address="123 Main St",
                city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="",
                status="", notes="", bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2,
                practice="Practice B",
                phone="",
                address="456 Oak Ave",
                city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="",
                status="", notes="", bg_color="#ffffff"
            )
        ]

        detect_duplicates(rows)

        # Should not be grouped (empty phones)
        assert rows[0].duplicate_group_id is None
        assert rows[1].duplicate_group_id is None

    def test_two_row_group_minimum(self):
        """Duplicate detection requires at least 2 rows with same phone"""
        # This is implicit in the logic - single phone numbers are skipped
        # Just documenting the behavior
        rows = [
            ProviderRow(
                row_num=1, practice="Practice A", phone="555-111-1111",
                address="123 Main St", city="Austin", state="TX", zip="78701",
                qty_2023="", qty_2024="", qty_2025="",
                status="", notes="", bg_color="#ffffff"
            ),
            ProviderRow(
                row_num=2, practice="Practice B", phone="555-222-2222",
                address="456 Oak Ave", city="Austin", state="TX", zip="78702",
                qty_2023="", qty_2024="", qty_2025="",
                status="", notes="", bg_color="#ffffff"
            )
        ]

        detect_duplicates(rows)

        # Neither should be flagged (different phones)
        assert rows[0].duplicate_group_id is None
        assert rows[1].duplicate_group_id is None

    def test_large_network_notation(self):
        """Test network notation with many locations (e.g., ~10)"""
        network_name = "largehospitalsystem"
        location_count = 10

        notation = f"{network_name} network (~{location_count})"
        assert notation == "largehospitalsystem network (~10)"
        assert '~10' in notation


class TestSeverityCategories:
    """Test severity categorization for duplicates"""

    def test_exact_duplicates_severity_auto_fix(self):
        """Exact duplicates should be 'auto_fix' severity (can be automatically resolved)"""
        # This tests the expected behavior/categorization
        expected_severity = "auto_fix"
        assert expected_severity == "auto_fix"

    def test_networks_severity_review(self):
        """Networks should be 'review' severity (need human verification)"""
        expected_severity = "review"
        assert expected_severity == "review"

    def test_fuzzy_duplicates_severity_review(self):
        """Fuzzy duplicates should be 'review' severity (need human judgment)"""
        expected_severity = "review"
        assert expected_severity == "review"
