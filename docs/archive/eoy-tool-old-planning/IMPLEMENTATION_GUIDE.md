# EOY Tool Implementation Guide

**For:** Next LLM session (fresh mind)
**Task:** Build `scripts/eoy_obgyn_tool.py`
**Estimated Time:** 4-6 hours
**Status:** All planning complete, ready to build

---

## 📚 READ FIRST (In Order)

### 1. **Architecture V2** (PRIMARY REFERENCE)
**File:** `docs/EOY_TOOL_ARCHITECTURE_V2.md` (1560 lines)

**Contains:**
- Complete technology stack
- All 5 phases with code examples
- Data models (ProviderRow, NewOrderRow, Issue, ReviewCategory)
- Textual UI screens (EditRowScreen, NetworkConfirmScreen, etc.)
- Shadow worksheet creation
- Progress save/resume
- Error handling
- Helper functions

**READ THIS FULLY** - Everything you need is specified here

---

### 2. **Gap Analysis** (CONTEXT)
**File:** `docs/ARCHITECTURE_GAP_ANALYSIS.md`

**Shows:**
- What gaps were identified in v1 architecture
- How they were resolved
- Why certain decisions were made

**READ IF CONFUSED** about design choices

---

### 3. **Unresolved Questions** (MINOR ISSUES)
**File:** `docs/UNRESOLVED_QUESTIONS.md`

**Contains:** 10 minor questions that can be resolved during build

**Most Important:**
- QTY column location detection (search headers)
- Color hex normalization (test actual colors)
- Network mass-invalid reason format
- INVALID vs INACTIVE usage

**READ WHEN ENCOUNTERING** these issues during build

---

### 4. **Notes Analysis** (DATA REFERENCE)
**File:** `docs/NOTES_SAMPLE_ANALYSIS.txt`

**Contains:** Analysis of 289 actual notes from Working List
- Standard patterns (67%): vm x2, not interested, sent, network
- Non-standard patterns (33%): clearable callbacks, emails, office notes

**REFERENCE WHEN** implementing note chunk detection & cleanup

---

### 5. **Rate Limits** (API INFO)
**File:** `docs/GSPREAD_RATE_LIMITS.md`

**Shows:** Tool uses only ~11 API calls per run (well under 300/min limit)

**READ IF** concerned about API quota

---

## 🎯 QUICK START

### Prerequisites Verified
- ✅ gspread-formatting installed
- ✅ rapidfuzz installed
- ✅ textual installed
- ✅ Color reading tested & working
- ✅ Fuzzy matching tested (100% match on word-order differences)
- ✅ Worksheet duplication preserves formulas

### File to Create
```
scripts/eoy_obgyn_tool.py  (1500-2000 lines estimated)
```

### Run When Done
```bash
cd "C:\Users\noagi\Desktop\JGDC"
python scripts/eoy_obgyn_tool.py
```

---

## 📋 BUILD CHECKLIST

### Phase 1: Data Loading (30-45 min)
- [ ] Import dependencies (gspread, gspread_formatting, rapidfuzz, textual, pandas)
- [ ] Define ProviderRow dataclass
- [ ] Define NewOrderRow dataclass
- [ ] Define Issue dataclass
- [ ] Define ReviewCategory dataclass
- [ ] Implement `load_data(year)` function
  - [ ] Authenticate with gspread
  - [ ] Open 'OBGYN List 2025 - Use This List!'
  - [ ] Load Working List, New Orders, Invalid/Inactive List, STATS
  - [ ] Read cell colors (gspread_formatting)
  - [ ] Parse into ProviderRow objects
  - [ ] Parse into NewOrderRow objects
- [ ] Test: Verify can load data and print row counts

### Phase 2: Validation Functions (1-1.5 hours)
- [ ] Implement `normalize_name()`
- [ ] Implement `normalize_address()`
- [ ] Implement `normalize_phone()`
- [ ] Implement `validate_yellow_to_no()`
  - [ ] Token set ratio fuzzy matching
  - [ ] 70% name, 30% address weighting
  - [ ] Categorize by confidence (95+, 80-94, <80)
