# gspread & Google Sheets API Rate Limits

**Last Updated:** December 2024
**Purpose:** Document rate limits for EOY tool development

---

## Google Sheets API v4 Quotas

**Source:** https://developers.google.com/sheets/api/limits

### Read Requests
- **Per minute per project:** 300
- **Per minute per user:** 60

### Write Requests
- **Per minute per project:** 300
- **Per minute per user:** 60

### Combined (Read + Write)
- **Per day:** 500,000,000 requests

---

## gspread Library Behavior

### Single Operations
- `worksheet.get_all_values()` - **1 read request**
- `worksheet.update('A1:Z100', values)` - **1 write request**
- `worksheet.acell('A1')` - **1 read request**
- `worksheet.update_cell(1, 1, 'value')` - **1 write request**

### Batch Operations (EFFICIENT)
- `worksheet.batch_update([{range, values}, ...])` - **1 write request** (up to 500 updates)
- `worksheet.batch_get([ranges])` - **1 read request** (multiple ranges)

### Multiple Calls (INEFFICIENT)
- Loop calling `update_cell()` 100 times = **100 write requests** ❌
- Use `update()` with range instead = **1 write request** ✅

---

## EOY Tool Expected Usage

### Initial Load (1 time)
- Load Working List (737 rows) - **1 read**
- Load New Orders (269 rows) - **1 read**
- Load Invalid/Inactive List (sample for reasons) - **1 read**
- Load STATS (for formulas) - **1 read**

**Total: 4 reads** (~7 seconds)

### Updates (1 time at end)
- Update Working List (batch, ~150 rows) - **1 write**
- Add to New Orders (if needed, ~5 rows) - **1 write**
- Add to Invalid/Inactive List (~10 rows) - **1 write**
- Create shadow worksheets - **3 writes** (WL_CLEANUP, Invalid_CLEANUP, STATS_CLEANUP)
- Duplicate STATS and update formulas - **1 write**

**Total: 7 writes** (~10 seconds)

### Shadow Worksheet Operations
- Duplicate worksheet - **1 write**
- Update all cells in duplicated worksheet - **1 write** (batch update)
- Update formulas in STATS dupe - **1 write**

---

## Tool Strategy to Stay Under Limits

### Design Decisions
1. **Load all data at start** (4 reads total)
2. **Process in memory** (0 API calls, pure Python)
3. **Batch write at end** (7 writes total)
4. **No real-time sync** (interactive review happens offline)

### Total API Usage Per Run
- **Reads:** 4 (well under 60/min limit)
- **Writes:** 7 (well under 60/min limit)
- **Time:** ~20 seconds total API time

### If Interrupted
- **Progress saved to local JSON** (no API calls)
- **Resume loads from JSON** (0 reads)
- **Only final write uses API** (7 writes)

---

## Rate Limit Safeguards

### Built into gspread
```python
# gspread automatically retries on quota errors
# Default: 3 retries with exponential backoff
# Can customize with:
client = gspread.authorize(creds, retries=5, backoff_factor=2)
```

### Custom Safeguards (if needed)
```python
import time

def safe_batch_update(worksheet, updates, delay=1):
    """
    Batch update with delay between requests
    Only needed if making multiple batch calls in succession
    """
    try:
        worksheet.batch_update(updates)
    except gspread.exceptions.APIError as e:
        if 'Quota exceeded' in str(e):
            print("Rate limit hit, waiting 60s...")
            time.sleep(60)
            worksheet.batch_update(updates)  # Retry
        else:
            raise
    time.sleep(delay)  # Small delay between batches
```

---

## Comparison: EOY Tool vs Manual

### Manual Approach (old)
- Open sheet in browser
- Edit cells one-by-one
- Each edit = 1 write request
- 150 edits = **150 writes** (takes ~30 minutes, ~150 API calls)

### EOY Tool (new)
- Load once, edit in terminal, write once
- Total = **7 writes** (takes ~10 seconds API time)
- **21x more efficient**

---

## Worst Case Scenarios

### Large Campaign (2000 rows)
- Load WL (2000 rows) - **1 read**
- Load NO (500 rows) - **1 read**
- Update WL (500 rows changed) - **1 write**
- **Still under limits**

### Multiple Runs Same Day
- Run 1: 4 reads + 7 writes
- Run 2: 4 reads + 7 writes (resume)
- Run 3: 4 reads + 7 writes (final)
- **Total: 12 reads + 21 writes** (well under 60/min)

### Hit Rate Limit Anyway
- Tool waits 60 seconds
- Retries automatically
- User sees progress bar
- No data loss (everything in memory/JSON)

---

## Daily Quota (500M requests)

**Will never hit this.**

Even if running tool 100 times per day:
- 100 runs × 11 requests = **1,100 requests**
- Daily limit: **500,000,000**
- Usage: **0.0002%**

---

## Recommendations

1. ✅ **Use batch operations** (already planned)
2. ✅ **Load once, write once** (already designed)
3. ✅ **Save progress to JSON** (no API calls)
4. ✅ **No real-time sync needed** (terminal-based)
5. ⚠️ **Add retry logic** for quota errors (use gspread defaults)
6. ⚠️ **Log API calls** for debugging (optional)

---

## Testing Notes

**Test with small data first:**
- Use TEST Working List 2025 (found in sheet list)
- Verify API call count matches expectations
- Check timing (should be ~10-20 seconds total)
- Confirm batch updates work correctly

**Monitor usage:**
- Google Cloud Console → APIs & Services → Quotas
- Check "Sheets API" usage
- Verify staying under 60/min

---

## Conclusion

**EOY tool will use ~11 API calls per run**, well under all limits.

No special rate limiting needed beyond gspread's built-in retry logic.

**Expected performance:**
- Load: 5-7 seconds
- Process: 0 API calls (in memory)
- Write: 5-10 seconds
- **Total API time: 10-17 seconds**

User review time (2-4 hours) uses **0 API calls**.
