# Documentation Review Questions

**Last Updated:** 2025-11-17
**Purpose:** Track questions while methodically reviewing all docs and code

---

## AGENT_PRINCIPLES.md ✅ REVIEWED & ANSWERED

**No issues** - File is current and accurate

**Q1 ANSWERED:** Line 144 "Final validation? → Backup + production"
- Context: Test coverage section
- Meaning: Before doing final validation on production sheet, create backup first, then validate on production
- Related to line 118: "❌ Edit production without backup"

---

## STRUCTURE.md - PARTIAL REVIEW (deferred)

**Major Issues Found:**
- Missing 11 Python scripts in scripts/ root (eoy_tool.py + tests + utils)
- docs/ folder tree incomplete (missing 5 .md files)
- Contradictions between line 83 table and lines 19-28 tree
- TEST_RESULTS.md not mentioned but exists in root

**Deferred for later cleanup**

---

## MASTER_SYSTEM_DOCUMENTATION.md ✅ REVIEWED & ANSWERED (1426 lines - 77% OBSOLETE!)

**Purpose:** Comprehensive technical reference for entire system

**STATUS:** Mix of current and outdated - **77% of file is obsolete API documentation**

**SYSTEM DATE:** November 17, 2025

**STRUCTURE ANALYSIS:**

**Section 1 (Lines 1-375): Core System Documentation**
- System overview, pipeline, verification, EOY, sheet structures
- **Has issues but generally useful**
- Contradictions: Line 19 "Verify via Google Places API" vs Line 96 "NO GOOGLE PLACES API"
- Broken refs: Line 4 `OBGYN_CLEANUP_CHECKLIST.md` (should be `docs/...DEPRECATED.md`)
- Line 6: References `DEBUG_REPAIR_SYSTEM_SPEC.md` ✅ **ANSWERED: File does NOT exist** (broken reference)
- Line 178: "Oct 2025" is CORRECT (1 month ago, API removed Oct 29, 2025)
- Line 212, 304, 317, 375: Wrong file paths (missing `docs/` and `_DEPRECATED` suffix)
- Line 216: Says `scripts/eoy_obgyn_tool.py` (actual: `scripts/eoy_tool.py`)
- Line 240: References outdated `docs/EOY_TOOL_SPEC.md` (should ref `docs/README.md`)
- Line 322: "API limit hit" - API doesn't exist anymore (removed Oct 29, 2025)
- Line 324: "Yellow validation failing" - contradicts git commit `d219925` saying FIXED
- Version numbers ✅ **ANSWERED: UniversalProviderSuite.js is v13.3** (docs say v8.0/v9.0/v10.1 - all outdated)

**Section 2 (Lines 376-733): System Properties Documentation**
- **100% OBSOLETE** - All about `PLACES_API_KEY`, `apiCallCount`, API configuration
- Google Places API was removed **October 29, 2025** (commit b553266, 3 weeks ago)
- 357 lines of dead documentation
- Includes: API key setup, call counter, progress tracking, migration, security, troubleshooting

**Section 3 (Lines 742-1095): EOY vs Reset Phase Documentation**
- Explains difference between EOY cleanup and Reset phase
- Workflow timeline, implementation status, examples, FAQ
- **Likely still relevant** (describes Apps Script EOY automation vs manual reset)
- 353 lines

**Section 4 (Lines 1098-1426): Google Places API Pricing/Billing Guide**
- **100% OBSOLETE** - All about API SKUs, quotas, pricing, billing
- "March 1, 2025" is CORRECT date (8 months ago)
- "October-December 2025" is mostly PAST (API removed Oct 29)
- "Q1 2026" is FUTURE planning (2 months away - obsolete since API gone)
- 328 lines of dead documentation
- Includes: New vs old API, free tier, pricing tiers, billing tracking, comparisons, FAQs

**OBSOLETE CONTENT TOTAL:**
- Lines 376-733: 357 lines (API properties/config)
- Lines 1098-1426: 328 lines (API pricing/billing)
- **Total: ~685 lines (48%) are purely API docs**
- Additional ~400 lines have API references mixed with current info
- **Effective obsolete: ~1100 lines (77%)**

**ALL QUESTIONS ANSWERED:**
1. ✅ `DEBUG_REPAIR_SYSTEM_SPEC.md` does NOT exist (broken reference - remove it)
2. ✅ UniversalProviderSuite.js current version is **v13.3** (git commits show version history)
3. ✅ Lines 742-1095 (EOY vs Reset) likely still valid - describes Apps Script automation differences

