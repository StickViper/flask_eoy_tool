# EOY Tool Implementation Plan

**Last Updated:** 2025-12-05

## Overview

This document captures the implementation roadmap for completing the EOY (End of Year) Cleanup Tool. The tool is **engineer-only** - used by the technical maintainer to review and clean up Working List data, then export for manual paste back into Google Sheets.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GOOGLE SHEETS (Read-Only Source)                           │
│  - Load once at session start                               │
│  - No writes back during session                            │
└─────────────────────────────────────────────────────────────┘
                          ↓ Load
┌─────────────────────────────────────────────────────────────┐
│  LOCAL STATE (JSON)                                         │
│  - All edits happen here                                    │
│  - Undo/redo stacks (200 action limit)                      │
│  - Auto-save to JSON periodically                           │
│  - Resume from JSON on reload                               │
└─────────────────────────────────────────────────────────────┘
                          ↓ Export
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT OPTIONS                                             │
│  A) Download CSV file                                       │
│  B) Copy-pastable CSV text (comma-delimited)                │
│  Engineer manually pastes into Google Sheets                │
└─────────────────────────────────────────────────────────────┘
```

---

## Categories (12 Total)

### Urgency Ranking

| Urgency | Categories | Reason |
|---------|------------|--------|
| 🔴 **CRITICAL** | exact_dupes, yellow_low, orphan_no, red_invalid | Data integrity, must fix |
| 🟡 **REVIEW** | networks, fuzzy_dupes, yellow_80, green_sent, not_interested_invalid | Needs judgment call |
| 🟢 **VERIFY** | yellow_95, fuschia_vm, manual_review | Low priority, just confirm |

### Category Details

| # | ID | Name | Description | Primary Action |
|---|-----|------|-------------|----------------|
| 1 | `exact_dupes` | Duplicates | Identical rows (same name, address, phone) | keep_first_delete_rest |
| 2 | `networks` | Networks | Same phone, similar names, different locations | confirm_network |
| 3 | `fuzzy_dupes` | Possible Dupes | Similar rows that might be duplicates | merge_rows |
| 4 | `yellow_95` | Orders (Exact Match) | ≥95% confidence match to New Orders | accept_all |
| 5 | `yellow_80` | Orders (Good Match) | 80-94% confidence match | manual review |
| 6 | `yellow_low` | Orders (Not Found) | Yellow but <80% match to New Orders | mark_not_found |
| 7 | `orphan_no` | Unmatched Orders | New Orders without yellow WL match | orphan_no_handler |
| 8 | `green_sent` | Email Sent | Green status with 'sent' in notes | convert_to_not_interested |
| 9 | `fuschia_vm` | Voicemails | Voicemail status, check notes | add_vm_note |
| 10 | `red_invalid` | Potentially Invalid | Red status, review for Invalid List | move_to_invalid |
| 11 | `not_interested_invalid` | Not Int (Invalid?) | White but notes suggest closed/invalid | move_to_invalid |
| 12 | `manual_review` | Manual Review | Catch-all for complex edge cases | ALL actions available |

---

## Implementation Order

| Priority | Task | Status |
|----------|------|--------|
| 1 | Verify test suite runs with real data | ✅ Complete |
| 2 | Manual Review category (Category 12) | ✅ Complete |
| 3 | orphan_no_handler logic | ✅ Complete |
| 4 | Inline editing (double-click) | ⬜ Pending |
| 5 | Undo/redo restoration | ⬜ Pending |
| 6 | merge_rows UI | ⬜ Pending |
| 7 | confirm_network with auto-suggest | ⬜ Pending |
| 8 | Urgency progress bar | ⬜ Pending |
| 9 | Export functionality (CSV + copy-paste) | ⬜ Pending |

---

## Detailed Implementation Approach

### Priority 1: Verify Test Suite

**Approach:**
1. Run `python tests/load_real_data.py` to generate/refresh cache
2. Run `cd scripts && python -m pytest ../tests/ -v`
3. Verify all 124 tests pass
4. Note any failures for investigation

**No decisions needed** - purely verification.

---

### Priority 2: Manual Review Category

**Current State:**
- Category 12 referenced but not in `categorize_issues()` function
- No mechanism to manually send rows to this category

**Approach:**
1. Add `manual_review` to category list in `categorize_issues()` (line ~920)
2. Create `/api/send_to_manual_review` action handler
3. Make ALL actions available in this category

**Code Location:** `eoy_tool.py` lines 816-946

**Implementation:**
```python
ReviewCategory(
    id="manual_review",
    name="Manual Review",
    description="Complex cases requiring engineer judgment",
    row_nums=[],
    allow_batch=False,
    primary_action=None,
    secondary_actions=[
        "edit", "delete", "change_status", "move_to_invalid",
        "merge", "add_vm_note", "mark_reviewed"
    ]
)
```

### ❓ DECISIONS NEEDED - Manual Review:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 2.1 | **How are rows added?** | A) Only via orphan_no_handler B) User can manually send any row C) Both | C - Both |
| 2.2 | **"mark_reviewed" action?** | Mark as "reviewed, no changes needed" for progress tracking | Yes, add it |
| 2.3 | **Remove resolved rows from category?** | A) Remove when action taken B) Keep but mark resolved | A - Remove |

---

### Priority 3: orphan_no_handler

**Current State:**
- `orphan_no` category populated during validation
- Invalid/Inactive List loaded at line 222 but not used for matching
- No handler to process orphan rows

**Approach:**
1. For each orphan NO row, fuzzy match against Invalid/Inactive List
2. If match found (≥80%) → show match info, suggest resolution
3. If no match → send to Manual Review category

**Flow:**
```
orphan NO row
    ↓
