# Strategic Decision Questions

**Date:** November 17, 2025
**Source:** CODE_REVIEW_SUMMARY.md cross-analysis
**Purpose:** Strategic questions requiring user decisions before proceeding with fixes

---

## 🎯 HIGH-IMPACT DECISIONS (Affect Architecture)

### Q1: Should status-to-color use exact match or substring match?

**Current state:**
- **JavaScript (ToolboxSuite.js):** Exact match required
  ```javascript
  'Successful Order' === status  // Must match exactly
  ```
- **Python (eoy_tool.py):** Substring match (flexible)
  ```python
  if "successful" in status and "order" in status  # Handles variations
  ```

**Impact:**
- User types "Voicemail" → JS shows white, Python shows fuschia (inconsistent)
- No dropdown validation to enforce exact strings

**Options:**
- **A) Exact match (JavaScript approach)** - Stricter, less flexible, requires dropdown validation
- **B) Substring match (Python approach)** - Flexible, handles typos/variations

**Recommendation:** Option A (exact match) + add dropdown validation
- **Reason:** Archive shows mapping has been stable over time (5 colors unchanged)
- **Benefit:** Enforces data quality, prevents typos
- **Cost:** Need to add Google Sheets dropdown validation

**Your decision:** [ ]

---

### Q2: Should there be dropdown validation for Status column?

**Current:** Free text (users can type anything)

**Impact:** Without validation, status-to-color breaks if users type "voicemail" or "Order successful" (typos/variations)

**Recommendation:** YES - add dropdown validation
- **Values:** Exact strings from colorMappings (see Q1)
- **Implementation:** Google Sheets Data Validation → List from range or explicit list
- **Benefit:** Ensures consistent colors across Apps Script and Python

**Your decision:** [ ]

---

### Q8: Should EOY Apps Script automation be deprecated?

**Current state:** Two separate EOY tools exist
1. **ToolboxSuite.js EOY automation** (menu items lines 49-55)
   - Functions: auditWorkingList(), validateYellowOrders(), runFullEOYAutomation()
   - **Status:** Functional but has bugs (TODO.md section 0)
2. **eoy_tool.py Flask web app** (1349 lines)
   - **Status:** Read-only mode working, write phase NOT implemented

**TODO.md line 72 says:** "Flask tool is intended to replace this, but both currently functional"

**Options:**
- **A) Keep both** - Maintain redundant systems until Flask write phase complete
- **B) Deprecate Apps Script** - Focus solely on Flask tool, remove ToolboxSuite EOY functions
- **C) Fix Apps Script bugs, keep as backup** - Two tools for different use cases

**Questions:**
- Should Apps Script EOY functions be removed once Flask write phase is complete?
- Or keep both for different workflows (automated vs. manual review)?
- Are the bugs in Apps Script EOY worth fixing if Flask will replace it?

**Impact:**
- Maintenance burden (2 codebases to maintain)
- User training (which tool to use when?)
- Feature parity (Flask has better UI, Apps Script has automated workflow)

**Your decision:** [ ]

---

## 🔧 FEATURE COMPLETENESS

### Q3: Are shortcuts.js TODOs (Ctrl+F search, Ctrl+E export) planned?

**Current:** shortcuts.js:62-66, 68-72 have incomplete features
```javascript
// TODO: Open search modal
// TODO: Export current category
```

**Options:**
- **A) Implement features** - Add search modal and export functionality
- **B) Remove TODOs** - If not priority, clean up TODOs

**Your decision:** [ ]

---

### Q4: Should undo/redo be prioritized?

**Current state:**
- **Frontend:** undo.js exists, buttons visible in UI
- **Backend:** eoy_tool.py:1098, 1118 stubbed out with "TODO: Implement state restoration logic"
- **Result:** Buttons exist but don't work (misleading UX)

**Options:**
- **A) Implement backend** - Priority feature, implement state restoration
- **B) Disable frontend buttons** - Hide buttons until backend ready
- **C) Remove feature entirely** - Not needed, delete undo.js

**Questions:**
- How important is undo/redo for EOY cleanup workflow?
- Can users tolerate manual Ctrl+S saves only?
- Or is undo critical for confidence when making bulk changes?

**Your decision:** [ ]

---

## 🧪 TESTING & VALIDATION

### Q5: Should tests have --non-interactive flag?

**Current:** `input()` prompts block automation
- **Function:** validate_stats_color_counts() in eoy_tool.py:431
- **Prompt:** `input("Continue anyway? (y/n): ")`
- **Impact:** Can't run tests in CI/CD

**Options:**
- **A) Add --assume-yes flag** - Bypass prompts in automated mode
- **B) Leave as-is** - Tests are always manual/interactive
- **C) Remove prompts entirely** - Always continue (risky)

**Recommendation:** Option A - add flag for automation while keeping interactive mode default

**Your decision:** [ ]

---

### Q6: How should test files (similarity-test.js, ToolboxSuite.test.js) be run?

**Current:** Unclear execution method
- **Location:** test-data/
- **Type:** Standalone JavaScript (not Apps Script)

**Options:**
- **A) Node.js** - `node test-data/similarity-test.js`
- **B) Browser console** - Copy/paste into Chrome DevTools
- **C) Manual testing** - Reference only, not executable

**Question:** What's the current practice? How do you run these tests?

**Your decision:** [ ]

---

