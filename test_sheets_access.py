#!/usr/bin/env python3
"""Quick test to check Google Sheets access"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(creds)

# Try to open the spreadsheet
spreadsheet_id = '1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0'

print("Testing Google Sheets access...")
print(f"Spreadsheet ID: {spreadsheet_id}")
print()

try:
    sh = gc.open_by_key(spreadsheet_id)
    print(f"✓ Successfully opened spreadsheet: {sh.title}")
    print()

    # List worksheets
    worksheets = sh.worksheets()
    print(f"✓ Found {len(worksheets)} worksheets:")
    for ws in worksheets:
        print(f"  - {ws.title} ({ws.row_count} rows x {ws.col_count} cols)")
    print()

    # Try to read from Working List 2025
    try:
        wl_sheet = sh.worksheet('Working List 2025')
        data = wl_sheet.get_all_values()
        print(f"✓ Successfully read Working List 2025: {len(data)} rows")
        print(f"  Headers: {data[0][:5]}..." if data else "  (empty)")
        print()
    except Exception as e:
        print(f"✗ Could not read Working List 2025: {e}")
        print()

    # Try to read from New Orders 2025
    try:
        no_sheet = sh.worksheet('New Orders 2025')
        data = no_sheet.get_all_values()
        print(f"✓ Successfully read New Orders 2025: {len(data)} rows")
        print()
    except Exception as e:
        print(f"✗ Could not read New Orders 2025: {e}")
        print()

    # Try to read from Invalid/Inactive List
    try:
        invalid_sheet = sh.worksheet('Invalid/Inactive List')
        data = invalid_sheet.get_all_values()
        print(f"✓ Successfully read Invalid/Inactive List: {len(data)} rows")
        print()
    except Exception as e:
        print(f"✗ Could not read Invalid/Inactive List: {e}")
        print()

    print("=" * 60)
    print("SUCCESS: Google Sheets access is working!")
    print("=" * 60)

except gspread.exceptions.APIError as e:
    print(f"✗ API Error: {e}")
    print()
    print("This usually means:")
    print("  - Service account doesn't have permission to access the sheet")
    print("  - The spreadsheet ID is incorrect")
    print("  - The sheet hasn't been shared with the service account email")

except gspread.exceptions.SpreadsheetNotFound as e:
    print(f"✗ Spreadsheet not found: {e}")
    print()
    print("Make sure the spreadsheet ID is correct and the sheet")
    print("is shared with the service account email from credentials.json")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    print(f"  Type: {type(e).__name__}")
    print()
    import traceback
    traceback.print_exc()