fuzzy match vs Invalid/Inactive List
    ↓
┌─ Match ≥80%?
│   ├─ YES → Show: "Matches [Invalid Row]. Reason: [notes]"
│   │         Actions: "Confirm Match" | "Create WL Row" | "Manual Review"
│   │
│   └─ NO  → Auto-send to Manual Review
```

### ❓ DECISIONS NEEDED - orphan_no_handler:

| # | Question | Options | Blocking? |
|---|----------|---------|-----------|
| 3.1 | **Invalid List columns?** | What columns exist? (practice, address, phone?, reason?) | **YES - need this info** |
| 3.2 | **Match threshold?** | A) 80% B) 70% C) 90% | No - default 80% |
| 3.3 | **"Create WL Row" action?** | Create new WL row from orphan NO | No - can skip initially |
| 3.4 | **What if match confirmed?** | A) Delete orphan B) Mark resolved C) Link to WL row | No - default B |

---

### Priority 4: Inline Editing

**Current State:**
- No inline editing exists
- Edits only via bulk action buttons

**Approach:**
1. Add `dblclick` event listener to editable cells
2. Replace cell with `<input>` (text) or `<select>` (status)
3. Save on blur/Enter, cancel on Escape
4. Call `/api/edit_field` to persist

**Code Location:**
- Frontend: New `static/js/editing.js` or inline in `category.html`
- Backend: New route `/api/edit_field`

### ❓ DECISIONS NEEDED - Inline Editing:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 4.1 | **Editable fields?** | practice, phone, address, city, state, zip, status, notes, qty_2025 | All except row_num, bg_color |
| 4.2 | **Phone validation?** | A) None B) 10 digits C) Normalize to ###-###-#### | A - None (light touch) |
| 4.3 | **State validation?** | A) None B) 2 letters only C) Valid US state | A - None |
| 4.4 | **QTY fields editable?** | A) All three B) Only 2025 C) None | B - Only 2025 |
| 4.5 | **Visual feedback on save?** | A) None B) Flash green C) Toast message | B - Flash green |

---

### Priority 5: Undo/Redo Restoration

**Current State:**
- Stacks exist: `state.undo_stack`, `state.redo_stack`
- `add_to_undo_stack()` works
- TODO stubs at lines 1105, 1124 - no restoration logic

**Approach:**
1. Enhance `before_state` to capture full row data
2. Create `restore_row_state()` helper
3. Implement restoration in `api_undo()` and `api_redo()`
4. Handle each action_type appropriately

**Code Location:** `eoy_tool.py` lines 1095-1131

**Restoration Logic:**
```python
def restore_row_state(row_state):
    row = find_row(row_state['row_num'])
    if not row:
        return False
    for field, value in row_state['fields'].items():
        if hasattr(row, field):
            setattr(row, field, value)
    row.field_edits = row_state.get('field_edits', {})
    row.action = row_state.get('action', None)
    return True
