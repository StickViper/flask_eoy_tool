# Google Maps Platform Quota Changes - March 2025

**Last Updated:** October 18, 2025
**Applies To:** UniversalProviderSuite.js (Google Places API usage)
**Impact:** FREE TIER INCREASED (good news!)

---

## TL;DR

✅ **GOOD NEWS:** Free tier INCREASED from ~2,857 calls/month to 10,000 calls/month
✅ This project's current 3,000 call limit is now well under the free tier
⚠️ Need to understand SKU categories to verify we're using "Essentials" tier

---

## What Changed on March 1, 2025

### Old System (Before March 1, 2025)

**Monthly Credit Model:**
- $200 USD monthly recurring credit
- Applied across all Google Maps Platform services
- Text Search (Places API New): $17 per 1,000 calls
- Effective free calls: ~2,857 per month ($200 / $17 * 1000 ≈ 11,765 calls, but shared across all services)

### New System (After March 1, 2025)

**Per-SKU Free Usage Model:**
- Free usage varies by SKU category
- **Essentials SKUs:** 10,000 free monthly calls
- **Pro SKUs:** 5,000 free monthly calls
- **Enterprise SKUs:** 1,000 free monthly calls
- Each service tracked separately (not pooled)

---

## Places API (New) - What We Use

### Current Implementation

**API:** Places API (New) - Text Search
**Endpoint:** `https://places.googleapis.com/v1/places:searchText`
**File:** `scripts/provider-search/UniversalProviderSuite.js`
**Usage Pattern:** Batch verification of NPPES provider data

### SKU Category (Needs Verification)

**Question:** Which SKU category does Text Search fall under?

**Likely:** Essentials (10,000 free calls)
- Text Search is basic functionality
- Closest to legacy Places API Text Search
- Blog post mentions "up to 10,000 monthly free calls per product"

**Need to Confirm:** Check Google Cloud Console → Billing → SKUs

### Current vs. New Limits

| Aspect | Old System | New System (Essentials) | Impact |
|--------|------------|------------------------|--------|
| Free Tier | ~2,857 calls* | 10,000 calls | +250% increase |
| This Project's Limit | 3,000 calls | 3,000 calls | Now fully free! |
| Overage Cost | $17 / 1,000 | $17 / 1,000** | Same |
| Volume Discounts | 100K+ usage | 5M+ usage | Better scaling |

*Approximate, shared across services
**Assumes Essentials tier, verify in console

---

## Impact on This Project

### Current Usage Pattern

**Typical Campaigns:**
- OBGYN (Oct 2025): ~465 expected calls (TX, WA, CO, PA)
- PCP (Oct 2025): ~300 expected calls (NM, UT, NE, AL)
- **Total:** ~765 calls for current campaigns

**Hard Limit:**
- Self-imposed: 3,000 calls/month
- Warning threshold: 2,800 calls
- Safety margin: 200 calls

### With New Quota (10,000 free/month)

**New Reality:**
- Current usage (~765 calls): 7.7% of free tier
- Self-imposed limit (3,000): 30% of free tier
- **Recommendation:** Consider raising limit to 5,000-8,000 calls

**Benefits:**
- More aggressive filtering (larger sample sizes)
- Multiple state campaigns per month without worry
- Buffer for testing/development

---

## Action Items

### Immediate (October 2025)

- [ ] Verify SKU category in Google Cloud Console
  1. Go to: https://console.cloud.google.com
  2. Billing → Reports → Filter by "Places API (New)"
  3. Check SKU name (should mention "Essentials", "Pro", or "Enterprise")
  4. Confirm free tier amount matches expectation (10,000)

- [ ] Update API usage tracking code (if needed)
  - Current hard limit: 3,000 calls
  - Consider: Increase to 8,000 calls (80% of free tier)
  - Update warning threshold: 7,500 calls

- [ ] Document actual SKU category
  - Update this file with confirmed SKU
  - Update SYSTEM_PROPERTIES.md if tracking logic changes

### Future Enhancements

- [ ] Auto-reset counter on billing cycle
  - Track last reset date in ScriptProperties
  - Auto-reset monthly (or warn user)

- [ ] Better usage analytics
  - Track calls per campaign
  - Success rate vs. API usage
  - Monthly usage trends

- [ ] Dynamic limit adjustment
  - Read free tier limit from API (if available)
  - Adjust warnings based on actual quota

---

## Legacy vs. New Places API

### Why This Matters

**Legacy Places API:**
- Old endpoint: `https://maps.googleapis.com/maps/api/place/textsearch/json`
- Designated "Legacy" as of March 2025
- Limited volume discounts (100K+ only)
- No new feature development
- **Status:** We don't use this (good!)

**Places API (New):**
- New endpoint: `https://places.googleapis.com/v1/places:searchText`
- Active development
- Better volume discounts (5M+ scaling)
- 10,000 free calls/month (Essentials)
- **Status:** We use this ✅

**Implication:** We're already using the recommended API, no migration needed.

---

## Volume Discounts (For Future Scale)

### Pricing Tiers (Essentials SKU)

| Monthly Usage | Cost per 1,000 | Effective Cost |
|---------------|----------------|----------------|
| 0 - 10,000 | $0 | FREE |
| 10,001 - 100,000 | $17.00 | $17/1K |
| 100,001 - 500,000 | $13.60 | $13.60/1K (20% discount) |
| 500,001 - 5,000,000 | $10.88 | $10.88/1K (36% discount) |
| 5,000,001+ | $8.16 | $8.16/1K (52% discount) |

