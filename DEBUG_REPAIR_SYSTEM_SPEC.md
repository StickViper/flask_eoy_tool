# 🔧 Debug Repair Sidebar - Implementation Spec

## CRITICAL FIX NEEDED IN EOY STEP 2

**ACTUAL Reality (from user):**
- New Orders sheet has: **Office Name + Address ONLY** (NO phone numbers)
- Current code uses phone-only matching → BROKEN
- Must use fuzzy matching on Office Name + Address

**Files to fix:**
- `scripts/obgyn-list/ToolboxSuite.js:815-883`
- `scripts/pcp-list/ToolboxSuite.js:764-833`

---

## 🎯 Debug Sidebar Purpose

Professional sidebar tool to resolve Working List data issues with:
- **Style:** Dark navy (#1e3a5f) + teal (#00bcd4) - matches QuickStartWizard
- **Safety:** All operations reversible, no data loss
- **Speed:** Resolve debug row in < 30 seconds

---

## 🔴 YELLOW ROW SCENARIOS (Successful Order)

**Core Issue:** Yellow rows must exist in both Working List AND New Orders

### Y1: Perfect Match
- Working: "Smith Family Medicine, 123 Main St, Austin TX"
- New Orders: "Smith Family Medicine, 123 Main St, Austin TX"
- **Action:** ✅ Show green checkmark

### Y2: Office Name Mismatch (Fuzzy Match Needed)
- Working: "Dr Smith Family Med LLC"
- New Orders: "Smith Family Medicine"
- Address: MATCHES
- **Action:** Show comparison, user confirms, uses fuzzy matching

### Y3: Missing from New Orders
- Yellow in Working List, NOT found in New Orders by office name + address
- **Actions:**
  1. Search by fuzzy office name
  2. Search by address
  3. Show "Add to New Orders" button
  4. Show "False yellow - change status" button
  5. Google search link

### Y4: QTY Mismatch (minor <10%)
- **Action:** Auto-trust New Orders QTY, update Working List

### Y5: QTY Mismatch (major >10%)
- **Action:** FLAG for manual review, show both values

### Y6: Duplicate Yellow Rows
- Same address appears multiple times as yellow
- **Action:** Show all instances, merge tool, "Keep all" option

### Y7: Office Name Changed
- Same address, different names between Working List and New Orders
- **Tools:** Address comparison, Google search, "Update name" button

---

## 💜 FUSCHIA ROW SCENARIOS (Voicemail/No Answer)

### F1: Standard Voicemail
- Notes: "vm 10/5"
- **Tool:** Auto-count VM attempts, suggest "vm x2" → "vm x3"

### F2: Multiple Voicemails
- Notes: "vm 10/1, vm 10/3, vm 10/7"
- **Action:** Consolidate to "vm x3 (last: 10/7)"

### F3: Too Many Attempts (> 3)
- **Action:** Suggest "Clear for future cycle" (removes color, keeps notes)

### F4: QTY > 0 on Fuschia
- **Ambiguity:** Should be yellow or error
- **Tools:** "Convert to yellow + add to New Orders" OR "Clear QTY"

---

## 🔴 RED ROW SCENARIOS (Potentially Invalid)

### R1: Disconnected/Closed
- **Action:** Add to Invalid/Inactive list, Google verify first

### R2: Moved/Relocated
- **Tools:** "Update address" OR "Create new entry"

### R3: Wrong Specialty
- **Action:** Move to Invalid list with specialty note

---

## 🟢 GREEN ROW SCENARIOS (Requested Email)

### G1: Email Sent, Awaiting Response (< 2 weeks)
- **Action:** No change, show days since email

### G2: No Response (> 4 weeks)
- **Action:** Convert to "Not interested"

### G3: Check Gmail
- **Tool:** Button opens Gmail with search filter

---

## 🔍 FUZZY MATCHING ENGINE

### Phone Number Normalization
```javascript
function normalizePhone(phone) {
  const mainPhone = phone.split(/\s*[xX]|ext/i)[0];
  const digitsOnly = mainPhone.replace(/\D/g, '');
  return digitsOnly.slice(-10);
}
```

### Office Name Fuzzy Matching
**Thresholds:**
- ≥ 95%: Auto-match (green checkmark)
- 80-94%: Suggest match (user confirms)
- 60-79%: Possible match (show in results)
- < 60%: Not a match

### Multi-Field Matching (for New Orders validation)
```
Score = (Name Match × 60%) + (Address Match × 40%)
```

**Thresholds:**
- ≥ 85%: High confidence
- 70-84%: Medium confidence (user review)
- < 70%: No match

---

## 🎨 UI LAYOUT

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
│ ┌─────────────────────────┐ │
│ │ 🔍 Google Search        │ │
│ │ ➡️  Next Debug Row        │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

---

## 📊 IMPLEMENTATION PRIORITY

### Phase 1 (CRITICAL - Unblocks EOY automation)
1. **Fix EOY Step 2** - Rewrite fuzzy matching for New Orders (Office Name + Address, NO phone)
2. **Fix network notation** - Use actual network name + count format: "sunlife network (~8);"

### Phase 2 (Core Debug Sidebar)
3. Build sidebar UI (Yellow row repair tools)
4. Auto-clear functions

### Phase 3 (Full Coverage)
5. Fuschia/Red/Green/White repair tools
6. Filter view automation
7. Bulk operations

---

## 🚀 DEPLOYMENT

- Deploy to OBGYN list first (active campaign)
- Test with real data
- Copy to PCP list after verification
