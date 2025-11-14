# EOY Tool Architecture - Comprehensive Plan

**File:** `scripts/eoy_obgyn_tool.py`
**Purpose:** Local Python tool to replace Apps Script EOY validation
**Status:** Architecture finalized, ready to build

---

## Executive Summary

### What It Does
1. Loads Working List (737 rows) + New Orders (269 rows) via gspread
2. Runs validations (yellow→NO, duplicates, status issues, not interested)
3. Interactive terminal review organized by category
4. User makes decisions with editable fields
5. Batch writes to shadow worksheets (_CLEANUP suffix)
6. Duplicates STATS sheet with updated formula references

### Key Design Principles
- **Category-based review** (not 1-by-1 for everything)
- **Editable fields** always available (secondary to predefined actions)
- **Quick UI** for common tasks (hover/keypress for note chunks)
- **Batch operations** available when user exhausts manual work
- **New Orders is canon** - never modified
- **Shadow worksheets** for safe rollback

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: INITIAL SETUP                                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Ask user for year (default: 2025)                        │
│ 2. Detect existing shadow worksheets                        │
│ 3. Load sheets via gspread (4 API calls)                    │
│    - Working List 2025                                      │
│    - New Orders 2025                                        │
│    - Invalid/Inactive List (for reason samples)             │
│    - STATS (for formula references)                         │
│ 4. Load previous progress from JSON (if exists)             │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: VALIDATION (all in memory, 0 API calls)            │
├─────────────────────────────────────────────────────────────┤
│ 1. Yellow → New Orders matching (token set ratio)           │
│ 2. Duplicate detection (exact + fuzzy + networks)           │
│ 3. Status-based issues (fuschia/green/red/empty)            │
│ 4. Not interested validation (auto-fix)                     │
│ 5. Categorize all issues for organized review               │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: INTERACTIVE REVIEW (0 API calls, save to JSON)     │
├─────────────────────────────────────────────────────────────┤
│ Categories presented in optimal order:                      │
│ 1. Exact duplicates (batch fix available)                   │
│ 2. Networks (batch confirm per network)                     │
│ 3. Fuzzy duplicates (1-by-1 + batch after)                  │
│ 4. Yellow high-confidence matches (95%+, quick review)      │
│ 5. Yellow medium-confidence (80-94%, careful review)        │
│ 6. Yellow low-confidence (<80%, likely not found)           │
│ 7. Green "sent" emails (auto-suggest not interested)        │
│ 8. Fuschia voicemails (check notes)                         │
│ 9. Red invalid (review, move to Invalid List)               │
│ 10. Not interested issues (auto-fixed, just confirm)        │
│ 11. Non-standard notes (quick delete chunks)                │
│                                                              │
│ Each category:                                               │
│ - Show all rows in scrollable table                         │
│ - Editable fields (secondary to actions)                    │
│ - Predefined actions (primary)                              │
│ - Batch operations when available                           │
│ - Progress saved every 20 decisions                         │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: FINAL WRITE (7 API calls)                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Create shadow worksheets:                                │
│    - Working List 2025_CLEANUP (copy of WL with updates)    │
│    - Invalid/Inactive List_CLEANUP (with new invalids)      │
│    - STATS_CLEANUP (formulas reference WL_CLEANUP)          │
│ 2. Batch write all changes to shadows                       │
│ 3. Verify STATS formulas still work                         │
│ 4. If STATS broken, undo and report error                   │
│ 5. Print summary report                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### In-Memory Representation

```python
@dataclass
class ProviderRow:
    """Single row from Working List"""
    row_num: int  # Original row number (for updates)
    practice: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    qty_2023: str  # Keep as string to preserve empty vs "0"
    qty_2024: str
    qty_2025: str
    status: str
    notes: str
    bg_color: str  # Hex color (#ffff00, etc.)

    # Validation results
    issues: List[Issue] = field(default_factory=list)
    matched_no_row: Optional[int] = None  # New Orders row match
    match_confidence: float = 0.0
    duplicate_of: Optional[int] = None  # Row number if duplicate
    network_group: Optional[str] = None  # Network name if network

@dataclass
class Issue:
    """Single validation issue"""
    category: str  # "yellow_match", "duplicate", "status", "not_interested", etc.
    severity: str  # "auto_fix", "review", "critical"
    message: str
    suggested_action: Optional[str] = None
    data: Dict = field(default_factory=dict)  # Extra context

@dataclass
class ReviewCategory:
    """Group of related issues"""
    name: str  # "Exact Duplicates", "Yellow 95%+ Matches", etc.
    issues: List[ProviderRow]
    allow_batch: bool  # Can batch fix this category?
    batch_action: Optional[str] = None  # "delete_dupes", "confirm_network", etc.
```

