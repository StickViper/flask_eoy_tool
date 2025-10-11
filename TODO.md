# JGDC Master TODO List

## 🔴 IMMEDIATE PRIORITIES (Current Session)

### 0. Fix Half-Implemented EOY Features (CRITICAL BUGS)

**Status:** In progress - fixing bugs found during codebase audit

#### ✅ COMPLETED:
- [x] Fix DebugRepairSidebar field name mismatches (backend now returns proper column headers)

#### 🔧 IN PROGRESS:
- [ ] **EOY Step 2: Rewrite to use fuzzy matching** (CRITICAL BUG)
  - **Problem:** Currently uses phone-only matching but phone isn't in New Orders
  - **Reality:** New Orders only has Office Name + Address
  - **Fix:** Use existing `fuzzyMatchNewOrders()` function with multi-field matching
  - **Files:** `scripts/obgyn-list/ToolboxSuite.js:815-883`, `scripts/pcp-list/ToolboxSuite.js:764-833`

#### 📋 PENDING:
- [ ] **EOY Step 1: Actually populate Debug/Issues column**
  - **Problem:** Only shows alert with counts, doesn't write to Debug column
  - **Fix:** Modify `auditWorkingList()` to write findings to column (not dry-run mode)
  - **Files:** `scripts/obgyn-list/ToolboxSuite.js:723-757`, `scripts/pcp-list/ToolboxSuite.js:723-757`

- [ ] **Fix network notation format**
  - **Current:** "Same network - multiple locations"
  - **Wanted:** "sunlife network (~8);" with actual network name and location count
  - **Files:** `scripts/obgyn-list/ToolboxSuite.js:1037-1042`, `scripts/pcp-list/ToolboxSuite.js:959-1056`

- [ ] **Implement programmatic filter views**
  - [ ] `showDebugFilter()` - unhide and filter Debug/Issues column
  - [ ] `clearDebugFilter()` - restore normal view
  - [ ] `showColorFilter(color)` - filter by status color
  - [ ] Add '🔍 Debug Views' submenu to Misc. Tools menu

- [ ] **Menu cleanup**
  - [ ] Remove unused `validateCurrentSheet()` stub (lines 691-701)
  - [ ] Remove unused `findDuplicatesInSheet()` stub (lines 707-712)
  - [ ] Remove '🔍 Validation & Debugging' submenu from menu (lines 33-35)

- [ ] **Move Not Interested to sidebar**
  - [ ] Add Not Interested handling to DebugRepairSidebar UI
  - [ ] Remove EOY Step 3 from menu after moving to sidebar

### 1. Install Python Dependencies (BLOCKING)
```bash
pip install pandas
```
- **Why:** Required for NPPES filtering script to run
- **Status:** Not installed on current machine

### 2. Run OBGYN Filtering (TX, WA, CO, PA)
- **Goal:** Generate ~400 TX + ~80 each WA/CO/PA providers for verification
- **Steps:**
  1. Verify pandas is installed
  2. Set `DRY_RUN = False` in `nppes_filter_pcps.py`
  3. Run: `python nppes_filter_pcps.py`
  4. Import filtered CSVs to Google Sheets (manual)
  5. Run verification (watch API limit: 3000 max)
- **Expected API usage:** ~465 calls (well under 3000 limit)

### 3. Test EOY Automation on OBGYN Working List
- **Status:** ⚠️ BLOCKED - Critical bugs found, fixing before testing
- **Menu location:** Misc. Tools → End-of-Year Workflow
- **Blocking issues identified:**
  1. ❌ Step 1 only shows alerts, doesn't populate Debug column
  2. ❌ Step 2 uses phone matching but phone not in New Orders (BROKEN)
  3. ⚠️ Network notation format wrong
  4. ⚠️ DebugRepairSidebar had field name mismatches (FIXED)
- **Steps to test (after fixes):**
  1. Open OBGYN Working List 2025
  2. Run "Step 1: Audit Working List"
  3. Review flagged issues in hidden "Debug/Issues" column
  4. Fix issues manually or run individual validation steps
- **Edge cases to watch:**
  - Messy copy-paste in New Orders sheet
  - "Not interested" variations in Notes column
  - Duplicate detection accuracy

### 4. Update OBGYN Sheet Script Connection
- **Current:** OBGYN uses standalone `onEdit()` function
- **Goal:** Connect to ToolboxSuite.js for EOY automation
- **Steps:**
  1. Get OBGYN sheet Script ID
  2. `cd scripts/obgyn-list` (create folder)
  3. `clasp clone <OBGYN_SCRIPT_ID>`
  4. Replace old code with ToolboxSuite.js functions
  5. Test onEdit coloring still works

---

