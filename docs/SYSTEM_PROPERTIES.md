# System Properties Documentation

**Purpose:** Documents all PropertiesService properties used by Google Apps Script code
**Last Updated:** October 18, 2025
**Applies To:** UniversalProviderSuite.js, ToolboxSuite.js

---

## Overview

Google Apps Script uses `PropertiesService.getScriptProperties()` to store persistent configuration and state data. These properties persist across script executions and are scoped per Google Apps Script project.

**Key Principle:** Each Google Sheet has its own Apps Script project, so properties are NOT shared between OBGYN and PCP sheets.

---

## Properties Used by UniversalProviderSuite.js

### `PLACES_API_KEY`

- **Type:** String
- **Purpose:** Google Places API (New) authentication key
- **Set By:** Menu → API Configuration → Enter API Key
- **Read By:** `UniversalProviderSuite.js:228` (`getApiKey()`)
- **Default:** None (required - verification will fail if missing)
- **Reset Procedure:**
  1. Menu → API Configuration → Enter API Key
  2. Paste new key
  3. Click OK
- **Shared Between Sheets:** ❌ No - each sheet needs its own key
- **Security:** Stored in ScriptProperties (not visible to sheet users, only Apps Script editor)

**Code References:**
```javascript
// Set: Line 217
PropertiesService.getScriptProperties().setProperty('PLACES_API_KEY', apiKey);

// Get: Line 228
return PropertiesService.getScriptProperties().getProperty('PLACES_API_KEY');
```

---

### `targetStates`

- **Type:** String (comma-separated state codes)
- **Purpose:** Stores which states to process during verification
- **Set By:** Quick Start Wizard or `saveConfig()` function
- **Read By:** `UniversalProviderSuite.js:28` (`getConfig()`)
- **Default:** Falls back to `DEFAULT_CONFIG.TARGET_STATES` if not set
- **Format:** `"TX,CA,FL"` or single state `"TX"`
- **Reset Procedure:**
  1. Menu → Quick Start Wizard
  2. Select target states
  3. Complete wizard
- **Shared Between Sheets:** ❌ No

**Code References:**
```javascript
// Set: Line 47-50
const props = PropertiesService.getScriptProperties();
props.setProperty('targetStates', configData.targetStates);

// Get: Line 28
const targetStatesStr = props.getProperty('targetStates') || DEFAULT_CONFIG.TARGET_STATES;
```

---

### `apiCallCount`

- **Type:** String (stored as number string)
- **Purpose:** Tracks total Google Places API calls this billing month
- **Set By:** `incrementApiCallCount()` after each API call
- **Read By:** `UniversalProviderSuite.js:1076` (`getApiCallCount()`)
- **Default:** `"0"` (if not set)
- **Reset Procedure:**
  1. Menu → API Usage → Reset Counter
  2. Confirm reset
  3. **ONLY reset at start of billing month**
- **Shared Between Sheets:** ❌ No - each sheet tracks separately
- **Critical:** Hard limit at 3,000 calls/month (free tier)

**Code References:**
```javascript
// Get: Line 1076-1078
function getApiCallCount() {
  const props = PropertiesService.getScriptProperties();
  return parseInt(props.getProperty('apiCallCount') || '0');
}

// Increment: Line 1081-1084
function incrementApiCallCount(count) {
  const props = PropertiesService.getScriptProperties();
  const current = getApiCallCount();
  props.setProperty('apiCallCount', (current + count).toString());
}

// Reset: Line 1104
PropertiesService.getScriptProperties().setProperty('apiCallCount', '0');
```

---

### `progress_[PROVIDER_TYPE]_[TARGET_STATES]`

- **Type:** String (row number)
- **Purpose:** Tracks verification progress to resume after timeout
- **Set By:** `saveProcessingProgress(row)` during verification
- **Read By:** `UniversalProviderSuite.js:850` (`getProcessingProgress()`)
- **Default:** `"1"` (start from row 1)
- **Format:** `"progress_PCP_TX"` or `"progress_OBGYN_CA,CO,PA"`
- **Reset Procedure:** Automatically reset to `"1"` when verification completes
- **Shared Between Sheets:** ❌ No
- **Purpose:** Handles 6-minute execution timeout (resumes where it left off)

**Code References:**
```javascript
// Get: Line 850-856
function getProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  return parseInt(props.getProperty(key) || '1');
}

// Set: Line 860-864
function saveProcessingProgress(row) {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  props.setProperty(key, row.toString());
}

// Reset: Line 867-871
function resetProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  props.setProperty(key, '1');
}
```

---

## Properties Used by ToolboxSuite.js

**None currently.** ToolboxSuite.js does NOT use PropertiesService.

All configuration is hardcoded or detected from sheet structure (column names, sheet names).

---

