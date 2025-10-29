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
- **Filter efficiency:** 99.99% reduction (9.1M → 8K providers)
- **Manual verification speed:** 300-500 providers/hour with keyboard shortcuts
- **Cost:** $0 (no API, 100% manual)
- **Processing time:** 3 min filter + manual verification as needed

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

### Stage 2: Manual Verification

**Script:** `scripts/provider-search/UniversalProviderSuite.js` (v9.0 - Manual Only)

**Process:**
1. Import CSV to any sheet in Provider Search workbook
2. Add Google search links: Quick Tools → Add Search Links
3. Manual verification using sidebar:
   - Load row (L), Google search (G), mark status (1/2), skip (S)
   - Auto-saves reviewer name and date
4. Routes to 2 sheets:
   - **All_Verified_Providers**: Operational providers
   - **Manual_Review_Queue**: Needs more research

**Common rejections:** Closed, moved, wrong specialty, duplicate

**NO GOOGLE PLACES API:** Switched to 100% manual (API was too expensive/risky)
- Free, unlimited verification
- Full control over decisions
- 300-500 providers/hour with keyboard shortcuts

**Tools:**
- Universal duplicate removal (works on any sheet)
- Copy verified from queue (hides rows, preserves audit trail)
- Capitalization fixer

**See README.md MISC section for keyboard shortcut details**

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

## MANUAL VERIFICATION WORKFLOW

**NO API - 100% Manual (Google Places API removed Oct 2025)**

**Why Manual?**
- Google Places API billing is unpredictable
- Hit $346.86 in one month (Enterprise SKU triggered accidentally)
- Free tier too risky for solo dev nonprofit project
- Manual verification gives full control and is free

**Keyboard-Driven UI:**
- **L** - Load selected row
- **G** - Open Google search in new tab
- **1** - Mark as Active/Operational
- **2** - Mark as Closed
- **S** - Skip to next row
- Auto-saves reviewer name and timestamp

**Speed:** 5-10 seconds per provider = 300-500 providers/hour

**Tools:**
- Google search link generator (free, no API)
- Universal duplicate removal (phone, address, office name)
- Copy verified from queue (preserves audit trail)
- Capitalization fixer

**Alternative: NPI Registry API (Future)**
- Free, unlimited API calls
- Can check NPI status, address changes, deactivations
- Cannot verify operational status or patient acceptance
- See TODO.md for implementation plan

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
# System Properties Documentation

**Purpose:** Documents all PropertiesService properties used by Google Apps Script code
**Last Updated:** October 18, 2025
**Applies To:** UniversalProviderSuite.js, ToolboxSuite.js

---

## Overview

Google Apps Script uses `PropertiesService.getScriptProperties()` to store persistent configuration and state data. These properties persist across script executions and are scoped per Google Apps Script project.

**Key Principle:** Each Google Sheet has its own Apps Script project, so properties are NOT shared between OBGYN and PCP sheets.

---

## Properties Used by UniversalProviderSuite.js

### `PLACES_API_KEY`

- **Type:** String
- **Purpose:** Google Places API (New) authentication key
- **Set By:** Menu → API Configuration → Enter API Key
- **Read By:** `UniversalProviderSuite.js:228` (`getApiKey()`)
- **Default:** None (required - verification will fail if missing)
- **Reset Procedure:**
  1. Menu → API Configuration → Enter API Key
  2. Paste new key
  3. Click OK
- **Shared Between Sheets:** ❌ No - each sheet needs its own key
- **Security:** Stored in ScriptProperties (not visible to sheet users, only Apps Script editor)

**Code References:**
```javascript
// Set: Line 217
PropertiesService.getScriptProperties().setProperty('PLACES_API_KEY', apiKey);

// Get: Line 228
return PropertiesService.getScriptProperties().getProperty('PLACES_API_KEY');
```

---

### `targetStates`

- **Type:** String (comma-separated state codes)
- **Purpose:** Stores which states to process during verification
- **Set By:** Quick Start Wizard or `saveConfig()` function
- **Read By:** `UniversalProviderSuite.js:28` (`getConfig()`)
- **Default:** Falls back to `DEFAULT_CONFIG.TARGET_STATES` if not set
- **Format:** `"TX,CA,FL"` or single state `"TX"`
- **Reset Procedure:**
  1. Menu → Quick Start Wizard
  2. Select target states
  3. Complete wizard