---

## Validation Algorithms

### 1. Yellow → New Orders Matching

```python
def match_yellow_to_new_orders(wl_row, new_orders_df):
    """
    Match Working List yellow row to New Orders
    Returns: (best_match, confidence, row_index)
    """
    # Filter to same state (exact match required)
    state_matches = new_orders_df[new_orders_df['State'] == wl_row.state]

    if len(state_matches) == 0:
        return None, 0.0, None

    best_confidence = 0.0
    best_match = None
    best_index = None

    for idx, no_row in state_matches.iterrows():
        # Name matching (70% weight, token set ratio)
        name_score = fuzz.token_set_ratio(
            normalize_name(wl_row.practice),
            normalize_name(no_row['Practice'])
        ) / 100.0

        # Address matching (30% weight, token set ratio)
        addr_score = fuzz.token_set_ratio(
            normalize_address(wl_row.address),
            normalize_address(no_row['Address'])
        ) / 100.0

        # Combined confidence
        confidence = (name_score * 0.7) + (addr_score * 0.3)

        if confidence > best_confidence:
            best_confidence = confidence
            best_match = no_row
            best_index = idx

    return best_match, best_confidence, best_index

def normalize_name(name):
    """Normalize name for comparison"""
    if not name:
        return ""
    # Remove: LLC, PC, PLLC, INC, Dr., Doctor
    # Standardize: & → and, + → and
    # Lowercase
    # Strip whitespace
    return name.lower().strip()

def normalize_address(addr):
    """Normalize address for comparison"""
    if not addr:
        return ""
    # Standardize: Street→St, Avenue→Ave, etc.
    # Remove suite numbers (Suite 200, Ste 3, etc.)
    # Lowercase
    # Strip whitespace
    return addr.lower().strip()
```

**Confidence Thresholds:**
- **≥95%:** Exact match (show but allow quick accept)
- **80-94%:** High confidence (review carefully)
- **60-79%:** Medium confidence (likely mismatch)
- **<60%:** Not found

**Justification Testing:**
```python
# Test on sample data:
# "Smith Family Practice" vs "Family Practice Smith"
# → name_score: token_set=100%, simple=60%
#
# "123 Main Street" vs "123 Main St"
# → addr_score: token_set=90%, simple=75%
#
# Combined: 0.7*1.0 + 0.3*0.9 = 0.97 (97% confidence) ✅
```

### 2. Duplicate Detection

```python
def detect_duplicates(working_list):
    """
    Detect exact duplicates, fuzzy duplicates, and networks
    Returns: Dict[category, List[groups]]
    """
    results = {
        'exact': [],      # Same phone+name+address (0 QTY, no notes)
        'fuzzy': [],      # Similar (90%+ match) same phone
        'network': [],    # Same phone, different addresses, similar names
        'ambiguous': []   # Same phone, different names (not network)
    }

    # Group by normalized phone
    phone_groups = defaultdict(list)
    for row in working_list:
        norm_phone = normalize_phone(row.phone)
        if norm_phone:
            phone_groups[norm_phone].append(row)

    # Analyze each phone group
    for phone, rows in phone_groups.items():
        if len(rows) == 1:
            continue  # Not a duplicate

        # Check if exact match
        if is_exact_duplicate_group(rows):
            results['exact'].append(rows)
        # Check if network
        elif is_network_group(rows):
            results['network'].append(rows)
        # Check if fuzzy duplicate
        elif is_fuzzy_duplicate_group(rows):
            results['fuzzy'].append(rows)
        else:
            results['ambiguous'].append(rows)

    return results

def normalize_phone(phone):
    """Normalize phone for comparison"""
    if not phone:
        return ""
    # Strip extensions (x123, ext 456)
    # Remove non-digits
    # Take last 10 digits (handles +1 country code)
    digits = re.sub(r'[^\d]', '', phone)
    return digits[-10:] if len(digits) >= 10 else digits

def is_exact_duplicate_group(rows):
    """All rows same name, address, phone, and QTY=0 or empty"""
    # All have same normalized name
    # All have same normalized address
    # All have QTY empty or "0"
    # All have no notes or minimal notes
    return all_match

def is_network_group(rows):
    """Same phone, similar names (≥85%), different addresses"""
    # All names ≥85% similar (Levenshtein)
    # All addresses < 70% similar (different locations)
    # Common pattern: clinic name + location
    return is_network

def is_fuzzy_duplicate_group(rows):
    """Same phone, similar everything (likely data entry variations)"""
    # Names ≥90% similar
    # Addresses ≥80% similar
    return is_fuzzy_dupe
```

