# Filtering & Verification Improvements - Brainstorm

**Date:** 2025-10-11
**Context:** Discovered dermatologist passed as PCP with 96% confidence

---

## 🔴 CRITICAL: Verification Stage (Google Places API)

### Current Problem
Verification only checks: name similarity + phone match + operational status
**NO specialty checking** → False positives (dermatologists, dentists, vets pass as PCPs)

### Solution 1: Business Type Checking (Google Places API)
**Use `place.types` or `place.primaryType` field**

**Whitelist approach (strict):**
```javascript
const ALLOWED_TYPES = [
  'doctor',
  'health',
  'medical_clinic',
  'primary_care_doctor',
  'general_practitioner'
];

// Must have at least one allowed type
const hasAllowedType = place.types.some(t => ALLOWED_TYPES.includes(t));
if (!hasAllowedType) {
  points -= 40; // Heavy penalty
}
```

**Blacklist approach (permissive):**
```javascript
const EXCLUDED_TYPES = [
  'dentist',
  'veterinary_care',
  'physiotherapist',
  'chiropractor',
  'dermatologist',  // May not exist in API, need testing
  'eye_doctor',
  'optometrist',
  'pharmacy',
  'hospital',
  'urgent_care',
  'beauty_salon',
  'spa'
];

const hasExcludedType = place.types.some(t => EXCLUDED_TYPES.includes(t));
if (hasExcludedType) {
  points -= 40;
  result.notes = `Wrong specialty: ${place.types.join(', ')}`;
}
```

**RECOMMENDED:** Blacklist approach (more flexible, catches obvious wrong specialties)

**TODO:** Test what Google Places API returns for known dermatologists/dentists

---

## 🟡 MEDIUM: Python Filtering Stage (NPPES)

### Current System
**Taxonomy whitelisting only** - works well but has edge cases:
- Providers with outdated taxonomy codes
- Providers who switched specialties
- Multi-specialty providers with wrong primary taxonomy

### Improvement 1: Organization Name Blacklist (Already exists but could expand)

**Current blacklist patterns (line 96-106 in nppes_filter_pcps.py):**
```python
'EXCLUDE_ORG_PATTERNS': [
    'cardiology', 'oncology', 'dermatology', 'orthopedic', 'neurology',
    'pediatric', 'pediatrics', 'children', "children's", 'kids health',
    # etc.
]
```

**Suggested additions:**
```python
ADDITIONAL_EXCLUDE_PATTERNS = [
    # Specialty clinics
    'allergy', 'asthma', 'diabetes', 'endocrinology',
    'gastro', 'nephrology', 'rheumatology', 'pulmonary',
    'infectious disease', 'hematology',

    # Surgical/procedural
    'surgery', 'surgical', 'endoscopy', 'colonoscopy',
    'laser', 'aesthetic', 'cosmetic', 'plastic surgery',

    # Mental health (unless you want psychiatrists)
    'behavioral health', 'mental health', 'psychiatry', 'psychology',

    # Therapy/rehab
    'physical therapy', 'occupational therapy', 'speech therapy',
    'rehab', 'rehabilitation', 'chiropractic',

    # Imaging/diagnostics
    'radiology', 'imaging center', 'mri', 'ct scan', 'x-ray',
    'lab', 'laboratory', 'diagnostics',

    # Alternative medicine
    'acupuncture', 'naturopathic', 'homeopathic', 'holistic',

    # Dental/vision
    'dental', 'dentistry', 'orthodontic', 'oral surgery',
    'optometry', 'ophthalmology', 'vision', 'eye care',

    # Other non-PCP
    'urgent care', 'walk-in', 'minute clinic', 'retail clinic',
    'occupational health', 'travel medicine', 'sports medicine',
    'wound care', 'pain management', 'sleep', 'bariatric'
]
```

**Risk:** May over-filter if provider has multi-specialty group practice name

---

### Improvement 2: Individual Provider Name Filtering

**Currently:** `NAME_PATTERN_FILTER` exists but is DISABLED (line 117)

**Activate with caution:**
```python
'NAME_PATTERN_FILTER': {
    'ENABLED': True,  # ⚠️ Test first!
    'RISK_THRESHOLD': 'HIGH',  # Only exclude obvious specialists
}
```

**Add dermatology/dental patterns:**
```python
'HIGH_RISK_PATTERNS': [
    # Current patterns
    'hospital', 'medical center', 'emergency', 'urgent care',
    'pediatric', 'children', "children's", 'student health',
    'cardiology', 'oncology', 'surgery', 'surgical',

    # NEW: Add these
    'dermatology', 'dermatologist', 'skin care', 'skin clinic',
    'dental', 'dentist', 'orthodontic', 'dds', 'dmd',
    'veterinary', 'animal hospital', 'vet clinic',
    'chiropractic', 'chiropractor',
    'optometry', 'optometrist', 'eye doctor', 'vision center',
    'podiatry', 'podiatrist', 'foot care',
]
```

