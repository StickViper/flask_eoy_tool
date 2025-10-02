# Provider Search - Google Apps Script

This folder contains the Apps Script code for the **Provider Search / Verification** sheet.

## Files

- **UniversalProviderSuite.js** - Main verification logic (API calls, batch processing)
- **QuickStartWizard.html** - Setup wizard UI
- **VerificationSidebar.html** - Manual verification sidebar
- **appsscript.json** - Apps Script manifest

## Setup with clasp

```bash
cd scripts/provider-search

# Get your Script ID from Provider Search sheet
# (Extensions → Apps Script → Settings → Script ID)

clasp clone <PROVIDER_SEARCH_SCRIPT_ID>

# This will create .clasp.json with your project ID
# Now you can push changes:
clasp push
```

## What this script does

1. **Automated verification** - Uses Google Places API to verify providers
2. **Batch processing** - 25 providers per batch, auto-schedules next batch
3. **Manual verification UI** - Sidebar for edge cases
4. **Output sheets:**
   - `nppes_verified` - Operational providers
   - `nppes_errors` - Failed verification
   - `nppes_formatted` - Export-ready

## Configuration

Edit `PROVIDER_CONFIG` in UniversalProviderSuite.js:
- Provider type (PCP, OBGYN)
- Target state
- Sheet naming (unified vs. separate)
- Verification thresholds
