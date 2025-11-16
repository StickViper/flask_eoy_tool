# EOY Tool Architecture V2 - REVISED

**File:** `scripts/eoy_obgyn_tool.py`
**UI Framework:** Textual (modern Python TUI)
**Status:** Ready to implement

---

## Changes from V1

### ✅ RESOLVED GAPS
1. **Color reading:** Using `gspread-formatting` ✅ Tested
2. **Fuzzy matching:** Using `rapidfuzz` ✅ Tested
3. **Terminal UI:** Using Textual for rich TUI ✅ Installed
4. **Duplicate QTY logic:** NO is canon, match WL to NO ✅ Fixed
5. **Reverse validation:** Added NO→WL orphan check ✅ Added
6. **Network naming:** User provides with smart default ✅ Simplified
7. **Shadow worksheets:** Create at end only ✅ Clarified
8. **Non-standard notes:** Analyzed actual data ✅ Patterns identified

### 📝 USER CLARIFICATIONS
- **Batch operations:** Always available as button/keypress
- **Orphan NO rows:** Flag in linear review process
- **Notes review:** Show uncommon chunks for quick deletion (analyzed 289 actual notes)
- **UI complexity:** Standalone app with nice UX using Textual
- **Shadow creation:** At end, keep changes in memory during review

---

## Technology Stack

```python
# Core
import gspread  # Google Sheets API
from gspread_formatting import get_effective_format  # Cell colors
from oauth2client.service_account import ServiceAccountCredentials

# Data processing
import pandas as pd
from rapidfuzz import fuzz  # Fuzzy string matching
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json
from datetime import datetime
import re

# TUI Framework
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Button, DataTable, Footer, Header, Input, Label,
    Static, TabbedContent, TabPane, Tree, Checkbox,
    RadioSet, RadioButton, Select, TextArea
)
from textual.binding import Binding
from textual.screen import Screen
```

---

## UI Framework: Textual Overview

**Why Textual?**
- Modern Python TUI framework (like React for terminal)
- Mouse support (click buttons!)
- Keyboard shortcuts
- Scrollable containers
- Tables, forms, tabs
- CSS-like styling
- Reactive data binding

**Textual Features We'll Use:**
- `DataTable` for row display
- `TabbedContent` for categories
- `Button` for actions
- `Footer` for keyboard shortcuts
- `Input` for field editing
- `Checkbox` for batch selection
- `Screen` for modal dialogs

**Example Textual Layout:**
```
┌─ EOY Tool ─────────────────────────────────────────────────────┐
│ [Exact Duplicates] [Networks] [Yellow 95%+] [Yellow 80-94%] ... │
├────────────────────────────────────────────────────────────────┤
│ Row  Practice                Phone      Address           QTY  │
│ ──────────────────────────────────────────────────────────────│
│ 45   Smith Family Practice   555-1234   123 Main St       50  │
│ 78   Smith Family Practice   555-1234   123 Main St       30  │← Duplicate
│                                                                 │
│ Match in New Orders: Row 89 (95% confidence)                   │
│ NO QTY: 50 (matches row 45, NOT row 78!)                      │
├────────────────────────────────────────────────────────────────┤
│ [Keep Row 45] [Keep Row 78] [Keep Both] [Edit] [Batch Delete] │
│ F1: Help | F2: Save Progress | F3: Batch Mode | Esc: Quit     │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Model (Revised)

```python
@dataclass
class ProviderRow:
    """Single row from Working List"""
    row_num: int  # 1-based row number in sheet
    practice: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    qty_2023: str  # Keep as string (empty vs "0")
    qty_2024: str
    qty_2025: str
    status: str
    notes: str
    bg_color: str  # Hex from gspread-formatting

    # Validation results
    issues: List['Issue'] = field(default_factory=list)
    matched_no_row: Optional[int] = None
    match_confidence: float = 0.0
    duplicate_group_id: Optional[int] = None
    network_name: Optional[str] = None

    # User decisions
    action: Optional[str] = None  # "keep", "delete", "move_to_invalid", etc.
    field_edits: Dict[str, str] = field(default_factory=dict)

@dataclass
class NewOrderRow:
    """Single row from New Orders"""
    row_num: int
    practice: str
    address: str
    city: str
    state: str
    zip: str
    qty_2025: str

    # Reverse matching
    matched_wl_rows: List[int] = field(default_factory=list)
    is_orphan: bool = False  # No yellow match in WL

@dataclass
class Issue:
    """Validation issue"""
    category: str  # Category name
    severity: str  # "auto_fix", "review", "critical"
    message: str
    suggested_action: Optional[str] = None
    data: Dict = field(default_factory=dict)

@dataclass
class ReviewCategory:
    """Group of issues for review"""
    id: str  # "exact_dupes", "yellow_95", etc.
    name: str  # Display name
    rows: List[ProviderRow]
    allow_batch: bool
    batch_actions: List[str] = field(default_factory=list)
    description: str = ""
