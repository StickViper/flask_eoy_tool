#!/usr/bin/env python3
"""
NPPES PCP Filter Script v3.0 - Enhanced Edition
Filters NPPES data for Primary Care Physicians suitable for genetic screening outreach.

NEW IN v3.0:
- Tightened taxonomy codes (adult family care only)
- Independent clinic support with strict filtering
- Capitalization fixes (5 types: all-caps, Mc/Mac, apostrophes, hyphens, periods)
- Deduplication (prefer individual providers over clinics)
- Name pattern filtering (toggleable, risk-rated)
- Dry-run preview mode
- Excluded providers audit trail

This script follows the vibe-coding style of the Google Apps Scripts,
with clear configuration sections and comprehensive filtering.
"""

import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# vv---------------------------------------------------------------------------------vv
# TODO: USER - Configuration - UPDATE THESE VALUES
CONFIG = {
    # ═══════════════════════════════════════════════════════════════════════════════
    # CORE SETTINGS
    # ═══════════════════════════════════════════════════════════════════════════════

    # Provider Type Selection
    'PROVIDER_TYPE': 'PCP',  # Options: 'PCP', 'OBGYN', 'BOTH'

    # State Filter (use 2-letter state codes)
    'TARGET_STATES': ['FL'],  # Florida campaign

    # State-specific sampling limits (smart sampling for API efficiency)
    # Goal: 150-200 verified FL PCPs (target 175)
    # Based on actual 25% verification success rate (not 70% guess!)
    'STATE_SAMPLE_LIMITS': {
        'FL': 700,   # Target 175 verified (25% success rate)
    },

    # Input/Output Files
    'INPUT_FILE': '../../data/nppes/NPPES_Data_Dissemination_September_2025_V2/npidata_pfile_20050523-20250907.csv',
    'OUTPUT_PREFIX': 'FILTERED_pcps',  # Will create: FILTERED_pcps_FL.csv, etc.

    # Dry Run Mode - Set True to preview what would be filtered WITHOUT actually filtering
    'DRY_RUN': False,  # When True: generates preview stats, no output files created

    # ═══════════════════════════════════════════════════════════════════════════════
    # TAXONOMY CODES - TIGHTENED FOR ADULT FAMILY PRIMARY CARE
    # ═══════════════════════════════════════════════════════════════════════════════

    # PCP Taxonomy Codes - STRICT WHITELIST (v3.0)
    # Removed: Generic NP, Adult Health NP, Pediatrics, Clinic codes
    'PCP_TAXONOMIES': [
        '207Q00000X',  # Family Medicine (physicians)
        '208D00000X',  # General Practice (physicians)
        '207R00000X',  # Internal Medicine (adult-focused physicians)
        '363LF0000X',  # Family Nurse Practitioner (FNP only)
    ],

    # OBGYN Taxonomy Codes
    'OBGYN_TAXONOMIES': [
        '207V00000X',  # Obstetrics & Gynecology
        '207VX0000X',  # Obstetrics
        '207VG0400X',  # Gynecology
        '207VX0201X',  # Maternal & Fetal Medicine
    ],

    # ═══════════════════════════════════════════════════════════════════════════════
    # ORGANIZATION HANDLING - INDEPENDENT CLINICS ONLY
    # ═══════════════════════════════════════════════════════════════════════════════

    'ORGANIZATION_HANDLING': {
        'INCLUDE_ORGANIZATIONS': True,  # Allow Entity Type 2 (organizations)

        # Strict clinic validation - org name MUST contain one of these
        'CLINIC_INDICATORS': [
            'family practice', 'family medicine', 'family health',
            'internal medicine', 'primary care', 'general practice',
            'medical associates', 'physicians group', 'medical group',
            'family physicians', 'family doctors'
        ],

        # Exclude large institutions/specialists (HIGH PRIORITY)
        'EXCLUDE_ORG_PATTERNS': [
            # Institutions
            'hospital', 'medical center', 'health system', 'healthcare system',
            'emergency', 'urgent care', 'walk-in', 'minute clinic',

            # Specialty services
            'cardiology', 'oncology', 'dermatology', 'orthopedic', 'neurology',
            'pediatric', 'pediatrics', 'children', "children's", 'kids health',
            'surgery center', 'surgical', 'specialty',

            # Non-outpatient
            'inpatient', 'hospitalist', 'icu', 'nicu',

            # Government/academic
            'va clinic', 'veterans', 'military', 'student health',
            'university health', 'college health', 'correctional',
        ],

        # Deduplication: When same address has individual + org, keep individual
        'DEDUPE_STRATEGY': 'prefer_individual',  # Options: 'prefer_individual', 'prefer_clinic'
    },

    # ═══════════════════════════════════════════════════════════════════════════════
    # NAME PATTERN FILTERING - TOGGLEABLE (For individual providers)
    # ═══════════════════════════════════════════════════════════════════════════════

    'NAME_PATTERN_FILTER': {
        'ENABLED': False,  # Set True to enable name-based filtering
        'RISK_THRESHOLD': 'HIGH',  # Options: 'HIGH', 'MEDIUM', 'LOW'

        'HIGH_RISK_PATTERNS': [
            'hospital', 'medical center', 'emergency', 'urgent care',
            'pediatric', 'children', "children's", 'student health',
            'cardiology', 'oncology', 'surgery', 'surgical',
        ],

        'MEDIUM_RISK_PATTERNS': [
            'health system', 'clinic network', 'specialty',
            'women\'s health', 'pain management', 'sports medicine',
        ],

        'LOW_RISK_PATTERNS': [
            'wellness center', 'diagnostic center', 'imaging',
        ],
    },

    # ═══════════════════════════════════════════════════════════════════════════════
    # CAPITALIZATION & FORMATTING
    # ═══════════════════════════════════════════════════════════════════════════════

    'FIX_CAPITALIZATION': True,  # Fix 5 types: ALL CAPS, Mc/Mac, apostrophes, hyphens, periods

    'PROTECTED_CREDENTIALS': [
        'MD', 'DO', 'PA', 'NP', 'RN', 'FNP', 'DNP', 'CRNP', 'ARNP', 'APRN',
        'MSN', 'PMHNP', 'WHNP', 'ANP', 'GNP', 'CRNA', 'CFNP', 'CWOCN',
        'LLC', 'PC', 'PLLC', 'INC', 'DDS', 'DPM', 'PHD', 'MS', 'MHS',
        'II', 'III', 'IV', 'Jr', 'Sr', 'JR', 'SR'
    ],

    # ═══════════════════════════════════════════════════════════════════════════════
    # BASIC FILTERS
    # ═══════════════════════════════════════════════════════════════════════════════

    # Deactivation Status to EXCLUDE
    'EXCLUDE_DEACTIVATED': True,
    
    # Business Practice Location Address Fields
    'ADDRESS_FIELDS': {
        'address': 'Provider First Line Business Practice Location Address',
        'address2': 'Provider Second Line Business Practice Location Address', 
        'city': 'Provider Business Practice Location Address City Name',
        'state': 'Provider Business Practice Location Address State Name',
        'zip': 'Provider Business Practice Location Address Postal Code',
        'phone': 'Provider Business Practice Location Address Telephone Number',
    },
    
    # Provider Name Fields
    'NAME_FIELDS': {
        'org_name': 'Provider Organization Name (Legal Business Name)',
        'first_name': 'Provider First Name',
        'last_name': 'Provider Last Name (Legal Name)',
        'middle_name': 'Provider Middle Name',
        'credential': 'Provider Credential Text',
    },
    
    # Maximum rows to process (set to None for all rows)
    'MAX_ROWS': None,  # Use 1000 for testing, None for production
    
    # Chunk size for processing large files
    'CHUNK_SIZE': 10000,
}
# ^^---------------------------------------------------------------------------------^^

