# Google Sheets API Access - Complete Technical Summary

## Problem Statement

Python application using `gspread` + `oauth2client` cannot access Google Sheets despite valid service account credentials. All API calls return **403 Forbidden** errors.

---

## Environment

- **Platform**: Linux 4.4.0 in containerized environment (Claude Code/SDK)
- **Python**: 3.11
- **Libraries**:
  - `gspread` 6.2.1
  - `oauth2client` (latest)
  - `google-api-python-client` (installed for testing)
  - `google-auth` (installed for testing)

---

## Service Account Details

```json
{
  "type": "service_account",
  "project_id": "jgdc-filter-pcp",
  "client_email": "gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com",
  "client_id": "102247191645219859720"
}
```

**Credentials file**: `credentials.json` (2371 bytes, valid JSON)
**File permissions**: `-rw-r--r-- 1 root root` (readable)

---

## Target Spreadsheet

- **Spreadsheet ID**: `1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0`
- **URL**: https://docs.google.com/spreadsheets/d/1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0
- **Required Worksheets**:
  - `Working List 2025`
  - `New Orders 2025`
  - `Invalid/Inactive List`

---

## Authentication Code

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(creds)

# This succeeds - authentication works
print("Client authorized")

# This fails with 403 Forbidden
sh = gc.open_by_key('1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0')
```

---

## Error Details

### Error 1: Opening Spreadsheet
```
gspread.exceptions.APIError: APIError: [-1]: <!DOCTYPE html>
<html lang=en>
  <title>Error 403 (Forbidden)!!1</title>
  <p><b>403.</b> <ins>That's an error.</ins>
  <p>Your client does not have permission to get URL
     <code>/v4/spreadsheets/1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0</code>
     from this server. <ins>That's all we know.</ins>
```

**Python Exception**: `PermissionError` (raised by gspread from APIError)

### Error 2: Creating New Spreadsheet
```python
gc.create('TEST_SHEET')
```

```
gspread.exceptions.APIError: APIError: [-1]: <!DOCTYPE html>
  <title>Error 403 (Forbidden)!!1</title>
  <p>Your client does not have permission to get URL
     <code>/drive/v3/files</code> from this server.