### Q7: Should 70% match threshold be configurable?

**Current:** run_all_tests.py:138 expects "at least 70% high confidence"

**Context:** Test cases (similarity-test.js) show threshold based on real data patterns:
- Capitalization: "Women to Women" vs "Women To Women"
- Apostrophes: "Women's" vs "Womens"
- Variations: & vs "and"

**Question:** Is 70% stable across all campaigns? Or should it be tunable?

**Options:**
- **A) Keep hardcoded 70%** - Threshold is stable based on historical data
- **B) Make configurable** - Allow tuning per campaign/dataset
- **C) Auto-tune based on data** - Calculate optimal threshold dynamically

**Your decision:** [ ]

---

## 🏗️ ARCHITECTURAL CLARITY

### Q9: What is GetStatsSnapshot.js used for?

**Current:** Purpose unclear
- **Comments:** "Run getStatsSnapshot() from Apps Script editor" and "Returns: JSON string of STATS sheet data (copy to Claude)"
- **Menu:** Creates "📊 Stats Tools" menu (conflicts with ToolboxSuite onOpen)

**Questions:**
- Is this for debugging/development only?
- Or actively used in production workflow?
- Should it be in separate utils/ folder if just debugging?

**Impact:** Affects whether to merge onOpen() menus or keep separate

**Your decision:** [ ]

---

### Q10: Is VerificationSidebar.html polling complexity justified?

**Current implementation:**
- 300ms polling to detect row changes
- Debouncing logic (2 consecutive polls required for stability)
- Stale response handling (ignore old responses if user moved)
- 10-second timeout with auto-recovery

**Question:** Is this sophisticated client-side logic necessary?

**Options:**
- **A) Keep as-is** - Complexity is justified for smooth UX
- **B) Simplify** - Reduce polling frequency or remove debouncing
- **C) Rearchitect** - Use event-driven approach instead of polling

**Context:** This is production code (UniversalProviderSuite.js integration works)

**Your decision:** [ ]

---

### Q11: Is beforeunload auto-save acceptable?

**Current:** selection.js uses beforeunload event for auto-save
- **Issue:** docs/README.md:410 acknowledges "beforeunload event not 100% reliable"
- **Workaround:** Manual save (Ctrl+S) recommended as primary method

**Question:** Should there be periodic auto-save instead/additionally?

**Options:**
- **A) Keep as-is** - beforeunload + manual Ctrl+S is acceptable
- **B) Add periodic auto-save** - Every 30-60 seconds automatically
- **C) Remove beforeunload, manual only** - Simpler, more predictable

**Trade-off:** Data loss risk vs. implementation complexity

**Your decision:** [ ]

---

### Q13: Where are keyboard shortcuts handled (HTML vs backend)?

**Current:** UniversalProviderSuite.js header documents shortcuts: G, Q, E, R, S, L

**Question:** Are keyboard handlers in VerificationSidebar.html (client-side) or delegated to UniversalProviderSuite.js (server-side)?

**Impact:** Need to clarify architecture for maintenance

**Your answer:** [ ]

---

## 🔬 MINOR DECISIONS (Lower Priority)

### Q12: Should spot_check_taxonomy.py sample randomly instead of first 30?

**Current:** Shows first 30 providers (`df.head(30)`)

**Question:** Is this representative? Or should it sample randomly?

**Your decision:** [ ]

---

### Q14 (new): Should DebugRepairSidebar prompt() be upgraded?

**Current:** Uses blocking `prompt('Edit notes:', currentNotes)` (line 635)

**Options:**
- **A) Keep as-is** - Acceptable for sidebar tool
- **B) Upgrade to inline editing** - Modern UX
- **C) Upgrade to modal dialog** - Non-blocking alternative

**Priority:** Low (only if users complain)

**Your decision:** [ ]

---

### Q15 (new): Should NPPES column names have defensive checks?

**Current:** Hardcoded column names in spot_check_taxonomy.py
- Examples: 'Provider First Name', 'Provider Last Name (Legal Name)', 'Healthcare Provider Taxonomy Code_1'

**Risk:** If NPPES changes format, script breaks silently

**Options:**
- **A) Accept risk** - NPPES format has been stable historically
- **B) Add defensive checks** - Verify expected columns exist on load
- **C) Document only** - Note NPPES version/format assumptions in README

**Your decision:** [ ]

---

## 📝 SUMMARY FOR QUICK REFERENCE

**High-impact (must decide):**
- Q1: Status-to-color: exact vs substring?
- Q2: Add dropdown validation?
- Q8: Deprecate Apps Script EOY automation?

**Feature completeness:**
- Q3: Implement or remove shortcuts.js TODOs?
- Q4: Prioritize undo/redo implementation?

**Testing:**
- Q5: Add --non-interactive flag?
- Q6: How to run JavaScript tests?
- Q7: Make 70% threshold configurable?

**Architecture clarity:**
- Q9: GetStatsSnapshot.js purpose?
- Q10: VerificationSidebar polling complexity justified?
- Q11: beforeunload auto-save acceptable?
- Q13: Keyboard shortcuts architecture?

**Minor:**
- Q12: Random sampling for spot-check?
- Q14: Upgrade DebugRepairSidebar prompt()?
- Q15: NPPES column name defensive checks?

---

**Next steps:** Review these questions and provide decisions. This will unblock Phase 1 and Phase 2 of the remediation plan.