```

---

## Phase 1: Data Loading

```python
def load_data(year: int = 2025):
    """
    Load all data from sheets
    Returns: (wl_rows, no_rows, invalid_reasons, stats_formulas)
    """
    # 1. Authenticate
    gc = gspread.authorize(creds)
    sh = gc.open('OBGYN List 2025 - Use This List!')

    # 2. Get worksheets
    wl_sheet = sh.worksheet(f'Working List {year}')
    no_sheet = sh.worksheet(f'New Orders {year}')
    invalid_sheet = sh.worksheet('Invalid/Inactive List')
    stats_sheet = sh.worksheet('STATS')

    # 3. Load data
    wl_data = wl_sheet.get_all_values()
    no_data = no_sheet.get_all_values()

    # 4. Load colors (CRITICAL - uses gspread-formatting)
    wl_colors = {}
    for row_num in range(2, len(wl_data) + 1):
        try:
            fmt = get_effective_format(wl_sheet, f'A{row_num}')
            if fmt and hasattr(fmt, 'backgroundColor'):
                bg = fmt.backgroundColor
                if hasattr(bg, 'red'):
                    r = int(bg.red * 255) if bg.red else 0
                    g = int(bg.green * 255) if bg.green else 0
                    b = int(bg.blue * 255) if bg.blue else 0
                    wl_colors[row_num] = f"#{r:02x}{g:02x}{b:02x}"
        except:
            wl_colors[row_num] = "#ffffff"  # Default white

    # 5. Parse into ProviderRow objects
    wl_rows = []
    for i, row in enumerate(wl_data[1:], 2):  # Skip header
        wl_rows.append(ProviderRow(
            row_num=i,
            practice=row[0] if len(row) > 0 else "",
            phone=row[1] if len(row) > 1 else "",
            address=row[2] if len(row) > 2 else "",
            city=row[3] if len(row) > 3 else "",
            state=row[4] if len(row) > 4 else "",
            zip=row[5] if len(row) > 5 else "",
            qty_2023=row[6] if len(row) > 6 else "",
            qty_2024=row[7] if len(row) > 7 else "",
            qty_2025=row[8] if len(row) > 8 else "",
            status=row[9] if len(row) > 9 else "",
            notes=row[10] if len(row) > 10 else "",
            bg_color=wl_colors.get(i, "#ffffff")
        ))

    # 6. Parse New Orders
    no_rows = []
    for i, row in enumerate(no_data[1:], 2):
        no_rows.append(NewOrderRow(
            row_num=i,
            practice=row[0] if len(row) > 0 else "",
            address=row[2] if len(row) > 2 else "",  # Column C
            city=row[3] if len(row) > 3 else "",
            state=row[4] if len(row) > 4 else "",
            zip=row[5] if len(row) > 5 else "",
            qty_2025=row[8] if len(row) > 8 else "",  # Find QTY column
        ))

    # 7. Get common invalid reasons
    invalid_data = invalid_sheet.get_all_values()
    invalid_reasons = set()
    for row in invalid_data[1:]:
        if len(row) > 6 and row[6]:  # Column G
            invalid_reasons.add(row[6])

    # 8. Store stats sheet reference for later duplication

    return wl_rows, no_rows, invalid_reasons, stats_sheet
```

**Estimated time:** 5-7 seconds (tested)

---

## Phase 2: Validation (In Memory)

### 2.1 Yellow → New Orders Matching

```python
def validate_yellow_to_no(wl_rows, no_rows):
    """Match yellow rows to New Orders"""
    for wl_row in wl_rows:
        if wl_row.bg_color != '#ffff00':
            continue  # Skip non-yellow

        # Find best match in NO
        best_match = None
        best_confidence = 0.0
        best_no_row = None

        for no_row in no_rows:
            # State must match exactly
            if wl_row.state != no_row.state:
                continue

            # Name matching (70% weight, token set ratio)
            name_score = fuzz.token_set_ratio(
                normalize_name(wl_row.practice),
                normalize_name(no_row.practice)
            ) / 100.0

            # Address matching (30% weight)
            addr_score = fuzz.token_set_ratio(
                normalize_address(wl_row.address),
                normalize_address(no_row.address)
            ) / 100.0

            confidence = (name_score * 0.7) + (addr_score * 0.3)

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = no_row
                best_no_row = no_row.row_num

        # Store match
        wl_row.matched_no_row = best_no_row
        wl_row.match_confidence = best_confidence

        # Add to issues based on confidence
        if best_confidence >= 0.95:
            category = "yellow_95"
            severity = "review"  # Quick review
        elif best_confidence >= 0.80:
            category = "yellow_80"
            severity = "review"  # Careful review
        else:
            category = "yellow_low"
            severity = "critical"  # Not found

        # Check QTY match (NO is canon!)
        qty_mismatch = False
        if best_match and best_match.qty_2025 != wl_row.qty_2025:
            qty_mismatch = True

        wl_row.issues.append(Issue(
            category=category,
            severity=severity,
            message=f"Match confidence: {best_confidence*100:.1f}%",
            suggested_action="accept" if best_confidence >= 0.95 else "review",
            data={
                'no_row': best_no_row,
                'no_practice': best_match.practice if best_match else None,
                'no_qty': best_match.qty_2025 if best_match else None,
                'qty_mismatch': qty_mismatch,
                'confidence': best_confidence
            }
        ))

def normalize_name(name):
    """Normalize for comparison"""
    if not name:
        return ""
    # Remove: LLC, PC, PLLC, INC, Dr., Doctor, MD, DO
    # Standardize: & → and
    # Lowercase, strip
    name = re.sub(r'\b(LLC|PC|PLLC|INC|Dr|Doctor|MD|DO)\b', '', name, flags=re.IGNORECASE)
    name = name.replace('&', 'and').replace('+', 'and')
    return name.lower().strip()

def normalize_address(addr):
    """Normalize address for comparison"""
    if not addr:
        return ""
    # USPS abbreviations
    replacements = {
        'street': 'st', 'avenue': 'ave', 'boulevard': 'blvd',
        'drive': 'dr', 'road': 'rd', 'lane': 'ln',
        'suite': 'ste', 'apartment': 'apt', 'building': 'bldg'
    }
    addr_lower = addr.lower()
    for full, abbr in replacements.items():
        addr_lower = addr_lower.replace(full, abbr)
    # Remove suite numbers
    addr_lower = re.sub(r'\b(ste|apt|suite|apartment)\s*\.?\s*\d+\w*\b', '', addr_lower)
    return addr_lower.strip()
```

### 2.2 Reverse Validation (NO → WL)

```python
def validate_no_to_wl(wl_rows, no_rows):
    """Find orphan NO rows (no yellow match in WL)"""
    for no_row in no_rows:
        # Find matching yellow rows
        matches = [
            wl for wl in wl_rows
            if wl.matched_no_row == no_row.row_num
            and wl.bg_color == '#ffff00'
        ]

        no_row.matched_wl_rows = [m.row_num for m in matches]

        if len(matches) == 0:
            no_row.is_orphan = True
            # Will be shown in review as separate category