- **Shared Between Sheets:** ❌ No

**Code References:**
```javascript
// Set: Line 47-50
const props = PropertiesService.getScriptProperties();
props.setProperty('targetStates', configData.targetStates);

// Get: Line 28
const targetStatesStr = props.getProperty('targetStates') || DEFAULT_CONFIG.TARGET_STATES;
```

---

### `apiCallCount`

- **Type:** String (stored as number string)
- **Purpose:** Tracks total Google Places API calls this billing month
- **Set By:** `incrementApiCallCount()` after each API call
- **Read By:** `UniversalProviderSuite.js:1076` (`getApiCallCount()`)
- **Default:** `"0"` (if not set)
- **Reset Procedure:**
  1. Menu → API Usage → Reset Counter
  2. Confirm reset
  3. **ONLY reset at start of billing month**
- **Shared Between Sheets:** ❌ No - each sheet tracks separately
- **Critical:** Hard limit at 3,000 calls/month (free tier)

**Code References:**
```javascript
// Get: Line 1076-1078
function getApiCallCount() {
  const props = PropertiesService.getScriptProperties();
  return parseInt(props.getProperty('apiCallCount') || '0');
}

// Increment: Line 1081-1084
function incrementApiCallCount(count) {
  const props = PropertiesService.getScriptProperties();
  const current = getApiCallCount();
  props.setProperty('apiCallCount', (current + count).toString());
}

// Reset: Line 1104
PropertiesService.getScriptProperties().setProperty('apiCallCount', '0');
```

---

### `progress_[PROVIDER_TYPE]_[TARGET_STATES]`

- **Type:** String (row number)
- **Purpose:** Tracks verification progress to resume after timeout
- **Set By:** `saveProcessingProgress(row)` during verification
- **Read By:** `UniversalProviderSuite.js:850` (`getProcessingProgress()`)
- **Default:** `"1"` (start from row 1)
- **Format:** `"progress_PCP_TX"` or `"progress_OBGYN_CA,CO,PA"`
- **Reset Procedure:** Automatically reset to `"1"` when verification completes
- **Shared Between Sheets:** ❌ No
- **Purpose:** Handles 6-minute execution timeout (resumes where it left off)

**Code References:**
```javascript
// Get: Line 850-856
function getProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  return parseInt(props.getProperty(key) || '1');
}

// Set: Line 860-864
function saveProcessingProgress(row) {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  props.setProperty(key, row.toString());
}

// Reset: Line 867-871
function resetProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  props.setProperty(key, '1');
}
```

---

## Properties Used by ToolboxSuite.js

**None currently.** ToolboxSuite.js does NOT use PropertiesService.

All configuration is hardcoded or detected from sheet structure (column names, sheet names).

---

## Common Operations

### View All Properties (Manual)

1. Open Google Sheet
2. Extensions → Apps Script
3. Run this in Apps Script editor:

```javascript
function listAllProperties() {
  const props = PropertiesService.getScriptProperties().getProperties();
  Logger.log(JSON.stringify(props, null, 2));
}
```

4. View → Logs (Ctrl+Enter)

---

### Delete All Properties (危険 DANGER)

**⚠️ WARNING:** Only do this if you want to completely reset the script to factory defaults.

```javascript
function deleteAllProperties() {
  PropertiesService.getScriptProperties().deleteAllProperties();
  Logger.log('All properties deleted');
}
```

**Consequences:**
- API key lost (must re-enter)
- API call count reset to 0 (billing tracking lost)
- Verification progress lost
- Configuration lost (states, provider type)

---

## Migration Notes

### Moving Between Sheets

**Problem:** Copying OBGYN code to PCP sheet doesn't copy properties

**Solution:** After `clasp push` to new sheet, must manually reconfigure:
1. Menu → API Configuration → Enter API Key (paste same key)
2. Menu → Quick Start Wizard → Configure states/provider type
3. Menu → API Usage → Verify counter is 0 (or set manually if needed)

---

### Backup Properties

**Before major changes:**