**RECOMMENDATION:**
- **Keep:** Lines 1-375 (with fixes for contradictions/broken refs/outdated versions)
- **Keep:** Lines 742-1095 (EOY vs Reset docs - still relevant for Apps Script automation)
- **Archive:** Lines 376-741, 1098-1426 (obsolete API documentation)
- **Result:** 1426 lines → ~728 lines (49% reduction)

---

## README.md (root) ✅ REVIEWED (965 lines - mostly current, needs EOY tool section)

**Purpose:** Comprehensive project overview - mostly current and useful

**CRITICAL ISSUES:**

1. **MISSING: Entire EOY Flask Tool Section**
   - No mention of `scripts/eoy_tool.py` (1349 lines, Flask web app)
   - No mention of `templates/`, `static/`, `docs/README.md` (EOY tool files)
   - No mention of `TEST_RESULTS.md` in project structure (lines 95-139)
   - Line 315 says EOY consolidation is "MANUAL (automation planned)"
   - **But Flask tool already exists and is partially working!**

2. **Pipeline Numbering Error (lines 32-91):**
   - STEP 1, 2, 3, 4, then jumps to STEP 6
   - Missing STEP 5 (or renumber needed?)

3. **File Location Contradictions:**
   - Lines 46, 130: "data/nppes/.../nppes_filter_pcps.py"
   - But STRUCTURE.md said: "scripts/nppes-filter/nppes_filter_pcps.py"
   - **Both locations exist with identical files** (verified with `fc`)
   - Which is source of truth? Delete duplicate?

4. ~~**Future Date Typo:**~~ ✅ **CORRECTED**
   - Line 650: "October **2025**" is **CORRECT** (1 month ago from Nov 17, 2025)
   - LLM time-blind error - always check `date` first!

5. ~~**Fuzzy Matching Weights Mismatch:**~~ ✅ **ANSWERED - NOT A MISMATCH**
   - Lines 686-689: 40% phone + 40% name + 20% address (general duplicate detection)
   - docs/README.md: 70% name + 30% address, NO phone (EOY Yellow→NO validation)
   - **These are DIFFERENT algorithms for DIFFERENT purposes:**
     - EOY validation: New Orders sheet **has no phone column**, so uses name+address only
     - Duplicate detection: Has phone, so uses phone+name+address
   - **NOT an inconsistency** - different data availability requires different weights

6. ~~**Version Number Inconsistencies:**~~ ✅ **ANSWERED**
   - Line 62: "v10.1", Line 948: "v8.0" - **Both OUTDATED**
   - Current version: **UniversalProviderSuite.js v13.3** (git log shows latest)
   - Line 949: "ToolboxSuite.js v10.0" - Need to verify (likely also outdated)

7. **Incomplete File Structure (lines 95-139):**
   - Shows `scripts/pcp-list/` but not `scripts/obgyn-list/`
   - Doesn't show `scripts/eoy_tool.py`
   - Doesn't show `scripts/tests/` or `scripts/test_*.py` files
   - Missing `docs/EOY_TOOL_SPEC.md`, `docs/README.md`, `docs/IMPROVEMENTS_MADE.md`
   - Missing `TEST_RESULTS.md` in root
   - Missing `templates/` and `static/` folders

4. **Hardcoded Script IDs (lines 177-191):**
   - Contains actual Google Apps Script IDs
   - Security issue? Should these be redacted in git?

5. **State List Mismatch (line 44):**
   - Says: "currently: TX, TN, OK, OR"
   - But TODO.md mentioned: TX, WA, CO, PA for OBGYN
   - Which is current?

6. **Incomplete File Structure (lines 95-139):**
   - Only shows pcp-list/, not obgyn-list/
   - Doesn't show scripts/eoy_tool.py
   - Doesn't show scripts/tests/
   - Doesn't show TEST_RESULTS.md in root
   - Missing docs/EOY_TOOL_SPEC.md, docs/README.md

7. **Version Number Inconsistency:**
   - Line 63: "v10.1"
   - Line 949: "v10.0"
   - Line 948: "v8.0"
   - Which is current?

8. **Vague Claims:**
   - Line 338: Duplicates check "Under development" - but is there code for it?
   - Line 315: EOY "automation planned" - but eoy_tool.py exists

**QUESTIONS:**

Q: Where IS nppes_filter_pcps.py actually located?
   **ANSWER:** EXISTS IN BOTH LOCATIONS (identical files):
   - data/nppes/NPPES_Data_Dissemination_September_2025_V2/nppes_filter_pcps.py
   - scripts/nppes-filter/nppes_filter_pcps.py
   **PROBLEM:** Which is source of truth? Should one be deleted?
