# JGDC - Provider Outreach Management System

## 🎯 Project Overview

### What is this project?

This is a **healthcare provider outreach system** built for the **Canavan Foundation**, a nonprofit organization in the United States. The foundation reaches out to healthcare providers (doctors, nurse practitioners, medical clinics) to offer free educational brochures about Canavan disease - a rare genetic disorder.

The system helps volunteers:
1. **Find** primary care providers (PCPs) from a national database
2. **Verify** they are still in business and accepting patients
3. **Track** phone call outcomes over multiple years
4. **Manage** brochure orders and follow-ups

### Why does this project exist?

**The problem:**
- Manually finding and verifying thousands of doctors is time-consuming
- Tracking 3+ years of call history across multiple volunteers is messy
- Data quality issues (duplicate providers, wrong phone numbers, closed practices)
- Need to consolidate data from multiple sources at year-end

**The solution:**
This codebase automates the boring parts (filtering, verification) while providing spreadsheet-based tools for the human parts (calling, decision-making).

---

## 🏗️ System Architecture

### The Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: DATA ACQUISITION                              │
│ Download NPPES database → 11 MILLION healthcare providers       │
│ (National Plan and Provider Enumeration System - public CMS data)│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: FILTERING (Python - Local Computer)                     │
│ Filter 11M → ~30K providers per state                           │
│ • Only Family Medicine, Internal Medicine, Family NPs           │
│ • Only specific states (currently: TX, TN, OK, OR)             │
│ • Remove: Pediatricians, Specialists, Hospitals, Closed practices│
│ • Fix: ALL CAPS names, credential formats                       │
│ Script: data/nppes/.../nppes_filter_pcps.py                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: IMPORT TO GOOGLE SHEETS (Manual)                        │
│ Import filtered CSVs → Google Sheets                            │
│ Sheet name format: "PCP_TX_import"                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: MANUAL VERIFICATION (Google Apps Script)                │
│ 100% manual verification - works directly on import sheets:     │
│ • Add Search Links (works on selection OR whole sheet)         │
│ • Remove Duplicates (works on selection OR whole sheet)        │
│ • Sidebar verification with keyboard shortcuts (L, G, 1, 2, S) │
│ • Verified → All_Verified_Providers (row hidden, not deleted)  │
│ • Closed → Invalid/Inactive List (row hidden, not deleted)     │
│ Script: scripts/provider-search/UniversalProviderSuite.js v10  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: OUTREACH & CALLING (Google Sheets + Volunteers)        │
│ Working List sheets with:                                      │
│ • Color-coded call status (Yellow=Order, Red=Invalid, etc.)    │
│ • Year-over-year quantity tracking (2023/2024/2025 QTY columns)│
│ • Automatic row formatting on status change                    │
│ Script: scripts/pcp-list/ToolboxSuite.js                       │
│ Sheet name: "Working List 2025"                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: ORDER FULFILLMENT (Subsheet of PCP Sheet, External)     │
│ Copy orders to "New Orders 2025" sheet                          │
│ External volunteer packages and ships brochures                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: YEAR-END CONSOLIDATION (First time specific List is touched after year-end)│
│ Merge all data sources into master archive:                     │
│ • Combine multiple working lists from same year                 │
│ • Deduplicate by phone/NPI/address                              │
│ • Preserve order history across years                           │
│ • Clear statuses for next year's calling cycle                  │
│ Script: scripts/pcp-list/ToolboxSuite.js (consolidation tools)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure (File System)

