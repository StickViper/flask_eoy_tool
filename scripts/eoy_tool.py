"""
EOY Cleanup Tool - Flask Web Application
Healthcare Provider Data Cleanup for End of Year Reset

Architecture: Flask backend + HTML/CSS/JS frontend
Design: "Data Atelier" - Refined craftsmanship aesthetic
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
# from gspread_formatting import get_effective_format  # Unused
from oauth2client.service_account import ServiceAccountCredentials
from rapidfuzz import fuzz
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json
import os
import re
from datetime import datetime
from collections import defaultdict
import webbrowser
import threading

import sys
import os
import argparse

# Configure Flask to look for templates/static in parent directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(parent_dir, 'templates')
static_dir = os.path.join(parent_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-prod')

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ProviderRow:
    """Single row from Working List"""
    row_num: int
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
    bg_color: str

    # Validation results
    issues: List[Dict] = field(default_factory=list)
    matched_no_row: Optional[int] = None
    match_confidence: float = 0.0
    duplicate_group_id: Optional[int] = None
    network_name: Optional[str] = None

    # User decisions
    action: Optional[str] = None
    field_edits: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'qty_2023': self.qty_2023,
            'qty_2024': self.qty_2024,
            'qty_2025': self.qty_2025,
            'status': self.status,
            'notes': self.notes,
            'bg_color': self.bg_color,
            'issues': self.issues,
            'matched_no_row': self.matched_no_row,
            'match_confidence': self.match_confidence,
            'duplicate_group_id': self.duplicate_group_id,
            'network_name': self.network_name,
            'action': self.action,
            'field_edits': self.field_edits
        }

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

    matched_wl_rows: List[int] = field(default_factory=list)
    is_orphan: bool = False

    def to_dict(self):
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'qty_2025': self.qty_2025,
            'matched_wl_rows': self.matched_wl_rows,
            'is_orphan': self.is_orphan
        }

@dataclass
class InvalidRow:
    """Single row from Invalid/Inactive List"""
    row_num: int
    practice: str
    phone: str
    address: str
    city: str
    state: str
    zip: str
    reason: str      # Column G: INVALID/INACTIVE reason
    notes: str       # Column H: Notes (may contain QTY info)

    def to_dict(self):
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip': self.zip,
            'reason': self.reason,
            'notes': self.notes
        }

@dataclass
class ReviewCategory:
    """Group of issues for review"""
    id: str
    name: str
    description: str
    row_nums: List[int]
    allow_batch: bool
    primary_action: Optional[str] = None
    secondary_actions: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'row_count': len(self.row_nums),
            'row_nums': self.row_nums,
            'allow_batch': self.allow_batch,
            'primary_action': self.primary_action,
            'secondary_actions': self.secondary_actions
        }

# ============================================================================
# GLOBAL STATE (in-memory session storage)
# ============================================================================

class AppState:
    """Application state management"""
    def __init__(self):
        self.wl_rows: List[ProviderRow] = []
        self.no_rows: List[NewOrderRow] = []
        self.invalid_rows: List[InvalidRow] = []
        self.categories: List[ReviewCategory] = []
        self.invalid_reasons: set = set()
        self.year: int = 2025
        self.undo_stack: List[Dict] = []
        self.redo_stack: List[Dict] = []
        self.current_category_id: Optional[str] = None
        self.loaded: bool = False

    def to_dict(self):
        """Serialize state for JSON storage"""
        return {
            'wl_rows': [row.to_dict() for row in self.wl_rows],
            'no_rows': [row.to_dict() for row in self.no_rows],
            'invalid_rows': [row.to_dict() for row in self.invalid_rows],
            'categories': [cat.to_dict() for cat in self.categories],
            'invalid_reasons': list(self.invalid_reasons),
            'year': self.year,
            'undo_stack': self.undo_stack[-50:],  # Keep last 50
            'current_category_id': self.current_category_id,
            'loaded': self.loaded
        }

class NotesValidator:
    """Validator for note patterns with action associations

    Loads patterns from config/notes_patterns.json and provides methods
    to categorize note chunks and suggest appropriate actions.
    """

    def __init__(self, config_path='config/notes_patterns.json'):
        self.config_path = config_path
        self.patterns = {}
        self.loaded = False

    def load_patterns(self) -> bool:
        """Load patterns from config file"""
        import json
        import os

        if not os.path.exists(self.config_path):
            print(f"Warning: Notes patterns config not found at {self.config_path}")
            return False

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Filter out underscore-prefixed metadata keys
            self.patterns = {k: v for k, v in config.items() if not k.startswith('_')}
            self.loaded = True
            return True

        except Exception as e:
            print(f"Error loading notes patterns: {e}")
            return False

    def get_note_category(self, note_chunk: str) -> dict:
        """Determine category and suggested actions for a note chunk

        Args:
            note_chunk: The note text to categorize

        Returns:
            dict with keys: category, action, suggested_actions, description
        """
        if not self.loaded:
            self.load_patterns()

        chunk_lower = note_chunk.lower().strip()

        # Check each pattern category
        for category, config in self.patterns.items():
            for pattern in config.get('patterns', []):
                if pattern.lower() in chunk_lower:
                    return {
                        'category': category,
                        'action': config.get('action', 'FLAG_REVIEW'),
                        'suggested_actions': config.get('suggested_actions', []),
                        'description': config.get('description', '')
                    }

        # Unknown pattern - flag for review
        return {
            'category': 'unknown',
            'action': 'FLAG_REVIEW',
            'suggested_actions': [],
            'description': 'Unrecognized pattern - needs manual review'
        }

    def categorize_notes(self, notes: str) -> list:
        """Categorize all chunks in a notes field

        Args:
            notes: Semicolon-separated notes string

        Returns:
            list of dicts with chunk, category, action, suggested_actions
        """
        if not notes:
            return []

        chunks = [c.strip() for c in notes.split(';') if c.strip()]
        results = []

        for chunk in chunks:
            category_info = self.get_note_category(chunk)
            results.append({
                'chunk': chunk,
                **category_info
            })

        return results

    def should_preserve_notes(self, notes: str) -> tuple:
        """Check if notes should be preserved during edits

        Args:
            notes: Semicolon-separated notes string

        Returns:
            (should_preserve: bool, reason: str)
        """
        categorized = self.categorize_notes(notes)

        for item in categorized:
            if item['action'] == 'PRESERVE':
                return (True, f"Contains {item['category']}: {item['chunk']}")

        return (False, "No preservation patterns found")

# Global state instance
state = AppState()

# Global notes validator instance
notes_validator = NotesValidator()

# ============================================================================
# PHASE 1: DATA LOADING
# ============================================================================

def status_to_color(status: str) -> str:
    """
    Map status column text to expected background color.
    This avoids 737 individual API calls to read colors.

    Status values are set by user and trigger onEdit() to update colors.
    We use Status as the source of truth to avoid rate limits.
    """
    if not status:
        return "#ffffff"  # White (uncalled/empty)

    status_lower = status.lower().strip()

    # EXACT MATCH enforcement (Decision Q1)
    # We do NOT use substring matching anymore to prevent "Voicemail" matching "Voicemail/No Answer"
    
    status_map = {
        'successful order': '#ffff00',    # Yellow
        'voicemail/no answer': '#ff00ff', # Fuschia
        'not interested': '#ffffff',      # White
        'potentially invalid': '#ff0000', # Red
        'requested email': '#00ff00',     # Green
        'email': '#00ff00',               # Green (Legacy/Alternative)
        '': '#ffffff'                     # Empty = White
    }
    
    return status_map.get(status_lower, '#ffffff')

def load_data(year: int = 2025):
    """Load all data from Google Sheets"""
    print(f"[Phase 1] Loading data from Google Sheets...")

    # Authenticate
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(creds)

    # Open by spreadsheet ID to bypass Drive API
    sh = gc.open_by_key('1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0')

    # Get worksheets
    wl_sheet = sh.worksheet(f'Working List {year}')
    no_sheet = sh.worksheet(f'New Orders {year}')
    invalid_sheet = sh.worksheet('Invalid/Inactive List')

    # Load data
    wl_data = wl_sheet.get_all_values()
    no_data = no_sheet.get_all_values()
    invalid_data = invalid_sheet.get_all_values()

    print(f"  Loaded {len(wl_data)-1} Working List rows")
    print(f"  Loaded {len(no_data)-1} New Orders rows")

    # IMPORTANT: We derive colors from Status column instead of reading individually
    # Reading colors individually = 737 API calls > 60/minute quota limit
    # Status column text maps to colors via onEdit() Apps Script automation
    print(f"  Deriving colors from Status column (avoiding API rate limits)...")

    # Parse Working List
    wl_rows = []
    for i, row in enumerate(wl_data[1:], 2):
        if len(row) < 11:
            continue

        # Get status text and derive color from it
        status = row[9] if len(row) > 9 else ""
        bg_color = status_to_color(status)

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
            status=status,
            notes=row[10] if len(row) > 10 else "",
            bg_color=bg_color
        ))

    # Parse New Orders
    no_rows = []
    for i, row in enumerate(no_data[1:], 2):
        if len(row) < 7 or not row[2]:  # Skip if no practice name
            continue
        no_rows.append(NewOrderRow(
            row_num=i,
            practice=row[2] if len(row) > 2 else "",
            address=row[3] if len(row) > 3 else "",
            city=row[4] if len(row) > 4 else "",
            state=row[5] if len(row) > 5 else "",
            zip=row[6] if len(row) > 6 else "",
            qty_2025=row[7] if len(row) > 7 else ""
        ))

    # Parse Invalid/Inactive List
    invalid_rows = []
    for i, row in enumerate(invalid_data[1:], 2):
        if len(row) < 7:  # Skip if not enough columns
            continue
        invalid_rows.append(InvalidRow(
            row_num=i,
            practice=row[0] if len(row) > 0 else "",
            phone=row[1] if len(row) > 1 else "",
            address=row[2] if len(row) > 2 else "",
            city=row[3] if len(row) > 3 else "",
            state=row[4] if len(row) > 4 else "",
            zip=row[5] if len(row) > 5 else "",
            reason=row[6] if len(row) > 6 else "",
            notes=row[7] if len(row) > 7 else ""
        ))

    # Get common invalid reasons
    invalid_reasons = set()
    for row in invalid_data[1:]:
        if len(row) > 6 and row[6]:
            invalid_reasons.add(row[6])

    # Load STATS worksheet for validation
    stats_sheet = sh.worksheet('STATS')

    # Diagnostic: Log any unusual status values that might not map correctly
    print(f"\n[Diagnostic] Checking for unusual status values...")
    unusual_statuses = {}
    expected_statuses = [
        'successful order', 'voicemail', 'no answer', 'not interested',
        'invalid', 'potentially invalid', 'requested email', 'email'
    ]

    for row in wl_rows:
        if row.status:
            status_lower = row.status.lower().strip()
            # Check if status contains any expected keyword
            is_recognized = any(exp in status_lower for exp in expected_statuses)
            if not is_recognized:
                if status_lower not in unusual_statuses:
                    unusual_statuses[status_lower] = []
                unusual_statuses[status_lower].append(row.row_num)

    if unusual_statuses:
        print(f"  [!] Found {len(unusual_statuses)} unusual status values:")
        for status, rows in list(unusual_statuses.items())[:10]:  # Show first 10
            print(f"      '{status}' (rows: {', '.join(map(str, rows[:5]))}{'...' if len(rows) > 5 else ''})")
        if len(unusual_statuses) > 10:
            print(f"      ... and {len(unusual_statuses) - 10} more")
        print(f"  These may not map to expected colors correctly.")
    else:
        print(f"  [OK] All status values are recognized")

    print(f"\n[Phase 1] Complete!")
    return wl_rows, no_rows, invalid_rows, invalid_reasons, stats_sheet

def validate_stats_color_counts(wl_rows, stats_sheet, year=2025, assume_yes=False):
    """
    Validate Status-derived colors against STATS worksheet color counts.

    STATS worksheet uses formulas to COUNT actual cell background colors.
    We derive colors from Status column to avoid API rate limits.
    This function checks if they match.

    If mismatch > 10%, warns user to manually fix Status column in sheet.
    """
    print(f"\n[Validation] Checking Status-derived colors against STATS...")

    # Count Status-derived colors in our data
    status_counts = {
        'yellow': 0,
        'fuschia': 0,
        'red': 0,
        'green': 0,
        'white': 0
    }

    for row in wl_rows:
        color = row.bg_color.lower()
        if color in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']:
            status_counts['yellow'] += 1
        elif color in ['#ff00ff', '#ff00fe', '#fe00ff']:
            status_counts['fuschia'] += 1
        elif color in ['#ff0000', '#ff0001', '#fe0000']:
            status_counts['red'] += 1
        elif color in ['#00ff00', '#00ff01', '#00fe00']:
            status_counts['green'] += 1
        else:
            status_counts['white'] += 1

    # Read STATS color counts (formulas calculate actual colors)
    # STATS worksheet structure:
    # Row 2, Col C: Yellow (ORDER SECURED)
    # Row 3, Col C: White with "not interested"
    # Row 4, Col C: Fuschia (CALLBACK)
    # Row 5, Col C: White uncalled (no "not interested")
    # Row 6, Col C: Red (VERIFY ACTIVITY/VALIDITY)
    # Row 7, Col C: Green (UNRESOLVED EMAILS)
    try:
        stats_data = stats_sheet.get('A1:C10')  # Get first 10 rows of STATS

        stats_counts = {}

        # Parse based on actual STATS structure (hardcoded row positions)
        # This is reliable since STATS layout is fixed
        try:
            # Row 2 (index 1): Yellow
            if len(stats_data) > 1 and len(stats_data[1]) > 2:
                stats_counts['yellow'] = int(stats_data[1][2])

            # Row 4 (index 3): Fuschia
            if len(stats_data) > 3 and len(stats_data[3]) > 2:
                stats_counts['fuschia'] = int(stats_data[3][2])

            # Row 6 (index 5): Red
            if len(stats_data) > 5 and len(stats_data[5]) > 2:
                stats_counts['red'] = int(stats_data[5][2])

            # Row 7 (index 6): Green
            if len(stats_data) > 6 and len(stats_data[6]) > 2:
                stats_counts['green'] = int(stats_data[6][2])

            # White = Row 3 (not interested) + Row 5 (uncalled)
            white_not_interested = 0
            white_uncalled = 0
            if len(stats_data) > 2 and len(stats_data[2]) > 2:
                white_not_interested = int(stats_data[2][2])
            if len(stats_data) > 4 and len(stats_data[4]) > 2:
                white_uncalled = int(stats_data[4][2])
            stats_counts['white'] = white_not_interested + white_uncalled

        except (ValueError, IndexError) as e:
            print(f"  [!] Could not parse STATS counts: {e}")
            return True  # Continue anyway

        # Compare counts
        print(f"\n  Status-Derived Counts vs STATS Color Counts:")
        print(f"  {'Color':<15} {'Status':<10} {'STATS':<10} {'Diff':<10} {'Status'}")
        print(f"  {'-'*55}")

        has_mismatch = False
        for color in ['yellow', 'fuschia', 'red', 'green', 'white']:
            status_val = status_counts.get(color, 0)
            stats_val = stats_counts.get(color, 0)
            diff = status_val - stats_val

            # Check if significant mismatch (>10% or >10 rows)
            threshold = max(10, stats_val * 0.10)
            status_mark = "[!] MISMATCH" if abs(diff) > threshold else "[OK]"

            if abs(diff) > threshold:
                has_mismatch = True

            print(f"  {color.capitalize():<15} {status_val:<10} {stats_val:<10} {diff:+10} {status_mark}")

        print()

        if has_mismatch:
            print("  [!] WARNING: Status column doesn't match actual cell colors!")
            print("  -> This means some rows have Status text that doesn't match their background color")
            print("  -> STATS uses actual cell colors (formulas count background colors)")
            print("  -> Status column is used by this tool to avoid API rate limits")
            print()
            print("  RECOMMENDED ACTION:")
            print("  1. Open the Working List in Google Sheets")
            print("  2. Review rows where Status doesn't match color")
            print("  3. Either:")
            print("     a) Update Status to match color (Apps Script will auto-update color)")
            print("     b) Manually update color to match Status (in cell formatting)")
            print("  4. Re-run this tool after fixing")
            print()
            if assume_yes:
                print("  [Automation] --assume-yes active: Continuing despite mismatch.")
                return True
                
            response = input("  Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("\n[Validation] User chose to exit. Please fix Status/color mismatch first.")
                return False

        else:
            print("  [OK] Status-derived colors match STATS color counts!")
            print("  -> Safe to proceed with Status column as color source")

        return True

    except Exception as e:
        print(f"  [!] Could not validate against STATS: {e}")
        print(f"  -> Proceeding with Status-derived colors (validation skipped)")
        return True

# ============================================================================
# PHASE 2: VALIDATION LOGIC
# ============================================================================

def normalize_name(name):
    """Normalize provider name for comparison"""
    if not name:
        return ""
    name = re.sub(r'\b(LLC|PC|PLLC|INC|Dr|Doctor|MD|DO|OB/GYN|OBGYN)\b', '', name, flags=re.IGNORECASE)
    name = name.replace('&', 'and').replace('+', 'and')
    return name.lower().strip()

def normalize_address(addr):
    """Normalize address for comparison"""
    if not addr:
        return ""
    replacements = {
        'street': 'st', 'avenue': 'ave', 'boulevard': 'blvd',
        'drive': 'dr', 'road': 'rd', 'lane': 'ln',
        'suite': 'ste', 'apartment': 'apt', 'building': 'bldg'
    }
    addr_lower = addr.lower()
    for full, abbr in replacements.items():
        addr_lower = addr_lower.replace(full, abbr)
    addr_lower = re.sub(r'\b(ste|apt|suite|apartment)\s*\.?\s*\d+\w*\b', '', addr_lower)
    return addr_lower.strip()

def normalize_phone(phone):
    """Normalize phone for matching"""
    if not phone:
        return ""
    digits = re.sub(r'[^\d]', '', phone)
    return digits[-10:] if len(digits) >= 10 else digits

def validate_yellow_to_no(wl_rows, no_rows):
    """Match yellow rows to New Orders"""
    print(f"[Phase 2.1] Matching yellow rows to New Orders...")

    yellow_count = 0
    for wl_row in wl_rows:
        # Normalize color (yellow variations)
        color = wl_row.bg_color.lower()
        if color not in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']:
            continue

        yellow_count += 1

        # Find best match in NO
        best_match = None
        best_confidence = 0.0
        best_no_row = None

        for no_row in no_rows:
            # State must match exactly
            if wl_row.state != no_row.state:
                continue

            # Name matching (70% weight)
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

        # Categorize by confidence
        if best_confidence >= 0.95:
            category = "yellow_95"
            severity = "review"
        elif best_confidence >= 0.80:
            category = "yellow_80"
            severity = "review"
        else:
            category = "yellow_low"
            severity = "critical"

        # Check QTY match
        qty_mismatch = False
        if best_match and best_match.qty_2025 != wl_row.qty_2025:
            qty_mismatch = True

        wl_row.issues.append({
            'category': category,
            'severity': severity,
            'message': f"Match confidence: {best_confidence*100:.1f}%",
            'no_row': best_no_row,
            'no_practice': best_match.practice if best_match else None,
            'no_qty': best_match.qty_2025 if best_match else None,
            'qty_mismatch': qty_mismatch,
            'confidence': best_confidence
        })

    print(f"  Matched {yellow_count} yellow rows")

def validate_no_to_wl(wl_rows, no_rows):
    """Find orphan NO rows (no yellow match in WL)"""
    print(f"[Phase 2.2] Finding orphan New Orders...")

    orphan_count = 0
    for no_row in no_rows:
        # Find matching yellow rows
        matches = [
            wl for wl in wl_rows
            if wl.matched_no_row == no_row.row_num
            and wl.bg_color.lower() in ['#ffff00', '#ffff01', '#fffef0', '#ffffe0']
        ]

        no_row.matched_wl_rows = [m.row_num for m in matches]

        if len(matches) == 0:
            no_row.is_orphan = True
            orphan_count += 1

    print(f"  Found {orphan_count} orphan New Orders")

def detect_duplicates(wl_rows):
    """Detect duplicates and networks"""
    print(f"[Phase 2.3] Detecting duplicates and networks...")

    # Group by normalized phone
    phone_groups = defaultdict(list)
    for row in wl_rows:
        norm_phone = normalize_phone(row.phone)
        if norm_phone:
            phone_groups[norm_phone].append(row)

    group_id = 1
    exact_dupes = 0
    networks = 0
    fuzzy_dupes = 0

    for phone, rows in phone_groups.items():
        if len(rows) <= 1:
            continue

        # Check if exact duplicates
        first = rows[0]
        is_exact = all(
            normalize_name(r.practice) == normalize_name(first.practice) and
            normalize_address(r.address) == normalize_address(first.address)
            for r in rows[1:]
        )

        if is_exact:
            for row in rows:
                row.duplicate_group_id = group_id
                row.issues.append({
                    'category': 'exact_dupes',
                    'severity': 'auto_fix',
                    'message': f"Exact duplicate ({len(rows)} copies)",
                    'group_size': len(rows)
                })
            exact_dupes += len(rows)

        # Check if network (similar names, different addresses)
        else:
            names = [normalize_name(r.practice) for r in rows]
            addrs = [normalize_address(r.address) for r in rows]

            # Name similarity check
            is_network = True
            for i in range(len(names)):
                for j in range(i+1, len(names)):
                    if fuzz.ratio(names[i], names[j]) < 85:
                        is_network = False
                        break
                if not is_network:
                    break

            # Address dissimilarity check
            if is_network:
                for i in range(len(addrs)):
                    for j in range(i+1, len(addrs)):
                        if fuzz.ratio(addrs[i], addrs[j]) >= 70:
                            is_network = False
                            break
                    if not is_network:
                        break

            if is_network:
                # Extract default network name
                name = rows[0].practice
                name = re.sub(r'\b(North|South|East|West|Downtown|Uptown|Medical|Clinic|Center|Office)\b', '', name, flags=re.IGNORECASE)
                name = re.sub(r'[^a-z]', '', name.lower())

                for row in rows:
                    row.network_name = name
                    row.issues.append({
                        'category': 'networks',
                        'severity': 'review',
                        'message': f"Network detected (~{len(rows)} locations)",
                        'network_name': name,
                        'location_count': len(rows)
                    })
                networks += len(rows)
            else:
                # Fuzzy duplicates
                for row in rows:
                    row.duplicate_group_id = group_id
                    row.issues.append({
                        'category': 'fuzzy_dupes',
                        'severity': 'review',
                        'message': f"Possible duplicate ({len(rows)} similar rows)",
                        'group_size': len(rows)
                    })
                fuzzy_dupes += len(rows)

        group_id += 1

    print(f"  Found {exact_dupes} exact duplicates, {networks} network locations, {fuzzy_dupes} fuzzy duplicates")

def validate_status_issues(wl_rows):
    """Check status-related issues"""
    print(f"[Phase 2.4] Validating status issues...")

    counts = defaultdict(int)

    for row in wl_rows:
        color = row.bg_color.lower()

        # Fuschia without vm note
        if color in ['#ff00ff', '#ff00fe', '#fe00ff']:
            if 'vm' not in row.notes.lower():
                row.issues.append({
                    'category': 'fuschia_vm',
                    'severity': 'review',
                    'message': "Fuschia but no 'vm' in notes"
                })
                counts['fuschia_vm'] += 1

        # Green with "sent"
        elif color in ['#00ff00', '#00ff01', '#00fe00']:
            if 'sent' in row.notes.lower():
                row.issues.append({
                    'category': 'green_sent',
                    'severity': 'auto_fix',
                    'message': "Green with 'sent' -> suggest Not interested"
                })
                counts['green_sent'] += 1

        # Red (all need review)
        elif color in ['#ff0000', '#ff0001', '#fe0000']:
            row.issues.append({
                'category': 'red_invalid',
                'severity': 'critical',
                'message': "Marked as Potentially Invalid"
            })
            counts['red_invalid'] += 1

        # Not interested with invalid keywords
        if row.status == 'Not interested' or row.status == 'Not Interested':
            invalid_keywords = [
                'closed', 'disconnected', 'wrong number', 'moved',
                'no longer', 'out of business', 'permanently closed',
                'number out of service', 'not doing ob', 'not an ob'
            ]
            notes_lower = row.notes.lower()
            if any(kw in notes_lower for kw in invalid_keywords):
                row.issues.append({
                    'category': 'not_interested_invalid',
                    'severity': 'review',
                    'message': "'Not interested' but notes suggest invalid provider"
                })
                counts['not_interested_invalid'] += 1

    for cat, count in counts.items():
        print(f"    {cat}: {count} rows")

def auto_fix_not_interested(wl_rows):
    """Auto-fix not interested rows"""
    print(f"[Phase 2.5] Auto-fixing 'Not interested' rows...")

    fixed = 0
    for row in wl_rows:
        if row.status not in ['Not interested', 'Not Interested']:
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
            row.notes = re.sub(r'\s*;\s*;', ';', row.notes)
            row.notes = row.notes.strip('; ')
            changes.append('removed_sent')

        if changes:
            row.issues.append({
                'category': 'not_interested',
                'severity': 'auto_fix',
                'message': f"Auto-fixed: {', '.join(changes)}"
            })
            fixed += 1

    print(f"  Auto-fixed {fixed} rows")

def detect_non_standard_notes(wl_rows):
    """Identify notes with non-standard chunks"""
    print(f"[Phase 2.6] Detecting non-standard notes...")

    standard_patterns = [
        'not interested',
        'sent', ':sent',
        'vm x2', 'vm x3', 'vm',
        'network', 'same network',
        'callback', 'call back',
        'repeat',
    ]

    count = 0
    for row in wl_rows:
        if not row.notes:
            continue

        chunks = [c.strip() for c in row.notes.split(';') if c.strip()]
        non_standard_chunks = []

        for chunk in chunks:
            chunk_lower = chunk.lower()
            is_standard = any(pattern in chunk_lower for pattern in standard_patterns)
            if not is_standard:
                non_standard_chunks.append(chunk)

        if non_standard_chunks:
            row.issues.append({
                'category': 'non_standard_notes',
                'severity': 'review',
                'message': f"{len(non_standard_chunks)} non-standard note chunks",
                'non_standard_chunks': non_standard_chunks,
                'all_chunks': chunks
            })
            count += 1

    print(f"  Found {count} rows with non-standard notes")

def categorize_issues(wl_rows, no_rows):
    """Organize issues into review categories"""
    print(f"[Phase 2.7] Categorizing issues...")

    categories = [
        ReviewCategory(
            id="exact_dupes",
            name="Duplicates",
            description="Identical rows (same name, address, phone)",
            row_nums=[],
            allow_batch=True,
            primary_action="keep_first_delete_rest",
            secondary_actions=["delete_all", "edit", "review_individual"]
        ),
        ReviewCategory(
            id="networks",
            name="Networks",
            description="Same phone, similar names, different locations",
            row_nums=[],
            allow_batch=True,
            primary_action="confirm_network",
            secondary_actions=["mass_invalid", "review_individual"]
        ),
        ReviewCategory(
            id="fuzzy_dupes",
            name="Possible Dupes",
            description="Similar rows that might be duplicates",
            row_nums=[],
            allow_batch=True,
            primary_action=None,
            secondary_actions=["merge", "delete", "edit"]
        ),
        ReviewCategory(
            id="yellow_95",
            name="Orders (Exact Match)",
            description="High-confidence matches to New Orders",
            row_nums=[],
            allow_batch=True,
            primary_action="accept_all",
            secondary_actions=["fix_qty_mismatches", "not_found"]
        ),
        ReviewCategory(
            id="yellow_80",
            name="Orders (Good Match)",
            description="Medium-confidence matches (review carefully)",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["accept", "not_found", "edit"]
        ),
        ReviewCategory(
            id="yellow_low",
            name="Orders (Not Found)",
            description="Yellow rows not found in New Orders",
            row_nums=[],
            allow_batch=False,
            primary_action="mark_not_found",
            secondary_actions=["change_to_white", "move_to_invalid"]
        ),
        ReviewCategory(
            id="orphan_no",
            name="Unmatched Orders",
            description="New Orders without yellow match - fuzzy check against Invalid List",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["check_invalid_matches", "send_to_manual_review"]
        ),
        ReviewCategory(
            id="green_sent",
            name="Email Sent",
            description="Requested email with 'sent' in notes",
            row_nums=[],
            allow_batch=True,
            primary_action="convert_to_not_interested",
            secondary_actions=["remove_sent", "delete"]
        ),
        ReviewCategory(
            id="fuschia_vm",
            name="Voicemails",
            description="Voicemail status, check notes",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["add_vm_note", "change_status"]
        ),
        ReviewCategory(
            id="red_invalid",
            name="Potentially Invalid",
            description="Review and move to Invalid List",
            row_nums=[],
            allow_batch=True,
            primary_action="move_all_to_invalid",
            secondary_actions=["review_individual", "change_status"]
        ),
        ReviewCategory(
            id="not_interested_invalid",
            name="Not Int (Invalid?)",
            description="'Not interested' but notes suggest invalid - could be various colors/statuses with misc note patterns",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=[
                "edit", "change_status", "move_to_invalid",
                "change_to_white", "remove_sent", "mark_not_found",
                "delete"
            ]
        ),
        ReviewCategory(
            id="manual_review",
            name="Manual Review",
            description="Edge cases sent for manual review - all actions available",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=[
                "edit", "delete", "merge", "change_status",
                "move_to_invalid", "change_to_white", "mark_not_found",
                "fix_qty_mismatches", "add_vm_note", "remove_sent"
            ]
        ),
    ]

    # Populate categories from WL rows
    for row in wl_rows:
        for issue in row.issues:
            for cat in categories:
                if cat.id == issue['category']:
                    if row.row_num not in cat.row_nums:
                        cat.row_nums.append(row.row_num)

    # Add orphan NO rows (stored separately)
    orphan_cat = next(c for c in categories if c.id == "orphan_no")
    for no_row in no_rows:
        if no_row.is_orphan:
            orphan_cat.row_nums.append(no_row.row_num)

    # Filter out empty categories
    categories = [c for c in categories if len(c.row_nums) > 0]

    # Sort rows within each category
    for cat in categories:
        cat.row_nums.sort()

    for cat in categories:
        print(f"  {cat.name}: {len(cat.row_nums)} rows")

    return categories

def run_validations(year=2025):
    """Run all validation phases"""
    print(f"\n[Phase 2] Running validations...")

    # Load data
    wl_rows, no_rows, invalid_rows, invalid_reasons, stats_sheet = load_data(year)

    # IMPORTANT: Validate Status-derived colors against STATS
    # This ensures Status column matches actual cell colors
    # If mismatch, user is warned to fix manually before proceeding
    if not validate_stats_color_counts(wl_rows, stats_sheet, year):
        # User chose to exit due to Status/color mismatch
        return None, None, None, None

    # Validation pipeline
    validate_yellow_to_no(wl_rows, no_rows)
    validate_no_to_wl(wl_rows, no_rows)
    detect_duplicates(wl_rows)
    validate_status_issues(wl_rows)
    # DISABLED: auto_fix_not_interested(wl_rows)  # No auto-fixing per user request
    # DISABLED: detect_non_standard_notes(wl_rows)  # Not a real category
    categories = categorize_issues(wl_rows, no_rows)

    print(f"\n[Phase 2] Complete!")

    return wl_rows, no_rows, invalid_rows, categories, invalid_reasons

# ============================================================================
# UNDO/REDO SYSTEM
# ============================================================================

def add_to_undo_stack(action_type: str, description: str, before_state: Any, after_state: Any = None):
    """Add action to undo stack"""
    action = {
        'id': len(state.undo_stack) + 1,
        'timestamp': datetime.now().isoformat(),
        'action_type': action_type,
        'description': description,
        'before_state': before_state,
        'after_state': after_state
    }

    state.undo_stack.append(action)
    state.redo_stack.clear()  # Clear redo stack when new action added

    # Keep only last 50 actions
    if len(state.undo_stack) > 50:
        state.undo_stack.pop(0)

    # Save to disk
    save_undo_log()

def restore_state(state_dict: Dict) -> bool:
    """Restore row state from undo/redo dictionary

    Args:
        state_dict: Dictionary containing state to restore
                   Can have formats:
                   - {'row_num': X, 'field': value, ...} - single row restoration
                   - {'row_nums': [X, Y, Z]} - multi-row deletion restoration
                   - {'rows': [{row_num: X, field: value}, ...]} - multi-row field restoration

    Returns:
        True if restoration successful, False otherwise
    """
    if not state_dict:
        return False

    # Handle single row restoration
    if 'row_num' in state_dict:
        row_num = state_dict['row_num']
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)

        if not row:
            return False

        # Restore all fields present in state_dict (except row_num)
        for field, value in state_dict.items():
            if field != 'row_num' and hasattr(row, field):
                setattr(row, field, value)

        return True

    # Handle multi-row field restoration (new action handlers)
    elif 'rows' in state_dict:
        for row_state in state_dict['rows']:
            row_num = row_state['row_num']
            row = next((r for r in state.wl_rows if r.row_num == row_num), None)

            if not row:
                continue

            # Restore all fields from row_state
            for field, value in row_state.items():
                if field != 'row_num' and hasattr(row, field):
                    setattr(row, field, value)

        return True

    # Handle multi-row deletion restoration
    elif 'row_nums' in state_dict:
        # For delete_rows, we marked action='delete'
        # To undo, clear the delete marker
        for row_num in state_dict['row_nums']:
            row = next((r for r in state.wl_rows if r.row_num == row_num), None)
            if row and row.action == 'delete':
                row.action = None
        return True

    return False

def save_undo_log():
    """Save undo stack to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eoy_undo_log_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump({
            'actions': state.undo_stack,
            'current_position': len(state.undo_stack)
        }, f, indent=2)

