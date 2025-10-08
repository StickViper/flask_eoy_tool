# Configuration Tool Audit Report
**Date:** 2025-10-07
**Scope:** QuickStartWizard.html + UniversalProviderSuite.js integration

---

## 🚨 CRITICAL ISSUES (Must Fix)

### 1. **State Configuration Never Saved** ⚠️⚠️⚠️
**Location:** QuickStartWizard.html line 427 → UniversalProviderSuite.js line 52

**Problem:**
- Wizard sends: `config.state` (single state)
- Backend expects: `configData.states` (plural)
- **Result:** User's state selection is SILENTLY IGNORED, always defaults to 'TX'

**Evidence:**
```javascript
// QuickStartWizard.html line 427
.saveConfigAndStart(config);  // config.state = 'CA'

// UniversalProviderSuite.js line 52-54
if (configData.states) {  // Looking for 'states' but gets 'state'
  props.setProperty('targetStates', configData.states);
}
```

**Impact:** User selects "CA", thinks it's saved, but system processes TX instead!

**Fix Required:** Change wizard line 427 to send `states: config.state` OR change backend to accept `state`

---

### 2. **Multi-State Support Not Implemented in Wizard** 🔧
**Location:** QuickStartWizard.html lines 152-156

**Problem:**
- Backend now supports multi-state: `'TX,WA,CO,PA'` (comma-separated)
- Wizard UI only supports single state selection
- No way for user to configure multiple states via wizard

**Current UI:**
```html
<input type="text" id="state" placeholder="Enter 2-letter state code (e.g., TX)"
       maxlength="2" ... >
```

**What it should be:**
- Text input with validation for comma-separated format: `"TX,WA,CO,PA"`
- OR multi-select state buttons
- Validation: Each state must be 2 characters, comma-separated

**Impact:** Cannot use multi-state filtering feature through wizard (must edit script properties manually)

---

### 3. **Sheet Name Shown in Summary is Wrong** 📋
**Location:** QuickStartWizard.html line 402

**Problem:**
```javascript
// Wizard shows:
document.getElementById('summary-input').textContent =
  `${config.providerType}_${config.state}_import`;
  // Result: "OBGYN_CA_import"

// But actual backend (line 69-70) creates:
const stateLabel = config.TARGET_STATES_ARRAY.length === 1
  ? config.TARGET_STATES_ARRAY[0]
  : 'MultiState';
const prefix = `${config.PROVIDER_TYPE}_${stateLabel}`;
  // Result for multi-state: "OBGYN_MultiState_import"
```

**Impact:** User creates sheet with name shown in wizard ("OBGYN_CA_import") but system looks for different name ("OBGYN_MultiState_import"). **Verification fails to start!**

---

## ⚠️ MAJOR ISSUES (Should Fix)

### 4. **No Validation for State Input Format**
**Location:** QuickStartWizard.html lines 324-327

**Current validation:**
```javascript
if (!config.state || config.state.length !== 2) {
  alert('Please enter a valid 2-letter state code');
  return false;
}
```

**Problem:** If we update to support multi-state, this validation breaks
**Needed:** Validate comma-separated format: `"TX"` OR `"TX,WA,CO,PA"`

---

### 5. **Progress Tracking Has Complex Key Issue**
**Location:** UniversalProviderSuite.js lines 699, 709, 716

**Problem:**
```javascript
const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
// For multi-state: "progress_OBGYN_TX,WA,CO,PA"
```

**Issues:**
- Comma in key name (unusual but works)
- If user changes states mid-run, progress is lost
- Progress not shared between single-state and multi-state runs

**Recommendation:** Use hash or simplified key format

---

### 6. **Wizard Doesn't Show Current Configuration**
**Location:** QuickStartWizard.html - missing feature

**Problem:**
- Wizard always starts from defaults
- If user already configured once, they don't see their current settings
- No way to know what's currently set without opening "View Configuration" menu

**Needed:** Load current config from ScriptProperties on wizard open

---

## 📝 MINOR ISSUES (Nice to Have)

### 7. **State Grid Not Wired for Multi-Select**
**Location:** QuickStartWizard.html lines 266-283

**Current:** Clicking state button sets single state
**If updating for multi-state:** Need to support multiple selections with visual feedback

---

### 8. **Output Mode "Separate by State" Unclear for Multi-State**
**Location:** QuickStartWizard.html line 168

**Question:** What does "Separate by state" mean when processing 4 states?
- 4 separate sheets? (`OBGYN_TX_verified`, `OBGYN_WA_verified`, etc.)
- Or still unified but with state column?

**Current behavior:** `USE_UNIFIED_OUTPUT` flag (line 34 in UniversalProviderSuite.js)
- `true` → All_Verified_Providers (all states together)
- `false` → `${prefix}_verified` (but prefix is 'MultiState' for multi-state!)

**Result:** "Separate" mode creates `OBGYN_MultiState_verified` which is NOT separated by state!