```

### 2.3 Duplicate Detection

```python
def detect_duplicates(wl_rows):
    """Detect duplicates and networks"""
    # Group by normalized phone
    phone_groups = defaultdict(list)
    for row in wl_rows:
        norm_phone = normalize_phone(row.phone)
        if norm_phone:
            phone_groups[norm_phone].append(row)

    duplicate_groups = []
    network_groups = []

    group_id = 1
    for phone, rows in phone_groups.items():
        if len(rows) <= 1:
            continue

        # Check if exact duplicates
        if is_exact_duplicate_group(rows):
            for row in rows:
                row.duplicate_group_id = group_id
                row.issues.append(Issue(
                    category="exact_dupes",
                    severity="auto_fix",
                    message=f"Exact duplicate ({len(rows)} copies)",
                    suggested_action="delete_all_but_one"
                ))
            duplicate_groups.append(rows)

        # Check if network
        elif is_network_group(rows):
            network_name = extract_network_name_default(rows)
            for row in rows:
                row.network_name = network_name
                row.issues.append(Issue(
                    category="networks",
                    severity="review",
                    message=f"Network detected (~{len(rows)} locations)",
                    suggested_action="confirm_network",
                    data={'network_name': network_name, 'location_count': len(rows)}
                ))
            network_groups.append(rows)

        # Fuzzy duplicates
        else:
            for row in rows:
                row.duplicate_group_id = group_id
                row.issues.append(Issue(
                    category="fuzzy_dupes",
                    severity="review",
                    message=f"Possible duplicate ({len(rows)} similar rows)",
                    suggested_action="review"
                ))
            duplicate_groups.append(rows)

        group_id += 1

def normalize_phone(phone):
    """Normalize phone for matching"""
    if not phone:
        return ""
    # Remove extensions, formatting
    digits = re.sub(r'[^\d]', '', phone)
    return digits[-10:] if len(digits) >= 10 else digits

def is_exact_duplicate_group(rows):
    """Check if all rows are exact duplicates"""
    # Same normalized name
    # Same normalized address
    # All QTY empty or "0"
    # Minimal notes
    first = rows[0]
    for row in rows[1:]:
        if normalize_name(row.practice) != normalize_name(first.practice):
            return False
        if normalize_address(row.address) != normalize_address(first.address):
            return False
    return True

def is_network_group(rows):
    """Check if same network (similar names, different addresses)"""
    # All names ≥85% similar
    # All addresses < 70% similar
    names = [normalize_name(r.practice) for r in rows]
    addrs = [normalize_address(r.address) for r in rows]

    # Check name similarity
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            if fuzz.ratio(names[i], names[j]) < 85:
                return False

    # Check address dissimilarity
    for i in range(len(addrs)):
        for j in range(i+1, len(addrs)):
            if fuzz.ratio(addrs[i], addrs[j]) >= 70:
                return False  # Too similar, not different locations

    return True

def extract_network_name_default(rows):
    """Generate default network name from first row"""
    # Take first provider name, normalize
    name = rows[0].practice
    # Remove location words, numbers, "Medical", "Clinic", etc.
    name = re.sub(r'\b(North|South|East|West|Downtown|Uptown|Medical|Clinic|Center|Office)\b', '', name, flags=re.IGNORECASE)
    # Remove special chars, lowercase, no spaces
    name = re.sub(r'[^a-z]', '', name.lower())
    return name
```

### 2.4 Status-Based Issues

```python
def validate_status_issues(wl_rows):
    """Check status-related issues"""
    for row in wl_rows:
        # Fuschia without vm note
        if row.bg_color == '#ff00ff':
            if 'vm' not in row.notes.lower():
                row.issues.append(Issue(
                    category="fuschia_vm",
                    severity="review",
                    message="Fuschia but no 'vm' in notes",
                    suggested_action="add_vm_note"
                ))

        # Green with "sent"
        elif row.bg_color == '#00ff00':
            if 'sent' in row.notes.lower():
                row.issues.append(Issue(
                    category="green_sent",
                    severity="auto_fix",
                    message="Green with 'sent' → suggest Not interested",
                    suggested_action="convert_to_not_interested"
                ))

        # Red (all need review)
        elif row.bg_color == '#ff0000':
            row.issues.append(Issue(
                category="red_invalid",
                severity="critical",
                message="Marked as Potentially Invalid",
                suggested_action="review_and_move_to_invalid"
            ))

        # Not interested but reason suggests invalid
        elif row.status == 'Not interested':
            if suggests_invalid(row.notes):
                row.issues.append(Issue(
                    category="not_interested_invalid",
                    severity="review",
                    message="'Not interested' but notes suggest invalid provider",
                    suggested_action="move_to_invalid"
                ))

def suggests_invalid(notes):
    """Check if notes suggest provider is invalid"""
    invalid_keywords = [
        'closed', 'disconnected', 'wrong number', 'moved',
        'no longer', 'out of business', 'permanently closed',
        'number out of service', 'not doing ob', 'not an ob'
    ]
    notes_lower = notes.lower()
    return any(kw in notes_lower for kw in invalid_keywords)
```

### 2.5 Not Interested Auto-Fix

```python
def auto_fix_not_interested(wl_rows):
    """Auto-fix not interested rows"""
    fixed = []
    for row in wl_rows:
        if row.status != 'Not interested':
            continue

        changes = []

        # Fix missing note
        if 'not interested' not in row.notes.lower():
            if row.notes:
                row.notes += '; not interested'
            else:
                row.notes = 'not interested'
            changes.append('added_note')

        # Fix QTY
        if row.qty_2025 != '0':
            row.qty_2025 = '0'
            changes.append('set_qty_0')

        # Remove "sent" or ":sent"
        if 'sent' in row.notes.lower():
            row.notes = re.sub(r':?sent', '', row.notes, flags=re.IGNORECASE).strip()
            # Clean up extra semicolons
            row.notes = re.sub(r'\s*;\s*;', ';', row.notes)
            changes.append('removed_sent')

        if changes:
            row.issues.append(Issue(
                category="not_interested",
                severity="auto_fix",
                message=f"Auto-fixed: {', '.join(changes)}",
                suggested_action=None
            ))
            fixed.append(row)

    return fixed
