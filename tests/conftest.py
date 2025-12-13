"""
pytest configuration and fixtures for EOY tool testing

Fixtures provide real data samples for fast, repeatable testing
without hitting Google Sheets API every time.

Data Loading Strategy:
1. If real_data_cache.json exists: Load real sampled data from Google Sheets
2. Otherwise: Use synthetic fixture data (small but comprehensive)

To populate real data cache:
    python tests/load_real_data.py
"""

import pytest
import sys
import json
from pathlib import Path

# Add scripts/ to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Import from modular components
from models import ProviderRow, NewOrderRow
from helpers import status_to_color, normalize_name, normalize_address, normalize_phone


# =============================================================================
# DATA LOADING - Real or Synthetic
# =============================================================================

def load_cached_real_data():
    """Load real data from cache if available, otherwise return None"""
    cache_path = Path(__file__).parent / "fixtures" / "real_data_cache.json"

    if not cache_path.exists():
        return None, None

    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)

        # Reconstruct ProviderRow and NewOrderRow objects
        wl_rows = []
        for row_dict in cache_data['wl_rows']:
            row = ProviderRow(**row_dict)
            wl_rows.append(row)

        no_rows = []
        for row_dict in cache_data['no_rows']:
            row = NewOrderRow(**row_dict)
            no_rows.append(row)

        print(f"\n✅ Using REAL data cache: {len(wl_rows)} WL rows, {len(no_rows)} NO rows")
        print(f"   Generated: {cache_data.get('generated_at', 'unknown')}")

        return wl_rows, no_rows

    except Exception as e:
        print(f"\n⚠️  Failed to load cache: {e}")
        return None, None


def get_synthetic_wl_rows():
    """Synthetic Working List rows for testing when no real data cache"""
    return [
        # Yellow - Successful order (exact match expected)
        ProviderRow(
            row_num=45,
            practice="Women's Health Specialists",
            phone="555-123-4567",
            address="123 Main St Suite 200",
            city="Austin",
            state="TX",
            zip="78701",
            qty_2023="50",
            qty_2024="50",
            qty_2025="50",
            status="Successful Order",
            notes="ordered 2025",
            bg_color="#ffff00"
        ),

        # Yellow - with name variation (fuzzy match needed)
        ProviderRow(
            row_num=67,
            practice="Austin Women's Healthcare Center",
            phone="555-234-5678",
            address="456 Oak Ave",
            city="Austin",
            state="TX",
            zip="78702",
            qty_2023="",
            qty_2024="",
            qty_2025="25",
            status="Successful Order",
            notes="",
            bg_color="#ffff00"
        ),

        # Duplicate - exact match (same phone, name, address)
        ProviderRow(
            row_num=100,
            practice="Central Texas OBGYN",
            phone="555-345-6789",
            address="789 Elm St",
            city="Austin",
            state="TX",
            zip="78703",
            qty_2023="",
            qty_2024="50",
            qty_2025="",
            status="",
            notes="",
            bg_color="#ffffff"
        ),
        ProviderRow(
            row_num=101,
            practice="Central Texas OBGYN",
            phone="555-345-6789",
            address="789 Elm St",
            city="Austin",
            state="TX",
            zip="78703",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="",
            notes="",
            bg_color="#ffffff"
        ),

        # Network - same phone, different locations
        ProviderRow(
            row_num=150,
            practice="Women's Health Network - North",
            phone="555-456-7890",
            address="1000 North Lamar",
            city="Austin",
            state="TX",
            zip="78753",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="",
            notes="",
            bg_color="#ffffff"
        ),
        ProviderRow(
            row_num=151,
            practice="Women's Health Network - South",
            phone="555-456-7890",
            address="2000 South Congress",
            city="Austin",
            state="TX",
            zip="78704",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="",
            notes="",
            bg_color="#ffffff"
        ),
        ProviderRow(
            row_num=152,
            practice="Women's Health Network - Downtown",
            phone="555-456-7890",
            address="300 West 6th St",
            city="Austin",
            state="TX",
            zip="78701",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="",
            notes="",
            bg_color="#ffffff"
        ),

        # Fuschia - Voicemail
        ProviderRow(
            row_num=200,
            practice="Hill Country Women's Center",
            phone="555-567-8901",
            address="400 Main St",
            city="Fredericksburg",
            state="TX",
            zip="78624",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="Voicemail/No Answer",
            notes="vm x2",
            bg_color="#ff00ff"
        ),

        # Green - Email sent
        ProviderRow(
            row_num=250,
            practice="Lakeway Women's Health",
            phone="555-678-9012",
            address="500 Medical Pkwy",
            city="Lakeway",
            state="TX",
            zip="78734",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="Requested Email",
            notes=":sent",
            bg_color="#00ff00"
        ),

        # Red - Invalid
        ProviderRow(
            row_num=300,
            practice="Closed Practice",
            phone="555-789-0123",
            address="600 Old Ave",
            city="Austin",
            state="TX",
            zip="78705",
            qty_2023="",
            qty_2024="",
            qty_2025="",
            status="Potentially Invalid",
            notes="disconnected number",
            bg_color="#ff0000"
        ),

        # White - Not interested
        ProviderRow(
            row_num=350,
            practice="Smith OB/GYN",
            phone="555-890-1234",
            address="700 Park Rd",
            city="Austin",
            state="TX",
            zip="78706",
            qty_2023="",
            qty_2024="50",
            qty_2025="0",
            status="Not interested",
            notes="not interested; too busy",
            bg_color="#ffffff"
        ),
    ]