```
JGDC/
│
├── README.md                          ← You are here (main documentation)
├── TODO.md                            ← Prioritized task list
├── STRUCTURE.md                       ← Visual folder guide
├── .gitignore                         ← Excludes CSVs, secrets from git
│
├── scripts/                           ← Google Apps Script code
│   │
│   ├── provider-search/               ← For "Provider Search" Google Sheet
│   │   ├── README.md                  ← Setup instructions
│   │   ├── UniversalProviderSuite.js  ← Main verification logic
│   │   ├── QuickStartWizard.html      ← Setup wizard UI
│   │   ├── VerificationSidebar.html   ← Manual verification UI
│   │   ├── appsscript.json            ← Apps Script config
│   │   └── .clasp.json                ← (created when you run: clasp clone)
│   │
│   └── pcp-list/                      ← For "Working List" Google Sheets
│       ├── README.md                  ← Setup instructions
│       ├── ToolboxSuite.js            ← Utilities (consolidation, validation)
│       └── .clasp.json                ← (created when you run: clasp clone)
│
├── data/                              ← All data files (gitignored)
│   │
│   ├── exports/                       ← CSV exports from Google Sheets
│   │   ├── PCP List 2025 - Working List 2025.csv
│   │   ├── PCP List 2025 - STATS.tsv
│   │   └── NPPES Provider Search - All_Verified_Providers.csv
│   │
│   └── nppes/                         ← NPPES bulk data (~11 GB)
│       ├── README.md
│       └── NPPES_Data_Dissemination_September_2025_V2/
│           ├── nppes_filter_pcps.py              ⭐ Python filter script
│           ├── npidata_pfile_*.csv               (11 GB - raw provider data)
│           ├── FILTERED_pcps_TX_20250927.csv     (filtered outputs)
│           ├── FILTERED_pcps_TN_20250929.csv
│           ├── FILTERED_pcps_OK_20250929.csv
│           └── FILTERED_pcps_OR_20250929.csv
│
└── docs/                              ← Documentation
    └── CLASP_SETUP.md                 ← How to sync Apps Script with git
```

---

## 🚀 Setup Instructions (First Time Setup)

### Prerequisites

1. **Google Account** - with access to the Google Sheets
2. **Python 3.x** - for NPPES filtering (`python --version` to check)
3. **Node.js** - for clasp tool (`node --version` to check)
4. **Git** - already initialized in this project
5. **Text editor** - VS Code, Sublime, or any code editor

### Step 1: Install clasp (Google Apps Script CLI)
[X]
```bash
# Open terminal/command prompt
npm install -g @google/clasp

# Verify installation
clasp --version

# Login to Google (opens browser)
clasp login
# Select your Google account that has access to the sheets
```

**What is clasp?**
- clasp = Command Line Apps Script Projects
- It lets you edit Google Apps Script files on your local computer
- Changes sync between local files and Google Sheets
- Enables version control with git

### Step 2: Get Your Google Apps Script IDs
[X]
**You need TWO script IDs (one for each Google Sheet):**

 1FXjGC-3NVUzKcQ-oEpDwptaX5gizcJp_3EFHoqLxTo5lo7Wiw2jDH8ri
