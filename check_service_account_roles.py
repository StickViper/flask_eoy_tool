#!/usr/bin/env python3
"""Check service account IAM roles and permissions"""

import json

print("=" * 70)
print("SERVICE ACCOUNT IAM ROLE CHECKER")
print("=" * 70)
print()

with open('credentials.json') as f:
    creds = json.load(f)

project_id = creds['project_id']
service_account_email = creds['client_email']

print(f"Project: {project_id}")
print(f"Service Account: {service_account_email}")
print()

print("=" * 70)
print("REQUIRED IAM ROLES FOR GOOGLE SHEETS ACCESS")
print("=" * 70)
print()

print("The service account needs IAM roles in the GCP project:")
print()
print("OPTION A - Minimal permissions (recommended):")
print("  • No IAM roles needed (just share the spreadsheet)")
print()
print("OPTION B - Project-level access:")
print("  • roles/editor (full project access)")
print("  OR")
print("  • roles/serviceusage.serviceUsageConsumer (API access)")
print()

print("=" * 70)
print("HOW TO CHECK/FIX IAM ROLES")
print("=" * 70)
print()

print("1. Go to IAM settings:")
print(f"   https://console.cloud.google.com/iam-admin/iam?project={project_id}")
print()

print("2. Look for this service account in the list:")
print(f"   {service_account_email}")
print()

print("3. Check what role(s) it has")
print()

print("4. If it has NO roles or very restricted roles:")
print("   a) Click the pencil icon to edit")
print("   b) Add role: 'Service Usage Consumer'")
print("   c) Save")
print()

print("=" * 70)
print("ALTERNATIVE: ENABLE APIS FOR THE PROJECT")
print("=" * 70)
print()

print("The 403 errors suggest APIs might not be enabled. Enable these:")
print()

print("1. Google Sheets API:")
print(f"   https://console.cloud.google.com/apis/library/sheets.googleapis.com?project={project_id}")
print()

print("2. Google Drive API:")
print(f"   https://console.cloud.google.com/apis/library/drive.googleapis.com?project={project_id}")
print()

print("Click 'ENABLE' on each page, then wait 5-10 minutes.")
print()

print("=" * 70)
print("MOST LIKELY SOLUTION")
print("=" * 70)
print()

print("Since you can authenticate but get 403 on API calls:")
print()
print("1. APIs are not enabled in the project (most likely)")
print(f"   → Enable Sheets + Drive APIs at: https://console.cloud.google.com/apis/dashboard?project={project_id}")
print()
print("2. Service account has no project permissions")
print(f"   → Add 'Service Usage Consumer' role at: https://console.cloud.google.com/iam-admin/iam?project={project_id}")
print()
print("3. Spreadsheet not shared (separate issue)")
print(f"   → Share with: {service_account_email}")
print()

print("=" * 70)
print("QUICK CHECK - ARE APIS ENABLED?")
print("=" * 70)
print()

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    creds_obj = Credentials.from_service_account_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    # Try to list enabled services
    service = build('serviceusage', 'v1', credentials=creds_obj)

    parent = f'projects/{project_id}'
    request = service.services().list(
        parent=parent,
        filter='state:ENABLED',
        fields='services(name,state)'
    )

    response = request.execute()

    enabled_services = [s['name'] for s in response.get('services', [])]

    print("Enabled APIs:")

    sheets_enabled = any('sheets' in s for s in enabled_services)
    drive_enabled = any('drive' in s for s in enabled_services)

    if sheets_enabled:
        print("  ✓ Google Sheets API - ENABLED")
    else:
        print("  ✗ Google Sheets API - NOT ENABLED")
        print(f"    → Enable: https://console.cloud.google.com/apis/library/sheets.googleapis.com?project={project_id}")

    if drive_enabled:
        print("  ✓ Google Drive API - ENABLED")
    else:
        print("  ✗ Google Drive API - NOT ENABLED")
        print(f"    → Enable: https://console.cloud.google.com/apis/library/drive.googleapis.com?project={project_id}")

    print()

    if not sheets_enabled or not drive_enabled:
        print("ACTION REQUIRED: Enable the missing APIs above")
    else:
        print("APIs are enabled. Issue must be with spreadsheet sharing.")

except ImportError:
    print("Cannot check automatically (google-api-python-client needed)")
    print(f"Check manually: https://console.cloud.google.com/apis/dashboard?project={project_id}")

except HttpError as e:
    if e.resp.status == 403:
        print("✗ Cannot check - service account lacks permission to view APIs")
        print(f"  → Go manually to: https://console.cloud.google.com/apis/dashboard?project={project_id}")
    else:
        print(f"✗ HTTP Error: {e}")

except Exception as e:
    print(f"Cannot check automatically: {e}")
    print(f"Check manually: https://console.cloud.google.com/apis/dashboard?project={project_id}")

print()
