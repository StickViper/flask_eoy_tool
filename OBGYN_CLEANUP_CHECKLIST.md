# OBGYN Working List - EOY Cleanup Guide

**Purpose:** End-of-year data cleanup using automation tools
**Time:** ~2 hours (down from 8-10 hours manual)
**See also:** `MASTER_SYSTEM_DOCUMENTATION.md` for full system details

---

## ✅ STATUS - READY TO USE (Oct 18, 2025)

**CRITICAL BUGS FIXED:**
1. ✅ **Step 2 FIXED** - Now uses dynamic weight fuzzy matching (works without phone column)
2. ✅ **Step 1 VERIFIED** - Already populates Debug/Issues column correctly
3. ✅ **Network notation VERIFIED** - Already uses correct "networkname network (~8);" format

See `TODO.md` section 0 for verification details and deployment status.

---

## QUICK REFERENCE - What Tools Do What

**Automated (Misc. Tools → End-of-Year Workflow):**
- **Step 1:** Audit Working List → Counts issues, creates hidden Debug/Issues column
- **Step 2:** Validate Yellow → New Orders → Cross-references working list with orders ✅ FIXED
- **Step 3:** Enforce Not Interested Rules → Auto-adds "not interested" to notes, sets QTY=0
- **Step 4:** Detect Duplicates → Finds duplicate phone/address, detects networks
- **Step 5:** Review Status-Based Issues → Categorizes Red/Fuschia/Green/Empty rows

**Still Manual:**
- Connecting OBGYN sheet to ToolboxSuite.js (one-time setup)
- Fixing flagged issues in Debug/Issues column
- Adding new QTY column for next year
- Duplicating/renaming sheets
- Updating STATS tab formulas

---

## ONE-TIME SETUP (If not already done)

### Get OBGYN Script ID
1. Open OBGYN Working List in browser
2. Extensions → Apps Script → ⚙️ Project Settings
3. Copy Script ID

### Connect Automation
```bash
cd "C:\Users\noagi\Desktop\JGDC"
mkdir scripts\obgyn-list
cd scripts\obgyn-list
clasp clone <SCRIPT_ID>
cp ../pcp-list/ToolboxSuite.js .
clasp push
```

### Verify Menu
1. Refresh Google Sheets (Ctrl+R)
2. Check for "Misc. Tools" menu
3. Look for "End-of-Year Workflow" submenu

---

## EOY CLEANUP PROCEDURE

### Phase 1: Backup (5 min)
```
File → Make a copy → Name: "OBGYN Working List 2025 - BACKUP - [Date]"
```

### Phase 2: Run Audit (15 min)
```
Misc. Tools → End-of-Year Workflow → Step 1: Audit Working List
```
**Records issue counts:**
- Yellow not in New Orders: ___
- Not interested issues: ___
- Duplicates: ___
- Status reviews needed: ___

**Unhide Debug/Issues column:** Right-click column headers → Unhide

---

### Phase 3: Fix Yellow → New Orders Issues (15-30 min)

✅ **Automated:** Step 2 now uses fuzzy matching (office name + address)

```
Misc. Tools → End-of-Year Workflow → Step 2: Validate Yellow → New Orders
```

**What it does:**
- Finds yellow rows in Working List
- Fuzzy matches against New Orders (name 70% + address 30%)
- Flags mismatches in Debug/Issues column with confidence scores

**Manual review needed for:**
- Medium confidence matches (80-95%) - verify they're the same provider
- QTY mismatches - decide which sheet has correct quantity
- "Not found" providers - verify if they should have been in New Orders

---

### Phase 4: Fix "Not Interested" Issues (20 min)

```
Misc. Tools → End-of-Year Workflow → Step 3: Enforce Not Interested Rules
```

**What it does automatically:**
- Adds "not interested" to Notes if missing
- Sets QTY to 0

**Manual:** Review edge cases flagged in Debug/Issues column

---

### Phase 5: Handle Duplicates (30-60 min)

```
Misc. Tools → End-of-Year Workflow → Step 4: Detect Duplicates
```

