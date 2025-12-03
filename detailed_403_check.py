#!/usr/bin/env python3
"""Detailed 403 error investigation"""

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

print("=" * 70)
print("DETAILED 403 FORBIDDEN INVESTIGATION")
print("=" * 70)
print()

with open('credentials.json') as f:
    creds_data = json.load(f)

service_account_email = creds_data['client_email']
spreadsheet_id = '1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0'

print("Service Account Email:")
print(f"  {service_account_email}")
print()
print("Spreadsheet:")
print(f"  ID: {spreadsheet_id}")
print(f"  URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
print()

# Authenticate
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(creds)

print("=" * 70)
print("PLEASE CHECK THE FOLLOWING:")
print("=" * 70)
print()

print("1. Open this URL in your browser:")
print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
print()

print("2. Click the 'Share' button (top right)")
print()

print("3. Check if this email is in the list of people with access:")
print(f"   {service_account_email}")
print()

print("4. If NOT in the list:")
print("   a) Click 'Add people and groups'")
print(f"   b) Paste: {service_account_email}")
print("   c) Set permission to 'Editor' (or 'Viewer' for read-only)")
print("   d) UNCHECK 'Notify people' (it's a robot, not a person)")
print("   e) Click 'Share' or 'Send'")
print()

print("5. If ALREADY in the list:")
print("   a) Check the permission level (should be Editor or Viewer)")
print("   b) Try removing and re-adding it")
print("   c) Check if there's a domain restriction (e.g., 'Only people at...")
print()

print("6. Organization/Workspace restrictions:")
print("   If this is a Google Workspace account, check:")
print("   a) External sharing settings")
print("   b) Service account policies")
print("   c) Ask your Google Workspace admin if service accounts are blocked")
print()

print("=" * 70)
print("TESTING ACCESS...")
print("=" * 70)
print()

try:
    sh = gc.open_by_key(spreadsheet_id)
    print(f"✓✓✓ SUCCESS! ✓✓✓")
    print(f"✓ Opened: {sh.title}")
    worksheets = sh.worksheets()
    worksheet_names = [ws.title for ws in worksheets]
    print(f"✓ Worksheets: {worksheet_names}")
    print()
    print("Access is working! You can now run the EOY tool.")

except gspread.exceptions.APIError as e:
    error_text = str(e)

    if '403' in error_text or 'Forbidden' in error_text:
        print("✗ Still getting 403 Forbidden")
        print()
        print("This means ONE of:")
        print()
        print("  A) Spreadsheet not shared with service account")
        print(f"     → Check: {service_account_email} is in Share settings")
        print()
        print("  B) Wrong spreadsheet ID")
        print(f"     → Verify: {spreadsheet_id}")
        print()
        print("  C) Organization policy blocking service accounts")
        print("     → Contact: Google Workspace admin")
        print()
        print("  D) Spreadsheet is in a different Google account")
        print("     → Make sure you're logged into the correct Google account")
        print()

    elif '404' in error_text or 'Not found' in error_text:
        print("✗ 404 Not Found - Spreadsheet doesn't exist or wrong ID")
        print(f"   Check: {spreadsheet_id}")

    else:
        print(f"✗ Unexpected API error: {e}")

except PermissionError:
    print("✗ Permission Error (403 Forbidden)")
    print()
    print("MOST LIKELY CAUSE:")
    print(f"  The spreadsheet has NOT been shared with: {service_account_email}")
    print()
    print("FIX:")
    print(f"  1. Open: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print("  2. Click 'Share'")
    print(f"  3. Add: {service_account_email}")
    print("  4. Set to 'Editor'")
    print("  5. Click 'Share'")

except Exception as e:
    print(f"✗ Unexpected error: {type(e).__name__}: {e}")

print()
print("=" * 70)
print("COPY THIS FOR SHARING:")
print("=" * 70)
print(service_account_email)
print("=" * 70)
