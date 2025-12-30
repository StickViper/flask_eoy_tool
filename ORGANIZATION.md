# EOY Cleanup Tool - Code Organization

**Last Updated:** 2025-12-12
**Maintainer Alert:** If this file's structure doesn't match the actual codebase, update this document.

---

## Directory Structure

```
flask_eoy_tool/
├── scripts/
│   ├── eoy_tool.py          # Main entry point, Flask app init (~150 lines)
│   ├── models.py            # Data models (ProviderRow, NewOrderRow, etc.)
│   ├── state.py             # AppState class and global state instance
│   ├── helpers.py           # Utility functions (safe_int, normalizers)
│   ├── loading.py           # Phase 1: Google Sheets data loading
│   ├── validation.py        # Phase 2: Validation pipeline
│   ├── undo_redo.py         # Undo/redo stack management
│   └── routes.py            # All Flask route handlers
│
├── templates/
│   ├── index.html           # Landing/load page
│   └── category.html        # Category review page
│
├── static/
│   ├── css/
│   │   └── main.css         # "Data Atelier" design system
│   └── js/
│       ├── category.js      # Category page interactions
│       ├── shortcuts.js     # Keyboard shortcuts
│       ├── selection.js     # Row selection helpers
│       └── undo.js          # Undo/redo UI handlers
│
├── tests/                   # Unit tests (124 tests)
├── docs/                    # Documentation
├── data/                    # Generated data (undo logs, exports)
│
├── ORGANIZATION.md          # THIS FILE - structure documentation
├── TODO.md                  # Current tasks
└── README.md                # Project overview
```

---

## Module Responsibilities

### scripts/eoy_tool.py (Entry Point)
- Flask app initialization
- CLI argument parsing
- Browser auto-open
- Imports and registers routes from routes.py

### scripts/models.py
- `ProviderRow` - Working List row dataclass
- `NewOrderRow` - New Orders row dataclass
- `InvalidRow` - Invalid/Inactive List row dataclass
- `ReviewCategory` - Issue category dataclass

### scripts/state.py
- `AppState` class - session state management
- Global `state` instance
- State serialization (`to_dict()`)

### scripts/helpers.py
- `safe_int()` - Safe integer conversion
- `safe_int_list()` - Safe list conversion
- `normalize_name()` - Practice name normalization
- `normalize_address()` - Address normalization
- `normalize_phone()` - Phone number normalization
- `status_to_color()` - Status text to hex color mapping

### scripts/loading.py
- `load_data()` - Load from Google Sheets
- `validate_stats_color_counts()` - Validate against STATS sheet
- Google Sheets authentication

### scripts/validation.py
- `validate_yellow_to_no()` - Match yellow rows to New Orders
- `validate_no_to_wl()` - Find orphan NO rows
- `detect_duplicates()` - Duplicate and network detection
- `validate_status_issues()` - Status-related validation
- `categorize_issues()` - Create review categories
- `run_validations()` - Main validation pipeline

### scripts/undo_redo.py
- `add_to_undo_stack()` - Add action to undo stack
- `restore_state()` - Restore state for undo/redo
- `save_undo_log()` - Persist undo log to disk
- `save_progress()` - Save session progress
- `calculate_progress()` - Calculate progress stats

### scripts/routes.py
- All `/api/*` endpoints
- Page routes (`/`, `/load`, `/category/<id>`)
- Export functionality

---

## Import Dependencies

```
models.py          → (no dependencies)
helpers.py         → (no dependencies)
state.py           → models
loading.py         → models, helpers, state
validation.py      → models, helpers, state
undo_redo.py       → state, helpers
routes.py          → models, state, helpers, loading, validation, undo_redo
eoy_tool.py        → routes (registers blueprint)
```

---

## Adding New Features

### New Data Field
1. Add to `models.py` dataclass
2. Update `to_dict()` method
3. Update loading in `loading.py`
4. Update relevant routes in `routes.py`

### New Validation Category
1. Add category in `validation.py` `categorize_issues()`
2. Add category handling in `routes.py` if needed
3. Update `category.html` template if special UI needed

### New API Endpoint
1. Add route function in `routes.py`
2. Add undo support in `undo_redo.py` `restore_state()`
3. Add frontend handler in `static/js/category.js`

### New Action Type for Undo
1. Store `before_state` and `after_state` when calling `add_to_undo_stack()`
2. Add case in `restore_state()` for the action type
3. Ensure both undo (restore before) and redo (restore after) work

---

## Testing

Run all tests:
```bash
cd scripts && python -m pytest ../tests/ -v
```

Test specific module:
```bash
python -m pytest ../tests/test_fuzzy_matching.py -v
```

Coverage report:
```bash
python -m pytest ../tests/ --cov=eoy_tool --cov-report=html
```

---

## Version History

- **2025-12-12**: Initial modular organization created
- **Previous**: Single 2600-line eoy_tool.py file
