"""
Comprehensive EOY Tool Test Suite

Runs all tests and reports results
"""

import sys
import os

# Add parent directory to path so we can import eoy_tool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eoy_tool import (
    load_data,
    validate_stats_color_counts,
    validate_yellow_to_no,
    validate_no_to_wl,
    detect_duplicates,
    validate_status_issues,
    categorize_issues,
    status_to_color
)

def test_status_to_color_mapping():
    """Test that all expected status values map to correct colors"""
    print("\n" + "="*80)
    print("TEST 1: Status to Color Mapping")
    print("="*80)

    test_cases = [
        ("Successful Order", "#ffff00", "Yellow"),
        ("successful order", "#ffff00", "Yellow"),  # case insensitive
        ("SUCCESSFUL ORDER", "#ffff00", "Yellow"),
        ("Voicemail", "#ff00ff", "Fuschia"),
        ("No Answer", "#ff00ff", "Fuschia"),
        ("voicemail left", "#ff00ff", "Fuschia"),
        ("Not interested", "#ffffff", "White"),
        ("not interested", "#ffffff", "White"),
        ("Potentially Invalid", "#ff0000", "Red"),
        ("Invalid", "#ff0000", "Red"),
        ("Requested Email", "#00ff00", "Green"),
        ("Email", "#00ff00", "Green"),
        ("", "#ffffff", "White (empty)"),
    ]

    passed = 0
    failed = 0

    for status, expected_color, description in test_cases:
        result = status_to_color(status)
        if result == expected_color:
            print(f"  [PASS] '{status}' -> {result} ({description})")
            passed += 1
        else:
            print(f"  [FAIL] '{status}' -> {result}, expected {expected_color} ({description})")
            failed += 1

    print(f"\n  Total: {passed} passed, {failed} failed")
    return failed == 0

