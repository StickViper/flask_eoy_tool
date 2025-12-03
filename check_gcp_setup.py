#!/usr/bin/env python3
"""Check Google Cloud Project API setup"""

import json
import requests

print("=" * 70)
print("GOOGLE CLOUD PROJECT API CHECK")
print("=" * 70)
print()

# Load credentials
with open('credentials.json', 'r') as f:
    creds = json.load(f)

project_id = creds['project_id']
service_account = creds['client_email']

print(f"Project ID: {project_id}")
print(f"Service Account: {service_account}")
print()

print("REQUIRED APIs for Google Sheets access:")
print("  1. Google Sheets API")
print("  2. Google Drive API")
print()

print("TO ENABLE THESE APIs:")
print()
print(f"1. Go to: https://console.cloud.google.com/apis/dashboard?project={project_id}")
print()
print("2. Click '+ ENABLE APIS AND SERVICES'")
print()
print("3. Search for and enable:")
print("   - Google Sheets API")
print("   - Google Drive API")
print()
print("4. Wait 5-10 minutes for propagation")
print()

print("ALTERNATIVE: Try using Sheets API directly (no Drive API needed)")
print("=" * 70)
print()

# Try using google-api-python-client directly
print("Testing Sheets API v4 (without Drive API)...")
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    # Use only Sheets API scope (not Drive)
    creds_obj = Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    service = build('sheets', 'v4', credentials=creds_obj)

    spreadsheet_id = '1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0'

    print(f"  Attempting to read spreadsheet: {spreadsheet_id}")

    # Try to get spreadsheet properties
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    print(f"  ✓ SUCCESS! Can access via Sheets API v4")
    print(f"  ✓ Title: {result.get('properties', {}).get('title')}")
    print(f"  ✓ Sheets: {len(result.get('sheets', []))}")
    print()

    # List sheet names
    sheets = result.get('sheets', [])
    print("  Available worksheets:")
    for sheet in sheets:
        title = sheet['properties']['title']
        print(f"    - {title}")
    print()

    # Try to read data from first sheet
    try:
        range_name = 'Working List 2025!A1:K10'
        values_result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = values_result.get('values', [])
        print(f"  ✓ Successfully read data from 'Working List 2025'")
        print(f"  ✓ Got {len(values)} rows")
        if values:
            print(f"  ✓ Headers: {values[0]}")
        print()

        print("=" * 70)
        print("✓✓✓ SHEETS API v4 WORKS! ✓✓✓")
        print("=" * 70)
        print()
        print("RECOMMENDATION: Modify eoy_tool.py to use google-api-python-client")
        print("instead of gspread, since Sheets API works but Drive API doesn't.")
        print()

    except HttpError as e:
        print(f"  ✗ Could not read data: {e}")
        print()

except ImportError:
    print("  ✗ google-api-python-client not installed")
    print("  Run: pip install google-api-python-client")
    print()

except HttpError as e:
    if e.resp.status == 403:
        print(f"  ✗ 403 Forbidden - Sheets API might not be enabled")
        print(f"  Enable at: https://console.cloud.google.com/apis/library/sheets.googleapis.com?project={project_id}")
    elif e.resp.status == 404:
        print(f"  ✗ 404 Not Found - spreadsheet doesn't exist or not shared")
    else:
        print(f"  ✗ HTTP {e.resp.status}: {e}")
    print()

except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    print()

print()
print("NEXT STEPS:")
print()
print("Option A: Enable Drive API in GCP Console")
print(f"  → https://console.cloud.google.com/apis/library/drive.googleapis.com?project={project_id}")
print()
print("Option B: Switch to Sheets API v4 (if it works)")
print("  → Use google-api-python-client instead of gspread")
print()
print("Option C: Check organization policies")
print("  → Ask workspace admin about service account restrictions")
print()