```javascript
function backupProperties() {
  const props = PropertiesService.getScriptProperties().getProperties();
  Logger.log('BACKUP:');
  Logger.log(JSON.stringify(props, null, 2));
  // Copy from Logs and save to local file
}
```

**Restore:**

```javascript
function restoreProperties() {
  const backup = {
    "PLACES_API_KEY": "your-key-here",
    "apiCallCount": "1234",
    "targetStates": "TX,CA"
  };

  const props = PropertiesService.getScriptProperties();
  Object.keys(backup).forEach(key => {
    props.setProperty(key, backup[key]);
  });

  Logger.log('Properties restored');
}
```

---

## Security Best Practices

### API Key Security

✅ **DO:**
- Store in ScriptProperties (isolated per project)
- Use environment-specific keys (dev vs prod)
- Restrict key to specific APIs (Places API only)
- Set usage quotas in Google Cloud Console

❌ **DON'T:**
- Hardcode in .js files (visible in git)
- Share same key across unrelated projects
- Give key broader permissions than needed
- Commit API keys to version control

---

### Access Control

**Who can see ScriptProperties:**
- ✅ Anyone with "Edit" access to Apps Script project
- ❌ Sheet viewers (read-only)
- ❌ Sheet editors (unless also Apps Script editors)

**Implications:**
- Volunteers making phone calls: ❌ Cannot see API key
- Technical maintainer: ✅ Can see API key via Apps Script editor

---

## Troubleshooting

### "API key missing" error

**Symptom:** Verification fails with "No API key configured"

**Fix:**
```javascript
// Check if key exists
const key = PropertiesService.getScriptProperties().getProperty('PLACES_API_KEY');
Logger.log('API Key exists: ' + (key ? 'YES' : 'NO'));

// If NO: Menu → API Configuration → Enter API Key
```

---

### API counter seems wrong

**Symptom:** Counter shows 500 but you expect 200

**Possible Causes:**
1. Multiple users running verification simultaneously (both increment counter)
2. Failed runs still increment counter (API calls were made even if verification failed)
3. Testing/development runs not accounted for

**Fix:**
```javascript
// Check current value
const count = PropertiesService.getScriptProperties().getProperty('apiCallCount');
Logger.log('Current count: ' + count);

// Manually set if needed (ONLY if you're certain)
PropertiesService.getScriptProperties().setProperty('apiCallCount', '200');
```

---

### Progress counter stuck

**Symptom:** Re-running verification starts from middle of sheet, not beginning

**Fix:**
```javascript
// Check all progress keys
const props = PropertiesService.getScriptProperties().getProperties();
Object.keys(props).forEach(key => {
  if (key.startsWith('progress_')) {
    Logger.log(key + ': ' + props[key]);
  }
});

// Reset specific progress
PropertiesService.getScriptProperties().setProperty('progress_PCP_TX', '1');

// Or use menu: (Progress is auto-reset when verification completes)
```

---

## Future Enhancements

**Potential additions (not yet implemented):**

- `lastVerificationDate` - Track when verification last ran
- `verificationSuccessRate` - Track historical success rate
- `apiResetDate` - Auto-reset counter on billing cycle
- `debugMode` - Enable verbose logging
- `batchSize` - Configurable batch size for processing

**If adding new properties:**
1. Document in this file
2. Add getter/setter functions
3. Update backup/restore procedures
4. Test migration between sheets

---

**Last Updated:** October 18, 2025
**Maintained By:** Technical user (AI agents should update when adding new properties)
# EOY vs. Reset Phase - Critical Distinction

**Purpose:** Clarify the difference between End-of-Year cleanup and Reset for next year
**Last Updated:** October 18, 2025
**Audience:** Technical user, AI agents working on EOY automation

---

## TL;DR

- **EOY** = Data cleanup and validation of current year (2025)
- **Reset** = Prepare sheets for next year's campaign (2026)
- **Key:** EOY runs while still adding to 2025 QTY column
- **Reset** happens later (separate phase)

---

## EOY (End-of-Year) Phase

### What It Is

**Data cleanup and validation** of the current year's calling campaign while it's still active.

### When It Runs