**Network Name Extraction:**
```python
def extract_network_name(provider_names):
    """
    Extract common network name from list of provider names
    Returns: network_name (lowercase, no spaces)
    """
    # Find longest common substring
    # Remove location-specific words (North, South, Downtown, etc.)
    # Remove "Office", "Clinic", "Medical", etc.
    # Lowercase, remove spaces
    # Example: "Women's Health Center North" → "womenshealthcenter"
    return network_name
```

### 3. Status-Based Validation

```python
def validate_status_issues(working_list):
    """
    Check for status-related issues
    Returns: Dict[status_type, List[rows]]
    """
    issues = {
        'fuschia_missing_vm': [],  # Fuschia but no "vm" in notes
        'green_sent': [],           # Green with "sent" in notes
        'red_verify': [],           # Red (all need manual review)
        'empty_uncalled': [],       # Empty status, white color
        'not_interested_invalid': [], # Not interested but reason suggests invalid
    }

    for row in working_list:
        if row.bg_color == '#ff00ff':  # Fuschia
            if not has_vm_note(row.notes):
                issues['fuschia_missing_vm'].append(row)

        elif row.bg_color == '#00ff00':  # Green
            if 'sent' in row.notes.lower():
                issues['green_sent'].append(row)

        elif row.bg_color == '#ff0000':  # Red
            issues['red_verify'].append(row)

        elif row.bg_color == '#ffffff' and not row.status:  # Empty
            if 'not interested' not in row.notes.lower():
                issues['empty_uncalled'].append(row)

        elif row.status == 'Not interested':
            if suggests_invalid(row.notes):
                issues['not_interested_invalid'].append(row)

    return issues

def suggests_invalid(notes):
    """Check if notes suggest provider is actually invalid"""
    invalid_keywords = [
        'closed', 'disconnected', 'wrong number', 'moved',
        'no longer', 'out of business', 'permanently closed'
    ]
    notes_lower = notes.lower()
    return any(kw in notes_lower for kw in invalid_keywords)
```

### 4. Not Interested Auto-Fix

```python
def auto_fix_not_interested(working_list):
    """
    Auto-fix rows with status="Not interested" but missing note or QTY≠0
    Returns: (fixed_rows, summary)
    """
    fixed = []

    for row in working_list:
        if row.status != 'Not interested':
            continue

        changes_made = []

        # Fix missing "not interested" in notes
        if 'not interested' not in row.notes.lower():
            if row.notes:
                row.notes += '; not interested'
            else:
                row.notes = 'not interested'
            changes_made.append('added_note')

        # Fix QTY (should be "0", not empty or other)
        if row.qty_2025 != '0':
            row.qty_2025 = '0'
            changes_made.append('set_qty_0')

        # Remove ":sent" or "sent" from notes during cleanup
        if ':sent' in row.notes.lower() or 'sent' in row.notes.lower():
            row.notes = row.notes.replace(':sent', '').replace('sent', '').strip()
            changes_made.append('removed_sent')

        if changes_made:
            row.issues.append(Issue(
                category='not_interested',
                severity='auto_fix',
                message=f"Auto-fixed: {', '.join(changes_made)}",
                suggested_action=None
            ))
            fixed.append(row)

    summary = f"Auto-fixed {len(fixed)} not interested rows"
    return fixed, summary
```

---

## UI/UX Design

### Category Review Order (Optimized for Efficiency)