def fix_capitalization(name):
    """
    Fix name capitalization AND standardize periods (5 issue types + ProperCase damage).
    Handles: ALL CAPS, lowercase credentials (from ProperCase), Mc/Mac names, apostrophes, hyphens, periods
    """
    if not name or pd.isna(name):
        return name

    name = str(name).strip()

    # Step 1: Fix credential periods (both uppercase AND lowercase from ProperCase damage)
    # "M.D." → "MD", "m.d." → "MD", "F.N.P." → "FNP", "f.n.p." → "FNP"

    # Uppercase credentials with periods
    name = re.sub(r'\b([A-Z])\.([A-Z])\.([A-Z])\.([A-Z])\b', r'\1\2\3\4', name)  # 4-letter: A.R.N.P → ARNP
    name = re.sub(r'\b([A-Z])\.([A-Z])\.([A-Z])\b', r'\1\2\3', name)  # 3-letter: F.N.P → FNP
    name = re.sub(r'\b([A-Z])\.([A-Z])\b', r'\1\2', name)  # 2-letter: M.D → MD

    # Lowercase credentials with periods (from ProperCase damage) - uppercase them!
    name = re.sub(r'\b([a-z])\.([a-z])\.([a-z])\.([a-z])\b',
                  lambda m: m.group(1).upper() + m.group(2).upper() + m.group(3).upper() + m.group(4).upper(),
                  name)
    name = re.sub(r'\b([a-z])\.([a-z])\.([a-z])\b',
                  lambda m: m.group(1).upper() + m.group(2).upper() + m.group(3).upper(),
                  name)
    name = re.sub(r'\b([a-z])\.([a-z])\b',
                  lambda m: m.group(1).upper() + m.group(2).upper(),
                  name)

    # Step 2: Standardize middle initial periods
    # "Robert L Cossman" → "Robert L. Cossman"
    name = re.sub(r'\b([A-Z])\s+(?=[A-Z][a-z])', r'\1. ', name)

    words = name.split()
    fixed = []

    for word in words:
        clean_word = word.rstrip('.,')
        trailing_punctuation = word[len(clean_word):]

        # Force credentials to uppercase (catches "md", "Md", "MD", etc.)
        if clean_word.upper() in CONFIG['PROTECTED_CREDENTIALS']:
            fixed.append(clean_word.upper() + trailing_punctuation)
        # Handle single initials with period
        elif re.match(r'^[A-Z]\.$', word):
            fixed.append(word.upper())
        # Handle Mc names (McDonald, McIntosh, Mcintosh → McIntosh)
        elif clean_word.lower().startswith('mc') and len(clean_word) > 2:
            formatted = 'Mc' + clean_word[2:].capitalize()
            fixed.append(formatted + trailing_punctuation)
        # Handle Mac names (MacDonald, Macdonald → MacDonald)
        elif clean_word.lower().startswith('mac') and len(clean_word) > 3:
            formatted = 'Mac' + clean_word[3:].capitalize()
            fixed.append(formatted + trailing_punctuation)
        # Handle hyphens (Mary-Anne, mary-anne → Mary-Anne)
        elif '-' in clean_word:
            formatted = '-'.join(p.capitalize() for p in clean_word.split('-'))
            fixed.append(formatted + trailing_punctuation)
        # Handle apostrophes (O'Donnell, o'donnell → O'Donnell)
        elif "'" in clean_word:
            parts = clean_word.split("'")
            formatted = parts[0].capitalize() + "'" + parts[1].capitalize()
            fixed.append(formatted + trailing_punctuation)
        else:
            formatted = clean_word.capitalize()
            fixed.append(formatted + trailing_punctuation)

    return ' '.join(fixed)


