# JGDC Project Structure

## Root Directory - Active Documentation

```
JGDC/
├── README.md                           # Main project overview
├── TODO.md                             # Current task tracker (living document)
├── AGENT_PRINCIPLES.md                 # AI agent coding rules (anti-spaghettification)
├── STRUCTURE.md                        # This file (file locations guide)
├── MASTER_SYSTEM_DOCUMENTATION.md      # Complete system reference (includes appendices)
├── OBGYN_CLEANUP_CHECKLIST.md          # EOY operational guide
│
├── data/                               # Data files (gitignored)
│   ├── exports/                        # CSV exports from Google Sheets
│   ├── stats-snapshots/                # STATS sheet snapshots (JSON, dated)
│   └── nppes/                          # NPPES bulk data + filter scripts
│       └── NPPES_Data.../              # 9.1M provider records
│
├── docs/                               # Documentation & guides
│   ├── CLASP_SETUP.md                  # Apps Script CLI setup
│   └── archive/                        # Historical documentation
│       ├── sessions/                   # Session summaries
│       │   ├── SESSION_SUMMARY_20251003.md
│       │   └── OBGYN_FILTERING_SUMMARY_20251003.md
│       └── config-fixes/               # Configuration fix logs
│           ├── CONFIG_AUDIT_REPORT.md
│           └── CONFIG_FIX_TIMELOG.md
│
├── scripts/                            # Google Apps Script code
│   ├── provider-search/                # Verification automation
│   │   ├── UniversalProviderSuite.js   # Main verification engine (v8.0)
│   │   ├── QuickStartWizard.html       # Setup wizard UI
│   │   ├── VerificationSidebar.html    # Manual verification UI
│   │   ├── appsscript.json             # Apps Script manifest
│   │   └── .clasp.json                 # (gitignored - script ID)
│   │
│   ├── obgyn-list/                     # OBGYN Working List automation
│   │   ├── ToolboxSuite.js             # Main utilities (v10.0)
│   │   ├── DebugRepairSidebar.html     # Debug repair UI
│   │   ├── appsscript.json
│   │   ├── .clasp.json                 # (gitignored)
│   │   └── archive/                    # Old/deprecated scripts
│   │       ├── fix_caps_consolidated.js
│   │       ├── addHyperlink.js
│   │       ├── Code.js
│   │       └── status cells.js
│   │
│   ├── pcp-list/                       # PCP Working List automation
│   │   ├── ToolboxSuite.js             # Same as OBGYN version
│   │   ├── DebugRepairSidebar.html
│   │   ├── appsscript.json
│   │   └── .clasp.json                 # (gitignored)
│   │
│   └── nppes-filter/                   # NPPES filtering scripts
│       └── nppes_filter_pcps.py        # Python filter script (v3.0)
│
└── test-data/                          # Test scripts and data
    ├── README.md
    ├── similarity-test.js              # Fuzzy matching tests
    └── ToolboxSuite.test.js            # Unit tests
```

---

## Quick Reference

### Active Scripts
| File | Purpose | Sheet |
|------|---------|-------|
| `scripts/provider-search/UniversalProviderSuite.js` | API verification | Provider Search |
| `scripts/obgyn-list/ToolboxSuite.js` | EOY automation + utilities | OBGYN Working List |
| `scripts/pcp-list/ToolboxSuite.js` | EOY automation + utilities | PCP Working List |
| `scripts/nppes-filter/nppes_filter_pcps.py` | NPPES filtering | Local execution |

### Active Documentation
| File | Purpose | Audience |
|------|---------|----------|
| `README.md` | Project overview | Everyone |
| `TODO.md` | Current tasks | Development |
| `AGENT_PRINCIPLES.md` | AI agent rules | AI Agents |
| `STRUCTURE.md` | File locations | Everyone |
| `MASTER_SYSTEM_DOCUMENTATION.md` | Complete reference + appendices | Operations |
| `OBGYN_CLEANUP_CHECKLIST.md` | EOY procedures | Operations |
| `docs/CLASP_SETUP.md` | Apps Script setup | One-time setup |

### Archived Documentation
| File | Purpose | Date |
|------|---------|------|
| `docs/archive/sessions/SESSION_SUMMARY_20251003.md` | OBGYN campaign setup | Oct 3, 2025 |
| `docs/archive/sessions/OBGYN_FILTERING_SUMMARY_20251003.md` | Filtering results | Oct 3, 2025 |
| `docs/archive/config-fixes/CONFIG_AUDIT_REPORT.md` | Wizard bugs audit | Oct 7, 2025 |
| `docs/archive/config-fixes/CONFIG_FIX_TIMELOG.md` | Wizard redesign log | Oct 7, 2025 |

---

## Git Workflow

```bash
# Make changes to scripts locally
cd scripts/obgyn-list
# Edit ToolboxSuite.js

# Deploy to Google Sheets
clasp push

# Commit to git
git add ToolboxSuite.js
git commit -m "Add feature X"
```

---

## Organization Principles

### Root Directory
- **Active docs only** (6 files: README, TODO, AGENT_PRINCIPLES, STRUCTURE, MASTER_SYSTEM_DOCUMENTATION, OBGYN_CLEANUP_CHECKLIST)
- **No session logs or historical reports** (archived in docs/archive/)
- **No separate appendices** (consolidated into MASTER_SYSTEM_DOCUMENTATION)

### Scripts Folder
- **One folder per script deployment** (maps to Google Apps Script projects)
- **Active files only** (old/deprecated → archive subfolder)
- **Consistent naming** (ToolboxSuite.js, DebugRepairSidebar.html)

### Docs Folder
- **Setup guides** (CLASP_SETUP.md)
- **Archive subfolder** for historical documentation
  - `sessions/` - Session summaries and filtering results
  - `config-fixes/` - Bug fixes and audits

### Data Folder
- **Gitignored** (too large, sensitive)
- **exports/** - CSV exports from Sheets
- **stats-snapshots/** - STATS sheet JSON snapshots (dated)
- **nppes/** - NPPES bulk data (9.1M rows, 3 GB)

---

## Notes

- All `.csv` files are gitignored (too large)
- `.clasp.json` files are gitignored (contain project IDs)
- Python scripts are tracked in git
- Session summaries archived after work complete
- Deprecated scripts moved to `archive/` subfolders
