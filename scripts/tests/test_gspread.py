"""
Test gspread connection to OBGYN List 2025 - Use This List!
Run this AFTER completing gspread setup (see setup instructions below)
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Spreadsheet configuration
# Get the ID from the URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
SPREADSHEET_ID = "1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0"
SPREADSHEET_NAME = 'OBGYN List 2025 - Use This List!'

def test_connection():
    """Test basic gspread connection and data access"""

    print("=" * 60)
    print("GSPREAD CONNECTION TEST")
    print("=" * 60)

    # Step 1: Authenticate
    print("\n[1/5] Authenticating with Google Sheets API...")
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
        print("✅ Authentication successful!")
    except FileNotFoundError:
        print("❌ ERROR: credentials.json not found!")
        print("   Place credentials.json in the project root directory")
        return False
    except Exception as e:
        print(f"❌ ERROR: Authentication failed: {e}")
        return False

    # Step 2: Open spreadsheet
    # Get service account email for error messages
    try:
        import json
        with open('credentials.json') as f:
            service_email = json.load(f).get('client_email', 'unknown')
    except:
        service_email = 'unknown'

    if SPREADSHEET_ID:
        print(f"\n[2/5] Opening spreadsheet by ID: {SPREADSHEET_ID[:20]}...")
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            print(f"✅ Spreadsheet opened: {sh.title}")
            print(f"   URL: {sh.url}")
        except gspread.exceptions.APIError as e:
            error_str = str(e)
            if '403' in error_str:
                print("❌ ERROR: 403 Forbidden - Permission denied!")
                print("")
                print("   This usually means one of:")
                print("   1. Google Sheets API is NOT enabled")
                print("      → Go to: https://console.cloud.google.com/apis/library")
                print("      → Search 'Google Sheets API' and ENABLE it")
                print("")
                print("   2. Sheet not shared with service account")
                print(f"      → Share the spreadsheet with: {service_email}")
                print("      → Give 'Editor' access")
                print("")
                print("   3. Wrong spreadsheet ID")
                print(f"      → Current ID: {SPREADSHEET_ID}")
            else:
                print(f"❌ ERROR: API error: {e}")
            return False
        except PermissionError as e:
            print("❌ ERROR: Permission denied!")
            print(f"   Share the spreadsheet with: {service_email}")
            print("   Or enable Google Sheets API at:")
            print("   https://console.cloud.google.com/apis/library")
            return False
        except Exception as e:
            print(f"❌ ERROR: Failed to open spreadsheet: {type(e).__name__}: {e}")
            return False
    else:
        print(f"\n[2/5] Opening '{SPREADSHEET_NAME}'...")
        print("   (searching by name requires Drive API)")
        try:
            sh = gc.open(SPREADSHEET_NAME)
            print(f"✅ Spreadsheet opened: {sh.title}")
            print(f"   URL: {sh.url}")
        except gspread.SpreadsheetNotFound:
            print("❌ ERROR: Spreadsheet not found!")
            print("   Make sure you shared the sheet with the service account email")
            return False
        except gspread.exceptions.APIError as e:
            error_str = str(e)
            if '403' in error_str and '/drive/' in error_str:
                print("❌ ERROR: Google Drive API not enabled!")
                print("   SOLUTION: Either:")
                print("   1. Enable Drive API at: https://console.cloud.google.com/apis/library")
                print("      (search for 'Google Drive API' and enable it)")
                print("   OR")
                print("   2. Set SPREADSHEET_ID in this test file to open by ID instead")
                print("      (Get ID from sheet URL: .../spreadsheets/d/SPREADSHEET_ID/edit)")
            else:
                print(f"❌ ERROR: API error: {e}")
            return False
        except Exception as e:
            print(f"❌ ERROR: Failed to open spreadsheet: {e}")
            return False

    # Step 3: List all worksheets
    print("\n[3/5] Listing all worksheets...")
    try:
        worksheets = sh.worksheets()
        print(f"✅ Found {len(worksheets)} worksheets:")
        for ws in worksheets:
            print(f"   - {ws.title} ({ws.row_count} rows, {ws.col_count} cols)")
    except Exception as e:
        print(f"❌ ERROR: Failed to list worksheets: {e}")
        return False

    # Step 4: Read Working List header
    print("\n[4/5] Reading Working List 2025 header row...")
    try:
        wl = sh.worksheet('Working List 2025')
        headers = wl.row_values(1)
        print(f"✅ Found {len(headers)} columns:")
        for i, header in enumerate(headers[:12], 1):  # Show first 12
            print(f"   {i:2d}. {header}")
        if len(headers) > 12:
            print(f"   ... ({len(headers) - 12} more columns)")
    except Exception as e:
        print(f"❌ ERROR: Failed to read headers: {e}")
        return False

    # Step 5: Read sample data
    print("\n[5/5] Reading first 3 data rows...")
    try:
        data = wl.get('A2:J4')  # First 3 rows, first 10 columns
        print(f"✅ Read {len(data)} rows:")
        for i, row in enumerate(data, 2):
            practice = row[0] if len(row) > 0 else "N/A"
            phone = row[1] if len(row) > 1 else "N/A"
            print(f"   Row {i}: {practice} | {phone}")
    except Exception as e:
        print(f"❌ ERROR: Failed to read data: {e}")
        return False

    # Success!
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now use gspread to build the EOY tool.")
    return True


def show_setup_instructions():
    """Print setup instructions if test fails"""
    print("\n" + "=" * 60)
    print("GSPREAD SETUP INSTRUCTIONS")
    print("=" * 60)
    print("""
1. Install gspread:
   pip install gspread oauth2client

2. Enable APIs (CRITICAL - most common issue!):
   a. Go to: https://console.cloud.google.com/apis/library
   b. Enable "Google Sheets API"
   c. Enable "Google Drive API" (only needed if opening by name)

3. Create Google Service Account:
   a. Go to: https://console.cloud.google.com
   b. Select project or create new one
   c. APIs & Services → Credentials
   d. Create Credentials → Service Account
      - Name: "gspread-eoy-tool"
   e. Click the service account email
   f. Keys tab → Add Key → Create New Key → JSON
   g. Rename downloaded file to: credentials.json
   h. Place in project root directory

4. Share Sheet with Service Account:
   a. Open your Google Sheet in browser
   b. Click Share button (top right)
   c. Paste service account email (ends with .iam.gserviceaccount.com)
   d. Set to Editor
   e. Send

5. (Optional) Use spreadsheet ID to skip Drive API:
   - Get ID from URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   - Set SPREADSHEET_ID at top of this file

6. Run this script again:
   python scripts/tests/test_gspread.py
""")


if __name__ == '__main__':
    success = test_connection()

    if not success:
        show_setup_instructions()
        exit(1)
    else:
        exit(0)
