# EOY Cleanup Tool - Documentation

**Last Updated:** 2025-11-24

**Purpose:** Web application for cleaning up OBGYN Working List data at end of year

**Status:** Active development - Flask web app implementation (read-only mode functional, write phase pending)

---

## What This Tool Does

The EOY (End of Year) Cleanup Tool helps prepare the OBGYN Working List for the next year by:

1. **Validating Yellow Rows** - Fuzzy matching successful orders to New Orders sheet
2. **Finding Duplicates** - Detecting exact duplicates, networks, and similar entries
3. **Checking Status Issues** - Flagging voicemails, emails, invalid providers
4. **Organizing for Review** - Grouping issues into categories for systematic cleanup

**Key Benefit:** Reduces 6+ hours of manual work to 2-4 hours of focused review.

---

## Architecture

### Tech Stack

- **Backend:** Flask (Python web framework)
- **Frontend:** HTML + vanilla JavaScript + CSS
- **Data Source:** Google Sheets API (gspread)
- **Matching:** rapidfuzz library (fuzzy string matching)
- **Design:** "Data Atelier" aesthetic - refined, professional, easy on eyes

### Key Files

```
scripts/
  eoy_tool.py          # Main Flask application (backend + routes)
  test_eoy_output.py   # Testing/validation script

templates/
  base.html            # Base template (layout, fonts)
  index.html           # Landing page (load data)
  category.html        # Main review interface (where you spend 2-4 hours)

static/
  css/main.css         # All styling ("Data Atelier" design)
  js/
    selection.js       # Row selection logic (shift/ctrl click)
    undo.js            # Undo/redo system
    shortcuts.js       # Keyboard shortcuts

docs/
  EOY_TOOL_SPEC.md     # Original spec (high-level goals)
  GSPREAD_RATE_LIMITS.md  # API quota management
  NOTES_SAMPLE_ANALYSIS.txt  # Analysis of actual notes data
  archive/             # Outdated docs (described Textual TUI, not Flask)
```

---

## How It Works

### 1. Data Loading

```python
# scripts/eoy_tool.py: load_data()

1. Authenticate with Google Sheets API
2. Load Working List, New Orders, Invalid/Inactive List
3. Derive colors from Status column (avoids 737 API calls)
4. Validate against STATS worksheet
5. Return ProviderRow and NewOrderRow objects
```

**Critical:** Colors are derived from Status text, not read individually, to avoid API rate limits (60/min).

### 2. Validation Pipeline

```python
# scripts/eoy_tool.py

validate_yellow_to_no()      # Fuzzy match yellow rows to New Orders
validate_no_to_wl()          # Find orphan NO rows
detect_duplicates()          # Group by phone, detect networks
validate_status_issues()     # Check fuschia, green, red statuses
categorize_issues()          # Organize into review categories
```

**Fuzzy Matching:**
- Name: 70% weight (token_set_ratio handles word order)
- Address: 30% weight (normalized USPS abbreviations)
- State must match exactly
- Result: 0.0-1.0 confidence score

**Thresholds:**
- ≥95%: High confidence (exact match)
- 80-94%: Medium confidence (review carefully)
- <80%: Low confidence (not found)

### 3. Categorization

Issues grouped into 11 categories:

1. **Duplicates** - Exact matches (same name, address, phone)
2. **Networks** - Same phone, different locations
3. **Possible Dupes** - Similar but not identical
4. **Orders (Exact Match)** - Yellow ≥95% confidence
5. **Orders (Good Match)** - Yellow 80-94% confidence
6. **Orders (Not Found)** - Yellow <80% confidence
7. **Unmatched Orders** - NO rows without yellow WL match
8. **Email Sent** - Green with "sent" in notes
9. **Voicemails** - Fuschia status
10. **Potentially Invalid** - Red status
11. **Not Int (Invalid?)** - White "not interested" but notes suggest invalid

### 4. Review Interface

**Main UI:** `templates/category.html`

**Features:**
- Category sidebar (progress tracking)
- Sortable data table
- Multi-select (shift/ctrl click)
- Expandable details (▶ arrow shows match info)
- Context menus (right-click note chunks)
- Keyboard shortcuts (Ctrl+A, Ctrl+S, Ctrl+Z, etc.)
- Visual duplicate grouping (colored left borders)

