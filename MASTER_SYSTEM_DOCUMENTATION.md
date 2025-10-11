# JGDC Healthcare Provider Outreach - Technical Reference

**Organization:** The Canavan Foundation (nonprofit)
**System Status:** Production with known bugs (see TODO.md)
**For Procedures:** See `OBGYN_CLEANUP_CHECKLIST.md`
**For Bugs:** See `TODO.md` section 0
**For Debug Sidebar:** See `DEBUG_REPAIR_SYSTEM_SPEC.md`

---

## SYSTEM OVERVIEW

**Input:** 9.1M healthcare providers from NPPES database
**Output:** Verified, callable lists of PCPs and OBGYNs

**Pipeline:**
1. Filter 9.1M → ~10K/state (Python)
2. Sample ~1K-3K for verification (25% success rate)
3. Verify via Google Places API
4. Import to Google Sheets
5. Call providers, track with color coding
6. Fulfill orders
7. EOY cleanup (automated + manual steps)

### Key Metrics
- **Filter efficiency:** 99.99% reduction
- **Verification success:** 25% (not 70% as guessed)
- **API limit:** 3,000 calls/month (free tier)
- **Processing time:** 3 min filter + 30 min verify

---

## TECH STACK

**Python:** pandas, nppes_filter_pcps.py v3.0
**Google Cloud:** Sheets, Apps Script, Places API (New)
**Version Control:** Git + clasp

**Scripts:**
- `UniversalProviderSuite.js` v8.0 - API verification
- `ToolboxSuite.js` v10.0 - EOY automation

---

## DATA PIPELINE

### Stage 1: Python Filtering

**Script:** `data/nppes/.../nppes_filter_pcps.py`

**Configuration Example:**
```python
PROVIDER_TYPE = 'PCP'  # or 'OBGYN'
TARGET_STATES = ['FL']
STATE_SAMPLE_LIMITS = {'FL': 3000}
DRY_RUN = False
FIX_CAPITALIZATION = True
```

**Filtering Steps:**
1. Load 9.1M rows in chunks
2. Exclude deactivated NPIs
3. Filter by taxonomy codes (strict whitelist)
4. Filter by state
5. Validate organizations (94% rejection - only independent clinics)
6. Require phone + address
7. Deduplicate (prefer individuals over clinics)
8. Smart sample to target count

**Capitalization Fixes:**
- ALL CAPS → Title Case
- Mc/Mac names: McDonald, MacGregor
- Apostrophes: O'Donnell
- Credentials: M.D. → MD
- Suffixes: JR → Jr

**Output:** `FILTERED_[type]_[STATE]_[DATE].csv`

---

### Stage 2: Google Places Verification

**Script:** `scripts/provider-search/UniversalProviderSuite.js`

**Process:**
1. Import CSV to "Verification Input" sheet
2. Configure: Provider Type, Target State, API Key
3. Processes in batches of 25
4. Calls Google Places API with query: "Office Name" "Address" "City" "State"
5. Routes to 3 sheets:
   - **Verified** (≥85% confidence): ~25% of input
   - **Needs Review** (50-85%): ~32%
   - **Errors** (<50%): ~43%

**Common failures:** Closed, moved, phone disconnected, not in Google Places

**⚠️ KNOWN BUG:** No specialty verification - can pass dermatologists/dentists as PCPs (only checks name/phone/operational)

**CRITICAL:** State filter (v8.0) - only processes matching TARGET_STATE to avoid wasting API calls

**See README.md MISC section for detailed technical notes**

---

### Stage 3: Working List Management

**Sheet:** "Working List 2025" (separate for PCP/OBGYN)
**Script:** `scripts/[type]-list/ToolboxSuite.js`

**Column Structure:**
```
A: Office Name
B: Phone Number
C: Address
D: City
E: State
F: Zip
G-I: QTY (2023/2024/2025)
J: CALL STATUS (column 10 - triggers onEdit)
K: Notes
```

**Color Coding (onEdit trigger on column J):**

See README.md MISC > Color Coding & Status System for full table

---

### Stage 4: Order Fulfillment

**Sheet:** "New Orders 2025"

**CRITICAL DETAIL:** New Orders contains **Office Name + Address ONLY** (NO phone numbers copied)

**Process:**
1. Mark "Successful Order" (yellow) in Working List
2. Manually copy to New Orders
3. ⚠️ EOY validation currently BROKEN (uses phone matching but no phone in New Orders)
4. Orders fulfilled externally
5. QTY tracked year-over-year

---

## CRITICAL CONFIGURATION

### UniversalProviderSuite.js
```javascript
DEFAULT_CONFIG = {
  PROVIDER_TYPE: 'PCP',  // or 'OBGYN'
  TARGET_STATE: 'TX',
  BATCH_SIZE: 25,
  HIGH_CONFIDENCE_THRESHOLD: 0.85,
  API_CALL_LIMIT: 3000,
  API_WARNING_THRESHOLD: 2800
}
```

### ToolboxSuite.js
```javascript
targetSheetName = 'Working List 2025'  // UPDATE ANNUALLY
statusColumn = 10     // Column J
qtyColumn = 9         // Column I
notesColumn = 11      // Column K
```

