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
import csv
import io
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
    reason: str  # Why they're invalid

    def to_dict(self):
        return {
            'row_num': self.row_num,
            'practice': self.practice,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'reason': self.reason
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
        self.invalid_rows: List[InvalidRow] = []  # Invalid/Inactive List providers
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

# Global state instance
state = AppState()

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

    sh = gc.open('OBGYN List 2025 - Use This List!')

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

    # Parse Invalid/Inactive List rows and extract reasons
    # Assumed structure: Practice, Phone, Address, City, State, [Zip], Reason
    invalid_rows = []
    invalid_reasons = set()
    for i, row in enumerate(invalid_data[1:], start=2):  # Start at row 2 (after header)
        if len(row) >= 5:  # Need at least practice through state
            practice = row[0] if len(row) > 0 else ""
            phone = row[1] if len(row) > 1 else ""
            address = row[2] if len(row) > 2 else ""
            city = row[3] if len(row) > 3 else ""
            state_val = row[4] if len(row) > 4 else ""
            # Reason might be in column 5, 6, or beyond
            reason = ""
            for j in range(5, min(len(row), 10)):
                if row[j] and len(row[j]) > 5:  # Looks like a reason, not zip
                    reason = row[j]
                    break

            if practice or address:  # Only add if has some identifying info
                invalid_rows.append(InvalidRow(
                    row_num=i,
                    practice=practice,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state_val,
                    reason=reason
                ))
                if reason:
                    invalid_reasons.add(reason)

    print(f"  Loaded {len(invalid_rows)} Invalid/Inactive rows")

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
    # Remove non-breaking spaces and other unicode whitespace
    phone = phone.replace('\xa0', ' ').strip()
    # Remove extension first (ext, x, Ext., etc.)
    phone_clean = re.sub(r'\s*(ext\.?|x|extension)\s*\d+$', '', phone, flags=re.IGNORECASE)
    digits = re.sub(r'[^\d]', '', phone_clean)
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
            if not row.notes or 'vm' not in row.notes.lower():
                row.issues.append({
                    'category': 'fuschia_vm',
                    'severity': 'review',
                    'message': "Fuschia but no 'vm' in notes"
                })
                counts['fuschia_vm'] += 1

        # Green with "sent"
        elif color in ['#00ff00', '#00ff01', '#00fe00']:
            if row.notes and 'sent' in row.notes.lower():
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
            if row.notes:
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
        if not row.notes or 'not interested' not in row.notes.lower():
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
        if row.notes and 'sent' in row.notes.lower():
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
            description="New Orders without yellow match in Working List",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=[]
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
            description="'Not interested' but notes suggest invalid provider",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["move_to_invalid", "keep_as_is"]
        ),
        ReviewCategory(
            id="manual_review",
            name="Manual Review",
            description="Complex cases requiring engineer judgment",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["edit", "delete", "change_status", "move_to_invalid",
                             "merge", "add_vm_note", "mark_reviewed", "keep_as_is"]
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
        return None, None, None, None, None

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


def calculate_progress() -> Dict:
    """
    Calculate progress counts by urgency level.
    Returns dict with counts for critical, review, verify, and resolved.
    """
    # Define urgency levels
    CRITICAL = {'exact_dupes', 'yellow_low', 'orphan_no', 'red_invalid'}
    REVIEW = {'networks', 'fuzzy_dupes', 'yellow_80', 'green_sent', 'not_interested_invalid'}
    VERIFY = {'yellow_95', 'fuschia_vm', 'manual_review'}

    counts = {
        'critical_total': 0,
        'critical_resolved': 0,
        'review_total': 0,
        'review_resolved': 0,
        'verify_total': 0,
        'verify_resolved': 0,
    }

    # Track which rows we've already counted (for multi-category rows)
    # Use highest urgency for each row
    row_urgency = {}  # row_num -> urgency level

    for cat in state.categories:
        if cat.id in CRITICAL:
            urgency = 'critical'
            priority = 3
        elif cat.id in REVIEW:
            urgency = 'review'
            priority = 2
        elif cat.id in VERIFY:
            urgency = 'verify'
            priority = 1
        else:
            continue  # Unknown category

        for row_num in cat.row_nums:
            # Only count in highest urgency category
            current = row_urgency.get(row_num)
            if current is None or priority > current[1]:
                row_urgency[row_num] = (urgency, priority)

    # Now count by urgency
    for row_num, (urgency, _) in row_urgency.items():
        counts[f'{urgency}_total'] += 1

        # Check if resolved (has action taken)
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.action:
            counts[f'{urgency}_resolved'] += 1

    # Calculate totals and percentages
    total = counts['critical_total'] + counts['review_total'] + counts['verify_total']
    resolved = counts['critical_resolved'] + counts['review_resolved'] + counts['verify_resolved']

    counts['total'] = total
    counts['resolved'] = resolved
    counts['percent'] = round((resolved / total * 100) if total > 0 else 0, 1)

    # Calculate segment widths for the progress bar
    if total > 0:
        counts['critical_width'] = round(counts['critical_total'] / total * 100, 1)
        counts['review_width'] = round(counts['review_total'] / total * 100, 1)
        counts['verify_width'] = round(counts['verify_total'] / total * 100, 1)
    else:
        counts['critical_width'] = 0
        counts['review_width'] = 0
        counts['verify_width'] = 0

    return counts


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
                         categories=state.categories,
                         progress=calculate_progress(),
                         state=state)

