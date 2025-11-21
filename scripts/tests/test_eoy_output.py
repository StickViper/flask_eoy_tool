"""
Simple EOY Tool Output Testing Script

Run this after loading data to verify:
- Category counts make sense
- Match accuracy looks reasonable
- No obvious data issues
"""

def test_category_counts(categories):
    """Check if category counts are reasonable"""
    print("\n" + "="*80)
    print("CATEGORY COUNT CHECK")
    print("="*80)

    for cat in categories:
        print(f"  {cat.name:30s} {cat.row_count:4d} rows")

    total = sum(cat.row_count for cat in categories)
    print(f"\n  Total issues across all categories: {total}")
    print(f"  (Note: rows can appear in multiple categories)")

def test_match_distribution(wl_rows):
    """Check distribution of match confidence scores"""
    print("\n" + "="*80)
    print("MATCH CONFIDENCE DISTRIBUTION")
    print("="*80)

    yellow_rows = [r for r in wl_rows if r.bg_color.lower() in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']]

    if not yellow_rows:
        print("  No yellow rows found")
        return

    high = sum(1 for r in yellow_rows if r.match_confidence >= 0.95)
    medium = sum(1 for r in yellow_rows if 0.80 <= r.match_confidence < 0.95)
    low = sum(1 for r in yellow_rows if r.match_confidence < 0.80)

    print(f"  Yellow rows (should have order): {len(yellow_rows)}")
    print(f"    ≥95% confidence (exact match):  {high:3d} ({high/len(yellow_rows)*100:5.1f}%)")
    print(f"    80-94% confidence (good match):  {medium:3d} ({medium/len(yellow_rows)*100:5.1f}%)")
    print(f"    <80% confidence (not found):     {low:3d} ({low/len(yellow_rows)*100:5.1f}%)")

    if high < len(yellow_rows) * 0.7:
        print("\n  [!] Warning: Low exact match rate. Expected >70% to be ≥95%.")
        print("      This might indicate data quality issues or matching logic problems.")

def test_duplicate_groups(wl_rows):
    """Check duplicate group distribution"""
    print("\n" + "="*80)
    print("DUPLICATE GROUP CHECK")
    print("="*80)

    dup_rows = [r for r in wl_rows if r.duplicate_group_id]

    if not dup_rows:
        print("  No duplicates found")
        return

    from collections import defaultdict
    groups = defaultdict(list)
    for row in dup_rows:
        groups[row.duplicate_group_id].append(row)

    print(f"  Total duplicate groups: {len(groups)}")
    print(f"  Total rows in duplicates: {len(dup_rows)}")

    # Show first 5 groups
    print("\n  Sample groups:")
    for gid in sorted(groups.keys())[:5]:
        rows = groups[gid]
        print(f"    Group {gid}: {len(rows)} rows (practice: '{rows[0].practice}')")

def test_color_distribution(wl_rows):
    """Check distribution of row colors"""
    print("\n" + "="*80)
    print("COLOR DISTRIBUTION")
    print("="*80)

    from collections import Counter
    colors = Counter(r.bg_color.lower() for r in wl_rows)

    color_names = {
        '#ffff00': 'Yellow (orders)',
        '#ff00ff': 'Fuschia (voicemail)',
        '#ff0000': 'Red (invalid)',
        '#00ff00': 'Green (email)',
        '#ffffff': 'White (not interested / uncalled)'
    }

    for color in sorted(colors.keys()):
        # Normalize color variations
        base_color = color.replace('#ffff01', '#ffff00').replace('#fffef0', '#ffff00')
        base_color = base_color.replace('#ff00fe', '#ff00ff').replace('#fe00ff', '#ff00ff')
        base_color = base_color.replace('#ff0001', '#ff0000').replace('#fe0000', '#ff0000')
        base_color = base_color.replace('#00ff01', '#00ff00').replace('#00fe00', '#00ff00')

        name = color_names.get(base_color, f'Unknown ({color})')
        count = colors[color]
        print(f"  {name:40s} {count:4d} ({count/len(wl_rows)*100:5.1f}%)")

def run_all_tests(state):
    """Run all tests on loaded state"""
    print("\n" + "="*80)
    print("EOY TOOL OUTPUT VALIDATION")
    print("="*80)
    print(f"Year: {state.year}")
    print(f"Working List rows: {len(state.wl_rows)}")
    print(f"New Orders rows: {len(state.no_rows)}")
    print(f"Categories: {len(state.categories)}")

    test_category_counts(state.categories)
    test_match_distribution(state.wl_rows)
    test_duplicate_groups(state.wl_rows)
    test_color_distribution(state.wl_rows)

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print("\nReview the output above for any warnings or unexpected values.")
    print("If everything looks reasonable, the tool is working correctly.")

if __name__ == '__main__':
    print("This script should be imported and run after data is loaded.")
    print("\nUsage:")
    print("  from test_eoy_output import run_all_tests")
    print("  run_all_tests(state)  # After loading data in Flask app")
