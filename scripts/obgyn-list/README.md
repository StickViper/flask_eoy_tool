# OBGYN List - Google Apps Script

This folder contains the Apps Script code for the **OBGYN Working List** sheet.

## Setup Complete ✅

**Script ID:** `1-0uMVAXJ5_tJKIxjYPnPNLVO8lvJMCTw5_KI76afPo_e2en66E0imsXI`

**Date Connected:** 2025-10-03

**What was done:**
1. Cloned existing OBGYN script (had old onEdit code)
2. Added ToolboxSuite.js (same as PCP list)
3. Created .claspignore to exclude old files
4. Pushed ToolboxSuite.js to Google Sheets

## Files

- **ToolboxSuite.js** - Main utilities (same as PCP list)
  - Event-driven formatting (onEdit color coding)
  - EOY automation suite (6 validation steps)
  - Search links, capitalization fixes
  - Consolidation functions

- **appsscript.json** - Apps Script manifest

## Old Files (Excluded from Push)

These files are in the local folder but NOT pushed to Google Sheets:
- `Code.js` - Old custom functions (countColoredCells, refreshCalculations)
- `status cells.js` - Old onEdit function (replaced by ToolboxSuite.js)
- `addHyperlink.js` - Old hyperlink utility

**Why excluded:** ToolboxSuite.js provides all this functionality and more.

## Current Functionality

### Event-Driven Color Coding (onEdit)
- **Successful Order** → Yellow
- **Requested Email** → Green
- **Potentially Invalid** → Red
- **Voicemail/No Answer** → Fuschia
- **Not interested** → White (auto-adds note, sets QTY=0)

### EOY Automation Menu
Location: **Misc. Tools → End-of-Year Workflow**

1. **Audit Working List** - Scans all issues
2. **Validate Yellow → New Orders** - Cross-reference check
3. **Enforce Not Interested Rules** - Auto-fix notes + QTY
4. **Detect Duplicates** - Flag by phone/address
5. **Review Status Issues** - Categorize Red/Fuschia/Green/Empty
6. **Run Full EOY Automation** - All steps at once

## Configuration

Default settings in ToolboxSuite.js:
- `targetSheetName` = 'Working List 2025'
- `statusColumn` = 10 (Column J)
- `qtyColumn` = 9 (Column I)
- `notesColumn` = 11 (Column K)

**If your sheet has different columns:** Update these in the code.

## Using clasp

### Pull changes from Google Sheets
```bash
cd scripts/obgyn-list
clasp pull
```

### Push local changes to Google Sheets
```bash
cd scripts/obgyn-list
clasp push
```

### Open Apps Script editor in browser
```bash
clasp open
```

## Next Steps

1. **Verify Menu Appears**
   - Open OBGYN Working List sheet
   - Refresh page (Ctrl+R)
   - Check for "Misc. Tools" menu

2. **Test onEdit Color Coding**
   - Type "Successful Order" in Call Status column
   - Row should turn yellow

3. **Run First Audit**
   - Misc. Tools → End-of-Year Workflow → Audit Working List
   - Review issue counts
   - Check Debug/Issues column

## Troubleshooting

### Menu doesn't appear
- Refresh page and wait 30 seconds
- Check Apps Script editor for errors
- Verify ToolboxSuite.js was pushed successfully

### Colors not working
- Check Call Status is in column J
- If not, update `statusColumn` in ToolboxSuite.js
- Make sure you're editing "Working List 2025" sheet

### Functions running slow
- Normal for 500+ rows
- Each validation may take 2-5 minutes
- Don't interrupt mid-process

---

**Last Updated:** 2025-10-03
**Status:** Connected and ready for use