def save_progress():
    """Save current progress to JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eoy_progress_{timestamp}.json"

    progress = state.to_dict()
    progress['saved_at'] = timestamp

    with open(filename, 'w') as f:
        json.dump(progress, f, indent=2)

    print(f"Progress saved to {filename}")
    return filename

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page - always show load screen"""
    return render_template('index.html')

@app.route('/load', methods=['POST'])
def load():
    """Load data and run validations"""
    try:
        year = int(request.form.get('year', 2025))
        state.year = year

        # Run validations
        state.wl_rows, state.no_rows, state.invalid_rows, state.categories, state.invalid_reasons = run_validations(year)
        state.loaded = True
        state.current_category_id = state.categories[0].id if state.categories else None

        return jsonify({
            'success': True,
            'total_rows': len(state.wl_rows),
            'categories_count': len(state.categories)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/categories')
def categories():
    """Redirect to first category"""
    if not state.loaded:
        return redirect(url_for('index'))

    # Redirect to first category
    if state.categories:
        return redirect(url_for('category', category_id=state.categories[0].id))
    else:
        return "No categories found", 404

@app.route('/category/<category_id>')
def category(category_id):
    """View specific category"""
    if not state.loaded:
        return redirect(url_for('index'))

    cat = next((c for c in state.categories if c.id == category_id), None)
    if not cat:
        return "Category not found", 404

    state.current_category_id = category_id

    # Get rows for this category
    rows = [r for r in state.wl_rows if r.row_num in cat.row_nums]

    return render_template('category.html',
                         category=cat,
                         rows=rows,
                         categories=state.categories)

@app.route('/api/save_progress', methods=['POST'])
def api_save_progress():
    """API endpoint to save progress"""
    try:
        filename = save_progress()
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/undo', methods=['POST'])
def api_undo():
    """API endpoint to undo last action"""
    if not state.undo_stack:
        return jsonify({'success': False, 'error': 'Nothing to undo'}), 400

    action = state.undo_stack.pop()
    state.redo_stack.append(action)

    # Apply undo (restore before_state)
    success = restore_state(action['before_state'])

    if not success:
        # Restore the action back if restoration failed
        state.undo_stack.append(action)
        state.redo_stack.pop()
        return jsonify({'success': False, 'error': 'Failed to restore state'}), 500

    # Re-categorize issues after restoration
    state.categories = categorize_issues(state.wl_rows, state.no_rows)

    return jsonify({
        'success': True,
        'action': action['description'],
        'can_undo': len(state.undo_stack) > 0,
        'can_redo': len(state.redo_stack) > 0
    })

@app.route('/api/redo', methods=['POST'])
def api_redo():
    """API endpoint to redo last undone action"""
    if not state.redo_stack:
        return jsonify({'success': False, 'error': 'Nothing to redo'}), 400

    action = state.redo_stack.pop()
    state.undo_stack.append(action)

    # Apply redo (restore after_state)
    success = restore_state(action['after_state'])

    if not success:
        # Restore the action back if restoration failed
        state.redo_stack.append(action)
        state.undo_stack.pop()
        return jsonify({'success': False, 'error': 'Failed to restore state'}), 500

    # Re-categorize issues after restoration
    state.categories = categorize_issues(state.wl_rows, state.no_rows)

    return jsonify({
        'success': True,
        'action': action['description'],
        'can_undo': len(state.undo_stack) > 0,
        'can_redo': len(state.redo_stack) > 0
    })

@app.route('/api/delete_note_chunk', methods=['POST'])
def api_delete_note_chunk():
    """API endpoint to delete a note chunk"""
    data = request.get_json()
    row_num = data.get('row_num')
    chunk_index = data.get('chunk_index')

    # Find row
    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
    if not row:
        return jsonify({'success': False, 'error': 'Row not found'}), 404

    # Save before state for undo
    before_notes = row.notes

    # Delete chunk
    chunks = [c.strip() for c in row.notes.split(';') if c.strip()]
    if 0 <= chunk_index < len(chunks):
        chunk_text = chunks[chunk_index]
        del chunks[chunk_index]
        row.notes = '; '.join(chunks)

        # Add to undo stack
        add_to_undo_stack(
            action_type='delete_note_chunk',
            description=f"Deleted note chunk '{chunk_text}' from row {row_num}",
            before_state={'row_num': row_num, 'notes': before_notes},
            after_state={'row_num': row_num, 'notes': row.notes}
        )

        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Chunk index out of range'}), 400

@app.route('/api/delete_rows', methods=['POST'])
def api_delete_rows():
    """API endpoint to delete selected rows"""
    data = request.get_json()
    row_nums = data.get('row_nums', [])

    if not row_nums:
        return jsonify({'success': False, 'error': 'No rows specified'}), 400

    # Mark rows for deletion
    deleted_count = 0
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            row.action = 'delete'
            deleted_count += 1

    # Add to undo stack
    add_to_undo_stack(
        action_type='delete_rows',
        description=f"Deleted {deleted_count} rows",
        before_state={'row_nums': row_nums},
        after_state={'row_nums': row_nums}
    )

    return jsonify({'success': True, 'count': deleted_count})

@app.route('/api/keep_first_delete_rest', methods=['POST'])
def api_keep_first_delete_rest():
    """Keep first occurrence of each duplicate group, delete rest"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Group rows by duplicate_group_id
    from collections import defaultdict
    groups = defaultdict(list)

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.duplicate_group_id:
            groups[row.duplicate_group_id].append(row)

    # Keep first, delete rest
    deleted_count = 0
    for group_id, rows in groups.items():
        if len(rows) > 1:
            # Keep first (lowest row number)
            rows.sort(key=lambda r: r.row_num)
            for row in rows[1:]:  # Delete rest
                row.action = 'delete'
                deleted_count += 1

    return jsonify({'success': True, 'count': deleted_count})

@app.route('/api/accept_all_matches', methods=['POST'])
def api_accept_all_matches():
    """Accept all yellow matches in category"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Mark all rows as accepted
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            row.action = 'accepted'
            count += 1

    return jsonify({'success': True, 'count': count})

@app.route('/api/confirm_network', methods=['POST'])
def api_confirm_network():
    """Confirm network and add notation to notes"""
    data = request.get_json()
    category_id = data.get('category_id')
    network_name = data.get('network_name', '').strip()

    if not network_name:
        return jsonify({'success': False, 'error': 'Network name required'}), 400

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Add network notation to all rows
    count = 0
    network_notation = f"{network_name.lower().replace(' ', '')} network (~{len(category.row_nums)})"

    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Remove old network notations
            notes = re.sub(r'\b\w+ network \(~\d+\)', '', row.notes, flags=re.IGNORECASE)
            notes = re.sub(r'\s*;\s*;', ';', notes).strip(';').strip()

            # Add new notation
            row.notes = f"{network_notation}; {notes}" if notes else network_notation
            count += 1

    return jsonify({'success': True, 'count': count})

@app.route('/api/convert_to_not_interested', methods=['POST'])
def api_convert_to_not_interested():
    """Convert green 'sent' rows to Not Interested"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Convert all rows
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            row.status = "Not Interested"
            row.qty_2025 = "0"
            row.bg_color = "#ffffff"

            # Remove 'sent' from notes, add 'not interested'
            notes = re.sub(r':?sent', '', row.notes, flags=re.IGNORECASE).strip()
            if 'not interested' not in notes.lower():
                row.notes = f"{notes}; not interested" if notes else "not interested"
            else:
                row.notes = notes

            # Clean up extra semicolons
            row.notes = re.sub(r'\s*;\s*;', ';', row.notes).strip(';').strip()

            count += 1

    return jsonify({'success': True, 'count': count})

@app.route('/api/move_to_invalid', methods=['POST'])
def api_move_to_invalid():
    """Move rows to Invalid/Inactive List"""
    data = request.get_json()
    category_id = data.get('category_id')
    reason = data.get('reason', 'INVALID')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Mark all rows for move to invalid
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            row.action = 'move_to_invalid'
            row.field_edits['invalid_reason'] = reason
            count += 1

    return jsonify({'success': True, 'count': count})

@app.route('/api/fix_qty_mismatches', methods=['POST'])
def api_fix_qty_mismatches():
    """Update qty_2025 in WL rows to match NO rows"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Track changes for undo
    before_states = []
    after_states = []

    # Fix qty mismatches
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.matched_no_row:
            # Find matching NO row
            no_row = next((n for n in state.no_rows if n.row_num == row.matched_no_row), None)
            if no_row:
                # Capture before state
                before_states.append({
                    'row_num': row_num,
                    'field_edits': dict(row.field_edits),
                    'action': row.action
                })

                # Update qty to match NO row
                row.field_edits['qty_2025'] = no_row.qty_2025
                row.action = 'edit'

                # Capture after state
                after_states.append({
                    'row_num': row_num,
                    'field_edits': dict(row.field_edits),
                    'action': row.action
                })

                count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='fix_qty_mismatches',
            description=f"Fixed {count} QTY mismatches",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/mark_not_found', methods=['POST'])
def api_mark_not_found():
    """Add 'not found in new orders' note to yellow rows"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Track changes for undo
    before_states = []
    after_states = []

    # Mark as not found
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Add note
            existing_notes = row.notes if row.notes else ""
            note_to_add = "not found in new orders"

            # Only add if not already present
            if note_to_add not in existing_notes.lower():
                # Capture before state
                before_states.append({
                    'row_num': row_num,
                    'field_edits': dict(row.field_edits),
                    'action': row.action
                })

                if existing_notes and not existing_notes.endswith(';'):
                    existing_notes += '; '
                elif existing_notes:
                    existing_notes += ' '
                row.field_edits['notes'] = existing_notes + note_to_add + ';'
                row.action = 'edit'

                # Capture after state
                after_states.append({
                    'row_num': row_num,
                    'field_edits': dict(row.field_edits),
                    'action': row.action
                })

                count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='mark_not_found',
            description=f"Marked {count} rows as not found",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/add_vm_note', methods=['POST'])
def api_add_vm_note():
    """Parse and increment voicemail counter in notes"""
    data = request.get_json()
    category_id = data.get('category_id')
    row_nums = data.get('row_nums', [])  # Specific rows if provided

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Use provided row_nums or all in category
    target_rows = row_nums if row_nums else category.row_nums

    # Track changes for undo
    before_states = []
    after_states = []

    import re
    count = 0
    for row_num in target_rows:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Capture before state
            before_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            notes = row.notes if row.notes else ""

            # Parse existing vm count: "vm x2" or "vm x3"
            vm_match = re.search(r'vm x(\d+)', notes, re.IGNORECASE)
            if vm_match:
                # Increment counter
                current_count = int(vm_match.group(1))
                new_count = current_count + 1
                new_notes = re.sub(r'vm x\d+', f'vm x{new_count}', notes, flags=re.IGNORECASE)
            else:
                # Add new vm x2 (assuming this is 2nd attempt)
                if notes and not notes.endswith(';'):
                    notes += '; '
                elif notes:
                    notes += ' '
                new_notes = notes + 'vm x2;'

            row.field_edits['notes'] = new_notes
            row.action = 'edit'

            # Capture after state
            after_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='add_vm_note',
            description=f"Added/incremented VM note for {count} rows",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/change_status', methods=['POST'])
def api_change_status():
    """Change status and derive bg_color"""
    data = request.get_json()
    category_id = data.get('category_id')
    row_nums = data.get('row_nums', [])
    new_status = data.get('status')

    if not new_status:
        return jsonify({'success': False, 'error': 'Status required'}), 400

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Use provided row_nums or all in category
    target_rows = row_nums if row_nums else category.row_nums

    # Track changes for undo
    before_states = []
    after_states = []

    count = 0
    for row_num in target_rows:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Capture before state
            before_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            # Update status
            row.field_edits['status'] = new_status
            # Derive color from status
            row.field_edits['bg_color'] = status_to_color(new_status)
            row.action = 'edit'

            # Capture after state
            after_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='change_status',
            description=f"Changed status for {count} rows to '{new_status}'",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/change_to_white', methods=['POST'])
def api_change_to_white():
    """Change status to 'Not interested' (white)"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Track changes for undo
    before_states = []
    after_states = []

    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Capture before state
            before_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            row.field_edits['status'] = 'Not interested'
            row.field_edits['bg_color'] = '#ffffff'
            row.field_edits['qty_2025'] = '0'

            # Add "not interested" to notes if not present
            notes = row.notes if row.notes else ""
            if 'not interested' not in notes.lower():
                if notes and not notes.endswith(';'):
                    notes += '; '
                elif notes:
                    notes += ' '
                row.field_edits['notes'] = notes + 'not interested;'

            row.action = 'edit'

            # Capture after state
            after_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='change_to_white',
            description=f"Changed {count} rows to 'Not interested'",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/remove_sent', methods=['POST'])
def api_remove_sent():
    """Remove 'sent' from notes column"""
    data = request.get_json()
    category_id = data.get('category_id')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Track changes for undo
    before_states = []
    after_states = []

    import re
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.notes:
            # Remove "sent" (case-insensitive)
            new_notes = re.sub(r'\bsent\b', '', row.notes, flags=re.IGNORECASE)
            # Clean up extra semicolons and spaces
            new_notes = re.sub(r';\s*;', ';', new_notes)
            new_notes = re.sub(r'^\s*;\s*', '', new_notes)
            new_notes = re.sub(r'\s*;\s*$', '', new_notes)
            new_notes = re.sub(r'\s+', ' ', new_notes).strip()

            if new_notes != row.notes:
                # Capture before state
                before_states.append({
                    'row_num': row_num,
                    'field_edits': dict(row.field_edits),
                    'action': row.action
                })

                row.field_edits['notes'] = new_notes
                row.action = 'edit'

                # Capture after state
                after_states.append({
                    'row_num': row_num,
                    'field_edits': dict(row.field_edits),
                    'action': row.action
                })

                count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='remove_sent',
            description=f"Removed 'sent' from {count} rows",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/mass_invalid', methods=['POST'])
def api_mass_invalid():
    """Mark all rows in network as invalid"""
    data = request.get_json()
    category_id = data.get('category_id')
    reason = data.get('reason', 'INVALID - Network closed')

    # Find category
    category = next((c for c in state.categories if c.id == category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Track changes for undo
    before_states = []
    after_states = []

    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Capture before state
            before_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            row.action = 'move_to_invalid'
            row.field_edits['invalid_reason'] = reason

            # Capture after state
            after_states.append({
                'row_num': row_num,
                'field_edits': dict(row.field_edits),
                'action': row.action
            })

            count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='mass_invalid',
            description=f"Marked {count} network rows as invalid",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/send_to_manual_review', methods=['POST'])
def api_send_to_manual_review():
    """Send selected rows to manual review category"""
    data = request.get_json()
    source_category_id = data.get('category_id')
    row_nums = data.get('row_nums', [])

    if not row_nums:
        return jsonify({'success': False, 'error': 'No rows selected'}), 400

    # Find source category
    category = next((c for c in state.categories if c.id == source_category_id), None)
    if not category:
        return jsonify({'success': False, 'error': 'Category not found'}), 404

    # Track changes for undo
    before_states = []
    after_states = []

    # Add manual_review issue to each row
    count = 0
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            # Capture before state (deep copy of issues list)
            before_states.append({
                'row_num': row_num,
                'issues': [dict(issue) for issue in row.issues]
            })

            # Add issue
            row.issues.append({
                'category': 'manual_review',
                'severity': 'review',
                'description': f'Sent from {category.name} for manual review'
            })

            # Capture after state
            after_states.append({
                'row_num': row_num,
                'issues': [dict(issue) for issue in row.issues]
            })

            count += 1

    # Add to undo stack
    if count > 0:
        add_to_undo_stack(
            action_type='send_to_manual_review',
            description=f"Sent {count} rows to manual review",
            before_state={'rows': before_states},
            after_state={'rows': after_states}
        )

    # Re-categorize to update category lists
    state.categories = categorize_issues(state.wl_rows, state.no_rows)

    return jsonify({'success': True, 'count': count})

@app.route('/api/get_orphan_no_matches', methods=['GET'])
def api_get_orphan_no_matches():
    """Get orphan NO rows with fuzzy matches against Invalid/Inactive List"""
    from rapidfuzz import fuzz

    orphan_matches = []

    for no_row in state.no_rows:
        if no_row.is_orphan:
            # Fuzzy match against invalid list
            matches = []
            for invalid_row in state.invalid_rows:
                # Calculate fuzzy scores
                name_score = fuzz.token_set_ratio(no_row.practice, invalid_row.practice)
                address_score = fuzz.ratio(no_row.address, invalid_row.address)

                # Weighted average (70% name, 30% address)
                combined_score = (name_score * 0.7) + (address_score * 0.3)

                # Only include matches ≥80% confidence
                if combined_score >= 80:
                    matches.append({
                        'invalid_row_num': invalid_row.row_num,
                        'practice': invalid_row.practice,
                        'phone': invalid_row.phone,
                        'address': invalid_row.address,
                        'city': invalid_row.city,
                        'state': invalid_row.state,
                        'zip': invalid_row.zip,
                        'reason': invalid_row.reason,
                        'notes': invalid_row.notes,
                        'name_score': round(name_score, 1),
                        'address_score': round(address_score, 1),
                        'combined_score': round(combined_score, 1)
                    })

            # Sort matches by combined score (descending)
            matches.sort(key=lambda x: x['combined_score'], reverse=True)

            orphan_matches.append({
                'no_row_num': no_row.row_num,
                'practice': no_row.practice,
                'address': no_row.address,
                'city': no_row.city,
                'state': no_row.state,
                'zip': no_row.zip,
                'qty_2025': no_row.qty_2025,
                'matches': matches[:5]  # Top 5 matches
            })

    return jsonify({
        'success': True,
        'orphan_nos': orphan_matches,
        'count': len(orphan_matches)
    })

@app.route('/api/confirm_orphan_invalid', methods=['POST'])
def api_confirm_orphan_invalid():
    """Confirm that an orphan NO matches an invalid provider"""
    data = request.get_json()
    no_row_num = data.get('no_row_num')
    invalid_row_num = data.get('invalid_row_num')

    # Find the NO row
    no_row = next((r for r in state.no_rows if r.row_num == no_row_num), None)
    if not no_row:
        return jsonify({'success': False, 'error': 'NO row not found'}), 404

    # Find the invalid row
    invalid_row = next((r for r in state.invalid_rows if r.row_num == invalid_row_num), None)
    if not invalid_row:
        return jsonify({'success': False, 'error': 'Invalid row not found'}), 404

    # Mark the NO row as confirmed invalid
    # Add a note to track this decision
    no_row.is_orphan = False  # Remove from orphan list

    # Log the confirmation (could add to undo stack if needed)
    return jsonify({
        'success': True,
        'message': f"Confirmed {no_row.practice} matches invalid provider {invalid_row.practice}"
    })

@app.route('/api/get_merge_candidates', methods=['POST'])
def api_get_merge_candidates():
    """Get detailed info for rows to merge"""
    data = request.get_json()
    row_nums = data.get('row_nums', [])

    if len(row_nums) < 2:
        return jsonify({'success': False, 'error': 'At least 2 rows required for merge'}), 400

    rows = []
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            rows.append({
                'row_num': row.row_num,
                'practice': row.practice,
                'phone': row.phone,
                'address': row.address,
                'city': row.city,
                'state': row.state,
                'zip': row.zip,
                'qty_2023': row.qty_2023,
                'qty_2024': row.qty_2024,
                'qty_2025': row.qty_2025,
                'status': row.status,
                'notes': row.notes,
                'bg_color': row.bg_color
            })

    # Extract unique phone numbers for selection
    phones = list(set(r['phone'] for r in rows if r['phone']))

    # Extract note chunks from all rows
    all_note_chunks = []
    for row in rows:
        if row['notes']:
            chunks = [c.strip() for c in row['notes'].split(';') if c.strip()]
            for chunk in chunks:
                if chunk not in all_note_chunks:
                    all_note_chunks.append(chunk)

    # Suggest network name from common words in practice names
    practice_words = []
    for row in rows:
        words = row['practice'].split()
        practice_words.extend(words)

    # Count word frequency (excluding common articles)
    from collections import Counter
    word_counts = Counter(w.lower() for w in practice_words if len(w) > 3 and w.lower() not in ['obgyn', 'gynecology', 'obstetrics'])
    suggested_network = word_counts.most_common(1)[0][0].title() if word_counts else ""

    return jsonify({
        'success': True,
        'rows': rows,
        'phones': phones,
        'all_note_chunks': all_note_chunks,
        'suggested_network': suggested_network
    })

@app.route('/api/execute_merge', methods=['POST'])
def api_execute_merge():
    """Execute merge of multiple rows into one"""
    data = request.get_json()
    row_nums = data.get('row_nums', [])  # All rows to merge
    keep_row_num = data.get('keep_row_num')  # Row to keep
    network_name = data.get('network_name', '')
    selected_phone = data.get('selected_phone', '')
    selected_notes = data.get('selected_notes', [])  # List of note chunks to keep

    if len(row_nums) < 2:
        return jsonify({'success': False, 'error': 'At least 2 rows required'}), 400

    if keep_row_num not in row_nums:
        return jsonify({'success': False, 'error': 'Keep row must be in merge list'}), 400

    # Track changes for undo
    before_states = []
    after_states = []

    # Find the row to keep
    keep_row = next((r for r in state.wl_rows if r.row_num == keep_row_num), None)
    if not keep_row:
        return jsonify({'success': False, 'error': 'Keep row not found'}), 404

    # Capture before state of keep row
    before_states.append({
        'row_num': keep_row.row_num,
        'practice': keep_row.practice,
        'phone': keep_row.phone,
        'notes': keep_row.notes,
        'network_name': keep_row.network_name,
        'action': keep_row.action
    })

    # Update the keep row
    if network_name:
        keep_row.practice = network_name
        keep_row.network_name = network_name

    if selected_phone:
        keep_row.field_edits['phone'] = selected_phone

    # Merge notes
    merged_notes = '; '.join(selected_notes) if selected_notes else keep_row.notes
    keep_row.field_edits['notes'] = merged_notes
    keep_row.action = 'edit'

    # Capture after state of keep row
    after_states.append({
        'row_num': keep_row.row_num,
        'practice': keep_row.practice,
        'phone': keep_row.phone if 'phone' not in keep_row.field_edits else keep_row.field_edits['phone'],
        'notes': merged_notes,
        'network_name': keep_row.network_name,
        'action': keep_row.action,
        'field_edits': dict(keep_row.field_edits)
    })

    # Mark other rows for deletion
    deleted_rows = []
    for row_num in row_nums:
        if row_num != keep_row_num:
            row = next((r for r in state.wl_rows if r.row_num == row_num), None)
            if row:
                before_states.append({
                    'row_num': row.row_num,
                    'action': row.action
                })
                row.action = 'delete'
                after_states.append({
                    'row_num': row.row_num,
                    'action': 'delete'
                })
                deleted_rows.append(row_num)

    # Add to undo stack
    add_to_undo_stack(
        action_type='merge_rows',
        description=f"Merged {len(row_nums)} rows into row {keep_row_num}",
        before_state={'rows': before_states, 'deleted_rows': deleted_rows},
        after_state={'rows': after_states}
    )

    return jsonify({
        'success': True,
        'kept_row': keep_row_num,
        'deleted_rows': deleted_rows,
        'count': len(row_nums)
    })

@app.route('/api/analyze_notes', methods=['GET'])
def api_analyze_notes():
    """Extract and analyze all note chunks from Working List

    Returns frequency analysis of note patterns for manual categorization.
    Used to build data-driven notes_patterns.json configuration.
    """
    from collections import Counter

    all_chunks = []
    chunk_locations = {}

    # Extract all note chunks
    for row in state.wl_rows:
        if row.notes:
            # Split by semicolon, strip whitespace
            chunks = [c.strip() for c in row.notes.split(';') if c.strip()]

            for chunk in chunks:
                chunk_lower = chunk.lower()
                all_chunks.append(chunk_lower)

                # Track which rows contain this chunk
                if chunk_lower not in chunk_locations:
                    chunk_locations[chunk_lower] = []
                chunk_locations[chunk_lower].append(row.row_num)

    # Count frequencies
    chunk_counts = Counter(all_chunks)

    # Build analysis results
    analysis = []
    total_rows_with_notes = sum(1 for r in state.wl_rows if r.notes)

    for chunk, count in chunk_counts.most_common():
        pct = round(count / len(state.wl_rows) * 100, 1) if state.wl_rows else 0

        analysis.append({
            'chunk': chunk,
            'count': count,
            'pct': pct,
            'example_rows': chunk_locations[chunk][:3]  # First 3 examples
        })

    return jsonify({
        'success': True,
        'total_unique_chunks': len(analysis),
        'total_rows': len(state.wl_rows),
        'total_with_notes': total_rows_with_notes,
        'chunks': analysis
    })

@app.route('/api/download_notes_csv', methods=['GET'])
def api_download_notes_csv():
    """Export notes analysis as CSV for LLM categorization

    Returns CSV file with note chunks, frequencies, and examples.
    User can review with Claude/GPT to categorize patterns.
    """
    from collections import Counter
    import io
    import csv
    from flask import make_response

    all_chunks = []
    chunk_locations = {}

    # Extract all note chunks
    for row in state.wl_rows:
        if row.notes:
            chunks = [c.strip() for c in row.notes.split(';') if c.strip()]
            for chunk in chunks:
                chunk_lower = chunk.lower()
                all_chunks.append(chunk_lower)

                if chunk_lower not in chunk_locations:
                    chunk_locations[chunk_lower] = []
                chunk_locations[chunk_lower].append(row.row_num)

    # Count frequencies
    chunk_counts = Counter(all_chunks)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['chunk', 'count', 'pct', 'example_rows'])

    # Write data rows
    total_rows = len(state.wl_rows)
    for chunk, count in chunk_counts.most_common():
        pct = round(count / total_rows * 100, 1) if total_rows else 0
        example_rows = ','.join(str(r) for r in chunk_locations[chunk][:3])
        writer.writerow([chunk, count, pct, example_rows])

    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=notes_analysis.csv'

    return response

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def open_browser():
    """Open browser after short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EOY Cleanup Tool')
    parser.add_argument('--assume-yes', action='store_true', help='Automatically answer yes to prompts')
    args = parser.parse_args()

    print("\n" + "="*80)
    print("EOY Cleanup Tool - Starting...")
    if args.assume_yes:
        print("Mode: AUTOMATED (Input prompts disabled)")
    print("="*80)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Flask app
    app.run(debug=True, use_reloader=False, port=5000)
