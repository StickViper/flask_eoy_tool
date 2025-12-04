"""
Test gspread connection to OBGYN List 2025 - Use This List!
Run this AFTER completing gspread setup (see setup instructions below)
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
        print("   Place credentials.json in C:\\Users\\noagi\\Desktop\\JGDC\\")
        return False
    except Exception as e:
        print(f"❌ ERROR: Authentication failed: {e}")
        return False

    # Step 2: Open spreadsheet
    print("\n[2/5] Opening 'OBGYN List 2025 - Use This List!'...")
    try:
        sh = gc.open('OBGYN List 2025 - Use This List!')
        print(f"✅ Spreadsheet opened: {sh.title}")
        print(f"   URL: {sh.url}")
    except gspread.SpreadsheetNotFound:
        print("❌ ERROR: Spreadsheet not found!")
        print("   Make sure you shared the sheet with the service account email")
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

2. Create Google Service Account (3 min):
   a. Go to: https://console.cloud.google.com
   b. Select project or create new one
   c. APIs & Services → Credentials
   d. Create Credentials → Service Account
      - Name: "gspread-eoy-tool"
      - Role: None (we'll grant per-sheet)
   e. Click the service account email
   f. Keys tab → Add Key → Create New Key → JSON
   g. Download saves as project-id-abc123.json
   h. Rename to: credentials.json
   i. Move to: C:\\Users\\noagi\\Desktop\\JGDC\\credentials.json

3. Share Sheet with Service Account (1 min):
   a. Open 'OBGYN List 2025 - Use This List!' in browser
   b. Share button (top right)
   c. Paste service account email (from step 2.e)
   d. Set to Editor
   e. Send

4. Run this script again:
   python scripts/test_gspread.py
""")


if __name__ == '__main__':
    success = test_connection()

    if not success:
        show_setup_instructions()
        exit(1)
    else:
        exit(0)