Q: Should Google Apps Script IDs be redacted from README?
Q: What are the actual current target states (TX/TN/OK/OR vs TX/WA/CO/PA)?
Q: Why no mention of the EOY Flask tool at all?

---

## TEST_RESULTS.md ✅ REVIEWED

**Purpose:** Automated test results for EOY tool (229 lines)

**STATUS:** Accurate test data, but misleading conclusion

**Test Date:** 2025-11-16 (recent - 1 day ago)

**What's GOOD:**
- Documents 8/8 tests passing
- Shows specific metrics (737 WL rows, 241 NO rows, 97.6% match accuracy)
- Test methodology is sound
- All data checks out

**What's MISLEADING:**
- Line 5: "✅ ALL TESTS PASSED (8/8)"
- Line 228: "Status: ✅ READY FOR PRODUCTION"
- **But:** docs/README.md says write phase not implemented (tool is read-only)
- Tests validate DATA PROCESSING, not complete functionality

**QUESTION:** Are these tests still valid? They test the Flask tool's validation logic, which seems correct.

**DECISION:** Keep file, but add caveat at top about read-only status

---

## TODO.md ✅ REVIEWED

**Purpose:** Task tracking document (368 lines)

**STATUS:** SEVERELY OUTDATED - contradicts reality

**CRITICAL ISSUES:**

1. **Lines 7-51: Section 0 completely wrong**
   - Line 7: "ARCHITECTURE COMPLETE - Ready to build"
   - Line 41: "Build `scripts/eoy_obgyn_tool.py`"
   - Line 42: "Framework: Textual TUI"
   - **REALITY:** Flask tool (scripts/eoy_tool.py) already built, 1349 lines
   - **This entire section is pre-build planning, not current status**

2. **Broken References:**
   - Line 26: "docs/EOY_TOOL_ARCHITECTURE_V2.md" (in archive, not active)
   - Line 32: "docs/ARCHITECTURE_GAP_ANALYSIS.md" (in archive)
   - Line 36: "docs/UNRESOLVED_QUESTIONS.md" (in archive)
   - Line 73: "Read EOY_TOOL_ARCHITECTURE_V2.md" (outdated instruction)

3. **Future Date Typo:**
   - Line 65: "Google Places API removed (Oct 2025)" - should be 2024?

4. **Contradicts Other Docs:**
   - Says tool needs to be built
   - But docs/README.md documents Flask tool as already built
   - But docs/IMPROVEMENTS_MADE.md says "production-ready"

**DECISION:** Section 0 needs complete rewrite to reflect Flask tool reality

---

## docs/README.md ✅ REVIEWED

**Purpose:** Complete EOY Flask tool documentation (447 lines) - CURRENT and ACCURATE

**STATUS:** This is the GOOD README for the EOY tool

**Key Findings:**
- Documents actual Flask implementation (not Textual TUI)
- Clear about what's implemented vs not (lines 315-333)
- Line 446: "Trust the code, not the old docs" ← EXCELLENT principle
- All referenced folders verified to exist (templates/, static/, scripts/)
- Explicitly says to IGNORE archived docs about Textual TUI

**NOT YET IMPLEMENTED (confirmed):**
1. Writing changes to Google Sheets
2. Undo/redo restore logic
3. Full edit modal
4. Some bulk actions

**RELATIONSHIP TO ROOT README:**
- docs/README.md = EOY tool only
- Root README.md = Entire project
- **Problem:** Root README doesn't mention EOY tool at all!
- Should root README reference this doc?

---

## docs/EOY_TOOL_SPEC.md ✅ REVIEWED

**Purpose:** Original planning doc for EOY tool (402 lines)

**STATUS:** OUTDATED - describes Terminal UI, not Flask web app

**Key Findings:**
- Line 5: "Planning phase - need answers to questions below before building"
- Line 3: Says file would be "scripts/eoy_obgyn_tool.py" (never created)
- Describes "Interactive Terminal UI" (was never built - Flask was built instead)
- Data model section (lines 30-68) has useful domain knowledge
- Validation logic matches what was actually implemented

**DECISION:** Should be archived
- Useful for historical context / understanding requirements
- But actual implementation is different (Flask not Terminal)
- docs/README.md is the current doc

---

## docs/CLASP_SETUP.md ✅ REVIEWED

**Purpose:** clasp setup guide (194 lines)

**STATUS:** CURRENT and USEFUL - keep as-is

**No issues found** - straightforward setup doc that's accurate

---

## docs/FILTERING_IMPROVEMENTS_BRAINSTORM.md ✅ REVIEWED

**Purpose:** Future improvement ideas (309 lines, dated 2025-10-11)