@app.route('/api/save_progress', methods=['POST'])
def api_save_progress():
    """API endpoint to save progress"""
    try:
        filename = save_progress()
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get_progress')
def api_get_progress():
    """Get current progress by urgency level"""
    return jsonify(calculate_progress())


def get_action_taken(row) -> str:
    """
    Derive action taken label for a row based on its action and field_edits.
    Returns standard action labels for export.
    """
    if not row.action and not row.field_edits:
        return ''

    action = row.action or ''

    # Map actions to standard labels
    action_map = {
        'deleted': 'DELETED',
        'accepted': 'VERIFIED',
        'verified': 'VERIFIED',
        'marked_reviewed': 'VERIFIED',
        'matched': 'VERIFIED',
        'merged_into': 'MERGED',
        'network_confirmed': 'NETWORK_CONFIRMED',
        'moved_to_invalid': 'MOVED_TO_INVALID',
        'converted': 'CONVERTED',
    }

    # Check for action match
    for key, label in action_map.items():
        if key in action.lower():
            return label

    # If has field edits but no specific action
    if row.field_edits:
        return 'EDITED'

    # Has some action but not mapped
    if action:
        return 'MODIFIED'

    return ''


@app.route('/api/export')
def api_export():
    """
    Export all rows as CSV.
    Query params:
    - mode: 'download' (file) or 'clipboard' (json with CSV text)
    - include_deleted: 'true' or 'false' (default true)
    """
    from flask import Response

    mode = request.args.get('mode', 'clipboard')
    include_deleted = request.args.get('include_deleted', 'true').lower() == 'true'

    # Filter rows
    rows = state.wl_rows
    if not include_deleted:
        rows = [r for r in rows if 'deleted' not in (r.action or '').lower()]

    # Sort by row_num
    rows = sorted(rows, key=lambda r: r.row_num)

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    for row in rows:
        # Clean notes (replace newlines with space)
        notes = (row.notes or '').replace('\n', ' ').replace('\r', ' ')

        # Get action taken
        action_taken = get_action_taken(row)

        # Write row: practice, phone, address, city, state, zip, qty_2023, qty_2024, qty_2025, status, notes, action_taken
        writer.writerow([
            row.practice,
            row.phone,
            row.address,
            row.city,
            row.state,
            row.zip,
            row.qty_2023,
            row.qty_2024,
            row.qty_2025,
            row.status,
            notes,
            action_taken
        ])

    csv_text = output.getvalue()

    if mode == 'download':
        # Return as downloadable file
        filename = f'eoy_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return Response(
            csv_text,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    else:
        # Return as JSON for clipboard copy
        return jsonify({
            'success': True,
            'csv': csv_text,
            'row_count': len(rows)
        })


