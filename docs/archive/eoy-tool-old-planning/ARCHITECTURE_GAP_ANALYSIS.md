# EOY Tool Architecture - Gap Analysis

**Purpose:** Critical self-review of architecture before implementation
**Date:** December 2024
**Status:** Identifying gaps, ambiguities, and big leaps

---

## 🚨 CRITICAL GAPS IDENTIFIED

### 1. **ROW COLOR READING - MAJOR GAP**

**THE PROBLEM:**
My architecture assumes I can read background colors from cells via gspread.

**REALITY CHECK:**
```python
# Can gspread actually read cell background colors?
# Standard gspread: cell.value only gives TEXT, not formatting!
```

**INVESTIGATION NEEDED:**
- Does `gspread` support reading cell formatting?
- Do I need `gspread-formatting` library?
- Or do I need to use Google Sheets API v4 directly?

**WHY THIS IS CRITICAL:**
- Yellow/green/red/fuschia detection DEPENDS on reading colors
- If can't read colors, need to rely ONLY on status column
- BUT user said "messy notes and incorrect call status" - so status column is unreliable!

**POSSIBLE SOLUTIONS:**
1. Use `gspread-formatting` library (need to test if it works)
2. Read status column ONLY (but user said it's incorrect - circular problem!)
3. Read color via raw API call (more complex)

**ACTION REQUIRED:**
- Test color reading BEFORE building tool
- If can't read colors, need to revise entire validation logic

---

### 2. **FUZZY MATCHING LIBRARY - NOT INSTALLED**

**THE PROBLEM:**
Architecture uses `fuzzywuzzy` library:
```python
from fuzzywuzzy import fuzz
score = fuzz.token_set_ratio(name1, name2)
```

**REALITY CHECK:**
- Is `fuzzywuzzy` installed? Unknown
- Modern replacement: `rapidfuzz` (faster, maintained)
- Need to verify which library to use

**ACTION REQUIRED:**
- Check if `fuzzywuzzy` installed
- If not, use `rapidfuzz` instead (better maintained)
- Test token_set_ratio with sample data BEFORE coding

---

### 3. **HOVER/KEYPRESS UI IN TERMINAL - BIG LEAP**

**THE PROBLEM:**
Architecture describes "hover-over chunks, right-click or key-press to delete":
```
Notes: network notation; vm x2; sent
       ¹                 ²      ³
Hover over note chunk to highlight, then [d] to delete
```

**REALITY CHECK:**
- Python terminal doesn't support hover/right-click!
- This requires a GUI library or curses
- Simple input() loops can't do this

**WHAT'S ACTUALLY POSSIBLE IN TERMINAL:**
```
Notes: network notation; vm x2; sent
Chunks:
  [1] network notation
  [2] vm x2
  [3] sent
Delete which? (space-separated, e.g., "1 3"): _
```

**ACTION REQUIRED:**
- Simplify to numbered chunks with text input
- OR use `curses` library for terminal UI (more complex)
- OR use `rich` library for better terminal formatting

---

### 4. **SCROLLABLE TABLE IN TERMINAL - BIG LEAP**

**THE PROBLEM:**
Architecture shows scrollable tables with arrow keys:
```
... (scroll with ↑↓ arrows or j/k)
```

**REALITY CHECK:**
- Requires `curses` or similar library
- Not trivial to implement
- Might be overkill for first version

**SIMPLER ALTERNATIVE:**
- Show paginated tables (10 rows at a time)
- Simple "[n]ext page, [p]revious" commands
- Focus on functionality over fancy UI

**ACTION REQUIRED:**
- Decide: curses/rich for fancy UI, or simple pagination?
- User priority: speed of review, not fancy UI
- Start simple, can enhance later

---

### 5. **EDIT FIELD MODAL - COMPLEXITY UNDERESTIMATED**

**THE PROBLEM:**
Architecture shows inline editing with tab navigation:
```
[Practice] Smith Family Practice_____ [Enter to accept]
[Phone]    555-1234__________________ [Tab to next]
```

**REALITY CHECK:**
- Detecting Tab key requires low-level terminal control
- Simple `input()` doesn't support this
- Requires `curses`, `prompt_toolkit`, or similar

**SIMPLER ALTERNATIVE:**
```
Edit row 45:
  [p] Practice: Smith Family Practice
  [n] Phone: 555-1234
  [a] Address: 123 Main St
  [c] City: Houston
  [s] State: TX
  [z] Zip: 77001
  [q] QTY: 50
  [t] Status: Successful Order
  [o] Notes: vm x2

What to edit? (p/n/a/c/s/z/q/t/o or [done]): _
```

**ACTION REQUIRED:**
- Start with simple letter-based field selection
- Can enhance UI later if needed

---

### 6. **SHADOW WORKSHEET CREATION TIMING - AMBIGUOUS**

**THE PROBLEM:**
Architecture says "Create shadow worksheets" in Phase 4 (final write).

**BUT ALSO SAYS:**
Phase 2 updates are "all in memory" - so when do we write to shadows?

**CONFUSION:**
- Do we create shadows at START (Phase 1) or END (Phase 4)?
- If at end: How do we verify STATS formulas before writing?
- If at start: Need to duplicate all data upfront (more API calls)

**CLARIFICATION NEEDED:**
Should be:
1. **Phase 1:** Create shadow worksheets (empty or duplicates?)
2. **Phase 2-3:** Build changes in memory
3. **Phase 4:** Write changes to shadows + verify STATS

**OR:**
1. **Phase 1-3:** Build changes in memory
2. **Phase 4a:** Create shadows (duplicate originals)
3. **Phase 4b:** Apply changes to shadows
4. **Phase 4c:** Verify STATS

**ACTION REQUIRED:**
- Clarify exact sequence
- Test if duplicating worksheet preserves formulas (it should)

---

### 7. **NETWORK NAME EXTRACTION - NO ALGORITHM**

**THE PROBLEM:**
Architecture mentions:
```python
def extract_network_name(provider_names):
    # Find longest common substring
    # Remove location words
    return network_name
```

**BUT NO ACTUAL ALGORITHM!**

**REAL EXAMPLES FROM DATA:**
- "Women's Health Center North" vs "Women's Health Center Downtown"
  → Should extract: "womenshealthcenter"
- But what if names are:
  - "North Women's Health" vs "Women's Health South"?
  - "ABC Medical - Dallas" vs "Dallas ABC Medical"?

**COMPLEXITY:**
- Longest common substring is O(n²)
- Word order matters
- Need to handle variations

**SIMPLER SOLUTION:**
- Just ask user to type network name
- Pre-fill with normalized version of first provider name
- User can edit if wrong

**ACTION REQUIRED:**
- Don't over-engineer
- Let user provide network name (with smart default)

---

### 8. **PROGRESS SAVING - INCOMPLETE DESIGN**

**THE PROBLEM:**
Architecture shows progress JSON structure but doesn't explain:

**QUESTIONS:**
1. What if user edits a row, then quits without saving that category?
2. What if user restarts and data in sheet has changed?
3. How do we match progress to current data (row numbers might shift)?
4. What if user made decisions, then someone else edited the sheet?

**REAL SCENARIO:**
- User reviews 50 rows, saves progress
- Quits for lunch
- Coworker deletes row 30
- User resumes - row numbers are now off by 1!

**SOLUTION NEEDED:**
- Use unique identifiers (phone + name) instead of row numbers?
- Or timestamp check: warn if sheet modified after progress saved?
- Or just accept risk for first version?

**ACTION REQUIRED:**
- Decide on strategy
- Document limitations clearly

---

### 9. **DUPLICATE QTY COMBINING - USER SAID "DEPENDS ON NO"**

**THE PROBLEM:**
User answered Q9: "NO determines what truth is, depends on what it says"

**MY ARCHITECTURE SAYS:**
```python
# When merging duplicates with QTYs
if both_have_orders_in_NO:
    options = ["combine QTYs", "keep both"]
```

**BUT THIS DOESN'T MATCH USER'S ANSWER!**

**USER ACTUALLY SAID:**
- New Orders is canon
- If NO says 50, WL should say 50
- If duplicate has different QTY than NO, flag it

**CORRECT LOGIC:**
1. Check what NO says for each provider
2. WL should match NO
3. If WL duplicate has DIFFERENT QTY than NO → human error, ask user
4. Don't auto-combine anything

**ACTION REQUIRED:**
- Revise duplicate handling logic
- Match WL QTY to NO QTY (NO is source of truth)

---

### 10. **STATS FORMULA VALIDATION - VAGUE**

**THE PROBLEM:**
Architecture says "verify STATS formulas still work" by:
```python
# Check if cells return numeric values
if not value.isdigit():
    error!
```

**BUT THIS IS INSUFFICIENT!**

**WHAT IF:**
- Formula evaluates to "0" when it should be "247"?
- Formula has circular reference?
- Formula references wrong sheet?

**BETTER VALIDATION:**
1. Read counts from original STATS (before changes)
2. Read counts from new STATS_CLEANUP (after changes)
3. Compare: should be similar (allowing for fixed rows)
4. If drastically different (e.g., yellow count goes from 247 to 0), flag error

**ACTION REQUIRED:**
- Implement before/after comparison
- Define acceptable variance (e.g., ±50 rows)

---

### 11. **BATCH OPERATIONS - AMBIGUOUS TRIGGER**

**THE PROBLEM:**
User said: "batch process available as soon as I determine I've exhausted need for manual work"

**WHAT DOES THIS MEAN IN CODE?**
- Show batch option after every row?
- Show batch option only at end of category?
- How does user signal "exhausted manual work"?

**POSSIBLE IMPLEMENTATION:**
After each decision in a category:
```
Action: [a]ccept, [r]eject, [s]kip, [b]atch fix remaining, [q]uit
```

If user chooses [b]atch:
- Apply same action to all remaining rows in category
- Ask for confirmation
- Show summary

**ACTION REQUIRED:**
- Clarify exact UX flow
- Test with mock data

---

### 12. **REVERSE MATCHING (NO → WL) - INCOMPLETE**

**THE PROBLEM:**
User confirmed: "flag NO rows without yellow match (reverse check)"

**MY ARCHITECTURE:**
- Validates yellow rows against NO ✅
- But doesn't implement reverse check! ❌

**MISSING LOGIC:**
```python
def validate_no_to_wl(new_orders_df, working_list):
    """Check if each NO row has matching yellow in WL"""
    orphans = []
    for no_row in new_orders_df:
        # Find matching yellow row in WL
        match = find_in_working_list(no_row, working_list)
        if not match or match.bg_color != '#ffff00':
            orphans.append(no_row)
    return orphans
```

**ACTION REQUIRED:**
- Add reverse validation to Phase 2
- Add category for orphan NO rows
- What should user do with these? (User said: edge case, don't modify NO)

---

### 13. **GOOGLE SEARCH LINK GENERATION - NOT SPECIFIED**

**THE PROBLEM:**
Architecture mentions "provide search link easily available" for duplicates.

**HOW EXACTLY?**

**OPTION A:** Generate URL and print it
```
Google search: https://www.google.com/search?q=Smith+Family+Practice+Houston+TX
```

**OPTION B:** Auto-open in browser
```python
import webbrowser
webbrowser.open(search_url)
```

**OPTION C:** Both (print + offer to open)

**USER'S NEED:**
- Quick verification during review
- Might want to open multiple at once (networks)

**ACTION REQUIRED:**
- Implement URL generation
- Ask user: auto-open or just print?

---

### 14. **INVALID LIST REASON AUTOCOMPLETE - VAGUE**

**THE PROBLEM:**
User said: "optional reason field for moving to invalid, maybe with simple autocomplete form (whatever thats called) for common reasons"

**WHAT'S "AUTOCOMPLETE FORM" IN TERMINAL?**

**PYTHON OPTIONS:**
1. `prompt_toolkit` library (has autocomplete)
2. Simple numbered list of common reasons
3. Type-ahead filtering (complex)

**SIMPLER APPROACH:**
```
Common reasons:
  [1] Closed/Out of business
  [2] Disconnected/Wrong number
  [3] Moved/No longer at address
  [4] Wrong specialty
  [5] Network won't accept
  [6] Other (type reason)

Select reason (1-6): _
```

**ACTION REQUIRED:**
- Start with numbered list
- Can add autocomplete later if needed

---

### 15. **CATEGORY 11: "NON-STANDARD NOTES" - UNDEFINED**

**THE PROBLEM:**
Architecture lists category 11: "Non-standard notes (quick delete chunks)"

**WHAT ARE "NON-STANDARD NOTES"?**
- Notes without issues in other categories?
- Notes with typos?
- Notes that don't follow semicolon format?

**SHOULD THIS EVEN BE A CATEGORY?**

**ALTERNATIVE:**
- Just let user edit notes during other categories
- No need for separate "notes cleanup" category
- Or: make this optional/last step

**ACTION REQUIRED:**
- Clarify what this category is for
- Maybe remove it for first version

---

## 🤔 AMBIGUITIES REQUIRING CLARIFICATION

### A. **Year Detection**
Architecture says "Ask user for year (default: 2025)"

**BUT:**
- How to detect what sheets exist?
- What if "Working List 2026" already exists?
- Should tool auto-detect year from available sheets?

### B. **Resuming with Different Year**
What if progress JSON says year=2025 but user now wants to run for 2026?

### C. **Empty vs "0" in QTY Column**
Architecture treats them differently, but how to READ the difference?
- gspread returns empty cells as "" (empty string)
- User enters "0" as string "0"
- These are different in Python ✅
- But what if cell has formula evaluating to 0?

### D. **Status Column vs Background Color Priority**
If status="Successful Order" but background is WHITE, which is correct?
- Trust status? (but user said it's messy)
- Trust color? (but might not be able to read it)
- Flag conflict?

### E. **Network Notation Format**
User said: "womenshealthcenter network (~3);"

**QUESTIONS:**
- Lowercase? Yes (user confirmed)
- No spaces in name? Yes (based on example)
- Count in parentheses? Yes
- Semicolon at end? Yes
- BUT: what if there's already a note? Append with "; " separator? Yes

**CONFIRMED, BUT EDGE CASE:**
What if note already contains similar network notation?
- "ABC network (~2); ABC network (~3)" ← duplicate notation!
- Should replace old notation, not append

---

## 📊 STEP-BY-STEP IMPLEMENTATION REALITY CHECK

### Phase 1: Initial Setup

```python
def main():
    # 1. Ask for year ✅ Simple
    year = input("Year (default: 2025): ") or "2025"

    # 2. Authenticate gspread ✅ Simple
    gc = gspread.authorize(creds)

    # 3. Open spreadsheet ✅ Simple
    sh = gc.open('OBGYN List 2025 - Use This List!')

    # 4. Load sheets
    wl = sh.worksheet(f'Working List {year}')
    no = sh.worksheet(f'New Orders {year}')
    invalid = sh.worksheet('Invalid/Inactive List')
    stats = sh.worksheet('STATS')

    # 5. Get all data ✅ Simple
    wl_data = wl.get_all_values()  # Returns list of lists
    no_data = no.get_all_values()

    # 6. Get colors ⚠️ PROBLEM!
    # How to read background colors?
    # Need to research gspread-formatting or API v4
```

**BLOCKER:** Step 6 is unclear!

### Phase 2: Validation

```python
def run_validations(wl_data, no_data):
    # Parse data into ProviderRow objects ✅ Straightforward
    providers = parse_working_list(wl_data)

    # 1. Yellow → NO matching
    for p in providers:
        if p.bg_color == '#ffff00':  # ⚠️ Can we read this?
            match, confidence = match_to_no(p, no_data)
            p.matched_no_row = match
            p.match_confidence = confidence

    # 2. Duplicate detection ✅ Clear algorithm
    duplicates = detect_duplicates(providers)

    # 3. Status-based issues ⚠️ Depends on color reading
    status_issues = validate_status(providers)

    # 4. Not interested auto-fix ✅ Clear logic
    auto_fix_not_interested(providers)

    # 5. Categorize ✅ Straightforward
    categories = categorize_issues(providers)

    return categories
```

**BLOCKER:** Color reading in steps 1 and 3!

### Phase 3: Interactive Review

```python
def interactive_review(categories):
    for category in categories:
        print(f"\n=== {category.name} ===")
        print(f"{len(category.issues)} issues found")

        for i, row in enumerate(category.issues):
            # Show row details ✅ Simple
            print(f"\nRow {row.row_num}: {row.practice}")
            print(f"  Phone: {row.phone}")
            print(f"  Address: {row.address}")

            # Show actions ⚠️ Complex UX
            # How to make this smooth?
            action = input("Action [a/r/s/e/q]: ")

            if action == 'e':
                edit_row(row)  # ⚠️ How complex should this be?
            elif action == 'b':
                batch_fix_remaining(category, i)  # ✅ Clear
            # ... etc
```

**CHALLENGE:** Making UX smooth without over-engineering

### Phase 4: Write Changes

```python
def write_changes(gc, sh, year, all_changes):
    # 1. Create shadow worksheets ⚠️ WHEN?
    # Option A: Duplicate entire worksheet (preserves formulas)
    wl_orig = sh.worksheet(f'Working List {year}')
    wl_cleanup = wl_orig.duplicate(
        new_sheet_name=f'Working List {year}_CLEANUP'
    )

    # 2. Apply changes ⚠️ How exactly?
    # Batch update specific cells? Or rewrite entire sheet?

    # 3. Verify STATS ⚠️ Need better validation

    # 4. Rollback if error ✅ Clear logic
```

**QUESTIONS:**
- Duplicate preserves formulas? (should test)
- Update specific cells or rewrite all? (batch update specific cells is faster)

---

## 🎯 BIG LEAPS IDENTIFIED

### 1. **TERMINAL UI COMPLEXITY**
**LEAP:** Assuming rich terminal UI (hover, scroll, tabs)
**REALITY:** Need simpler approach or library

### 2. **COLOR READING ASSUMPTION**
**LEAP:** Assuming gspread can read colors easily
**REALITY:** Might need extra library or API calls

### 3. **FUZZY MATCHING LIBRARY**
**LEAP:** Using specific library without testing
**REALITY:** Need to verify installed and working

### 4. **NETWORK NAME EXTRACTION**
**LEAP:** Automatic extraction algorithm
**REALITY:** Just ask user to provide name

### 5. **PROGRESS RESUME ROBUSTNESS**
**LEAP:** Assuming row numbers stay constant
**REALITY:** Sheet might change between sessions

---

## ✅ ACTION ITEMS BEFORE CODING

### CRITICAL (Must resolve first):
1. ⚠️ **Test gspread color reading** - Can we read background colors?
2. ⚠️ **Install and test fuzzy matching** - fuzzywuzzy or rapidfuzz?
3. ⚠️ **Simplify terminal UI** - No hover/scroll for v1, use pagination
4. ⚠️ **Clarify shadow worksheet timing** - Create at start or end?
5. ⚠️ **Fix duplicate QTY logic** - Match to NO, don't auto-combine

### IMPORTANT (Simplify before coding):
6. ⚠️ **Simplify edit UI** - Letter-based field selection, not tabs
7. ⚠️ **Simplify notes chunk deletion** - Numbered list, not hover
8. ⚠️ **Remove network name extraction** - User provides name
9. ⚠️ **Simplify Invalid reason input** - Numbered list, not autocomplete
10. ⚠️ **Add reverse NO→WL validation** - Missing from architecture

### NICE TO HAVE (Can defer):
11. ⚠️ **Remove/clarify category 11** - Non-standard notes unclear
12. ⚠️ **Improve STATS validation** - Before/after comparison
13. ⚠️ **Add Google search helper** - Auto-open or just print URL?

---

## 🎬 RECOMMENDED NEXT STEPS

1. **Create test script** to verify:
   - Can gspread read cell colors?
   - Is fuzzywuzzy/rapidfuzz installed?
   - Does worksheet.duplicate() preserve formulas?

2. **Revise architecture** based on findings:
   - Simplify UI expectations
   - Remove big leaps
   - Fill in gaps

3. **Build minimal viable version**:
   - Focus on core validation logic
   - Simple terminal UI (no fancy features)
   - Get it working, enhance later

4. **Test with TEST Working List 2025** before real data

---

## 📝 CONFUSING/AMBIGUOUS ITEMS

1. **"Non-standard notes" category** - What qualifies as non-standard?
2. **Batch operation trigger** - When exactly does user invoke batch mode?
3. **Shadow worksheet creation timing** - Start or end of process?
4. **Progress resume with changed data** - How to handle row number shifts?
5. **Status vs color priority** - Which to trust when they conflict?
6. **Network notation replacement** - Replace old notation or append?
7. **Orphan NO rows** - What should user do with them?
8. **QTY combining logic** - User said "depends on NO" but architecture shows auto-combine

---

**CONCLUSION:** Architecture has solid foundation but makes several big leaps and has critical gaps around color reading and UI complexity. Need to test assumptions and simplify before coding.