```

### 2.6 Non-Standard Notes Detection

```python
def detect_non_standard_notes(wl_rows):
    """
    Identify notes with non-standard chunks
    Based on actual data analysis (see NOTES_SAMPLE_ANALYSIS.txt)
    """
    # Standard patterns (from analysis: 67% of chunks)
    standard_patterns = [
        'not interested',
        'sent', ':sent',
        'vm x2', 'vm x3', 'vm',
        'network', 'same network',
        'callback', 'call back',
        'repeat',
    ]

    # Clearable patterns (not needed for new year)
    clearable_patterns = [
        'call back', 'callback', 'try again',
        'gave my #', 'ask for', 'attn:',
        'office closed', 'temporarily closed',
        'call back tomorrow', 'call back monday',
    ]

    for row in wl_rows:
        if not row.notes:
            continue

        chunks = [c.strip() for c in row.notes.split(';') if c.strip()]
        non_standard_chunks = []
        clearable_chunks = []

        for chunk in chunks:
            chunk_lower = chunk.lower()

            # Check if standard
            is_standard = any(pattern in chunk_lower for pattern in standard_patterns)

            if not is_standard:
                non_standard_chunks.append(chunk)

                # Check if clearable
                is_clearable = any(pattern in chunk_lower for pattern in clearable_patterns)
                if is_clearable:
                    clearable_chunks.append(chunk)

        if non_standard_chunks:
            row.issues.append(Issue(
                category="non_standard_notes",
                severity="review",
                message=f"{len(non_standard_chunks)} non-standard note chunks",
                suggested_action="review_and_clean",
                data={
                    'non_standard_chunks': non_standard_chunks,
                    'clearable_chunks': clearable_chunks,
                    'all_chunks': chunks
                }
            ))
```

### 2.7 Categorize All Issues

```python
def categorize_issues(wl_rows, no_rows):
    """Organize issues into review categories"""
    categories = [
        ReviewCategory(
            id="exact_dupes",
            name="Exact Duplicates",
            rows=[],
            allow_batch=True,
            batch_actions=["delete_all_but_one"],
            description="Identical rows (same name, address, phone)"
        ),
        ReviewCategory(
            id="networks",
            name="Networks",
            rows=[],
            allow_batch=True,
            batch_actions=["confirm_network", "mass_add_to_invalid"],
            description="Same phone, similar names, different locations"
        ),
        ReviewCategory(
            id="fuzzy_dupes",
            name="Fuzzy Duplicates",
            rows=[],
            allow_batch=True,
            batch_actions=["merge_all"],
            description="Similar rows that might be duplicates"
        ),
        ReviewCategory(
            id="yellow_95",
            name="Yellow 95%+ Match",
            rows=[],
            allow_batch=True,
            batch_actions=["accept_all"],
            description="High-confidence matches to New Orders"
        ),
        ReviewCategory(
            id="yellow_80",
            name="Yellow 80-94% Match",
            rows=[],
            allow_batch=False,
            description="Medium-confidence matches (review carefully)"
        ),
        ReviewCategory(
            id="yellow_low",
            name="Yellow <80% (Not Found)",
            rows=[],
            allow_batch=False,
            description="Yellow rows not found in New Orders"
        ),
        ReviewCategory(
            id="orphan_no",
            name="Orphan New Orders",
            rows=[],  # Will contain NO rows, not WL rows
            allow_batch=False,
            description="New Orders without yellow match in Working List"
        ),
        ReviewCategory(
            id="green_sent",
            name="Green 'Sent' Emails",
            rows=[],
            allow_batch=True,
            batch_actions=["convert_all_to_not_interested"],
            description="Requested email with 'sent' in notes"
        ),
        ReviewCategory(
            id="fuschia_vm",
            name="Fuschia Voicemails",
            rows=[],
            allow_batch=False,
            description="Voicemail status, check notes"
        ),
        ReviewCategory(
            id="red_invalid",
            name="Red (Potentially Invalid)",
            rows=[],
            allow_batch=False,
            description="Review and move to Invalid List"
        ),
        ReviewCategory(
            id="not_interested",
            name="Not Interested (Auto-Fixed)",
            rows=[],
            allow_batch=True,
            batch_actions=["confirm_all_fixes"],
            description="Auto-fixed missing notes/QTY"
        ),
        ReviewCategory(
            id="non_standard_notes",
            name="Non-Standard Notes",
            rows=[],
            allow_batch=False,
            description="Uncommon note chunks for cleanup"
        ),
    ]

    # Populate categories
    for row in wl_rows:
        for issue in row.issues:
            for cat in categories:
                if cat.id == issue.category:
                    if row not in cat.rows:
                        cat.rows.append(row)

    # Add orphan NO rows to special category
    orphan_cat = next(c for c in categories if c.id == "orphan_no")
    for no_row in no_rows:
        if no_row.is_orphan:
            orphan_cat.rows.append(no_row)  # Note: NO rows, not WL rows!

    # Filter out empty categories
    categories = [c for c in categories if len(c.rows) > 0]

    return categories
