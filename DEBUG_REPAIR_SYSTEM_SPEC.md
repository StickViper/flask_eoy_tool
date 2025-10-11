# 🔧 Debug Repair Sidebar - Comprehensive Specification

## ✅ COMPLETED FIXES (just pushed to Google Sheets)
- **Comma input bug FIXED**: Can now type `TX,WA,CO,PA` without losing commas
- **UniversalProviderSuite.js**: Verified error-free, safe column mapping
- All code pushed to Google Sheets successfully

---

## 🎯 MISSION: Debug Repair Sidebar
**Purpose**: Professional, safe, streamlined tool to resolve all Working List issues
**Style**: Dark navy (#1e3a5f) + teal (#00bcd4), matches QuickStartWizard professional aesthetic
**Safety**: ALL operations must preserve data integrity - no destructive actions without confirmation

---

## 📋 CRITICAL ISSUES TO SOLVE

### 🔴 **Issue #1: New Orders Checker is Broken**
**Problem**: Flags every yellow row as "not in New Orders" even when present
**Root Cause**: Exact string matching fails due to:
- Office name cleanup history (Dr. → Doctor, LLC variations, etc.)
- Whitespace differences
- Capitalization differences
- Punctuation variations (& vs and, etc.)

**Solution**: Multi-layer fuzzy matching system

---

## 🧩 COMPREHENSIVE SCENARIO ENUMERATION

### **YELLOW ROWS** (Successful Order)
**Expected State**: Yellow row exists in both Working List AND New Orders with matching phone/QTY

#### Scenario Y1: **Perfect Match**
- Working List: "Smith Family Medicine, (555) 123-4567, QTY: 50"
- New Orders: "Smith Family Medicine, (555) 123-4567, QTY: 50"
- **Action**: ✅ No action needed
- **Tool**: Show green checkmark "Verified"

#### Scenario Y2: **Office Name Mismatch (Fuzzy Match)**
- Working List: "Dr Smith Family Med LLC"
- New Orders: "Smith Family Medicine"
- Phone: MATCHES
- **Fuzzy Score**: 85% similarity
- **Action**: Show comparison side-by-side, user confirms match
- **Tool**: "Accept fuzzy match" button

#### Scenario Y3: **Missing from New Orders**
- Yellow row in Working List
- Phone number NOT found in New Orders
- **Possible Causes**:
  - Genuinely not added to New Orders yet
  - Phone number format mismatch
  - Entry error
- **Actions**:
  1. Search New Orders by fuzzy office name
  2. Search New Orders by address
  3. Show "Add to New Orders" button (pre-fills form)
  4. Show "False yellow - change status" button
  5. Google search link to verify office exists

#### Scenario Y4: **QTY Mismatch (minor)**
- Working List QTY: 48
- New Orders QTY: 50
- **Difference**: 2 (< 10% variance)
- **Action**: Auto-trust New Orders QTY, update Working List with note
- **Tool**: "Trust New Orders QTY" (default), "Trust Working List QTY", "Manual entry"

#### Scenario Y5: **QTY Mismatch (major)**
- Working List QTY: 5
- New Orders QTY: 50
- **Difference**: 45 (90% variance)
- **Action**: FLAG for manual review, show both values prominently
- **Tools**:
  - View notes from both sheets
  - Search history in Notes column
  - Manual QTY entry with reason field

#### Scenario Y6: **Duplicate Yellow Rows**
- Same phone appears multiple times as yellow
- **Ambiguity**: Which is correct?
- **Actions**:
  - Show all instances side-by-side
  - Compare office names, addresses
  - Show QTY totals from New Orders
  - "Merge duplicates" tool
  - "Keep all (different locations)" option

#### Scenario Y7: **Phone Format Mismatch**
- Working List: "(555) 123-4567"
- New Orders: "5551234567"
- **Solution**: Normalize phone numbers (strip non-digits, compare last 10 digits)
- **Tool**: Auto-detect and highlight format differences

#### Scenario Y8: **Phone with Extension**
- Working List: "(555) 123-4567 x102"
- New Orders: "(555) 123-4567"
- **Solution**: Strip extensions before comparison
- **Tool**: Auto-normalize, show "Extension: x102" as metadata

#### Scenario Y9: **Multiple Entries in New Orders**
- One yellow row in Working List
- Found 3 matching phone numbers in New Orders (multiple shipments)
- **Action**: Sum QTYs from New Orders, compare to Working List
- **Tool**: Show shipment history, "Sum QTYs" button

#### Scenario Y10: **Office Name Changed**
- Working List (old): "Smith Clinic"
- New Orders (new): "Smith Women's Health"
- Phone: MATCHES
- **Ambiguity**: Name change or different office?
- **Tools**:
  - Address comparison
  - Google search both names
  - Notes history review
  - "Update name in Working List" button

---

### **FUSCHIA ROWS** (Voicemail/No Answer)
**Expected State**: Attempted contact, no response yet

#### Scenario F1: **Standard Voicemail**
- Notes: "vm 10/5"
- **Action**: Edit notes, track follow-up count
- **Tool**: Auto-count VM attempts, suggest "vm x2" → "vm x3"

#### Scenario F2: **Auto-Strip Common Notes**
- Notes: "vm vm vm office closed"
- **Patterns to strip**: "vm", "vm x2", "office closed", "no answer", "busy"
- **Action**: Clean to "vm x3, office closed"
- **Tool**: "Smart cleanup" button with preview

#### Scenario F3: **Multiple Voicemails**
- Notes: "vm 10/1, vm 10/3, vm 10/7"
- **Action**: Consolidate to "vm x3 (last: 10/7)"
- **Tool**: Auto-consolidation with pattern detection

#### Scenario F4: **Office Closed (temporary)**
- Notes: "office closed for holiday"
- **Ambiguity**: Re-call later or mark invalid?
- **Tools**:
  - "Schedule re-call" (date picker)
  - "Mark as potentially invalid" (move to red)
  - Add to notes without changing status

#### Scenario F5: **Wrong Number**
- Notes: "wrong number, residential"
- **Action**: Should be RED (invalid), not fuschia
- **Tool**: "Move to invalid list" button

#### Scenario F6: **No QTY (correct)**
- Fuschia row with empty QTY field
- **Expected**: Empty QTY means "attempted, no response" (vs 0 = "not interested")
- **Tool**: Validate QTY is empty, warn if user tries to set to 0

#### Scenario F7: **Fuschia with QTY > 0**
- **Ambiguity**: Should be yellow (successful) or error?
- **Tools**:
  - "Convert to yellow + add to New Orders"
  - "Clear QTY (voicemail, no order)"
  - Manual review flag

#### Scenario F8: **Too Many Attempts**
- Notes: "vm x5, vm x6, vm x7"
- **Threshold**: > 3 attempts
- **Action**: Suggest moving to "Unreachable" category or clearing for next cycle
- **Tool**: "Clear for future cycle" (removes color, keeps notes)

---

### **RED ROWS** (Potentially Invalid)
**Expected State**: Disconnected, wrong number, or business closed permanently

#### Scenario R1: **Disconnected Number**
- Notes: "disconnected"
- **Action**: Add to Invalid/Inactive list, remove from Working List
- **Tools**:
  - "Add to Invalid list" button
  - Verify with Google search first
  - Archive row (move to separate sheet)

#### Scenario R2: **Business Closed Permanently**
- Notes: "out of business"
- **Action**: Add to Invalid list with reason
- **Tools**:
  - Google search to verify
  - "Mark as closed" (with date)
  - Move to Invalid/Inactive sheet

#### Scenario R3: **Moved/Relocated**
- Notes: "moved to [new address]"
- **Ambiguity**: Update address or create new entry?
- **Tools**:
  - "Update address" (if same business)
  - "Create new entry" (if new location)
  - Compare old vs new phone numbers
  - Google Maps verification

#### Scenario R4: **Wrong Specialty**
- Notes: "not OBGYN, is pediatrics"
- **Action**: Move to Invalid list with specialty note
- **Tool**: "Remove from OBGYN list, add to Invalid (wrong specialty)"

#### Scenario R5: **No Longer Accepting Patients**
- Notes: "not taking new patients"
- **Ambiguity**: Invalid forever or temporary?
- **Tools**:
  - "Mark as temporarily inactive" (with re-check date)
  - "Move to Invalid (permanent)"
  - Add to Notes without removing

#### Scenario R6: **Duplicate of Existing Entry**
- Red because it's a duplicate, not because it's invalid
- **Action**: Find master entry, merge data
- **Tools**:
  - "Find duplicates" (fuzzy search)
  - "Merge with [row X]" button
  - "Keep as separate entry" (different location)

#### Scenario R7: **Unverifiable**
- Can't find online, no info
- **Ambiguity**: Invalid or just not online?
- **Tools**:
  - Deep Google search (office name + city + state)
  - NPI lookup tool
  - "Mark as unverifiable" (separate category)

---

### **GREEN ROWS** (Requested Email)
**Expected State**: Provider requested brochure info via email

#### Scenario G1: **Email Sent, Awaiting Response**
- Notes: "email req 10/5, sent 10/6"
- Age: < 2 weeks
- **Action**: No change, keep green
- **Tool**: Show days since email sent

#### Scenario G2: **No Response (old)**
- Notes: "email req 9/1, sent 9/2"
- Age: > 4 weeks
- **Action**: Convert to "Not interested"
- **Tool**: "Convert to not interested" (sets QTY=0, adds note, clears color)

#### Scenario G3: **Email Sent, Check for Reply**
- **Action**: Open Gmail with search filter
- **Tools**:
  - Button: "Open Gmail" → `https://mail.google.com/mail/u/0/#search/from%3Adr@example.com`
  - Extract email from notes if present
  - Show "Reply received?" buttons (Yes/No)

#### Scenario G4: **Email Not Sent Yet**
- Notes: "email req 10/8"
- No "sent" date
- **Action**: Flag as pending email
- **Tools**:
  - "Mark as sent" (adds date)
  - "Email template" button (copies email draft)
  - Track unsent email requests

#### Scenario G5: **Email Bounced**
- Notes: "email bounced"
- **Action**: Try phone contact or mark invalid
- **Tools**:
  - "Convert to fuschia" (try phone)
  - "Mark as invalid" (bad email)
  - Search for correct email

#### Scenario G6: **Replied but No Order**
- Email reply received, but said no
- **Action**: Convert to "Not interested"
- **Tool**: "Mark replied (no order)" → sets QTY=0, adds note

#### Scenario G7: **Replied and Ordered**
- Email reply with order
- **Action**: Convert to yellow, add to New Orders
- **Tools**:
  - "Convert to successful order"
  - Pre-fill New Orders entry
  - Set QTY from email

#### Scenario G8: **Clear Status for Fresh Calling**
- Green rows should be reset for next campaign
- **Action**: Remove green color, clear email notes, keep office data
- **Tool**: "Reset for next cycle" button

---

### **WHITE/EMPTY ROWS** (No Status Set)
**Expected State**: Never called OR status cleared

#### Scenario W1: **Truly Uncalled**
- No notes, no status, no QTY
- **Action**: Leave as-is for future campaigns
- **Tool**: Show "Ready to call" indicator

#### Scenario W2: **Has Notes but No Status**
- Notes: "called 10/5, spoke with Jane"
- Status: Empty
- **Ambiguity**: Someone forgot to set status
- **Action**: Prompt for correct status
- **Tools**:
  - Read notes, suggest status
  - Quick status buttons (Yellow/Green/Red/Fuschia)

#### Scenario W3: **Has QTY but No Status**
- QTY: 50
- Status: Empty
- **Error State**: Should be yellow
- **Action**: Auto-fix to yellow, check if in New Orders
- **Tool**: "Auto-fix status" button

#### Scenario W4: **"Not Interested" in Notes**
- Notes: "not interested"
- Status: Empty
- **Error**: Should have status set
- **Action**: Auto-set QTY=0, add "not interested" label
- **Tool**: "Fix not interested status"

---

### **DEBUG MODE ROWS** (Has Debug/Issues column warnings)
**Expected State**: Rows flagged by automation with specific issues

#### Scenario D1: **"⚠️ Yellow but NOT in New Orders"**
- See Yellow Scenarios Y3-Y10
- **Action**: Use New Orders matcher with fuzzy logic

#### Scenario D2: **"⚠️ QTY mismatch: Working=X, Orders=Y"**
- See Yellow Scenarios Y4-Y5

#### Scenario D3: **"⚠️ Missing 'not interested' in Notes"**
- Status suggests "not interested" but missing in notes
- **Action**: Auto-add "not interested" to notes
- **Tool**: "Fix notes" button

#### Scenario D4: **"⚠️ QTY should be 0"**
- Not interested but QTY > 0
- **Action**: Set QTY to 0 with confirmation
- **Tool**: "Fix QTY" button

#### Scenario D5: **"🔄 Duplicate phone (appears X times)"**
- See Yellow Scenario Y6, but applies to all colors
- **Actions**:
  - Compare all instances
  - Check if same office or different locations
  - Merge tool
  - "Keep all" option

#### Scenario D6: **"🔄 Duplicate address"**
- Same address, different phone numbers
- **Ambiguity**: Same building (suite differences) or data error?
- **Tools**:
  - Google Maps link
  - Compare office names
  - Suite number extraction
  - "Merge" or "Keep separate"

#### Scenario D7: **Mixed Status Indicators**
- Row is yellow but notes say "not interested"
- **Conflict**: Status vs Notes
- **Action**: Show conflict, ask user which is correct
- **Tools**:
  - "Trust status" (remove conflicting notes)
  - "Trust notes" (update status)

#### Scenario D8: **Orphaned New Orders Entry**
- Entry in New Orders has NO matching phone in Working List
- **Action**: Create new Working List entry (reverse lookup)
- **Tool**: "Import from New Orders" button

---

## 🔍 FUZZY MATCHING ENGINE SPEC

### **Phone Number Normalization**
```javascript
function normalizePhone(phone) {
  // Strip extension: "555-1234 x102" → "555-1234"
  const mainPhone = phone.split(/\s*[xX]|ext/i)[0];
  // Strip all non-digits
  const digitsOnly = mainPhone.replace(/\D/g, '');
  // Return last 10 digits (handles +1 country code)
  return digitsOnly.slice(-10);
}
```

### **Office Name Fuzzy Matching**
**Layers of comparison** (in order):
1. **Exact match** (case-insensitive) → 100% confidence
2. **Normalized exact** (strip LLC, Dr., punctuation) → 95% confidence
3. **Levenshtein distance** → 0-100% confidence
4. **Token overlap** (split by words, count matches) → 0-100% confidence
5. **Soundex/Metaphone** (phonetic matching) → 0-100% confidence

**Confidence Thresholds**:
- ≥ 95%: Auto-match (green checkmark)
- 80-94%: Suggest match (yellow warning, user confirms)
- 60-79%: Possible match (show in results, user decides)
- < 60%: Not a match

### **Address Matching**
1. Normalize street abbreviations (St → Street, Ave → Avenue)
2. Strip suite numbers
3. Compare city + ZIP (exact)
4. Fuzzy compare street address
5. Flag if ZIP matches but street doesn't (possible data error)

### **Multi-Field Matching Score**
```
Total Score = (Phone Match × 40%) + (Name Match × 40%) + (Address Match × 20%)
```

**Thresholds**:
- ≥ 85%: High confidence match
- 70-84%: Medium confidence (user review)
- < 70%: No match

---

## 🎨 UI/UX DESIGN REQUIREMENTS

### **Visual Style** (matches QuickStartWizard)
- Background: Dark navy gradient (#1e3a5f → #0f2744)
- Accent: Teal (#00bcd4)
- Success: Green (#4caf50)
- Warning: Amber (#f59e0b)
- Error: Red (#f44336)
- Monospace code: JetBrains Mono
- Clean sans-serif: Inter

### **Sidebar Layout**
```
┌─────────────────────────────┐
│ 🔧 Debug Repair Mode        │
│ ───────────────────────────│
│ Row 47: Smith Family Med    │
│ Status: 🟡 Yellow           │
│ ───────────────────────────│
│ ⚠️ Issues Detected: 2       │
│                             │
│ Issue 1: Not in New Orders  │
│ ┌─────────────────────────┐ │
│ │ Fuzzy Match: 87%        │ │
│ │ Working: Dr Smith Med   │ │
│ │ New Ord: Smith Family   │ │
│ │ ✓ Accept Match          │ │
│ └─────────────────────────┘ │
│                             │
│ Issue 2: QTY Mismatch       │
│ ┌─────────────────────────┐ │
│ │ Working: 48 | New: 50   │ │
│ │ Diff: 2 (4%)            │ │
│ │ ✓ Trust New Orders      │ │
│ │ ⚪ Trust Working List    │ │
│ │ ⚪ Manual Entry          │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ 🔍 Google Search        │ │
│ │ 📧 Open Gmail           │ │
│ │ 🗑️ Clear Row Color       │ │
│ │ ➡️  Next Debug Row        │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### **Interactive Elements**
- **Radio buttons** for exclusive choices
- **Checkboxes** for multi-select
- **Sliders** for confidence thresholds
- **Color-coded pills** for status (like code-pill in wizard)
- **Expandable sections** for detailed info
- **Live search** for finding duplicates

---

## 🛠️ TOOLBAR AUTO-CLEAR FUNCTIONS

### **Bulk Operations** (in main menu)
1. **Clear All Yellow** (with confirmation)
2. **Clear All Fuschia** (after 3+ attempts)
3. **Clear All Green** (old email requests)
4. **Clear All Uncalled** (empty rows)
5. **Clear Debug Warnings** (after manual review)

### **Safety Checks**
- **Preview** before bulk clear (show affected rows)
- **Undo buffer** (store last 10 clears)
- **Confirmation dialog** for > 10 rows
- **Dry run mode** (show what would happen)

---

## 📊 ADDITIONAL DIMENSIONS OF UNCERTAINTY

### **Temporal Ambiguity**
- **Stale data**: How old is too old? (30 days? 90 days?)
- **Time zones**: Notes with timestamps but no zone
- **Relative dates**: "last week" vs "10/5"
- **Tool**: Auto-detect date formats, standardize

### **Multi-State Complexity**
- Same office name in multiple states (legitimate)
- Phone area code doesn't match state
- **Tool**: State validation, flag mismatches

### **Language/Character Issues**
- Accented characters: "José" vs "Jose"
- Apostrophes: "O'Brien" vs "OBrien" vs "O Brien"
- **Tool**: Unicode normalization

### **Organizational Changes**
- Mergers: "Smith Clinic" + "Jones Clinic" → "Smith Jones Medical Group"
- Acquisitions: Office name changed, phone same
- **Tool**: Historical notes tracking

### **Seasonal Variations**
- Summer closures (vacation)
- Holiday schedules
- **Tool**: "Seasonal inactive" category (different from permanent invalid)

### **Data Entry Errors**
- Typos in phone numbers (one digit off)
- Transposed digits
- **Tool**: "Did you mean?" suggestions for close matches

### **Multiple Contact Methods**
- Office has main line + fax + direct line
- Which phone to match on?
- **Tool**: "Alternate phones" field

### **Legal Entity Changes**
- PC → PLLC (same office)
- Sole practitioner → Group practice
- **Tool**: Entity type normalization

### **Address Precision**
- "123 Main St Suite 100" vs "123 Main St #100" vs "123 Main St Ste 100"
- **Tool**: Suite number extraction and normalization

### **Caps Lock Accidents**
- "SMITH FAMILY MEDICINE" vs "Smith Family Medicine"
- **Tool**: Smart capitalization fixer (respect MD, LLC, etc.)

### **Partial Information**
- Office name known, phone missing
- Phone known, address missing
- **Tool**: "Incomplete data" flag + search tools

---

## 🔬 FILTER VIEW AUTOMATION

### **Programmatic Filter Creation**
```javascript
// Create temporary filter showing only debug rows
function showDebugRowsOnly() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const debugColIndex = getColumnIndex('Debug/Issues');

  // Create or update filter
  const filter = sheet.getFilter() || sheet.getDataRange().createFilter();

  // Filter criteria: Debug/Issues column is not empty
  const criteria = SpreadsheetApp.newFilterCriteria()
    .whenTextNotEqualTo('')
    .build();

  filter.setColumnFilterCriteria(debugColIndex, criteria);
}
```

### **Pre-Built Filter Views**
1. **All Debug Rows** (Debug/Issues not empty)
2. **Yellow Issues Only** (Status = yellow AND debug flag)
3. **Duplicates Only** (Debug contains "Duplicate")
4. **QTY Mismatches** (Debug contains "QTY mismatch")
5. **Missing from New Orders** (Debug contains "NOT in New Orders")

---

## 💾 STATS SHEET STANDARDIZATION (TODO)
**Add to future TODO**:
- Make STATS formulae consistent between OBGYN and PCP
- Auto-generate stats from Working List + New Orders
- Visual dashboard with charts
- Success rate calculation
- Call conversion metrics

---

## 📝 IMPLEMENTATION PRIORITY

### **Phase 1: Core Debug Repair** (IMMEDIATE)
1. Fix New Orders fuzzy matching
2. Debug sidebar UI (matches QuickStartWizard style)
3. Yellow row repair tools
4. Auto-clear functions

### **Phase 2: Advanced Features** (NEXT)
5. Fuschia/Red/Green repair tools
6. Duplicate detection and merging
7. Filter view automation
8. Bulk operations

### **Phase 3: Intelligence** (LATER)
9. Pattern learning from corrections
10. Confidence threshold tuning
11. Automated suggestions
12. Stats sheet integration

---

## 🎯 SUCCESS CRITERIA

1. **Comma input works** ✅ (DONE)
2. **New Orders checker doesn't false-flag** (fuzzy matching)
3. **User can resolve debug row in < 30 seconds**
4. **Zero data loss** (all operations reversible)
5. **Professional aesthetic** (matches QuickStartWizard)
6. **Mobile-friendly** (sidebar width 350px)
7. **Keyboard shortcuts** (arrow keys for next/prev)

---

## 🚀 NEXT STEPS

1. **User**: Tell me how to share Google Sheets (I'll tell you formulas)
2. **Build**: Debug Repair Sidebar HTML + backend functions
3. **Test**: Run on sample OBGYN data
4. **Deploy**: Push to both OBGYN and PCP lists
5. **Document**: Update OBGYN_CLEANUP_CHECKLIST with new tools

---

**END OF SPECIFICATION**
**Reminder**: Tell me to record all this discussion for future reference!