## Common Operations

### View All Properties (Manual)

1. Open Google Sheet
2. Extensions → Apps Script
3. Run this in Apps Script editor:

```javascript
function listAllProperties() {
  const props = PropertiesService.getScriptProperties().getProperties();
  Logger.log(JSON.stringify(props, null, 2));
}
```

4. View → Logs (Ctrl+Enter)

---

### Delete All Properties (危険 DANGER)

**⚠️ WARNING:** Only do this if you want to completely reset the script to factory defaults.

```javascript
function deleteAllProperties() {
  PropertiesService.getScriptProperties().deleteAllProperties();
  Logger.log('All properties deleted');
}
```

**Consequences:**
- API key lost (must re-enter)
- API call count reset to 0 (billing tracking lost)
- Verification progress lost
- Configuration lost (states, provider type)

---

## Migration Notes

### Moving Between Sheets

**Problem:** Copying OBGYN code to PCP sheet doesn't copy properties

**Solution:** After `clasp push` to new sheet, must manually reconfigure:
1. Menu → API Configuration → Enter API Key (paste same key)
2. Menu → Quick Start Wizard → Configure states/provider type
3. Menu → API Usage → Verify counter is 0 (or set manually if needed)

---

### Backup Properties

**Before major changes:**

```javascript
function backupProperties() {
  const props = PropertiesService.getScriptProperties().getProperties();
  Logger.log('BACKUP:');
  Logger.log(JSON.stringify(props, null, 2));
  // Copy from Logs and save to local file
}
```

**Restore:**

```javascript
function restoreProperties() {
  const backup = {
    "PLACES_API_KEY": "your-key-here",
    "apiCallCount": "1234",
    "targetStates": "TX,CA"
  };

  const props = PropertiesService.getScriptProperties();
  Object.keys(backup).forEach(key => {
    props.setProperty(key, backup[key]);
  });

  Logger.log('Properties restored');
}
```

---

## Security Best Practices

### API Key Security

✅ **DO:**
- Store in ScriptProperties (isolated per project)
- Use environment-specific keys (dev vs prod)
- Restrict key to specific APIs (Places API only)
- Set usage quotas in Google Cloud Console

❌ **DON'T:**
- Hardcode in .js files (visible in git)
- Share same key across unrelated projects
- Give key broader permissions than needed
- Commit API keys to version control

---

### Access Control

**Who can see ScriptProperties:**
- ✅ Anyone with "Edit" access to Apps Script project
- ❌ Sheet viewers (read-only)
- ❌ Sheet editors (unless also Apps Script editors)

**Implications:**
- Volunteers making phone calls: ❌ Cannot see API key
- Technical maintainer: ✅ Can see API key via Apps Script editor

---

## Troubleshooting

### "API key missing" error

**Symptom:** Verification fails with "No API key configured"

**Fix:**
```javascript
// Check if key exists
const key = PropertiesService.getScriptProperties().getProperty('PLACES_API_KEY');
Logger.log('API Key exists: ' + (key ? 'YES' : 'NO'));

// If NO: Menu → API Configuration → Enter API Key
```

---

### API counter seems wrong

**Symptom:** Counter shows 500 but you expect 200

**Possible Causes:**
1. Multiple users running verification simultaneously (both increment counter)
2. Failed runs still increment counter (API calls were made even if verification failed)
3. Testing/development runs not accounted for

**Fix:**
```javascript
// Check current value
const count = PropertiesService.getScriptProperties().getProperty('apiCallCount');
Logger.log('Current count: ' + count);

// Manually set if needed (ONLY if you're certain)
PropertiesService.getScriptProperties().setProperty('apiCallCount', '200');
```

---

### Progress counter stuck

**Symptom:** Re-running verification starts from middle of sheet, not beginning

**Fix:**
```javascript
// Check all progress keys
const props = PropertiesService.getScriptProperties().getProperties();
Object.keys(props).forEach(key => {
  if (key.startsWith('progress_')) {
    Logger.log(key + ': ' + props[key]);
  }
});

// Reset specific progress
PropertiesService.getScriptProperties().setProperty('progress_PCP_TX', '1');

// Or use menu: (Progress is auto-reset when verification completes)
```

---

## Future Enhancements

**Potential additions (not yet implemented):**

- `lastVerificationDate` - Track when verification last ran
- `verificationSuccessRate` - Track historical success rate
- `apiResetDate` - Auto-reset counter on billing cycle
- `debugMode` - Enable verbose logging
- `batchSize` - Configurable batch size for processing

**If adding new properties:**
1. Document in this file
2. Add getter/setter functions
3. Update backup/restore procedures
4. Test migration between sheets

---

**Last Updated:** October 18, 2025
**Maintained By:** Technical user (AI agents should update when adding new properties)