**Example:** 50,000 calls/month
- First 10,000: FREE
- Next 40,000: $680 (40 × $17)
- **Total:** $680/month

**Current Project:** Never exceeds 3,000 calls → Always FREE

---

## Billing Cycle Tracking

### Current System

**Problem:** Don't know when Google's billing month starts

**Current Approach:**
- Assume monthly reset on 1st of month
- Manual reset via menu when month changes
- No automated tracking

**Risks:**
- Forget to reset → Inaccurate tracking
- Billing month doesn't match calendar month → Over/under count

### Recommended Fix

**Add to ScriptProperties:**
```javascript
// New properties to track
'billingCycleStart': '2025-10-01',  // ISO date of current billing period
'lastApiReset': '2025-10-01',       // Last time counter was reset
```

**Auto-reset logic:**
```javascript
function checkAndResetIfNeeded() {
  const props = PropertiesService.getScriptProperties();
  const lastReset = props.getProperty('lastApiReset');

  if (!lastReset) {
    // First time, ask user for billing cycle start
    return;
  }

  const lastResetDate = new Date(lastReset);
  const now = new Date();

  // If more than 30 days since reset, warn user
  const daysSinceReset = (now - lastResetDate) / (1000 * 60 * 60 * 24);

  if (daysSinceReset > 30) {
    const ui = SpreadsheetApp.getUi();
    const response = ui.alert(
      'API Counter Reset Needed?',
      `It's been ${Math.floor(daysSinceReset)} days since last reset.\n\n` +
      `Current count: ${getApiCallCount()}\n\n` +
      `Reset counter for new billing month?`,
      ui.ButtonSet.YES_NO
    );

    if (response === ui.Button.YES) {
      props.setProperty('apiCallCount', '0');
      props.setProperty('lastApiReset', now.toISOString().split('T')[0]);
    }
  }
}
```

**Future TODO:** Implement this logic in UniversalProviderSuite.js

---

## Comparison with Other APIs

### Google Maps Platform Services

| Service | Essentials Free Tier | Pro Free Tier |
|---------|---------------------|---------------|
| Places API (New) - Text Search | 10,000 | 5,000 |
| Geocoding API | 10,000 | 5,000 |
| Maps JavaScript API | 10,000 dynamic loads | 5,000 |
| Routes API | 10,000 | 5,000 |

**Note:** Each service has separate free tier (not pooled)

**Implication:** If we ever add Geocoding (to validate addresses), we get another 10,000 free calls/month.

---

## FAQ

### Q: Do I need to do anything to get the new free tier?

**A:** No, it automatically applied on March 1, 2025. If your billing account was active before March 1, you automatically transitioned to the new system.

### Q: Is our current 3,000 call limit still valid?

**A:** Yes, but it's conservative. With 10,000 free calls, you could safely increase to 5,000-8,000 if needed.

### Q: What happens if we exceed 10,000 calls?

**A:** You'll be charged $17 per 1,000 additional calls (Essentials tier). Example: 11,000 calls = $17 charge.

### Q: Do we need to migrate from Places API to Places API (New)?

**A:** No, we're already using Places API (New). No migration needed.

### Q: Can we use the old $200 credit approach?

**A:** No, that system ended February 28, 2025. New per-SKU free tier is automatic.

### Q: How do I check my current billing/usage?

**A:** Google Cloud Console → Billing → Reports → Filter by "Places API (New)"

### Q: What if we need more than 10,000 calls/month?

**A:** You'll pay for overage, but with volume discounts:
- 50K calls/month: ~$680/month
- 100K calls/month: ~$1,530/month
- (Still free tier for first 10K)

---

## Recommendations

### Short-Term (October-December 2025)

1. ✅ **Verify SKU category** in Google Cloud Console
2. ✅ **Keep current 3,000 limit** (conservative, safe)
3. ✅ **Document billing cycle start date** (when does your month reset?)
4. ✅ **Monitor actual usage** for 2-3 months to establish baseline

### Medium-Term (Q1 2026)

1. **Consider increasing limit to 5,000-8,000 calls**
   - Current usage (~750/month) well under even conservative 3K limit
   - New free tier (10K) provides much more headroom
   - Allows larger campaigns or multiple simultaneous campaigns

2. **Implement auto-reset reminder**
   - Check days since last reset
   - Warn user when >30 days
   - Prevent accidental quota tracking errors

3. **Add usage analytics**
   - Calls per campaign
   - Success rate tracking
   - Month-over-month trends

### Long-Term (2026+)

1. **Dynamic quota management**
   - Read actual free tier from billing API (if available)
   - Adjust limits automatically
   - Handle quota changes without code updates

2. **Campaign planning tool**
   - Input: Expected providers to verify
   - Output: Estimated API calls needed
   - Check: Available quota remaining this month

---

## References

- [Google Maps Platform March 2025 Changes](https://developers.google.com/maps/billing-and-pricing/march-2025)
- [Places API (New) Pricing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)
- [Core Services Pricing List](https://developers.google.com/maps/billing-and-pricing/pricing)

---

**Last Updated:** October 18, 2025
**Next Review:** January 2026 (after 3 months of new billing system)

**Action Required:** Verify SKU category in Google Cloud Console