```
1. EXACT DUPLICATES (batch fix available)
   → Quick: Show pairs, ask "Delete all duplicates? [y/n]"

2. NETWORKS (batch confirm per network)
   → Show all rows in network
   → Ask: "Confirm this is [networkname] network (~3 locations)? [y/n]"
   → If yes: batch add notation to all
   → If no: review 1-by-1 to separate

3. FUZZY DUPLICATES (1-by-1 + batch after)
   → Show both rows side-by-side
   → Ask: "Keep row A, B, or both?"
   → After all reviewed: "Fix all remaining? [y/n]"

4. YELLOW HIGH-CONFIDENCE (95%+ matches)
   → Show match details (name%, addr%)
   → Quick accept: [a]ccept all, [r]eview 1-by-1

5. YELLOW MEDIUM-CONFIDENCE (80-94%)
   → Careful review, show top 3 candidates if within 10%
   → Manual decision each one

6. YELLOW LOW-CONFIDENCE (<80%, not found)
   → Options: Change status to white, Add to NO (flag only), Skip

7. GREEN "SENT" EMAILS
   → Auto-suggest convert to not interested
   → Quick: [a]ccept all suggestions, [r]eview 1-by-1

8. FUSCHIA VOICEMAILS
   → Check notes, add "vm x2" if missing
   → Quick UI for adding notes

9. RED INVALID
   → Review each, move to Invalid List with reason dropdown

10. NOT INTERESTED ISSUES
    → Already auto-fixed, just show summary for confirmation

11. NON-STANDARD NOTES
    → Hover-over chunks, keypress to fade/delete
    → Very fast cleanup
```

### Interactive UI Components

#### 1. Scrollable Table View

```
Category: Exact Duplicates (12 pairs found)
═══════════════════════════════════════════════════════════════
Row  Practice                    Phone        Address
───────────────────────────────────────────────────────────────
45   Smith Family Practice       555-1234     123 Main St
78   Smith Family Practice       555-1234     123 Main St        (DUPE)

92   Johnson Medical             555-5678     456 Oak Ave
103  Johnson Medical             555-5678     456 Oak Ave        (DUPE)

... (scroll with ↑↓ arrows or j/k)
═══════════════════════════════════════════════════════════════
Actions: [a]ccept batch delete, [r]eview 1-by-1, [e]dit row, [q]uit
```

#### 2. Edit Field Modal (when pressing [e])

```
Editing Row 45: Smith Family Practice
═══════════════════════════════════════════════════════════════
[Practice] Smith Family Practice_____________________ [Enter to accept]
[Phone]    555-1234__________________________________ [Tab to next]
[Address]  123 Main St_______________________________
[City]     Houston___________________________________
[State]    TX [dropdown: TX▼]
[Zip]      77001_____________________________________
[2025 QTY] [empty]____ (empty=uncalled, 0=no materials)
[Status]   [dropdown: Successful Order▼]
[Notes]    network notation; vm x2____________________
           [1] network notation  [2] vm x2
           Delete chunks: 1 2_ (space-separated, Enter to delete)

═══════════════════════════════════════════════════════════════
[s]ave changes, [c]ancel
```

#### 3. Notes Chunk UI (hover/keypress)

```
Notes: network notation; vm x2; sent; callback tuesday
       ¹                 ²      ³     ⁴

Hover over note chunk to highlight, then:
  [d] Delete highlighted chunk
  [1] Delete chunk 1
  [2] Delete chunk 2
  [3] Delete chunk 3
  [4] Delete chunk 4

Deleted chunks fade out (can undo with [u]):
  network notation; vm x2; ~~sent~~; callback tuesday

Press [Enter] to apply changes
```

#### 4. Network Confirmation

```
Category: Networks - Group 1/8
═══════════════════════════════════════════════════════════════
Network detected: womenshealthcenter (~3 locations)

Rows in network:
  45: Women's Health Center North    | 555-1234 | 123 Main St
  67: Women's Health Center Downtown | 555-1234 | 456 Oak Ave
  89: Women's Health Center East     | 555-1234 | 789 Elm St

═══════════════════════════════════════════════════════════════
Network name: [womenshealthcenter___________] (edit if needed)

Options:
  [y] Confirm network, add notation to all 3 rows
  [n] Not a network, review each row individually
  [i] Mass-add to Invalid List (network won't accept pamphlets)
  [c] Copy fields between rows (if names don't match)
  [g] Google search all providers (opens 3 tabs)
```

#### 5. Duplicate with QTY Conflict