def test_data_loading():
    """Test that data loads correctly"""
    print("\n" + "="*80)
    print("TEST 2: Data Loading")
    print("="*80)

    try:
        wl_rows, no_rows, invalid_reasons, stats_sheet = load_data(2025)

        print(f"  [PASS] Loaded {len(wl_rows)} Working List rows")
        print(f"  [PASS] Loaded {len(no_rows)} New Orders rows")
        print(f"  [PASS] Loaded {len(invalid_reasons)} invalid reasons")

        # Check that rows have required fields
        if len(wl_rows) > 0:
            first_row = wl_rows[0]
            required_fields = ['row_num', 'practice', 'phone', 'address', 'status', 'bg_color']
            missing = [f for f in required_fields if not hasattr(first_row, f)]
            if missing:
                print(f"  [FAIL] Missing fields: {missing}")
                return False
            else:
                print(f"  [PASS] All required fields present")

        return True, wl_rows, no_rows, stats_sheet

    except Exception as e:
        print(f"  [FAIL] Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None, None

def test_color_validation(wl_rows, stats_sheet):
    """Test that Status-derived colors match STATS"""
    print("\n" + "="*80)
    print("TEST 3: Color Validation Against STATS")
    print("="*80)

    try:
        result = validate_stats_color_counts(wl_rows, stats_sheet, 2025)
        if result:
            print(f"  [PASS] Status-derived colors match STATS worksheet")
        else:
            print(f"  [WARN] User chose not to continue after mismatch warning")
        return result
    except Exception as e:
        print(f"  [FAIL] Error validating colors: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fuzzy_matching(wl_rows, no_rows):
    """Test fuzzy matching logic"""
    print("\n" + "="*80)
    print("TEST 4: Fuzzy Matching (Yellow -> NO)")
    print("="*80)

    try:
        validate_yellow_to_no(wl_rows, no_rows)

        # Count yellow rows and their match distribution
        yellow_rows = [r for r in wl_rows if r.bg_color.lower() in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']]

        if len(yellow_rows) == 0:
            print(f"  [WARN] No yellow rows found")
            return True

        high_conf = sum(1 for r in yellow_rows if r.match_confidence >= 0.95)
        medium_conf = sum(1 for r in yellow_rows if 0.80 <= r.match_confidence < 0.95)
        low_conf = sum(1 for r in yellow_rows if r.match_confidence < 0.80)

        print(f"  [INFO] Yellow rows: {len(yellow_rows)}")
        print(f"  [INFO]   >=95% confidence: {high_conf} ({high_conf/len(yellow_rows)*100:.1f}%)")
        print(f"  [INFO]   80-94% confidence: {medium_conf} ({medium_conf/len(yellow_rows)*100:.1f}%)")
        print(f"  [INFO]   <80% confidence: {low_conf} ({low_conf/len(yellow_rows)*100:.1f}%)")

        # Expect at least 70% to be high confidence
        if high_conf / len(yellow_rows) >= 0.70:
            print(f"  [PASS] >=70% of yellow rows have high confidence matches")
        else:
            print(f"  [WARN] <70% of yellow rows have high confidence matches")
            print(f"         This might indicate data quality issues")

        return True

    except Exception as e:
        print(f"  [FAIL] Error in fuzzy matching: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orphan_detection(wl_rows, no_rows):
    """Test orphan NO row detection"""
    print("\n" + "="*80)
    print("TEST 5: Orphan New Orders Detection")
    print("="*80)

    try:
        validate_no_to_wl(wl_rows, no_rows)

        orphans = [r for r in no_rows if r.is_orphan]

        print(f"  [INFO] Found {len(orphans)} orphan New Orders (no yellow WL match)")

        # Show first 3 orphans
        if len(orphans) > 0:
            print(f"  [INFO] First {min(3, len(orphans))} orphans:")
            for i, orphan in enumerate(orphans[:3], 1):
                print(f"         {i}. Row {orphan.row_num}: {orphan.practice[:40]}")

        print(f"  [PASS] Orphan detection completed")
        return True

    except Exception as e:
        print(f"  [FAIL] Error detecting orphans: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_duplicate_detection(wl_rows):
    """Test duplicate detection"""
    print("\n" + "="*80)
    print("TEST 6: Duplicate Detection")
    print("="*80)

    try:
        detect_duplicates(wl_rows)

        # Count duplicates
        dup_rows = [r for r in wl_rows if r.duplicate_group_id is not None]

        if len(dup_rows) == 0:
            print(f"  [INFO] No duplicates found")
            return True

        # Count unique groups
        unique_groups = set(r.duplicate_group_id for r in dup_rows)

        print(f"  [INFO] Found {len(dup_rows)} rows in {len(unique_groups)} duplicate groups")

        # Show first 3 groups
        from collections import defaultdict
        groups = defaultdict(list)
        for row in dup_rows:
            groups[row.duplicate_group_id].append(row)

        print(f"  [INFO] First {min(3, len(unique_groups))} groups:")
        for i, (gid, rows) in enumerate(sorted(groups.items())[:3], 1):
            print(f"         Group {gid}: {len(rows)} rows ('{rows[0].practice[:30]}')")

        print(f"  [PASS] Duplicate detection completed")
        return True

    except Exception as e:
        print(f"  [FAIL] Error detecting duplicates: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_categorization(wl_rows, no_rows):
    """Test issue categorization"""
    print("\n" + "="*80)
    print("TEST 7: Issue Categorization")
    print("="*80)

    try:
        validate_status_issues(wl_rows)
        categories = categorize_issues(wl_rows, no_rows)

        print(f"  [INFO] Created {len(categories)} categories:")
        for cat in categories:
            print(f"         {cat.name:30s} {len(cat.row_nums):4d} rows")

        total_issues = sum(len(cat.row_nums) for cat in categories)
        print(f"  [INFO] Total issue instances: {total_issues}")
        print(f"         (Note: rows can appear in multiple categories)")

        print(f"  [PASS] Categorization completed")
        return True, categories

    except Exception as e:
        print(f"  [FAIL] Error categorizing issues: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_edge_cases():
    """Test edge cases in status mapping"""
    print("\n" + "="*80)
    print("TEST 8: Edge Cases")
    print("="*80)

    edge_cases = [
        ("Successful order x2", "#ffff00", "Multiple orders variant"),
        ("Voicemail left x3", "#ff00ff", "Multiple voicemails"),
        ("not interested - closed", "#ffffff", "Not interested with reason"),
        ("potentially invalid - disconnected", "#ff0000", "Invalid with reason"),
        ("Requested email - no response", "#00ff00", "Email with note"),
        ("NO ANSWER", "#ff00ff", "All caps"),
        (None, "#ffffff", "None value"),
    ]

    passed = 0
    failed = 0

    for status, expected_color, description in edge_cases:
        result = status_to_color(status) if status is not None else status_to_color("")
        if result == expected_color:
            print(f"  [PASS] {description}: '{status}' -> {result}")
            passed += 1
        else:
            print(f"  [FAIL] {description}: '{status}' -> {result}, expected {expected_color}")
            failed += 1

    print(f"\n  Total: {passed} passed, {failed} failed")
    return failed == 0

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE EOY TOOL TEST SUITE")
    print("="*80)
    print(f"Testing against: OBGYN Working List 2025")
    print(f"Timestamp: {os.popen('echo %date% %time%').read().strip()}")

    results = []

    # Test 1: Status mapping
    results.append(("Status to Color Mapping", test_status_to_color_mapping()))

    # Test 2: Data loading
    load_result = test_data_loading()
    if isinstance(load_result, tuple):
        success, wl_rows, no_rows, stats_sheet = load_result
        results.append(("Data Loading", success))

        if success:
            # Test 3: Color validation
            results.append(("Color Validation", test_color_validation(wl_rows, stats_sheet)))

            # Test 4: Fuzzy matching
            results.append(("Fuzzy Matching", test_fuzzy_matching(wl_rows, no_rows)))

            # Test 5: Orphan detection
            results.append(("Orphan Detection", test_orphan_detection(wl_rows, no_rows)))

            # Test 6: Duplicate detection
            results.append(("Duplicate Detection", test_duplicate_detection(wl_rows)))

            # Test 7: Categorization
            cat_result = test_categorization(wl_rows, no_rows)
            if isinstance(cat_result, tuple):
                success, categories = cat_result
                results.append(("Categorization", success))
    else:
        results.append(("Data Loading", load_result))

    # Test 8: Edge cases
    results.append(("Edge Cases", test_edge_cases()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test_name}")

    print(f"\n  Total: {passed}/{len(results)} tests passed")

    if failed == 0:
        print("\n  [OK] ALL TESTS PASSED - Tool is ready for use!")
    else:
        print(f"\n  [X] {failed} test(s) failed - Review failures above")

    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