```

### ❓ DECISIONS NEEDED - Undo/Redo:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 5.1 | **Persist across refresh?** | A) Session only B) Save in JSON | A - Session only |
| 5.2 | **Undo deleted rows?** | A) Full restore B) Cannot undo | A - Full restore |
| 5.3 | **Undo limit?** | A) Keep 50 B) Increase to 200 | B - Increase to 200 |
| 5.4 | **Cross-category undo?** | Undo in Cat A affects Cat B | Allow - actions are global |

---

### Priority 6: merge_rows UI

**Current State:**
- `fuzzy_dupes` category exists
- No merge functionality

**Approach:**
1. Create merge modal UI
2. Show rows side-by-side
3. User selects field values from any row
4. Option to merge notes
5. Result: one row survives, others marked deleted

**UI Wireframe:**
```
┌─────────────────────────────────────────────────────────────┐
│ MERGE ROWS                                         [X Close]│
├─────────────────────────────────────────────────────────────┤
│ Select values to keep:                                      │
│                                                             │
│ Field      │ Row 45          │ Row 89          │ Custom    │
│ ───────────┼─────────────────┼─────────────────┼───────────│
│ Practice   │ ● Smith Family  │ ○ Smith Fam     │ ○ [     ] │
│ Phone      │ ● 512-555-1234  │ ○ 512-555-1234  │           │
│ Address    │ ○ 123 Main St   │ ● 123 Main      │ ○ [     ] │
│ Notes      │ ☐ vm x2         │ ☑ callback      │ [Merge ☑] │
│                                                             │
│                            [Cancel]    [Preview]    [Merge] │
└─────────────────────────────────────────────────────────────┘
```

### ❓ DECISIONS NEEDED - merge_rows:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 6.1 | **UI style?** | A) Modal popup B) Inline expansion C) Separate page | A - Modal |
| 6.2 | **Notes handling?** | A) Concat with semicolon B) Pick one C) Free edit | A - Concat |
| 6.3 | **Surviving row?** | A) Lowest row_num B) User chooses C) Auto-pick best | B - User chooses |
| 6.4 | **Merged rows fate?** | A) Mark deleted B) Remove from state C) Archive | A - Mark deleted |
| 6.5 | **Groups of 3+?** | A) Merge all at once B) Pairwise | A - All at once |

---

### Priority 7: confirm_network

**Current State:**
- `networks` category populated
- `confirm_network` action exists but incomplete

**Approach:**
1. Auto-derive name from common practice name substrings
2. Show preview modal
3. User can edit name, select/deselect rows
4. Add network notation to all selected rows

**Name Derivation Algorithm:**
```python
def derive_network_name(rows):
    # Get words from all practice names
    word_sets = [set(r.practice.lower().split()) for r in rows]

    # Find common words
    common = word_sets[0].intersection(*word_sets[1:])

    # Remove filler words
    filler = {'the', 'of', 'and', 'clinic', 'medical', 'center', 'practice'}
    common = common - filler

    return ''.join(sorted(common)) or 'network'
```

### ❓ DECISIONS NEEDED - confirm_network:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 7.1 | **Name derivation?** | A) Common substrings B) Longest prefix C) User always enters | A - Common substrings |
| 7.2 | **QTY handling?** | A) Sum all → first row B) Keep as-is C) User decides | B - Keep as-is |
| 7.3 | **Notation format?** | `networkname network (~3);` | Keep existing format |
| 7.4 | **Apply to which rows?** | A) All in network B) Only first | A - All rows |

---

### Priority 8: Urgency Progress Bar

**Current State:**
- No progress UI

**Approach:**
1. Calculate counts by urgency level
2. Track "resolved" (rows with action taken)
3. Render segmented bar in sidebar
4. Update on each action

**Progress Calculation:**
```python
def calculate_progress():
    critical = ['exact_dupes', 'yellow_low', 'orphan_no', 'red_invalid']
    review = ['networks', 'fuzzy_dupes', 'yellow_80', 'green_sent', 'not_interested_invalid']
    verify = ['yellow_95', 'fuschia_vm', 'manual_review']

    counts = {'critical': 0, 'review': 0, 'verify': 0, 'resolved': 0}

    for cat in state.categories:
        for row_num in cat.row_nums:
            row = find_row(row_num)
            if row.action:
                counts['resolved'] += 1
            elif cat.id in critical:
                counts['critical'] += 1
            # ... etc

    return counts