def check_name_patterns(name, entity_type):
    """
    Check if provider name matches risky patterns.
    Returns: (should_exclude, reason)
    """
    if not CONFIG['NAME_PATTERN_FILTER']['ENABLED']:
        return False, None

    if pd.isna(name):
        return False, None

    name_lower = str(name).lower()
    threshold = CONFIG['NAME_PATTERN_FILTER']['RISK_THRESHOLD']

    # Check high-risk patterns
    for pattern in CONFIG['NAME_PATTERN_FILTER']['HIGH_RISK_PATTERNS']:
        if pattern.lower() in name_lower:
            return True, f"HIGH_RISK: Contains '{pattern}'"

    # Check medium-risk if threshold allows
    if threshold in ['MEDIUM', 'LOW']:
        for pattern in CONFIG['NAME_PATTERN_FILTER']['MEDIUM_RISK_PATTERNS']:
            if pattern.lower() in name_lower:
                return True, f"MEDIUM_RISK: Contains '{pattern}'"

    # Check low-risk if threshold allows
    if threshold == 'LOW':
        for pattern in CONFIG['NAME_PATTERN_FILTER']['LOW_RISK_PATTERNS']:
            if pattern.lower() in name_lower:
                return True, f"LOW_RISK: Contains '{pattern}'"

    return False, None