```
Category: Fuzzy Duplicates - Row 2/15
═══════════════════════════════════════════════════════════════
CONFLICT: Both rows have QTY values

Row A (45): Smith Family Practice
  Phone: 555-1234 | Address: 123 Main St | 2025 QTY: 50
  NO Match: Row 89 (95% confidence)

Row B (78): Smith Family Practice
  Phone: 555-1234 | Address: 123 Main Street | 2025 QTY: 30
  NO Match: Row 120 (92% confidence)

═══════════════════════════════════════════════════════════════
New Orders says:
  Row 89: Smith Family Practice, 123 Main St → QTY: 50  ✅
  Row 120: Smith Family Practice, 123 Main Street → QTY: 30 ✅

Decision: Both rows have valid orders in New Orders!
═══════════════════════════════════════════════════════════════
Options:
  [k] Keep both (maybe different doctors, same practice)
  [m] Merge (combine QTYs: 50+30=80) → Single row
  [a] Keep Row A, delete Row B
  [b] Keep Row B, delete Row A
  [e] Edit either row
```

---

## Progress Saving & Resuming

### Progress File Format

```python
# eoy_progress_20251213_1430.json
{
  "session_id": "20251213_143052",
  "year": 2025,
  "started_at": "2025-12-13T14:30:52",
  "last_saved_at": "2025-12-13T15:45:12",
  "categories_completed": [
    "exact_duplicates",
    "networks",
    "fuzzy_duplicates",
    "yellow_high_confidence"
  ],
  "current_category": "yellow_medium_confidence",
  "current_index": 23,
  "decisions": [
    {
      "row_num": 45,
      "action": "delete_duplicate",
      "timestamp": "2025-12-13T14:32:15"
    },
    {
      "row_num": 67,
      "action": "confirm_network",
      "network_name": "womenshealthcenter",
      "network_group": [67, 89, 102],
      "timestamp": "2025-12-13T14:35:42"
    },
    // ... more decisions
  ],
  "field_changes": [
    {
      "row_num": 45,
      "field": "notes",
      "old_value": "vm x2",
      "new_value": "womenshealthcenter network (~3); vm x2",
      "timestamp": "2025-12-13T14:35:42"
    },
    // ... more changes
  ]
}
```

### Auto-Save Trigger

```python
def auto_save_progress(decisions_count):
    """Save progress every 20 decisions"""
    if decisions_count % 20 == 0:
        save_to_json(progress)
        print(f"✅ Progress saved ({decisions_count} decisions)")
```

### Resume Logic

```python
def resume_session():
    """Detect and offer to resume previous session"""
    progress_files = glob.glob('eoy_progress_*.json')
    if not progress_files:
        return None

    # Find most recent
    latest = max(progress_files, key=os.path.getmtime)

    print(f"Found previous session: {latest}")
    print(f"  Started: {progress['started_at']}")
    print(f"  Last saved: {progress['last_saved_at']}")
    print(f"  Progress: {len(progress['categories_completed'])}/11 categories")

    resume = input("Resume this session? [y/n]: ")

    if resume.lower() == 'y':
        return load_progress(latest)
    else:
        return None
```

---

## Shadow Worksheet System

### Creation Process

```python
def create_shadow_worksheets(gc, spreadsheet, year):
    """
    Create shadow worksheets for safe updates
    Returns: (wl_cleanup, invalid_cleanup, stats_cleanup)
    """
    # 1. Duplicate Working List
    wl_orig = spreadsheet.worksheet(f'Working List {year}')
    wl_cleanup = wl_orig.duplicate(
        new_sheet_name=f'Working List {year}_CLEANUP'
    )

    # 2. Duplicate Invalid/Inactive List
    invalid_orig = spreadsheet.worksheet('Invalid/Inactive List')
    invalid_cleanup = invalid_orig.duplicate(
        new_sheet_name='Invalid/Inactive List_CLEANUP'
    )

    # 3. Duplicate STATS
    stats_orig = spreadsheet.worksheet('STATS')
    stats_cleanup = stats_orig.duplicate(
        new_sheet_name='STATS_CLEANUP'
    )

    # 4. Update STATS formulas to reference _CLEANUP sheets
    update_stats_formulas(stats_cleanup, year)

    return wl_cleanup, invalid_cleanup, stats_cleanup
```

### Formula Update Logic

