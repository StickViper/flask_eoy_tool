# OBGYN Working List Cleanup - Step-by-Step Action Plan

**Goal:** Clean up messy OBGYN Working List and prepare it for EOY transition
**Status:** Detailed action-by-action checklist
**Estimated Time:** 3-4 hours

---

## PHASE 1: CONNECT OBGYN SHEET TO AUTOMATION (30 min)

### Step 1.1: Get OBGYN Sheet Script ID
**What to do:**
1. Open your OBGYN Working List sheet in Google Sheets
2. Click **Extensions → Apps Script**
3. Click the **gear icon** (Project Settings) in left sidebar
4. Copy the **Script ID** (long string like `1a2b3c4d5e6f7g8h9i0j...`)
5. Paste it somewhere safe (we'll use it next)

**Why:** We need this to connect the EOY automation tools to your OBGYN sheet

---

### Step 1.2: Clone OBGYN Script to Local Computer
**What to do:**
1. Open command line / terminal
2. Run these commands:
```bash
cd "C:\Users\noagi\Desktop\JGDC"
mkdir scripts\obgyn-list
cd scripts\obgyn-list
clasp clone <PASTE_YOUR_SCRIPT_ID_HERE>
```

**What this does:** Downloads current OBGYN script to your computer so we can update it

**Expected result:** You'll see a message like "Cloned 1 file" and a `.clasp.json` file will appear

---

### Step 1.3: Copy ToolboxSuite.js to OBGYN Script
**What to do:**
1. Copy `scripts/pcp-list/ToolboxSuite.js` to `scripts/obgyn-list/ToolboxSuite.js`
2. In `scripts/obgyn-list/`, run:
```bash
clasp push
```

**What this does:** Gives your OBGYN sheet access to all the EOY automation functions

**Expected result:** Message says "Pushed 2 files" (appsscript.json + ToolboxSuite.js)

---

### Step 1.4: Verify Menu Appears
**What to do:**
1. Go back to your OBGYN Working List sheet
2. **Refresh the page** (Ctrl+R or Cmd+R)
3. Look for **"Misc. Tools"** menu at the top
4. Click it and verify you see **"End-of-Year Workflow"** submenu

**If menu doesn't appear:**
- Wait 30 seconds, refresh again
- Check Apps Script editor - any red errors?
- Make sure you pushed to the correct script

**Why:** This confirms the automation is connected and ready to use

---

## PHASE 2: BACKUP & PREPARE (10 min)

### Step 2.1: Create Backup Copy
**What to do:**
1. In Google Sheets: **File → Make a copy**
2. Name it: `OBGYN Working List 2025 - BACKUP - [Today's Date]`
3. Move backup to a "Backups" folder (or leave in My Drive)

**Why:** Safety net in case automation makes unexpected changes

---

### Step 2.2: Document Current Column Structure
**What to do:**
1. Open a text file or notepad
2. Write down the column letters and names from your OBGYN sheet:
   - Example: `A = Office Name, B = Phone Number, C = Address, ...`
3. Note which column is **"Call Status"** (usually J)
4. Note which column is **"2025 QTY"** (usually I)
5. Note which column is **"Notes"** (usually K)

**Why:** EOY automation needs to know where these columns are. We'll verify the script is looking at the right columns.

---

### Step 2.3: Check Sheet Name
**What to do:**
1. Look at the sheet tab name at the bottom
2. Is it exactly **"Working List 2025"**?

**If NOT "Working List 2025":**
- We'll need to update the script OR rename the sheet
- Note the current name for next steps

**Why:** Automation looks for sheet named "Working List 2025" by default

---

## PHASE 3: RUN INITIAL AUDIT (15 min)

### Step 3.1: Run Full Audit
**What to do:**
1. Open OBGYN Working List 2025
2. Click **Misc. Tools → End-of-Year Workflow → Step 1: Audit Working List**
3. Click **OK** when prompted
4. Wait for completion (may take 2-5 minutes depending on size)

**What this does:** Scans your entire sheet and counts:
- Yellow rows not in New Orders
- "Not interested" rows missing notes or wrong QTY
- Duplicate entries
- Status-based issues (Red/Fuschia/Green/Empty)

**Expected result:** A popup showing totals like:
```
Found 87 total issues:
• Yellow rows not in New Orders: 12
• Not Interested missing notes: 8
• Not Interested wrong QTY: 5
• Duplicate entries: 42
• Status reviews needed: 20
```

**Write these numbers down!** We'll use them to verify fixes later.

---

### Step 3.2: Unhide Debug/Issues Column
**What to do:**
1. Right-click on any column letter at the top
2. Look for a hidden column indicator (small arrows between columns)
3. Right-click the hidden column area
4. Select **"Unhide columns"**
5. Find the column named **"Debug/Issues"** (probably at the far right)

**What you'll see:** Rows with issues will have warning messages like:
- `⚠️ Yellow but NOT in New Orders`
- `⚠️ QTY mismatch: Working=5, Orders=3`
- `⚠️ Missing "not interested" in Notes; QTY should be 0`
- `🔄 Duplicate phone (appears 2 times)`

**Why:** This shows you exactly what needs fixing, row by row

---

### Step 3.3: Sort by Issues (Optional but Helpful)
**What to do:**
1. Select the entire data range (click A1, then Ctrl+Shift+End)
2. **Data → Create a filter**
3. Click the filter icon on "Debug/Issues" column
4. **Uncheck "Blanks"** to show only rows with issues
5. Now you can see all problem rows together

**Why:** Easier to fix issues when they're grouped together

---

## PHASE 4: FIX YELLOW → NEW ORDERS ISSUES (30-60 min)

### Step 4.1: Understand the Yellow Issue
**What it means:** Rows highlighted **yellow** (Successful Order status) should exist in the "New Orders" sheet with the same phone number and QTY amount.

**Why it happens:**
- Copy-paste errors
- Orders placed but not copied to New Orders sheet
- QTY mismatch between sheets
- Phone number formatting differences

---

### Step 4.2: Fix Missing Yellow Rows
**For each row with `⚠️ Yellow but NOT in New Orders`:**

1. Look at the Office Name and Phone Number
2. Open the "New Orders 2025" sheet (or whatever it's called)
3. Search for that phone number (Ctrl+F)

**If found in New Orders:**
- There's a phone format mismatch (e.g., (123) 456-7890 vs 1234567890)
- **Action:** Standardize phone format in one or both sheets
- **OR:** Manually verify the order exists and clear the warning

**If NOT found in New Orders:**
- **Option A:** The order was never copied → Copy the row to New Orders
- **Option B:** False positive → Change status from "Successful Order" to appropriate status
- **Option C:** Old data → Mark for review

**After fixing:**
1. Clear the warning text in Debug/Issues column for that row
2. Move to next issue

---

### Step 4.3: Fix QTY Mismatches
**For each row with `⚠️ QTY mismatch: Working=X, Orders=Y`:**

1. Check which QTY is correct:
   - Did we actually send X or Y brochures?
   - Look at Notes for context
   - Check with team if unsure

2. Update the **wrong** QTY to match the **correct** one:
   - Update Working List QTY column, OR
   - Update New Orders QTY column

3. Clear the warning in Debug/Issues column

**Why this matters:** QTY must match for accurate year-end reports

---

### Step 4.4: Verify All Yellow Issues Fixed
**What to do:**
1. Go back to Working List 2025
2. **Misc. Tools → End-of-Year Workflow → Step 2: Validate Yellow → New Orders**
3. Check the popup - should say "Found 0 issues"

**If still showing issues:**
- Review the Debug/Issues column again
- Make sure you saved changes
- Double-check phone number formats

---

## PHASE 5: FIX "NOT INTERESTED" ISSUES (20-30 min)

### Step 5.1: Run Auto-Fix for Not Interested
**What to do:**
1. **Misc. Tools → End-of-Year Workflow → Step 3: Enforce Not Interested Rules**
2. Click **OK** when prompted

**What this does automatically:**
- Adds "not interested" to Notes column if missing
- Sets QTY to 0 if it's not already
- Flags edge cases in Debug/Issues column

**Expected result:** Popup says something like:
```
Found 13 issues, fixed 10 automatically.
Check "Debug/Issues" column for edge cases.
```

---

### Step 5.2: Handle Edge Cases
**Look for rows with warnings like:**
- `⚠️ Missing "not interested" in Notes` (but QTY is weird)
- `⚠️ QTY should be 0 (currently 5)` (but they actually ordered?)

**For each edge case:**
1. Read the Notes column - what's the story?
2. Check Call Status - is it really "Not Interested"?
3. Decide:
   - **If truly not interested:** Delete the note that shouldn't be there, set QTY=0
   - **If actually ordered:** Change status to "Successful Order" (yellow)
   - **If unsure:** Flag for team review (add note in Debug/Issues)

**After fixing:**
- Clear the warning in Debug/Issues column

---

### Step 5.3: Verify All Not Interested Issues Fixed
**What to do:**
1. **Misc. Tools → End-of-Year Workflow → Step 3: Enforce Not Interested Rules**
2. Should say "Found 0 issues"

---

## PHASE 6: HANDLE DUPLICATES (30-60 min)

### Step 6.1: Understand Duplicate Detection
**What it flags:**
- `🔄 Duplicate phone (appears X times)`
- `🔄 Duplicate address (appears X times)`

**Why it happens:**
- Same provider called multiple times
- Data imported from multiple sources
- Clinic + individual doctor at same location
- Copy-paste errors

**IMPORTANT:** The script does **NOT** auto-merge. You must review each manually.

---

### Step 6.2: Review Each Duplicate Group
**For each duplicate:**

1. Use Ctrl+F to find all rows with the same phone/address
2. Compare the rows side-by-side:
   - Same Office Name? → Probably true duplicate
   - Different Office Name but same address? → Could be same building
   - Different Office Name + phone? → Possible data entry error

3. Check Call Status and Notes:
   - Has one been called but not the other?
   - Do they have different order histories?

**Decision matrix:**

| Scenario | Action |
|----------|--------|
| **Exact duplicates** (same name, phone, address) | Delete one, keep the best one (most recent activity) |
| **Same clinic, different doctors** | Keep both (they're different providers) |
| **Same phone, different offices** | Verify which is correct, delete wrong one |
| **Data entry typo** | Fix the typo, then delete duplicate |
| **Unsure** | Add note in Debug/Issues: "REVIEW: possible duplicate - [your note]" |

---

### Step 6.3: Merge Order Histories (If Deleting Duplicate)
**Before deleting a duplicate row:**

1. Check if it has orders in "New Orders" sheet
2. If yes:
   - Go to New Orders sheet
   - Find orders for the duplicate phone number
   - **Add a note** in the duplicate order row: "MERGED - see [other phone/office]"
   - **Sum the QTYs** from both rows if appropriate
3. Update the row you're keeping with combined info

**Why:** Don't lose order history when merging duplicates

---

### Step 6.4: Clear Duplicate Warnings
**After handling each duplicate:**
1. Clear the `🔄 Duplicate` text from Debug/Issues column
2. OR add "REVIEWED - keeping both" if intentionally not merging

---

## PHASE 7: REVIEW STATUS-BASED ISSUES (30-45 min)

### Step 7.1: Run Status Review
**What to do:**
1. **Misc. Tools → End-of-Year Workflow → Step 5: Review Status-Based Issues**
2. Read the categorization popup carefully

**What you'll see:**
```
Status-Based Review:

🔴 Red (Potentially Invalid): 15
   → Should exist or be added to Invalid/Inactive list

💜 Fuschia (Voicemail/No Answer): 42
   → Triple follow-up, leave empty at EOY (no 0 in QTY)

🟢 Green (Requested Email): 8
   → Keep green if recent, change to "not interested" if old

⚪ Empty (Uncalled): 103
   → Never reached, leave as-is
```

---

### Step 7.2: Handle Red (Potentially Invalid) Rows
**For each RED row:**

1. Look at Notes - why is it marked "Potentially Invalid"?
   - Disconnected phone?
   - Wrong address?
   - Provider retired/moved?

2. Verify it's truly invalid:
   - Try calling again?
   - Google the provider?
   - Check if they moved offices?

3. Action:
   - **If confirmed invalid:** Add to "Invalid/Inactive List" sheet (create if doesn't exist)
   - **If actually valid:** Update phone/address, change status to appropriate color
   - **If unsure:** Add note: "VERIFY: needs follow-up"

---

### Step 7.3: Handle Fuschia (Voicemail/No Answer) Rows
**For each FUSCHIA row:**

1. Check Notes - how many follow-up attempts?
   - 1st attempt?
   - 2nd attempt?
   - 3rd attempt (triple follow-up)?

2. Action based on attempts:
   - **Less than 3 attempts:** Schedule another follow-up call
   - **3+ attempts:** Leave status as Fuschia
   - **Important:** Do NOT put 0 in QTY column (leave empty to distinguish from "Not interested")

**Why empty vs 0 matters:**
- Empty = We tried to reach them but couldn't
- 0 = They said "not interested"

---

### Step 7.4: Handle Green (Requested Email) Rows
**For each GREEN row:**

1. Check date of email request (should be in Notes)
2. Has it been sent?
   - **Sent recently (< 2 weeks):** Keep green, wait for response
   - **Sent a while ago (> 4 weeks) + no response:** Change to "Not interested"
   - **Not sent yet:** Send email OR add to email queue

3. Update Notes with email status

---

### Step 7.5: Handle Empty (Uncalled) Rows
**For each row with empty Call Status:**

1. Check if there's activity in Notes
   - **No activity:** Leave empty (truly uncalled)
   - **Has notes but no status:** Someone forgot to set status - fix it
2. These will be called in next campaign cycle

**Action:** Generally leave these alone unless obviously wrong

---

## PHASE 8: FINAL VALIDATION (15 min)

### Step 8.1: Run Full Audit Again
**What to do:**
1. **Misc. Tools → End-of-Year Workflow → Step 1: Audit Working List**
2. Compare totals to your initial audit numbers

**Goal:** All issue counts should be 0 or very low:
```
Found 3 total issues:  ← Down from 87!
• Yellow rows not in New Orders: 0
• Not Interested missing notes: 0
• Not Interested wrong QTY: 0
• Duplicate entries: 0
• Status reviews needed: 3  ← Flagged for manual review
```

---

### Step 8.2: Review Remaining Issues
**If any issues remain:**
1. Unhide Debug/Issues column
2. Read each remaining warning
3. Decide if it's:
   - A real issue → Fix it
   - An edge case → Add note explaining why it's OK
   - A false positive → Clear the warning

---

### Step 8.3: Hide Debug/Issues Column
**What to do:**
1. Right-click on "Debug/Issues" column header
2. Select **"Hide column"**

**Why:** Keeps sheet clean for daily use, but you can unhide anytime

---

### Step 8.4: Test onEdit Color Coding
**What to do:**
1. Pick any empty row
2. Type "Successful Order" in the Call Status column
3. Press Enter

**Expected result:** Entire row turns **yellow**

**Test other statuses:**
- "Requested Email" → Green
- "Potentially Invalid" → Red
- "Voicemail/No Answer" → Fuschia
- "Not interested" → White (and auto-adds "not interested" to Notes, sets QTY=0)

**If colors don't work:**
- Check Call Status column is column J (or whatever you noted in Step 2.2)
- Open Apps Script editor, check for errors
- Verify ToolboxSuite.js was pushed correctly

---

## PHASE 9: PREPARE NEW ORDERS SHEET (20 min)

### Step 9.1: Check for Duplicate Detection in New Orders
**What to do:**
1. Open "New Orders 2025" sheet
2. Look for "Debug/Issues" column (may need to unhide)
3. Check for duplicate warnings

**If duplicates found:**
- Same process as Working List duplicates
- Verify QTY totals are correct
- Don't ship duplicate orders!

---

### Step 9.2: Validate All Orders Have Matching Yellow Rows
**What to do:**
1. For each row in New Orders
2. Find the matching phone number in Working List
3. Verify that row is **yellow** (Successful Order)

**If NOT yellow:**
- Either Working List is wrong (should be yellow)
- Or New Orders is wrong (shouldn't be there)
- Investigate and fix

---

### Step 9.3: Check QTY Consistency
**What to do:**
1. Compare QTY column in Working List vs. New Orders
2. They should match for the same phone number

**If mismatch:**
- Which is correct?
- Update the wrong one
- Add note explaining the change

---

## PHASE 10: DOCUMENT & WRAP UP (10 min)

### Step 10.1: Create Cleanup Summary Document
**What to do:**
1. Create a text file or Google Doc: "OBGYN Cleanup Summary - [Date]"
2. Write down:
   - Initial issue counts (from Phase 3)
   - Final issue counts (from Phase 8)
   - Number of duplicates removed
   - Number of rows marked invalid
   - Any edge cases still pending review
   - Total time spent

**Why:** Helps track progress and identify recurring issues

---

### Step 10.2: Share with Team
**What to do:**
1. Send summary to your team
2. Highlight any items that need their input
3. Document any decisions made (e.g., "we decided to keep both rows because...")

---

### Step 10.3: Plan Next Campaign
**What to do:**
1. Count how many rows are ready to call (empty status or fuschia needing follow-up)
2. Estimate how long the calling will take
3. Schedule campaign start date

---

## TROUBLESHOOTING

### "The script isn't finding the right sheet"
**Fix:**
1. Open Apps Script editor
2. Find the line: `targetSheetName = 'Working List 2025'`
3. Change it to your actual sheet name
4. Save and refresh

---

### "onEdit color coding isn't working"
**Fix:**
1. Verify Call Status is in column J
2. If not, update the script:
   - Find: `statusColumn = 10`
   - Change 10 to your column number (A=1, B=2, ... K=11)
3. Save and refresh

---

### "Automation is too slow"
**This is normal if:**
- You have 500+ rows
- Each validation step may take 2-5 minutes
- Be patient, don't interrupt

**If it's been > 10 minutes:**
- Check Apps Script logs (View → Logs)
- Look for error messages
- May need to run in smaller batches

---

### "I accidentally deleted important data"
**Don't panic:**
1. Go to your backup copy (Phase 2, Step 2.1)
2. Copy the data you need
3. Paste it back into main sheet
4. Re-run affected validation steps

---

## QUICK REFERENCE CHECKLIST

Use this to track your progress:

- [ ] Phase 1: Connect OBGYN sheet to automation
  - [ ] Get Script ID
  - [ ] Clone script locally
  - [ ] Push ToolboxSuite.js
  - [ ] Verify menu appears

- [ ] Phase 2: Backup & prepare
  - [ ] Create backup copy
  - [ ] Document column structure
  - [ ] Verify sheet name

- [ ] Phase 3: Run initial audit
  - [ ] Run full audit, record numbers
  - [ ] Unhide Debug/Issues column
  - [ ] Sort by issues (optional)

- [ ] Phase 4: Fix yellow → New Orders issues
  - [ ] Fix missing yellow rows
  - [ ] Fix QTY mismatches
  - [ ] Verify all fixed

- [ ] Phase 5: Fix "not interested" issues
  - [ ] Run auto-fix
  - [ ] Handle edge cases
  - [ ] Verify all fixed

- [ ] Phase 6: Handle duplicates
  - [ ] Review each duplicate group
  - [ ] Merge or separate as appropriate
  - [ ] Clear warnings

- [ ] Phase 7: Review status-based issues
  - [ ] Handle red rows
  - [ ] Handle fuschia rows
  - [ ] Handle green rows
  - [ ] Handle empty rows

- [ ] Phase 8: Final validation
  - [ ] Run audit again
  - [ ] Review remaining issues
  - [ ] Hide Debug/Issues column
  - [ ] Test onEdit color coding

- [ ] Phase 9: Prepare New Orders sheet
  - [ ] Check for duplicates
  - [ ] Validate yellow matches
  - [ ] Check QTY consistency

- [ ] Phase 10: Document & wrap up
  - [ ] Create cleanup summary
  - [ ] Share with team
  - [ ] Plan next campaign

---

**Estimated Total Time: 3-4 hours**
**Best done in: 2 sessions (Phase 1-5, then Phase 6-10)**
**Questions? Check SESSION_SUMMARY_20251003.md or TODO.md**
