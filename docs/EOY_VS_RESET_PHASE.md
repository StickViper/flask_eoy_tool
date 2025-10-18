# EOY vs. Reset Phase - Critical Distinction

**Purpose:** Clarify the difference between End-of-Year cleanup and Reset for next year
**Last Updated:** October 18, 2025
**Audience:** Technical user, AI agents working on EOY automation

---

## TL;DR

- **EOY** = Data cleanup and validation of current year (2025)
- **Reset** = Prepare sheets for next year's campaign (2026)
- **Key:** EOY runs while still adding to 2025 QTY column
- **Reset** happens later (separate phase)

---

## EOY (End-of-Year) Phase

### What It Is

**Data cleanup and validation** of the current year's calling campaign while it's still active.

### When It Runs

- ASAP for OBGYN (October 2025)
- Can run multiple times during a campaign
- **Critical:** 2025 calling continues AFTER EOY runs
- Users will keep adding to "2025 QTY" column in "Working List 2025" sheet

### What It Does

1. **Validate Yellow Rows** → Verify "Successful Order" rows exist in "New Orders 2025"
2. **Fix Not Interested** → Ensure QTY=0 and "not interested" in Notes
3. **Detect Duplicates** → Flag duplicate phone/address, identify networks
4. **Categorize Status Issues** → Review Red/Fuschia/Green/Empty rows
5. **Populate Debug/Issues Column** → Hidden column with warnings for manual review
6. **Audit Data Quality** → Count issues, show summary

### What It Does NOT Do

- ❌ Add "2026 QTY" column
- ❌ Duplicate sheets with "OLD" prefix
- ❌ Clear New Orders sheet
- ❌ Clear colors/statuses
- ❌ Update STATS formulas
- ❌ Change year references

### Expected State After EOY

```
Working List 2025:
- All data still present (2023/2024/2025 QTY columns)
- Debug/Issues column created (auto-hidden)
- Issues flagged for review
- Colors/statuses UNCHANGED
- Volunteers continue calling and adding 2025 orders
```

### Who Uses It

**Technical user only** - volunteers never see or use EOY automation

### Tools/Menu Location

Menu: `Misc. Tools → End-of-Year Workflow`

Steps:
- Step 1: Audit Working List
- Step 2: Validate Yellow → New Orders
- Step 3: Enforce Not Interested Rules
- Step 4: Detect Duplicates
- Step 5: Review Status-Based Issues
- Step 6: Run All (1-5 sequentially)

---

## Reset Phase

### What It Is

**Transition to next year's campaign** - structural changes to sheets and formulas.

### When It Runs

- After 2025 calling is completely finished (likely January-February 2026)
- **Only once** per year
- After all 2025 orders are fulfilled

### What It Does

1. **Add 2026 QTY Column**
   - Insert new column after "2025 QTY"
   - Name it "2026 QTY"
   - Leave empty initially

2. **Duplicate and Rename Sheets**
   - Duplicate "Working List 2025" → Rename old to "OLD Working List 2025"
   - Rename duplicate to "Working List 2026"
   - Same for "New Orders 2025" → "OLD New Orders 2025" + "New Orders 2026"