def validate_organization(org_name):
    """
    Validate if organization is an independent clinic suitable for outreach.
    Returns: (is_valid, reason)
    """
    if pd.isna(org_name) or not org_name:
        return False, "No organization name"

    org_lower = str(org_name).lower()

    # First check exclusion patterns (high priority)
    for pattern in CONFIG['ORGANIZATION_HANDLING']['EXCLUDE_ORG_PATTERNS']:
        if pattern.lower() in org_lower:
            return False, f"Excluded pattern: '{pattern}'"

    # Then check if it has clinic indicators (strict requirement)
    for indicator in CONFIG['ORGANIZATION_HANDLING']['CLINIC_INDICATORS']:
        if indicator.lower() in org_lower:
            return True, f"Valid clinic: '{indicator}'"

    return False, "No clinic indicators found"


def load_nppes_chunk(file_path, chunk_size=10000, max_rows=None):
    """
    Load NPPES data in chunks to handle large files efficiently.
    """
    print(f"[*] Loading NPPES data from: {file_path}")
    
    # Define columns we need to keep memory usage low
    needed_columns = [
        'NPI',
        'Entity Type Code',
        'Provider Organization Name (Legal Business Name)',
        'Provider Last Name (Legal Name)',
        'Provider First Name',
        'Provider Middle Name',
        'Provider Credential Text',
        'Provider First Line Business Practice Location Address',
        'Provider Second Line Business Practice Location Address',
        'Provider Business Practice Location Address City Name',
        'Provider Business Practice Location Address State Name',
        'Provider Business Practice Location Address Postal Code',
        'Provider Business Practice Location Address Telephone Number',
        'Healthcare Provider Taxonomy Code_1',
        'Healthcare Provider Taxonomy Code_2',
        'Healthcare Provider Taxonomy Code_3',
        'NPI Deactivation Date',
        'Is Sole Proprietor',
    ]
    
    # Read in chunks
    chunks = []
    total_rows = 0
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, 
                             usecols=lambda x: x in needed_columns,
                             low_memory=False,
                             dtype=str):
        chunks.append(chunk)
        total_rows += len(chunk)
        print(f"  [+] Loaded {total_rows:,} rows...", end='\r')

        if max_rows and total_rows >= max_rows:
            break

    print(f"\n[OK] Loaded {total_rows:,} total rows")
    return pd.concat(chunks, ignore_index=True)

