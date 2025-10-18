# Deduplication Workflow - Complete Strategy

## Overview
This document explains how deduplication works across the entire provider verification workflow, from Python filtering through Google Sheets processing.

---

## Stage 1: Python Filter (NPPES → CSV)
**File:** `data/nppes/NPPES_Data_Dissemination_September_2025_V2/nppes_filter_pcps.py`

### Strategy: One Provider Per Phone
**Function:** `deduplicate_providers()` (lines 522-584)

**Logic:**
1. Group all providers by normalized phone number (last 10 digits, no extensions)
2. For each phone group:
   - If only 1 provider → keep it
   - If multiple providers (network detected):
     - **Prefer individuals over organizations**
     - Keep the **FIRST** individual (Entity Type 1) if any exist
     - Otherwise keep the **FIRST** organization (Entity Type 2)
     - Mark ALL others as excluded

**Example:**
```
Input: 5 providers with phone (555) 123-4567
- Dr. Smith (individual) at 123 Main St
- Dr. Jones (individual) at 456 Oak Ave
- Sun Life Family Practice (org) at 789 Elm St
- Sun Life Medical Group (org) at 321 Pine Rd
- Sun Life Health Center (org) at 654 Maple Dr

Output: Keep Dr. Smith (first individual)
Excluded: Dr. Jones, Sun Life Family Practice, Sun Life Medical Group, Sun Life Health Center
Reason: "Duplicate phone: network with 5 locations"
```

**Result:** CSV contains ONE provider per unique phone number (~30K providers instead of 50K)

---

## Stage 2: Import to Google Sheets
**Action:** Import CSV to `PCP_TX_import` sheet (or state-specific import sheet)

**What happens:**
- No deduplication yet - just import the pre-filtered data
- Each row represents ONE unique phone number

---

## Stage 3: Provider Verification (API Calls)
**File:** `scripts/provider-search/UniversalProviderSuite.js`

### Deduplication: Safety Check Only
**Function:** `findAndRemoveDuplicates()` (lines 1232-1268)

