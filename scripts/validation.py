"""
Validation pipeline for EOY Cleanup Tool

Phase 2: Match yellow rows to New Orders, detect duplicates/networks, validate status.
"""

import re
from collections import defaultdict
from rapidfuzz import fuzz

from models import ReviewCategory
from helpers import normalize_name, normalize_address, normalize_phone


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


def extract_street_number(address):
    """Extract street number from address for grouping."""
    if not address:
        return None
    # Match leading digits (street number)
    match = re.match(r'^\s*(\d+)', address)
    return match.group(1) if match else None


def detect_address_clusters(wl_rows):
    """Detect rows sharing same address but different phones/names.

    This catches scenarios like:
    - 4 rows with 4 different names and phones
    - But 3 share street number + state
    - Possible same building, multi-location practice, or data issues
    """
    print(f"[Phase 2.3b] Detecting address-based clusters...")

    # Group by (street_number, state) - catches same building
    addr_groups = defaultdict(list)
    for row in wl_rows:
        street_num = extract_street_number(row.address)
        state = (row.state or '').strip().upper()
        if street_num and state:
            key = (street_num, state)
            addr_groups[key].append(row)

    cluster_count = 0
    for key, rows in addr_groups.items():
        if len(rows) < 2:
            continue

        # Skip if ALL already flagged as duplicates/networks (by phone grouping)
        all_already_flagged = all(
            any(issue.get('category') in ['exact_dupes', 'networks', 'fuzzy_dupes']
                for issue in row.issues)
            for row in rows
        )
        if all_already_flagged:
            continue

        # Check if they have DIFFERENT phones (phone grouping would miss these)
        phones = set(normalize_phone(r.phone) for r in rows if r.phone)
        if len(phones) <= 1:
            continue  # Same phone - already caught by phone grouping

        # This is an address cluster with different phones
        street_num, state = key
        for row in rows:
            # Don't double-flag if already caught
            existing_cats = [issue.get('category') for issue in row.issues]
            if 'address_cluster' not in existing_cats:
                row.issues.append({
                    'category': 'address_cluster',
                    'severity': 'review',
                    'message': f"Same address ({street_num}... {state}), different phones ({len(rows)} rows)",
                    'cluster_size': len(rows),
                    'address_key': f"{street_num}, {state}"
                })
                cluster_count += 1

    print(f"  Found {cluster_count} rows in address clusters (different phones)")


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
    """Auto-fix not interested rows (DISABLED - kept for reference)"""
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
    """Identify notes with non-standard chunks (DISABLED - kept for reference)"""
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
            id="address_cluster",
            name="Same Address",
            description="Different phones/names at same street address",
            row_nums=[],
            allow_batch=False,
            primary_action=None,
            secondary_actions=["confirm_network", "merge", "edit", "review_individual"]
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


def run_validations(wl_rows, no_rows, invalid_rows, invalid_reasons):
    """Run all validation phases on pre-loaded data.

    Args:
        wl_rows: List of ProviderRow from WL sheet
        no_rows: List of NewOrderRow from NO sheet
        invalid_rows: List of InvalidRow from Invalid List sheet
        invalid_reasons: List of unique invalid reasons

    Returns:
        categories: List of ReviewCategory objects
    """
    print(f"\n[Phase 2] Running validations...")

    # Validation pipeline
    validate_yellow_to_no(wl_rows, no_rows)
    validate_no_to_wl(wl_rows, no_rows)
    detect_duplicates(wl_rows)
    detect_address_clusters(wl_rows)  # Catches different phones at same address
    validate_status_issues(wl_rows)
    # DISABLED: auto_fix_not_interested(wl_rows)  # No auto-fixing per user request
    # DISABLED: detect_non_standard_notes(wl_rows)  # Not a real category
    categories = categorize_issues(wl_rows, no_rows)

    print(f"\n[Phase 2] Complete!")

    return categories