def filter_providers(df, provider_type='PCP', states=None):
    """
    Filter providers based on type, location, and organization rules.
    Enhanced in v3.0 with organization handling and name pattern filtering.
    """
    print(f"\n[FILTER] Filtering for {provider_type} providers...")
    initial_count = len(df)
    excluded_records = []  # Track what we exclude for audit trail

    # Step 1: Exclude deactivated NPIs
    if CONFIG['EXCLUDE_DEACTIVATED']:
        deactivated = df[df['NPI Deactivation Date'].notna()]
        excluded_records.extend([
            {'NPI': row['NPI'], 'Name': _get_name(row), 'Reason': 'Deactivated NPI'}
            for _, row in deactivated.iterrows()
        ])
        df = df[df['NPI Deactivation Date'].isna()]
        print(f"  [OK] After excluding deactivated: {len(df):,} rows")

    # Step 2: Filter by taxonomy codes (STRICT in v3.0)
    if provider_type == 'PCP':
        taxonomies = CONFIG['PCP_TAXONOMIES']
    elif provider_type == 'OBGYN':
        taxonomies = CONFIG['OBGYN_TAXONOMIES']
    else:  # BOTH
        taxonomies = CONFIG['PCP_TAXONOMIES'] + CONFIG['OBGYN_TAXONOMIES']

    taxonomy_mask = (
        df['Healthcare Provider Taxonomy Code_1'].isin(taxonomies) |
        df['Healthcare Provider Taxonomy Code_2'].isin(taxonomies) |
        df['Healthcare Provider Taxonomy Code_3'].isin(taxonomies)
    )

    non_matching = df[~taxonomy_mask]
    excluded_records.extend([
        {'NPI': row['NPI'], 'Name': _get_name(row), 'Reason': 'Not matching PCP taxonomy'}
        for _, row in non_matching.iterrows()
    ])

    df = df[taxonomy_mask]
    print(f"  [OK] After taxonomy filter (strict): {len(df):,} rows")

    # Step 3: Filter by state
    if states:
        non_state = df[~df['Provider Business Practice Location Address State Name'].isin(states)]
        excluded_records.extend([
            {'NPI': row['NPI'], 'Name': _get_name(row), 'Reason': f"Not in target states"}
            for _, row in non_state.iterrows()
        ])

        df = df[df['Provider Business Practice Location Address State Name'].isin(states)]
        print(f"  [OK] After state filter ({', '.join(states)}): {len(df):,} rows")

    # Step 4: Handle organizations (NEW in v3.0)
    if CONFIG['ORGANIZATION_HANDLING']['INCLUDE_ORGANIZATIONS']:
        print(f"\n  [ORG] Processing organizations with strict clinic validation...")

        # Separate individuals and organizations
        individuals = df[df['Entity Type Code'] == '1'].copy()
        organizations = df[df['Entity Type Code'] == '2'].copy()

        print(f"    - Found {len(individuals):,} individuals")
        print(f"    - Found {len(organizations):,} organizations")

        # Validate organizations
        valid_orgs = []
        for _, row in organizations.iterrows():
            org_name = row['Provider Organization Name (Legal Business Name)']
            is_valid, reason = validate_organization(org_name)

            if is_valid:
                valid_orgs.append(row)
            else:
                excluded_records.append({
                    'NPI': row['NPI'],
                    'Name': org_name,
                    'Reason': f'Organization: {reason}'
                })

        valid_orgs_df = pd.DataFrame(valid_orgs) if valid_orgs else pd.DataFrame()
        print(f"    - Kept {len(valid_orgs_df):,} valid independent clinics")
        print(f"    - Excluded {len(organizations) - len(valid_orgs_df):,} organizations")

        # Combine individuals and valid organizations
        df = pd.concat([individuals, valid_orgs_df], ignore_index=True)
    else:
        # Exclude all organizations (original behavior)
        orgs = df[df['Entity Type Code'] == '2']
        excluded_records.extend([
            {'NPI': row['NPI'], 'Name': _get_name(row), 'Reason': 'Organization (excluded)'}
            for _, row in orgs.iterrows()
        ])
        df = df[df['Entity Type Code'] == '1']
        print(f"  [OK] After excluding all organizations: {len(df):,} rows")

    # Step 5: Name pattern filtering (optional, NEW in v3.0)
    if CONFIG['NAME_PATTERN_FILTER']['ENABLED']:
        print(f"\n  [FILTER] Applying name pattern filter (threshold: {CONFIG['NAME_PATTERN_FILTER']['RISK_THRESHOLD']})...")
        filtered_names = []

        for _, row in df.iterrows():
            name = _get_name(row)
            should_exclude, reason = check_name_patterns(name, row['Entity Type Code'])

            if should_exclude:
                excluded_records.append({
                    'NPI': row['NPI'],
                    'Name': name,
                    'Reason': f'Name pattern: {reason}'
                })
            else:
                filtered_names.append(row)

        excluded_count = len(df) - len(filtered_names)
        df = pd.DataFrame(filtered_names) if filtered_names else pd.DataFrame()
        print(f"    - Excluded {excluded_count:,} providers due to name patterns")

    # Step 6: Remove providers without essential contact info
    missing_phone = df[df['Provider Business Practice Location Address Telephone Number'].isna()]
    missing_address = df[df['Provider First Line Business Practice Location Address'].isna()]

    for _, row in pd.concat([missing_phone, missing_address]).drop_duplicates().iterrows():
        excluded_records.append({
            'NPI': row['NPI'],
            'Name': _get_name(row),
            'Reason': 'Missing phone or address'
        })

    df = df[df['Provider Business Practice Location Address Telephone Number'].notna()]
    df = df[df['Provider First Line Business Practice Location Address'].notna()]
    print(f"  [OK] After requiring phone & address: {len(df):,} rows")

    # Step 7: Deduplicate (prefer individuals over clinics if same location)
    if CONFIG['ORGANIZATION_HANDLING']['INCLUDE_ORGANIZATIONS']:
        print(f"\n  [DEDUPE] Deduplicating (strategy: {CONFIG['ORGANIZATION_HANDLING']['DEDUPE_STRATEGY']})...")
        df, dupes_removed = deduplicate_providers(df)
        excluded_records.extend(dupes_removed)
        print(f"    - Removed {len(dupes_removed):,} duplicate entries")

    print(f"\n[STATS] Final result: {initial_count:,} -> {len(df):,} providers ({len(excluded_records):,} excluded)")

    # Store excluded records for audit trail
    df._excluded_records = excluded_records

    return df