**Logic:**
- Groups by `phone` OR `API_Place_ID`
- Keeps first occurrence, deletes ALL subsequent matches
- **Purpose:** Catch any duplicates that slipped through (shouldn't happen if Python filter worked)

**When to use:** After verification completes, run this as a safety check

**Expected result:** Should find 0 duplicates if Python filter worked correctly

---

## Stage 4: Network Detection in Sheets
**File:** `scripts/pcp-list/ToolboxSuite.js` (or `obgyn-list/ToolboxSuite.js`)

### Strategy: Flag Networks, Don't Delete
**Function:** `detectAndFlagDuplicates()` (lines 956-1055)

**Logic:**
1. Group providers by phone number
2. For each phone group with multiple providers:
   - Compare office names using fuzzy matching (≥85% similarity)
   - If similar names + same phone + different addresses → **network detected**
   - Add note: `"sunlife network (~8);"` (network name + location count)
   - Add Debug/Issues flag: `"Same network (8 locations, 1 phone)"`

**Important:** This does NOT delete anything - it only adds informational notes

**Example:**
```
Working List 2025 has these rows:
Row 50: Dr. Smith at Sun Life - Tampa
Row 120: Sun Life Family Practice - Orlando  (already in sheet from previous year)

When you import NEW providers from NPPES:
- Python kept Dr. Smith (first individual for phone 555-1234)
- Excluded Sun Life Family Practice (duplicate phone)

When you run detectAndFlagDuplicates():
- Detects: Row 50 (Dr. Smith) + Row 120 (Sun Life) have same phone
- Adds to Row 50: Notes = "sunlife network (~2);"
- Adds to Row 120: Notes = "sunlife network (~2);"
- Flags both in Debug/Issues: "Same network (2 locations, 1 phone)"
```

**Purpose:** Helps you identify which providers are part of multi-location networks for context during outreach

---

## Verification with Network Detection

### Enhanced Confidence Scoring
**File:** `scripts/provider-search/UniversalProviderSuite.js` (lines 493-577)

**Proposed Enhancement (Q4 implementation):**

When a provider is flagged as part of a network (3+ locations), reduce confidence score to push it into Manual Review:

```javascript
// After line 565 (business type penalty)

// Network penalty (for multi-location practices)
// Check if this provider was flagged as part of a network
const notesCol = headers.indexOf('Notes');
if (notesCol !== -1) {
  const notes = (rowData[notesCol] || '').toString().toLowerCase();
  const networkMatch = notes.match(/network \(~(\d+)\)/);

  if (networkMatch) {
    const networkSize = parseInt(networkMatch[1]);

    if (networkSize >= 3) {
      // Networks with 3+ locations get moderate penalty
      points -= 10;
      result.notes = (result.notes ? result.notes + '; ' : '') +
                     `Part of ${networkSize}-location network (needs manual review)`;
    }
  }
}

result.confidence = Math.max(0, points / maxPoints);
```

**Effect:**
- Single location: No penalty (85%+ confidence = auto-verify)
- 2-location network: No penalty
- 3+ location network: -10 points penalty
  - Example: 90% → 80% (drops below 85% threshold → Manual Review)

---

## Complete Workflow Summary

### Step 1: Python Filter
```
Input: 9.1M NPPES records
↓ Filter by taxonomy, state, organization type
↓ Deduplicate: ONE per phone
Output: ~30K unique providers → FILTERED_pcps_FL.csv
```

### Step 2: Import to Sheets
```
FILTERED_pcps_FL.csv → PCP_TX_import sheet
All providers have unique phone numbers (no duplicates yet)
```

### Step 3: Run Verification
```
UniversalProviderSuite.js → verifyPlace()
Calls Google Places API for each provider
Outputs to: All_Verified_Providers sheet

If network detected (Notes contains "network (~X)"):
  - Apply -10 point penalty for networks ≥3 locations
  - Pushes to Manual Review Queue
```

### Step 4: Network Detection (EOY Workflow)
```
detectAndFlagDuplicates() from ToolboxSuite.js
Compares IMPORT data with EXISTING Working List data
Flags any shared phone numbers as networks
Adds notes: "sunlife network (~8);"
Does NOT delete anything
```

### Step 5: Manual Review
```
Review networks manually:
- Single provider = call normally
- 2-location network = call normally
- 3+ location network = manual decision (centralized? franchises?)
```

---

## Configuration Changes Made

### Updated: `nppes_filter_pcps.py`
**Line 522-584:** Changed deduplication strategy from "phone + address" to "phone only"
- **Old:** Kept all individuals at same phone+address
- **New:** Keeps ONE provider per phone (prefer individual over org)

### Recommendation: Update `UniversalProviderSuite.js`
**Add after line 565:** Network penalty logic (see code above)
- Detects "network (~X)" in Notes column
- Applies -10 penalty for networks ≥3 locations
- Forces Manual Review for large networks

---

## Testing Plan

1. **Re-run Python filter** with new deduplication logic
   - Expected: ~30K providers (down from 50K)
   - Verify: No duplicate phones in output CSV

2. **Import to Sheets** and run verification
   - Expected: ~7.5K verified (25% success rate)
   - Check: "sunlife network" notes appear for multi-location practices

3. **Run detectAndFlagDuplicates()** after importing new data
   - Expected: Flags any networks that span old + new data
   - Check: Debug/Issues column shows "Same network" messages

4. **Manual Review Queue**
   - Expected: Large networks (3+ locations) appear in review queue
   - Verify: Confidence scores are reduced for networks

---

## Questions Answered

✅ **Q1:** Which 20K duplicates did Sheets find?
- **A:** UniversalProviderSuite's `findAndRemoveDuplicates()` found them (phone OR placeId matching)

✅ **Q2:** What deduplication strategy do you want?
- **A:** Keep one per phone (now implemented in Python)

✅ **Q3:** Should Python filter be more aggressive?
- **A:** Yes - now keeps ONLY ONE individual per phone

✅ **Q4:** What about networks? One rep or keep all?
- **A:** One rep (Python), but flag networks in Sheets for context. Networks ≥3 locations → Manual Review.

---

## Future Enhancements

### Option 1: Add network info to CSV during Python filtering
Add column to output CSV with network size info:
```python
output_df['Network_Size'] = df['_network_size']  # Track how many were grouped
```

### Option 2: Smarter network representative selection
Instead of "first individual", choose based on:
- Highest patient volume (if available)
- Main/corporate office (if indicated in name)
- Most complete contact information

### Option 3: Network-specific outreach strategy
When calling a network representative:
- Script: "I see you have X locations..."
- Ask: "Which location handles genetic testing/patient referrals?"
- Update notes with centralized decision info