```

**Estimated time:** 15-20 seconds for 737 rows

---

## Phase 3: Textual TUI (Interactive Review)

### App Structure

```python
class EOYToolApp(App):
    """Main Textual app"""

    CSS = """
    DataTable {
        height: 1fr;
    }

    .actions {
        dock: bottom;
        height: auto;
        padding: 1;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $panel;
    }
    """

    BINDINGS = [
        ("f1", "help", "Help"),
        ("f2", "save_progress", "Save Progress"),
        ("f3", "toggle_batch", "Batch Mode"),
        ("escape", "quit", "Quit"),
    ]

    def __init__(self, categories, wl_rows, no_rows, year):
        super().__init__()
        self.categories = categories
        self.wl_rows = wl_rows
        self.no_rows = no_rows
        self.year = year
        self.current_category_idx = 0
        self.decisions = []

    def compose(self) -> ComposeResult:
        """Create UI layout"""
        yield Header()

        # Category tabs
        with TabbedContent():
            for cat in self.categories:
                with TabPane(cat.name, id=cat.id):
                    yield Label(cat.description)
                    yield DataTable(id=f"table_{cat.id}")

                    # Action buttons
                    with Horizontal(classes="actions"):
                        yield Button("Keep", id="btn_keep", variant="primary")
                        yield Button("Delete", id="btn_delete", variant="error")
                        yield Button("Edit", id="btn_edit")
                        yield Button("Skip", id="btn_skip")

                        if cat.allow_batch:
                            for action in cat.batch_actions:
                                yield Button(
                                    action.replace('_', ' ').title(),
                                    id=f"btn_batch_{action}"
                                )

        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self):
        """Initialize when app starts"""
        self.populate_current_category()

    def populate_current_category(self):
        """Fill table with rows from current category"""
        cat = self.categories[self.current_category_idx]
        table = self.query_one(f"#table_{cat.id}", DataTable)

        # Add columns
        table.add_columns("Row", "Practice", "Phone", "Address", "City", "QTY", "Notes")

        # Add rows
        for row in cat.rows:
            table.add_row(
                str(row.row_num),
                row.practice[:30],  # Truncate
                row.phone,
                row.address[:30],
                row.city,
                row.qty_2025,
                row.notes[:30] if row.notes else ""
            )

    # Event handlers for buttons...
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "btn_keep":
            self.handle_keep()
        elif button_id == "btn_delete":
            self.handle_delete()
        elif button_id == "btn_edit":
            self.handle_edit()
        # ... etc
```

### Textual Screens (Modals)

#### Edit Row Screen

```python
class EditRowScreen(Screen):
    """Modal screen for editing a row"""

    def __init__(self, row: ProviderRow):
        super().__init__()
        self.row = row
        self.changes = {}

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Editing Row {self.row.row_num}: {self.row.practice}"),
            Input(value=self.row.practice, placeholder="Practice", id="edit_practice"),
            Input(value=self.row.phone, placeholder="Phone", id="edit_phone"),
            Input(value=self.row.address, placeholder="Address", id="edit_address"),
            Input(value=self.row.city, placeholder="City", id="edit_city"),
            Input(value=self.row.state, placeholder="State (2 letters)", id="edit_state"),
            Input(value=self.row.zip, placeholder="Zip", id="edit_zip"),
            Input(value=self.row.qty_2025, placeholder="2025 QTY (empty or 0)", id="edit_qty"),
            Input(value=self.row.status, placeholder="Status", id="edit_status"),
            TextArea(self.row.notes, id="edit_notes"),
            Label("Notes Chunks (check to delete):"),
            *self.create_note_checkboxes(),
            Horizontal(
                Button("Save", variant="primary", id="btn_save"),
                Button("Cancel", id="btn_cancel"),
            )
        )

    def create_note_checkboxes(self):
        """Create checkboxes for each note chunk"""
        if not self.row.notes:
            return []

        chunks = [c.strip() for c in self.row.notes.split(';') if c.strip()]
        checkboxes = []
        for i, chunk in enumerate(chunks):
            checkboxes.append(
                Checkbox(chunk, value=False, id=f"chunk_{i}")
            )
        return checkboxes

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_save":
            self.save_changes()
            self.dismiss(True)
        elif event.button.id == "btn_cancel":
            self.dismiss(False)

    def save_changes(self):
        """Collect changes from form"""
        self.changes = {
            'practice': self.query_one("#edit_practice", Input).value,
            'phone': self.query_one("#edit_phone", Input).value,
            'address': self.query_one("#edit_address", Input).value,
            'city': self.query_one("#edit_city", Input).value,
            'state': self.query_one("#edit_state", Input).value,
            'zip': self.query_one("#edit_zip", Input).value,
            'qty_2025': self.query_one("#edit_qty", Input).value,
            'status': self.query_one("#edit_status", Input).value,
            'notes': self.query_one("#edit_notes", TextArea).text,
        }

        # Handle deleted note chunks
        deleted_chunks = []
        for checkbox in self.query(Checkbox):
            if checkbox.value:  # Checked = delete
                chunk_id = checkbox.id
                deleted_chunks.append(int(chunk_id.split('_')[1]))

        if deleted_chunks:
            chunks = [c.strip() for c in self.row.notes.split(';') if c.strip()]
            remaining = [c for i, c in enumerate(chunks) if i not in deleted_chunks]
            self.changes['notes'] = '; '.join(remaining)
```

#### Network Confirmation Screen

```python
class NetworkConfirmScreen(Screen):
    """Screen for confirming network and editing network name"""

    def __init__(self, network_rows: List[ProviderRow], default_name: str):
        super().__init__()
        self.network_rows = network_rows
        self.default_name = default_name
        self.action = None

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Network Detected ({len(self.network_rows)} locations)"),
            DataTable(id="network_table"),
            Label("Network name:"),
            Input(value=self.default_name, placeholder="networkname", id="network_name"),
            Label("Actions:"),
            Button("Confirm Network", variant="primary", id="btn_confirm"),
            Button("Not a Network (review individually)", id="btn_not_network"),
            Button("Mass Add to Invalid List", variant="error", id="btn_mass_invalid"),
            Button("Google Search All", id="btn_google_all"),
        )

    def on_mount(self):
        table = self.query_one("#network_table", DataTable)
        table.add_columns("Row", "Practice", "Phone", "Address")
        for row in self.network_rows:
            table.add_row(
                str(row.row_num),
                row.practice,
                row.phone,
                row.address
            )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_confirm":
            self.action = "confirm"
            self.dismiss(True)
        elif event.button.id == "btn_not_network":
            self.action = "not_network"
            self.dismiss(False)
        elif event.button.id == "btn_mass_invalid":
            self.action = "mass_invalid"
            self.dismiss(True)
        elif event.button.id == "btn_google_all":
            self.open_google_searches()