3. **Clear Data for 2026**
   - New Orders 2026: Delete all rows (keep header only)
   - Working List 2026:
     - Clear colors (Format → Clear formatting)
     - Clear Call Status column (column J)
     - **PRESERVE email Notes** (don't clear Notes column)
     - Keep office info (Name, Phone, Address, etc.)
     - Keep historical QTY (2023/2024/2025 columns)

4. **Update STATS Tab**
   - Update sheet name references in formulas
   - Extend yearly stats columns (add 2026 row)
   - Update "current round" month reference

5. **Update Dashboard Links**
   - Update IMPORTRANGE formulas to point to "Working List 2026"
   - Adjust cell ranges for new year
   - Test all links

### What It Does NOT Involve

- ❌ Data validation (that's EOY phase)
- ❌ Duplicate detection (that's EOY phase)
- ❌ Yellow row verification (that's EOY phase)

### Expected State After Reset

```
Working List 2026:
- Office info intact (Name, Phone, Address, City, State, Zip)
- Historical QTY intact (2023/2024/2025 columns)
- Email Notes preserved
- Call Status cleared (ready for new calls)
- Colors cleared (all white)
- 2026 QTY empty (ready for new orders)

Working List 2025 (OLD):
- Archived as "OLD Working List 2025"
- Complete historical record
- No changes made

New Orders 2026:
- Empty (header only)
- Ready for first 2026 orders

STATS Tab:
- Formulas point to 2026 sheets
- Historical data preserved (2023/2024/2025)
```

### Who Uses It

**Technical user** - complex manual process (not yet automated)

### Current Status

**NOT AUTOMATED** - Too complex/risky for initial automation

**Manual procedure documented in:** OBGYN_CLEANUP_CHECKLIST.md (Phase 9)

---

## Workflow Timeline

```
Oct 2025                  Dec 2025                 Jan 2026
  │                         │                        │
  ├─[EOY Phase 1]──────────►│                        │
  │  Validate data          │                        │
  │  Flag issues            │                        │
  │  Continue calling       │                        │
  │                         │                        │
  ├─[EOY Phase 2]──────────►│                        │
  │  (can run multiple      │                        │
  │   times as needed)      │                        │
  │                         │                        │
  │  Still adding to        │                        │
  │  2025 QTY column        │                        │
  │                         │                        │
  │                         ├─[Calling Ends]────────►│
  │                         │                        │
  │                         │                        ├─[Reset Phase]
  │                         │                        │  Structural changes
  │                         │                        │  Prepare for 2026
  │                         │                        │
  │                         │                        ├─[2026 Calling Starts]
```

---

## Key Differences Table

| Aspect | EOY Phase | Reset Phase |
|--------|-----------|-------------|
| **Purpose** | Data cleanup/validation | Structural transition |
| **Timing** | During active campaign | After campaign ends |
| **Frequency** | Multiple times (as needed) | Once per year |
| **Automation** | Partially automated | Manual (complex) |
| **Data Changes** | Flags issues, minor fixes | Clears statuses, adds columns |
| **Year Focus** | Current year (2025) | Next year (2026) |
| **Calling Status** | Continues during/after | Stopped before reset |
| **2025 QTY** | Still being added to | No longer modified |
| **Sheets Modified** | Working List 2025, New Orders 2025 | Creates 2026 sheets, archives 2025 |
| **Formulas** | Unchanged | Updated to reference 2026 |

---

## Why This Distinction Matters

### For AI Agents

**Common mistake:** Assuming EOY means "prepare for next year"

**Reality:** EOY = clean current year's data while campaign is still active

**Implication:** Don't auto-clear data, don't add new year columns, don't rename sheets

### For Planning

**EOY can run now** (ASAP for OBGYN) because:
- Doesn't disrupt ongoing calling
- Flags issues for review
- Improves data quality for final orders
- Can run multiple times (iterative cleanup)

**Reset must wait** because:
- Requires all 2025 calling to be complete
- Destructive changes (clearing statuses)
- Can't easily reverse
- One-time operation

### For Bug Fixes

**When fixing EOY automation:**
- Focus: Data validation, duplicate detection, issue flagging
- Test: Run multiple times on same data (should be idempotent)
- Safety: Never delete rows, never clear historical data

**When considering Reset automation (future):**
- Focus: Sheet duplication, column insertion, formula updates
- Test: On copy of production (highly destructive)
- Safety: Require backup, confirmation dialog, rollback plan

---

## Current Implementation Status

### EOY Phase

**Automated (Menu Items):**
- ✅ Step 1: Audit (counts issues) - ⚠️ Bug: doesn't populate Debug column
- ✅ Step 3: Not Interested (auto-fixes)
- ✅ Step 4: Duplicates (flags) - ⚠️ Bug: network notation wrong format
- ✅ Step 5: Status Review (categorizes)
- ❌ Step 2: Yellow validation - **BROKEN** (phone matching, but New Orders has no phone)

**Status:** Partial - critical bugs block OBGYN EOY (fixing ASAP)

### Reset Phase

**Automated:**
- ❌ None - entirely manual

**Documented:**
- ✅ Manual procedure in OBGYN_CLEANUP_CHECKLIST.md (Phase 9)

**Future Work:**
- Low priority (once per year)
- High complexity (formula updates risky)
- Good candidate for future automation (after EOY proven)

---

## Examples

### Example 1: October 2025 OBGYN Campaign

**Situation:**
- OBGYN Working List 2025 has 710 active contacts
- 230 yellow (orders), 117 fuschia (callback), 265 uncalled
- Campaign started in September, ongoing through December
- Technical user wants to clean up data quality issues

**Correct Action:** **Run EOY Phase**
- Validates 230 yellow rows against New Orders
- Detects duplicates (if any)
- Flags status issues
- Creates Debug/Issues column for review
- **Calling continues** - volunteers keep working

**Incorrect Action:** ~~Run Reset Phase~~
- Would clear statuses (lose progress!)
- Would create 2026 sheets (premature)
- Would disrupt ongoing campaign

---

### Example 2: January 2026 PCP Campaign

**Situation:**
- PCP List 2025 has 1,874 active contacts
- All calling finished in December 2025
- 633 orders fulfilled, all shipped
- Ready to start 2026 campaign

**Correct Action:** **Run Reset Phase**
- Archive "Working List 2025" as "OLD Working List 2025"
- Create "Working List 2026" (cleared statuses, preserved data)
- Add 2026 QTY column
- Update STATS formulas
- Ready for 2026 calling

**Incorrect Action:** ~~Run EOY Phase again~~
- Data already cleaned (EOY ran in December)
- Won't transition to 2026
- Calling can't start (still using 2025 sheet)

---

## FAQ

### Q: Can I run EOY multiple times?

**A:** Yes! EOY is designed to be idempotent. Run it whenever you want to validate data quality. Useful during active campaigns to catch issues early.

### Q: When should I run Reset?

**A:** Only after 100% of current year calling is finished AND all orders are fulfilled. Typically January-February of next year.

### Q: What if I run Reset too early?

**A:** Big problem! You'll lose all current year statuses and can't easily recover. Volunteers lose progress. Always finish calling first.

### Q: Can I automate Reset phase?

**A:** Theoretically yes, but very risky. Formula updates can break dashboards. Start with EOY automation, tackle Reset later.

### Q: Does EOY clear the Notes column?

**A:** No! EOY only *adds* to Notes (e.g., network notation). Reset phase preserves email notes but clears statuses.

### Q: How do I know if calling is "finished"?

**A:** Check STATS sheet:
- % uncalled < 5%
- % unresolved (callback) < 10%
- All orders fulfilled and shipped
- Volunteers confirm done

---

**Remember:** EOY = clean while active | Reset = transition when done

---

**Last Updated:** October 18, 2025