- [ ] Implement `validate_no_to_wl()` (reverse check for orphans)
- [ ] Implement `detect_duplicates()`
  - [ ] Group by normalized phone
  - [ ] Detect exact duplicates
  - [ ] Detect networks (similar names, different addresses)
  - [ ] Detect fuzzy duplicates
- [ ] Implement `validate_status_issues()`
  - [ ] Fuschia without vm
  - [ ] Green with "sent"
  - [ ] Red (all flagged)
  - [ ] Not interested with invalid keywords
- [ ] Implement `auto_fix_not_interested()`
- [ ] Implement `detect_non_standard_notes()` (use patterns from NOTES_SAMPLE_ANALYSIS.txt)
- [ ] Implement `categorize_issues()`
- [ ] Test: Run validations on loaded data, print category counts

### Phase 3: Textual UI (2-3 hours)
- [ ] Define `EOYToolApp(App)` main class
  - [ ] CSS styling
  - [ ] Keyboard bindings (F1, F2, F3, Esc)
  - [ ] compose() method (layout)
  - [ ] on_mount() (initialize)
- [ ] Implement category tabs (TabbedContent)
- [ ] Implement DataTable population
- [ ] Implement button handlers
  - [ ] Keep, Delete, Edit, Skip buttons
  - [ ] Batch action buttons
- [ ] Define `EditRowScreen(Screen)`
  - [ ] Input fields for all columns
  - [ ] Notes checkboxes for chunk deletion
  - [ ] Save/Cancel buttons
- [ ] Define `NetworkConfirmScreen(Screen)`
  - [ ] Network name input with default
  - [ ] Table showing network rows
  - [ ] Confirm/Not Network/Mass Invalid buttons
  - [ ] Google Search All button
- [ ] Define `InvalidReasonScreen(Screen)`
  - [ ] Radio buttons for common reasons
  - [ ] Custom reason input
  - [ ] OK/Cancel buttons
- [ ] Define `MatchReviewScreen(Screen)`
  - [ ] Show WL row vs NO match side-by-side
  - [ ] Show confidence percentage
  - [ ] Accept/Not Found/Edit/Google/Skip buttons
- [ ] Test: Run app, navigate tabs, test screens

### Phase 4: Shadow Worksheets (30 min)
- [ ] Implement `create_shadow_worksheets()`
  - [ ] Duplicate Working List → Working List {year}_CLEANUP
  - [ ] Duplicate Invalid/Inactive List → Invalid/Inactive List_CLEANUP
  - [ ] Duplicate STATS → STATS_CLEANUP
- [ ] Implement `update_stats_formulas()`
  - [ ] Find all references to 'Working List {year}'
  - [ ] Replace with 'Working List {year}_CLEANUP'
- [ ] Test: Create shadows, verify STATS formulas updated

### Phase 5: Write Changes (30-45 min)
- [ ] Implement `write_changes_to_shadow()`
  - [ ] Batch update changed cells
  - [ ] Delete duplicate rows (reverse order)
  - [ ] Append to Invalid/Inactive List (with QTY history in notes)
- [ ] Implement `validate_stats_changes()`
  - [ ] Read counts from original STATS
  - [ ] Read counts from STATS_CLEANUP
  - [ ] Compare, flag if >100 difference
- [ ] Implement `rollback_shadows()` (if validation fails)
- [ ] Test: Make changes, write to shadows, verify STATS

### Phase 6: Progress Save/Resume (30 min)
- [ ] Implement `save_progress()`
  - [ ] Save to `eoy_progress_YYYYMMDD_HHMMSS.json`
  - [ ] Include decisions, row changes, current category
- [ ] Implement `load_progress()`
- [ ] Implement `apply_saved_progress()`
  - [ ] Match by practice + phone (not row number)
- [ ] Add F2 keybinding for manual save
- [ ] Add auto-save every 20 decisions
- [ ] Test: Make decisions, save, resume

### Phase 7: Helper Functions (15-30 min)
- [ ] Implement `open_google_search()`
  - [ ] Build URL with webbrowser.open()
  - [ ] Print URL to terminal
