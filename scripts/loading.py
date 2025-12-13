"""
Data loading from Google Sheets for EOY Cleanup Tool

Phase 1: Load data from Working List, New Orders, and Invalid/Inactive sheets.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from models import ProviderRow, NewOrderRow, InvalidRow
from helpers import status_to_color


def load_data(year: int = 2025):
    """Load all data from Google Sheets"""
    print(f"[Phase 1] Loading data from Google Sheets...")

    # Authenticate
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(creds)

    sh = gc.open('OBGYN List 2025 - Use This List!')

    # Get worksheets
    wl_sheet = sh.worksheet(f'Working List {year}')
    no_sheet = sh.worksheet(f'New Orders {year}')
    invalid_sheet = sh.worksheet('Invalid/Inactive List')

    # Load data
    wl_data = wl_sheet.get_all_values()
    no_data = no_sheet.get_all_values()
    invalid_data = invalid_sheet.get_all_values()

    print(f"  Loaded {len(wl_data)-1} Working List rows")
    print(f"  Loaded {len(no_data)-1} New Orders rows")

    # IMPORTANT: We derive colors from Status column instead of reading individually
    # Reading colors individually = 737 API calls > 60/minute quota limit
    # Status column text maps to colors via onEdit() Apps Script automation
    print(f"  Deriving colors from Status column (avoiding API rate limits)...")

    # Parse Working List
    wl_rows = []
    for i, row in enumerate(wl_data[1:], 2):
        if len(row) < 11:
            continue

        # Get status text and derive color from it
        status = row[9] if len(row) > 9 else ""
        bg_color = status_to_color(status)

        wl_rows.append(ProviderRow(
            row_num=i,
            practice=row[0] if len(row) > 0 else "",
            phone=row[1] if len(row) > 1 else "",
            address=row[2] if len(row) > 2 else "",
            city=row[3] if len(row) > 3 else "",
            state=row[4] if len(row) > 4 else "",
            zip=row[5] if len(row) > 5 else "",
            qty_2023=row[6] if len(row) > 6 else "",
            qty_2024=row[7] if len(row) > 7 else "",
            qty_2025=row[8] if len(row) > 8 else "",
            status=status,
            notes=row[10] if len(row) > 10 else "",
            bg_color=bg_color
        ))

    # Parse New Orders
    no_rows = []
    for i, row in enumerate(no_data[1:], 2):
        if len(row) < 8 or not row[2]:  # Skip if no practice name or missing cols
            continue
        no_rows.append(NewOrderRow(
            row_num=i,
            practice=row[2] if len(row) > 2 else "",
            address=row[3] if len(row) > 3 else "",
            city=row[4] if len(row) > 4 else "",
            state=row[5] if len(row) > 5 else "",
            zip=row[6] if len(row) > 6 else "",
            qty_2025=row[7] if len(row) > 7 else ""
        ))

    # Parse Invalid/Inactive List rows and extract reasons
    # Assumed structure: Practice, Phone, Address, City, State, [Zip], Reason
    invalid_rows = []
    invalid_reasons = set()
    for i, row in enumerate(invalid_data[1:], start=2):  # Start at row 2 (after header)
        if len(row) >= 5:  # Need at least practice through state
            practice = row[0] if len(row) > 0 else ""
            phone = row[1] if len(row) > 1 else ""
            address = row[2] if len(row) > 2 else ""
            city = row[3] if len(row) > 3 else ""
            state_val = row[4] if len(row) > 4 else ""
            # Reason might be in column 5, 6, or beyond
            reason = ""
            for j in range(5, min(len(row), 10)):
                if row[j] and len(row[j]) > 5:  # Looks like a reason, not zip
                    reason = row[j]
                    break

            if practice or address:  # Only add if has some identifying info
                invalid_rows.append(InvalidRow(
                    row_num=i,
                    practice=practice,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state_val,
                    reason=reason
                ))
                if reason:
                    invalid_reasons.add(reason)

    print(f"  Loaded {len(invalid_rows)} Invalid/Inactive rows")

    # Load STATS worksheet for validation
    stats_sheet = sh.worksheet('STATS')

    # Diagnostic: Log any unusual status values that might not map correctly
    print(f"\n[Diagnostic] Checking for unusual status values...")
    unusual_statuses = {}
    expected_statuses = [
        'successful order', 'voicemail', 'no answer', 'not interested',
        'invalid', 'potentially invalid', 'requested email', 'email'
    ]

    for row in wl_rows:
        if row.status:
            status_lower = row.status.lower().strip()
            # Check if status contains any expected keyword
            is_recognized = any(exp in status_lower for exp in expected_statuses)
            if not is_recognized:
                if status_lower not in unusual_statuses:
                    unusual_statuses[status_lower] = []
                unusual_statuses[status_lower].append(row.row_num)

    if unusual_statuses:
        print(f"  [!] Found {len(unusual_statuses)} unusual status values:")
        for status, rows in list(unusual_statuses.items())[:10]:  # Show first 10
            print(f"      '{status}' (rows: {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
        if len(unusual_statuses) > 10:
            print(f"      ... and {len(unusual_statuses) - 10} more")
        print(f"  These may not map to expected colors correctly.")
    else:
        print(f"  [OK] All status values are recognized")

    print(f"\n[Phase 1] Complete!")
    return wl_rows, no_rows, invalid_rows, invalid_reasons, stats_sheet


def validate_stats_color_counts(wl_rows, stats_sheet, year=2025, assume_yes=False):
    """
    Validate Status-derived colors against STATS worksheet color counts.

    STATS worksheet uses formulas to COUNT actual cell background colors.
    We derive colors from Status column to avoid API rate limits.
    This function checks if they match.

    If mismatch > 10%, warns user to manually fix Status column in sheet.
    """
    print(f"\n[Validation] Checking Status-derived colors against STATS...")

    # Count Status-derived colors in our data
    status_counts = {
        'yellow': 0,
        'fuschia': 0,
        'red': 0,
        'green': 0,
        'white': 0
    }

    for row in wl_rows:
        color = row.bg_color.lower()
        if color in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']:
            status_counts['yellow'] += 1
        elif color in ['#ff00ff', '#ff00fe', '#fe00ff']:
            status_counts['fuschia'] += 1
        elif color in ['#ff0000', '#ff0001', '#fe0000']:
            status_counts['red'] += 1
        elif color in ['#00ff00', '#00ff01', '#00fe00']:
            status_counts['green'] += 1
        else:
            status_counts['white'] += 1

    # Read STATS color counts (formulas calculate actual colors)
    # STATS worksheet structure:
    # Row 2, Col C: Yellow (ORDER SECURED)
    # Row 3, Col C: White with "not interested"
    # Row 4, Col C: Fuschia (CALLBACK)
    # Row 5, Col C: White uncalled (no "not interested")
    # Row 6, Col C: Red (VERIFY ACTIVITY/VALIDITY)
    # Row 7, Col C: Green (UNRESOLVED EMAILS)
    try:
        stats_data = stats_sheet.get('A1:C10')  # Get first 10 rows of STATS

        stats_counts = {}

        # Parse based on actual STATS structure (hardcoded row positions)
        # This is reliable since STATS layout is fixed
        try:
            # Row 2 (index 1): Yellow
            if len(stats_data) > 1 and len(stats_data[1]) > 2:
                stats_counts['yellow'] = int(stats_data[1][2])

            # Row 4 (index 3): Fuschia
            if len(stats_data) > 3 and len(stats_data[3]) > 2:
                stats_counts['fuschia'] = int(stats_data[3][2])

            # Row 6 (index 5): Red
            if len(stats_data) > 5 and len(stats_data[5]) > 2:
                stats_counts['red'] = int(stats_data[5][2])

            # Row 7 (index 6): Green
            if len(stats_data) > 6 and len(stats_data[6]) > 2:
                stats_counts['green'] = int(stats_data[6][2])

            # White = Row 3 (not interested) + Row 5 (uncalled)
            white_not_interested = 0
            white_uncalled = 0
            if len(stats_data) > 2 and len(stats_data[2]) > 2:
                white_not_interested = int(stats_data[2][2])
            if len(stats_data) > 4 and len(stats_data[4]) > 2:
                white_uncalled = int(stats_data[4][2])
            stats_counts['white'] = white_not_interested + white_uncalled

        except (ValueError, IndexError) as e:
            print(f"  [!] Could not parse STATS counts: {e}")
            return True  # Continue anyway

        # Compare counts
        print(f"\n  Status-Derived Counts vs STATS Color Counts:")
        print(f"  {'Color':<15} {'Status':<10} {'STATS':<10} {'Diff':<10} {'Status'}")
        print(f"  {'-'*55}")

        has_mismatch = False
        for color in ['yellow', 'fuschia', 'red', 'green', 'white']:
            status_val = status_counts.get(color, 0)
            stats_val = stats_counts.get(color, 0)
            diff = status_val - stats_val

            # Check if significant mismatch (>10% or >10 rows)
            threshold = max(10, stats_val * 0.10)
            status_mark = "[!] MISMATCH" if abs(diff) > threshold else "[OK]"

            if abs(diff) > threshold:
                has_mismatch = True

            print(f"  {color.capitalize():<15} {status_val:<10} {stats_val:<10} {diff:+10} {status_mark}")

        print()

        if has_mismatch:
            print("  [!] WARNING: Status column doesn't match actual cell colors!")
            print("  -> This means some rows have Status text that doesn't match their background color")
            print("  -> STATS uses actual cell colors (formulas count background colors)")
            print("  -> Status column is used by this tool to avoid API rate limits")
            print()
            print("  RECOMMENDED ACTION:")
            print("  1. Open the Working List in Google Sheets")
            print("  2. Review rows where Status doesn't match color")
            print("  3. Either:")
            print("     a) Update Status to match color (Apps Script will auto-update color)")
            print("     b) Manually update color to match Status (in cell formatting)")
            print("  4. Re-run this tool after fixing")
            print()
            if assume_yes:
                print("  [Automation] --assume-yes active: Continuing despite mismatch.")
                return True

            response = input("  Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("\n[Validation] User chose to exit. Please fix Status/color mismatch first.")
                return False

        else:
            print("  [OK] Status-derived colors match STATS color counts!")
            print("  -> Safe to proceed with Status column as color source")

        return True

    except Exception as e:
        print(f"  [!] Could not validate against STATS: {e}")
        print(f"  -> Proceeding with Status-derived colors (validation skipped)")
        return True