```

#### Invalid Reason Screen

```python
class InvalidReasonScreen(Screen):
    """Screen for selecting invalid reason"""

    def __init__(self, common_reasons: set):
        super().__init__()
        self.common_reasons = common_reasons
        self.selected_reason = None
        self.custom_reason = None

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Select reason for moving to Invalid/Inactive List:"),
            RadioSet(
                *[RadioButton(reason, id=f"reason_{i}")
                  for i, reason in enumerate(sorted(self.common_reasons))],
                RadioButton("CUSTOM (type below)", id="reason_custom"),
                id="reason_radio"
            ),
            Input(placeholder="Type custom reason...", id="custom_reason"),
            Horizontal(
                Button("OK", variant="primary", id="btn_ok"),
                Button("Cancel", id="btn_cancel"),
            )
        )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_ok":
            radio = self.query_one("#reason_radio", RadioSet)
            if radio.pressed_button.id == "reason_custom":
                self.custom_reason = self.query_one("#custom_reason", Input).value
                self.selected_reason = self.custom_reason
            else:
                idx = int(radio.pressed_button.id.split('_')[1])
                self.selected_reason = sorted(self.common_reasons)[idx]
            self.dismiss(True)
        elif event.button.id == "btn_cancel":
            self.dismiss(False)
```

#### Match Review Screen

```python
class MatchReviewScreen(Screen):
    """Screen for reviewing yellow→NO matches"""

    def __init__(self, wl_row: ProviderRow, no_match, confidence: float):
        super().__init__()
        self.wl_row = wl_row
        self.no_match = no_match
        self.confidence = confidence
        self.action = None

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Yellow Row {self.wl_row.row_num} Match Review"),
            Label(f"Confidence: {self.confidence*100:.1f}%"),

            Label("\n=== Working List ==="),
            Static(f"Practice: {self.wl_row.practice}"),
            Static(f"Address: {self.wl_row.address}"),
            Static(f"Phone: {self.wl_row.phone}"),
            Static(f"2025 QTY: {self.wl_row.qty_2025}"),

            Label("\n=== New Orders (CANON) ==="),
            Static(f"Practice: {self.no_match.practice if self.no_match else 'NOT FOUND'}"),
            Static(f"Address: {self.no_match.address if self.no_match else ''}"),
            Static(f"2025 QTY: {self.no_match.qty_2025 if self.no_match else ''}"),

            Label("\n=== Actions ==="),
            Button("Accept Match", variant="primary", id="btn_accept"),
            Button("Not Found (change WL to white)", id="btn_not_found"),
            Button("Edit WL Row", id="btn_edit"),
            Button("Google Search", id="btn_google"),
            Button("Skip", id="btn_skip"),
        )

    def on_button_pressed(self, event: Button.Pressed):
        self.action = event.button.id.replace('btn_', '')
        self.dismiss(self.action != 'skip')
```

---

## Phase 4: Shadow Worksheet Creation

```python
def create_shadow_worksheets(gc, sh, year, wl_rows, invalid_rows):
    """
    Create shadow worksheets at END of process
    All changes already applied to in-memory objects
    """
    print("\n[Phase 4] Creating shadow worksheets...")

    # 1. Duplicate Working List
    print("  Duplicating Working List...")
    wl_orig = sh.worksheet(f'Working List {year}')
    wl_cleanup = wl_orig.duplicate(
        new_sheet_name=f'Working List {year}_CLEANUP'
    )
    print(f"  Created: {wl_cleanup.title}")

    # 2. Duplicate Invalid/Inactive List
    print("  Duplicating Invalid/Inactive List...")
    invalid_orig = sh.worksheet('Invalid/Inactive List')
    invalid_cleanup = invalid_orig.duplicate(
        new_sheet_name='Invalid/Inactive List_CLEANUP'
    )
    print(f"  Created: {invalid_cleanup.title}")

    # 3. Duplicate STATS
    print("  Duplicating STATS...")
    stats_orig = sh.worksheet('STATS')
    stats_cleanup = stats_orig.duplicate(
        new_sheet_name='STATS_CLEANUP'
    )
    print(f"  Created: {stats_cleanup.title}")

    # 4. Update STATS formulas
    print("  Updating STATS formulas to reference _CLEANUP sheets...")
    update_stats_formulas(stats_cleanup, year)

    return wl_cleanup, invalid_cleanup, stats_cleanup

def update_stats_formulas(stats_cleanup, year):
    """Update all formulas in STATS to reference _CLEANUP sheets"""
    # Get all formulas
    all_cells = stats_cleanup.get('A1:Z52', value_render_option='FORMULA')

    updated = []
    changes_made = 0

    for row_idx, row in enumerate(all_cells):
        updated_row = []
        for cell in row:
            if isinstance(cell, str) and f'Working List {year}' in cell:
                # Replace: 'Working List 2025' → 'Working List 2025_CLEANUP'
                # Handle both quote styles
                old_ref = f"'Working List {year}'"
                new_ref = f"'Working List {year}_CLEANUP'"
                cell = cell.replace(old_ref, new_ref)

                # Also handle without quotes (shouldn't exist but be safe)
                old_ref_nq = f"Working List {year}"
                new_ref_nq = f"Working List {year}_CLEANUP"
                if old_ref_nq in cell and new_ref not in cell:
                    cell = cell.replace(old_ref_nq, new_ref_nq)

                changes_made += 1

            updated_row.append(cell)
        updated.append(updated_row)

    # Write back
    stats_cleanup.update('A1:Z52', updated, value_input_option='USER_ENTERED')
    print(f"  Updated {changes_made} formula references")