def _get_name(row):
    """Helper to get provider name (org or individual)."""
    if row['Entity Type Code'] == '2':
        return row['Provider Organization Name (Legal Business Name)']
    else:
        parts = [
            row.get('Provider First Name'),
            row.get('Provider Middle Name'),
            row.get('Provider Last Name (Legal Name)'),
            row.get('Provider Credential Text')
        ]
        return ' '.join([str(p) for p in parts if pd.notna(p) and p])


def deduplicate_providers(df):
    """
    Deduplicate providers at same location.
    Strategy: prefer_individual = keep individual doctors, remove clinic NPI
    """
    excluded = []

    # Create location key (phone + address)
    df['_location_key'] = (
        df['Provider Business Practice Location Address Telephone Number'].astype(str) + '|' +
        df['Provider First Line Business Practice Location Address'].astype(str)
    )

    # Group by location
    grouped = df.groupby('_location_key')

    keep_rows = []
    for location, group in grouped:
        if len(group) == 1:
            keep_rows.append(group.iloc[0])
            continue

        # Check if group has both individuals and organizations
        has_individual = (group['Entity Type Code'] == '1').any()
        has_org = (group['Entity Type Code'] == '2').any()

        if has_individual and has_org:
            # Prefer individuals, exclude organizations
            individuals = group[group['Entity Type Code'] == '1']
            organizations = group[group['Entity Type Code'] == '2']

            keep_rows.extend([row for _, row in individuals.iterrows()])

            for _, row in organizations.iterrows():
                excluded.append({
                    'NPI': row['NPI'],
                    'Name': _get_name(row),
                    'Reason': 'Duplicate: individual provider exists at same location'
                })
        else:
            # All same type - keep all (might be group practice with multiple doctors)
            keep_rows.extend([row for _, row in group.iterrows()])

    result_df = pd.DataFrame(keep_rows).drop(columns=['_location_key'])
    return result_df, excluded

def apply_state_sampling(df):
    """
    Apply state-specific sampling limits to optimize API usage.
    Randomly samples providers to meet target verified counts.
    """
    if 'STATE_SAMPLE_LIMITS' not in CONFIG or not CONFIG['STATE_SAMPLE_LIMITS']:
        return df

    print("\n[SAMPLE] Applying state-specific sampling for API efficiency...")

    sampled_dfs = []
    for state, limit in CONFIG['STATE_SAMPLE_LIMITS'].items():
        state_df = df[df['Provider Business Practice Location Address State Name'] == state]

        if len(state_df) > limit:
            # Randomly sample to limit
            state_sampled = state_df.sample(n=limit, random_state=42)
            print(f"  {state}: {len(state_df):,} -> {len(state_sampled):,} providers (sampled)")
            sampled_dfs.append(state_sampled)
        else:
            print(f"  {state}: {len(state_df):,} providers (all included)")
            sampled_dfs.append(state_df)

    result = pd.concat(sampled_dfs, ignore_index=True) if sampled_dfs else pd.DataFrame()
    print(f"  Total after sampling: {len(result):,} providers")
    return result