**Workflow:**
1. Click category in sidebar
2. Review rows in table
3. Click ▶ to see match details
4. Select rows (shift/ctrl)
5. Take action (edit, delete, Google search, etc.)
6. Save progress (auto-saves to JSON)
7. Move to next category

### 5. State Management

**In-Memory:** Global `state` object (AppState class)
- wl_rows: List[ProviderRow]
- no_rows: List[NewOrderRow]
- categories: List[ReviewCategory]
- undo_stack: Last 50 actions
- year: 2025

**Persistence:**
- Auto-save to JSON every 20 actions
- Save on quit (beforeunload event)
- Can resume from saved progress

**NOT YET IMPLEMENTED:**
- Writing changes to Google Sheets
- Shadow worksheet creation
- Undo/redo functionality

---

## Data Models

### ProviderRow (Working List)

```python
@dataclass
class ProviderRow:
    # Core data
    row_num: int           # 1-based row number in sheet
    practice: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    qty_2023: str
    qty_2024: str
    qty_2025: str
    status: str
    notes: str
    bg_color: str          # Derived from status

    # Validation results
    issues: List[Dict]     # List of Issue objects
    matched_no_row: int    # Row number in New Orders
    match_confidence: float  # 0.0-1.0
    duplicate_group_id: int  # Group ID for duplicates
    network_name: str      # Network name if applicable

    # User decisions
    action: str            # "keep", "delete", "move_to_invalid", etc.
    field_edits: Dict      # Pending changes
```

### NewOrderRow

```python
@dataclass
class NewOrderRow:
    row_num: int
    practice: str
    address: str
    city: str
    state: str
    zip: str
    qty_2025: str

    # Reverse matching
    matched_wl_rows: List[int]  # WL rows that match this NO
    is_orphan: bool             # True if no yellow WL match
```

### ReviewCategory

```python
@dataclass
class ReviewCategory:
    id: str                    # "exact_dupes", "yellow_95", etc.
    name: str                  # Display name
    description: str           # Help text
    row_nums: List[int]        # Row numbers in this category
    allow_batch: bool          # Can batch process?
    primary_action: str        # Default action button
    secondary_actions: List[str]  # Other action buttons
```

---

## API Rate Limits

**Google Sheets API:** 60 reads/minute per user

**Original Approach (BROKEN):**
- Read each cell color individually = 737 API calls
- Exceeds quota after ~66 rows
- Result: 90% data loss

**Current Approach (WORKING):**
- Read Status column text (1 API call)
- Map status → color via `status_to_color()`
- Read STATS formulas to validate (1 API call)
- Total: ~11 API calls per full run

**Status → Color Mapping:**
```python
"Successful Order" → #ffff00 (yellow)
"Voicemail" → #ff00ff (fuschia)
"Not interested" → #ffffff (white)
"Potentially Invalid" → #ff0000 (red)
"Requested Email" → #00ff00 (green)
```

See `docs/GSPREAD_RATE_LIMITS.md` for details.

---

## User Interface Design

**Design Philosophy:** "Data Atelier"
- Refined craftsmanship aesthetic
- Warm, natural colors (avoid harsh blue light)
- Beautiful typography (Fraunces, DM Sans, JetBrains Mono)
- Subtle animations (150ms ease transitions)
- High information density without clutter

