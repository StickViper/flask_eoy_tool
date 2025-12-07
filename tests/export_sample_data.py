#!/usr/bin/env python3
"""
Export sample data from Google Sheets for analysis.

This script exports real data samples that can be shared for code review/testing.
Run this and share the output when debugging data format issues.

Usage:
    python tests/export_sample_data.py > sample_data_output.txt
"""

import sys
import json
from pathlib import Path

# Add scripts/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from eoy_tool import load_data, status_to_color


def main():
    """Export sample data for analysis"""
    print("=" * 70)
    print("SAMPLE DATA EXPORT FOR CODE REVIEW")
    print("=" * 70)
    print()

    try:
        # Load real data
        print("Loading data from Google Sheets...")
        wl_rows, no_rows, invalid_rows, invalid_reasons, stats_sheet = load_data(year=2025)
        print(f"Loaded {len(wl_rows)} WL rows, {len(no_rows)} NO rows")
        print()

        # 1. Status values analysis
        print("=" * 70)
        print("1. UNIQUE STATUS VALUES")
        print("=" * 70)
        status_counts = {}
        for row in wl_rows:
            status = row.status or "(empty)"
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            color = status_to_color(status if status != "(empty)" else "")
            print(f"  '{status}' -> {color} ({count} rows)")

        # 2. Sample rows by color
        print()
        print("=" * 70)
        print("2. SAMPLE ROWS BY COLOR (3 per color)")
        print("=" * 70)

        by_color = {'yellow': [], 'fuschia': [], 'green': [], 'red': [], 'white': []}
        for row in wl_rows:
            c = row.bg_color.lower()
            if c.startswith('#ffff'):
                by_color['yellow'].append(row)
            elif c.startswith('#ff00'):
                by_color['fuschia'].append(row)
            elif c.startswith('#00ff'):
                by_color['green'].append(row)
            elif c == '#ff0000':
                by_color['red'].append(row)
            else:
                by_color['white'].append(row)

        for color_name, rows in by_color.items():
            print(f"\n  [{color_name.upper()} - {len(rows)} total]")
            for row in rows[:3]:
                print(f"    Row {row.row_num}:")
                print(f"      Practice: {repr(row.practice)}")
                print(f"      Phone: {repr(row.phone)}")
                print(f"      Address: {repr(row.address)}")
                print(f"      Status: {repr(row.status)}")
                print(f"      Notes: {repr(row.notes)}")
                print(f"      BG Color: {row.bg_color}")

        # 3. Special characters analysis
        print()
        print("=" * 70)
        print("3. ROWS WITH SPECIAL CHARACTERS")
        print("=" * 70)

        special_chars = set("'\"\\`<>&;")
        for row in wl_rows[:500]:  # Check first 500
            has_special = False
            for field in [row.practice, row.notes, row.address]:
                if field and any(c in field for c in special_chars):
                    has_special = True
                    break
            if has_special:
                print(f"\n  Row {row.row_num}:")
                print(f"    Practice: {repr(row.practice)}")
                print(f"    Address: {repr(row.address)}")
                print(f"    Notes: {repr(row.notes)}")

        # 4. Phone format analysis
        print()
        print("=" * 70)
        print("4. PHONE NUMBER FORMATS (first 20 unique)")
        print("=" * 70)
        phone_formats = set()
        for row in wl_rows:
            if row.phone and len(phone_formats) < 20:
                # Get format pattern
                pattern = ""
                for c in row.phone:
                    if c.isdigit():
                        pattern += "N"
                    else:
                        pattern += c
                phone_formats.add((pattern, row.phone))

        for pattern, example in sorted(phone_formats):
            print(f"  Pattern: {pattern}")
            print(f"  Example: {example}")
            print()

        # 5. Notes with semicolons
        print("=" * 70)
        print("5. SAMPLE NOTES WITH SEMICOLONS (10 examples)")
        print("=" * 70)
        count = 0
        for row in wl_rows:
            if row.notes and ';' in row.notes:
                print(f"\n  Row {row.row_num}: {repr(row.notes)}")
                chunks = [c.strip() for c in row.notes.split(';') if c.strip()]
                print(f"    Chunks: {chunks}")
                count += 1
                if count >= 10:
                    break

        # 6. QTY field formats
        print()
        print("=" * 70)
        print("6. QTY_2025 FIELD VALUES (unique)")
        print("=" * 70)
        qty_values = set()
        for row in wl_rows:
            qty_values.add(row.qty_2025)
        for val in sorted(qty_values, key=lambda x: (len(x or ''), x or '')):
            print(f"  {repr(val)}")

        # 7. Sample New Orders rows
        print()
        print("=" * 70)
        print("7. SAMPLE NEW ORDERS ROWS (5 examples)")
        print("=" * 70)
        for row in no_rows[:5]:
            print(f"\n  Row {row.row_num}:")
            print(f"    Practice: {repr(row.practice)}")
            print(f"    Address: {repr(row.address)}")
            print(f"    City: {repr(row.city)}, State: {repr(row.state)}")
            print(f"    QTY: {repr(row.qty_2025)}")

        # 8. Sample Invalid rows
        print()
        print("=" * 70)
        print("8. SAMPLE INVALID LIST ROWS (5 examples)")
        print("=" * 70)
        for row in invalid_rows[:5]:
            print(f"\n  Row {row.row_num}:")
            print(f"    Practice: {repr(row.practice)}")
            print(f"    Phone: {repr(row.phone)}")
            print(f"    Address: {repr(row.address)}")
            print(f"    Reason: {repr(row.reason)}")

        print()
        print("=" * 70)
        print("EXPORT COMPLETE")
        print("=" * 70)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
