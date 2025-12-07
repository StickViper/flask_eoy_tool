# JGDC Working List Management System

**Organization:** Jewish Genetic Disease Consortium (Canavan Foundation)
**Purpose:** Tools for managing OBGYN and PCP provider outreach campaigns

---

## Overview

This repository contains tools for managing provider working lists for Canavan disease awareness campaigns. The system helps track outreach to medical practices across the US, managing contact attempts, orders, and data cleanup.

### Current Focus: OBGYN End-of-Year Cleanup Tool

Flask web application for preparing the OBGYN Working List for the next year:
- Validates successful orders against New Orders sheet (fuzzy matching)
- Detects duplicate providers and networks
- Flags status issues (voicemail callbacks, unresolved emails, invalid providers)
- Organizes 737 providers into 12 review categories
- Full editing, undo/redo, merge, and export capabilities

**Status:** ✅ Fully functional - All 9 implementation priorities complete

---

## Quick Start

### Prerequisites
- Python 3.9+
- Google Sheets API credentials (credentials.json)
- Libraries: Flask, gspread, rapidfuzz, oauth2client

### Running the EOY Tool

```bash
# Install dependencies
pip install flask gspread rapidfuzz oauth2client gspread-formatting

# Run the app
cd /path/to/flask_eoy_tool
python scripts/eoy_tool.py

# Open in browser
# http://127.0.0.1:5000
```

### First-Time Setup

1. **Get credentials.json**: Set up Google Sheets API service account (see scripts/tests/archive/test_gspread.py for setup instructions)
2. **Place in root**: `flask_eoy_tool/credentials.json`
3. **Run app**: It will connect to "OBGYN List 2025 - Use This List!" sheet

---

## Repository Structure

```
flask_eoy_tool/
├── scripts/
│   ├── eoy_tool.py              # Main Flask application (~2400 lines)
│   ├── nppes_filter.py          # NPPES database PCP filtering
│   ├── obgyn-list/              # Apps Script code for OBGYN sheet
│   │   ├── ToolboxSuite.js
│   │   └── GetStatsSnapshot.js
│   ├── pcp-list/                # Apps Script code for PCP sheet
│   │   ├── ToolboxSuite.js
│   │   └── GetStatsSnapshot.js
│   ├── tests/                   # Test scripts
│   └── utils/                   # Utility scripts
├── templates/                   # Flask HTML templates
├── static/                      # CSS and JavaScript
├── docs/                        # Documentation
│   ├── README.md                # EOY tool technical docs
│   ├── EOY_TOOL_SPEC.md         # Original spec (deprecated TUI approach)
│   └── GSPREAD_RATE_LIMITS.md   # API quota management
├── data/                        # Data files (gitignored)
├── PLAN.md                      # Implementation roadmap (all 9 priorities complete)
└── credentials.json             # Google API credentials (private repo)
```

---

## Key Features

### EOY Cleanup Tool - Complete Feature Set

| Feature | Description |
|---------|-------------|
| **12 Review Categories** | Systematic organization by issue type and urgency |
| **Fuzzy Matching** | 70% name / 30% address weighting to validate orders |
| **Duplicate Detection** | Exact matches, networks (same phone), fuzzy duplicates |
| **Inline Editing** | Double-click any cell to edit in place |
| **Merge Duplicates** | Side-by-side comparison with field selection |
| **Network Confirmation** | Auto-suggest network names, bulk confirm |
| **Orphan Matching** | Match orphan NO rows against Invalid List |
| **Undo/Redo** | Full action history (Ctrl+Z/Ctrl+Y) |
| **Urgency Progress Bar** | Visual tracking by Critical/Review/Verify |
| **Export** | Copy CSV to clipboard or download file |
| **Manual Review** | Catch-all category with all actions available |

### Review Categories (12 Total)

| Urgency | Categories |
|---------|------------|
| 🔴 **CRITICAL** | exact_dupes, yellow_low, orphan_no, red_invalid |
| 🟡 **REVIEW** | networks, fuzzy_dupes, yellow_80, green_sent, not_interested_invalid |
| 🟢 **VERIFY** | yellow_95, fuschia_vm, manual_review |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+S | Save progress |
| Ctrl+A | Select all rows |
| Double-click | Edit cell inline |
| Right-click | Context menu |

---

## Documentation

**For LLM agents/developers:**
- `SYSTEM_OVERVIEW.md` - Comprehensive system documentation
- `AGENT_PRINCIPLES.md` - AI agent workflow rules
- `PLAN.md` - Implementation roadmap (all priorities complete)

**For EOY tool:**
- `docs/README.md` - Technical documentation, architecture, data models
- `docs/EOY_TOOL_SPEC.md` - Original planning (deprecated TUI approach)

**For Google Sheets scripts:**
- Apps Script code in `scripts/obgyn-list/` and `scripts/pcp-list/`
- Deployed via clasp to Google Sheets

---

## Testing

**Status:** ✅ **Comprehensive test suite** (124 tests, 34% coverage)

**Automated Testing:**
- 124 tests passing across 3 phases (status mapping, fuzzy matching, categorization)
- Run tests: `cd scripts && python -m pytest ../tests/ -v`
- Coverage report: `python -m pytest ../tests/ --cov=eoy_tool --cov-report=html`
- See `tests/README.md` for complete documentation

---

## Current Campaign Status

### OBGYN List 2025
- **737 providers** tracked across all 50 states
- **247 successful orders** (yellow rows) in 2025
- **December 2024 cleanup** complete using Flask EOY tool

### PCP List
- Not yet active (future campaign)
- Infrastructure ready (ToolboxSuite.js deployed)

---

## Contributing

This is a private repository for JGDC internal use.

**Before modifying code:**
1. Read `AGENT_PRINCIPLES.md` for workflow rules
2. Check `PLAN.md` for current status
3. Review recent git commits: `git log --oneline -10`

**When making changes:**
- Update documentation in same commit as code changes
- Run tests: `cd scripts && python -m pytest ../tests/ -v`
- All 124 tests should pass

---

## Contact

**Organization:** Jewish Genetic Disease Consortium (Canavan Foundation)
**Maintained by:** JGDC Team

For questions about this codebase, see `AGENT_PRINCIPLES.md` and `PLAN.md` for current context.
