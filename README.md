# JGDC - Provider Outreach System

Healthcare provider outreach system for the Canavan Foundation (nonprofit).

## Project Structure

```
JGDC/
├── README.md                    # This file
├── TODO.md                      # Master task list
│
├── Google Apps Script Files/    # Deployed to Google Sheets
│   ├── ToolboxSuite.js         # Main utilities for Working List sheets
│   ├── UniversalProviderSuite.js  # Provider verification (API-based)
│   ├── QuickStartWizard.html   # Setup wizard
│   └── VerificationSidebar.html   # Manual verification UI
│
├── Python Scripts/              # Local data filtering
│   └── nppes_filter_pcps.py    # NPPES data filtering (v3.0)
│
└── Data/                        # CSV files (gitignored)
    ├── Filtered CSVs (TX, TN, OK, OR)
    └── Working lists
```

## Workflow

### 1. Data Acquisition (Python - Local)
- Download NPPES bulk data from CMS
- Run `nppes_filter_pcps.py` to filter by:
  - Taxonomy codes (Family Medicine, Internal Medicine, FNP only)
  - States
  - Independent clinics (strict validation)
  - Removes specialists, hospitalists, pediatricians
- **Output:** Filtered CSVs by state

### 2. Import to Google Sheets
- **Manual step:** Import filtered CSVs to Google Sheets
- Sheet naming: `PCP_[STATE]_import`

### 3. Automated Verification (Google Apps Script)
- **Script:** `UniversalProviderSuite.js`
- Uses Google Places API to verify providers are operational
- **Output Sheets:**
  - `nppes_verified` - Operational providers
  - `nppes_errors` - Failed verification
  - `nppes_formatted` - Export-ready

### 4. Manual Verification (Edge Cases)
- **Script:** `VerificationSidebar.html`
- Sidebar UI for manual review of ambiguous cases

### 5. Outreach & Calling
- **Script:** `ToolboxSuite.js` (event-driven formatting)
- Working List format: `Working List [YEAR]`
- Color-coded by call status:
  - Yellow: Successful Order
  - Green: Requested Email
  - Red: Potentially Invalid
  - Fuchsia: Voicemail/No Answer
  - White: Not interested

### 6. Year-End Consolidation
- **Script:** `ToolboxSuite.js` (consolidation tools)
- Merges multiple sheets for same year
- Deduplicates by phone/NPI/address
- Preserves order history across years (2023 QTY, 2024 QTY, 2025 QTY)

---

## Setup Instructions

### Google Apps Script Deployment

#### Option 1: Manual Copy-Paste
1. Open your Google Sheet
2. Extensions → Apps Script
3. Copy contents of each `.js` and `.html` file
4. Create matching filenames in Apps Script editor
5. Save & deploy

#### Option 2: clasp (Command-line)
```bash
# Install clasp
npm install -g @google/clasp

# Login
clasp login

# Clone your existing project
clasp clone <SCRIPT_ID>

# Or create new project
clasp create --title "JGDC Provider Tools" --type sheets

# Push code
clasp push
```

**Find your SCRIPT_ID:**
1. Open your Google Sheet → Extensions → Apps Script
2. Project Settings (gear icon)
3. Copy "Script ID"

### Python Setup
```bash
cd "PCP Hunt/NPPES_Data_Dissemination_September_2025_V2"
python3 nppes_filter_pcps.py
```

**Configuration** (edit `CONFIG` in nppes_filter_pcps.py):
- `DRY_RUN`: Set `True` for preview mode
- `TARGET_STATES`: Add state codes
- `FIX_CAPITALIZATION`: Toggle name fixes
- `ORGANIZATION_HANDLING`: Configure clinic filtering

---

## Tools Reference

### ToolboxSuite.js (Working List Sheets)
- **Event-driven formatting:** Auto-colors rows on status change
- **Search links:** Google search from Office column
- **Capitalization fix:** Fixes ALL CAPS, Mc/Mac, credentials
- **Consolidation:** Year-end data merge
- **Validation:** (TODO) Find data issues

### UniversalProviderSuite.js (Provider Verification Sheet)
- **API verification:** Google Places validation
- **Batch processing:** 25 providers per batch
- **Manual sidebar:** For edge cases
- **Deduplication:** By NPI/phone/address

### nppes_filter_pcps.py (Local Filtering)
- **v3.0 Features:**
  - Tightened taxonomy codes (no pediatrics, no specialists)
  - Independent clinic support (strict validation)
  - Capitalization fixes (6 types)
  - Dry-run preview mode
  - Excluded providers audit trail

---

## Key Files to Edit

### When adding new states:
- `nppes_filter_pcps.py` → `CONFIG['TARGET_STATES']`

### When changing provider type:
- `nppes_filter_pcps.py` → `CONFIG['PROVIDER_TYPE']`
- `UniversalProviderSuite.js` → `PROVIDER_CONFIG.PROVIDER_TYPE`

### When starting new year:
- Create new `Working List [YEAR]` sheet
- Update `ToolboxSuite.js` → `targetSheetName` in `onEdit()`
- Run consolidation on old year

---

## Known Issues & Limitations

1. **Manual import step:** No automated CSV → Sheets import (need UI for batch size control)
2. **Validation tools incomplete:** Stubs in place, need implementation
3. **"Not interested" enforcement:** Soft validation only (coworkers bypass it)
4. **Filter views:** Not implemented (fear of breaking routes)
5. **Capitalization scattered:** Needs to run at every stage (NPPES → Sheets → Verification)

---

## Contributing

This is a volunteer-run nonprofit project. When making changes:
1. Test on a COPY of the sheet first
2. Document what you changed
3. Update TODO.md with new tasks
4. Be cautious with automation (human error anxiety)

---

## Links

- **NPPES Data:** https://download.cms.gov/nppes/NPI_Files.html
- **Google Places API:** https://console.cloud.google.com
- **clasp Documentation:** https://github.com/google/clasp