**Smart column detection:** Finds columns by name (handles "Practice" OR "Office", "Number" OR "Phone", etc.)

---

## API MANAGEMENT

**Google Places API (New)**
- **Endpoint:** `https://places.googleapis.com/v1/places:searchText`
- **Free tier:** 3,000 calls/month
- **Overage:** $17/1,000 calls
- **Storage:** ScriptProperties (`apiKey`, `apiCallCount`)

**Usage Tracking:**
- Persistent counter in ScriptProperties
- View: Menu → API Usage
- Reset: Manual (start of billing month only)

**Safety:**
- Pre-flight check: Blocks if ≥3000, warns if ≥2800
- In-flight check: Stops before each batch if limit reached

---

## EOY AUTOMATION

**See `OBGYN_CLEANUP_CHECKLIST.md` for detailed procedures**

**Location:** Misc. Tools → End-of-Year Workflow

**6 Automated Steps:**
1. **Audit** - Counts issues, creates Debug/Issues column
2. **Validate Yellow** - ⚠️ BROKEN (uses phone but New Orders has no phone)
3. **Not Interested** - Auto-adds note, sets QTY=0
4. **Duplicates** - Flags duplicates, detects networks
5. **Status Review** - Categorizes Red/Fuschia/Green/Empty
6. **Full EOY** - Runs 1-5 sequentially

**Still Manual:**
- Add new QTY column
- Duplicate/rename sheets
- Clear data for new year
- Update STATS tab
- Update dashboard links

**Debug/Issues Column:**
- Auto-created, auto-hidden (yellow background)
- Format: `⚠️ Yellow but NOT in New Orders`, `🔄 Duplicate phone (appears 2 times)`
- Unhide: Right-click column headers → Unhide

---

## SHEET STRUCTURES

### Working List
| Col | Name | Type | Notes |
|-----|------|------|-------|
| A | Practice | Text | "Office Name" or "Practice" |
| B | Number | Text | "Phone" or "Number" |
| C | Address | Text | Full street address |
| D | Town | Text | "City" or "Town" |
| E | State | Text | 2-letter code |
| F | Zip | Text | 5-digit |
| G-I | QTY | Number | Year columns (2023/2024/2025) |
| J | CALL STATUS | Dropdown | Triggers color coding |
| K | Notes | Text | Freeform, semicolon-separated |

### New Orders
**Same structure as Working List**
**CRITICAL:** Contains Office Name + Address only (NO phone copied)

### Invalid/Inactive List
| Col | Name | Type |
|-----|------|------|
| A-F | Office info | Text |
| G | INVALID/INACTIVE | Text (reason) |
| H | Notes | Text |

---

## WORKFLOW QUICK REF

### New Campaign Setup
1. Update Python config (PROVIDER_TYPE, TARGET_STATES, SAMPLE_LIMITS)
2. Run `python nppes_filter_pcps.py` (3 min)
3. Import CSV to Google Sheets
4. Configure verification (Provider Type, State, API Key)
5. Run verification (~30 min per 1,000 providers)
6. Import verified to Working List

**Total:** ~1.5 hours

### EOY Cleanup
**See `OBGYN_CLEANUP_CHECKLIST.md` for full procedure**

1. Backup sheet
2. Run automation (Misc. Tools → EOY Workflow)
3. Fix flagged issues
4. Manual tasks (add QTY column, duplicate sheets, clear data, update formulas)

**Total:** 2-4 hours (was 8-10 hours before automation)

---

## COMMON ISSUES

**See `OBGYN_CLEANUP_CHECKLIST.md` Troubleshooting section**

### Quick Fixes
- **Menu missing:** Refresh (Ctrl+R), wait 30s
- **onEdit not working:** Check sheet name = "Working List 2025", Call Status in column J
- **API limit hit:** Menu → API Usage, reset at start of month
- **Verification low success:** Expected 25% (not 70%), increase sample size
- **Yellow validation failing:** ⚠️ Known bug - Step 2 uses phone but New Orders has no phone

---

## MAINTENANCE

**Daily:** Monitor questions, check data entry
**Weekly:** Review calling progress
**Monthly:** Reset API counter, check STATS
**Quarterly:** Download new NPPES data, clean Invalid List
**Annually:** Full EOY workflow, update year references

---

## USEFUL COMMANDS

**Python:**
```bash
pip install pandas
python nppes_filter_pcps.py
```

**clasp:**
```bash
clasp clone <SCRIPT_ID>
clasp push
clasp pull
clasp open
```

**Git:**
```bash
git add -A
git commit -m "message"
git status
```

---

## VERSION HISTORY

- **v1.0 (2023):** Manual process
- **v2.0 (2024):** Python filtering + basic Apps Script
- **v3.0 (2025-09):** Smart sampling, org validation, cap fixes
- **v8.0 (2025-10):** API safeguards, state filtering
- **v10.0 (2025-10):** EOY automation (with known bugs)

---

**Last Updated:** 2025-10-11
**Critical Bugs:** See TODO.md section 0
**Procedures:** See OBGYN_CLEANUP_CHECKLIST.md