- [ ] Implement `suggests_invalid()` (keyword matching)
- [ ] Implement `extract_network_name_default()` (smart default)
- [ ] Implement `replace_network_notation()` (replace old notation)
- [ ] Test: Call helpers with sample data

### Phase 8: Main Entry Point (15 min)
- [ ] Implement `main()` function
  - [ ] Ask for year (default 2025)
  - [ ] Check for existing progress files
  - [ ] Offer to resume if found
  - [ ] Load data
  - [ ] Run validations
  - [ ] Categorize issues
  - [ ] Launch Textual app
  - [ ] Create shadows
  - [ ] Write changes
  - [ ] Validate STATS
  - [ ] Print summary
- [ ] Add `if __name__ == '__main__': main()`
- [ ] Test: Full end-to-end run

---

## 🧪 TESTING STRATEGY

### Unit Test Each Phase
After completing each phase, test independently:

```python
# Example: Test Phase 1
if __name__ == '__main__':
    wl_rows, no_rows, invalid_reasons, stats_sheet = load_data(2025)
    print(f"Loaded {len(wl_rows)} Working List rows")
    print(f"Loaded {len(no_rows)} New Orders rows")
    print(f"Invalid reasons: {invalid_reasons}")
```

### Integration Test
Before full run, test on **TEST Working List 2025** sheet:
- Smaller dataset
- Safe to modify
- Verify shadows created correctly

### Full Test
Run on real **OBGYN List 2025 - Use This List!**:
- User will QA interactively
- Takes 2-4 hours for full review
- Creates _CLEANUP shadows (safe rollback)

---

## 💡 TIPS & GOTCHAS

### 1. Textual Docs
**Reference:** https://textual.textualize.io/

Key widgets to use:
- `DataTable` for row display
- `TabbedContent` & `TabPane` for categories
- `Screen` for modals
- `Button`, `Input`, `TextArea`, `Checkbox`, `RadioSet`

### 2. Color Reading
Use `gspread_formatting.get_effective_format()`:
```python
from gspread_formatting import get_effective_format

fmt = get_effective_format(worksheet, 'A2')
bg = fmt.backgroundColor
r = int(bg.red * 255) if bg.red else 0
g = int(bg.green * 255) if bg.green else 0
b = int(bg.blue * 255) if bg.blue else 0
hex_color = f"#{r:02x}{g:02x}{b:02x}"
```

Colors found in actual data:
- #ffffff (white)
- #ffff00 (yellow)
- #ff00ff (fuschia)
- #ff0000 (red)
- #00ff00 (green)

### 3. Fuzzy Matching
Use `rapidfuzz.fuzz.token_set_ratio()`:
```python
from rapidfuzz import fuzz

score = fuzz.token_set_ratio(str1, str2)  # Returns 0-100
confidence = score / 100.0  # Convert to 0.0-1.0
```

Tested: "Smith Family Practice" vs "Family Practice Smith" = 100% match ✅

### 4. Shadow Worksheets
Create at END only:
- Duplicate preserves formulas ✅ (tested)
- Update ALL formulas in STATS_CLEANUP
- Validate before committing

### 5. Progress Save
Match rows by practice + phone, NOT row number:
- Sheet might change between sessions
- Row numbers unreliable
- Practice + phone = unique enough

### 6. Batch Operations
Always available as buttons (per user request):
- Not just at end of category
- User can trigger any time
- Show confirmation before executing

---

## 🎨 UI DESIGN EXAMPLES

### Main App Layout
```
┌─ EOY Tool ─────────────────────────────────────────────────────┐
│ [Exact Dupes] [Networks] [Yellow 95%+] [Yellow 80-94%] ... ◀── Tabs
├────────────────────────────────────────────────────────────────┤
│ Row  Practice                Phone      Address           QTY  │ ◀─┐
│ ──────────────────────────────────────────────────────────────│   │ DataTable
│ 45   Smith Family Practice   555-1234   123 Main St       50  │   │ (scrollable)
│ 78   Smith Family Practice   555-1234   123 Main St       30  │   │
│                                                                 │ ◀─┘
│ Match in NO: Row 89 (95% confidence) | NO QTY: 50              │ ◀── Status info
├────────────────────────────────────────────────────────────────┤
│ [Keep Row 45] [Keep Row 78] [Keep Both] [Edit] [Batch Delete] │ ◀── Action buttons
│ F1: Help | F2: Save | F3: Batch | Esc: Quit                    │ ◀── Footer
└────────────────────────────────────────────────────────────────┘
```