**Color Palette:**
- Base: Warm cream (#f8f6f3) - easy on eyes for 2-4 hour sessions
- Primary: Deep forest green (#1b4332) - trustworthy
- Accent: Warm terracotta (#c1592d) - distinctive
- Data states: Preserve Google Sheets colors (familiarity)

**Key UX Features:**
1. **No text selection on shift-click** (user-select: none)
2. **Single-row toggle deselect** (click selected row to deselect)
3. **Column sorting** (click header to toggle A-Z / Z-A)
4. **Expandable details** (▶ arrow to see match info)
5. **Duplicate grouping** (colored left borders)
6. **Context menus** (right-click for chunk operations)

---

## Testing

### Manual Testing Checklist

After loading data:
1. Check console for diagnostic output (unusual statuses)
2. Verify category counts make sense
3. Try expanding a row (▶ arrow) - match info correct?
4. Check duplicate borders - same color for same group?
5. Test selection (shift/ctrl click, select all, clear)
6. Test sorting (click column headers)
7. Test save progress (Ctrl+S)

### Automated Testing

**Status:** ⚠️ **NOT YET IMPLEMENTED**

Comprehensive test suite needed for:
- Status-to-color mapping (edge cases)
- Fuzzy matching with different weight configurations
- Duplicate detection and network identification
- Undo/redo functionality
- Categorization logic
- Data loading from gspread

See TODO.md for test suite implementation priority.

---

## Known Issues & Limitations

### Not Yet Implemented

1. **Writing changes to Google Sheets**
   - Currently in-memory only
   - Need to implement batch update logic
   - Need shadow worksheet creation

2. **Undo/Redo**
   - Stack exists, but restore logic not implemented
   - Need to apply saved state back to rows

3. **Edit Modal**
   - Inline editing exists
   - Full modal for complex edits not built

4. **Bulk Actions**
   - Some bulk actions not fully implemented
   - Need to wire up backend handlers

### Potential Issues

1. **Status/Color Mismatches**
   - If Status text doesn't match expected keywords
   - Diagnostic logging helps identify these
   - Can update `status_to_color()` mapping as needed

2. **Progress Save Reliability**
   - Uses beforeunload event (not 100% reliable)
   - Manual save (Ctrl+S) recommended

3. **Browser Caching**
   - Hard refresh (Ctrl+Shift+R) needed after code changes
   - Static files may be cached

---

## Development

### Running Locally

```bash
cd C:\Users\noagi\Desktop\JGDC
python scripts/eoy_tool.py
```

Server starts at http://127.0.0.1:5000

**Debug mode:** Enabled (auto-reload on code changes)

### Making Changes

**Backend (Python):**
- Edit `scripts/eoy_tool.py`
- Flask auto-reloads

**Frontend (HTML/CSS/JS):**
- Edit files in `templates/` or `static/`
- Hard refresh browser (Ctrl+Shift+R)

**Validation Logic:**
- Functions in `scripts/eoy_tool.py`
- Tests: See TODO.md for test suite implementation plan

### Adding New Categories

1. Add ReviewCategory to `categorize_issues()` in eoy_tool.py
2. Add validation logic that populates `row.issues`
3. Update templates/category.html if special display needed
4. Update docs

---

## Troubleshooting

### "No matches found" but should match
- Check Status column in sheet (might be empty/wrong)
- Check if state matches (must be exact)
- Run with diagnostic logging to see confidence scores

### Colors wrong in UI
- Check console for unusual status values
- Status text might not map correctly
- Update `status_to_color()` function

### Browser shows old UI
- Hard refresh: Ctrl+Shift+R
- Check for multiple Flask instances (kill extras)

### API quota exceeded
- Should not happen with current approach
- If it does, check if reading colors individually somewhere

### Progress not saving
- Use manual save (Ctrl+S)
- Check browser console for errors
- beforeunload event not 100% reliable

---

## Future Enhancements

### High Priority
1. Implement Google Sheets writing (batch updates)
2. Create shadow worksheets (_CLEANUP)
3. Implement undo/redo restore logic
4. Add all bulk action handlers

### Nice to Have
1. Keyboard navigation (arrow keys between rows)
2. Export to CSV for offline review
3. Diff view (before/after changes)
4. Confidence score tuning (adjust thresholds)
5. Custom fuzzy match weights (name vs address)

---

## Archived Documentation

Old docs in `docs/archive/`:
- EOY_TOOL_ARCHITECTURE_V2.md (described Textual TUI, not Flask)
- IMPLEMENTATION_GUIDE.md (outdated build checklist)
- UNRESOLVED_QUESTIONS.md (mostly resolved now)

These were planning documents before implementation. **Ignore them** - they describe a different architecture (terminal UI) that was not built.

---

## Contact / Questions

This tool was built iteratively with extensive user feedback. The actual workflow and requirements emerged during development, so documentation had to be rewritten to match reality.

**Key Principle:** Trust the code, not the old docs.
