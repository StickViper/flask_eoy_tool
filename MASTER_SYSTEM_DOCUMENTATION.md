# JGDC Healthcare Provider Outreach System - Master Documentation

**Organization:** The Canavan Foundation (nonprofit)
**Mission:** Distribute educational brochures about Canavan Disease to healthcare providers
**System Status:** Production-ready with comprehensive automation
**Last Updated:** 2025-10-07

---

## TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Complete Tech Stack](#complete-tech-stack)
3. [Data Pipeline](#data-pipeline)
4. [Critical Configuration](#critical-configuration)
5. [API Management & Limits](#api-management--limits)
6. [EOY Automation Suite](#eoy-automation-suite)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Sheet Structures](#sheet-structures)
9. [Workflow Procedures](#workflow-procedures)
10. [Maintenance Schedule](#maintenance-schedule)

---

## SYSTEM OVERVIEW

### What This System Does

**Input:** 9.1M healthcare providers from NPPES database (CMS)
**Output:** Verified, callable lists of PCPs and OBGYNs who accept brochure orders

**End-to-End Process:**
1. **Filter** 9.1M records → ~10K providers per state (Python script)
2. **Smart Sample** 10K → 800-1,280 for verification (based on actual 25% success rate)
3. **Verify** via Google Places API → 200-300 operational providers per state
4. **Import** to Google Sheets Working Lists
5. **Call** providers, track status with color coding
6. **Fulfill** orders from "New Orders" sheet
7. **EOY Reset** for next year's campaign

### Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **NPPES Database Size** | 9,129,558 records | Updated quarterly from CMS |
| **Filter Efficiency** | 99.99% reduction | 9.1M → ~9K per state |
| **Verification Success Rate** | 25% (actual) | Was guessed at 70%, reality is much lower |
| **API Calls Per Provider** | 1 call | No retries currently |
| **Monthly API Limit** | 3,000 calls (free tier) | $17/month for overage |
| **Processing Time** | ~3 min filter, ~30 min verify | For 1,280 providers |

---

## COMPLETE TECH STACK

### Core Technologies

**Python Environment:**
- Python 3.x
- pandas (data processing)
- Script: `nppes_filter_pcps.py` v3.0

**Google Cloud:**
- Google Sheets (data storage, UI)
- Google Apps Script (automation, event handling)
- Google Places API (New) - verification
- API Key storage: ScriptProperties (per-script persistent storage)

**Version Control:**
- Git (local repository)
- clasp (Google Apps Script CLI - syncs .js files to cloud)
- GitHub (potential future remote)

### File Structure

```
JGDC/
├── scripts/
│   ├── provider-search/          # Verification automation
│   │   ├── UniversalProviderSuite.js  (v8.0 - verification engine)
│   │   ├── QuickStartWizard.html
│   │   ├── VerificationSidebar.html
│   │   ├── appsscript.json
│   │   ├── .clasp.json            (gitignored - contains script ID)
│   │   └── README.md
│   ├── pcp-list/                  # PCP Working List automation
│   │   ├── ToolboxSuite.js        (v10.0 - EOY automation)
│   │   ├── appsscript.json
│   │   └── .clasp.json
│   └── obgyn-list/                # OBGYN Working List automation
│       ├── ToolboxSuite.js        (v10.0 - same as PCP)
│       ├── appsscript.json
│       └── .clasp.json
├── data/
│   └── nppes/
│       └── NPPES_Data_Dissemination_September_2025_V2/
│           ├── npidata_pfile_20050523-20250907.csv  (9.1M records, ~3GB)
│           ├── nppes_filter_pcps.py  (v3.0)
│           ├── FILTERED_obgyns_TX_20251007.csv  (800 providers)
│           ├── FILTERED_obgyns_WA_20251007.csv  (160 providers)
│           ├── FILTERED_obgyns_CO_20251007.csv  (160 providers)
│           ├── FILTERED_obgyns_PA_20251007.csv  (160 providers)
│           ├── FILTERED_obgyns_ALL_20251007.csv  (1,280 combined)
│           └── EXCLUDED_FILTERED_obgyns_20251007.csv  (audit trail)
├── docs/
│   └── CLASP_SETUP.md
├── TODO.md
├── OBGYN_CLEANUP_CHECKLIST.md
├── SESSION_SUMMARY_20251003.md
└── MASTER_SYSTEM_DOCUMENTATION.md  (this file)
```

---

## DATA PIPELINE

### Stage 1: NPPES Filtering (Python)

**Script:** `nppes_filter_pcps.py` v3.0
**Input:** 9,129,558 NPPES records
**Output:** 1,280 sampled providers (for OBGYN campaign)

**Configuration Variables:**
```python
PROVIDER_TYPE = 'OBGYN'  # or 'PCP' or 'BOTH'
TARGET_STATES = ['TX', 'WA', 'CO', 'PA']
STATE_SAMPLE_LIMITS = {
    'TX': 800,   # Targets 200 verified (25% rate)
    'WA': 160,   # Targets 40 verified
    'CO': 160,   # Targets 40 verified
    'PA': 160,   # Targets 40 verified
}
DRY_RUN = False  # Set True to preview without saving
FIX_CAPITALIZATION = True
```

**Filtering Pipeline:**
1. **Load:** Reads 9.1M rows in chunks (low memory usage)
2. **Deactivated:** Removes 336,027 deactivated NPIs
3. **Taxonomy:** Strict codes only (OBGYN: 207V*, PCP: 208D*, 363L*, etc.)
   - Result: 73,858 OBGYNs nationally
4. **State:** Filters to target states only
   - Result: 12,101 in TX/WA/CO/PA
5. **Organizations:** Validates independent clinics (94% rejection rate)
   - Keeps: "Family Medicine Clinic", "Women's Health Center"
   - Rejects: Hospitals, imaging centers, labs, health systems
   - Result: 9,281 providers
6. **Required Fields:** Must have phone + address
7. **Deduplication:** Prefers individuals over clinics at same location
   - Result: 9,223 unique providers
8. **Smart Sampling:** Random selection based on target verified counts
   - TX: 4,315 → 800 sampled
   - WA: 1,276 → 160 sampled
   - CO: 1,117 → 160 sampled
   - PA: 2,515 → 160 sampled
   - **Total: 1,280 providers to verify**

**Capitalization Fixes (5 types):**
1. ALL CAPS → Title Case: `MARY SMITH MD` → `Mary Smith MD`
2. Mc/Mac names: `MCDONALD` → `McDonald`, `MACGREGOR` → `MacGregor`
3. Apostrophes: `O'DONNELL` → `O'Donnell`
4. Credentials: `M.D.` → `MD`, `D.O.` → `DO`
5. Suffixes: `JR` → `Jr`, `SR` → `Sr`, `III` → `III`

**Output Files:**
- `FILTERED_obgyns_[STATE]_[DATE].csv` - Per-state files
- `FILTERED_obgyns_ALL_[DATE].csv` - Combined file
- `EXCLUDED_FILTERED_obgyns_[DATE].csv` - Audit trail (523 MB)

---

### Stage 2: Google Places API Verification

**Script:** `UniversalProviderSuite.js` v8.0
**Input:** Filtered CSVs from Stage 1
**Output:** Verified, Needs Review, Errors sheets

**How It Works:**
1. Import CSV to Google Sheet ("OBGYN Verification Input" or similar)
2. Configure via menu: Provider Type, Target State, API Key
3. Script processes in batches of 25 providers
4. For each provider:
   - Builds search query: `"Office Name" "Address" "City" "State"`
   - Calls Google Places API (Text Search)
   - Scores confidence based on name match, address match, phone match
   - **STATE FILTER (NEW):** Skips rows where State != TARGET_STATE
5. Routes to 3 output sheets based on confidence:
   - **Verified:** Confidence ≥ 0.85, operational, has phone
   - **Needs Review:** 0.50 ≤ Confidence < 0.85
   - **Errors:** Confidence < 0.50 or API error

**Actual Success Rates (480 providers tested):**
- ✅ Verified: 119 (25%)
- ⚠️ Needs Review: 154 (32%)
- ❌ Errors: 207 (43% - mostly "Failed verification")

**Common Failure Reasons:**
- Provider moved/closed
- Phone disconnected
- Not in Google Places database
- Address changed
- Name mismatch (maiden name, practice name change)

---

### Stage 3: Working List Management

**Sheets:** "Working List 2025" (PCP and OBGYN have separate sheets)
**Script:** `ToolboxSuite.js` v10.0

**Column Structure:**
```
A: Practice/Office Name
B: Number/Phone
C: Address
D: Town/City
E: State
F: Zip
G: 2023 QTY
H: 2024 QTY
I: 2025 QTY
J: CALL STATUS  (column 10 - triggers color coding)
K: Notes
```

**Color Coding (Event-Driven via onEdit):**
| Status | Color | Hex | Auto-Actions |
|--------|-------|-----|--------------|
| Successful Order | Yellow | #FFFF00 | None |
| Requested Email | Green | #00FF00 | None |
| Potentially Invalid | Red | #FF0000 | None |
| Voicemail/No Answer | Fuschia | #FF00FF | None |
| Not interested | White | #FFFFFF | Sets QTY=0, adds "not interested" to Notes |

**Event Trigger:** When column J (Call Status) is edited, entire row changes color.

---

### Stage 4: Order Fulfillment

**Sheet:** "New Orders 2025"
**Column Structure:**
```
A: Practice
B: Number
C: Address
D: Town
E: State
F: Zip
G: 2023 QTY
H: 2024 QTY
I: 2025 QTY
J: CALL STATUS
K: Notes
```

**Process:**
1. Caller marks provider "Successful Order" (yellow) in Working List
2. Manually copy row to "New Orders 2025" sheet
3. EOY automation validates all yellow rows exist in New Orders
4. Orders fulfilled and shipped
5. QTY tracked year-over-year

---

## CRITICAL CONFIGURATION

### Google Apps Script Configuration

**UniversalProviderSuite.js Settings:**
```javascript
DEFAULT_CONFIG = {
  PROVIDER_TYPE: 'PCP',           // or 'OBGYN'
  TARGET_STATE: 'TX',             // 2-letter code
  USE_UNIFIED_OUTPUT: true,
  MAX_BATCHES_PER_RUN: 0,         // 0 = unlimited
  BATCH_SIZE: 25,
  MAX_EXECUTION_TIME: 270000,     // 4.5 min (Apps Script limit: 6 min)
  NAME_SIMILARITY_THRESHOLD: 0.65,
  HIGH_CONFIDENCE_THRESHOLD: 0.85,
  REQUIRE_PHONE_FOR_OPERATIONAL: true,
  CACHE_DURATION: 21600,          // 6 hours
  FIX_CAPITALIZATION: true,
  API_CALL_LIMIT: 3000,           // Hard stop
  API_WARNING_THRESHOLD: 2800     // Warning prompt
}
```

**ToolboxSuite.js Settings:**
```javascript
// onEdit defaults
targetSheetName = 'Working List 2025'
statusColumn = 10     // Column J
qtyColumn = 9         // Column I (most recent year)
notesColumn = 11      // Column K

// EOY automation uses smart column detection:
// - Finds columns by name (not hardcoded position)
// - Handles "Practice" OR "Office" OR "Name"
// - Handles "Number" OR "Phone"
// - Finds most recent QTY column (2025 > 2024 > 2023)
```

---

## API MANAGEMENT & LIMITS

### Google Places API (New)

**Endpoint:** `https://places.googleapis.com/v1/places:searchText`
**Method:** POST
**Authentication:** `X-Goog-Api-Key` header

**Pricing:**
- **Free tier:** 3,000 calls/month
- **Overage:** $17.00 per 1,000 calls
- **Our usage:** 1,280 calls for current OBGYN campaign (43% of limit)

**API Key Storage:**
- Stored in: `PropertiesService.getScriptProperties()`
- Key name: `apiKey`
- Scope: Per-script (Provider Search script only)
- Security: Not visible in sheet, only in Apps Script editor

**Usage Tracking:**
- **Persistent counter:** `apiCallCount` in ScriptProperties
- **Incremented:** Every successful API call
- **Displayed:** Menu → API Usage (shows count, %, remaining, status emoji)
- **Reset:** Manual via menu (only reset at start of new billing month)

**Safety Mechanisms:**
1. **Pre-flight check:** Before starting verification, checks current usage
   - Blocks if ≥ 3000 calls
   - Warns if ≥ 2800 calls
2. **In-flight check:** During batch processing, checks before each batch
   - Stops immediately if limit reached
3. **User visibility:** Shows usage in startup confirmation dialog

**State Filtering (NEW - Critical):**
```javascript
// In processBatch(), BEFORE API call:
if (config.TARGET_STATE && state &&
    state.toString().trim().toUpperCase() !== config.TARGET_STATE.toUpperCase()) {
  logMessage(`Skipping row ${actualRow}: State '${state}' != target '${config.TARGET_STATE}'`);
  return;  // Skip this row, don't waste API call
}
```

**Why This Matters:** Previous version processed ALL states in CSV, wasting API calls. Now only processes matching state.

---

## EOY AUTOMATION SUITE

### Overview

**Location:** Misc. Tools → End-of-Year Workflow
**Status:** Code complete, needs real-world testing
**Purpose:** Automate 80% of year-end cleanup work

### Six Automation Steps

#### Step 1: Audit Working List
**What it does:** Runs all 4 validations in dry-run mode, reports totals

**Output:**
```
Found 87 total issues:
• Yellow rows not in New Orders: 12
• Not Interested missing notes: 8
• Not Interested wrong QTY: 5
• Duplicate entries: 42
• Status reviews needed: 20
```

**Creates:** Hidden "Debug/Issues" column with row-by-row flags

---

#### Step 2: Validate Yellow → New Orders
**What it does:** Cross-references Working List yellow rows with New Orders sheet

**Checks:**
- Every yellow row has matching phone in New Orders
- QTY matches between sheets

**Flags:**
- `⚠️ Yellow but NOT in New Orders` - Order was never copied
- `⚠️ QTY mismatch: Working=5, Orders=3` - Data inconsistency

**Edge Cases Handled:**
- Phone format variations (normalizes to digits only)
- Extensions (strips "x123" before matching)
- Multiple QTY columns (finds most recent year)

---

#### Step 3: Enforce Not Interested Rules
**What it does:** Auto-fixes rows with "Not interested" status

**Auto-fixes:**
1. Adds "not interested" to Notes if missing
2. Sets QTY to 0 if not already

**Example:**
```
Before:
Status: Not interested
Notes: Called 3x, no response
QTY: 5

After:
Status: Not interested
Notes: Called 3x, no response; not interested
QTY: 0
```

**Why:** Ensures "not interested" is clearly documented and no orders are placed

---

#### Step 4: Detect Duplicates
**What it does:** Finds duplicate phone numbers and addresses

**Smart Detection:**
- Same name + same phone + different addresses = **Network** (auto-notes)
- Same phone + different names = Duplicate (flag for review)
- Same address + different names = Duplicate (flag for review)

**Network Example:**
```
Row 1: Women's Health Center, 555-1234, 123 Main St, Austin
Row 2: Women's Health Center, 555-1234, 456 Oak Ave, Austin

Action: Adds to Notes column: "Same network - multiple locations"
```

**Duplicate Example:**
```
Row 1: Dr. Smith, 555-1234, 123 Main St
Row 2: Smith Family Practice, 555-1234, 123 Main St

Flags: 🔄 Duplicate phone (appears 2 times)
User must: Review manually and merge or keep both
```

**NEVER auto-merges** - too risky for data loss

---

#### Step 5: Review Status-Based Issues
**What it does:** Categorizes providers needing follow-up

**Categories:**
- 🔴 **Red (Potentially Invalid):** Move to Invalid/Inactive list or re-verify
- 💜 **Fuschia (Voicemail/No Answer):** Triple follow-up, leave QTY empty (not 0)
- 🟢 **Green (Requested Email):** Keep if recent, mark "not interested" if old
- ⚪ **Empty (Uncalled):** Leave as-is for next campaign

**Output:** Report with counts and guidance (does NOT auto-fix)

---

#### Step 6: Run Full EOY Automation
**What it does:** Runs steps 1-5 sequentially

**Process:**
1. Shows confirmation dialog
2. Runs full audit (Step 1)
3. Validates yellow/orders (Step 2) - dry run
4. Enforces not interested (Step 3) - **LIVE, makes changes**
5. Detects duplicates (Step 4) - dry run
6. Reviews status (Step 5) - dry run
7. Shows summary report

---

### Manual Steps Still Required

These are too complex/risky to automate:

**Step 7: Add New Year QTY Column**
- Insert column after "2025 QTY"
- Name it "2026 QTY"
- Formula update required

**Step 8: Duplicate & Rename Sheets**
- Duplicate "Working List 2025" → "Working List 2026"
- Rename old: "Working List 2025" → "OLD Working List 2025"
- Same for "New Orders 2025"

**Step 9: Clear Data for New Year**
- New Orders: Delete all rows (keep header)
- Working List: Clear colors, clear Call Status, preserve email Notes

**Step 10: Update STATS Tab**
- Update formulas to reference new sheet names
- Extend yearly stats columns
- Update "current round" month

**Step 11: Update Dashboard Links**
- Update IMPORTRANGE formulas
- Adjust 22x11 chunks for new year
- Test all links work

---

### Hidden Debug/Issues Column

**How it works:**
- Created automatically by `getOrCreateDebugColumn()`
- Named: "Debug/Issues"
- Background: Yellow (#fff2cc)
- **Auto-hidden** after creation
- To view: Right-click column headers → Unhide columns

**Content Format:**
```
⚠️ Yellow but NOT in New Orders
⚠️ QTY mismatch: Working=5, Orders=3
⚠️ Missing "not interested" in Notes; QTY should be 0
🔄 Duplicate phone (appears 2 times)
🔄 Same network (3 locations, 1 phone)
```

**To clear:** Delete cell content after fixing issue

---

## COMMON ISSUES & SOLUTIONS

### 1. "All states processed instead of just target state"

**Symptom:** Verification runs on TX, WA, CO, PA when you only want WA
**Cause:** Old code didn't filter by state before API calls
**Fix:** Updated `UniversalProviderSuite.js` line 396-400 (state filter added)
**Status:** ✅ Fixed in v8.0

---

### 2. "API limit reached unexpectedly"

**Symptom:** Processing stops at 2,846 calls instead of 3,000
**Cause:** Previous runs didn't reset counter
**Check:** Menu → API Usage (see current count)
**Fix:** Reset counter at start of new billing month
**Prevention:** Pre-flight check now warns at 2,800

---

### 3. "Verification success rate much lower than expected"

**Expected:** 70% verified
**Actual:** 25% verified
**Causes:**
- Providers closed/moved since NPPES update
- Phone numbers disconnected
- Not in Google Places database
- Address mismatches

**Solutions:**
- Use "Needs Review" queue (32% of results)
- Increase initial sample size (now using 1,280 instead of 480)
- Accept lower yield

---

### 4. "Yellow rows not matching New Orders"

**Symptom:** EOY validation finds many yellow rows "not in New Orders"
**Common Causes:**
1. **Phone format mismatch:** (555) 123-4567 vs 5551234567
   - Fixed: normalizePhone() strips all non-digits
2. **Copy-paste error:** Worker forgot to copy to New Orders
   - Solution: Manual review each flagged row
3. **Extension included:** 555-123-4567 x123
   - Fixed: Extensions stripped before matching

---

### 5. "Duplicate detection false positives"

**Symptom:** Same network flagged as duplicates
**Cause:** Multiple locations with one central phone
**Solution:** Network detection logic added (v10.0)
**Behavior now:**
- Same name + phone + diff addresses = "Same network" (auto-noted)
- Different names + same phone = "Duplicate" (manual review)

---

### 6. "onEdit color coding not working"

**Check:**
1. Is Call Status in column J (column 10)?
   - If not, update `statusColumn` variable
2. Is sheet named "Working List 2025"?
   - If not, update `targetSheetName` variable
3. Did you refresh the page after pushing code?
   - Refresh required after `clasp push`

**Test:** Type "Successful Order" in any Call Status cell → row should turn yellow

---

### 7. "Menu doesn't appear after clasp push"

**Steps:**
1. Refresh Google Sheets page (Ctrl+R)
2. Wait 30 seconds (Apps Script needs to load)
3. Check Apps Script editor for errors
4. Verify `clasp push` succeeded (check output)
5. Try `clasp open` to check which script you're editing

---

### 8. "Can't find New Orders sheet"

**Error:** `Cannot find "New Orders 2025" sheet`
**Cause:** Sheet named differently
**Fix (NEW):** Smart sheet detection tries:
1. "New Orders 2025"
2. "New Orders"
3. "Orders 2025"
4. Any sheet with "new" AND "order"
5. Any sheet with "order"

**Status:** ✅ Fixed - no longer hardcoded

---

## SHEET STRUCTURES

### Working List Sheet

**Name:** "Working List 2025" (PCP) or "OBGYN Working List 2025"
**Purpose:** Track all calling activity year-over-year

**Columns:**
| Col | Name | Type | Example | Notes |
|-----|------|------|---------|-------|
| A | Practice | Text | Women's Health Center | Can be "Office Name" or "Practice" |
| B | Number | Text | (512) 555-1234 | Can be "Phone" or "Number" |
| C | Address | Text | 123 Main St Suite 200 | Full street address |
| D | Town | Text | Austin | Can be "City" or "Town" |
| E | State | Text | TX | 2-letter code |
| F | Zip | Text | 78701 | 5-digit |
| G | 2023 QTY | Number | 5 | Previous year orders |
| H | 2024 QTY | Number | 10 | Previous year orders |
| I | 2025 QTY | Number | 15 | Current year orders |
| J | CALL STATUS | Dropdown | Successful Order | Triggers color coding |
| K | Notes | Text | Email sent 10/3 | Freeform notes |

**Validation (Column J):**
- Successful Order
- Requested Email
- Potentially Invalid
- Voicemail/No Answer
- Not interested
- (empty)

**Row Colors:**
- Yellow (#FFFF00) = Successful Order
- Green (#00FF00) = Requested Email
- Red (#FF0000) = Potentially Invalid
- Fuschia (#FF00FF) = Voicemail/No Answer
- White (#FFFFFF) = Not interested or empty

---

### New Orders Sheet

**Name:** "New Orders 2025"
**Purpose:** Track orders to be fulfilled

**Columns:** Same as Working List (Practice, Number, Address, Town, State, Zip, QTYs, Call Status, Notes)

**Rules:**
- Only contains providers with successful orders (yellow rows)
- QTY must match Working List
- All rows should be findable by phone in Working List

---

### Invalid/Inactive List

**Name:** "Invalid/Inactive List"
**Purpose:** Providers who are confirmed closed, moved, or unreachable

**Columns:**
| Col | Name | Type | Example |
|-----|------|------|---------|
| A | Name | Text | Dr. Smith |
| B | Phone | Text | 555-1234 |
| C | Address | Text | 123 Main St |
| D | City | Text | Austin |
| E | ST | Text | TX |
| F | Zip | Text | 78701 |
| G | INVALID/INACTIVE | Text | Closed - retired |
| H | Notes | Text | Called 10/3, phone disconnected |

---

### Verification Output Sheets

Created by `UniversalProviderSuite.js`:

**Sheet 1: nppes_[type]_[state]_verified**
- Providers that passed verification (confidence ≥ 0.85)
- Columns: Office Name, Phone, Address, City, State, ZIP, API corrections, Place ID, Confidence Score, Date

**Sheet 2: nppes_[type]_[state]_review**
- Medium confidence (0.50-0.85), needs manual review
- Columns: Same as verified + Priority score

**Sheet 3: nppes_[type]_[state]_errors**
- Failed verification or API errors
- Columns: Office Name, Address, City, State, ZIP, Error Notes

---

## WORKFLOW PROCEDURES

### New Campaign Setup (e.g., OBGYN 2025)

**Prerequisites:**
- Latest NPPES data downloaded
- pandas installed (`pip install pandas`)
- Google Places API key configured
- Target states decided

**Steps:**

1. **Update Python Config** (5 min)
```python
# In nppes_filter_pcps.py
PROVIDER_TYPE = 'OBGYN'
TARGET_STATES = ['TX', 'WA', 'CO', 'PA']
STATE_SAMPLE_LIMITS = {
    'TX': 800,    # 200 target ÷ 0.25 success rate
    'WA': 160,    # 40 target ÷ 0.25
    'CO': 160,
    'PA': 160,
}
DRY_RUN = False
OUTPUT_PREFIX = 'FILTERED_obgyns'
```

2. **Run Filtering** (3 min)
```bash
cd data/nppes/NPPES_Data_Dissemination_September_2025_V2
python nppes_filter_pcps.py
```

3. **Verify Output** (1 min)
- Check `FILTERED_obgyns_ALL_[DATE].csv` exists
- Verify row counts match sample limits
- Spot-check a few rows for data quality

4. **Import to Google Sheets** (5 min)
- Create new sheet: "OBGYN Verification Input"
- File → Import → Upload
- Select `FILTERED_obgyns_ALL_[DATE].csv`
- Import location: Replace current sheet
- Verify column headers match

5. **Configure Verification** (2 min)
- Menu → Provider Verification → Quick Start Wizard
- Provider Type: OBGYN
- Target State: TX (or whichever you're doing first)
- API Key: (enter key)
- Click "Start Processing"

6. **Monitor Verification** (~30 min for 1,280 providers)
- Don't close the sheet
- Check Menu → API Usage periodically
- Wait for completion dialog

7. **Review Results** (10 min)
- Check "nppes_obgyn_TX_verified" sheet
- Count rows (should be ~25% of input)
- Spot-check a few for quality
- Review "errors" sheet for patterns

8. **Repeat for Other States** (if running multiple)
- Change Target State in config
- Re-run verification (only processes that state due to filter)

9. **Import to Working List** (manual, 15 min)
- Copy verified rows to "OBGYN Working List 2025"
- Format as needed
- Add to calling queue

**Total Time:** ~1.5 hours for full multi-state campaign

---

### EOY Cleanup Procedure

**When:** End of calendar year, before starting next year's campaign
**Time:** 3-4 hours
**Reference:** See `OBGYN_CLEANUP_CHECKLIST.md` for detailed step-by-step

**High-Level Steps:**

1. **Connect automation** (if not already connected)
   - Get Script ID from Google Sheet
   - `clasp clone` to local
   - Copy ToolboxSuite.js
   - `clasp push`

2. **Run audit** (15 min)
   - Misc. Tools → EOY Workflow → Audit Working List
   - Record issue counts

3. **Fix yellow/orders issues** (30-60 min)
   - Review flagged rows
   - Fix copy-paste errors
   - Reconcile QTY mismatches

4. **Fix "not interested" issues** (20-30 min)
   - Run auto-fix
   - Handle edge cases

5. **Review duplicates** (30-60 min)
   - Decide: merge, keep both, or mark as network
   - Update Notes

6. **Review status issues** (30-45 min)
   - Red: Move to invalid list or re-verify
   - Fuschia: Schedule triple follow-up
   - Green: Follow up or mark not interested
   - Empty: Leave for next year

7. **Final validation** (15 min)
   - Run audit again
   - Should show 0 or near-0 issues

8. **Clean New Orders** (20 min)
   - Check for duplicates
   - Validate all have yellow match

9. **Manual EOY tasks** (60 min)
   - Add 2026 QTY column
   - Duplicate sheets
   - Rename old sheets
   - Clear data
   - Update STATS tab
   - Update dashboard links

**Total: 3-4 hours** (down from 8-10 hours manual)

---

### Monthly Maintenance

**First Monday of Month** (30 min):
1. Check API usage: Menu → API Usage
2. Reset counter if new billing month
3. Document actual usage for planning

**Ongoing** (as needed):
1. Check for specialist contamination in lists
2. Validate STATS tab accuracy
3. Review and respond to worker questions

---

### Quarterly Maintenance

**When NPPES releases new data** (1 hour):
1. Download latest NPPES data from CMS
2. Update `INPUT_FILE` path in Python config
3. Re-run filtering for active campaigns
4. Compare new vs old results
5. Update Working Lists with new providers

**Inactive Provider Review** (2 hours):
1. Review red (Potentially Invalid) providers
2. Confirm still inactive
3. Move confirmed to Invalid/Inactive List
4. Free up space in Working Lists

---

## MAINTENANCE SCHEDULE

### Daily
- Monitor worker questions/issues
- Check for data entry errors

### Weekly
- Review calling progress
- Check order fulfillment status

### Monthly
- Reset API counter (if new billing cycle)
- Review API usage trends
- Check STATS tab accuracy

### Quarterly
- Download new NPPES data
- Re-verify closed/inactive providers
- Clean up Invalid/Inactive List
- Review success rate trends

### Annually
- Run full EOY workflow
- Archive old year sheets
- Update year references in code
- Review and optimize entire pipeline
- Consider success rate adjustments

---

## APPENDIX

### Useful Commands

**Python:**
```bash
# Install dependencies
pip install pandas

# Run filtering (preview)
python nppes_filter_pcps.py  # (with DRY_RUN=True)

# Run filtering (production)
python nppes_filter_pcps.py  # (with DRY_RUN=False)
```

**clasp (Apps Script CLI):**
```bash
# One-time setup
npm install -g @google/clasp
clasp login

# Clone existing script
cd scripts/provider-search
clasp clone <SCRIPT_ID>

# Push local changes to Google
clasp push

# Pull Google changes to local
clasp pull

# Open in browser
clasp open

# Check status
clasp status
```

**Git:**
```bash
# Stage all changes
git add -A

# Commit with message
git commit -m "Your message here"

# Check status
git status

# View recent commits
git log --oneline -10
```

---

### Contact & Support

**For Issues:**
- Check this documentation first
- Review `TODO.md` for known issues
- Check `OBGYN_CLEANUP_CHECKLIST.md` for procedures
- Review session summaries in root directory

**For Code Changes:**
- Edit locally
- Test thoroughly
- `clasp push` to deploy
- `git commit` to save
- Document in TODO.md

---

### Version History

**v1.0 (2023):** Initial manual process
**v2.0 (2024):** Python filtering added, basic Apps Script automation
**v3.0 (2025-09):** Smart sampling, organization validation, capitalization fixes
**v8.0 (2025-10):** API usage safeguards, state filtering, enhanced tracking
**v10.0 (2025-10):** Complete EOY automation suite, network detection, smart column detection

---

**Last Updated:** 2025-10-07
**Next Review:** 2026-01-01 (or when major issues arise)
