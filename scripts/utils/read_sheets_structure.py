"""
Quick script to read STATS sheet and Invalid/Inactive List structure
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def read_structure():
    # Authenticate
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json',
        scope
    )
    gc = gspread.authorize(creds)

    # Open sheet
    sh = gc.open('OBGYN List 2025 - Use This List!')

    print("=" * 80)
    print("ALL WORKSHEETS")
    print("=" * 80)
    for ws in sh.worksheets():
        print(f"  - {ws.title} ({ws.row_count} rows, {ws.col_count} cols)")

    # Read STATS sheet structure
    print("\n" + "=" * 80)
    print("STATS SHEET STRUCTURE")
    print("=" * 80)
    try:
        stats = sh.worksheet('STATS')
        headers = stats.row_values(1)
        print(f"\nHeaders ({len(headers)} columns):")
        for i, h in enumerate(headers, 1):
            if h:  # Only show non-empty headers
                print(f"  {chr(64+i):>2} (col {i:2d}): {h}")

        # Show first few data rows to understand structure
        print(f"\nFirst 5 data rows:")
        data = stats.get('A2:Z6')  # First 5 rows, up to column Z
        for i, row in enumerate(data, 2):
            print(f"  Row {i}: {row[:10]}...")  # Show first 10 values

    except Exception as e:
        print(f"Error reading STATS: {e}")

    # Read Invalid/Inactive List structure
    print("\n" + "=" * 80)
    print("INVALID/INACTIVE LIST STRUCTURE")
    print("=" * 80)
    try:
        invalid = sh.worksheet('Invalid/Inactive List')
        headers = invalid.row_values(1)
        print(f"\nHeaders ({len(headers)} columns):")
        for i, h in enumerate(headers, 1):
            if h:  # Only show non-empty headers
                print(f"  {chr(64+i):>2} (col {i:2d}): {h}")

        # Show sample data to see reason formats
        print(f"\nSample data (first 10 rows):")
        data = invalid.get('A2:K11')  # First 10 data rows
        for i, row in enumerate(data, 2):
            if len(row) > 6:  # Has reason column
                print(f"  Row {i}: {row[0][:30]:30s} | Reason: {row[6] if len(row) > 6 else 'N/A'}")
            else:
                print(f"  Row {i}: {row[0][:30]:30s} | (no reason)")

        # Get all unique reasons to understand dropdown/common reasons
        print(f"\nAnalyzing all reasons...")
        all_data = invalid.get_all_values()
        reasons = set()
        for row in all_data[1:]:  # Skip header
            if len(row) > 6 and row[6]:  # Column G (index 6) has reason
                reasons.add(row[6])

        print(f"\nUnique reasons found ({len(reasons)}):")
        for r in sorted(reasons):
            print(f"  - {r}")

    except Exception as e:
        print(f"Error reading Invalid/Inactive List: {e}")

    # Read Working List structure for reference
    print("\n" + "=" * 80)
    print("WORKING LIST 2025 STRUCTURE")
    print("=" * 80)
    try:
        wl = sh.worksheet('Working List 2025')
        headers = wl.row_values(1)
        print(f"\nHeaders ({len(headers)} columns):")
        for i, h in enumerate(headers, 1):
            if h:
                print(f"  {chr(64+i):>2} (col {i:2d}): {h}")

        # Count colors
        print(f"\nCounting row colors...")
        all_data = wl.get_all_values()
        print(f"Total data rows: {len(all_data) - 1}")

    except Exception as e:
        print(f"Error reading Working List: {e}")

if __name__ == '__main__':
    read_structure()
