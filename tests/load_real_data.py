#!/usr/bin/env python3
"""
Load real data from Google Sheets and cache it for testing

This script:
1. Loads actual Working List and New Orders data from Google Sheets
2. Samples a representative subset for testing
3. Saves to tests/fixtures/real_data_cache.json for fast test runs

Run once to populate cache, then tests use cached data (no API calls needed).
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from eoy_tool import load_data, ProviderRow, NewOrderRow


def sample_data_for_tests(wl_rows, no_rows, sample_size=100):
    """
    Sample representative data for comprehensive testing

    Args:
        wl_rows: All Working List rows
        no_rows: All New Orders rows
        sample_size: Number of WL rows to sample

    Returns:
        Tuple of (sampled_wl_rows, sampled_no_rows)
    """
    print(f"Sampling {sample_size} WL rows from {len(wl_rows)} total...")

    # Stratified sampling to ensure we get:
    # - Mix of all colors (yellow, fuschia, green, red, white)
    # - Mix of all statuses
    # - Some duplicates
    # - Some networks
    # - Various match quality levels

    samples = {
        'yellow': [],
        'fuschia': [],
        'green': [],
        'red': [],
        'white': [],
        'other': []
    }

    # Categorize by color
    for row in wl_rows:
        color = row.bg_color.lower()
        if color in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']:
            samples['yellow'].append(row)
        elif color in ['#ff00ff', '#ff00fe', '#fe00ff']:
            samples['fuschia'].append(row)
        elif color in ['#00ff00', '#00ff01', '#00fe00']:
            samples['green'].append(row)
        elif color in ['#ff0000', '#ff0001', '#fe0000']:
            samples['red'].append(row)
        elif color in ['#ffffff', '#fffffe', '#fefefe']:
            samples['white'].append(row)
        else:
            samples['other'].append(row)

    print(f"  Yellow (Successful Order): {len(samples['yellow'])}")
    print(f"  Fuschia (Voicemail): {len(samples['fuschia'])}")
    print(f"  Green (Requested Email): {len(samples['green'])}")
    print(f"  Red (Potentially Invalid): {len(samples['red'])}")
    print(f"  White (Not interested/empty): {len(samples['white'])}")
    print(f"  Other colors: {len(samples['other'])}")

    # Sample proportionally
    total = len(wl_rows)
    sampled_wl = []

    for color_name, rows in samples.items():
        if not rows:
            continue
        proportion = len(rows) / total
        n_samples = max(1, int(sample_size * proportion))
        n_samples = min(n_samples, len(rows))  # Don't sample more than available

        # Take every Nth row to get spread
        step = max(1, len(rows) // n_samples)
        sampled = rows[::step][:n_samples]
        sampled_wl.extend(sampled)
        print(f"  Sampled {len(sampled)} {color_name} rows")

    # For NO rows, sample proportionally (about 1/3 of WL sample size)
    no_sample_size = max(20, len(sampled_wl) // 3)
    no_step = max(1, len(no_rows) // no_sample_size)
    sampled_no = no_rows[::no_step][:no_sample_size]

    print(f"Sampled {len(sampled_no)} NO rows from {len(no_rows)} total")

    return sampled_wl, sampled_no


def save_cache(wl_rows, no_rows, cache_path):
    """Save sampled data to JSON cache"""
    cache_data = {
        'generated_at': datetime.now().isoformat(),
        'wl_rows_count': len(wl_rows),
        'no_rows_count': len(no_rows),
        'wl_rows': [row.to_dict() for row in wl_rows],
        'no_rows': [row.to_dict() for row in no_rows]
    }

    cache_path.parent.mkdir(parents=True, exist_ok=True)

    with open(cache_path, 'w') as f:
        json.dump(cache_data, f, indent=2)

    print(f"\n✅ Cache saved to {cache_path}")
    print(f"   {len(wl_rows)} WL rows, {len(no_rows)} NO rows")
    print(f"   Tests can now run without API calls")


def main():
    """Load real data and create test cache"""
    print("=" * 60)
    print("Loading Real Data from Google Sheets")
    print("=" * 60)
    print()

    try:
        # Load real data (will hit Google Sheets API)
        print("Loading data from Google Sheets (this may take a moment)...")
        wl_rows, no_rows, invalid_rows, invalid_reasons, stats_sheet = load_data(year=2025)

        print(f"\n✅ Loaded {len(wl_rows)} Working List rows")
        print(f"✅ Loaded {len(no_rows)} New Orders rows")
        print()

        # Sample for testing
        sampled_wl, sampled_no = sample_data_for_tests(wl_rows, no_rows, sample_size=100)

        # Save cache
        cache_path = Path(__file__).parent / "fixtures" / "real_data_cache.json"
        save_cache(sampled_wl, sampled_no, cache_path)

        print()
        print("=" * 60)
        print("✅ Real data cache created successfully!")
        print("=" * 60)
        print()
        print("Now run tests: cd scripts && python -m pytest ../tests/ -v")

    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        print()
        print("Make sure:")
        print("  1. credentials.json exists in project root")
        print("  2. Google Sheets API is enabled")
        print("  3. You have access to the OBGYN List 2025 spreadsheet")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