def format_output(df):
    """
    Format the output to match Google Sheets structure.
    Enhanced in v3.0 with proper capitalization fixes (5 types).
    """
    print("\n[FORMAT] Formatting output data...")

    output_df = pd.DataFrame()

    # Create Office Name with PROPER capitalization fix (v3.0)
    def create_office_name(row):
        if pd.notna(row['Provider Organization Name (Legal Business Name)']):
            name = row['Provider Organization Name (Legal Business Name)']
        else:
            parts = []
            if pd.notna(row['Provider First Name']):
                parts.append(str(row['Provider First Name']))
            if pd.notna(row['Provider Middle Name']):
                parts.append(str(row['Provider Middle Name']))
            if pd.notna(row['Provider Last Name (Legal Name)']):
                parts.append(str(row['Provider Last Name (Legal Name)']))
            if pd.notna(row['Provider Credential Text']):
                parts.append(str(row['Provider Credential Text']))
            name = ' '.join(parts)

        # Apply capitalization fix if enabled
        if CONFIG['FIX_CAPITALIZATION']:
            return fix_capitalization(name)
        else:
            return name

    output_df['Office Name'] = df.apply(create_office_name, axis=1)
    
    # Format phone number (remove extensions, standardize)
    def format_phone(phone):
        if pd.isna(phone):
            return ''
        # Keep only digits
        phone = ''.join(filter(str.isdigit, str(phone)))
        if len(phone) == 10:
            return f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"
        return phone
    
    output_df['Phone Number'] = df['Provider Business Practice Location Address Telephone Number'].apply(format_phone)
    
    # Format address (proper case)
    def format_address(addr):
        if pd.isna(addr):
            return ''
        # Keep suite/apt/unit indicators uppercase
        addr = addr.title()
        addr = addr.replace('Ste ', 'Suite ').replace('Apt ', 'Apt ')
        return addr
    
    output_df['Address'] = df['Provider First Line Business Practice Location Address'].apply(format_address)
    
    # Add address line 2 if present
    def combine_address(row):
        addr1 = format_address(row['Provider First Line Business Practice Location Address'])
        addr2 = row['Provider Second Line Business Practice Location Address']
        if pd.notna(addr2) and addr2.strip():
            return f"{addr1}, {format_address(addr2)}"
        return addr1
    
    output_df['Address'] = df.apply(combine_address, axis=1)
    
    # City (proper case)
    output_df['City'] = df['Provider Business Practice Location Address City Name'].str.title()
    
    # State (uppercase)
    output_df['State'] = df['Provider Business Practice Location Address State Name'].str.upper()
    
    # ZIP (5-digit format)
    output_df['ZIP'] = df['Provider Business Practice Location Address Postal Code'].str[:5]
    
    return output_df

def save_by_state(df, output_prefix):
    """
    Save filtered data by state into separate CSV files.
    """
    print(f"\n[SAVE] Saving filtered data...")

    states = df['State'].unique()
    files_created = []

    for state in states:
        state_df = df[df['State'] == state]
        filename = f"{output_prefix}_{state}_{datetime.now().strftime('%Y%m%d')}.csv"
        state_df.to_csv(filename, index=False)
        files_created.append(filename)
        print(f"  [OK] Saved {len(state_df):,} {state} providers to: {filename}")
    
    # Also save combined file if multiple states
    if len(states) > 1:
        combined_filename = f"{output_prefix}_ALL_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(combined_filename, index=False)
        files_created.append(combined_filename)
        print(f"  [OK] Saved combined file: {combined_filename}")
    
    return files_created

