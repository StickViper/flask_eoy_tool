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

## Implementation Phases

### Phase 1: Core Functionality (Backend)

#### 1.1 Manual Review Category (Category 12)
- **Purpose:** Catch-all for orphans and complex edge cases
- **Actions:** ALL actions available (edit, status, delete, merge, move to invalid)
- **Population:** orphan_no rows that don't match Invalid List

#### 1.2 orphan_no_handler
- **Logic:**
  1. Fuzzy match NO row against Invalid/Inactive List
  2. If match found → check Invalid notes for QTY → resolve
  3. If no match → send to Manual Review category

#### 1.3 merge_rows (Fuzzy Dupes)
- **UI Requirements:**
  - User selects which row is "canonical"
  - User picks specific fields to keep from each row
  - Optional: merge notes with semicolon separator
  - Result: one row with best data from all

#### 1.4 confirm_network
- **Logic:**
  - Auto-derive network name from common substrings
  - Show preview: "Suggested name: womenshealthcenter"
  - Allow user to select/deselect rows in network
  - Update QTY defaults based on selections

### Phase 2: Undo/Redo Completion

#### 2.1 State Capture Enhancement
```python
before_state = {
    'row_num': row.row_num,
    'fields': row.to_dict(),
    'field_edits': copy.deepcopy(row.field_edits),
    'action': row.action,
    'issues': copy.deepcopy(row.issues)
}
```

#### 2.2 Restoration Logic
- Simple actions: Use specific restoration handlers
- Complex actions: Use generic field restoration
- Constraint: Must restore field_edits dict and action flags accurately

### Phase 3: UX (Frontend)

#### 3.1 Inline Editing
- **Trigger:** Double-click cell
- **Behavior:**
  - Text fields → input box
  - Status → dropdown with 5 options
  - Save on: Enter, blur, Tab
  - Cancel on: Escape

#### 3.2 Urgency Progress Bar
```
┌────────────────────────────────────────────┐
│ 🔴 Critical: 45  │ 🟡 Review: 123  │ 🟢 Low: 67 │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│ 19% complete (45 of 235 resolved)          │
└────────────────────────────────────────────┘
```

#### 3.3 Export
- **Options:**
  - A) Download CSV button → triggers file download
  - B) Copy to Clipboard button → copies comma-delimited text
- **Format:** Same columns as WL + "Action Taken" at end
- **No header row** (user pastes into existing sheet)

---

## Implementation Order

| Priority | Task | Status |
|----------|------|--------|
| 1 | Verify test suite runs with real data | ⬜ Pending |
| 2 | Manual Review category (Category 12) | ⬜ Pending |
| 3 | orphan_no_handler logic | ⬜ Pending |
| 4 | Inline editing (double-click) | ⬜ Pending |
| 5 | Undo/redo restoration | ⬜ Pending |
| 6 | merge_rows UI | ⬜ Pending |
| 7 | confirm_network with auto-suggest | ⬜ Pending |
| 8 | Urgency progress bar | ⬜ Pending |
| 9 | Export functionality (CSV + copy-paste) | ⬜ Pending |

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Write strategy | Export CSV/copy-paste | No real-time Sheets writes needed |
| Undo scope | Bulk actions as one unit | Matches user intent |
| Undo limit | 200 actions | Sufficient for 2-4 hour sessions |
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

---

## Change Tracker Structure

```python
change_log = [
    {
        'id': 1,
        'timestamp': '2025-12-05T14:30:00',
        'action_type': 'delete_rows',
        'description': 'Deleted 5 duplicate rows',
        'row_nums': [45, 67, 89, 123, 456],
        'before_states': [...],  # For undo
        'exportable': True       # Include in Action Taken column
    }
]
```

---

## User Types

| Role | Who | Tools Used |
|------|-----|------------|
| **Volunteers (3)** | Phone callers | Google Sheets directly |
| **Shipping (1)** | Fulfillment | New Orders sheet |
| **Engineer (1)** | Technical maintainer | Flask EOY tool, Apps Script |

**Note:** EOY Tool is engineer-only. Volunteers never see or use it.

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/eoy_tool.py` | Main Flask application (~1580 lines) |
| `templates/category.html` | Main review interface |
| `static/js/shortcuts.js` | Keyboard shortcuts |
| `tests/conftest.py` | Test fixtures |
| `tests/load_real_data.py` | Load real data cache |

---

## Next Steps

1. Run `python tests/load_real_data.py` to generate cache
2. Run `cd scripts && python -m pytest ../tests/ -v` to verify
3. Begin implementation at Priority 2 (Manual Review category)