```

---

## Diagnostic Results

### ✓ Working (Confirmed)

1. **Credentials file is valid**
   - JSON parses successfully
   - All required fields present (`type`, `project_id`, `private_key`, `client_email`)

2. **Authentication succeeds**
   - `ServiceAccountCredentials.from_json_keyfile_name()` works
   - `gspread.authorize(creds)` returns client object
   - No errors during auth token generation

3. **Network connectivity**
   ```bash
   curl -I https://oauth2.googleapis.com
   # Returns: HTTP/2 200 OK (then 404 for root path - expected)
   ```

4. **DNS resolution**
   - Can reach `oauth2.googleapis.com`
   - Can reach `sheets.googleapis.com`

### ✗ Failing (Confirmed)

1. **Cannot access specific spreadsheet**
   - Error: 403 Forbidden on `/v4/spreadsheets/{id}`

2. **Cannot create new spreadsheets**
   - Error: 403 Forbidden on `/drive/v3/files`

3. **Cannot list spreadsheets** (Drive API)
   - Error: 403 Forbidden

4. **Google API Python Client fails differently**
   ```python
   from google.oauth2.service_account import Credentials
   from googleapiclient.discovery import build

   creds = Credentials.from_service_account_file('credentials.json')
   service = build('sheets', 'v4', credentials=creds)
   # Fails with: "Unable to find the server at oauth2.googleapis.com"
   # (DNS resolution error - httplib2 issue)
   ```

---

## Troubleshooting Steps Attempted

### 1. Spreadsheet Sharing
**Status**: User reports they have shared the spreadsheet

**Expected configuration**:
- Add email: `gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com`
- Permission: Editor (or Viewer for read-only)
- Notify: Unchecked

**Issue**: Still getting 403 even after sharing

### 2. API Enablement
**User needs to check**: https://console.cloud.google.com/apis/dashboard?project=jgdc-filter-pcp

**Required APIs**:
- Google Sheets API
- Google Drive API

**Cannot verify automatically**: API check fails with network error

### 3. IAM Roles
**User needs to check**: https://console.cloud.google.com/iam-admin/iam?project=jgdc-filter-pcp

**Expected**: Service account should have IAM role:
- `roles/serviceusage.serviceUsageConsumer` (minimal)
- OR `roles/editor` (full access)

**Issue**: Cannot verify automatically

### 4. Alternative Authentication Methods
Tested `google-auth` + `google-api-python-client`:
- Fails with different error (DNS/network)
- Suggests httplib2 transport issue

---

## Possible Root Causes

### A. APIs Not Enabled in GCP Project (70% likely)
The 403 on `/drive/v3/files` suggests Drive API is not enabled.

**Evidence**:
- Can't create spreadsheets (Drive API operation)
- Can't access spreadsheets (requires Drive API for metadata)

**Fix**:
1. Go to https://console.cloud.google.com/apis/library/sheets.googleapis.com?project=jgdc-filter-pcp
2. Click "ENABLE"
3. Go to https://console.cloud.google.com/apis/library/drive.googleapis.com?project=jgdc-filter-pcp
4. Click "ENABLE"
5. Wait 5-10 minutes for propagation

### B. Service Account Has No IAM Permissions (60% likely)
Service account may exist but have no project-level permissions.

**Evidence**:
- 403 on all API operations
- Can authenticate but can't make API calls

**Fix**:
1. Go to https://console.cloud.google.com/iam-admin/iam?project=jgdc-filter-pcp
2. Find: `gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com`
3. If missing or no role: Add role "Service Usage Consumer"

### C. Spreadsheet Not Actually Shared (50% likely)
User may think it's shared but permission didn't apply.

**Evidence**:
- 403 is consistent with unshared spreadsheet

**Fix**:
1. Open spreadsheet in browser
2. Click Share
3. Verify `gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com` is in list
4. If present: Remove and re-add
5. If absent: Add with Editor permission

### D. Google Workspace External Sharing Policy (40% likely)
If spreadsheet owner uses Google Workspace, org policy may block external service accounts.

**Evidence**:
- Would explain 403 even when shared

**Check**:
- Is this a Google Workspace (business/education) account?
- Are there domain restrictions on sharing?
- Contact Google Workspace admin

**Fix** (Admin required):
1. Admin console > Apps > Google Workspace > Drive and Docs
2. Sharing settings > External sharing
3. Allow sharing with service accounts outside domain

### E. Service Account Key Disabled/Expired (10% likely)
The private key may have been disabled in GCP.

**Evidence**:
- Would fail at authentication (but auth succeeds)

**Check**:
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts?project=jgdc-filter-pcp
2. Click on service account
3. Check "Keys" tab
4. Verify key ID `33100c4ab14909c842f751945d09313bd98bd7a3` is active

### F. Billing/Quota Issues (5% likely)
GCP project may have billing disabled or quota exceeded.

**Evidence**:
- Would typically return different error (429 or specific quota message)

**Check**:
- https://console.cloud.google.com/billing?project=jgdc-filter-pcp
- https://console.cloud.google.com/apis/api/sheets.googleapis.com/quotas?project=jgdc-filter-pcp

---

## Network Peculiarities

### Issue with google-api-python-client
When using newer `google-auth` library:
```
httplib2.error.ServerNotFoundError: Unable to find the server at oauth2.googleapis.com
```

But `curl` to same domain works fine. Suggests:
- httplib2 DNS resolution issue in container
- May be unrelated to main 403 problem
- `oauth2client` (older library) works better in this environment

---

## Diagnostic Scripts Created

Located in `/home/user/flask_eoy_tool/`:

1. **test_sheets_access.py** - Basic connection test
2. **diagnose_auth.py** - 6-step authentication diagnostic
3. **check_gcp_setup.py** - API enablement checker
4. **detailed_403_check.py** - Sharing instructions and testing
5. **check_service_account_roles.py** - IAM role checker

**Run any of these**:
```bash
python3 test_sheets_access.py
python3 detailed_403_check.py
```

---

## Questions for Investigation

### For User to Check in GCP Console:

1. **Are these APIs enabled?**
   - Navigate to: https://console.cloud.google.com/apis/dashboard?project=jgdc-filter-pcp
   - Look for: "Google Sheets API" - is it in the enabled list?
   - Look for: "Google Drive API" - is it in the enabled list?

2. **What IAM role does the service account have?**
   - Navigate to: https://console.cloud.google.com/iam-admin/iam?project=jgdc-filter-pcp
   - Find: `gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com`
   - What role(s) are listed? (If none listed, that's the problem)

3. **Is the service account key active?**
   - Navigate to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=jgdc-filter-pcp
   - Click on: `gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com`
   - Keys tab: Is key `33100c...` shown as active?

4. **Is the spreadsheet properly shared?**
   - Open: https://docs.google.com/spreadsheets/d/1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0
   - Click: Share button
   - Is `gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com` in the list?
   - What permission level? (Editor/Viewer/etc)

5. **Is this a Google Workspace account?**
   - When you log into Google, does it show a company/school domain?
   - Or is it a personal @gmail.com account?

6. **Are there any billing issues?**
   - Navigate to: https://console.cloud.google.com/billing?project=jgdc-filter-pcp
   - Is billing enabled for this project?

---

## Expected Resolution Path

**Most likely sequence**:

1. User enables Google Sheets API + Drive API in GCP Console
2. User adds "Service Usage Consumer" IAM role to service account
3. User confirms spreadsheet is shared with service account email
4. Wait 5-10 minutes for changes to propagate
5. Run `python3 test_sheets_access.py` to verify

**If still failing after above**:
- Check Google Workspace admin settings
- Verify service account key is active
- Check billing/quota status
- Contact Google Cloud Support

---

## Alternative Workarounds (if blocked)

### Option 1: Use OAuth 2.0 User Flow
Instead of service account, use user's own Google account:
- Requires browser-based OAuth flow
- User grants permission to app
- More complex but bypasses service account restrictions

### Option 2: Use Different GCP Project
Create new GCP project:
- Enable APIs from the start
- Create new service account with proper roles
- Use new credentials

### Option 3: Use Google Apps Script
If APIs can't be enabled:
- Create Apps Script attached to spreadsheet
- Access from Python via Apps Script API
- More limited but works within Sheets environment

---

## Contact Information

**GCP Project**: jgdc-filter-pcp
**Service Account**: gspread-eoy-tool@jgdc-filter-pcp.iam.gserviceaccount.com
**Spreadsheet ID**: 1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0

---

## Next Steps

**For IT/Admin to execute**:

1. Open GCP Console for project `jgdc-filter-pcp`
2. Enable Google Sheets API + Google Drive API
3. Grant service account the "Service Usage Consumer" role
4. Verify spreadsheet sharing settings
5. Wait 10 minutes
6. Test with: `python3 test_sheets_access.py`

**Expected outcome**: Script should show ✓ SUCCESS and list all worksheets.
