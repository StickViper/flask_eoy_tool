# EOY Tool Specification & Planning

**File:** `scripts/eoy_obgyn_tool.py`
**Purpose:** Local Python tool to replace Apps Script EOY validation
**Status:** Planning phase - need answers to questions below before building

---

## Overview

**Problem:** Apps Script EOY validation flags ALL 244 yellow rows as "not found" in New Orders (100% false positive rate)

**Solution:** Build local Python tool with gspread that:
1. Loads Working List + New Orders instantly (no polling)
2. Runs all validations with detailed confidence scores
3. Shows issues interactively one-by-one
4. User makes decisions (fix/skip/delete/move to Invalid)
5. Batch updates sheet at end (one write operation)

**Benefits:**
- ✅ No client-side polling lag
- ✅ No 6-minute execution limit
- ✅ Easy to debug (print confidence scores, inspect data)
- ✅ Testable (run on test data in 2 seconds)
- ✅ No browser cache issues
- ✅ Can process 1000s of rows efficiently

---

## Data Model (from sheets)

### Working List 2025 (738 rows)
| Column | Name | Content | Notes |
|--------|------|---------|-------|
| A | Practice | Office name | Or "Office Name" |
| B | Number | Phone | Or "Phone Number" |
| C | Address | Street address | Full street |
| D | Town | City | Or "City" |
| E | State | 2-letter code | TX, WA, CO, PA |
| F | Zip | 5-digit | String |
| G-I | QTY | 2023/2024/2025 | **Empty vs 0 matters!** |
| J | CALL STATUS | Dropdown | Triggers color |
| K | Notes | Freeform text | Semicolon-separated |
| ? | Background Color | #ffff00, #ff00ff, etc. | Row color |

