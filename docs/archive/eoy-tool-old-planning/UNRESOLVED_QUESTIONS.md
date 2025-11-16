# Unresolved Questions for Implementation

**Last Updated:** December 2024
**Status:** Minor clarifications needed before/during build

---

## 🟡 MINOR - Can Resolve During Build

### 1. New Orders QTY Column Location

**Question:** New Orders QTY might not be in column I (index 8). How to find it?

**Options:**
- A. Hardcode column index (fast, fragile)
- B. Search headers for "QTY" or "2025 QTY" (robust)
- C. Ask user on first run

**Recommendation:** Option B - search headers

**Code:**
```python
headers = no_data[0]
qty_col_idx = next((i for i, h in enumerate(headers) if '2025' in h and 'qty' in h.lower()), None)
if qty_col_idx is None:
    # Fall back to asking user or default
    qty_col_idx = 8
```

---

### 2. Exact Color Hex Codes

**Question:** Are colors EXACTLY #ffff00, #ff00ff, etc.? Or slight variations?

**From Test:** Found #ffffff, #ff00ff, #ffff00 in sample

**Potential Issue:** RGB might be (255, 255, 0) = #ffff00, but Google Sheets might store as (1.0, 1.0, 0.0) floating point

**Resolution:** Test actual color codes during build, create color matching with tolerance:

```python
def normalize_color(hex_color):
    """Normalize slight color variations"""
    # Yellow variations
    if hex_color in ['#ffff00', '#ffff01', '#fffef0']:
        return '#ffff00'
    # Fuschia variations
    if hex_color in ['#ff00ff', '#ff00fe', '#fe00ff']:
        return '#ff00ff'
    # etc.
    return hex_color
```

---

### 3. Network Mass-Invalid Reason Format

**Question:** When mass-adding network to invalid list, what reason to use?

**Options:**
- A. "Network: [networkname] - won't accept materials"
- B. Just "Network: [networkname]"
- C. Ask user for reason each time

**Recommendation:** Option A with user confirmation

**Code:**
```python
reason = f"Network: {network_name} - won't accept materials"
# User can edit before confirming
```

---

### 4. Replacing Existing Network Notation

**Question:** If notes already have "abc network (~2);", how to replace with new notation?

**Scenario:**
- Old: "abc network (~2); vm x2"
- New: "abcnetwork network (~3); vm x2"

**Solution:**
```python
def replace_network_notation(notes, new_notation):
    """Replace existing network notation"""
    # Remove old network notations (pattern: "word network (~N)")
    notes = re.sub(r'\b\w+ network \(~\d+\)', '', notes, flags=re.IGNORECASE)
    # Clean up multiple semicolons
    notes = re.sub(r'\s*;\s*;', ';', notes).strip(';').strip()
    # Prepend new notation
    return f"{new_notation}; {notes}" if notes else new_notation
```

---

### 5. Textual Documentation References

**Question:** Should I include links to Textual docs for next LLM?

**Answer:** Yes

**Links to add:**
- Textual Tutorial: https://textual.textualize.io/tutorial/
- Textual Widgets: https://textual.textualize.io/widget_gallery/
- Textual Guide: https://textual.textualize.io/guide/
- Textual API: https://textual.textualize.io/api/

---

### 6. INVALID vs INACTIVE Dropdown

**Question:** When to use INVALID vs INACTIVE?

**From User (Q6):** "INACTIVE for locations temporarily closed for say renovation"

**Clarification Needed:**
- INVALID = permanently invalid (closed, wrong specialty, disconnected)
- INACTIVE = temporarily unavailable (renovation, moving, temporary closure)

**UI:** Radio buttons, default to INVALID, user selects INACTIVE if appropriate

---

### 7. Resume Progress - Show Summary?

**Question:** When resuming from saved progress, show detailed summary before continuing?

**Options:**
- A. Just apply silently, continue
- B. Show modal with summary, ask to confirm
- C. Show summary in terminal, wait for Enter

**Recommendation:** Option C

**Code:**
```python
def show_resume_summary(progress):
    print("\n" + "="*80)
    print("RESUMING FROM SAVED PROGRESS")
    print("="*80)
    print(f"Session: {progress['session_id']}")
    print(f"Decisions made: {progress['decisions_count']}")
    print(f"Row changes: {len(progress['row_changes'])}")
    print(f"Current category: {progress['current_category_idx']}")
    print("\nPress Enter to continue, Ctrl+C to cancel...")
    input()
```

---

### 8. Auto-Save Progress Trigger

**Question:** Save every 20 decisions, or other interval?

**Current Plan:** Every 20 decisions

**Alternative:** Time-based (every 5 minutes)

**Recommendation:** Every 20 decisions + on quit (F2 key)

**Reasoning:** User controls pace, decisions are meaningful milestones

---

### 9. Batch Delete Exact Duplicates Logic

**Question:** When batch deleting exact duplicates, which row to keep?

**Options:**
- A. Keep first occurrence
- B. Keep row with most recent QTY
- C. Keep row with most notes
- D. Ask user which to keep

**Recommendation:** A (keep first occurrence) - simplest, most predictable

**Edge Case:** What if first has empty QTY but second has QTY?
- **Answer:** Still keep first (NO is canon, not WL QTY)

---

### 10. Status Change Auto-Color Update

**Question:** If user edits status field, should we auto-update color?

**From Apps Script:** onEdit() auto-updates colors

**In Python Tool:** We can't auto-update colors in gspread (would need additional API call per edit)

**Solution:** Document that colors update when user opens sheet in browser (Apps Script onEdit will trigger)

**OR:** Add color updates to batch write phase

**Recommendation:** Ignore colors during tool, let Apps Script onEdit handle it after

---

## ✅ RESOLVED (No Action Needed)

### ~~Shadow Worksheet Timing~~
**RESOLVED:** Create at end, keep changes in memory

### ~~Batch Operations Availability~~
**RESOLVED:** Always available as buttons

### ~~Orphan NO Rows Handling~~
**RESOLVED:** Flag in linear review, user investigates

### ~~Network Naming~~
**RESOLVED:** User provides, smart default from first row

### ~~Non-Standard Notes Definition~~
**RESOLVED:** Analyzed actual data (33% of chunks), categorized patterns

### ~~Duplicate QTY Combining~~
**RESOLVED:** NO is canon, don't auto-combine, match WL to NO

### ~~Google Search Helper~~
**RESOLVED:** Auto-open in browser + print URL

---

## 📋 SUMMARY

**Total Unresolved:** 10 minor questions
**Severity:** All can be resolved during implementation
**Blockers:** None

**Recommendation:** Proceed with build, resolve questions as encountered using best judgment + user QA

**Most Important to Confirm Before Build:**
1. ✅ None - all critical questions resolved

**Can Decide During Build:**
1. QTY column location detection
2. Color hex normalization
3. Network mass-invalid reason format
4. Resume progress UX

**Document for User:**
5. INVALID vs INACTIVE usage
6. Color updates (Apps Script handles)
7. Batch delete logic (keep first)