```

---

## Phase 5: Write Changes to Shadow Worksheets

```python
def write_changes_to_shadow(wl_cleanup, invalid_cleanup, wl_rows, invalid_additions, deleted_rows):
    """
    Write all changes to shadow worksheets
    Uses batch operations for efficiency
    """
    print("\n[Phase 5] Writing changes to shadow worksheets...")

    # 1. Update Working List cells (batch)
    print("  Building batch updates for Working List...")
    updates = []

    for row in wl_rows:
        if row.action == 'delete':
            continue  # Handle separately

        # Check if any fields changed
        if row.field_edits:
            for field, new_value in row.field_edits.items():
                # Map field name to column
                col_map = {
                    'practice': 1,
                    'phone': 2,
                    'address': 3,
                    'city': 4,
                    'state': 5,
                    'zip': 6,
                    'qty_2023': 7,
                    'qty_2024': 8,
                    'qty_2025': 9,
                    'status': 10,
                    'notes': 11,
                }
                col = col_map.get(field)
                if col:
                    cell = gspread.utils.rowcol_to_a1(row.row_num, col)
                    updates.append({
                        'range': cell,
                        'values': [[new_value]]
                    })

    if updates:
        print(f"  Batch updating {len(updates)} cells...")
        wl_cleanup.batch_update(updates, value_input_option='USER_ENTERED')
        print(f"  Done!")

    # 2. Delete rows (reverse order to preserve indices)
    if deleted_rows:
        print(f"  Deleting {len(deleted_rows)} duplicate rows...")
        for row_num in sorted(deleted_rows, reverse=True):
            wl_cleanup.delete_rows(row_num)
        print(f"  Done!")

    # 3. Add to Invalid/Inactive List (batch append)
    if invalid_additions:
        print(f"  Adding {len(invalid_additions)} rows to Invalid List...")
        rows_to_add = []
        for addition in invalid_additions:
            # Format: [Name, Phone, Address, City, ST, Zip, INVALID/INACTIVE, Notes]
            # Notes should include QTY history if exists
            notes = addition.get('notes', '')
            if addition.get('qty_2023') or addition.get('qty_2024') or addition.get('qty_2025'):
                qty_parts = []
                if addition.get('qty_2023'):
                    qty_parts.append(f"2023 QTY: {addition['qty_2023']}")
                if addition.get('qty_2024'):
                    qty_parts.append(f"2024 QTY: {addition['qty_2024']}")
                if addition.get('qty_2025'):
                    qty_parts.append(f"2025 QTY: {addition['qty_2025']}")

                qty_note = '; '.join(qty_parts)
                notes = f"{notes}; {qty_note}" if notes else qty_note

            rows_to_add.append([
                addition['practice'],
                addition['phone'],
                addition['address'],
                addition['city'],
                addition['state'],
                addition['zip'],
                addition['reason'],  # INVALID or INACTIVE
                notes
            ])

        invalid_cleanup.append_rows(rows_to_add, value_input_option='USER_ENTERED')
        print(f"  Done!")

def validate_stats_changes(stats_orig, stats_cleanup):
    """
    Validate STATS formulas still work
    Compare before/after counts
    """
    print("\n[Phase 5b] Validating STATS changes...")

    test_cells = [
        ('C2', 'Yellow count'),
        ('C3', 'Not interested count'),
        ('C4', 'Fuschia count'),
        ('C5', 'Uncalled count'),
        ('C6', 'Red count'),
    ]

    errors = []
    warnings = []

    for cell_addr, description in test_cells:
        # Read original
        orig_val = stats_orig.acell(cell_addr).value
        # Read new
        new_val = stats_cleanup.acell(cell_addr).value

        try:
            orig_num = int(orig_val) if orig_val else 0
            new_num = int(new_val) if new_val else 0

            # Check if drastically different
            if abs(orig_num - new_num) > 100:
                errors.append(f"{description}: Changed from {orig_num} to {new_num} (diff: {abs(orig_num - new_num)})")
            elif abs(orig_num - new_num) > 50:
                warnings.append(f"{description}: Changed from {orig_num} to {new_num} (diff: {abs(orig_num - new_num)})")
            else:
                print(f"  {description}: {orig_num} → {new_num} [OK]")

        except ValueError:
            errors.append(f"{description}: Non-numeric value (orig: {orig_val}, new: {new_val})")

    if errors:
        print("\n  [FAIL] STATS validation failed:")
        for err in errors:
            print(f"    - {err}")
        return False, errors

    if warnings:
        print("\n  [WARN] STATS validation warnings:")
        for warn in warnings:
            print(f"    - {warn}")

    print("\n  [OK] STATS validation passed!")
    return True, []

def rollback_shadows(sh, year):
    """Delete shadow worksheets if validation fails"""
    print("\n[Rollback] Deleting shadow worksheets...")
    try:
        for sheet_name in [
            f'Working List {year}_CLEANUP',
            'Invalid/Inactive List_CLEANUP',
            'STATS_CLEANUP'
        ]:
            try:
                ws = sh.worksheet(sheet_name)
                sh.del_worksheet(ws)
                print(f"  Deleted: {sheet_name}")
            except:
                pass
    except Exception as e:
        print(f"  Error during rollback: {e}")
