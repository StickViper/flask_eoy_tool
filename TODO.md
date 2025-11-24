# JGDC Master TODO List

## 🔴 IMMEDIATE PRIORITIES (Current Session)

### 0. OBGYN EOY Cleanup Tool (December 2024)

**Status:** ✅ FLASK WEB APP BUILT - Read-only mode working, write phase not implemented
**Last Updated:** 2025-11-17

#### ✅ COMPLETED:
- [x] **Flask web application built** (`scripts/eoy_tool.py`, 1349 lines)
  - Backend: Flask + gspread + rapidfuzz
  - Frontend: HTML templates + vanilla JS + CSS
  - Design: "Data Atelier" aesthetic (warm colors, easy on eyes for 2-4hr sessions)
- [x] **Data loading works** (11 API calls, well under 60/min quota)
  - Working List: 737 rows
  - New Orders: 241 rows
  - Status-to-color mapping (avoids reading 737 cell colors individually)
- [x] **All validation pipelines implemented:**
  - ✅ Yellow→NO fuzzy matching (97.6% high confidence, per TEST_RESULTS.md)
  - ✅ Duplicate detection (exact matches, networks, similar entries)
  - ✅ Status issue flagging (voicemail, email sent, potentially invalid)
  - ✅ 11 review categories with row grouping
- [x] **UI features working:**
  - ✅ Expandable match details (click ▶ to see NO row, confidence %)
  - ✅ Visual duplicate grouping (color-coded borders)
  - ✅ Multi-select (shift/ctrl click)
  - ✅ Sortable columns
  - ✅ Progress auto-save to JSON
  - ✅ Keyboard shortcuts
- [x] **Testing framework created** (`scripts/test_eoy_output.py`)
  - All 8 tests passing (as of 2024-11-16)
  - Match accuracy: 97.6% high confidence
- [x] **Documentation complete** (docs/README.md - 447 lines, current and accurate)

#### ❌ NOT YET IMPLEMENTED (Write Phase):
- [ ] Writing changes to Google Sheets (batch updates)
- [ ] Shadow worksheet creation (_CLEANUP suffix)
- [ ] Undo/redo restore logic (stack exists, restore not implemented)
- [ ] Full edit modal for complex edits
- [ ] Some bulk action handlers

#### 🔧 CURRENT STATE:
**What works:** Load data → Run validations → Review in UI → See match details
**What doesn't:** Actually writing changes back to Google Sheets

**To use tool:**
```bash
cd C:\Users\noagi\Desktop\JGDC
python scripts/eoy_tool.py
# Open http://127.0.0.1:5000
```

#### 📦 ARCHIVED PLANNING DOCS:
These described a Textual TUI that was never built - Flask web app was built instead:
- `docs/archive/EOY_TOOL_ARCHITECTURE_V2.md` (Textual UI design)
- `docs/archive/ARCHITECTURE_GAP_ANALYSIS.md` (planning)
- `docs/archive/UNRESOLVED_QUESTIONS.md` (pre-build questions)

#### 🔴 CRITICAL - TEST SUITE (HIGH PRIORITY)

**Status:** ❌ NOT IMPLEMENTED - Comprehensive test suite needed BEFORE completing write phase

**Priority:** Must complete before implementing write phase to ensure data integrity

**Scope:**
1. **Status-to-color mapping** - Test exact match logic, edge cases
2. **Fuzzy matching** - Test with different weight configurations (70/30 name/addr)
   - A/B testing with real data samples to optimize weights
   - Network detection (same phone, ~# format)
3. **Duplicate detection** - Exact, fuzzy, and network identification
4. **Undo/redo** - Extensive testing of state snapshots and restoration
5. **Categorization logic** - Verify all 11 categories populate correctly
6. **Data loading** - gspread integration, Status-to-color derivation

**Framework:** pytest recommended (better reporting, fixtures, parametrize for edge cases)

**Why critical:** Write phase modifies Google Sheets data. Without tests, risk data loss/corruption.

#### 📋 NEXT STEPS (After Test Suite):

**TO COMPLETE WRITE PHASE:**
1. Implement batch Google Sheets updates (`gspread.batch_update()`)
2. Create shadow worksheets with _CLEANUP suffix
3. Wire up undo/redo restore logic
4. Test on real OBGYN data

**APPS SCRIPT EOY AUTOMATION:**
- Still exists in `scripts/obgyn-list/ToolboxSuite.js`
- Steps 1-5 work (per commit `d219925`: "Mark EOY Steps 1, 2, network notation as FIXED/VERIFIED")
- See `docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md` for usage
- Flask tool is intended to replace this, but both currently functional

---

## 🟠 HIGH PRIORITY (After OBGYN Reset)

### 2. PECOS Cross-Reference Integration

**Goal:** Reduce closed/inactive providers by 40%, increase call success rate from 25% to 35-40%

- [ ] **Build PECOS cross-reference script** (`scripts/pecos_cross_reference.py`)
  - **Input:** NPPES filtered CSV (e.g., `FILTERED_PCP_TX_2024.csv`)
  - **Process:**
    - Query CMS PECOS API by NPI
    - Keep only Medicare-enrolled providers (active enrollment)
    - Filter out closed/inactive providers automatically
  - **Output:** PECOS-verified CSV (e.g., `FILTERED_PCP_TX_2024_PECOS.csv`)
  - **Benefits:**
    - FREE (PECOS API is free, unlimited)
    - Eliminates 40-50% of closed providers
    - More current than NPPES (revalidates every 5 years)
    - Specialty info more accurate
  - **Time:** 2-3 hours to build, instant to run

- [ ] **Test PECOS filtering on recent NPPES export**
  - Run on 1000 TX providers
  - Measure: How many filtered out? (expect ~400-500 remaining)
  - Manual spot check: Are filtered providers actually closed?
  - Measure call success rate improvement

- [ ] **Optional: Add Twilio phone validation** (if PECOS alone insufficient)
  - Cost: $0.005 per phone = $5 per 1000 providers
  - Validates phone number exists and is reachable
  - Further reduces closed providers
  - Decision: Run after PECOS test to see if needed

### 3. Provider Filtering Improvements

**From `docs/FILTERING_IMPROVEMENTS_BRAINSTORM.md`:**

- [ ] **Expand organization blacklist** (nppes_filter_pcps.py)
  - Add: dermatology, dental, veterinary, chiropractic, etc.
  - Test on recent NPPES export
  - Measure over-filtering rate

- [ ] **Secondary taxonomy code check**
  - NPPES has up to 15 taxonomy codes per provider
  - Check if ANY code indicates specialist (not just primary)
  - Catches multi-specialty groups

### 4. Documentation & Testing

- [ ] **Create test data generator** (`scripts/test_data_generator.py`)
  - Generate 150-200 realistic EOY test cases
  - All edge cases: perfect matches, fuzzy matches, duplicates, status issues
  - Upload to "EOY Test - PCP" sheet once
  - Use for fast iteration during development

- [ ] **Document local Python workflow**
  - When to use Apps Script vs Python
  - gspread setup guide
  - EOY tool usage guide
  - PECOS integration guide

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