## 🟠 HIGH PRIORITY (Next Week)

### Data Quality & Validation

- [ ] **Test all 6 EOY automation steps individually**
  - [ ] Step 1: Audit Working List (❌ BUG: doesn't populate Debug column)
  - [ ] Step 2: Validate Yellow → New Orders (❌ BROKEN: phone not in New Orders)
  - [x] Step 3: Enforce Not Interested Rules ✅ (works but needs to move to sidebar)
  - [ ] Step 4: Detect Duplicates (⚠️ works but network notation format wrong)
  - [x] Step 5: Review Status Issues ✅ (code complete)
  - [ ] Test with real OBGYN data (BLOCKED until bugs fixed)
  - [ ] Identify and document edge cases

- [ ] **Handle EOY transitions (Steps 6-7 - NOT YET AUTOMATED)**
  - Manual steps still required:
    1. Add "202X QTY" column
    2. Duplicate sheets, rename old ones with "OLD" prefix
    3. Clear New Orders sheet
    4. Clear colors/statuses (preserve email Notes)
    5. Update STATS tab formulas
    6. Update linked dashboard IMPORTRANGE
  - Automation complexity: High (formatting, formula updates)
  - Priority: Medium (once per year)

### API Usage Management

- [x] **Centralized API tracking** ✅ COMPLETE
  - [x] Hard limit at 3000 calls
  - [x] Warning at 2800 calls
  - [x] Pre-flight check before verification
  - [x] In-flight check during batch processing
  - [x] Enhanced usage display with percentages

- [ ] **API usage reset procedure**
  - Document when/how to reset counter
  - Track actual billing cycle dates
  - Add monthly usage log

### Documentation

- [ ] **Create OBGYN-specific docs**
  - How to run OBGYN filtering (different from PCP)
  - Expected taxonomy codes for OBGYN
  - State-specific considerations

- [ ] **Update EOY workflow guide**
  - Document each automation step
  - Screenshot expected outputs
  - Troubleshooting common errors

---

## 🟡 MEDIUM PRIORITY (This Month)

### Code Quality

- [ ] **Test capitalization fixes across both sheets**
  - Verify Mc/Mac names work
  - Test credential standardization (MD, DO, etc.)
  - Check apostrophe handling (O'Donnell)
  - Confirm mixed case suffixes (Jr, Sr)

- [ ] **Add error handling to EOY automation**
  - Graceful failures if columns missing
  - Better error messages for users
  - Rollback option if automation fails mid-process

- [ ] **Consolidation function improvements**
  - The current consolidation logic is complex
  - Add dry-run preview mode
  - Better conflict resolution UI
  - Test with multiple data sources

### User Experience

- [ ] **Improve duplicate detection accuracy**
  - Fuzzy matching for office names (optional)
  - Address normalization (Suite vs Ste)
  - Phone number format variations
  - Consider name similarity scoring

- [ ] **Better status-based review workflow**
  - Create actionable checklists for each status type
  - Add quick-action buttons (move to invalid list, etc.)
  - Track review progress

---

## 🟢 LOW PRIORITY (Future Enhancements)

### Automation Gaps

- [ ] **CSV import automation**
  - Auto-create properly named sheets
  - Map columns automatically
  - Validate data on import

- [ ] **Annual re-verification scheduler**
  - Mark providers needing re-verification
  - Batch re-verification process
  - Update verification dates

### Features

- [ ] **Enhanced search functionality**
  - Search across all sheets
  - Find provider by phone/name/city
  - "Where is this provider?" tool

- [ ] **Reporting & Analytics**
  - Success rate by state
  - Call efficiency metrics
  - Year-over-year comparison
  - Export board reports

### Technical Debt

- [ ] **Standardize sheet naming conventions**
  - Document naming rules
  - Update hardcoded references
  - Create config file for sheet names

- [ ] **Optimize performance**
  - Batch API calls more efficiently
  - Reduce sheet read/write operations
  - Cache frequently accessed data

---

## ✅ RECENTLY COMPLETED (This Session)

### Previous Session:
- [x] Updated Python config for OBGYN filtering (TX, WA, CO, PA)
- [x] Changed OUTPUT_PREFIX to 'FILTERED_obgyns'
- [x] Added centralized API usage tracker (3000 limit)
- [x] Added pre-flight safety check before verification starts
- [x] Added in-flight safety check during batch processing
- [x] Enhanced showApiUsage() with limit status and percentages
- [x] Built EOY automation suite (6 validation steps) - ⚠️ found bugs, see section 0
  - Yellow → New Orders validation (❌ BROKEN - phone not in New Orders)
  - Not Interested rule enforcement (✅ works)
  - Duplicate detection (⚠️ works but network notation format wrong)
  - Status-based review (✅ works)
  - Hidden Debug/Issues column creation (✅ works)
- [x] Added EOY workflow menu to Misc. Tools
- [x] Pushed all changes to Google Sheets via clasp
- [x] Verified OBGYN taxonomy codes in filter script

### Current Session (Bug Fixes):
- [x] Audited codebase for half-implemented features
- [x] Fixed DebugRepairSidebar field name mismatches
- [x] Added detailed TODO section for remaining bugs
- [x] Pushed DebugRepairSidebar fixes to both OBGYN and PCP sheets

---

## 📋 MAINTENANCE TASKS

### Regular (Monthly)
- [ ] Check for specialist contamination in new imports
- [ ] Review API usage trends
- [ ] Validate STATS tab accuracy

### Quarterly
- [ ] Update NPPES data (download from CMS)
- [ ] Re-verify closed/inactive providers
- [ ] Clean up Invalid/Inactive List

### Annually
- [ ] Run full EOY workflow
- [ ] Archive old year sheets
- [ ] Update year references in code
- [ ] Review and optimize entire workflow

---

## 🔬 RESEARCH & EXPLORATION

- [ ] **Explore OBGYN-specific filtering needs**
  - Are there OBGYN specialists we should exclude? (e.g., maternal-fetal medicine)
  - Should we include OB/GYN nurse practitioners?
  - Geographic concentration differences vs PCP

- [ ] **Better duplicate detection algorithms**
  - Levenshtein distance for name matching
  - Address parsing libraries
  - Phone number similarity scoring

- [ ] **EOY automation phase 2**
  - Sheet duplication with OLD prefix
  - Formula updates in STATS tab
  - IMPORTRANGE link updates
  - Complexity: Very High

---

## 📝 NOTES & DECISIONS

### Python Setup
- **Pandas required:** Script will fail without pandas installed
- **Installation:** `pip install pandas` (or `pip3` on some systems)
- **Testing:** Always run with `DRY_RUN = True` first

### API Limits
- **Free tier:** 3000 Places API calls per month
- **Current buffer:** 200-call safety margin (warning at 2800)
- **Actual usage:** Counter persists in ScriptProperties across sessions
- **Reset:** Manual via "API Usage" menu item

### EOY Workflow Philosophy
- **Flag, don't fix:** Most issues are flagged for manual review
- **Exception:** "Not interested" rules are auto-fixed (low risk)
- **Hidden column:** Debug/Issues column is auto-hidden to avoid clutter
- **Dry-run first:** All functions support dry-run mode for safety

### OBGYN vs PCP Differences
- **Taxonomy codes:** OBGYN uses 207V* codes
- **Provider density:** OBGYNs are less common than PCPs
- **Filtering ratio:** May need different input:output ratio
- **Organization handling:** Same rules apply (independent clinics only)

---

## 🎯 SUCCESS METRICS

### This Campaign (OBGYN 2025)
- [ ] 200 verified OBGYNs in TX
- [ ] 40 verified OBGYNs each in WA, CO, PA
- [ ] Total API calls < 3000
- [ ] Zero duplicate orders shipped
- [ ] Clean EOY transition with no data loss

### Long-term
- Reduce manual EOY work by 80%
- Zero formatting errors in consolidated data
- < 5% duplicate rate across all sheets
- 100% of yellow rows accounted for in New Orders

---

## 🚨 KNOWN ISSUES & RISKS

### Critical (Must Fix Now)
- **EOY Step 2 broken:** Uses phone matching but phone not in New Orders sheet
- **EOY Step 1 incomplete:** Doesn't populate Debug column, only shows alert
- **Network notation wrong format:** Uses generic text instead of "network-name network (~8);"

### High Risk
- **Pandas not installed:** BLOCKING Python script execution
- **Messy copy-pastes in New Orders:** Yellow validation will find many issues (once Step 2 fixed)
- **OBGYN sheet not connected to ToolboxSuite:** EOY automation won't work until connected

### Medium Risk
- **Missing filter view functions:** `showDebugFilter()`, `clearDebugFilter()`, `showColorFilter()` not implemented
- **Edge cases in "not interested" logic:** Need to test variations in Notes column
- **Duplicate detection false positives:** Phone number formatting variations
- **Status-based review complexity:** Many edge cases to handle

### Low Risk
- **API limit exceeded:** Unlikely with current safeguards (3000 limit, 465 expected usage)
- **Unused validation menu stubs:** Don't break anything but clutter the menu

---

## 💡 IDEAS FOR FUTURE

- Video tutorials for volunteers
- Automated backups before major changes
- Dashboard showing campaign progress
- Integration with dialer software
- Machine learning for predicting "not interested"
- Zapier/Make.com automation for some steps