```

---

## Progress Save/Resume System

```python
def save_progress(year, decisions, current_category_idx, wl_rows):
    """
    Save progress to JSON file
    Format: eoy_progress_YYYYMMDD_HHMMSS.json
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eoy_progress_{timestamp}.json"

    # Build progress data
    progress = {
        'session_id': timestamp,
        'year': year,
        'started_at': timestamp,
        'current_category_idx': current_category_idx,
        'decisions_count': len(decisions),
        'decisions': decisions,
        'row_changes': []
    }

    # Collect all row changes
    for row in wl_rows:
        if row.action or row.field_edits:
            progress['row_changes'].append({
                'row_num': row.row_num,
                'practice': row.practice,  # For identification
                'phone': row.phone,        # For identification
                'action': row.action,
                'field_edits': row.field_edits
            })

    # Write to file
    with open(filename, 'w') as f:
        json.dump(progress, f, indent=2)

    print(f"\n[Progress saved to {filename}]")
    return filename

def load_progress(filename):
    """Load progress from JSON file"""
    with open(filename, 'r') as f:
        progress = json.load(f)

    print(f"\nLoaded progress from: {filename}")
    print(f"  Session started: {progress['started_at']}")
    print(f"  Decisions made: {progress['decisions_count']}")
    print(f"  Current category: {progress['current_category_idx']}")

    return progress

def apply_saved_progress(wl_rows, progress):
    """Apply saved decisions to current data"""
    # Match rows by practice + phone (more robust than row number)
    applied = 0

    for change in progress['row_changes']:
        # Find matching row
        for row in wl_rows:
            if (row.practice == change['practice'] and
                row.phone == change['phone']):
                row.action = change.get('action')
                row.field_edits = change.get('field_edits', {})
                applied += 1
                break

    print(f"  Applied {applied} saved changes to current data")
    return applied
```

---

## Error Handling & Edge Cases

### Case 1: Sheet Modified Between Sessions

```python
def detect_sheet_changes(wl_sheet, progress):
    """Warn if sheet changed since progress saved"""
    current_row_count = wl_sheet.row_count
    # Could store row count in progress, compare
    # For v1: just warn user
    print("[WARN] Sheet may have changed since progress saved")
    print("       Row numbers might be inaccurate")
    print("       Matching by practice+phone instead")
```

### Case 2: Network with Different Names

```python
# Already handled in network confirmation screen
# User can review individually if names don't match
```

### Case 3: Duplicate with Both QTY in NO

```python
def handle_duplicate_both_in_no(dup_rows, no_rows):
    """
    When both duplicate rows have matching orders in NO
    User decides: keep both, merge, or pick one
    """
    # Check NO for both
    no_matches = []
    for dup in dup_rows:
        for no in no_rows:
            if no.row_num == dup.matched_no_row:
                no_matches.append((dup, no))

    if len(no_matches) == len(dup_rows):
        # Both have orders in NO!
        # Show special screen
        return "show_both_valid_screen"
```

### Case 4: Phone Number Formatting Variations

```python
# Already handled in normalize_phone()
# Strips all formatting, takes last 10 digits
```

---

## Helper Functions

### Google Search Helper

```python
def open_google_search(row):
    """Open Google search for provider"""
    import webbrowser

    query = f"{row.practice} {row.address} {row.city} {row.state}"
    url = f"https://www.google.com/search?q={quote_plus(query)}"

    # Open in browser
    webbrowser.open(url)

    # Also print URL for reference
    print(f"Google search: {url}")
```

### Fuzzy Match Threshold Testing

```python
def test_fuzzy_thresholds():
    """
    Test thresholds on sample data
    Justifies 95/80/60 thresholds
    """
    test_cases = [
        # (name1, name2, address1, address2, expected_category)
        ("Smith Family Practice", "Family Practice Smith", "123 Main St", "123 Main Street", "95+"),
        ("Smith Family Practice", "Smith Practice", "123 Main St", "123 Main St", "95+"),
        ("Johnson Medical", "Johnson Clinic", "456 Oak Ave", "456 Oak Ave", "80-94"),
        ("ABC Women's Health", "XYZ Women's Health", "789 Elm St", "789 Elm St", "<80"),
    ]

    for name1, name2, addr1, addr2, expected in test_cases:
        name_score = fuzz.token_set_ratio(name1, name2) / 100.0
        addr_score = fuzz.token_set_ratio(addr1, addr2) / 100.0
        confidence = (name_score * 0.7) + (addr_score * 0.3)

        category = "95+" if confidence >= 0.95 else ("80-94" if confidence >= 0.80 else "<80")

        print(f"{name1} vs {name2}")
        print(f"  Name: {name_score*100:.1f}%, Addr: {addr_score*100:.1f}%")
        print(f"  Confidence: {confidence*100:.1f}% → {category} [Expected: {expected}]")
        print()
```

---

## Complete File Structure

```
scripts/eoy_obgyn_tool.py           # Main application
├── main()                          # Entry point
├── Phase 1: load_data()
├── Phase 2: Validation functions
│   ├── validate_yellow_to_no()
│   ├── validate_no_to_wl()
│   ├── detect_duplicates()
│   ├── validate_status_issues()
│   ├── auto_fix_not_interested()
│   ├── detect_non_standard_notes()
│   └── categorize_issues()
├── Phase 3: Textual App
│   ├── class EOYToolApp(App)
│   ├── class EditRowScreen(Screen)
│   ├── class NetworkConfirmScreen(Screen)
│   ├── class InvalidReasonScreen(Screen)
│   └── class MatchReviewScreen(Screen)
├── Phase 4: create_shadow_worksheets()
├── Phase 5: write_changes_to_shadow()
├── Progress: save/load/apply functions
└── Helpers: normalize, google search, etc.
```

**Estimated file size:** 1500-2000 lines
**Estimated build time:** 4-6 hours
**Estimated first run time:** 2-4 hours (user review)

---

## ARCHITECTURE V2 COMPLETE ✅

**All gaps resolved:**
- ✅ Color reading (gspread-formatting)
- ✅ Fuzzy matching (rapidfuzz, token_set_ratio)
- ✅ UI framework (Textual with screens, tables, buttons)
- ✅ Duplicate QTY logic (NO is canon)
- ✅ Reverse validation (NO→WL orphans)
- ✅ Network naming (user provides, smart default)
- ✅ Shadow worksheets (created at end)
- ✅ Non-standard notes (analyzed actual data, 33% of chunks)
- ✅ Batch operations (always available)
- ✅ Progress save/resume
- ✅ Error handling
- ✅ STATS validation

**Ready for implementation!**
