# EOY Cleanup Tool - TODO

**Last Updated:** 2025-12-17

## Current Status

The Flask EOY Cleanup Tool is **fully functional** for read operations and UI. The application provides:
- Data loading from Google Sheets
- 11 validation categories with fuzzy matching
- Interactive review UI with inline editing
- Progress tracking and save/export functionality

---

## Remaining Tasks

### Write Phase (Not Yet Implemented)
- [ ] Batch writing changes to Google Sheets (`gspread.batch_update()`)
- [ ] Shadow worksheet creation with `_CLEANUP` suffix
- [ ] Full edit modal for complex multi-field edits

### UI Enhancements
- [ ] Filter view functions (`showDebugFilter()`, `clearDebugFilter()`)
- [ ] Improved duplicate detection (phone format normalization)

### Testing
- [ ] Integration tests for API endpoints
- [ ] End-to-end test with real sheet data

---

## Recently Completed

### 2025-12-17 - Bug Fixes & Security
- [x] Added visual indicators for deleted/merged rows (CSS + badges)
- [x] Fixed XSS vulnerability in JS modals (added escapeHtml)
- [x] Fixed crash on empty practice names in derive_network_name()
- [x] Fixed None value crashes in orphan matching
- [x] Moved deprecated EOY_TOOL_SPEC.md to archive
- [x] Undo/redo fully working with field_edits sync
- [x] All bulk action handlers implemented (6 secondary actions)

### 2025-12-12 - Frontend Cleanup
- [x] Extracted ~1400 lines of inline JS from category.html to external file
- [x] Created `/static/js/category.js` for better maintainability
- [x] Reduced category.html from 1817 to 447 lines

### Previous Sessions
- [x] All 9 PLAN.md priorities completed
- [x] 278 unit tests passing
- [x] Full validation pipeline working
- [x] Interactive UI with selection, sorting, inline editing
- [x] Keyboard shortcuts and context menus

---

## Notes

### Running the Tool
```bash
cd /home/user/flask_eoy_tool
python scripts/eoy_tool.py
# Open http://127.0.0.1:5000
```

### Key Files
- `scripts/eoy_tool.py` - Main Flask application
- `templates/category.html` - Category review page
- `static/js/category.js` - Category page JavaScript
- `static/css/main.css` - "Data Atelier" design system
- `tests/` - Unit test suite (278 tests)