---

## ✅ WHAT WORKS CORRECTLY

1. **API Key Validation** - testApiKeyValid() works ✅
2. **Provider Type Selection** - Correctly saved ✅
3. **Max Batches Per Run** - Correctly saved ✅
4. **Output Mode** - Correctly saved (but behavior unclear for multi-state)
5. **API Key Skip Logic** - Detects existing key and skips step 2 ✅
6. **Three-Step Wizard Flow** - Navigation works ✅

---

## 🛠️ RECOMMENDED FIXES (Prioritized)

### **Priority 1: Must Fix Before Use** (15 min)

Fix the critical `state` vs `states` mismatch:

**Option A - Quick Fix (Backend Change):**
```javascript
// UniversalProviderSuite.js line 52-54
if (configData.state) {  // Changed from configData.states
  props.setProperty('targetStates', configData.state);
}
```
**Pros:** Wizard works immediately
**Cons:** Still single-state only

**Option B - Full Fix (Wizard Change):**
```javascript
// QuickStartWizard.html line 427
.saveConfigAndStart({
  ...config,
  states: config.state  // Add this mapping
});
```
**Pros:** More explicit
**Cons:** Wizard still single-state only

---

### **Priority 2: Should Implement** (1-2 hours)

**Update wizard to support multi-state input:**

1. Change state input to allow comma-separated values:
```html
<input type="text" id="state"
       placeholder="Enter state(s): TX or TX,WA,CO,PA"
       oninput="validateStates()">
```

2. Update validation:
```javascript
function validateCurrentStep() {
  if (currentStep === 1) {
    const statesInput = document.getElementById('state').value;
    const statesArray = statesInput.split(',').map(s => s.trim().toUpperCase());

    // Validate each state is 2 characters
    const invalid = statesArray.filter(s => s.length !== 2);
    if (invalid.length > 0) {
      alert(`Invalid state codes: ${invalid.join(', ')}`);
      return false;
    }

    config.states = statesArray.join(',');  // Save as comma-separated
    return true;
  }
}
```

3. Update summary to show correct sheet name:
```javascript
function updateSummary() {
  const statesArray = config.states.split(',');
  const stateLabel = statesArray.length === 1 ? statesArray[0] : 'MultiState';

  document.getElementById('summary-input').textContent =
    `${config.providerType}_${stateLabel}_import`;
}
```

---

### **Priority 3: Polish** (30 min)

1. Load current configuration when wizard opens
2. Add visual feedback for multi-state selection in state grid
3. Clarify "Separate by state" option behavior
4. Add help text explaining multi-state format

---

## 🤔 UNREASONABLE TO IMPLEMENT

### **Dynamic Sheet Detection/Creation**
**Why it's hard:**
- Different users have different naming conventions
- Wizard would need to scan all sheets and guess which one is the import sheet
- Risk of processing wrong data

**Current approach is better:** User must create correctly-named sheet manually

---

### **Automatic API Key Management**
**Why it's hard:**
- OAuth2 flow requires redirect URLs and user interaction
- API keys are sensitive - better to have user manage them
- Google Cloud Console changes frequently

**Current approach is better:** User gets key from console and pastes it

---

### **Real-time Verification Preview**
**Why it's hard:**
- Would require actual API calls during setup
- Uses up limited API quota
- Slow user experience (each test takes 2-3 seconds)

**Current approach is better:** Test API key only, not actual verification

---

## 📊 TESTING CHECKLIST

Before deploying fixes, test:

- [ ] Single state selection saves correctly
- [ ] Multi-state selection (e.g., "TX,WA,CO,PA") saves correctly
- [ ] Sheet name in summary matches actual backend sheet name
- [ ] Validation accepts valid formats, rejects invalid
- [ ] Wizard loads current config (not just defaults)
- [ ] API key test still works
- [ ] Start verification actually uses configured states
- [ ] Progress tracking works across runs

---

## 💬 QUESTIONS FOR USER

1. **Multi-state UI preference:**
   - A) Simple text input: "TX,WA,CO,PA" (faster to implement)
   - B) Multi-select state grid (better UX, more code)

2. **"Separate by state" for multi-state:**
   - Should it create 4 separate sheets?
   - Or just one unified sheet with state column?
   - Or disable this option for multi-state?

3. **Sheet naming for multi-state:**
   - Keep "MultiState" label?
   - Or list all states: "OBGYN_TX_WA_CO_PA_import" (gets long)

4. **Backward compatibility:**
   - Support old single-state configs?
   - Or force re-configuration?

---

## 🎯 BOTTOM LINE

**Current status:** Wizard is BROKEN for state configuration. User's state selection is ignored.

**Minimum to make it work:** Fix `state` vs `states` mismatch (5 min fix)

**To make it good:** Add multi-state input support + correct sheet name display (1-2 hours)

**Risk if not fixed:** Users will be confused why their state selection doesn't work, and verification will fail with "sheet not found" errors.