def main():
    """
    Main processing function - Enhanced in v3.0
    """
    print("=" * 80)
    print("NPPES PCP FILTER SCRIPT v3.0 - ENHANCED EDITION")
    print("=" * 80)
    print(f"Provider Type: {CONFIG['PROVIDER_TYPE']}")
    print(f"Target States: {', '.join(CONFIG['TARGET_STATES'])}")
    print(f"Dry Run Mode: {'ENABLED (preview only)' if CONFIG['DRY_RUN'] else 'DISABLED (will save files)'}")
    print(f"Capitalization Fix: {'ENABLED' if CONFIG['FIX_CAPITALIZATION'] else 'DISABLED'}")
    print(f"Name Pattern Filter: {'ENABLED' if CONFIG['NAME_PATTERN_FILTER']['ENABLED'] else 'DISABLED'}")
    print(f"Organizations: {'INCLUDED (strict clinic validation)' if CONFIG['ORGANIZATION_HANDLING']['INCLUDE_ORGANIZATIONS'] else 'EXCLUDED'}")
    print("=" * 80)

    # Check if input file exists
    input_path = Path(CONFIG['INPUT_FILE'])
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {CONFIG['INPUT_FILE']}")
        return

    # Load data
    df = load_nppes_chunk(
        CONFIG['INPUT_FILE'],
        chunk_size=CONFIG['CHUNK_SIZE'],
        max_rows=CONFIG['MAX_ROWS']
    )

    # Filter providers
    filtered_df = filter_providers(
        df,
        provider_type=CONFIG['PROVIDER_TYPE'],
        states=CONFIG['TARGET_STATES']
    )

    # Remove duplicates based on NPI
    initial_count = len(filtered_df)
    unique_filtered_df = filtered_df.drop_duplicates(subset=['NPI'])
    print(f"\n[DEDUPE] After removing NPI duplicates: {len(unique_filtered_df):,} unique providers (removed {initial_count - len(unique_filtered_df):,})")

    # Apply state-specific sampling for API efficiency
    sampled_df = apply_state_sampling(unique_filtered_df)

    # Get excluded records for audit trail
    excluded_records = getattr(filtered_df, '_excluded_records', [])

    # Format output
    output_df = format_output(sampled_df)

    # DRY RUN MODE - Preview only
    if CONFIG['DRY_RUN']:
        print("\n" + "=" * 80)
        print("[DRY-RUN] PREVIEW MODE (No files created)")
        print("=" * 80)
        print(f"\nFinal provider count: {len(output_df):,}")
        print(f"Excluded providers: {len(excluded_records):,}")
        print("\nBreakdown by state:")
        for state in output_df['State'].unique():
            count = len(output_df[output_df['State'] == state])
            print(f"  {state}: {count:,} providers")
        print("\nSample of kept providers (first 10):")
        print(output_df[['Office Name', 'Phone Number', 'City', 'State']].head(10).to_string(index=False))

        if excluded_records:
            print("\n\nSample of excluded providers (first 10):")
            excluded_df = pd.DataFrame(excluded_records).head(10)
            print(excluded_df.to_string(index=False))

        print("\n" + "=" * 80)
        print("[INFO] To save files, set CONFIG['DRY_RUN'] = False")
        print("=" * 80)
        return output_df

    # NORMAL MODE - Save files
    files = save_by_state(output_df, CONFIG['OUTPUT_PREFIX'])

    # Save excluded providers audit trail
    if excluded_records:
        excluded_df = pd.DataFrame(excluded_records)
        excluded_filename = f"EXCLUDED_{CONFIG['OUTPUT_PREFIX']}_{datetime.now().strftime('%Y%m%d')}.csv"
        excluded_df.to_csv(excluded_filename, index=False)
        files.append(excluded_filename)
        print(f"  [OK] Saved excluded providers audit: {excluded_filename}")

    print("\n" + "=" * 80)
    print("[COMPLETE] PROCESSING COMPLETE!")
    print(f"Total providers kept: {len(output_df):,}")
    print(f"Total providers excluded: {len(excluded_records):,}")
    print(f"Files created: {len(files)}")
    print("\nFiles saved:")
    for f in files:
        print(f"  - {f}")
    print("=" * 80)

    return output_df

if __name__ == "__main__":
    result = main()
