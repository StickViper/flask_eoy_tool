# EOY Tool Test Suite

**Last Updated:** 2025-12-01

Comprehensive test suite for OBGYN EOY cleanup tool validation logic.

## Quick Start

```bash
# Run tests with synthetic data (fast, no API calls)
cd scripts
python -m pytest ../tests/ -v

# Load real data from Google Sheets (one-time setup)
python tests/load_real_data.py

# Run tests with real data
cd scripts
python -m pytest ../tests/ -v

# Generate coverage report
python -m pytest ../tests/ --cov=eoy_tool --cov-report=html
open htmlcov/index.html
```

## Data Strategy

Tests can run with either **real data** or **synthetic data**:

### Synthetic Data (Default)
- 11 Working List rows, 3 New Orders rows
- Carefully crafted to test all edge cases
- Fast, repeatable, no API calls
- Good for rapid development and CI/CD

### Real Data (Recommended for Validation)
- 100+ sampled Working List rows from actual Google Sheets
- Proportional sampling across all statuses (yellow, fuschia, green, red, white)
- Cached in `tests/fixtures/real_data_cache.json`
- Tests run against actual provider names, addresses, phone numbers
- Validates fuzzy matching weights with real-world data

## Loading Real Data

**Prerequisites:**
- `credentials.json` in project root
- Access to OBGYN List 2025 Google Sheet
- Google Sheets API enabled

**Load data:**
```bash
python tests/load_real_data.py
```

This will:
1. Connect to Google Sheets
2. Load all Working List and New Orders data
3. Sample ~100 rows proportionally by status
4. Save to `tests/fixtures/real_data_cache.json`
5. Tests will automatically use cached data on next run

**Output:**
```
============================================================
Loading Real Data from Google Sheets
============================================================

Loading data from Google Sheets (this may take a moment)...

✅ Loaded 737 Working List rows
✅ Loaded 241 New Orders rows

Sampling 100 WL rows from 737 total...
  Yellow (Successful Order): 304
  Fuschia (Voicemail): 87
  Green (Requested Email): 52
  Red (Potentially Invalid): 15
  White (Not interested/empty): 279
  Other colors: 0
  Sampled 41 yellow rows
  Sampled 12 fuschia rows
  Sampled 7 green rows
  Sampled 2 red rows
  Sampled 38 white rows
Sampled 33 NO rows from 241 total

✅ Cache saved to tests/fixtures/real_data_cache.json
   100 WL rows, 33 NO rows
   Tests can now run without API calls

============================================================
✅ Real data cache created successfully!
============================================================

Now run tests: cd scripts && python -m pytest ../tests/ -v
```

## Test Structure

### Phase 1: Status-to-Color Mapping (38 tests)
- `tests/test_status_to_color.py` - Exact match enforcement
- `tests/test_verification.py` - Meta-tests proving tests catch failures

**Coverage:**
- All 5 status colors (yellow, fuschia, green, red, white)
- Case insensitivity
- Edge cases (empty, None, whitespace)
- No substring matching (exact match only)

### Phase 2: Fuzzy Matching & Duplicates (48 tests)
- `tests/test_fuzzy_matching.py` - 70/30 name/address weighting
- `tests/test_duplicates.py` - Exact, network, fuzzy detection

**Coverage:**
- Normalization (name, address, phone)
- token_set_ratio matching behavior
- Confidence thresholds (≥95%, ≥80%, <80%)
- Exact duplicates: same phone + name + address
- Networks: same phone, ≥85% name similarity, <70% address difference
- Fuzzy duplicates: same phone but neither exact nor network
- Network notation (~# format)

### Phase 3: Categorization & Undo/Redo (38 tests)
- `tests/test_categorization.py` - 12 review categories
- `tests/test_undo_redo.py` - State management

**Coverage:**
- All 12 categories: exact_dupes, networks, fuzzy_dupes, yellow_95, yellow_80,
  yellow_low, orphan_no, green_sent, fuschia_vm, red_invalid, not_interested_invalid, manual_review
- Category population and filtering
- Row number sorting
- Undo stack: 50-action limit, sequential IDs, timestamps
- Redo stack: action movement
- State serialization

## Test Files

```
tests/
├── README.md                    # This file
├── load_real_data.py           # Load real data from Google Sheets
├── conftest.py                 # pytest fixtures (real or synthetic)
├── test_status_to_color.py     # Phase 1 (31 tests)
├── test_verification.py        # Phase 1 meta (7 tests)
├── test_fuzzy_matching.py      # Phase 2 (26 tests)
├── test_duplicates.py          # Phase 2 (22 tests)
├── test_categorization.py      # Phase 3 (16 tests)
├── test_undo_redo.py           # Phase 3 (22 tests)
└── fixtures/
    └── real_data_cache.json    # Real data cache (created by load_real_data.py)
```

## Refreshing Real Data

To update the cache with latest Google Sheets data:

```bash
# Delete old cache
rm tests/fixtures/real_data_cache.json

# Load fresh data
python tests/load_real_data.py

# Run tests
cd scripts && python -m pytest ../tests/ -v
```

## CI/CD Considerations

For continuous integration:
- Use synthetic data (no credentials needed)
- OR commit `real_data_cache.json` to repo for real-data testing
- Cache file is ~200KB, safe to commit

## Troubleshooting

**"Using synthetic data" warning:**
- Normal if you haven't run `load_real_data.py`
- Tests will still pass with synthetic data
- Run `python tests/load_real_data.py` to use real data

**"Failed to load cache" error:**
- Check `tests/fixtures/real_data_cache.json` exists
- Verify JSON is valid (not corrupted)
- Re-run `python tests/load_real_data.py`

**Google Sheets API errors:**
- Verify `credentials.json` in project root
- Check Google Sheets API is enabled
- Confirm access to OBGYN List 2025 sheet
- Check rate limits (60 reads/minute)

## Performance

**Synthetic data:**
- Test runtime: ~0.2 seconds
- No network calls
- Perfect for TDD/rapid iteration

**Real data (cached):**
- Test runtime: ~0.4 seconds (slightly slower due to more data)
- No network calls (uses cache)
- Validates against 100+ real providers

**Loading real data:**
- Runtime: ~30-60 seconds (one-time)
- Hits Google Sheets API
- Creates cache for fast subsequent runs