```python
def update_stats_formulas(stats_cleanup, year):
    """
    Update all formulas in STATS_CLEANUP to reference Working List {year}_CLEANUP
    """
    # Get all formulas
    all_formulas = stats_cleanup.get('A1:Z52', value_render_option='FORMULA')

    # Find and replace
    updated = []
    for row_idx, row in enumerate(all_formulas):
        updated_row = []
        for cell in row:
            if isinstance(cell, str) and f'Working List {year}' in cell:
                # Replace both formats:
                # 'Working List 2025' → 'Working List 2025_CLEANUP'
                # "Working List 2025" → "Working List 2025_CLEANUP"
                cell = cell.replace(
                    f"'Working List {year}'",
                    f"'Working List {year}_CLEANUP'"
                )
                cell = cell.replace(
                    f'"Working List {year}"',
                    f'"Working List {year}_CLEANUP"'
                )
            updated_row.append(cell)
        updated.append(updated_row)

    # Write back
    stats_cleanup.update('A1:Z52', updated, value_input_option='USER_ENTERED')
```

### Validation Logic

```python
def validate_stats_formulas(stats_cleanup):
    """
    Verify STATS formulas work after update
    Returns: (success, errors)
    """
    errors = []

    # Read key cells that should have numeric values
    test_cells = [
        ('C2', 'ORDER SECURED count'),
        ('C3', 'NOT INTERESTED count'),
        ('C4', 'CALLBACK count'),
        ('C5', 'UNCALLED count'),
        ('C6', 'VERIFY count'),
    ]

    for cell_addr, description in test_cells:
        try:
            cell = stats_cleanup.acell(cell_addr)
            value = cell.value

            # Should be numeric
            if not value or not value.isdigit():
                errors.append(f"{cell_addr} ({description}): Got '{value}', expected number")
        except Exception as e:
            errors.append(f"{cell_addr} ({description}): Error - {str(e)}")

    if errors:
        return False, errors
    else:
        return True, []
```

### Rollback on Error

```python
def rollback_on_stats_error(spreadsheet, year):
    """
    If STATS validation fails, delete shadow worksheets
    """
    print("⚠️  STATS validation failed! Rolling back...")

    # Delete shadow worksheets
    try:
        spreadsheet.del_worksheet(
            spreadsheet.worksheet(f'Working List {year}_CLEANUP')
        )
        spreadsheet.del_worksheet(
            spreadsheet.worksheet('Invalid/Inactive List_CLEANUP')
        )
        spreadsheet.del_worksheet(
            spreadsheet.worksheet('STATS_CLEANUP')
        )
        print("✅ Shadow worksheets deleted")
    except Exception as e:
        print(f"❌ Error during rollback: {e}")

    print("\nNo changes were made to original sheets.")
    print("Review STATS formulas manually and try again.")
```

---

## Batch Update Strategy

### Grouping Changes

```python
def batch_updates_by_type(all_changes):
    """
    Group changes by type for efficient batch updates
    Returns: Dict[update_type, List[changes]]
    """
    batches = {
        'working_list': [],      # Updates to WL_CLEANUP
        'invalid_list': [],      # New rows for Invalid_CLEANUP
        'delete_rows': [],       # Rows to delete from WL_CLEANUP
    }

    for change in all_changes:
        if change['type'] == 'update_field':
            batches['working_list'].append(change)
        elif change['type'] == 'move_to_invalid':
            batches['invalid_list'].append(change)
        elif change['type'] == 'delete_duplicate':
            batches['delete_rows'].append(change)

    return batches
```

### Single Batch Write

```python
def apply_all_changes(wl_cleanup, invalid_cleanup, batches):
    """
    Apply all changes in single batch operation per worksheet
    """
    # 1. Update Working List (batch update)
    if batches['working_list']:
        updates = []
        for change in batches['working_list']:
            row = change['row_num']
            col = change['column']
            value = change['new_value']

            cell = gspread.utils.rowcol_to_a1(row, col)
            updates.append({
                'range': cell,
                'values': [[value]]
            })

        wl_cleanup.batch_update(updates)
        print(f"✅ Updated {len(updates)} cells in Working List")

    # 2. Add to Invalid List (batch append)
    if batches['invalid_list']:
        rows_to_add = []
        for change in batches['invalid_list']:
            rows_to_add.append([
                change['practice'],
                change['phone'],
                change['address'],
                change['city'],
                change['state'],
                change['zip'],
                change['reason'],  # INVALID or INACTIVE
                change['notes'],   # With QTY appended if exists
            ])

        invalid_cleanup.append_rows(rows_to_add)
        print(f"✅ Added {len(rows_to_add)} rows to Invalid List")

    # 3. Delete rows (reverse order to preserve indices)
    if batches['delete_rows']:
        # Sort descending
        rows_to_delete = sorted(
            [c['row_num'] for c in batches['delete_rows']],
            reverse=True
        )

        for row_num in rows_to_delete:
            wl_cleanup.delete_rows(row_num)

        print(f"✅ Deleted {len(rows_to_delete)} duplicate rows")
```