def restore_state(action: Dict, direction: str = 'undo') -> bool:
    """
    Restore state based on action type.
    direction: 'undo' restores before_state, 'redo' restores after_state
    Returns True if restoration was successful.
    """
    action_type = action.get('action_type')
    before_state = action.get('before_state', {})
    after_state = action.get('after_state', {})

    # Choose which state to restore
    target_state = before_state if direction == 'undo' else after_state

    try:
        if action_type == 'edit_field':
            # Single field edit
            row_num = target_state.get('row_num') if direction == 'undo' else after_state.get('row_num')
            row = next((r for r in state.wl_rows if r.row_num == row_num), None)
            if row:
                if direction == 'undo':
                    field = target_state.get('field')
                    old_value = target_state.get('old_value', '')
                    setattr(row, field, old_value)
                    if field == 'status':
                        row.bg_color = status_to_color(old_value)
                else:
                    field = after_state.get('field')
                    new_value = after_state.get('new_value', '')
                    setattr(row, field, new_value)
                    if field == 'status':
                        row.bg_color = status_to_color(new_value)
            return True

        elif action_type in ['delete', 'delete_rows']:
            # Row deletion - restore or re-delete
            rows_data = before_state.get('rows', [])
            for row_data in rows_data:
                row_num = row_data.get('row_num')
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                if row:
                    if direction == 'undo':
                        # Restore deleted row
                        row.action = row_data.get('fields', {}).get('action', None)
                    else:
                        # Re-delete
                        row.action = 'deleted'
            return True

        elif action_type == 'mark_reviewed':
            rows_data = before_state.get('rows', [])
            for row_data in rows_data:
                row_num = row_data.get('row_num')
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                if row:
                    if direction == 'undo':
                        # Restore original action
                        row.action = row_data.get('fields', {}).get('action', None)
                    else:
                        row.action = 'reviewed_no_change'
            return True

        elif action_type == 'send_to_manual_review':
            rows_data = before_state.get('rows', [])
            manual_review_cat = next((c for c in state.categories if c.id == 'manual_review'), None)

            for row_data in rows_data:
                row_num = row_data.get('row_num')
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)

                if direction == 'undo':
                    # Remove from manual review
                    if manual_review_cat and row_num in manual_review_cat.row_nums:
                        manual_review_cat.row_nums.remove(row_num)
                    # Remove manual_review issue
                    if row:
                        row.issues = [i for i in row.issues if i.get('category') != 'manual_review']
                else:
                    # Re-add to manual review
                    if manual_review_cat and row_num not in manual_review_cat.row_nums:
                        manual_review_cat.row_nums.append(row_num)
            return True

        elif action_type == 'confirm_orphan_match':
            orphan_row_num = before_state.get('orphan_row_num')
            no_row = next((r for r in state.no_rows if r.row_num == orphan_row_num), None)
            orphan_cat = next((c for c in state.categories if c.id == 'orphan_no'), None)

            if no_row:
                if direction == 'undo':
                    # Restore orphan status
                    no_row.is_orphan = True
                    if orphan_cat and orphan_row_num not in orphan_cat.row_nums:
                        orphan_cat.row_nums.append(orphan_row_num)
                else:
                    no_row.is_orphan = False
                    if orphan_cat and orphan_row_num in orphan_cat.row_nums:
                        orphan_cat.row_nums.remove(orphan_row_num)
            return True

        elif action_type in ['keep_first_delete_rest', 'accept_all', 'batch_action',
                              'change_status', 'change_to_white', 'remove_sent', 'mass_invalid',
                              'merge_rows', 'confirm_network']:
            # Bulk actions - restore all affected rows
            rows_data = before_state.get('rows', [])
            for row_data in rows_data:
                row_num = row_data.get('row_num')
                fields = row_data.get('fields', {})
                row = next((r for r in state.wl_rows if r.row_num == row_num), None)
                if row:
                    if direction == 'undo':
                        for field, value in fields.items():
                            if hasattr(row, field):
                                setattr(row, field, value)
                        # Clear field_edits that were set by the action
                        row.field_edits = {}
                    # For redo, would need to re-apply the action
            return True

        else:
            # Unknown action type - log but don't fail
            print(f"[Undo/Redo] Unknown action type: {action_type}")
            return True

    except Exception as e:
        print(f"[Undo/Redo] Error restoring state: {e}")
        return False

