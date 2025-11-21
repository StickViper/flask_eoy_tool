"""
Test validation logic with real OBGYN data
Analyze fuzzy matching, orphans, categories to understand issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from eoy_tool
from eoy_tool import (
    load_data,
    validate_stats_color_counts,
    validate_yellow_to_no,
    validate_no_to_wl,
    detect_duplicates,
    validate_status_issues,
    auto_fix_not_interested,
    detect_non_standard_notes,
    categorize_issues
)

def test_validation():
    """Run validation and analyze results"""

    print("="*80)
    print("TESTING EOY VALIDATION LOGIC WITH REAL DATA")
    print("="*80)

    # Load data
    print("\n[1] Loading data...")
    wl_rows, no_rows, invalid_reasons, stats_sheet = load_data(2025)

    print(f"[OK] Loaded {len(wl_rows)} Working List rows")
    print(f"[OK] Loaded {len(no_rows)} New Orders rows")
    print(f"[OK] Found {len(invalid_reasons)} common invalid reasons")

    # Validate Status-derived colors against STATS
    print("\n[2] Validating Status-derived colors against STATS...")
    if not validate_stats_color_counts(wl_rows, stats_sheet, 2025):
        print("[FAIL] Status/color validation failed. User chose to exit.")
        return

    # Check color distribution
    print("\n[3] Analyzing color distribution...")
    color_counts = {}
    for row in wl_rows:
        color = row.bg_color.lower()
        color_counts[color] = color_counts.get(color, 0) + 1

    print("\nColor distribution:")
    for color, count in sorted(color_counts.items(), key=lambda x: -x[1]):
        print(f"  {color}: {count} rows")

    # Run yellow matching
    print("\n[3] Testing yellow -> New Orders matching...")
    validate_yellow_to_no(wl_rows, no_rows)

    # Analyze match results
    yellow_rows = [r for r in wl_rows if r.bg_color.lower() in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']]
    print(f"\nYellow rows: {len(yellow_rows)}")

    confidence_buckets = {
        '95%+': 0,
        '80-94%': 0,
        '60-79%': 0,
        '<60%': 0,
        'No match': 0
    }

    for row in yellow_rows:
        conf = row.match_confidence
        if conf >= 0.95:
            confidence_buckets['95%+'] += 1
        elif conf >= 0.80:
            confidence_buckets['80-94%'] += 1
        elif conf >= 0.60:
            confidence_buckets['60-79%'] += 1
        elif conf > 0:
            confidence_buckets['<60%'] += 1
        else:
            confidence_buckets['No match'] += 1

    print("\nMatch confidence distribution:")
    for bucket, count in confidence_buckets.items():
        pct = (count / len(yellow_rows) * 100) if yellow_rows else 0
        print(f"  {bucket}: {count} ({pct:.1f}%)")

    # Show some examples of low-confidence matches
    print("\n[4] Sample low-confidence matches (<80%):")
    low_conf = [r for r in yellow_rows if 0 < r.match_confidence < 0.80][:5]
    for row in low_conf:
        print(f"\n  Row {row.row_num}: {row.practice}")
        print(f"    WL Address: {row.address}, {row.city}, {row.state}")
        print(f"    Confidence: {row.match_confidence*100:.1f}%")
        if row.matched_no_row:
            no_row = next((n for n in no_rows if n.row_num == row.matched_no_row), None)
            if no_row:
                print(f"    NO Match: {no_row.practice}")
                print(f"    NO Address: {no_row.address}, {no_row.city}, {no_row.state}")

    # Run reverse validation (orphan check)
    print("\n[5] Testing New Orders -> Working List (orphan detection)...")
    validate_no_to_wl(wl_rows, no_rows)

    orphan_no_rows = [r for r in no_rows if r.is_orphan]
    print(f"\nOrphan New Orders: {len(orphan_no_rows)} / {len(no_rows)} ({len(orphan_no_rows)/len(no_rows)*100:.1f}%)")

    # Show some orphan examples
    print("\n[6] Sample orphan New Orders (first 10):")
    for row in orphan_no_rows[:10]:
        print(f"\n  NO Row {row.row_num}: {row.practice}")
        print(f"    Address: {row.address}, {row.city}, {row.state}")
        print(f"    QTY: {row.qty_2025}")

        # Try to find similar in WL manually
        from eoy_tool import normalize_name
        similar_wl = []
        for wl in wl_rows:
            if wl.state == row.state:
                from rapidfuzz import fuzz
                name_sim = fuzz.token_set_ratio(normalize_name(wl.practice), normalize_name(row.practice))
                if name_sim > 70:
                    similar_wl.append((wl, name_sim))

        if similar_wl:
            similar_wl.sort(key=lambda x: -x[1])
            print(f"    Possible WL matches:")
            for wl, sim in similar_wl[:3]:
                print(f"      - Row {wl.row_num}: {wl.practice} (name sim: {sim}%, color: {wl.bg_color})")

    # Run other validations
    print("\n[7] Running duplicate detection...")
    detect_duplicates(wl_rows)

    print("\n[8] Running status validation...")
    validate_status_issues(wl_rows)

    print("\n[9] Auto-fixing 'Not interested' rows...")
    auto_fix_not_interested(wl_rows)

    print("\n[10] Detecting non-standard notes...")
    detect_non_standard_notes(wl_rows)

    # Categorize
    print("\n[11] Categorizing issues...")
    categories = categorize_issues(wl_rows, no_rows)

    print("\nFinal category breakdown:")
    for cat in categories:
        print(f"  {cat.name}: {len(cat.row_nums)} rows")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == '__main__':
    test_validation()