**STATUS:** Active planning doc - but CONTRADICTS current reality

**CRITICAL CONTRADICTION:**
- Line 8-16: Discusses Google Places API verification improvements
- But README.md line 468 says: "100% manual verification (no Google Places API)"
- README.md line 912-916: Google Places API was abandoned (too expensive, $346/month)

**QUESTIONS:**
- Is Google Places API still being used or not?
- If not, should this whole doc be archived?
- If yes, root README needs updating

**Line 258:** Only Priority 1 item #1 is checked off (rest unchecked)

**VALUE IF KEPT:**
- Good ideas for NPPES Python filtering improvements (lines 64-186)
- Organization blacklist expansions
- Secondary taxonomy code checking

**DECISION:** Keep but needs clarification header about API status

---

## docs/GSPREAD_RATE_LIMITS.md - ALREADY READ IN PREVIOUS SESSION

**Status:** Contains API rate limit info, seems current and useful

---

## docs/IMPROVEMENTS_MADE.md ✅ REVIEWED

**Purpose:** Changelog documenting EOY Flask tool build (256 lines)

**STATUS:** Useful historical record - KEEP

**Key Info:**
- Documents 5 major improvements made to Flask tool
- Lists all files created/modified/archived
- Line 255: Claims "production-ready" (but write phase not implemented per docs/README.md)

**CONTRADICTIONS WITH OTHER DOCS:**
- Line 96: Says "EOY_TOOL_SPEC.md" is "still valid"
  - But I marked it as outdated (describes Terminal UI not Flask)
  - Which is correct?

**DECISION:** Keep as historical changelog, but note the "production-ready" claim is misleading

---

## docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md ✅ REVIEWED (partial)

**Purpose:** Guide for Apps Script EOY automation (5-step process)

**STATUS:** Marked deprecated in filename, but...

**CONFUSING:**
- Line 8: "READY TO USE (Oct 18, 2025)" ← future date or typo?
- Describes Apps Script automation (steps 1-5)
- But Flask tool was built to REPLACE Apps Script automation
- Why is it "deprecated" if it says "ready to use"?

**TWO DIFFERENT EOY SYSTEMS:**
1. **Apps Script** (described in this doc) - 5-step automation in Google Sheets
2. **Flask tool** (scripts/eoy_tool.py) - Local Python web app

**QUESTION:** Are both systems in use, or did Flask replace Apps Script?

**DECISION:** Needs clarification before archiving

---

## docs/NOTES_SAMPLE_ANALYSIS.txt - ALREADY READ IN PREVIOUS SESSION

**Status:** Real data patterns from actual notes (289 rows, 39%), useful domain knowledge

---


## test-data/README.md ✅ REVIEWED

**Purpose:** Test data documentation (134 lines)

**STATUS:** Current and useful - KEEP

**Contents:**
- Documents test CSV with 22 edge cases
- Explains similarity-test.js results (0.85 threshold recommended)
- Lists known fixed bugs
- Test coverage goals (some unchecked)

**No issues found** - good reference doc

---

## SUMMARY OF DOCUMENTATION REVIEW

**TOTAL DOCS REVIEWED:** 12 markdown files

### ✅ GOOD DOCS (Keep as-is):
1. **AGENT_PRINCIPLES.md** - Fixed and updated
2. **docs/CLASP_SETUP.md** - Current and accurate
3. **docs/README.md** - Excellent Flask tool documentation
4. **docs/GSPREAD_RATE_LIMITS.md** - Technical reference, still valid
5. **docs/NOTES_SAMPLE_ANALYSIS.txt** - Domain knowledge
6. **test-data/README.md** - Test documentation

### ⚠️ NEEDS UPDATING:
7. **README.md (root)** - Missing entire EOY Flask tool section
8. **TEST_RESULTS.md** - Add caveat about read-only status
9. **docs/FILTERING_IMPROVEMENTS_BRAINSTORM.md** - Clarify API status

