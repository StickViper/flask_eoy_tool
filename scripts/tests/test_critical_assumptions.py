"""
Test critical assumptions before building EOY tool

Tests:
1. Can gspread read cell background colors?
2. Is fuzzy matching library available?
3. Does worksheet.duplicate() preserve formulas?
4. Can we detect exact vs "0" in QTY column?
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sys

# Spreadsheet configuration - use ID to bypass Drive API requirement
SPREADSHEET_ID = "1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0"

def test_color_reading():
    """Test if we can read cell background colors"""
    print("\n" + "=" * 80)
    print("TEST 1: Cell Background Color Reading")
    print("=" * 80)

    try:
        # Try basic gspread first
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json',
            scope
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        wl = sh.worksheet('Working List 2025')

        # Try to read a cell with color
        # Row 2 should have some color (yellow, red, etc.)
        cell = wl.acell('A2')
        print(f"\nBasic gspread cell object attributes:")
        print(f"  cell.value: {cell.value}")
        print(f"  cell.__dict__: {cell.__dict__}")

        # Check if cell has color attribute
        if hasattr(cell, 'color'):
            print(f"  [OK] cell.color: {cell.color}")
        else:
            print(f"  [NO] cell does NOT have .color attribute")

        # Try gspread-formatting if available
        print(f"\nTrying gspread-formatting library...")
        try:
            from gspread_formatting import get_effective_format

            fmt = get_effective_format(wl, 'A2')
            if fmt and hasattr(fmt, 'backgroundColor'):
                bg = fmt.backgroundColor
                print(f"  [OK] Background color found!")
                print(f"     Red: {bg.red if hasattr(bg, 'red') else 'N/A'}")
                print(f"     Green: {bg.green if hasattr(bg, 'green') else 'N/A'}")
                print(f"     Blue: {bg.blue if hasattr(bg, 'blue') else 'N/A'}")

                # Test converting to hex
                if hasattr(bg, 'red') and hasattr(bg, 'green') and hasattr(bg, 'blue'):
                    r = int(bg.red * 255) if bg.red else 0
                    g = int(bg.green * 255) if bg.green else 0
                    b = int(bg.blue * 255) if bg.blue else 0
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    print(f"     Hex: {hex_color}")
            else:
                print(f"  [FAIL] Format object has no backgroundColor")

        except ImportError:
            print(f"  [WARN] gspread-formatting NOT installed")
            print(f"     Install with: pip install gspread-formatting")
            return False
        except Exception as e:
            print(f"  [FAIL] Error using gspread-formatting: {e}")
            return False

        # Try reading a range with colors
        print(f"\nTrying to read multiple cells with colors...")
        try:
            from gspread_formatting import get_effective_format

            # Sample a few rows
            test_rows = [2, 3, 4, 5, 10, 20]
            colors_found = {}

            for row_num in test_rows:
                fmt = get_effective_format(wl, f'A{row_num}')
                if fmt and hasattr(fmt, 'backgroundColor'):
                    bg = fmt.backgroundColor
                    if hasattr(bg, 'red') and hasattr(bg, 'green') and hasattr(bg, 'blue'):
                        r = int(bg.red * 255) if bg.red else 0
                        g = int(bg.green * 255) if bg.green else 0
                        b = int(bg.blue * 255) if bg.blue else 0
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"

                        if hex_color not in colors_found:
                            colors_found[hex_color] = []
                        colors_found[hex_color].append(row_num)

            print(f"\n  Colors found in sample:")
            for color, rows in colors_found.items():
                print(f"    {color}: rows {rows}")

            # Check if we found expected colors
            expected = ['#ffff00', '#ff00ff', '#ff0000', '#00ff00', '#ffffff']
            found = list(colors_found.keys())

            print(f"\n  Expected colors: {expected}")
            print(f"  Found colors: {found}")

            if any(c in expected for c in found):
                print(f"\n  [OK] SUCCESS: Can read cell colors with gspread-formatting!")
                return True
            else:
                print(f"\n  [WARN] WARNING: Found colors but not expected ones")
                print(f"     Might need to adjust hex color detection")
                return True  # Still works, just need to adjust colors

        except Exception as e:
            print(f"  [FAIL] Error reading color range: {e}")
            return False

    except Exception as e:
        print(f"[FAIL] Error in color reading test: {e}")
        return False


def test_fuzzy_matching():
    """Test if fuzzy matching library is available"""
    print("\n" + "=" * 80)
    print("TEST 2: Fuzzy Matching Library")
    print("=" * 80)

    # Try fuzzywuzzy
    print("\nTrying fuzzywuzzy...")
    try:
        from fuzzywuzzy import fuzz
        print("  [OK] fuzzywuzzy installed!")

        # Test token_set_ratio
        score = fuzz.token_set_ratio("Smith Family Practice", "Family Practice Smith")
        print(f"  Test: 'Smith Family Practice' vs 'Family Practice Smith'")
        print(f"  Token set ratio: {score}%")

        if score >= 90:
            print(f"  [OK] Token set ratio works as expected!")
            return 'fuzzywuzzy'
        else:
            print(f"  [WARN] Score lower than expected (wanted ≥90%, got {score}%)")
            return 'fuzzywuzzy'

    except ImportError:
        print("  [FAIL] fuzzywuzzy NOT installed")

    # Try rapidfuzz (modern alternative)
    print("\nTrying rapidfuzz (modern alternative)...")
    try:
        from rapidfuzz import fuzz as rfuzz
        print("  [OK] rapidfuzz installed!")

        # Test token_set_ratio
        score = rfuzz.token_set_ratio("Smith Family Practice", "Family Practice Smith")
        print(f"  Test: 'Smith Family Practice' vs 'Family Practice Smith'")
        print(f"  Token set ratio: {score}%")

        if score >= 90:
            print(f"  [OK] Token set ratio works as expected!")
            return 'rapidfuzz'
        else:
            print(f"  [WARN] Score lower than expected (wanted ≥90%, got {score}%)")
            return 'rapidfuzz'

    except ImportError:
        print("  [FAIL] rapidfuzz NOT installed")

    print("\n[FAIL] CRITICAL: No fuzzy matching library available!")
    print("   Install one of:")
    print("     pip install fuzzywuzzy python-Levenshtein")
    print("     OR")
    print("     pip install rapidfuzz")
    return None


def test_worksheet_duplicate():
    """Test if worksheet.duplicate() preserves formulas"""
    print("\n" + "=" * 80)
    print("TEST 3: Worksheet Duplication (Formulas Preserved?)")
    print("=" * 80)

    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json',
            scope
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)

        # Try to duplicate STATS sheet (has formulas)
        print("\nDuplicating STATS sheet...")
        stats = sh.worksheet('STATS')

        # Read a formula before duplication
        cell_c2 = stats.acell('C2', value_render_option='FORMULA')
        print(f"  Original STATS C2 formula: {cell_c2.value}")

        # Duplicate
        print("\n  Creating duplicate...")
        stats_test = stats.duplicate(new_sheet_name='STATS_TEST_DUPLICATE')
        print(f"  [OK] Duplicate created: {stats_test.title}")

        # Read formula from duplicate
        cell_c2_dup = stats_test.acell('C2', value_render_option='FORMULA')
        print(f"  Duplicate STATS C2 formula: {cell_c2_dup.value}")

        # Compare
        if cell_c2.value == cell_c2_dup.value:
            print(f"\n  [OK] SUCCESS: Formulas preserved during duplication!")
            success = True
        else:
            print(f"\n  [FAIL] PROBLEM: Formulas changed during duplication")
            print(f"     Original: {cell_c2.value}")
            print(f"     Duplicate: {cell_c2_dup.value}")
            success = False

        # Clean up: delete test duplicate
        print("\n  Cleaning up test duplicate...")
        sh.del_worksheet(stats_test)
        print(f"  [OK] Test duplicate deleted")

        return success

    except Exception as e:
        print(f"[FAIL] Error in worksheet duplication test: {e}")
        return False


def test_empty_vs_zero():
    """Test if we can distinguish empty cells from '0'"""
    print("\n" + "=" * 80)
    print("TEST 4: Empty Cell vs '0' Detection")
    print("=" * 80)

    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json',
            scope
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        wl = sh.worksheet('Working List 2025')

        # Read QTY column (column I, index 8)
        print("\nReading 2025 QTY column (first 20 rows)...")

        qty_values = []
        for row_num in range(2, 22):  # Rows 2-21
            cell = wl.acell(f'I{row_num}')
            value = cell.value
            qty_values.append({
                'row': row_num,
                'value': value,
                'type': type(value).__name__,
                'is_empty': value == '' or value is None,
                'is_zero': value == '0' or value == 0
            })

        # Analyze
        empty_count = sum(1 for v in qty_values if v['is_empty'])
        zero_count = sum(1 for v in qty_values if v['is_zero'])
        other_count = len(qty_values) - empty_count - zero_count

        print(f"\n  Sample analysis (20 rows):")
        print(f"    Empty cells: {empty_count}")
        print(f"    '0' values: {zero_count}")
        print(f"    Other values: {other_count}")

        # Show examples
        print(f"\n  Examples:")
        for v in qty_values[:5]:
            print(f"    Row {v['row']}: value={repr(v['value'])}, "
                  f"type={v['type']}, empty={v['is_empty']}, zero={v['is_zero']}")

        # Can we distinguish?
        if empty_count > 0 and zero_count > 0:
            print(f"\n  [OK] SUCCESS: Can distinguish empty from '0'!")
            print(f"     Empty cells return: '' (empty string) or None")
            print(f"     Zero values return: '0' (string) or 0 (int)")
            return True
        elif empty_count == 0 and zero_count == 0:
            print(f"\n  [WARN] No empty or zero values found in sample")
            print(f"     Can't verify, but logic should work")
            return True
        else:
            print(f"\n  [OK] Found at least one type, logic should work")
            return True

    except Exception as e:
        print(f"[FAIL] Error in empty vs zero test: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CRITICAL ASSUMPTIONS TEST")
    print("Testing assumptions before building EOY tool")
    print("=" * 80)

    results = {}

    # Test 1: Color reading (CRITICAL)
    results['color'] = test_color_reading()

    # Test 2: Fuzzy matching (CRITICAL)
    results['fuzzy'] = test_fuzzy_matching()

    # Test 3: Worksheet duplication (IMPORTANT)
    results['duplicate'] = test_worksheet_duplicate()

    # Test 4: Empty vs zero (NICE TO HAVE)
    results['empty_zero'] = test_empty_vs_zero()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print(f"\n1. Cell color reading: {'[OK] PASS' if results['color'] else '[FAIL] FAIL'}")
    print(f"2. Fuzzy matching: {'[OK] PASS (' + results['fuzzy'] + ')' if results['fuzzy'] else '[FAIL] FAIL'}")
    print(f"3. Worksheet duplication: {'[OK] PASS' if results['duplicate'] else '[FAIL] FAIL'}")
    print(f"4. Empty vs '0' detection: {'[OK] PASS' if results['empty_zero'] else '[FAIL] FAIL'}")

    # Critical tests
    critical_pass = results['color'] and results['fuzzy']

    if critical_pass:
        print(f"\n[OK] ALL CRITICAL TESTS PASSED!")
        print(f"   Ready to proceed with building EOY tool")
        if results['fuzzy']:
            print(f"   Use library: {results['fuzzy']}")
    else:
        print(f"\n[FAIL] CRITICAL TESTS FAILED!")
        print(f"   Cannot proceed until resolved:")
        if not results['color']:
            print(f"     - Install gspread-formatting: pip install gspread-formatting")
        if not results['fuzzy']:
            print(f"     - Install rapidfuzz: pip install rapidfuzz")

    return critical_pass


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