**Status → Color mapping:**
- Yellow (#ffff00): "Successful Order"
- Green (#00ff00): "Requested Email"
- Red (#ff0000): "Potentially Invalid"
- Fuschia (#ff00ff): "Voicemail/No Answer"
- White (#ffffff): "Not interested" OR empty

**Key insight:** Empty QTY ≠ 0
- **Empty** = uncalled or unresolved
- **0** = explicitly requested zero materials

### New Orders 2025 (269 rows)
| Column | Name | Content | Notes |
|--------|------|---------|-------|
| A | Practice/Office Name | Office name | NO PHONE NUMBER |
| C | Address | Street address | For matching |
| D | Town/City | City | For matching |
| E | State | 2-letter | For matching |
| F | Zip | 5-digit | For matching |
| ?  | QTY 2025 | Quantity | May be in different column |

**CRITICAL:** New Orders does NOT have phone numbers (by design for delivery)

---

## Validation Logic

### 1. Yellow → New Orders Validation

**Goal:** Verify all 244 yellow rows in Working List exist in New Orders

**Fuzzy Matching (no phone):**
```python
def fuzzy_match_score(wl_row, no_row):
    """
    Calculate match confidence between Working List and New Orders rows
    Returns: 0.0 to 1.0
    """
    # Name matching (70% weight)
    name_score = fuzzy_string_match(
        wl_row['Practice'],
        no_row['Practice']
    )

    # Address matching (30% weight)
    address_score = fuzzy_string_match(
        wl_row['Address'],
        no_row['Address']
    )

    # Total confidence
    confidence = (name_score * 0.7) + (address_score * 0.3)

    return confidence

def find_best_match(wl_row, new_orders_df):
    """
    Find best matching row in New Orders
    Returns: (best_match_row, confidence, match_index) or (None, 0.0, None)
    """
    best_confidence = 0.0
    best_match = None
    best_index = None

    for idx, no_row in new_orders_df.iterrows():
        confidence = fuzzy_match_score(wl_row, no_row)
        if confidence > best_confidence:
            best_confidence = confidence
            best_match = no_row
            best_index = idx

    return best_match, best_confidence, best_index
```

**Threshold:**
- **≥ 95%:** Exact match ✅
- **80-94%:** High confidence ⚠️ (review)
- **60-79%:** Medium confidence ⚠️⚠️ (likely mismatch)
- **< 60%:** Not found ❌

**Questions:**
1. **What fuzzy string matching algorithm?**
   - Option A: Simple ratio (fast)
   - Option B: Token set ratio (handles word order)
   - Option C: Partial ratio (handles substrings)
   - **My recommendation:** Token set ratio (handles "Smith Family Practice" vs "Family Practice Smith")

2. **Show ALL potential matches or just best?**
   - If yellow row scores 85% with one NO row and 82% with another, show both?
   - **My recommendation:** Show top 3 if within 10% of each other

3. **What if New Orders row matches MULTIPLE yellow rows?**
   - 269 New Orders but 244 yellow = 25 NO rows without yellow match (expected?)
   - Should tool flag this reverse mismatch?
   - **My recommendation:** Yes, flag both directions

### 2. Duplicate Detection

**Check for:**
- Same phone (exact match)
- Same name + similar address (fuzzy)
- Same address + similar name (fuzzy)

**Network detection:**
- Same phone + different addresses = network
- Format: "smithclinic network (~3);" in Notes

**Questions:**
4. **Phone number normalization?**
   - Strip: (123) 456-7890 → 1234567890
   - Or keep as-is and require exact match?
   - **My recommendation:** Normalize (remove spaces, dashes, parens)

5. **Network notation - overwrite existing or append?**
   - If Notes already has text, append "; networkname network (~3)"?
   - **My recommendation:** Append with semicolon separator

### 3. Status-Based Issues

**Fuschia (Voicemail/No Answer):**
- If Notes missing "vm x2" or similar: flag for review
- Action: User adds "vm x2" or "vm x3" note
- QTY stays **empty** (not 0)

**Green (Requested Email):**
- If Notes contains "sent": likely no response → convert to "not interested"
- Action: Change status to "Not interested", set QTY=0, add "no response" to Notes

**Red (Potentially Invalid):**
- Verify if actually invalid (might just be wrong number)
- Action options:
  - Fix phone number (if found correct one)
  - Move to Invalid/Inactive List
  - Delete row

**Empty (Uncalled):**
- No action needed
- QTY stays **empty**

**Questions:**
6. **Green email handling - automatic or manual?**
   - If Notes contains "sent" (case-insensitive), automatically suggest converting to "not interested"?
   - Or always show and ask?
   - **My recommendation:** Show with suggestion, user confirms

7. **Moving to Invalid/Inactive List - what data?**
   - Copy entire row? Or just specific columns?
   - What sheet name? "Invalid/Inactive List" or "OBGYN Invalid 2025"?
   - **My recommendation:** Copy columns A-F + reason, to sheet "Invalid/Inactive List"

### 4. "Not Interested" Validation

**Rule:** Status="Not interested" MUST have:
- Notes contains "not interested" (case-insensitive)
- QTY = 0 (explicitly zero, not empty)

**Auto-fix:**
- Missing "not interested" in Notes → append "; not interested"
- QTY empty or other value → set to 0

**Questions:**
8. **Auto-fix without asking?**
   - This is low-risk (just adding missing note/QTY)
   - Show summary at end ("Fixed 15 not interested issues")?
   - **My recommendation:** Auto-fix silently, show summary

---

## User Interaction Flow

### Interactive Terminal UI

```
====================================================================
OBGYN EOY TOOL - WORKING LIST 2025
====================================================================

Loading data...
✅ Working List: 738 rows
✅ New Orders: 269 rows

Running validations...
✅ Yellow validation: 87 issues found
✅ Duplicate detection: 12 issues found
✅ Status issues: 23 issues found
✅ Not interested: 8 issues (auto-fixed)

====================================================================
REVIEW ISSUES (122 total)
====================================================================

Issue 1/122 [Yellow Validation]
  Row: 45
  Provider: Smith Family Practice
  Address: 123 Main St, Houston, TX 77001

  Best match in New Orders (row 89):
    Name: Smith Family Practice (95% match)
    Address: 123 Main Street, Houston, TX 77001 (92% match)
    → Overall confidence: 94%

  [a]ccept match, [r]eject (not found), [s]kip, [q]uit? a
  ✅ Marked as verified

Issue 2/122 [Yellow Validation]
  Row: 67
  Provider: Johnson Medical Clinic
  Address: 456 Oak Ave, Dallas, TX 75201

  No match found in New Orders (best was 45% confidence)

  Options:
    1. [a]dd to New Orders (will create new row)
    2. [c]hange status to white (remove yellow, not an order)
    3. [s]kip for now
    4. [q]uit

  Choice? c
  ✅ Status changed to white, notes updated

...

====================================================================
SUMMARY
====================================================================

Reviewed: 122 issues
Actions taken:
  - Yellow matches verified: 210
  - Yellow not found (added to NO): 3
  - Yellow converted to white: 31
  - Duplicates merged: 8
  - Duplicates kept separate: 4
  - Status fixes: 18
  - Moved to Invalid: 5
  - Not interested auto-fixed: 8

Write changes to sheet? [y/n] y

Writing updates...
✅ Updated Working List (143 rows modified)
✅ Updated New Orders (3 rows added)
✅ Updated Invalid/Inactive List (5 rows added)

Done! Check STATS sheet to verify counts.
```

**Questions:**
9. **Save progress periodically?**
   - If reviewing 122 issues takes 2 hours, save decisions every 20 issues?
   - To JSON file, can resume if interrupted?
   - **My recommendation:** Yes, save to `eoy_progress_YYYYMMDD.json`

10. **Undo functionality?**
    - Allow going back to previous issue?
    - **My recommendation:** Yes, allow [b]ack command

---

## Technical Implementation

### Libraries
```python
import gspread  # Google Sheets API
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd  # Data manipulation
from fuzzywuzzy import fuzz  # Fuzzy string matching
import json  # Progress saving
from datetime import datetime
import re  # Phone normalization
```

### File Structure
```
scripts/eoy_obgyn_tool.py
  - main() - Entry point
  - load_sheets() - Load WL + NO via gspread
  - validate_yellow() - Yellow → NO matching
  - detect_duplicates() - Find dupes/networks
  - check_status_issues() - Fuschia/green/red/empty
  - fix_not_interested() - Auto-fix not interested rules
  - interactive_review() - Terminal UI
  - apply_changes() - Batch write to sheets
  - save_progress() - Save to JSON
  - load_progress() - Resume from JSON
```

### Performance
- Load sheets: 2-3 seconds (via gspread)
- Run validations: 10-20 seconds (738 rows)
- Interactive review: 2-4 hours (user time)
- Write updates: 5-10 seconds (batch update)

**Total time:** 2-4 hours (mostly user review)

---

## Questions for User

**Critical (must answer before building):**

1. ✅ **Fuzzy string matching algorithm:** Token set ratio (handles word order)? **CONFIRM**

2. ✅ **Show multiple match candidates:** Show top 3 if within 10% confidence? **CONFIRM**

3. ✅ **Reverse matching:** Flag NO rows that don't match any yellow? **CONFIRM**

4. ✅ **Phone normalization:** Strip formatting (spaces, dashes, parens)? **CONFIRM**

5. ✅ **Network notation:** Append to existing Notes with semicolon? **CONFIRM**

6. ✅ **Green email auto-convert:** Show suggestion, user confirms? **CONFIRM**

7. ✅ **Invalid/Inactive List:** Copy what data? To what sheet name? **ANSWER**

8. ✅ **Not interested auto-fix:** Fix silently, show summary? **CONFIRM**

9. ✅ **Progress saving:** Save every 20 issues to JSON? **CONFIRM**

10. ✅ **Undo functionality:** Allow [b]ack to previous issue? **CONFIRM**

**Nice to have (can assume):**

11. **Confidence threshold:** 95% exact, 80-94% review, <80% not found? **CONFIRM or suggest different**

12. **New Orders additions:** When yellow not found, option to add to NO - should tool do this or just flag? **ANSWER**

13. **Duplicate resolution:** When duplicates found, show both and ask which to keep? **CONFIRM**

14. **STATS sheet:** Should tool validate STATS formulas still work after updates? **ANSWER**

15. **Backup before changes:** Auto-create backup or trust user did it manually? **ANSWER**

---

## Success Criteria

Tool is successful if:
- ✅ ALL 244 yellow rows validated (found in NO or explained why not)
- ✅ All duplicates identified and resolved
- ✅ All status issues fixed (fuschia/green/red/empty)
- ✅ All "not interested" rows have correct notes + QTY=0
- ✅ STATS sheet counts match reality
- ✅ User confident in data quality for reset phase
- ✅ Faster than Apps Script (target: 2-4 hours total vs 6+ hours manual)

---

## Next Steps

1. **User answers questions above**
2. **I build tool (3-4 hours)**
3. **Test with gspread on OBGYN sheet**
4. **User runs tool interactively**
5. **Verify STATS sheet**
6. **Manual reset phase**
7. **Document lessons learned for PCP in January**