### 🔴 SEVERELY OUTDATED:
10. **TODO.md** - Section 0 completely wrong (says tool needs building, but it's built)
11. **MASTER_SYSTEM_DOCUMENTATION.md** - API contradictions, broken references, too large (1426 lines)

### 🗂️ SHOULD BE ARCHIVED:
12. **docs/EOY_TOOL_SPEC.md** - Planning doc for Terminal UI (Flask was built instead)
13. **docs/IMPROVEMENTS_MADE.md** - Historical changelog (useful but archive-worthy)
14. **docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md** - Already has "DEPRECATED" in filename

### ⏭️ DEFERRED (Too complex for initial review):
- **STRUCTURE.md** - Needs complete rewrite after file cleanup

---

## CRITICAL QUESTIONS - ANSWERS FROM SYSTEMATIC REVIEW

**System Date:** November 17, 2025

### Q1: Google Places API Status ✅ ANSWERED
- **ANSWER:** API was **REMOVED on October 29, 2025** (commit b553266, 3 weeks ago)
- README.md line 912: Correct - "API abandoned, too expensive ($346/month)"
- MASTER_SYSTEM_DOCUMENTATION.md lines 19+36: OUTDATED (need removal)
- FILTERING_IMPROVEMENTS_BRAINSTORM.md: OUTDATED (discusses API improvements that won't happen)
- **Action needed:** Remove all API references from docs, archive API documentation sections

### Q2: EOY Tool - Which System Is Current? ✅ PARTIALLY ANSWERED
- **ANSWER:** **BOTH systems currently functional, Flask is intended replacement**
- **Apps Script EOY** (ToolboxSuite.js 5-step process):
  - Still works per git commit d219925 "Mark EOY Steps 1, 2 as FIXED/VERIFIED"
  - docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md documents it as functional
  - "DEPRECATED" in filename means "will be replaced by Flask", not "broken"
- **Flask tool** (scripts/eoy_tool.py, 1349 lines):
  - Already built (TODO.md Section 0 was outdated, now corrected)
  - Read-only mode working, write phase not implemented
  - docs/README.md is current documentation
- **Clarification needed from user:** When will Flask completely replace Apps Script?

### Q3: nppes_filter_pcps.py "Duplication" ✅ RESOLVED - NOT DUPLICATES!
- data/nppes/.../nppes_filter_pcps.py (Oct 18, 38KB) - **NEWER**
  - Targets: NM, UT, NE, AL (test campaign)
  - Has extensive SPECIALIST_TAXONOMIES blacklist (60+ specialist codes)
  - More sophisticated filtering
- scripts/nppes-filter/nppes_filter_pcps.py (Oct 10, 33KB) - **OLDER**
  - Targets: FL (different campaign)
  - Less filtering, older version
- **ANSWER:** These are DIFFERENT campaign configurations, NOT duplicates!
- **Action:** Keep both, but organize better (see folder structure recommendations)

### Q4: "Deprecated" Meaning ✅ ANSWERED
- docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md
- Line 8: "READY TO USE (Oct 18, 2025)" is **CORRECT** date (1 month ago, NOT future)
- **ANSWER:** "DEPRECATED" means "marked for replacement by Flask tool, but still functional"
- Apps Script EOY automation still works and is documented
- File should stay as reference until Flask tool write phase is complete
- **Not actually broken** - just planning to migrate away from it

---

## RECOMMENDED NEXT STEPS

1. **Answer the 4 critical questions above**
2. **Archive outdated planning docs:**
   - Move docs/EOY_TOOL_SPEC.md to docs/archive/
   - Move docs/IMPROVEMENTS_MADE.md to docs/archive/
3. **Rewrite severely outdated docs:**
   - TODO.md section 0 (make it reflect Flask tool reality)
   - MASTER_SYSTEM_DOCUMENTATION.md (resolve contradictions, possibly split up)
4. **Update docs with minor issues:**
   - Add EOY tool section to README.md
   - Add "read-only" caveat to TEST_RESULTS.md
   - Clarify API status in FILTERING_IMPROVEMENTS_BRAINSTORM.md
5. **Clean up file duplication:**
   - Decide on nppes script location, delete duplicate
6. **Rewrite STRUCTURE.md** (after cleanup complete)


---

## ✅ SYSTEMATIC REVIEW COMPLETE

**Date:** November 17, 2025
**Docs Reviewed:** 17 markdown files (excluding archived)

**Major Findings:**
1. ✅ **Time-blind error corrected** - Added principle to AGENT_PRINCIPLES.md, fixed all date misinterpretations
2. ✅ **API status clarified** - Google Places API removed Oct 29, 2025 (~77% of MASTER_SYSTEM_DOCUMENTATION.md is obsolete API docs)
3. ✅ **EOY systems clarified** - Both Apps Script and Flask tools functional, Flask is intended replacement
4. ✅ **Version numbers verified** - UniversalProviderSuite.js is v13.3 (many docs show v8.0-v10.1, outdated)
5. ✅ **Fuzzy matching explained** - Two different algorithms for different purposes (not a conflict)
6. ✅ **"Deprecated" meaning clarified** - Means "planned for replacement", not "broken"

**One question remains for user:**
- Q3: nppes_filter_pcps.py exists in 2 locations - which is source of truth?