- ASAP for OBGYN (October 2025)
- Can run multiple times during a campaign
- **Critical:** 2025 calling continues AFTER EOY runs
- Users will keep adding to "2025 QTY" column in "Working List 2025" sheet

### What It Does

1. **Validate Yellow Rows** → Verify "Successful Order" rows exist in "New Orders 2025"
2. **Fix Not Interested** → Ensure QTY=0 and "not interested" in Notes
3. **Detect Duplicates** → Flag duplicate phone/address, identify networks
4. **Categorize Status Issues** → Review Red/Fuschia/Green/Empty rows
5. **Populate Debug/Issues Column** → Hidden column with warnings for manual review
6. **Audit Data Quality** → Count issues, show summary

### What It Does NOT Do

- ❌ Add "2026 QTY" column
- ❌ Duplicate sheets with "OLD" prefix
- ❌ Clear New Orders sheet
- ❌ Clear colors/statuses
- ❌ Update STATS formulas
- ❌ Change year references

### Expected State After EOY

```
Working List 2025:
- All data still present (2023/2024/2025 QTY columns)
- Debug/Issues column created (auto-hidden)
- Issues flagged for review
- Colors/statuses UNCHANGED
- Volunteers continue calling and adding 2025 orders
```

### Who Uses It

**Technical user only** - volunteers never see or use EOY automation

### Tools/Menu Location

Menu: `Misc. Tools → End-of-Year Workflow`

Steps:
- Step 1: Audit Working List
- Step 2: Validate Yellow → New Orders
- Step 3: Enforce Not Interested Rules
- Step 4: Detect Duplicates
- Step 5: Review Status-Based Issues
- Step 6: Run All (1-5 sequentially)

---

## Reset Phase

### What It Is

**Transition to next year's campaign** - structural changes to sheets and formulas.

### When It Runs

- After 2025 calling is completely finished (likely January-February 2026)
- **Only once** per year
- After all 2025 orders are fulfilled

### What It Does

1. **Add 2026 QTY Column**
   - Insert new column after "2025 QTY"
   - Name it "2026 QTY"
   - Leave empty initially

2. **Duplicate and Rename Sheets**
   - Duplicate "Working List 2025" → Rename old to "OLD Working List 2025"
   - Rename duplicate to "Working List 2026"
   - Same for "New Orders 2025" → "OLD New Orders 2025" + "New Orders 2026"