**Risk:** Individual providers might have generic "Family Practice of [City]" names that don't indicate specialty

---

### Improvement 3: Taxonomy Code Secondary Check

**Currently:** Only checks taxonomy codes 1-3 (primary classifications)

**NPPES has up to 15 taxonomy codes per provider!**

**Improvement:**
```python
def has_specialist_taxonomy(row):
    """Check if ANY taxonomy code indicates non-PCP specialty."""
    specialist_codes = [
        '207N00000X',  # Dermatology
        '207W00000X',  # Ophthalmology
        '122300000X',  # Dentist
        '174400000X',  # Specialist
        # ... add more
    ]

    # Check all 15 taxonomy slots
    for i in range(1, 16):
        col = f'Healthcare Provider Taxonomy Code_{i}'
        if row.get(col) in specialist_codes:
            return True
    return False
```

**Exclude if:** Primary is PCP but secondary is specialist (likely multi-specialty group)

---

## 🟢 LOW: Post-Verification Stage (Working List)

### Improvement 4: "Check if Invalid" Tool Enhancement

**Currently:** Fuzzy matches against Invalid/Inactive List (ToolboxSuite.js)

**Add specialty keywords blacklist:**
```javascript
function checkForSpecialtyKeywords(officeName) {
  const specialtyPatterns = [
    /dermatology/i, /skin\s+care/i,
    /dental/i, /orthodontic/i,
    /veterinary/i, /animal\s+hospital/i,
    /eye\s+care/i, /optometry/i,
    /chiropractic/i,
    /podiatry/i, /foot\s+care/i
  ];

  for (const pattern of specialtyPatterns) {
    if (pattern.test(officeName)) {
      return {
        isSpecialist: true,
        specialty: pattern.source,
        confidence: 1.0
      };
    }
  }
  return { isSpecialist: false };
}
```

**Show warning in sidebar:** "⚠️ Office name contains 'dermatology' - may not be PCP"

---

## 📊 TESTING STRATEGY

### Phase 1: Identify False Positives
1. Export verified providers from current FL campaign
2. Manually review 50 random samples
3. Google search to verify specialty
4. Document all false positives (name patterns, taxonomy codes)

### Phase 2: Test Google Places API Types
```javascript
// Test script - run on known specialists
const testCases = [
  { name: "Wassef Dermatology", address: "Wellington FL" },
  { name: "Smith Dental", address: "Miami FL" },
  { name: "Johnson Veterinary", address: "Tampa FL" }
];

testCases.forEach(test => {
  const result = callPlacesAPI(test);
  console.log(`Types: ${result.types}`);
  console.log(`Primary: ${result.primaryType}`);
});
```

### Phase 3: Implement & A/B Test
- Run verification on 1000 providers WITH specialty checking
- Run verification on SAME 1000 providers WITHOUT specialty checking
- Compare false positive rates

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Priority 1: Verification Stage (Immediate)
- [x] Document bug in TODO.md
- [ ] Add `places.types` and `places.primaryType` to API field mask
- [ ] Implement blacklist approach in `verifyPlace()` function
- [ ] Test on known dermatologists/dentists
- [ ] Deploy to provider-search script

### Priority 2: Python Filtering (Next Sprint)
- [ ] Expand organization blacklist patterns
- [ ] Test on recent NPPES export
- [ ] Measure over-filtering rate

### Priority 3: Manual Review Tools (Future)
- [ ] Add specialty keyword detection to "Check if Invalid" tool
- [ ] Create "Specialty Checker" sidebar tool

---

## 💡 ALTERNATIVE APPROACHES

### Idea 1: Machine Learning Classification
Train model on:
- Input: Office name + address + NPPES taxonomy
- Output: PCP probability (0-1)
- Training data: 10K+ hand-labeled providers

**Pros:** Catches subtle patterns
**Cons:** Requires significant data labeling, maintenance

### Idea 2: External API Cross-Reference
Use NPI Registry API or CMS Provider Enrollment API to get current specialty
**Pros:** Most accurate
**Cons:** Rate limits, may require paid API

### Idea 3: Crowdsourced Validation
Add "Report Wrong Specialty" button in Working List
**Pros:** Real-world feedback
**Cons:** Requires volunteer training

---

## 📝 NOTES

**Key insight:** 25% verification success rate is EXPECTED, not a bug
- Many providers genuinely closed/moved
- Some wrong specialties (what we're fixing)
- Some have poor Google Maps presence

**Goal:** Reduce false positive rate from ~5% to <1% while maintaining 25% overall success rate

---

**Next Steps:** Implement verification blacklist first (highest ROI, lowest effort)