```

### ❓ DECISIONS NEEDED - Progress Bar:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 8.1 | **What = "resolved"?** | A) Any action B) Specific actions C) Explicit mark | A - Any action |
| 8.2 | **Clickable?** | Click segment → filter categories | Nice to have, not required |
| 8.3 | **Location?** | A) Sidebar B) Header C) Both | A - Sidebar |
| 8.4 | **Multi-category rows?** | A) Count in highest urgency B) Count in each | A - Highest urgency |

---

### Priority 9: Export Functionality

**Current State:**
- No export exists

**Approach:**
1. Create `/api/export` endpoint
2. Generate CSV: all WL columns + Action Taken
3. Two modes: file download OR clipboard copy
4. No header row (paste into existing sheet)

**CSV Format:**
```
Smith Family,512-555-1234,123 Main St,Austin,TX,78701,10,15,20,Successful Order,vm x2,VERIFIED
```

**Action Taken Values:**
- `VERIFIED` - accepted match
- `DELETED` - marked for deletion
- `MERGED` - result of merge (other rows say `MERGED_INTO_ROW_X`)
- `NETWORK_CONFIRMED` - network notation added
- `EDITED` - fields modified
- `MOVED_TO_INVALID` - marked for invalid list
- `NO_CHANGE` - reviewed but unchanged

### ❓ DECISIONS NEEDED - Export:

| # | Question | Options | My Default |
|---|----------|---------|------------|
| 9.1 | **Include deleted rows?** | A) Yes with DELETED B) Omit entirely C) Separate file | **NEED ANSWER** |
| 9.2 | **Export scope?** | A) All rows B) Modified only C) User choice | A - All rows |
| 9.3 | **Column order?** | Same as Google Sheet | Yes |
| 9.4 | **Quote handling?** | Quote if contains comma | Standard CSV rules |
| 9.5 | **Newlines in notes?** | A) Replace with space B) Keep C) Replace with ; | A - Replace with space |

---

## Key Decisions Already Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Write strategy | Export CSV/copy-paste | No real-time Sheets writes needed |
| Undo scope | Bulk actions as one unit | Matches user intent |
| Edit trigger | Double-click | Intuitive, avoids accidental edits |
| Status editing | Dropdown | Enforces valid values |
| Export format | Full WL + Action Taken column | Complete audit trail |

---

## Technical Specifications

### Status Values (Exact Match Required)
```
'Successful Order'     → #ffff00 (yellow)
'Voicemail/No Answer'  → #ff00ff (fuschia)
'Requested Email'      → #00ff00 (green)
'Potentially Invalid'  → #ff0000 (red)
'Not interested'       → #ffffff (white)
''                     → #ffffff (white/empty)
```

### Fuzzy Matching
- **Weights:** 70% Name / 30% Address
- **Thresholds:** High ≥ 0.95, Mid ≥ 0.80
- **Algorithm:** token_set_ratio (handles word order)

### Network Detection
- **Logic:** Same Phone + Different Address + Similar Name (≥85%)
- **Notation:** Append (~#) to notes (e.g., `womenshealthcenter network (~3);`)

### ProviderRow Fields (from eoy_tool.py lines 40-91)
```python
# Core data (from sheet)
row_num, practice, phone, address, city, state, zip
qty_2023, qty_2024, qty_2025, status, notes, bg_color

# Validation results (computed)
issues, matched_no_row, match_confidence
duplicate_group_id, network_name

# User decisions (mutable)
action, field_edits
```

---

## Summary: Pending Decisions

### 🔴 BLOCKING (Need Answer to Proceed)

| # | Question |
|---|----------|
| 3.1 | **Invalid/Inactive List columns** - What columns exist? |
| 9.1 | **Deleted rows in export** - Include or omit? |

### 🟡 SHOULD ANSWER (Affects Implementation)

| # | Question | My Default |
|---|----------|------------|
| 2.1 | Manual review: how to add rows? | Both auto + manual |
| 6.1 | Merge UI: modal or inline? | Modal |
| 6.3 | Merge: which row survives? | User chooses |

### 🟢 CAN USE DEFAULTS

All other questions have reasonable defaults noted. Will proceed with defaults unless you specify otherwise.

---

## Files Reference

| File | Purpose | Key Lines |
|------|---------|-----------|
| `scripts/eoy_tool.py` | Main Flask application | 1580 lines |
| ↳ Data models | ProviderRow, NewOrderRow, ReviewCategory | 40-140 |
| ↳ Categorization | categorize_issues() | 816-946 |
| ↳ Undo/Redo stubs | api_undo(), api_redo() | 1095-1131 |
| ↳ Action handlers | /api/* routes | 1133-1550 |
| `templates/category.html` | Main review interface | 837 lines |
| `static/js/shortcuts.js` | Keyboard shortcuts | 168 lines |
| `tests/conftest.py` | Test fixtures | |
| `tests/load_real_data.py` | Load real data cache | |

---

## Next Steps

1. **Answer blocking questions** (3.1 Invalid List columns, 9.1 deleted rows)
2. Run test verification (Priority 1)
3. Begin implementation at Priority 2
