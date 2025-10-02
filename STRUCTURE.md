# JGDC Project Structure

```
JGDC/
├── .git/                      # Git version control
├── .gitignore                 # Excludes CSVs, API keys, NPPES bulk data
│
├── README.md                  # Main project documentation
├── TODO.md                    # Master task list
├── STRUCTURE.md               # This file
│
├── scripts/                   # Google Apps Script code
│   ├── provider-search/       # For Provider Search/Verification sheet
│   │   ├── README.md
│   │   ├── UniversalProviderSuite.js   # Main verification logic
│   │   ├── QuickStartWizard.html       # Setup wizard UI
│   │   ├── VerificationSidebar.html    # Manual verification UI
│   │   ├── Code.js                     # (clasp-generated)
│   │   ├── appsscript.json             # Apps Script manifest
│   │   └── .clasp.json                 # (created when you run clasp clone)
│   │
│   └── pcp-list/              # For Working List sheets (year-over-year tracking)
│       ├── README.md
│       ├── ToolboxSuite.js             # Main utilities
│       └── .clasp.json                 # (created when you run clasp clone)
│
├── data/                      # All data files (gitignored)
│   ├── exports/               # CSV exports from Google Sheets
│   │   ├── PCP List 2025 - Use This List! - Working List 2025.csv
│   │   ├── PCP List 2025 - Use This List! - STATS.tsv
│   │   └── NPPES Provider Search - All_Verified_Providers.csv
│   │
│   └── nppes/                 # NPPES bulk data
│       ├── README.md
│       └── PCP Hunt/
│           └── NPPES_Data_Dissemination_September_2025_V2/
│               ├── nppes_filter_pcps.py              # v3.0 Filter script ⭐
│               ├── npidata_pfile_*.csv               # Raw NPPES data (HUGE)
│               ├── FILTERED_pcps_TX_20250927.csv    # Filtered outputs
│               ├── FILTERED_pcps_TN_20250929.csv
│               ├── FILTERED_pcps_OK_20250929.csv
│               └── FILTERED_pcps_OR_20250929.csv
│
└── docs/                      # Documentation
    └── CLASP_SETUP.md         # How to link Apps Script with Git
```

---

## Quick Start

### 1. Set up Google Apps Script sync (clasp)

```bash
# Install clasp
npm install -g @google/clasp

# Login
clasp login

# Setup Provider Search script
cd scripts/provider-search
clasp clone <PROVIDER_SEARCH_SCRIPT_ID>

# Setup PCP List script
cd ../pcp-list
clasp clone <PCP_LIST_SCRIPT_ID>
```

### 2. Run NPPES filter

```bash
cd data/nppes/PCP\ Hunt/NPPES_Data_Dissemination_September_2025_V2
python3 nppes_filter_pcps.py
```

### 3. Import to Google Sheets

Manually import the filtered CSVs to your Google Sheets.

---

## File Locations Quick Reference

| What you need | Where it is |
|--------------|-------------|
| Provider verification script | `scripts/provider-search/UniversalProviderSuite.js` |
| Working List utilities | `scripts/pcp-list/ToolboxSuite.js` |
| NPPES filter script | `data/nppes/PCP Hunt/.../nppes_filter_pcps.py` |
| Filtered provider CSVs | `data/nppes/PCP Hunt/.../FILTERED_pcps_*.csv` |
| Exported working lists | `data/exports/*.csv` |
| Setup guides | `docs/` and `scripts/*/README.md` |

---

## Which Script for Which Sheet?

### Provider Search Sheet
- **Scripts:** `scripts/provider-search/`
- **Purpose:** API-based verification of providers
- **Outputs:** `nppes_verified`, `nppes_errors`, `nppes_formatted`

### Working List Sheets (e.g., "Working List 2025")
- **Scripts:** `scripts/pcp-list/`
- **Purpose:** Outreach tracking, consolidation, utilities
- **Features:** Color coding, search links, capitalization fix

---

## Git Workflow

```bash
# Make changes to scripts locally
cd scripts/pcp-list
# Edit ToolboxSuite.js

# Test in Google Sheets
clasp push

# Once working, commit to git
git add ToolboxSuite.js
git commit -m "Add validation function"

# Push stays in Google Sheets (no separate push needed)
```

---

## Notes

- All `.csv` files are gitignored (too large)
- `.clasp.json` files are gitignored (contain project IDs)
- Python script is tracked in git
- Documentation and code are tracked in git