@app.route('/api/undo', methods=['POST'])
def api_undo():
    """API endpoint to undo last action"""
    if not state.undo_stack:
        return jsonify({'success': False, 'error': 'Nothing to undo'}), 400

    action = state.undo_stack.pop()

    # Apply undo (restore before_state)
    success = restore_state(action, 'undo')

    if success:
        state.redo_stack.append(action)

    return jsonify({
        'success': success,
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

    # Apply redo (restore after_state)
    success = restore_state(action, 'redo')

    if success:
        state.undo_stack.append(action)

    return jsonify({
        'success': success,
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

    # Check if notes exist
    if not row.notes:
        return jsonify({'success': False, 'error': 'No notes to delete from'}), 400

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
            notes = re.sub(r':?sent', '', row.notes or '', flags=re.IGNORECASE).strip()
            if not notes or 'not interested' not in notes.lower():
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

    # Fix qty mismatches
    count = 0
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row.matched_no_row:
            # Find matching NO row
            no_row = next((n for n in state.no_rows if n.row_num == row.matched_no_row), None)
            if no_row:
                # Update qty to match NO row
                row.field_edits['qty_2025'] = no_row.qty_2025
                row.action = 'edit'
                count += 1

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
                if existing_notes and not existing_notes.endswith(';'):
                    existing_notes += '; '
                elif existing_notes:
                    existing_notes += ' '
                row.field_edits['notes'] = existing_notes + note_to_add + ';'
                row.action = 'edit'
                count += 1

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

    import re
    count = 0
    for row_num in target_rows:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
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
            count += 1

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

    count = 0
    before_states = []
    for row_num in target_rows:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {'status': row.status, 'bg_color': row.bg_color, 'action': row.action}
            })
            # Update status
            row.field_edits['status'] = new_status
            # Derive color from status
            row.field_edits['bg_color'] = status_to_color(new_status)
            row.action = 'edit'
            count += 1

    if before_states:
        add_to_undo_stack(
            'change_status',
            f'Changed status to "{new_status}" on {count} row(s)',
            {'rows': before_states, 'new_status': new_status}
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

    count = 0
    before_states = []
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {
                    'status': row.status, 'bg_color': row.bg_color,
                    'qty_2025': row.qty_2025, 'notes': row.notes, 'action': row.action
                }
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
            count += 1

    if before_states:
        add_to_undo_stack(
            'change_to_white',
            f'Changed {count} row(s) to Not Interested',
            {'rows': before_states}
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

    count = 0
    before_states = []
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
                before_states.append({
                    'row_num': row_num,
                    'fields': {'notes': row.notes, 'action': row.action}
                })
                row.field_edits['notes'] = new_notes
                row.action = 'edit'
                count += 1

    if before_states:
        add_to_undo_stack(
            'remove_sent',
            f'Removed "sent" from {count} row(s)',
            {'rows': before_states}
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

    count = 0
    before_states = []
    for row_num in category.row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {'action': row.action}
            })
            row.action = 'move_to_invalid'
            row.field_edits['invalid_reason'] = reason
            count += 1

    if before_states:
        add_to_undo_stack(
            'mass_invalid',
            f'Marked {count} row(s) as invalid',
            {'rows': before_states, 'reason': reason}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/get_duplicate_group', methods=['POST'])
def api_get_duplicate_group():
    """Get all rows in a duplicate group for merge UI"""
    data = request.get_json()
    group_id = data.get('group_id')
    row_num = data.get('row_num')

    # Find group_id from row_num if not provided
    if not group_id and row_num:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            group_id = row.duplicate_group_id

    if not group_id:
        return jsonify({'success': False, 'error': 'No duplicate group specified'}), 400

    # Get all rows in this group
    group_rows = [r for r in state.wl_rows if r.duplicate_group_id == group_id]

    if len(group_rows) < 2:
        return jsonify({'success': False, 'error': 'Not enough rows in group'}), 400

    return jsonify({
        'success': True,
        'group_id': group_id,
        'rows': [r.to_dict() for r in group_rows]
    })

@app.route('/api/merge_rows', methods=['POST'])
def api_merge_rows():
    """
    Merge duplicate rows into a survivor.
    - survivor_row_num: Row that will keep existing
    - other_row_nums: Rows to merge into survivor then delete
    - merge_fields: Optional dict of field -> row_num to take value from
    """
    data = request.get_json()
    survivor_row_num = data.get('survivor_row_num')
    other_row_nums = data.get('other_row_nums', [])
    merge_fields = data.get('merge_fields', {})  # field -> row_num

    if not survivor_row_num:
        return jsonify({'success': False, 'error': 'No survivor row specified'}), 400

    if not other_row_nums:
        return jsonify({'success': False, 'error': 'No rows to merge'}), 400

    # Find survivor row
    survivor = next((r for r in state.wl_rows if r.row_num == survivor_row_num), None)
    if not survivor:
        return jsonify({'success': False, 'error': 'Survivor row not found'}), 404

    # Find other rows
    others = [r for r in state.wl_rows if r.row_num in other_row_nums]
    if not others:
        return jsonify({'success': False, 'error': 'No other rows found'}), 404

    # Store before states for undo
    before_states = [{
        'row_num': survivor.row_num,
        'fields': {
            'practice': survivor.practice, 'phone': survivor.phone,
            'address': survivor.address, 'city': survivor.city,
            'state': survivor.state, 'zip': survivor.zip,
            'notes': survivor.notes, 'action': survivor.action
        }
    }]
    for other in others:
        before_states.append({
            'row_num': other.row_num,
            'fields': {'action': other.action}
        })

    # Apply field merges from specific rows
    for field, source_row_num in merge_fields.items():
        source = next((r for r in state.wl_rows if r.row_num == source_row_num), None)
        if source and hasattr(survivor, field):
            value = getattr(source, field, '')
            setattr(survivor, field, value)
            survivor.field_edits[field] = value

    # Merge notes from all rows (combine unique chunks)
    all_notes = set()
    if survivor.notes:
        all_notes.update(c.strip() for c in survivor.notes.split(';') if c.strip())
    for other in others:
        if other.notes:
            all_notes.update(c.strip() for c in other.notes.split(';') if c.strip())

    if all_notes:
        merged_notes = '; '.join(sorted(all_notes))
        survivor.notes = merged_notes
        survivor.field_edits['notes'] = merged_notes

    survivor.action = 'merged_survivor'

    # Mark others as deleted
    for other in others:
        other.action = 'merged_deleted'

    add_to_undo_stack(
        'merge_rows',
        f'Merged {len(others) + 1} rows (survivor: #{survivor_row_num})',
        {'rows': before_states, 'survivor_row_num': survivor_row_num, 'other_row_nums': other_row_nums}
    )

    return jsonify({
        'success': True,
        'survivor_row_num': survivor_row_num,
        'deleted_count': len(others)
    })

@app.route('/api/get_network_group', methods=['POST'])
def api_get_network_group():
    """Get all rows in a network for confirm_network UI"""
    data = request.get_json()
    row_num = data.get('row_num')

    if not row_num:
        return jsonify({'success': False, 'error': 'No row number provided'}), 400

    # Find the row and its network_name
    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
    if not row or not row.network_name:
        return jsonify({'success': False, 'error': 'Row is not part of a network'}), 400

    network_name = row.network_name

    # Get all rows with the same network_name
    network_rows = [r for r in state.wl_rows if r.network_name == network_name]

    # Auto-derive a better network name from common words
    suggested_name = derive_network_name(network_rows)

    return jsonify({
        'success': True,
        'network_name': network_name,
        'suggested_name': suggested_name,
        'rows': [r.to_dict() for r in network_rows]
    })

def derive_network_name(rows):
    """
    Derive a readable network name from common practice name words.
    E.g., "Downtown Medical", "Uptown Medical" -> "Medical"
    """
    if not rows:
        return "Unknown Network"

    # Get words from all practice names, excluding common suffixes
    exclude_words = {'the', 'of', 'and', 'at', 'in', 'for', 'a', 'an',
                     'north', 'south', 'east', 'west', 'downtown', 'uptown',
                     'medical', 'clinic', 'center', 'office', 'health',
                     'healthcare', 'care', 'group', 'associates', 'llc', 'pc', 'md'}

    word_lists = []
    for r in rows:
        words = set(w.lower() for w in re.split(r'\W+', r.practice) if len(w) > 2)
        word_lists.append(words)

    # Find common words across all practices
    if word_lists:
        common = word_lists[0].copy()
        for wl in word_lists[1:]:
            common &= wl

        # Remove excluded words
        meaningful = common - exclude_words

        if meaningful:
            # Return the longest meaningful word, capitalized
            best_word = max(meaningful, key=len)
            return best_word.title() + " Network"

    # Fallback: use first practice name
    first_name = rows[0].practice.split()[0] if rows[0].practice else "Unknown"
    return first_name + " Network"

@app.route('/api/confirm_network', methods=['POST'])
def api_confirm_network():
    """
    Confirm rows as a network.
    - network_name: The name for this network
    - row_nums: Rows to include in the network
    - add_note: Optional note to add to all rows
    """
    data = request.get_json()
    network_name = data.get('network_name', 'Confirmed Network')
    row_nums = data.get('row_nums', [])
    add_note = data.get('add_note', '')

    if not row_nums:
        return jsonify({'success': False, 'error': 'No rows specified'}), 400

    count = 0
    before_states = []

    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {
                    'network_name': row.network_name,
                    'notes': row.notes,
                    'action': row.action
                }
            })

            # Update network name
            row.network_name = network_name

            # Add note if provided
            if add_note:
                current_notes = row.notes or ""
                if add_note.lower() not in current_notes.lower():
                    if current_notes and not current_notes.endswith(';'):
                        current_notes += '; '
                    elif current_notes:
                        current_notes += ' '
                    row.notes = current_notes + add_note
                    row.field_edits['notes'] = row.notes

            row.action = 'network_confirmed'
            count += 1

    # Remove from networks category since confirmed
    networks_cat = next((c for c in state.categories if c.id == 'networks'), None)
    if networks_cat:
        for row_num in row_nums:
            if row_num in networks_cat.row_nums:
                networks_cat.row_nums.remove(row_num)

    if before_states:
        add_to_undo_stack(
            'confirm_network',
            f'Confirmed {count} row(s) as "{network_name}"',
            {'rows': before_states, 'network_name': network_name}
        )

    return jsonify({
        'success': True,
        'count': count,
        'network_name': network_name
    })

@app.route('/api/send_to_manual_review', methods=['POST'])
def api_send_to_manual_review():
    """Send row(s) to Manual Review category for closer inspection"""
    data = request.get_json()
    row_nums = data.get('row_nums', [])
    reason = data.get('reason', 'Needs manual review')

    if not row_nums:
        return jsonify({'success': False, 'error': 'No row numbers provided'}), 400

    # Find or create manual_review category
    manual_review_cat = next((c for c in state.categories if c.id == 'manual_review'), None)
    if not manual_review_cat:
        # Create it if it doesn't exist (e.g., was filtered out as empty)
        manual_review_cat = ReviewCategory(
            id="manual_review",
            name="Manual Review",
            description="Complex cases requiring engineer judgment",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["edit", "delete", "change_status", "move_to_invalid",
                             "merge", "add_vm_note", "mark_reviewed", "keep_as_is"]
        )
        state.categories.append(manual_review_cat)

    count = 0
    before_states = []
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row and row_num not in manual_review_cat.row_nums:
            before_states.append({
                'row_num': row_num,
                'fields': {'practice': row.practice, 'status': row.status, 'notes': row.notes}
            })
            manual_review_cat.row_nums.append(row_num)
            # Add issue to row
            row.issues.append({
                'category': 'manual_review',
                'severity': 'review',
                'message': reason
            })
            count += 1

    manual_review_cat.row_nums.sort()

    if before_states:
        add_to_undo_stack(
            'send_to_manual_review',
            f'Sent {count} row(s) to Manual Review',
            {'rows': before_states, 'reason': reason}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/mark_reviewed', methods=['POST'])
def api_mark_reviewed():
    """Mark row as reviewed (no changes needed) for progress tracking"""
    data = request.get_json()
    row_nums = data.get('row_nums', [])

    if not row_nums:
        return jsonify({'success': False, 'error': 'No row numbers provided'}), 400

    count = 0
    before_states = []
    for row_num in row_nums:
        row = next((r for r in state.wl_rows if r.row_num == row_num), None)
        if row:
            before_states.append({
                'row_num': row_num,
                'fields': {'action': row.action}
            })
            row.action = 'reviewed_no_change'
            count += 1

    if before_states:
        add_to_undo_stack(
            'mark_reviewed',
            f'Marked {count} row(s) as reviewed',
            {'rows': before_states}
        )

    return jsonify({'success': True, 'count': count})

@app.route('/api/edit_field', methods=['POST'])
def api_edit_field():
    """
    Edit a single field of a row.
    Used for inline editing (double-click to edit).
    """
    data = request.get_json()
    row_num = data.get('row_num')
    field = data.get('field')
    value = data.get('value', '')

    if not row_num or not field:
        return jsonify({'success': False, 'error': 'Missing row_num or field'}), 400

    # Find the row
    row = next((r for r in state.wl_rows if r.row_num == row_num), None)
    if not row:
        return jsonify({'success': False, 'error': 'Row not found'}), 404

    # Editable fields
    editable_fields = ['practice', 'phone', 'address', 'city', 'state', 'zip', 'status', 'notes', 'qty_2025']

    if field not in editable_fields:
        return jsonify({'success': False, 'error': f'Field {field} is not editable'}), 400

    # Store before state for undo
    old_value = getattr(row, field, '')
    before_state = {
        'row_num': row_num,
        'field': field,
        'old_value': old_value
    }

    # Update the field
    setattr(row, field, value)

    # If status changed, update bg_color
    if field == 'status':
        row.bg_color = status_to_color(value)

    # Track field edit
    row.field_edits[field] = value
    row.action = 'edited'

    add_to_undo_stack(
        'edit_field',
        f'Changed {field} on row #{row_num}',
        before_state,
        {'row_num': row_num, 'field': field, 'new_value': value}
    )

    return jsonify({
        'success': True,
        'row_num': row_num,
        'field': field,
        'value': value,
        'bg_color': row.bg_color if field == 'status' else None
    })

@app.route('/api/match_orphan_to_invalid', methods=['POST'])
def api_match_orphan_to_invalid():
    """
    Match an orphan New Order row against the Invalid/Inactive List.
    Returns match info if found (≥80% confidence) or suggests manual review.
    """
    data = request.get_json()
    row_num = data.get('row_num')

    if not row_num:
        return jsonify({'success': False, 'error': 'No row number provided'}), 400

    # Find the orphan NO row
    no_row = next((r for r in state.no_rows if r.row_num == row_num and r.is_orphan), None)
    if not no_row:
        return jsonify({'success': False, 'error': 'Orphan row not found'}), 404

    # Fuzzy match against Invalid/Inactive List
    best_match = None
    best_score = 0.0

    for inv_row in state.invalid_rows:
        # Skip if different state
        if inv_row.state and no_row.state and inv_row.state.lower() != no_row.state.lower():
            continue

        # Calculate weighted match score (70% name, 30% address)
        name_score = fuzz.token_set_ratio(
            normalize_name(no_row.practice),
            normalize_name(inv_row.practice)
        ) / 100.0

        address_score = fuzz.token_set_ratio(
            normalize_address(no_row.address + ' ' + no_row.city),
            normalize_address(inv_row.address + ' ' + inv_row.city)
        ) / 100.0

        combined_score = (name_score * 0.7) + (address_score * 0.3)

        if combined_score > best_score:
            best_score = combined_score
            best_match = inv_row

    result = {
        'orphan_row': no_row.to_dict(),
        'match_found': best_score >= 0.80,
        'match_confidence': round(best_score * 100, 1)
    }

    if best_match and best_score >= 0.80:
        result['matched_invalid'] = best_match.to_dict()
        result['recommendation'] = 'confirm_match'
        result['message'] = f"Matches invalid provider: {best_match.practice}. Reason: {best_match.reason or 'Not specified'}"
    else:
        result['recommendation'] = 'manual_review'
        result['message'] = "No match found in Invalid/Inactive List. Send to Manual Review."

    return jsonify({'success': True, **result})

@app.route('/api/process_orphan_batch', methods=['POST'])
def api_process_orphan_batch():
    """
    Process all orphan NO rows at once, matching against Invalid List.
    Returns categorized results for bulk handling.
    """
    # Get all orphan rows
    orphan_rows = [r for r in state.no_rows if r.is_orphan]

    results = {
        'matched': [],      # Found in Invalid List (≥80% match)
        'unmatched': [],    # No match - need manual review
        'total': len(orphan_rows)
    }

    for no_row in orphan_rows:
        best_match = None
        best_score = 0.0

        for inv_row in state.invalid_rows:
            # Skip if different state
            if inv_row.state and no_row.state and inv_row.state.lower() != no_row.state.lower():
                continue

            # Calculate weighted match score
            name_score = fuzz.token_set_ratio(
                normalize_name(no_row.practice),
                normalize_name(inv_row.practice)
            ) / 100.0

            address_score = fuzz.token_set_ratio(
                normalize_address(no_row.address + ' ' + no_row.city),
                normalize_address(inv_row.address + ' ' + inv_row.city)
            ) / 100.0

            combined_score = (name_score * 0.7) + (address_score * 0.3)

            if combined_score > best_score:
                best_score = combined_score
                best_match = inv_row

        if best_match and best_score >= 0.80:
            results['matched'].append({
                'orphan': no_row.to_dict(),
                'invalid_match': best_match.to_dict(),
                'confidence': round(best_score * 100, 1)
            })
        else:
            results['unmatched'].append({
                'orphan': no_row.to_dict(),
                'best_score': round(best_score * 100, 1) if best_score > 0 else 0
            })

    return jsonify({'success': True, **results})

@app.route('/api/confirm_orphan_match', methods=['POST'])
def api_confirm_orphan_match():
    """
    Confirm that an orphan NO row matches an Invalid List entry.
    Marks the orphan as resolved (explained by invalid provider).
    """
    data = request.get_json()
    orphan_row_num = data.get('orphan_row_num')
    invalid_row_num = data.get('invalid_row_num')
    action = data.get('action', 'confirm')  # 'confirm' or 'reject'

    if not orphan_row_num:
        return jsonify({'success': False, 'error': 'No orphan row number provided'}), 400

    # Find the orphan
    no_row = next((r for r in state.no_rows if r.row_num == orphan_row_num), None)
    if not no_row:
        return jsonify({'success': False, 'error': 'Orphan row not found'}), 404

    if action == 'confirm':
        # Mark orphan as resolved (matched to invalid)
        no_row.is_orphan = False  # No longer orphan - explained
        inv_row = next((r for r in state.invalid_rows if r.row_num == invalid_row_num), None)
        reason = inv_row.reason if inv_row else 'Matched to Invalid List'

        # Remove from orphan_no category
        orphan_cat = next((c for c in state.categories if c.id == 'orphan_no'), None)
        if orphan_cat and orphan_row_num in orphan_cat.row_nums:
            orphan_cat.row_nums.remove(orphan_row_num)

        add_to_undo_stack(
            'confirm_orphan_match',
            f'Confirmed orphan #{orphan_row_num} matches invalid provider',
            {'orphan_row_num': orphan_row_num, 'invalid_row_num': invalid_row_num}
        )

        return jsonify({
            'success': True,
            'message': f'Confirmed match. Reason: {reason}'
        })
    else:
        # Reject match - send to manual review
        manual_review_cat = next((c for c in state.categories if c.id == 'manual_review'), None)
        if manual_review_cat and orphan_row_num not in manual_review_cat.row_nums:
            manual_review_cat.row_nums.append(orphan_row_num)
            manual_review_cat.row_nums.sort()

        return jsonify({
            'success': True,
            'message': 'Sent to Manual Review for further investigation'
        })

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
