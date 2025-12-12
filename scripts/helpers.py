"""
Helper functions for EOY Cleanup Tool

Utility functions for type conversion, text normalization, and color mapping.
"""

import re


def safe_int(value, allow_zero=True):
    """Safely convert value to int, handling None, empty string, and whitespace.

    Args:
        value: The value to convert (could be int, str, None, or '')
        allow_zero: If False, treat 0 as invalid (useful for row_num which starts at 2)

    Returns:
        int or None if invalid
    """
    if value is None:
        return None
    # Handle strings: strip whitespace and check for empty
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return None
    try:
        result = int(value)
        if not allow_zero and result == 0:
            return None
        return result
    except (ValueError, TypeError):
        return None


def safe_int_list(values):
    """Safely convert a list of values to ints, filtering out invalid entries."""
    if not values:
        return []
    return [safe_int(v, allow_zero=False) for v in values if safe_int(v, allow_zero=False) is not None]


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

    # EXACT MATCH enforcement
    # We do NOT use substring matching to prevent "Voicemail" matching "Voicemail/No Answer"

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