---

## Error Handling

### API Error Recovery

```python
try:
    wl_cleanup.batch_update(updates)
except gspread.exceptions.APIError as e:
    if 'Quota exceeded' in str(e):
        print("⚠️  Rate limit hit, waiting 60s...")
        time.sleep(60)
        wl_cleanup.batch_update(updates)  # Retry
    else:
        print(f"❌ API Error: {e}")
        print("Saving progress and exiting...")
        save_progress()
        sys.exit(1)
```

### Validation Errors

```python
def validate_before_write():
    """
    Final validation before writing to sheets
    Returns: (valid, errors)
    """
    errors = []

    # Check no duplicate row numbers in updates
    row_nums = [c['row_num'] for c in all_changes]
    if len(row_nums) != len(set(row_nums)):
        errors.append("Duplicate row numbers in updates")

    # Check no invalid values
    for change in all_changes:
        if 'new_value' in change and change['new_value'] is None:
            errors.append(f"Row {change['row_num']}: Invalid value")

    # Check STATS formulas valid
    success, stats_errors = validate_stats_formulas(stats_cleanup)
    if not success:
        errors.extend(stats_errors)

    return len(errors) == 0, errors
```

---

## Testing Strategy

### Unit Tests (Before Building)

```python
# Test fuzzy matching thresholds
test_cases = [
    ("Smith Family Practice", "Family Practice Smith", 0.95),  # Expect high
    ("123 Main Street", "123 Main St", 0.90),  # Expect high
    ("Johnson Medical", "Johnson Dental", 0.60),  # Expect low
]

for name1, name2, expected_min in test_cases:
    score = fuzz.token_set_ratio(name1, name2) / 100.0
    assert score >= expected_min, f"Failed: {name1} vs {name2} = {score}"
```

### Integration Test (With TEST Sheet)

```python
# Use "TEST Working List 2025" for safe testing
def run_integration_test():
    """
    Run full tool on TEST sheet, verify results
    """
    # 1. Load TEST Working List 2025
    # 2. Run validations
    # 3. Simulate user decisions (auto-accept all)
    # 4. Write to TEST_CLEANUP
    # 5. Verify counts match expectations
    # 6. Clean up (delete TEST_CLEANUP)
```

---

## Performance Targets

### Load Phase
- **Target:** 5-7 seconds
- **Actual:** ~4 reads at ~1.5s each = 6 seconds

### Validation Phase
- **Target:** 10-20 seconds for 737 rows
- **Fuzzy matching:** 737 × 269 comparisons ≈ 200K ops
- **Estimate:** 15 seconds (Python fuzzywuzzy is fast)

### Interactive Review
- **Target:** 2-4 hours
- **Actual:** Depends on user (0 API calls)

### Write Phase
- **Target:** 5-10 seconds
- **Actual:** ~7 writes at ~1s each = 7 seconds

### Total
- **API time:** 13-17 seconds
- **User time:** 2-4 hours
- **Total:** 2-4 hours

---

## Success Criteria

Tool is successful if:
1. ✅ ALL 244 yellow rows validated (matched or explained)
2. ✅ All duplicates identified and resolved
3. ✅ All status issues fixed
4. ✅ All "not interested" rows correct
5. ✅ STATS formulas work in _CLEANUP sheet
6. ✅ User can rename shadows and delete originals
7. ✅ Faster than manual (2-4 hours vs 6+ hours)
8. ✅ No data loss
9. ✅ Resumable if interrupted

---

## Next Steps

1. **Build tool** (3-4 hours estimated)
2. **Unit test matching algorithms**
3. **Integration test on TEST sheet**
4. **Run on OBGYN Working List 2025**
5. **User reviews and makes decisions**
6. **Verify STATS_CLEANUP**
7. **User renames shadows** (removes _CLEANUP suffix)
8. **Document lessons learned**

---

**Architecture Status:** FINALIZED, READY TO BUILD
**Estimated Build Time:** 3-4 hours
**Estimated First Run Time:** 2-4 hours (mostly user review)
