# PCP List - Google Apps Script

This folder contains the Apps Script code for the **Working List** sheets (year-over-year PCP tracking).

## Files

- **ToolboxSuite.js** - Main utilities for Working List sheets

## Setup with clasp

```bash
cd scripts/pcp-list

# Get your Script ID from PCP List sheet
# (Extensions → Apps Script → Settings → Script ID)

clasp clone <PCP_LIST_SCRIPT_ID>

# This will create .clasp.json with your project ID
# Now you can push changes:
clasp push
```

## What this script does

1. **Event-driven formatting** - Auto-colors rows based on call status
2. **Consolidation** - Year-end data merge across multiple sheets
3. **Search links** - Creates Google search links from office names
4. **Capitalization fix** - Fixes ALL CAPS, Mc/Mac, credentials
5. **Validation** - (TODO) Find data issues

## Menu Items

- **Misc. Tools**
  - 🔗 Create Search Links
  - ✨ Fix Capitalization in Selection
  - 🔍 Validation & Debugging
    - Find Issues in Current Sheet (TODO)
    - Check for Duplicates (TODO)

## Color Coding (Auto-applied on status change)

- **Yellow** - Successful Order
- **Green** - Requested Email
- **Red** - Potentially Invalid
- **Fuchsia** - Voicemail/No Answer
- **White** - Not interested

## Configuration

Edit these constants in ToolboxSuite.js:
- `targetSheetName` in `onEdit()` - Currently "Working List 2025"
- `statusColumn` - Column J (10)
- Color mappings
