# Test Data for JGDC EOY Automation

This directory contains test data and testing utilities for the JGDC healthcare provider outreach system.

## Files

### `obgyn-test-samples.csv`
Real edge cases extracted from OBGYN Working List 2025 export, plus synthetic edge cases.

**Contains 22 test cases covering:**
- ✅ Not Interested with proper notes + QTY=0
- ❌ Not Interested missing "not interested" in notes
- ❌ Not Interested with wrong QTY (not 0)
- ✅ Yellow rows (Successful Order)
- ⚠️ Yellow row with conflicting "not interested" note
- ✅ Voicemail/No Answer with empty QTY
- ✅ Potentially Invalid (red status)
- ✅ Requested Email (green status)
- ❌ Missing address field
- ✅ Phone extensions (x123)
- ✅ Phone format variations (parens, dots, dashes, none)
- 🔄 Network detection (same name, same phone, different addresses)
- 🔄 Fuzzy network matching ("Muth And Weber" vs "Muth & Weber")
- 🔄 Duplicate phone but different practices
- ⚪ Empty status
- ⚪ Mixed empty/zero QTY columns
- ⚪ Completely empty row

### `similarity-test.js`
Tests the `calculateSimilarity()` function with real office name variations.

**Run with:** `node similarity-test.js`

**Results:**
- Threshold 0.85: 100% accuracy (10/10 correct)
- Threshold 0.90: 80% accuracy (missed "& vs and" variations)

**Recommendation:** Use 0.85 threshold for network detection.

## Usage in Unit Tests

Import these samples in your unit tests:

```javascript
const fs = require('fs');
const csv = require('csv-parse/sync');

const testData = fs.readFileSync('./test-data/obgyn-test-samples.csv', 'utf8');
const records = csv.parse(testData, { columns: true });

// Filter by edge case type
const notInterestedIssues = records.filter(r =>
  r['Edge Case'].includes('Not Interested')
);

const networkCases = records.filter(r =>
  r['Edge Case'].includes('Network')
);
```

## Real Data Source

Edge cases extracted from:
- `data/exports/OBGYN List 2025 - Use This List! - Working List 2025.csv`
- 485 real providers from OBGYN outreach campaign

## Edge Case Categories

### Category 1: "Not Interested" Validation
- **Should pass:** QTY=0, notes include "not interested"
- **Should fail:** QTY≠0, missing "not interested" in notes

### Category 2: Yellow → New Orders Validation
- **Should pass:** Yellow rows exist in New Orders with matching phone+QTY
- **Should fail:** Yellow rows missing from New Orders, QTY mismatch

### Category 3: Duplicate Detection
- **Networks (auto-note):** Same/similar name, same phone, different addresses
- **Duplicates (flag only):** Same phone but different practices

### Category 4: Phone Normalization
- **Should all normalize to same 10 digits:**
  - `(562) 595-7729`
  - `562.595.7729`
  - `562-595-7729`
  - `5625957729`
  - `(562) 595-7729 x123` → `5625957729` (extension removed)

### Category 5: Missing Data
- Missing address
- Empty status
- Mixed empty/zero QTY

### Category 6: Status-Based Review
- Red: Move to invalid list or re-verify
- Fuschia: Triple follow-up, leave empty (not 0)
- Green: Follow up or mark not interested if old
- Empty: Leave for next year

## Known Issues to Test

1. **Phone extension corruption bug** (FIXED)
   - Before: `(555) 123-4567 x123` → `1234567123` ❌
   - After: `(555) 123-4567 x123` → `5551234567` ✅

2. **Network detection false negatives** (FIXED with fuzzy matching)
   - Before: "Muth And Weber" vs "Muth & Weber" → Not detected
   - After: Fuzzy match at 0.85 threshold → Detected ✅

3. **Multi-state filter** (FIXED)
   - Before: Processes all states regardless of config
   - After: Only processes states in TARGET_STATES array ✅

## Test Coverage Goals

- [ ] Phone normalization: 100% of format variations
- [ ] Network detection: 100% accuracy (0 false positives, 0 false negatives)
- [ ] Not Interested validation: All edge cases caught
- [ ] Yellow/Orders validation: Cross-sheet matching works
- [ ] Fuzzy name matching: Threshold 0.85 performance verified
- [ ] State filtering: Only target states processed
- [ ] Extension handling: No data corruption

## Adding New Test Cases

When you encounter a new edge case in production:

1. Add row to `obgyn-test-samples.csv`
2. Document in "Edge Case" column
3. Update this README with the category
4. Write unit test to cover it
5. Fix code if needed
6. Re-run all tests