### Edit Screen
```
┌─ Edit Row 45: Smith Family Practice ───────────────────────────┐
│                                                                  │
│ Practice: [Smith Family Practice___________________________]    │
│ Phone:    [555-1234____________________________________]    │
│ Address:  [123 Main St_________________________________]    │
│ City:     [Houston_____________________________________]    │
│ State:    [TX_] (2 letters)                                      │
│ Zip:      [77001_______________________________________]    │
│ 2025 QTY: [50_________] (empty or 0)                            │
│ Status:   [Successful Order________________________]    │
│ Notes:    [                                            ]    │
│           [                                            ]    │
│           [___________________________________________ ]    │
│                                                                  │
│ Note Chunks (check to delete):                                  │
│ [ ] network notation                                             │
│ [X] vm x2                                                        │
│ [ ] callback tuesday                                             │
│                                                                  │
│ [Save] [Cancel]                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ EDGE CASES TO HANDLE

### 1. New Orders QTY Column Not Found
Search headers for "2025" + "QTY" (case-insensitive)
Fall back to column I if not found

### 2. Color Slightly Different from Expected
Normalize variations:
- #ffff00, #ffff01, #fffef0 → all yellow
- Use tolerance-based matching

### 3. Duplicate with Both in NO
Show special screen, let user decide:
- Keep both (different doctors, same practice)
- Merge (combine QTYs? NO: NO is canon, match WL to NO)
- Pick one

### 4. Network with Disparate Names
If network detection fails (names <85% similar):
- Don't auto-categorize as network
- User can manually group in review

### 5. Progress File from Different Sheet State
Warn user, match by practice+phone instead of row number

---

## 📊 SUCCESS CRITERIA

Tool is successful if:
- ✅ Loads 737 rows from Working List
- ✅ Loads 269 rows from New Orders
- ✅ Validates all 244 yellow rows
- ✅ Detects duplicates and networks
- ✅ Flags status issues
- ✅ Auto-fixes not interested rows
- ✅ User can review issues in categories
- ✅ User can edit any field
- ✅ User can delete note chunks with checkboxes
- ✅ Batch operations work
- ✅ Creates shadow worksheets
- ✅ Writes changes in batch
- ✅ STATS formulas work in _CLEANUP sheet
- ✅ Can save/resume progress
- ✅ Google search helper works
- ✅ Takes 2-4 hours for full review (not 6+ hours manual)

---

## 🚀 FINAL CHECKLIST

Before marking as complete:
- [ ] All phases implemented
- [ ] All Textual screens work
- [ ] Tested on TEST Working List 2025
- [ ] Code commented for future maintenance
- [ ] No hardcoded values (use config/constants)
- [ ] Error handling for API failures
- [ ] Progress auto-saves every 20 decisions
- [ ] Keyboard shortcuts work (F1, F2, F3, Esc)
- [ ] User can quit safely at any point
- [ ] Shadow worksheets created correctly
- [ ] STATS validation works
- [ ] Rollback works if STATS fails

---

## 📞 USER QA PROCESS

After you build:
1. User runs tool
2. User reviews issues in categories
3. User makes decisions (2-4 hours)
4. User verifies STATS_CLEANUP
5. User reports bugs/issues
6. You fix iteratively
7. Final run creates clean shadows
8. User renames shadows (removes _CLEANUP)
9. Manual reset phase begins

---

**GOOD LUCK! Everything is planned. Just follow the architecture and build methodically.**

**Reference docs/EOY_TOOL_ARCHITECTURE_V2.md for ALL implementation details.**
