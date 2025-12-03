#!/usr/bin/env python3
"""Comprehensive Google Sheets authentication diagnostics"""

import json
import sys

print("=" * 70)
print("GOOGLE SHEETS AUTHENTICATION DIAGNOSTICS")
print("=" * 70)
print()

# Test 1: Check credentials file
print("[1/6] Checking credentials.json file...")
try:
    with open('credentials.json', 'r') as f:
        creds_data = json.load(f)

    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    missing = [f for f in required_fields if f not in creds_data]

    if missing:
        print(f"  ✗ Missing required fields: {missing}")
        sys.exit(1)

    print(f"  ✓ Valid JSON with all required fields")
    print(f"  ✓ Service account: {creds_data['client_email']}")
    print(f"  ✓ Project: {creds_data['project_id']}")
    print()
except FileNotFoundError:
    print("  ✗ credentials.json not found!")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"  ✗ Invalid JSON: {e}")
    sys.exit(1)

# Test 2: Import required libraries
print("[2/6] Checking required libraries...")
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    print(f"  ✓ gspread version: {gspread.__version__}")
    print(f"  ✓ oauth2client available")
    print()
except ImportError as e:
    print(f"  ✗ Missing library: {e}")
    sys.exit(1)

# Test 3: Create credentials object
print("[3/6] Creating credentials object...")
try:
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    print(f"  ✓ Credentials object created")
    print(f"  ✓ Scopes: {len(scope)} scopes")
    print()
except Exception as e:
    print(f"  ✗ Failed to create credentials: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Authorize gspread client
print("[4/6] Authorizing gspread client...")
try:
    gc = gspread.authorize(creds)
    print(f"  ✓ Client authorized")
    print()
except Exception as e:
    print(f"  ✗ Authorization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Try to list spreadsheets (if possible)
print("[5/6] Testing API access...")
try:
    # Try to open a test spreadsheet by ID
    test_id = '1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0'
    print(f"  Testing spreadsheet ID: {test_id}")

    sh = gc.open_by_key(test_id)
    print(f"  ✓ Successfully opened: {sh.title}")
    print(f"  ✓ URL: {sh.url}")
    print()

except gspread.exceptions.APIError as e:
    print(f"  ✗ API Error: {e}")
    print()
    print("  Response details:")
    if hasattr(e, 'response'):
        print(f"    Status code: {e.response.status_code}")
        print(f"    Response text: {e.response.text[:500]}")
    print()

    # Try alternative approaches
    print("  Trying alternative authentication method...")
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds_alt = Credentials.from_service_account_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        service = build('sheets', 'v4', credentials=creds_alt)

        # Try to get spreadsheet metadata
        result = service.spreadsheets().get(spreadsheetId=test_id).execute()
        print(f"  ✓ Alternative method worked! Title: {result.get('properties', {}).get('title')}")
        print()

    except Exception as e2:
        print(f"  ✗ Alternative method also failed: {e2}")
        import traceback
        traceback.print_exc()
        print()

except gspread.exceptions.SpreadsheetNotFound as e:
    print(f"  ✗ Spreadsheet not found: {e}")
    print("  This means authentication works but the spreadsheet ID is wrong")
    print("  or the sheet hasn't been shared with the service account")
    print()

except PermissionError as e:
    print(f"  ✗ Permission denied: {e}")
    print()
    print("  This is a 403 Forbidden error. Possible causes:")
    print("  1. Spreadsheet not shared with service account email")
    print("  2. Service account doesn't have Editor/Viewer permissions")
    print("  3. Organization policy blocking external service accounts")
    print("  4. Spreadsheet ID is incorrect")
    print()

except Exception as e:
    print(f"  ✗ Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 6: Check if we can create a new spreadsheet (tests write permissions)
print("[6/6] Testing spreadsheet creation (to verify account is active)...")
try:
    test_sheet = gc.create('AUTH_TEST_DELETE_ME')
    print(f"  ✓ Successfully created test spreadsheet!")
    print(f"  ✓ Title: {test_sheet.title}")
    print(f"  ✓ URL: {test_sheet.url}")
    print()
    print("  IMPORTANT: Delete this test spreadsheet from your Google Drive")
    print(f"  URL: {test_sheet.url}")
    print()

    # Try to delete it
    try:
        gc.del_spreadsheet(test_sheet.id)
        print("  ✓ Test spreadsheet automatically deleted")
        print()
    except:
        print("  ! Could not auto-delete. Please delete manually from Drive.")
        print()

except Exception as e:
    print(f"  ✗ Could not create spreadsheet: {e}")
    print("  This might indicate the service account has restrictions")
    print()

print("=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)
print()
print("If authentication works but you can't access the specific spreadsheet:")
print("  1. Open: https://docs.google.com/spreadsheets/d/1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0")
print("  2. Click 'Share' button")
print(f"  3. Add: {creds_data['client_email']}")
print("  4. Set permission to 'Editor'")
print("  5. Uncheck 'Notify people'")
print("  6. Click 'Share'")
print()
print("If using Google Workspace with domain restrictions:")
print("  - Admin may need to allow external service accounts")
print("  - Check: Admin console > Security > API Controls > Domain-wide delegation")
print()
