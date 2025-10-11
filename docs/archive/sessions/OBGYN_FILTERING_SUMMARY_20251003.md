# OBGYN Filtering Summary - October 3, 2025

## Execution Summary

**Script:** nppes_filter_pcps.py v3.0
**Provider Type:** OBGYN
**Target States:** TX, WA, CO, PA
**Execution Date:** 2025-10-03
**Mode:** Production (DRY_RUN = False)

---

## Input Data

- **Source File:** npidata_pfile_20050523-20250907.csv
- **Total Records Loaded:** 9,129,558

---

## Filtering Pipeline Results

| Stage | Description | Count | Excluded |
|-------|-------------|-------|----------|
| 1. Initial Load | All NPPES records | 9,129,558 | - |
| 2. Active NPIs | Removed deactivated | 8,793,531 | 336,027 |
| 3. OBGYN Taxonomy | Strict OBGYN codes only | 73,858 | 8,719,673 |
| 4. State Filter | TX, WA, CO, PA only | 12,101 | 61,757 |
| 5. Organizations | Independent clinics only | 9,281 | 2,820 |
| 6. Required Fields | Phone + Address present | 9,281 | 0 |
| 7. Deduplication | Remove duplicates | 9,223 | 58 |

**Total Excluded:** 9,120,335 providers

---

## Smart Sampling (NEW - API Efficiency)

To optimize Google Places API usage and achieve target verified counts:

| State | Filtered Pool | Sample Size | Target Verified | Expected Success Rate |
|-------|---------------|-------------|-----------------|----------------------|
| TX | 4,315 | **300** | 200+ | ~70% |
| WA | 1,276 | **60** | 40+ | ~70% |
| CO | 1,117 | **60** | 40+ | ~70% |
| PA | 2,515 | **60** | 40+ | ~70% |
| **TOTAL** | **9,223** | **480** | **320+** | **~70%** |

**Sampling Method:** Random selection (seed=42 for reproducibility)

---

## Output Files Generated

### Filtered Provider Lists (Ready for Verification)
- `FILTERED_obgyns_TX_20251003.csv` - 300 providers (25 KB)
- `FILTERED_obgyns_WA_20251003.csv` - 60 providers (4.7 KB)
- `FILTERED_obgyns_CO_20251003.csv` - 60 providers (4.9 KB)
- `FILTERED_obgyns_PA_20251003.csv` - 60 providers (5.0 KB)
- `FILTERED_obgyns_ALL_20251003.csv` - 480 providers combined (39 KB)

### Audit Trail
- `EXCLUDED_FILTERED_obgyns_20251003.csv` - 9.1M excluded records (523 MB)

---

## API Usage Projection

| Metric | Value | Status |
|--------|-------|--------|
| **Providers to verify** | 480 | - |
| **API calls needed** | 480 | Within budget |
| **Current API limit** | 3,000/month | Safe |
| **Usage percentage** | 16% | ✅ Excellent |
| **Remaining capacity** | 2,520 calls | ✅ Buffer available |

---

## Data Quality Features Applied

### Capitalization Fixes (5 types)
1. **ALL CAPS → Title Case:** MARY SMITH MD → Mary Smith MD
2. **Mc/Mac Names:** MCDONALD → McDonald, MACGREGOR → MacGregor
3. **Apostrophes:** O'DONNELL → O'Donnell
4. **Credentials:** M.D. → MD, D.O. → DO (standardized)
5. **Suffixes:** JR → Jr, SR → Sr, III → III

### Organization Validation
- **Included:** Independent OBGYN clinics with "clinic", "center", "practice" indicators
- **Excluded:** Hospitals, health systems, medical groups, imaging centers, labs
- **Deduplication:** Prefer individual providers over clinics at same address

### Required Fields
- Valid phone number
- Complete practice address
- Active NPI status

---

## Taxonomy Codes Used

```
207V00000X - Obstetrics & Gynecology
207VX0000X - Obstetrics
207VG0400X - Gynecology
207VX0201X - Maternal & Fetal Medicine
```

---

## Next Steps

### Immediate (Ready to Execute)
1. **Import to Google Sheets**
   - Create new sheet: "OBGYN Verification Input"
   - Import `FILTERED_obgyns_ALL_20251003.csv` OR individual state files
   - Verify column mapping