**What it does:**
- Flags duplicate phone/address
- Detects networks (same name + phone, different addresses)
- ⚠️ Network notation format currently wrong (see TODO.md)

**Manual review required:**

| Scenario | Action |
|----------|--------|
| Exact duplicates (same name, phone, address) | Delete one, keep most recent |
| Same clinic, different doctors | Keep both |
| Same phone, different offices | Verify which is correct, delete wrong one |
| Data entry typo | Fix typo, then delete duplicate |

**Before deleting:** Check if duplicate has orders in New Orders sheet - merge order history if yes

---

### Phase 6: Review Status-Based Issues (30 min)

```
Misc. Tools → End-of-Year Workflow → Step 5: Review Status-Based Issues
```

**🔴 Red (Potentially Invalid):**
- Verify truly invalid (call, Google search)
- If confirmed: Add to "Invalid/Inactive List" sheet
- If actually valid: Update info, change status

**💜 Fuschia (Voicemail/No Answer):**
- < 3 attempts: Schedule another call
- ≥ 3 attempts: Leave as-is
- **Important:** Leave QTY empty (not 0) - distinguishes from "not interested"

**🟢 Green (Requested Email):**
- Recent (< 2 weeks): Keep green
- Old (> 4 weeks) + no response: Change to "Not interested"

**⚪ Empty (Uncalled):**
- No notes: Leave empty (will call next cycle)
- Has notes but no status: Set correct status

---

### Phase 7: Final Validation (15 min)

```
Misc. Tools → End-of-Year Workflow → Step 1: Audit Working List
```

**Goal:** All counts should be 0 or near-0

**If issues remain:**
1. Unhide Debug/Issues column
2. Review each warning
3. Decide: Fix, explain why OK, or clear false positive

**Hide Debug/Issues column:** Right-click header → Hide column

---

### Phase 8: Clean New Orders Sheet (20 min)

**Check for duplicates:**
1. Sort by Office Name or Phone
2. Look for identical entries
3. Verify QTY totals match Working List

**Validate all have yellow match:**
- Each row in New Orders should have matching yellow row in Working List

---

### Phase 9: Manual EOY Tasks (60 min)

⚠️ **Not yet automated** - too complex/risky

**Add 2026 QTY column:**
1. Insert column after "2025 QTY"
2. Name it "2026 QTY"
3. Leave empty for now

**Duplicate sheets:**
1. Right-click "Working List 2025" → Duplicate
2. Rename old: "OLD Working List 2025"
3. Rename duplicate: "Working List 2026"
4. Same for "New Orders 2025"

**Clear data for new year:**
- New Orders 2026: Delete all rows (keep header)
- Working List 2026:
  - Clear colors (select all, Format → Clear formatting)
  - Clear Call Status column
  - PRESERVE email Notes (don't clear Notes column)

**Update STATS tab:**
- Update sheet name references
- Extend yearly stats columns
- Update "current round" month

**Update Dashboard links:**
- Update IMPORTRANGE formulas
- Adjust cell ranges for new year
- Test all links

---

## TROUBLESHOOTING

### "Automation isn't working"
- Check if sheet name is exactly "Working List 2025"
- Verify Call Status is in column J
- Refresh page after clasp push
- Check Apps Script editor for errors

### "Too many issues flagged"
- This is normal for first run
- Work through systematically
- Many are false positives (will learn patterns)

### "Duplicate detection false positives"
- Network detection logic handles same phone + different addresses
- If flagged as duplicate but is network: Add "network name network (~#);" to Notes

---

## SUCCESS CRITERIA

✅ All yellow rows accounted for in New Orders
✅ Zero "not interested" rows with QTY > 0
✅ All duplicates reviewed (merged or marked as networks)
✅ Red/Fuschia/Green rows triaged
✅ Debug/Issues column clear or explained
✅ New Orders validated against Working List
✅ Ready for next year's campaign

---

**Total time:** ~2-4 hours (was 8-10 hours before automation)
**Next cleanup:** End of 2026