#### For "Provider Search" sheet:
1. Open your "Provider Search" Google Sheet in browser
2. Click: **Extensions → Apps Script**
3. Click the gear icon (⚙️ Project Settings)
4. Copy the **Script ID** (looks like: `1a2b3c4d5e6f7g8h9i0j...`)
5. Save it somewhere (you'll use it in Step 3)

 1DjPdNWWtGbl4iR1jo4z9vsn-dTguko-AGxXF44MXvkSdxP3kyZQOqNVR 
#### For "PCP List 2025" (or "Working List") sheet:
1. Open your "PCP List 2025" Google Sheet in browser
2. Click: **Extensions → Apps Script**
3. Click the gear icon (⚙️ Project Settings)
4. Copy the **Script ID**
5. Save it somewhere


### Step 3: Link Local Code to Google Sheets
[X]

```bash
# Navigate to this project
cd "C:\Users\noagi\Desktop\JGDC"

# Link Provider Search script
cd scripts/provider-search
clasp clone <PASTE_PROVIDER_SEARCH_SCRIPT_ID_HERE>
# This creates .clasp.json file

# Link PCP List script
cd ../pcp-list
clasp clone <PASTE_PCP_LIST_SCRIPT_ID_HERE>
# This creates .clasp.json file

# You're done! Now you can sync code between local and Google Sheets
```

### Step 4: Verify Setup
[X]

```bash
# Test pushing code to Google Sheets
cd scripts/provider-search
clasp push
# This uploads your local files to Google Sheets

# Open Google Sheets Apps Script editor to verify
clasp open
# This opens your Apps Script project in browser

# Check git status
cd ../..
git status
# Should show .clasp.json files are gitignored (not tracked)
```

---

## 📖 How to Use This System

### Scenario 1: Adding a New State

**Goal:** You want to find PCPs in California (CA).

```bash
# 1. Edit the Python filter config
cd data/nppes/NPPES_Data_Dissemination_September_2025_V2

# 2. Open nppes_filter_pcps.py in editor
# Find this line (around line 24):
#   'TARGET_STATES': ['OK','OR','TN'],
# Change to:
#   'TARGET_STATES': ['CA'],

# 3. (Optional) Enable dry-run mode to preview first
# Find this line (around line 45):
#   'DRY_RUN': False,
# Change to:
#   'DRY_RUN': True,

# 4. Run the filter script
python3 nppes_filter_pcps.py
# This will show preview of what would be filtered

# 5. If preview looks good, disable dry-run and run for real
# Change 'DRY_RUN': True back to False
python3 nppes_filter_pcps.py
# Creates: FILTERED_pcps_CA_YYYYMMDD.csv

# 6. Import the CSV to Google Sheets manually (paste into new sheet)

# 7. Quick cleanup (optional but recommended):
#    a) Select all data rows → Quick Tools → Remove Duplicates
#       (hides duplicate rows, preserves data)
#    b) Select all OR specific rows → Quick Tools → Add Search Links
#       (makes office names clickable Google search links)

# 8. Manual verification (two options):

#    OPTION A - Click and verify:
#    - Click search link → Google opens
#    - If operational: leave row visible
#    - If closed/wrong: manually hide row
#    - When done: copy visible rows to All_Verified_Providers

#    OPTION B - Sidebar workflow:
#    - Select first data row
#    - Provider Tools → Manual Verification Sidebar
#    - Press L (load row), G (Google search), 1 (verified) or 2 (closed)
#    - Verified providers → All_Verified_Providers (row auto-hidden)
#    - Closed providers → Invalid/Inactive List (row auto-hidden)
#    - Automatically advances to next visible row
```

### Scenario 2: Fixing Capitalization in Existing Data

**Problem:** Office names are in ALL CAPS or have "M.d." instead of "MD".

```bash
# Option A: Fix in Google Sheets (for existing data)
1. Open your Google Sheet
2. Select the "Office Name" column (or any column with names)
3. Click menu: Misc. Tools → Fix Capitalization in Selection
4. Done! Names are now properly formatted

# Option B: Fix during import (for new data)
# Ensure Python script has this enabled:
#   'FIX_CAPITALIZATION': True,
# Re-run the filter script to regenerate CSVs with fixed names
```

### Scenario 3: Year-End Consolidation

**It's January 2026, and you need to:**
1. Archive all 2025 calling data
2. Prepare sheets for 2026 calling cycle

```bash
# WARNING: This is currently MANUAL (automation planned in TODO.md)

# Current manual steps:
1. Open your Google Sheet
2. Verify all "Successful Order" rows are in "New Orders 2025"
3. Verify all "Not interested" rows have notes and 0 in QTY
4. Run: Misc. Tools → (consolidation function - TO BE IMPLEMENTED)
5. Manually:
   - Add "2026 QTY" column
   - Duplicate sheets, rename old ones with "OLD 2025" prefix
   - Clear "New Orders 2025"
   - Clear colors and statuses (keep email notes)
   - Update STATS tab formulas

# See TODO.md for automation of these steps
```

### Scenario 4: Finding and Fixing Duplicates

**Problem:** Same provider appears multiple times with slightly different info.

```bash
# In Google Sheets:
1. Click menu: Misc. Tools → Validation & Debugging → Check for Duplicates
2. (Currently shows "Under development" - see TODO.md)

# Manual process currently:
1. Sort by phone number
2. Look for identical phone numbers
3. Check if same address
4. If duplicate: verify only one order was shipped (check New Orders sheet)
5. Merge the rows, keeping the most complete information
```

---

## 🔧 Configuration Files

### Python Script Configuration

**File:** `data/nppes/NPPES_Data_Dissemination_September_2025_V2/nppes_filter_pcps.py`

**Key settings to edit:**

```python
CONFIG = {
    # Which provider type to find
    'PROVIDER_TYPE': 'PCP',  # Options: 'PCP', 'OBGYN', 'BOTH'

    # Which states (2-letter codes)
    'TARGET_STATES': ['OK','OR','TN'],  # Change this!

    # Preview mode (no files created, just shows what would happen)
    'DRY_RUN': False,  # Set True to preview

    # Fix name capitalization issues
    'FIX_CAPITALIZATION': True,  # Keep this True!

    # Allow independent clinics (strict validation)
    'ORGANIZATION_HANDLING': {
        'INCLUDE_ORGANIZATIONS': True,  # Allow clinics
        # ... more settings below
    },

    # Optional name filtering (disabled by default)
    'NAME_PATTERN_FILTER': {
        'ENABLED': False,  # Set True to filter by name patterns
        'RISK_THRESHOLD': 'HIGH',  # How aggressive to filter
    }
}
```

### Google Apps Script Configuration

**File:** `scripts/provider-search/UniversalProviderSuite.js`

**Key settings:**

```javascript
const PROVIDER_CONFIG = {
  PROVIDER_TYPE: 'PCP',  // Options: 'PCP', 'OBGYN', 'SPECIALIST'
  TARGET_STATE: 'TX',     // 2-letter state code

  USE_UNIFIED_OUTPUT: true,  // All states in one sheet vs. separate

  SHEETS: {
    MASTER: function() {
      return `${PROVIDER_CONFIG.PROVIDER_TYPE}_${PROVIDER_CONFIG.TARGET_STATE}_import`;
    },
    VERIFIED: function() {
      return 'nppes_verified';  // or state-specific
    },
    // ... more sheet names
  }
}
```

**File:** `scripts/pcp-list/ToolboxSuite.js`

**Key settings:**

```javascript
function onEdit(e) {
  const statusColumn = 10; // Column J for "CALL STATUS"
  const targetSheetName = 'Working List 2025';  // ← Change this each year!

  const colorMappings = {
    'Successful Order': '#ffff00',    // Yellow
    'Requested Email': '#00ff00',     // Green
    'Potentially Invalid': '#ff0000', // Red
    'Voicemail/No Answer': '#ff00ff', // Fuchsia
    'Not interested': '#ffffff',      // White
    '': '#ffffff'                     // White for empty
  };
  // ...
}
```

---

## 🐛 Troubleshooting

### clasp errors

**Error:** "User has not enabled the Apps Script API"

**Solution:**
1. Go to: https://script.google.com/home/usersettings
2. Toggle ON: "Google Apps Script API"

**Error:** "Unable to read .clasp.json"

**Solution:**
You need to run `clasp clone <SCRIPT_ID>` first.

### Python script errors

**Error:** "No module named 'pandas'"

**Solution:**
```bash
pip install pandas
```

**Error:** "Input file not found: npidata_pfile_*.csv"

**Solution:**
1. Download NPPES data from: https://download.cms.gov/nppes/NPI_Files.html
2. Extract to `data/nppes/NPPES_Data_Dissemination_*/`
3. Verify the filename matches what's in CONFIG['INPUT_FILE']

### Google Sheets errors

**Note:** No API keys needed! This system uses 100% manual verification (no Google Places API).

---

## 🔐 Security & Privacy

### What data is stored where?

**Local computer (this folder):**
- Code files (tracked in git)
- NPPES bulk data (11 GB, NOT in git)
- Filtered CSVs (NOT in git)

**Google Sheets (cloud):**
- Provider lists
- Call history
- Order tracking

**NOT stored anywhere:**
- Patient data (we don't have it)
- Medical records (we don't collect it)
- Credit card info (brochures are free)

### Secrets & API Keys

**Never commit to git:**
- Google API keys
- `.clasp.json` files (contain project IDs)
- CSV files with provider data

**Already gitignored:**
- `*.csv`
- `.clasp.json`
- `*_secrets.*`
- `.env`

---

## 👥 Team & Contributors

This is a **volunteer-run nonprofit project** for the Canavan Foundation.

**Primary maintainer:** noa.gilbert@gmail.com

**Current team:**
- 3 volunteers making phone calls
- 1 volunteer handling shipping
- 1 volunteer (technical) maintaining this codebase

**When making changes:**
1. Test on a COPY of the sheet first (never on production)
2. Document what you changed
3. Update TODO.md with new tasks
4. Commit to git with clear message
5. Be cautious - data loss anxiety is real with volunteer-run projects!

---

## 📚 Key Concepts (For Developers)

### NPPES Database

**What is it?**
- National Plan and Provider Enumeration System
- Public database maintained by CMS (Centers for Medicare & Medicaid Services)
- Contains ~11 million healthcare providers in the US
- Updated monthly
- Each provider has an NPI (National Provider Identifier - unique 10-digit number)

**What data does it have?**
- Provider name, credentials
- Business address, phone
- Practice location
- Taxonomy codes (specialty classifications)
- Deactivation status

**Taxonomy Codes (Important!):**
- `207Q00000X` = Family Medicine physician
- `207R00000X` = Internal Medicine physician
- `208D00000X` = General Practice physician
- `363LF0000X` = Family Nurse Practitioner
- `207P00000X` = Emergency Medicine (we EXCLUDE this!)
- `208M00000X` = Hospitalist (we EXCLUDE this!)
- Many more...

We filter to ONLY family/primary care codes to avoid wasting time calling specialists.

### Google Apps Script

**What is it?**
- JavaScript-based scripting language for Google Workspace
- Runs on Google's servers (not your computer)
- Can interact with Google Sheets, Gmail, Calendar, etc.
- Has time-based triggers (run every X minutes)
- Has event-based triggers (run when sheet is edited)

**Why use it?**
- Volunteers are familiar with Google Sheets
- No server to maintain
- Free (within usage limits)
- Easy collaboration

**Limitations:**
- 6-minute execution time limit (we batch process to work around this)
- API call quotas
- No direct file system access (have to use Google Drive)

### clasp (Command Line Apps Script)

**What problem does it solve?**
- Editing code in the web-based Apps Script editor is painful
- No version control
- No proper code editor features
- Can't use git

**How it works:**
1. You edit `.js` and `.html` files locally (in VS Code, etc.)
2. Run `clasp push` to upload to Google
3. Run `clasp pull` to download from Google
4. `.clasp.json` file stores which Google project to sync with

### Git Workflow

**What's tracked:**
- All `.js` code files
- All `.html` UI files
- All `.md` documentation
- Python filter script

**What's NOT tracked:**
- CSV data files (too large)
- `.clasp.json` (contains project-specific IDs)
- API keys
- Secrets

---

## 🔗 External Resources

- **NPPES Data Downloads:** https://download.cms.gov/nppes/NPI_Files.html
- **NPI Registry API (Free!):** https://npiregistry.cms.hhs.gov/api-page
- **Google Apps Script Docs:** https://developers.google.com/apps-script
- **clasp Documentation:** https://github.com/google/clasp
- **Canavan Foundation:** https://www.canavanfoundation.org

---

## 📞 Support

**For technical issues:**
- Check TODO.md for known issues
- Check STRUCTURE.md for file locations
- Check docs/CLASP_SETUP.md for clasp help

**For questions about the workflow:**
- See "How to Use This System" section above
- See individual README files in scripts/provider-search/ and scripts/pcp-list/

**For emergencies:**
Contact: noa.gilbert@gmail.com

---

## 📝 MISC - Additional Context & Knowledge

### Multi-User Considerations

**Who uses these sheets:**
- 3 volunteers making phone calls (use Working List sheets directly)
- 1 technical maintainer (uses Misc. Tools menu and Apps Script)
- Volunteers DON'T use the Misc. Tools menu

**Important implications:**
- ⚠️ **Never use sheet-wide filters** - they affect all users simultaneously
- ✅ Per-user filter views are already configured - use those instead
- ✅ Color coding works for all users (onEdit triggers are global)
- ✅ Sidebar tools are individual (HTML Service isolates per user)

**Historical note:** Filter functions were removed from the Misc. Tools menu (commit ad88211) because they used `sheet.getFilter()` which creates sheet-wide filters that affected coworkers trying to work simultaneously.

---

### Recent Feature Additions (October 2025)

#### 🔧 Quick Fixes Menu
**Location:** Misc. Tools → Quick Fixes
**Added:** October 2025

Three new tools for common data cleanup tasks:

1. **✨ Fix Capitalization in Selection**
   - Handles: ALL CAPS → Title Case
   - Mc/Mac names: `MCDONALD` → `McDonald`
   - Apostrophes: `O'DONNELL` → `O'Donnell`
   - Credentials: `M.D.` → `MD`, `N.P.` → `NP`
   - Suffixes: `JR` → `Jr`, `SR` → `Sr`

2. **🏠 Standardize Addresses in Selection**
   - Applies USPS standard abbreviations
   - Street → St, Avenue → Ave, Boulevard → Blvd
   - Directional: North → N, Northeast → NE
   - Suite/Apartment: Ste., Apt. → Ste, Apt
   - Removes multiple spaces, fixes capitalization

3. **🔍 Check if in Invalid/Inactive List**
   - Uses fuzzy matching (40% phone + 40% name + 20% address)
   - Thresholds: ≥95% = EXACT, ≥80% = LIKELY
   - Shows confidence percentages
   - Displays invalid reason from Invalid/Inactive List
   - Safe: read-only, doesn't modify data

**Use case:** Select a range of cells (office names, addresses, etc.), run the tool, get cleaned data.

---

### Fuzzy Matching Algorithm Details

All fuzzy matching in the system uses consistent scoring:
- **40% weight:** Phone number (exact match after normalization)
- **40% weight:** Office name (uses Levenshtein distance)
- **20% weight:** Address (substring match)

**Thresholds:**
- ≥ 95% = "Exact match" (auto-fix QTY mismatches)
- ≥ 85% = Levenshtein similarity threshold (detects networks)
- ≥ 80% = "Likely match" (flag for manual review)

**Phone normalization:**
- Strips extensions: `555-1234 x123` → `5551234`
- Removes all non-digits: `(555) 123-4567` → `5551234567`
- Takes last 10 digits (handles +1 country code)

**Name normalization:**
- Removes: LLC, PC, PLLC, INC, Dr., Doctor
- Standardizes: & → and, + → and
- Strips punctuation (keeps hyphens and apostrophes)

**Empirically tested:** 85% threshold for network detection achieved 100% accuracy on real OBGYN data.

---

### Keyboard Shortcuts in Sidebars

**Apps Script HTML Service supports keyboard shortcuts!**

**How it works:**
- Keyboard events work WITHIN the sidebar HTML (`document.addEventListener('keydown')`)
- Do NOT work globally across Google Sheets (that's a platform limitation)
- Perfect for navigation within a focused UI tool

**Planned for Debug Repair Sidebar:**
- `n` = Next debug row
- `p` = Previous debug row
- `d` = Dismiss/downgrade issue
- `c` = Clear issue from Debug column

**Implementation pattern:**
```html
<script>
document.addEventListener('keydown', function(e) {
  if (e.key === 'n') moveToNextRow();
  if (e.key === 'p') moveToPreviousRow();
  // ... etc
});
</script>
```

---

### Debug/Issues Column Behavior

**Auto-created by EOY automation:**
- Named: "Debug/Issues"
- Background: Yellow (#fff2cc)
- **Automatically hidden** after creation
- To view: Right-click column headers → Unhide columns

**Format:**
```
⚠️ Yellow but NOT in New Orders
🔄 Duplicate phone (appears 2 times)
ℹ️ Same network (3 locations, 1 phone)
```

**Why hidden by default:** Prevents clutter for volunteers doing phone calls. Technical maintainer can unhide when needed for debugging.

---

### Network Detection Logic

**Problem:** Healthcare networks often have one central phone for multiple locations.

**Example:**
```
Row 1: Women's Health Center, 555-1234, 123 Main St, Austin
Row 2: Women's Health Center, 555-1234, 456 Oak Ave, Austin
Row 3: Women's Health Center, 555-1234, 789 Elm St, Round Rock
```

**Detection:**
- Same phone number across rows: ✓
- Same/similar name (≥85% similarity): ✓
- Different addresses: ✓
- **Conclusion:** Same network, NOT duplicates

**Auto-action:** Adds to Notes column:
```
womenshealthcenter network (~3);
```

**Format:** Lowercase name (no spaces) + "network" + location count + semicolon

**Why this format:** Consistent, searchable, doesn't conflict with other notes.

---

### OBGYN vs PCP Lists - Keeping in Sync

**Two separate Google Sheets:**
1. "OBGYN Working List 2025" (uses scripts/obgyn-list/)
2. "PCP List 2025" (uses scripts/pcp-list/)

**Code synchronization:**
- ToolboxSuite.js is identical in both folders
- When making changes: `cp scripts/obgyn-list/ToolboxSuite.js scripts/pcp-list/ToolboxSuite.js`
- Deploy separately: `clasp push` in each folder

**Why separate scripts:**
- Different Google Sheet = different Apps Script project
- Allows per-sheet API key storage (ScriptProperties is per-project)
- Enables independent testing (can test on PCP without affecting OBGYN)

---

### Invalid/Inactive List Sheet Structure

**Purpose:** Permanent list of providers who are closed, moved, or unreachable.

**Column structure documented in MASTER_SYSTEM_DOCUMENTATION.md:**
- Columns A-F: Office info (Name, Phone, Address, City, ST, Zip)
- Column G: INVALID/INACTIVE (reason)
- Column H: Notes

---

### Smart Column Detection

**Problem:** Different sheets have different column names.

**Solution:** Code finds columns by searching for keywords (case-insensitive).

**Examples:**
```javascript
// Finds "Office" OR "Practice" OR "Name"
const officeCol = headers.findIndex(h =>
  h && (h.toLowerCase().includes('office') ||
        h.toLowerCase().includes('practice') ||
        h.toLowerCase().includes('name'))
);

// Finds "Phone" OR "Number"
const phoneCol = headers.findIndex(h =>
  h && (h.toLowerCase().includes('phone') ||
        h.toLowerCase().includes('number'))
);

// Finds most recent QTY (2025 > 2024 > 2023)
const qtyCol = findMostRecentQtyColumn(headers);
```

**Why this matters:** You can rename columns without breaking the code (within reason).

**Works:** "Office Name" → "Practice" → "Office" → "Name"
**Breaks:** "Provider" (doesn't contain any of the search terms)

---

### Deployment Checklist

When making changes to ToolboxSuite.js:

1. ✅ Edit locally in `scripts/obgyn-list/ToolboxSuite.js`
2. ✅ Test logic/syntax locally
3. ✅ Sync to PCP: `cp scripts/obgyn-list/ToolboxSuite.js scripts/pcp-list/ToolboxSuite.js`
4. ✅ Commit to git: `git add -A && git commit -m "Description"`
5. ✅ Push to OBGYN sheet: `cd scripts/obgyn-list && clasp push`
6. ✅ Push to PCP sheet: `cd scripts/pcp-list && clasp push`
7. ✅ Test in Google Sheets (open both sheets, refresh, try the feature)
8. ✅ Document changes in TODO.md

**Common mistake:** Forgetting step 3 (sync to PCP) or step 6 (push to PCP sheet).

---

### Taxonomy Codes Quick Reference

**Family Medicine:**
- 207Q00000X - Family Medicine
- 208D00000X - General Practice
- 363LF0000X - Nurse Practitioner, Family

**OBGYN:**
- 207V00000X - Obstetrics & Gynecology
- 207VX0000X - Obstetrics
- 207VX0201X - Gynecology

**Internal Medicine (PCPs):**
- 207R00000X - Internal Medicine
- 207RA0000X - Adolescent Medicine
- 207RG0100X - Geriatric Medicine

**What we EXCLUDE:**
- 208M00000X - Hospitalist (not outpatient)
- 207P00000X - Emergency Medicine (not primary care)
- 208U00000X - Clinical Pharmacology (not prescribers)
- Anything with "Hospital" in organization name

---

### Color Coding & Status System

**Trigger:** onEdit on column J (Call Status) in "Working List 2025"

| Color | Status | Hex Code | Meaning |
|-------|--------|----------|---------|
| Yellow | Successful Order | #FFFF00 | Must exist in New Orders sheet |
| Green | Requested Email | #00FF00 | Awaiting email response |
| Red | Potentially Invalid | #FF0000 | Closed/disconnected/wrong number |
| Fuschia | Voicemail/No Answer | #FF00FF | Leave QTY empty (not 0) |
| White | Not interested | #FFFFFF | Auto-sets QTY=0, adds note |

**Implementation:** `scripts/pcp-list/ToolboxSuite.js` and `scripts/obgyn-list/ToolboxSuite.js` (onEdit function)

---

### Manual Verification Workflow

**NO AUTOMATED VERIFICATION:** This system uses 100% manual verification (Google Places API was too expensive/risky).

**Current approach:**
- NPPES taxonomy filtering (99.91% reduction: 9.1M → 8K)
- Manual Google search verification using keyboard-driven UI
- Duplicate detection across multiple criteria (phone, address, office name)

**Why manual?**
- Google Places API billing is unpredictable ($346 in one month!)
- Enterprise SKU triggered accidentally (only 1,000 free calls)
- Manual verification is free and gives better control
- Keyboard shortcuts make it fast (5-10 sec/provider)

**Keyboard shortcuts in sidebar:**
- `L` - Load selected row
- `G` - Open Google search
- `1` - Mark as Active
- `2` - Mark as Closed
- `S` - Skip to next

**Speed:** 300-500 providers/hour with experienced reviewer

---

### Common Gotchas

1. **Column J is hardcoded:** onEdit trigger in ToolboxSuite.js checks `statusColumn = 10`. Update if Call Status moves.

2. **Sheet name is hardcoded:** onEdit checks `targetSheetName = 'Working List 2025'`. Must update yearly.

3. **Semicolon separators in Notes:** Code splits on `;` for deduplication. Format: `note1; note2; note3`

4. **Network notation format:** Lowercase, no spaces, ends with semicolon: `womenshealthcenter network (~3);`

5. **Debug column is 1-based:** Apps Script uses 1-based indexing. `sheet.getRange(row, col)` where col=1 is column A.

6. **clasp push requires refresh:** After `clasp push`, refresh Google Sheets (Ctrl+R) to see changes.

---

### Version Numbers Explained

**Python script:** `nppes_filter_pcps.py` v3.0
**Provider verification:** `UniversalProviderSuite.js` v8.0
**Working List tools:** `ToolboxSuite.js` v10.0

**Why different versions?**
- Each component evolves independently
- v8.0 added API safeguards (major feature)
- v10.0 added EOY automation (major feature)

**Versioning scheme:** MAJOR.MINOR
- MAJOR: Breaking changes or significant new features
- MINOR: Bug fixes, small improvements (not used consistently)

---

### Contact

**Primary maintainer:** noa.gilbert@gmail.com