def get_synthetic_no_rows():
    """Synthetic New Orders rows for testing when no real data cache"""
    return [
        # Exact match to WL row 45
        NewOrderRow(
            row_num=10,
            practice="Women's Health Specialists",
            address="123 Main St Suite 200",
            city="Austin",
            state="TX",
            zip="78701",
            qty_2025="50"
        ),

        # Fuzzy match to WL row 67 (name variation)
        NewOrderRow(
            row_num=20,
            practice="Austin Women's Healthcare",  # Missing "Center"
            address="456 Oak Avenue",  # Avenue vs Ave
            city="Austin",
            state="TX",
            zip="78702",
            qty_2025="25"
        ),

        # Orphan - no yellow WL match
        NewOrderRow(
            row_num=93,
            practice="Union OB/GYN and Infertility Group",
            address="1000 Research Blvd",
            city="Austin",
            state="TX",
            zip="78759",
            qty_2025="100"
        ),
    ]


# =============================================================================
# MAIN DATA FIXTURES - Real or Synthetic
# =============================================================================

@pytest.fixture
def sample_wl_rows():
    """
    Working List rows for testing

    Uses real cached data if available (from python tests/load_real_data.py),
    otherwise falls back to synthetic data
    """
    cached_wl, cached_no = load_cached_real_data()

    if cached_wl is not None:
        return cached_wl

    print("\n⚠️  Using synthetic data - run 'python tests/load_real_data.py' for real data")
    return get_synthetic_wl_rows()


@pytest.fixture
def sample_no_rows():
    """
    New Orders rows for testing

    Uses real cached data if available (from python tests/load_real_data.py),
    otherwise falls back to synthetic data
    """
    cached_wl, cached_no = load_cached_real_data()

    if cached_no is not None:
        return cached_no

    return get_synthetic_no_rows()


# =============================================================================
# STATUS EDGE CASES
# =============================================================================