3. **Clear Data for 2026**
   - New Orders 2026: Delete all rows (keep header only)
   - Working List 2026:
     - Clear colors (Format → Clear formatting)
     - Clear Call Status column (column J)
     - **PRESERVE email Notes** (don't clear Notes column)
     - Keep office info (Name, Phone, Address, etc.)
     - Keep historical QTY (2023/2024/2025 columns)

4. **Update STATS Tab**
   - Update sheet name references in formulas
   - Extend yearly stats columns (add 2026 row)
   - Update "current round" month reference

5. **Update Dashboard Links**
   - Update IMPORTRANGE formulas to point to "Working List 2026"
   - Adjust cell ranges for new year
   - Test all links

### What It Does NOT Involve

- ❌ Data validation (that's EOY phase)
- ❌ Duplicate detection (that's EOY phase)
- ❌ Yellow row verification (that's EOY phase)

### Expected State After Reset

```
Working List 2026:
- Office info intact (Name, Phone, Address, City, State, Zip)
- Historical QTY intact (2023/2024/2025 columns)
- Email Notes preserved
- Call Status cleared (ready for new calls)
- Colors cleared (all white)
- 2026 QTY empty (ready for new orders)

Working List 2025 (OLD):
- Archived as "OLD Working List 2025"
- Complete historical record
- No changes made

New Orders 2026:
- Empty (header only)
- Ready for first 2026 orders

STATS Tab:
- Formulas point to 2026 sheets
- Historical data preserved (2023/2024/2025)
```

### Who Uses It

**Technical user** - complex manual process (not yet automated)

### Current Status

**NOT AUTOMATED** - Too complex/risky for initial automation

**Manual procedure documented in:** OBGYN_CLEANUP_CHECKLIST.md (Phase 9)

---

## Workflow Timeline

```
Oct 2025                  Dec 2025                 Jan 2026
  │                         │                        │
  ├─[EOY Phase 1]──────────►│                        │
  │  Validate data          │                        │
  │  Flag issues            │                        │
  │  Continue calling       │                        │
  │                         │                        │
  ├─[EOY Phase 2]──────────►│                        │
  │  (can run multiple      │                        │
  │   times as needed)      │                        │
  │                         │                        │
  │  Still adding to        │                        │
  │  2025 QTY column        │                        │
  │                         │                        │
  │                         ├─[Calling Ends]────────►│
  │                         │                        │
  │                         │                        ├─[Reset Phase]
  │                         │                        │  Structural changes
  │                         │                        │  Prepare for 2026
  │                         │                        │
  │                         │                        ├─[2026 Calling Starts]
```

---

## Key Differences Table

| Aspect | EOY Phase | Reset Phase |
|--------|-----------|-------------|
| **Purpose** | Data cleanup/validation | Structural transition |
| **Timing** | During active campaign | After campaign ends |
| **Frequency** | Multiple times (as needed) | Once per year |
| **Automation** | Partially automated | Manual (complex) |
| **Data Changes** | Flags issues, minor fixes | Clears statuses, adds columns |
| **Year Focus** | Current year (2025) | Next year (2026) |
| **Calling Status** | Continues during/after | Stopped before reset |
| **2025 QTY** | Still being added to | No longer modified |
| **Sheets Modified** | Working List 2025, New Orders 2025 | Creates 2026 sheets, archives 2025 |
| **Formulas** | Unchanged | Updated to reference 2026 |

---

## Why This Distinction Matters

### For AI Agents

**Common mistake:** Assuming EOY means "prepare for next year"

**Reality:** EOY = clean current year's data while campaign is still active

**Implication:** Don't auto-clear data, don't add new year columns, don't rename sheets

### For Planning

**EOY can run now** (ASAP for OBGYN) because:
- Doesn't disrupt ongoing calling
- Flags issues for review
- Improves data quality for final orders
- Can run multiple times (iterative cleanup)

**Reset must wait** because:
- Requires all 2025 calling to be complete
- Destructive changes (clearing statuses)
- Can't easily reverse
- One-time operation

### For Bug Fixes

**When fixing EOY automation:**
- Focus: Data validation, duplicate detection, issue flagging
- Test: Run multiple times on same data (should be idempotent)
- Safety: Never delete rows, never clear historical data

**When considering Reset automation (future):**
- Focus: Sheet duplication, column insertion, formula updates
- Test: On copy of production (highly destructive)
- Safety: Require backup, confirmation dialog, rollback plan

---

## Current Implementation Status

### EOY Phase

**Automated (Menu Items):**
- ✅ Step 1: Audit (counts issues) - ⚠️ Bug: doesn't populate Debug column
- ✅ Step 3: Not Interested (auto-fixes)
- ✅ Step 4: Duplicates (flags) - ⚠️ Bug: network notation wrong format
- ✅ Step 5: Status Review (categorizes)
- ❌ Step 2: Yellow validation - **BROKEN** (phone matching, but New Orders has no phone)

**Status:** Partial - critical bugs block OBGYN EOY (fixing ASAP)

### Reset Phase

**Automated:**
- ❌ None - entirely manual

**Documented:**
- ✅ Manual procedure in OBGYN_CLEANUP_CHECKLIST.md (Phase 9)

**Future Work:**
- Low priority (once per year)
- High complexity (formula updates risky)
- Good candidate for future automation (after EOY proven)

---

## Examples

### Example 1: October 2025 OBGYN Campaign

**Situation:**
- OBGYN Working List 2025 has 710 active contacts
- 230 yellow (orders), 117 fuschia (callback), 265 uncalled
- Campaign started in September, ongoing through December
- Technical user wants to clean up data quality issues

**Correct Action:** **Run EOY Phase**
- Validates 230 yellow rows against New Orders
- Detects duplicates (if any)
- Flags status issues
- Creates Debug/Issues column for review
- **Calling continues** - volunteers keep working

**Incorrect Action:** ~~Run Reset Phase~~
- Would clear statuses (lose progress!)
- Would create 2026 sheets (premature)
- Would disrupt ongoing campaign

---

### Example 2: January 2026 PCP Campaign

**Situation:**
- PCP List 2025 has 1,874 active contacts
- All calling finished in December 2025
- 633 orders fulfilled, all shipped
- Ready to start 2026 campaign

**Correct Action:** **Run Reset Phase**
- Archive "Working List 2025" as "OLD Working List 2025"
- Create "Working List 2026" (cleared statuses, preserved data)
- Add 2026 QTY column
- Update STATS formulas
- Ready for 2026 calling

**Incorrect Action:** ~~Run EOY Phase again~~
- Data already cleaned (EOY ran in December)
- Won't transition to 2026
- Calling can't start (still using 2025 sheet)

---

## FAQ

### Q: Can I run EOY multiple times?

**A:** Yes! EOY is designed to be idempotent. Run it whenever you want to validate data quality. Useful during active campaigns to catch issues early.

### Q: When should I run Reset?

**A:** Only after 100% of current year calling is finished AND all orders are fulfilled. Typically January-February of next year.

### Q: What if I run Reset too early?

**A:** Big problem! You'll lose all current year statuses and can't easily recover. Volunteers lose progress. Always finish calling first.

### Q: Can I automate Reset phase?

**A:** Theoretically yes, but very risky. Formula updates can break dashboards. Start with EOY automation, tackle Reset later.

### Q: Does EOY clear the Notes column?

**A:** No! EOY only *adds* to Notes (e.g., network notation). Reset phase preserves email notes but clears statuses.

### Q: How do I know if calling is "finished"?

**A:** Check STATS sheet:
- % uncalled < 5%
- % unresolved (callback) < 10%
- All orders fulfilled and shipped
- Volunteers confirm done

---

**Remember:** EOY = clean while active | Reset = transition when done

---

**Last Updated:** October 18, 2025
# Google Maps Platform Quota Changes - March 2025

**Last Updated:** October 18, 2025
**Applies To:** UniversalProviderSuite.js (Google Places API usage)
**Impact:** FREE TIER INCREASED (good news!)

---

## TL;DR

✅ **GOOD NEWS:** Free tier INCREASED from ~2,857 calls/month to 10,000 calls/month
✅ This project's current 3,000 call limit is now well under the free tier
⚠️ Need to understand SKU categories to verify we're using "Essentials" tier

---

## What Changed on March 1, 2025

### Old System (Before March 1, 2025)

**Monthly Credit Model:**
- $200 USD monthly recurring credit
- Applied across all Google Maps Platform services
- Text Search (Places API New): $17 per 1,000 calls
- Effective free calls: ~2,857 per month ($200 / $17 * 1000 ≈ 11,765 calls, but shared across all services)

### New System (After March 1, 2025)

**Per-SKU Free Usage Model:**
- Free usage varies by SKU category
- **Essentials SKUs:** 10,000 free monthly calls
- **Pro SKUs:** 5,000 free monthly calls
- **Enterprise SKUs:** 1,000 free monthly calls
- Each service tracked separately (not pooled)

---

## Places API (New) - What We Use

### Current Implementation

**API:** Places API (New) - Text Search
**Endpoint:** `https://places.googleapis.com/v1/places:searchText`
**File:** `scripts/provider-search/UniversalProviderSuite.js`
**Usage Pattern:** Batch verification of NPPES provider data

### SKU Category (Needs Verification)

**Question:** Which SKU category does Text Search fall under?

**Likely:** Essentials (10,000 free calls)
- Text Search is basic functionality
- Closest to legacy Places API Text Search
- Blog post mentions "up to 10,000 monthly free calls per product"

**Need to Confirm:** Check Google Cloud Console → Billing → SKUs

### Current vs. New Limits

| Aspect | Old System | New System (Essentials) | Impact |
|--------|------------|------------------------|--------|
| Free Tier | ~2,857 calls* | 10,000 calls | +250% increase |
| This Project's Limit | 3,000 calls | 3,000 calls | Now fully free! |
| Overage Cost | $17 / 1,000 | $17 / 1,000** | Same |
| Volume Discounts | 100K+ usage | 5M+ usage | Better scaling |

*Approximate, shared across services
**Assumes Essentials tier, verify in console

---

## Impact on This Project

### Current Usage Pattern

**Typical Campaigns:**
- OBGYN (Oct 2025): ~465 expected calls (TX, WA, CO, PA)
- PCP (Oct 2025): ~300 expected calls (NM, UT, NE, AL)
- **Total:** ~765 calls for current campaigns

**Hard Limit:**
- Self-imposed: 3,000 calls/month
- Warning threshold: 2,800 calls
- Safety margin: 200 calls

### With New Quota (10,000 free/month)

**New Reality:**
- Current usage (~765 calls): 7.7% of free tier
- Self-imposed limit (3,000): 30% of free tier
- **Recommendation:** Consider raising limit to 5,000-8,000 calls

**Benefits:**
- More aggressive filtering (larger sample sizes)
- Multiple state campaigns per month without worry
- Buffer for testing/development

---

## Action Items

### Immediate (October 2025)

- [ ] Verify SKU category in Google Cloud Console
  1. Go to: https://console.cloud.google.com
  2. Billing → Reports → Filter by "Places API (New)"
  3. Check SKU name (should mention "Essentials", "Pro", or "Enterprise")
  4. Confirm free tier amount matches expectation (10,000)

- [ ] Update API usage tracking code (if needed)
  - Current hard limit: 3,000 calls
  - Consider: Increase to 8,000 calls (80% of free tier)
  - Update warning threshold: 7,500 calls

- [ ] Document actual SKU category
  - Update this file with confirmed SKU
  - Update SYSTEM_PROPERTIES.md if tracking logic changes

### Future Enhancements

- [ ] Auto-reset counter on billing cycle
  - Track last reset date in ScriptProperties
  - Auto-reset monthly (or warn user)

- [ ] Better usage analytics
  - Track calls per campaign
  - Success rate vs. API usage
  - Monthly usage trends

- [ ] Dynamic limit adjustment
  - Read free tier limit from API (if available)
  - Adjust warnings based on actual quota

---

## Legacy vs. New Places API

### Why This Matters

**Legacy Places API:**
- Old endpoint: `https://maps.googleapis.com/maps/api/place/textsearch/json`
- Designated "Legacy" as of March 2025
- Limited volume discounts (100K+ only)
- No new feature development
- **Status:** We don't use this (good!)

**Places API (New):**
- New endpoint: `https://places.googleapis.com/v1/places:searchText`
- Active development
- Better volume discounts (5M+ scaling)
- 10,000 free calls/month (Essentials)
- **Status:** We use this ✅

**Implication:** We're already using the recommended API, no migration needed.

---

## Volume Discounts (For Future Scale)

### Pricing Tiers (Essentials SKU)

| Monthly Usage | Cost per 1,000 | Effective Cost |
|---------------|----------------|----------------|
| 0 - 10,000 | $0 | FREE |
| 10,001 - 100,000 | $17.00 | $17/1K |
| 100,001 - 500,000 | $13.60 | $13.60/1K (20% discount) |
| 500,001 - 5,000,000 | $10.88 | $10.88/1K (36% discount) |
| 5,000,001+ | $8.16 | $8.16/1K (52% discount) |

**Example:** 50,000 calls/month
- First 10,000: FREE
- Next 40,000: $680 (40 × $17)
- **Total:** $680/month

**Current Project:** Never exceeds 3,000 calls → Always FREE

---

## Billing Cycle Tracking

### Current System

**Problem:** Don't know when Google's billing month starts

**Current Approach:**
- Assume monthly reset on 1st of month
- Manual reset via menu when month changes
- No automated tracking

**Risks:**
- Forget to reset → Inaccurate tracking
- Billing month doesn't match calendar month → Over/under count

### Recommended Fix

**Add to ScriptProperties:**
```javascript
// New properties to track
'billingCycleStart': '2025-10-01',  // ISO date of current billing period
'lastApiReset': '2025-10-01',       // Last time counter was reset
```

**Auto-reset logic:**
```javascript
function checkAndResetIfNeeded() {
  const props = PropertiesService.getScriptProperties();
  const lastReset = props.getProperty('lastApiReset');

  if (!lastReset) {
    // First time, ask user for billing cycle start
    return;
  }

  const lastResetDate = new Date(lastReset);
  const now = new Date();

  // If more than 30 days since reset, warn user
  const daysSinceReset = (now - lastResetDate) / (1000 * 60 * 60 * 24);

  if (daysSinceReset > 30) {
    const ui = SpreadsheetApp.getUi();
    const response = ui.alert(
      'API Counter Reset Needed?',
      `It's been ${Math.floor(daysSinceReset)} days since last reset.\n\n` +
      `Current count: ${getApiCallCount()}\n\n` +
      `Reset counter for new billing month?`,
      ui.ButtonSet.YES_NO
    );

    if (response === ui.Button.YES) {
      props.setProperty('apiCallCount', '0');
      props.setProperty('lastApiReset', now.toISOString().split('T')[0]);
    }
  }
}
```

**Future TODO:** Implement this logic in UniversalProviderSuite.js

---

## Comparison with Other APIs

### Google Maps Platform Services

| Service | Essentials Free Tier | Pro Free Tier |
|---------|---------------------|---------------|
| Places API (New) - Text Search | 10,000 | 5,000 |
| Geocoding API | 10,000 | 5,000 |
| Maps JavaScript API | 10,000 dynamic loads | 5,000 |
| Routes API | 10,000 | 5,000 |

**Note:** Each service has separate free tier (not pooled)

**Implication:** If we ever add Geocoding (to validate addresses), we get another 10,000 free calls/month.

---

## FAQ

### Q: Do I need to do anything to get the new free tier?

**A:** No, it automatically applied on March 1, 2025. If your billing account was active before March 1, you automatically transitioned to the new system.

### Q: Is our current 3,000 call limit still valid?

**A:** Yes, but it's conservative. With 10,000 free calls, you could safely increase to 5,000-8,000 if needed.

### Q: What happens if we exceed 10,000 calls?

**A:** You'll be charged $17 per 1,000 additional calls (Essentials tier). Example: 11,000 calls = $17 charge.

### Q: Do we need to migrate from Places API to Places API (New)?

**A:** No, we're already using Places API (New). No migration needed.

### Q: Can we use the old $200 credit approach?

**A:** No, that system ended February 28, 2025. New per-SKU free tier is automatic.

### Q: How do I check my current billing/usage?

**A:** Google Cloud Console → Billing → Reports → Filter by "Places API (New)"

### Q: What if we need more than 10,000 calls/month?

**A:** You'll pay for overage, but with volume discounts:
- 50K calls/month: ~$680/month
- 100K calls/month: ~$1,530/month
- (Still free tier for first 10K)

---

## Recommendations

### Short-Term (October-December 2025)

1. ✅ **Verify SKU category** in Google Cloud Console
2. ✅ **Keep current 3,000 limit** (conservative, safe)
3. ✅ **Document billing cycle start date** (when does your month reset?)
4. ✅ **Monitor actual usage** for 2-3 months to establish baseline

### Medium-Term (Q1 2026)

1. **Consider increasing limit to 5,000-8,000 calls**
   - Current usage (~750/month) well under even conservative 3K limit
   - New free tier (10K) provides much more headroom
   - Allows larger campaigns or multiple simultaneous campaigns

2. **Implement auto-reset reminder**
   - Check days since last reset
   - Warn user when >30 days
   - Prevent accidental quota tracking errors

3. **Add usage analytics**
   - Calls per campaign
   - Success rate tracking
   - Month-over-month trends

### Long-Term (2026+)

1. **Dynamic quota management**
   - Read actual free tier from billing API (if available)
   - Adjust limits automatically
   - Handle quota changes without code updates

2. **Campaign planning tool**
   - Input: Expected providers to verify
   - Output: Estimated API calls needed
   - Check: Available quota remaining this month

---

## References

- [Google Maps Platform March 2025 Changes](https://developers.google.com/maps/billing-and-pricing/march-2025)
- [Places API (New) Pricing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)
- [Core Services Pricing List](https://developers.google.com/maps/billing-and-pricing/pricing)

---

**Last Updated:** October 18, 2025
**Next Review:** January 2026 (after 3 months of new billing system)

**Action Required:** Verify SKU category in Google Cloud Console