2. **Run Google Places API Verification**
   - Menu: Provider Verification → Start Processing
   - Expected runtime: ~20-30 minutes (480 providers ÷ 25/batch = 20 batches)
   - **Monitor API usage** via "View API Usage" menu item
   - Output sheets:
     - `nppes_obgyn_verified` - Operational providers (~336 expected)
     - `nppes_obgyn_errors` - Failed verification
     - `nppes_obgyn_review` - Manual review queue

3. **Quality Check Verified Results**
   - Confirm TX ≥ 200 verified-operational
   - Confirm WA, CO, PA ≥ 40 each
   - Review any providers in manual review queue

### Follow-up (After Verification)
4. **Export to Working List**
   - Copy verified providers to "OBGYN Working List 2025"
   - Apply formatting and status columns
   - Begin calling campaign

5. **Test EOY Automation**
   - Once OBGYN list has activity, test new EOY workflow
   - Menu: Misc. Tools → End-of-Year Workflow → Audit

---

## Configuration Changes

### Python Script Updates
- `PROVIDER_TYPE`: 'PCP' → **'OBGYN'**
- `TARGET_STATES`: ['OK','OR','TN'] → **['TX', 'WA', 'CO', 'PA']**
- `OUTPUT_PREFIX`: 'FILTERED_pcps' → **'FILTERED_obgyns'**
- **NEW:** `STATE_SAMPLE_LIMITS` dictionary added
- `DRY_RUN`: True → **False**

### Apps Script Updates (Already Deployed)
- **UniversalProviderSuite.js (v8.0)**
  - Added API_CALL_LIMIT: 3000
  - Added API_WARNING_THRESHOLD: 2800
  - Enhanced pre-flight and in-flight safety checks
  - Improved showApiUsage() with status indicators

- **ToolboxSuite.js (v10.0)**
  - Complete EOY automation suite (6 validation steps)
  - Hidden Debug/Issues column for flagged items
  - Yellow → New Orders validation
  - Not Interested rule enforcement
  - Duplicate detection (flag only)
  - Status-based review categorization

---

## Notes & Observations

### Filtering Efficiency
- **9.1M → 480 providers** (99.99% reduction)
- Very strict OBGYN taxonomy filtering (only 73K in entire US)
- Organization validation excluded 2,820 of 3,001 (94% rejection rate)
- Minimal duplicates found (58 out of 9,223 = 0.6%)

### Geographic Distribution
- **TX dominates:** 4,315 OBGYNs (47% of target states' total)
- **PA second:** 2,515 OBGYNs (27%)
- **WA third:** 1,276 OBGYNs (14%)
- **CO smallest:** 1,117 OBGYNs (12%)

### API Efficiency
- Smart sampling reduced API calls by **95%** (9,223 → 480)
- Maintains statistical diversity via random sampling
- Allows for buffer if verification rate is lower than expected
- Leaves 2,520 API calls available for future campaigns

---

## File Locations

**Input:**
```
C:\Users\noagi\Desktop\JGDC\data\nppes\NPPES_Data_Dissemination_September_2025_V2\npidata_pfile_20050523-20250907.csv
```

**Output:**
```
C:\Users\noagi\Desktop\JGDC\data\nppes\NPPES_Data_Dissemination_September_2025_V2\
├── FILTERED_obgyns_TX_20251003.csv
├── FILTERED_obgyns_WA_20251003.csv
├── FILTERED_obgyns_CO_20251003.csv
├── FILTERED_obgyns_PA_20251003.csv
├── FILTERED_obgyns_ALL_20251003.csv
└── EXCLUDED_FILTERED_obgyns_20251003.csv
```

**Script:**
```
C:\Users\noagi\Desktop\JGDC\data\nppes\NPPES_Data_Dissemination_September_2025_V2\nppes_filter_pcps.py
```

---

## Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| TX verified-operational | ≥ 200 | ⏳ Pending verification |
| WA verified-operational | ≥ 40 | ⏳ Pending verification |
| CO verified-operational | ≥ 40 | ⏳ Pending verification |
| PA verified-operational | ≥ 40 | ⏳ Pending verification |
| API calls used | < 3,000 | ✅ 480 projected (16%) |
| Zero duplicates shipped | 100% | ✅ Deduplication applied |
| Clean data format | 100% | ✅ 5-type capitalization fix |

---

*Generated: 2025-10-03*
*Script Version: nppes_filter_pcps.py v3.0 (OBGYN mode)*
*Estimated verification completion: ~30 minutes after import*