@pytest.fixture
def status_edge_cases():
    """Edge cases for status-to-color mapping"""
    return [
        # Standard cases
        ("Successful Order", "#ffff00"),
        ("successful order", "#ffff00"),  # lowercase
        ("SUCCESSFUL ORDER", "#ffff00"),  # uppercase

        # Voicemail variations
        ("Voicemail/No Answer", "#ff00ff"),
        ("voicemail/no answer", "#ff00ff"),

        # Not interested
        ("Not interested", "#ffffff"),
        ("Not Interested", "#ffffff"),
        ("not interested", "#ffffff"),

        # Email variations
        ("Requested Email", "#00ff00"),
        ("requested email", "#00ff00"),
        ("Email", "#00ff00"),

        # Invalid variations
        ("Potentially Invalid", "#ff0000"),
        ("potentially invalid", "#ff0000"),

        # Edge cases
        ("", "#ffffff"),  # empty
        (None, "#ffffff"),  # None (should handle gracefully)

        # WITH NOTES APPENDED (should NOT match - exact match only)
        ("Successful Order - paid", "#ffffff"),  # Not exact match
        ("Voicemail left x3", "#ffffff"),  # Not exact match
        ("Not interested - closed", "#ffffff"),  # Not exact match
    ]


# =============================================================================
# FUZZY MATCHING TEST CASES
# =============================================================================

@pytest.fixture
def fuzzy_match_cases():
    """Known match cases for fuzzy matching validation"""
    return [
        # (wl_practice, wl_addr, no_practice, no_addr, expected_confidence, category)

        # Exact matches (>= 95%)
        ("Women's Health Center", "123 Main St",
         "Women's Health Center", "123 Main St",
         1.0, "exact"),

        # Good matches (80-94%)
        ("Austin Women's Healthcare Center", "456 Oak Ave",
         "Austin Women's Healthcare", "456 Oak Avenue",
         0.90, "good"),  # Name missing "Center", addr "Avenue" vs "Ave"

        ("Smith Family Practice", "789 Elm Street Suite 100",
         "Family Practice Smith", "789 Elm St Ste 100",
         0.85, "good"),  # Word order different, abbreviations

        # Poor matches (<80%)
        ("Women's Health Specialists", "123 Main St",
         "Hill Country Women's Center", "456 Oak Ave",
         0.45, "poor"),  # Different names and addresses

        # Edge cases
        ("", "123 Main St",
         "Women's Health", "123 Main St",
         0.30, "poor"),  # Empty name

        ("Women's Health", "",
         "Women's Health", "123 Main St",
         0.70, "poor"),  # Empty address in WL
    ]


# =============================================================================
# NETWORK DETECTION TEST CASES
# =============================================================================

@pytest.fixture
def network_test_cases():
    """Test cases for network detection and notation"""
    return [
        {
            'rows': [
                {'practice': 'Women\'s Health Network - North', 'phone': '5551234567', 'address': '1000 N Lamar'},
                {'practice': 'Women\'s Health Network - South', 'phone': '5551234567', 'address': '2000 S Congress'},
                {'practice': 'Women\'s Health Network - Central', 'phone': '5551234567', 'address': '300 W 6th St'},
            ],
            'expected_network_name': 'womenshealthnetwork',
            'expected_notation': 'womenshealthnetwork network (~3)',
            'is_network': True
        },
        {
            'rows': [
                {'practice': 'Austin OBGYN Associates', 'phone': '5552345678', 'address': '100 Main St'},
                {'practice': 'Austin OBGYN Associates', 'phone': '5552345678', 'address': '100 Main St'},
            ],
            'expected_network_name': None,
            'expected_notation': None,
            'is_network': False,  # Exact duplicates, not network
            'is_duplicate': True
        },
    ]


# =============================================================================
# UNDO/REDO TEST FIXTURES
# =============================================================================

@pytest.fixture
def undo_test_state():
    """Sample state for undo/redo testing"""
    return {
        'before': {
            'row_num': 45,
            'practice': 'Women\'s Health Specialists',
            'status': 'Successful Order',
            'notes': 'ordered 2025',
            'qty_2025': '50'
        },
        'after_edit': {
            'row_num': 45,
            'practice': 'Women\'s Health Specialists',
            'status': 'Not interested',
            'notes': 'ordered 2025; not interested',
            'qty_2025': '0'
        }
    }
