/**
 * Universal Provider Verification Suite (v8.0 - RESTRUCTURED)
 * Complete rewrite with better architecture
 */

// ====================================================================================
// CONFIGURATION MANAGEMENT
// ====================================================================================

// ============================================================================
// IMPORTANT: FREE TIER COMPLIANCE (Solo dev / nonprofit project)
// ============================================================================
// Google Places API (New) has 3 pricing tiers based on FIELDS REQUESTED:
//   - ESSENTIALS SKU: 10,000 free calls/month, then $17/1,000
//   - PRO SKU: 5,000 free calls/month, then $25/1,000
//   - ENTERPRISE SKU: 1,000 free calls/month, then $34.07/1,000 (AVOID!)
//
// YOU ARE BILLED AT THE HIGHEST TIER OF ANY FIELD IN YOUR REQUEST!
//
// This code uses ONLY Essentials tier fields to stay 100% free:
//   ✅ places.id (required, no charge)
//   ✅ places.formattedAddress (Essentials)
//   ✅ places.types (Essentials)
//
// REMOVED FIELDS (to avoid Pro/Enterprise charges):
//   ❌ places.nationalPhoneNumber (Enterprise SKU - was the killer!)
//   ❌ places.displayName (Pro SKU)
//   ❌ places.businessStatus (Pro SKU)
//   ❌ places.primaryType (Pro SKU)
//
// DO NOT add fields without checking pricing tier at:
// https://developers.google.com/maps/billing-and-pricing/pricing
// ============================================================================

const DEFAULT_CONFIG = {
  PROVIDER_TYPE: 'PCP',
  TARGET_STATES: 'TX',  // Comma-separated: 'TX' or 'TX,WA,CO,PA' or empty for all
  USE_UNIFIED_OUTPUT: true,
  MAX_BATCHES_PER_RUN: 0,
  BATCH_SIZE: 25,
  MAX_EXECUTION_TIME: 270000,
  NAME_SIMILARITY_THRESHOLD: 0.65,
  HIGH_CONFIDENCE_THRESHOLD: 0.85,
  REQUIRE_PHONE_FOR_OPERATIONAL: true,
  CACHE_DURATION: 21600,
  FIX_CAPITALIZATION: true,
  API_CALL_LIMIT: 8000,  // Conservative limit (10,000 free for Essentials SKU, 2,000 buffer)
  API_WARNING_THRESHOLD: 7500  // Warn when approaching limit (500 below hard limit)
};

function getConfig() {
  const props = PropertiesService.getScriptProperties();
  const targetStatesStr = props.getProperty('targetStates') || DEFAULT_CONFIG.TARGET_STATES;

  return {
    PROVIDER_TYPE: props.getProperty('providerType') || DEFAULT_CONFIG.PROVIDER_TYPE,
    TARGET_STATES: targetStatesStr,  // Keep as string for storage
    TARGET_STATES_ARRAY: targetStatesStr ? targetStatesStr.split(',').map(s => s.trim().toUpperCase()) : [],  // Parsed array
    USE_UNIFIED_OUTPUT: (props.getProperty('outputMode') || 'unified') === 'unified',
    MAX_BATCHES_PER_RUN: parseInt(props.getProperty('maxBatchesPerRun') || '0'),
    BATCH_SIZE: DEFAULT_CONFIG.BATCH_SIZE,
    MAX_EXECUTION_TIME: DEFAULT_CONFIG.MAX_EXECUTION_TIME,
    NAME_SIMILARITY_THRESHOLD: DEFAULT_CONFIG.NAME_SIMILARITY_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD: DEFAULT_CONFIG.HIGH_CONFIDENCE_THRESHOLD,
    REQUIRE_PHONE_FOR_OPERATIONAL: DEFAULT_CONFIG.REQUIRE_PHONE_FOR_OPERATIONAL,
    CACHE_DURATION: DEFAULT_CONFIG.CACHE_DURATION,
    FIX_CAPITALIZATION: DEFAULT_CONFIG.FIX_CAPITALIZATION
  };
}

function saveConfig(configData) {
  const props = PropertiesService.getScriptProperties();

  if (configData.apiKey) {
    props.setProperty('PLACES_API_KEY', configData.apiKey);
  }
  // Accept both 'states' (new wizard) and 'state' (old wizard) for backward compat
  if (configData.states || configData.state) {
    const statesValue = configData.states || configData.state;
    props.setProperty('targetStates', statesValue);  // Save comma-separated string
  }
  if (configData.providerType) {
    props.setProperty('providerType', configData.providerType);
  }
  if (configData.outputMode) {
    props.setProperty('outputMode', configData.outputMode);
  }
  if (configData.maxBatchesPerRun !== undefined) {
    props.setProperty('maxBatchesPerRun', configData.maxBatchesPerRun.toString());
  }
}

function getSheetNames() {
  const config = getConfig();
  // For single state: PCP_TX, for multi: PCP_MultiState
  const stateLabel = config.TARGET_STATES_ARRAY.length === 1 ? config.TARGET_STATES_ARRAY[0] : 'MultiState';
  const prefix = `${config.PROVIDER_TYPE}_${stateLabel}`;
  
  return {
    INPUT: `${prefix}_import`,
    VERIFIED: config.USE_UNIFIED_OUTPUT ? 'All_Verified_Providers' : `${prefix}_verified`,
    ERRORS: config.USE_UNIFIED_OUTPUT ? 'All_Provider_Errors' : `${prefix}_errors`,
    REVIEW: 'Manual_Review_Queue',
    FORMATTED: config.USE_UNIFIED_OUTPUT ? 'All_Providers_Formatted' : `${prefix}_formatted`
  };
}

// ====================================================================================
// MENU & UI
// ====================================================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const config = getConfig();
  
  ui.createMenu(`⚡ Provider Suite (${config.PROVIDER_TYPE} - ${config.TARGET_STATES})`)
    .addItem('🚀 Quick Start Wizard', 'showQuickStartWizard')
    .addItem('📋 View Configuration', 'showCurrentConfig')
    .addSeparator()
    .addSubMenu(ui.createMenu('🤖 Automated Verification')
      .addItem('▶️ Start Verification', 'startProcessing')
      .addItem('⏸️ Pause', 'pauseProcessing')
      .addItem('▶️ Resume', 'resumeProcessing')
      .addItem('🛑 Reset', 'resetProcessing'))
    .addSeparator()
    .addItem('👁️ Open Review Queue', 'openReviewQueue')
    .addItem('📝 Manual Verification Tool', 'showVerificationSidebar')
    .addSeparator()
    .addSubMenu(ui.createMenu('🛠️ Tools')
      .addItem('🔗 Add Search Links', 'createGoogleSearchLinks')
      .addItem('📄 Format for Export', 'formatVerifiedSheet')
      .addItem('✨ Fix Capitalization', 'fixCapitalizationInSheet')
      .addItem('🔍 Remove Duplicates', 'findAndRemoveDuplicates')
      .addItem('📊 Stats Report', 'generateStatsReport')
      .addItem('🔧 Setup API Key', 'setupApiKey'))
    .addItem('📊 API Usage', 'showApiUsage')
    .addToUi();
}

function showQuickStartWizard() {
  const html = HtmlService.createHtmlOutputFromFile('QuickStartWizard')
    .setWidth(500)
    .setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(html, 'Provider Verification Setup');
}

function showVerificationSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('VerificationSidebar')
    .setWidth(350);
  SpreadsheetApp.getUi().showSidebar(html);
}

function saveConfigAndStart(configData) {
  try {
    saveConfig(configData);
    return { success: true };
  } catch (error) {
    Logger.log('Config save error: ' + error);
    return { success: false, error: error.message };
  }
}

function testApiKeyValid(apiKey) {
  try {
    const response = UrlFetchApp.fetch('https://places.googleapis.com/v1/places:searchText', {
      method: 'post',
      contentType: 'application/json',
      headers: {
        'X-Goog-Api-Key': apiKey,
        'X-Goog-FieldMask': 'places.id'
      },
      payload: JSON.stringify({ textQuery: 'test' }),
      muteHttpExceptions: true
    });

    const code = response.getResponseCode();
    if (code === 200) {
      return { valid: true, message: 'API key is valid!' };
    } else if (code === 403) {
      return { valid: false, message: 'Invalid API key or Places API not enabled' };
    } else {
      return { valid: false, message: `API returned code ${code}` };
    }
  } catch (error) {
    return { valid: false, message: error.message };
  }
}

function getSheetStatus(clientConfig) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = clientConfig || getConfig();
  const sheets = getSheetNames();
  
  const masterSheet = ss.getSheetByName(sheets.INPUT);
  const status = {
    sheets: { master: !!masterSheet },
    counts: { toProcess: 0 },
    hasApiKey: !!getApiKey(),
    hasRequiredHeaders: false
  };

  if (masterSheet && masterSheet.getLastRow() > 0) {
    status.counts.toProcess = Math.max(0, masterSheet.getLastRow() - 1);
    
    if (masterSheet.getLastColumn() > 0) {
      const headers = masterSheet.getRange(1, 1, 1, masterSheet.getLastColumn()).getValues()[0];
      const required = ['Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP'];
      status.hasRequiredHeaders = required.every(h => headers.includes(h));
    }
  }

  return status;
}

function showCurrentConfig() {
  const ui = SpreadsheetApp.getUi();
  const config = getConfig();
  const sheets = getSheetNames();
  const apiKey = getApiKey() ? '✅ Configured' : '❌ Not Set';
  const batchLimit = config.MAX_BATCHES_PER_RUN === 0 ? 'Unlimited' : `${config.MAX_BATCHES_PER_RUN} batches`;

  ui.alert('Current Configuration',
    `Provider Type: ${config.PROVIDER_TYPE}\n` +
    `Target States: ${config.TARGET_STATES}\n` +
    `Output Mode: ${config.USE_UNIFIED_OUTPUT ? 'Unified' : 'Separate'}\n` +
    `API Key: ${apiKey}\n\n` +
    `Batch Size: ${config.BATCH_SIZE} rows\n` +
    `Max Batches Per Run: ${batchLimit}\n\n` +
    `Input Sheet: ${sheets.INPUT}\n` +
    `Verified Sheet: ${sheets.VERIFIED}`,
    SpreadsheetApp.getUi().ButtonSet.OK);
}

function setupApiKey() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt('Setup Google Places API Key', 
    'Enter your API key:', ui.ButtonSet.OK_CANCEL);

  if (result.getSelectedButton() === ui.Button.OK) {
    const apiKey = result.getResponseText().trim();
    if (apiKey) {
      PropertiesService.getScriptProperties().setProperty('PLACES_API_KEY', apiKey);
      ui.alert('Success', 'API key saved!', ui.ButtonSet.OK);
    }
  }
}

function checkApiKeyExists() {
  return !!getApiKey();
}

function getApiKey() {
  return PropertiesService.getScriptProperties().getProperty('PLACES_API_KEY');
}

// ====================================================================================
// MAIN PROCESSING ENGINE
// ====================================================================================

function startProcessing() {
  const ui = SpreadsheetApp.getUi();
  const config = getConfig();
  const sheets = getSheetNames();

  if (!getApiKey()) {
    ui.alert('Setup Required', 'Please set up your API key first.\n\nUse Tools > Setup API Key', ui.ButtonSet.OK);
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const inputSheet = ss.getSheetByName(sheets.INPUT);

  if (!inputSheet) {
    ui.alert('Missing Input Sheet',
      `Cannot find sheet: ${sheets.INPUT}\n\nPlease create this sheet with your provider data.`,
      ui.ButtonSet.OK);
    return;
  }

  // API usage safety check
  const currentUsage = getApiCallCount();
  const remainingCalls = DEFAULT_CONFIG.API_CALL_LIMIT - currentUsage;
  const rowsToProcess = Math.max(0, inputSheet.getLastRow() - 1);

  if (currentUsage >= DEFAULT_CONFIG.API_CALL_LIMIT) {
    ui.alert('API Limit Reached',
      `You have used ${currentUsage} of ${DEFAULT_CONFIG.API_CALL_LIMIT} API calls.\n\n` +
      'Cannot start verification. Reset counter or wait for billing cycle.',
      ui.ButtonSet.OK);
    return;
  }

  if (currentUsage >= DEFAULT_CONFIG.API_WARNING_THRESHOLD) {
    const warningResponse = ui.alert('API Usage Warning',
      `⚠️ You have used ${currentUsage} of ${DEFAULT_CONFIG.API_CALL_LIMIT} API calls.\n` +
      `Only ${remainingCalls} calls remaining.\n\n` +
      `This run will process up to ${rowsToProcess} providers.\n\n` +
      'Continue?',
      ui.ButtonSet.YES_NO);

    if (warningResponse !== ui.Button.YES) return;
  }

  const response = ui.alert('Start Verification',
    `Ready to process ${config.PROVIDER_TYPE} providers in ${config.TARGET_STATES}\n\n` +
    `Input: ${sheets.INPUT}\n` +
    `Output: ${sheets.VERIFIED}\n` +
    `Rows to process: ${rowsToProcess}\n` +
    `API calls used: ${currentUsage}/${DEFAULT_CONFIG.API_CALL_LIMIT}\n\n` +
    'Continue?',
    ui.ButtonSet.YES_NO);

  if (response !== ui.Button.YES) return;

  deleteTriggers();
  resetProcessingProgress();
  initializeOutputSheets();

  // Show starting alert BEFORE processing
  ui.alert('Starting Verification',
    `Processing first batch of ${Math.min(config.BATCH_SIZE, rowsToProcess)} rows...\n\n` +
    'This may take 2-5 minutes. Please wait.',
    ui.ButtonSet.OK);

  processNextBatch();

  // Show progress AFTER first batch completes
  const progress = getProcessingProgress();
  const remaining = rowsToProcess - progress.lastProcessedRow;

  if (remaining > 0) {
    ui.alert('First Batch Complete',
      `Processed: ${progress.lastProcessedRow} of ${rowsToProcess} rows\n` +
      `Remaining: ${remaining} rows\n\n` +
      'Processing will continue automatically every 2 minutes.\n' +
      'Keep this sheet open to see the final completion alert.\n\n' +
      'Check the verified/review/error sheets for results so far.',
      ui.ButtonSet.OK);
  } else {
    // All done in first batch
    finishProcessing();
  }
}

function processNextBatch() {
  const startTime = Date.now();
  const config = getConfig();
  const sheets = getSheetNames();
  const apiKey = getApiKey();

  if (!apiKey) {
    logMessage('ERROR: No API key found');
    return;
  }

  // Check API limit before processing
  const currentUsage = getApiCallCount();
  if (currentUsage >= DEFAULT_CONFIG.API_CALL_LIMIT) {
    logMessage(`ERROR: API limit reached (${currentUsage}/${DEFAULT_CONFIG.API_CALL_LIMIT})`);
    finishProcessing();
    SpreadsheetApp.getUi().alert('API Limit Reached',
      `Processing stopped. Used ${currentUsage} of ${DEFAULT_CONFIG.API_CALL_LIMIT} API calls.`,
      SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const inputSheet = ss.getSheetByName(sheets.INPUT);

  if (!inputSheet) {
    logMessage('ERROR: Input sheet not found');
    return;
  }

  const progress = getProcessingProgress();
  const totalRows = inputSheet.getLastRow();

  if (progress.lastProcessedRow >= totalRows) {
    finishProcessing();
    return;
  }

  let batchesProcessed = 0;
  let currentRow = progress.lastProcessedRow + 1;

  while (currentRow <= totalRows) {
    // Check batch limit
    if (config.MAX_BATCHES_PER_RUN > 0 && batchesProcessed >= config.MAX_BATCHES_PER_RUN) {
      logMessage(`Batch limit reached (${config.MAX_BATCHES_PER_RUN}). Scheduling next run...`);
      saveProcessingProgress(currentRow - 1);
      scheduleTrigger();
      return;
    }

    // Check time limit
    if (Date.now() - startTime >= config.MAX_EXECUTION_TIME) {
      logMessage('Time limit approaching. Scheduling next run...');
      saveProcessingProgress(currentRow - 1);
      scheduleTrigger();
      return;
    }

    const endRow = Math.min(currentRow + config.BATCH_SIZE - 1, totalRows);
    logMessage(`Processing batch ${batchesProcessed + 1}: rows ${currentRow} to ${endRow} of ${totalRows}`);

    try {
      processBatch(inputSheet, currentRow, endRow, apiKey);
      saveProcessingProgress(endRow);
      currentRow = endRow + 1;
      batchesProcessed++;
    } catch (error) {
      logMessage(`ERROR in batch ${currentRow}-${endRow}: ${error.message}`);
      // Continue to next batch despite error
      saveProcessingProgress(endRow);
      currentRow = endRow + 1;
      batchesProcessed++;
    }
  }

  if (currentRow > totalRows) {
    finishProcessing();
  }
}

function processBatch(inputSheet, startRow, endRow, apiKey) {
  const config = getConfig();
  const headers = inputSheet.getRange(1, 1, 1, inputSheet.getLastColumn()).getValues()[0];
  const colMap = buildColumnMap(headers);
  
  const numRows = endRow - startRow + 1;
  const dataRange = inputSheet.getRange(startRow, 1, numRows, headers.length);
  const data = dataRange.getValues();

  // Build API requests
  const requests = [];
  const rowInfo = [];
  
  data.forEach((row, i) => {
    const actualRow = startRow + i;
    const officeName = row[colMap['Office Name']];
    const address = row[colMap['Address']];
    const city = row[colMap['City']];
    const state = row[colMap['State']];
    const phone = row[colMap['Phone Number']];
    const notes = colMap['Notes'] !== undefined ? row[colMap['Notes']] : null;

    // STATE FILTER: Skip rows not in target states list
    if (config.TARGET_STATES_ARRAY.length > 0 && state) {
      const stateUpper = state.toString().trim().toUpperCase();
      if (!config.TARGET_STATES_ARRAY.includes(stateUpper)) {
        logMessage(`Skipping row ${actualRow}: State '${state}' not in target states [${config.TARGET_STATES}]`);
        return;
      }
    }

    if (!officeName || !address) {
      recordError(actualRow, row, colMap, 'Missing required data');
      return;
    }

    const searchQuery = `${officeName} ${address} ${city} ${state}`;
    requests.push(buildSearchRequest(searchQuery, apiKey));
    rowInfo.push({
      rowNumber: actualRow,
      officeName: officeName,
      phone: phone,
      notes: notes,
      rowData: row
    });
  });

  if (requests.length === 0) return;

  // Execute API calls
  logMessage(`Calling Places API for ${requests.length} providers...`);
  incrementApiCallCount(requests.length);
  
  let responses;
  try {
    responses = UrlFetchApp.fetchAll(requests);
  } catch (error) {
    logMessage(`ERROR: API call failed - ${error.message}`);
    // Record all as errors
    rowInfo.forEach(info => {
      recordError(info.rowNumber, info.rowData, colMap, `API call failed: ${error.message}`);
    });
    return;
  }

  // Process responses
  responses.forEach((response, i) => {
    const info = rowInfo[i];
    
    try {
      const result = JSON.parse(response.getContentText());
      const verification = verifyPlace(result, info);
      recordResult(info.rowNumber, info.rowData, colMap, verification);
    } catch (error) {
      recordError(info.rowNumber, info.rowData, colMap, `Parse error: ${error.message}`);
    }
  });

  SpreadsheetApp.flush();
}

function buildSearchRequest(query, apiKey) {
  // ⚠️ FREE TIER COMPLIANCE: ONLY Essentials SKU fields (10,000 free calls/month)
  // DO NOT add Pro/Enterprise fields or you'll trigger expensive charges!
  // Current fields: places.id (free), places.formattedAddress (Essentials), places.types (Essentials)
  return {
    url: 'https://places.googleapis.com/v1/places:searchText',
    method: 'post',
    contentType: 'application/json',
    headers: {
      'X-Goog-Api-Key': apiKey,
      'X-Goog-FieldMask': 'places.id,places.formattedAddress,places.types'  // ESSENTIALS TIER ONLY!
    },
    payload: JSON.stringify({ textQuery: query }),
    muteHttpExceptions: true
  };
}

function verifyPlace(apiResult, rowInfo) {
  if (!apiResult.places || apiResult.places.length === 0) {
    return {
      success: false,
      status: 'NOT_FOUND',
      notes: 'Not found on Google Maps',
      confidence: 0
    };
  }

  const config = getConfig();
  const place = apiResult.places[0];

  // ⚠️ FREE TIER COMPLIANCE: Only Essentials fields available
  // We removed displayName, nationalPhoneNumber, businessStatus, primaryType to avoid charges
  const result = {
    placeId: place.id,
    status: 'FOUND',  // If Google returns it, assume it exists (was: businessStatus)
    correctedName: '',  // Not available (was: displayName - Pro SKU)
    correctedPhone: '',  // Not available (was: nationalPhoneNumber - Enterprise SKU)
    correctedAddress: place.formattedAddress || '',
    businessTypes: place.types || [],
    primaryType: '',  // Not available (was: primaryType - Pro SKU)
    confidence: 0
  };

  // Calculate confidence (SIMPLIFIED for Essentials tier)
  let points = 0;
  let maxPoints = 100;

  // Base confidence: If Google found a place matching our query, that's high confidence (80%)
  // The query already includes office name + full address, so if Google returns a result,
  // it's likely the right place.
  points += 80;

  // Business type validation (20%) - CRITICAL for specialty filtering
  // If types indicate it's a valid healthcare provider (not excluded), add points
  const hasValidType = result.businessTypes.some(t =>
    ['doctor', 'health', 'medical_clinic', 'hospital'].includes(t.toLowerCase())
  );
  if (hasValidType) {
    points += 20;
  }

  // Business type penalty (prevents non-PCPs from passing)
  // These types indicate it's NOT a PCP office
  const excludedTypes = [
    'dentist',
    'veterinary_care',
    'physiotherapist',
    'chiropractor',
    'optometrist',
    'pharmacy',
    'hospital',  // Hospitals are excluded (we want independent practices)
    'beauty_salon',
    'spa',
    'gym',
    'fitness_center'
  ];

  const hasExcludedType = result.businessTypes.some(t =>
    excludedTypes.includes(t.toLowerCase())
  );

  if (hasExcludedType) {
    points -= 40; // Heavy penalty - can drop from 100% to 60% (below 80% threshold)
    const excludedType = result.businessTypes.find(t => excludedTypes.includes(t.toLowerCase()));
    result.notes = `Wrong business type: ${excludedType}`;
  }

  // Office name/address specialty keyword filter (catches specialists Google tags as 'doctor')
  // This is a backup for specialists that slip through NPPES taxonomy filtering
  const specialtyKeywords = [
    // Medical Specialties
    'cardiology', 'cardiologist', 'heart center', 'heart clinic',
    'gastroenterology', 'gastroenterologist', 'digestive', 'gi clinic',
    'pulmonology', 'pulmonologist', 'lung center', 'respiratory',
    'endocrinology', 'endocrinologist', 'diabetes center', 'thyroid',
    'nephrology', 'nephrologist', 'kidney', 'dialysis',
    'rheumatology', 'rheumatologist', 'arthritis',
    'hematology', 'oncology', 'oncologist', 'cancer center', 'cancer clinic',
    'infectious disease',

    // Surgery Specialties
    'neurosurgery', 'neurosurgeon', 'brain surgeon',
    'plastic surgery', 'plastic surgeon', 'cosmetic surgery', 'reconstructive',
    'orthopedic', 'orthopaedic', 'sports medicine', 'joint replacement',
    'vascular surgery', 'vascular surgeon',
    'cardiac surgery', 'heart surgery',
    'bariatric', 'weight loss surgery',

    // Pediatrics
    'pediatric', 'pediatrics', 'pediatrician', 'children', "children's",
    'kids health', 'child health',

    // Other Specialists
    'dermatology', 'dermatologist', 'skin clinic',
    'neurology', 'neurologist',
    'psychiatry', 'psychiatrist', 'mental health',
    'allergy', 'allergist', 'immunology',
    'ophthalmology', 'ophthalmologist', 'eye doctor', 'eye clinic',
    'ent ', ' ent', 'ear nose throat', 'otolaryngology',
    'urology', 'urologist',
    'pain management', 'pain clinic',
    'sleep medicine', 'sleep center', 'sleep clinic',

    // Age-Specific (Non-Target)
    'geriatric', 'senior', 'elder care', 'retirement',
    'adolescent medicine', 'teen health'
  ];

  // Check office name from input and Google's formatted address (includes business name often)
  // Note: correctedName not available (Pro SKU), using formattedAddress instead
  const textsToCheck = [rowInfo.officeName, result.correctedAddress].filter(Boolean);

  for (const text of textsToCheck) {
    const textLower = (text || '').toLowerCase();

    for (const keyword of specialtyKeywords) {
      if (textLower.includes(keyword)) {  // keyword already lowercase
        points -= 40; // Same heavy penalty as wrong business type
        const prevNotes = result.notes || '';
        result.notes = prevNotes ? `${prevNotes}; Specialist keyword: ${keyword}` : `Specialist keyword detected: ${keyword}`;
        break; // Only apply penalty once per text
      }
    }

    if (result.notes && result.notes.includes('Specialist keyword')) {
      break; // Already found specialist keyword, no need to check other text
    }
  }

  // Network penalty (for multi-location practices with 3+ locations)
  // Check if rowInfo has Notes column data indicating a network
  if (rowInfo.notes) {
    const notesLower = rowInfo.notes.toString().toLowerCase();
    const networkMatch = notesLower.match(/network\s*\(~(\d+)\)/);

    if (networkMatch) {
      const networkSize = parseInt(networkMatch[1]);

      if (networkSize >= 3) {
        points -= 10; // Moderate penalty for large networks
        const networkNote = `Part of ${networkSize}-location network (manual review recommended)`;
        result.notes = result.notes ? `${result.notes}; ${networkNote}` : networkNote;
      }
    }
  }

  result.confidence = Math.max(0, points / maxPoints); // Ensure non-negative

  // Determine success (SIMPLIFIED - no businessStatus check needed)
  // If Google found it and confidence is high, it's verified
  result.success = result.confidence >= config.HIGH_CONFIDENCE_THRESHOLD;
  result.needsReview = result.confidence >= config.NAME_SIMILARITY_THRESHOLD &&
                       result.confidence < config.HIGH_CONFIDENCE_THRESHOLD;

  // Only set generic notes if specific reason wasn't already set (e.g., specialist detection)
  if (!result.notes) {
    result.notes = result.success ? 'Verified (Essentials tier)' :
                   result.needsReview ? `Medium confidence (${Math.round(result.confidence * 100)}%)` :
                   'Failed verification';
  }

  return result;
}

function recordResult(rowNumber, rowData, colMap, verification) {
  const config = getConfig();
  const sheets = getSheetNames();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Apply capitalization fixes if enabled
  const officeName = config.FIX_CAPITALIZATION ?
    fixCapitalization(rowData[colMap['Office Name']]) :
    rowData[colMap['Office Name']];
  // Note: correctedName not available (Pro SKU removed), using original name
  const correctedName = officeName;

  if (verification.success) {
    // Determine target sheet based on output mode
    let targetSheetName;
    if (config.USE_UNIFIED_OUTPUT) {
      targetSheetName = sheets.VERIFIED;  // "All_Verified_Providers"
    } else {
      // Separate mode: Create state-specific sheet
      const state = rowData[colMap['State']];
      targetSheetName = `${config.PROVIDER_TYPE}_${state}_verified`;
    }

    const verifiedSheet = getOrCreateSheet(targetSheetName, getVerifiedHeaders());
    const newRow = [
      officeName,
      rowData[colMap['Phone Number']],
      rowData[colMap['Address']],
      rowData[colMap['City']],
      rowData[colMap['State']],
      rowData[colMap['ZIP']],
      correctedName,
      rowData[colMap['Phone Number']],  // Use original phone (correctedPhone not available - Enterprise SKU)
      verification.correctedAddress,
      verification.placeId,
      rowData[colMap['State']],  // Use actual state from row, not config
      config.PROVIDER_TYPE,
      verification.confidence,
      new Date()
    ];
    verifiedSheet.appendRow(newRow);
  } else if (verification.needsReview) {
    // Add to review queue
    const reviewSheet = getOrCreateSheet(sheets.REVIEW, getReviewHeaders());
    const priority = Math.round((1 - verification.confidence) * 100);
    const newRow = [
      rowNumber,
      officeName,
      rowData[colMap['Phone Number']],
      rowData[colMap['Address']],
      rowData[colMap['City']],
      rowData[colMap['State']],
      rowData[colMap['ZIP']],
      config.PROVIDER_TYPE,
      verification.confidence,
      priority,
      'Pending',
      '',
      '',
      '',
      ''
    ];
    reviewSheet.appendRow(newRow);
  } else {
    // Add to errors
    recordError(rowNumber, rowData, colMap, verification.notes);
  }
}

function recordError(rowNumber, rowData, colMap, errorMessage) {
  const config = getConfig();
  const sheets = getSheetNames();

  // Apply capitalization fixes if enabled
  const officeName = config.FIX_CAPITALIZATION && rowData[colMap['Office Name']] ?
    fixCapitalization(rowData[colMap['Office Name']]) :
    (rowData[colMap['Office Name']] || '');

  // Determine target sheet based on output mode
  let targetSheetName;
  if (config.USE_UNIFIED_OUTPUT) {
    targetSheetName = sheets.ERRORS;  // "All_Provider_Errors"
  } else {
    // Separate mode: Create state-specific error sheet
    const state = rowData[colMap['State']] || 'UNKNOWN';
    targetSheetName = `${config.PROVIDER_TYPE}_${state}_errors`;
  }

  const errorSheet = getOrCreateSheet(targetSheetName, getErrorHeaders());

  const newRow = [
    officeName,
    rowData[colMap['Address']] || '',
    rowData[colMap['City']] || '',
    rowData[colMap['State']] || '',
    rowData[colMap['ZIP']] || '',
    config.PROVIDER_TYPE,
    rowNumber,
    errorMessage,
    new Date()
  ];

  errorSheet.appendRow(newRow);
}

// ====================================================================================
// SHEET MANAGEMENT
// ====================================================================================

function initializeOutputSheets() {
  const sheets = getSheetNames();
  getOrCreateSheet(sheets.VERIFIED, getVerifiedHeaders());
  getOrCreateSheet(sheets.ERRORS, getErrorHeaders());
  getOrCreateSheet(sheets.REVIEW, getReviewHeaders());
}

function getOrCreateSheet(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  
  if (!sheet) {
    sheet = ss.insertSheet(name);
    if (headers && headers.length > 0) {
      sheet.getRange(1, 1, 1, headers.length)
        .setValues([headers])
        .setFontWeight('bold')
        .setBackground('#e8eaf6');
      sheet.setFrozenRows(1);
    }
    logMessage(`Created sheet: ${name}`);
  }
  
  return sheet;
}

function getVerifiedHeaders() {
  return [
    'Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP',
    'API_Corrected_Name', 'API_Corrected_Phone', 'API_Corrected_Address',
    'API_Place_ID', 'Source_State', 'Provider_Type', 'Confidence_Score',
    'Verification_Date'
  ];
}

function getErrorHeaders() {
  return [
    'Office Name', 'Address', 'City', 'State', 'ZIP', 
    'Provider_Type', 'Original_Row', 'Error_Note', 'Date_Added'
  ];
}

function getReviewHeaders() {
  return [
    'Row_ID', 'Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP',
    'Provider_Type', 'Confidence_Score', 'Review_Priority', 'Review_Status',
    'Review_Notes', 'Reviewer', 'Review_Date', 'Final_Status'
  ];
}

function buildColumnMap(headers) {
  const map = {};
  const required = [
    'Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP', 'NPI'
  ];

  required.forEach(col => {
    map[col] = headers.indexOf(col);
  });

  // Optional columns (for network detection, etc.)
  const optional = ['Notes'];
  optional.forEach(col => {
    const idx = headers.indexOf(col);
    if (idx !== -1) {
      map[col] = idx;
    }
  });

  return map;
}

// ====================================================================================
// PROGRESS TRACKING
// ====================================================================================

function getProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  
  return {
    lastProcessedRow: parseInt(props.getProperty(key) || '1')
  };
}

function saveProcessingProgress(row) {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  props.setProperty(key, row.toString());
}

function resetProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATES}`;
  props.setProperty(key, '1');
}

function finishProcessing() {
  logMessage('Processing complete!');
  deleteTriggers();
  
  SpreadsheetApp.getUi().alert('Verification Complete!',
    'All providers have been processed.\n\nCheck the verified, review, and error sheets.',
    SpreadsheetApp.getUi().ButtonSet.OK);
}

// ====================================================================================
// TRIGGER MANAGEMENT
// ====================================================================================

function scheduleTrigger() {
  deleteTriggers();
  ScriptApp.newTrigger('processNextBatch')
    .timeBased()
    .after(2 * 60 * 1000)
    .create();
  logMessage('Next batch scheduled in 2 minutes');
}

function deleteTriggers() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'processNextBatch') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

function pauseProcessing() {
  deleteTriggers();
  SpreadsheetApp.getUi().alert('Processing paused. Use Resume to continue.');
}

function resumeProcessing() {
  processNextBatch();
  SpreadsheetApp.getUi().alert('Processing resumed.');
}

function resetProcessing() {
  const response = SpreadsheetApp.getUi().alert('Reset Processing',
    'This will reset progress and stop all processing.\n\nContinue?',
    SpreadsheetApp.getUi().ButtonSet.YES_NO);

  if (response === SpreadsheetApp.getUi().Button.YES) {
    deleteTriggers();
    resetProcessingProgress();
    SpreadsheetApp.getUi().alert('Processing reset. You can start fresh.');
  }
}

// ====================================================================================
// MANUAL REVIEW TOOLS
// ====================================================================================

function openReviewQueue() {
  const sheets = getSheetNames();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const reviewSheet = ss.getSheetByName(sheets.REVIEW);

  if (!reviewSheet || reviewSheet.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert('Review queue is empty.');
    return;
  }

  reviewSheet.activate();
  SpreadsheetApp.getUi().alert('Review Queue',
    'Red = High Priority\nOrange = Medium Priority\nGreen = Completed',
    SpreadsheetApp.getUi().ButtonSet.OK);
}

function getActiveRowData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();
  const config = getConfig();

  if (!range || range.getRow() < 2) {
    return { error: "Please select a data row" };
  }

  const row = range.getRow();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const values = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];

  const data = {};
  headers.forEach((h, i) => { data[h] = values[i]; });

  const searchQuery = [
    data['Office Name'],
    data['Address'],
    data['City'],
    data['State']
  ].filter(Boolean).join(' ');

  return {
    data: data,
    row: row,
    sheetName: sheet.getName(),
    providerType: config.PROVIDER_TYPE,
    states: config.TARGET_STATES,
    searchUrl: `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`,
    confidence: data['Confidence_Score'] || 0
  };
}

function updateRowStatus(rowNum, sheetName, status, notes) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
    if (!sheet) return `Error: Sheet not found`;

    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    
    const updates = {
      'Review_Status': 'Completed',
      'Review_Notes': notes,
      'Reviewer': Session.getActiveUser().getEmail(),
      'Review_Date': new Date(),
      'Final_Status': status === 'OPERATIONAL' ? 'Operational' : 
                      status === 'CLOSED' ? 'Closed' : 'Needs Info'
    };

    Object.keys(updates).forEach(col => {
      const idx = headers.indexOf(col);
      if (idx >= 0) {
        sheet.getRange(rowNum, idx + 1).setValue(updates[col]);
      }
    });

    const color = status === 'OPERATIONAL' ? '#d9ead3' :
                  status === 'CLOSED' ? '#f4cccc' : '#fff2cc';
    sheet.getRange(rowNum, 1, 1, sheet.getLastColumn()).setBackground(color);

    return `Row ${rowNum} updated successfully!`;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}

function moveToNextRow() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();
  if (!range) return null;

  const currentRow = range.getRow();
  const lastRow = sheet.getLastRow();

  if (currentRow < lastRow) {
    const nextRow = currentRow + 1;
    sheet.getRange(nextRow, 1).activate();
    return nextRow;
  }

  return null;
}

// ====================================================================================
// UTILITY FUNCTIONS
// ====================================================================================

function calculateSimilarity(str1, str2) {
  str1 = (str1 || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  str2 = (str2 || '').toLowerCase().replace(/[^a-z0-9]/g, '');

  if (str1 === str2) return 1;
  if (!str1 || !str2) return 0;

  const matrix = Array(str2.length + 1).fill(null).map(() => Array(str1.length + 1).fill(null));
  
  for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
  for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;

  for (let j = 1; j <= str2.length; j++) {
    for (let i = 1; i <= str1.length; i++) {
      const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[j][i] = Math.min(
        matrix[j][i - 1] + 1,
        matrix[j - 1][i] + 1,
        matrix[j - 1][i - 1] + cost
      );
    }
  }

  return 1 - (matrix[str2.length][str1.length] / Math.max(str1.length, str2.length));
}

function normalizePhone(phone) {
  if (!phone) return '';
  // Extract main phone number before extension (matches ToolboxSuite logic)
  const phoneStr = phone.toString();
  // Split at 'x' or 'ext' to remove extension, then strip non-digits
  const mainPhone = phoneStr.split(/\s*[xX]|ext/i)[0].replace(/\D/g, '');
  // Return last 10 digits (handles country codes like +1)
  return mainPhone.slice(-10);
}

function logMessage(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${message}`);
  Logger.log(message);
}

function getApiCallCount() {
  const props = PropertiesService.getScriptProperties();
  return parseInt(props.getProperty('apiCallCount') || '0');
}

function incrementApiCallCount(count) {
  const props = PropertiesService.getScriptProperties();
  const current = getApiCallCount();
  props.setProperty('apiCallCount', (current + count).toString());
}

function showApiUsage() {
  const ui = SpreadsheetApp.getUi();
  const count = getApiCallCount();
  const limit = DEFAULT_CONFIG.API_CALL_LIMIT;
  const remaining = limit - count;
  const percentUsed = Math.round((count / limit) * 100);

  let statusEmoji = '✅';
  if (count >= limit) statusEmoji = '🛑';
  else if (count >= DEFAULT_CONFIG.API_WARNING_THRESHOLD) statusEmoji = '⚠️';

  const response = ui.alert('API Usage Status',
    `${statusEmoji} API Calls Used: ${count} / ${limit} (${percentUsed}%)\n` +
    `Remaining: ${remaining} calls\n\n` +
    'Reset counter?',
    ui.ButtonSet.YES_NO);

  if (response === ui.Button.YES) {
    PropertiesService.getScriptProperties().setProperty('apiCallCount', '0');
    ui.alert('Counter Reset', 'API call counter reset to 0', ui.ButtonSet.OK);
  }
}

// ====================================================================================
// ADDITIONAL TOOLS
// ====================================================================================

function createGoogleSearchLinks() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data.shift();
  
  const officeIdx = headers.indexOf('Office Name');
  if (officeIdx === -1) {
    SpreadsheetApp.getUi().alert('Error: Office Name column not found');
    return;
  }

  const addressIdx = headers.indexOf('Address');
  const cityIdx = headers.indexOf('City');
  const stateIdx = headers.indexOf('State');

  const richText = data.map(row => {
    const office = row[officeIdx];
    if (office) {
      const parts = [office, row[addressIdx], row[cityIdx], row[stateIdx]].filter(Boolean);
      const url = `https://www.google.com/search?q=${encodeURIComponent(parts.join(' '))}`;
      return [SpreadsheetApp.newRichTextValue().setText(office).setLinkUrl(url).build()];
    }
    return [office];
  });

  if (richText.length > 0) {
    sheet.getRange(2, officeIdx + 1, richText.length, 1).setRichTextValues(richText);
    SpreadsheetApp.getUi().alert('Search links created!');
  }
}

function formatVerifiedSheet() {
  const sheets = getSheetNames();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName(sheets.VERIFIED);

  if (!source || source.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert('No verified data to format');
    return;
  }

  const data = source.getDataRange().getValues();
  const headers = data.shift();
  
  const formatted = data.map(row => [
    row[0], // Office Name
    row[1], // Phone
    row[2], // Address
    row[3], // City
    row[4], // State
    row[5]  // ZIP
  ]);

  let destSheet = ss.getSheetByName(sheets.FORMATTED);
  if (destSheet) {
    destSheet.clear();
  } else {
    destSheet = ss.insertSheet(sheets.FORMATTED);
  }

  const destHeaders = ['Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP'];
  destSheet.getRange(1, 1, 1, 6).setValues([destHeaders]).setFontWeight('bold').setBackground('#e8eaf6');
  destSheet.getRange(2, 1, formatted.length, 6).setValues(formatted);
  destSheet.activate();

  SpreadsheetApp.getUi().alert(`Formatted ${formatted.length} providers`);
}

function fixCapitalizationInSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const officeIdx = headers.indexOf('Office Name');

  if (officeIdx === -1) {
    SpreadsheetApp.getUi().alert('Office Name column not found');
    return;
  }

  let fixed = 0;
  for (let i = 1; i < data.length; i++) {
    const original = data[i][officeIdx];
    if (original && typeof original === 'string') {
      const corrected = fixCapitalization(original);
      if (corrected !== original) {
        sheet.getRange(i + 1, officeIdx + 1).setValue(corrected);
        fixed++;
      }
    }
  }

  SpreadsheetApp.getUi().alert(`Fixed ${fixed} entries`);
}

// CONSOLIDATED CAPITALIZATION FIX - Bug-Free Version
// Fixes: "Md." → "MD.", "Do." → "DO.", "women's" → "Women's" (not "Women'S")

// Configuration for capitalization rules
const ALL_CAPS_STRINGS = [
  'MD', 'DO', 'PA', 'NP', 'RN', 'FNP', 'DNP', 'CRNP', 'ARNP', 'APRN',
  'MSN', 'PMHNP', 'WHNP', 'ANP', 'GNP', 'CRNA', 'CFNP', 'CWOCN',
  'LLC', 'PC', 'PLLC', 'INC', 'DDS', 'DPM', 'PHD', 'MS', 'MHS',
  'II', 'III', 'IV'
];

const MIXED_CASE_SUFFIXES = {
  'JR': 'Jr',
  'SR': 'Sr'
};

/**
 * Fix capitalization issues in provider names.
 * Handles: ALL CAPS, ProperCase damage, Mc/Mac, apostrophes, hyphens, periods
 *
 * BUGS FIXED:
 * - "Md." now becomes "MD." (not "Md.")
 * - "Do." now becomes "DO." (not "Do.")
 * - "women's" now becomes "Women's" (not "Women'S")
 *
 * @param {string} name - The name to fix
 * @returns {string} - The corrected name
 */
function fixCapitalization(name) {
  if (!name || typeof name !== 'string') return name;

  name = name.trim();

  // Step 1: Fix credential periods (handles all cases like M.D., m.d., M.d, etc.)
  // The 'i' flag makes the regex case-insensitive.
  name = name.replace(/\b([a-z])\.([a-z])\.([a-z])\.([a-z])\b/gi, (m, a, b, c, d) =>
    a.toUpperCase() + b.toUpperCase() + c.toUpperCase() + d.toUpperCase());
  name = name.replace(/\b([a-z])\.([a-z])\.([a-z])\b/gi, (m, a, b, c) =>
    a.toUpperCase() + b.toUpperCase() + c.toUpperCase());
  name = name.replace(/\b([a-z])\.([a-z])\b/gi, (m, a, b) =>
    a.toUpperCase() + b.toUpperCase());

  // Step 2: Add periods after single initials: Robert L Cossman → Robert L. Cossman
  name = name.replace(/\b([A-Z])\s+(?=[A-Z][a-z])/g, '$1. ');

  // Step 3: Process word by word
  const words = name.split(/\s+/);
  const fixed = [];

  for (let word of words) {
    const match = word.match(/^(.+?)([.,]*)$/);
    if (!match) {
      fixed.push(word);
      continue;
    }

    const cleanWord = match[1];
    const punctuation = match[2];
    const upperCleanWord = cleanWord.toUpperCase();

    // Check for strings that should be ALL CAPS (e.g., MD, PHD)
    if (ALL_CAPS_STRINGS.includes(upperCleanWord)) {
      fixed.push(upperCleanWord + punctuation);
    }
    // Check for suffixes with specific mixed casing (e.g., Jr, Sr)
    else if (MIXED_CASE_SUFFIXES[upperCleanWord]) {
      fixed.push(MIXED_CASE_SUFFIXES[upperCleanWord] + punctuation);
    }
    // Single initials with period
    else if (/^[A-Z]\.$/.test(word)) {
      fixed.push(word.toUpperCase());
    }
    // Mc names (Mcintosh → McIntosh)
    else if (cleanWord.toLowerCase().startsWith('mc') && cleanWord.length > 2) {
      const formatted = 'Mc' + cleanWord.charAt(2).toUpperCase() + cleanWord.slice(3).toLowerCase();
      fixed.push(formatted + punctuation);
    }
    // Mac names (Macdonald → MacDonald)
    else if (cleanWord.toLowerCase().startsWith('mac') && cleanWord.length > 3) {
      const formatted = 'Mac' + cleanWord.charAt(3).toUpperCase() + cleanWord.slice(4).toLowerCase();
      fixed.push(formatted + punctuation);
    }
    // Hyphens (mary-anne → Mary-Anne)
    else if (cleanWord.includes('-')) {
      const parts = cleanWord.split('-');
      const formatted = parts.map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join('-');
      fixed.push(formatted + punctuation);
    }
    // Apostrophes (o'donnell → O'Donnell, women's → Women's)
    else if (cleanWord.includes("'")) {
      const parts = cleanWord.split("'");
      let afterApostrophe = '';
      if (parts[1]) {
        // FIX: If just possessive 's', keep lowercase; otherwise capitalize (O'Donnell)
        afterApostrophe = parts[1].toLowerCase() === 's' ? 's' :
                         parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase();
      }
      const formatted = parts[0].charAt(0).toUpperCase() + parts[0].slice(1).toLowerCase() +
        "'" + afterApostrophe;
      fixed.push(formatted + punctuation);
    }
    // Regular word
    else {
      const formatted = cleanWord.charAt(0).toUpperCase() + cleanWord.slice(1).toLowerCase();
      fixed.push(formatted + punctuation);
    }
  }

  let finalName = fixed.join(' ');

  // Strip the final period if it exists
  if (finalName.endsWith('.')) {
    finalName = finalName.slice(0, -1);
  }

  return finalName;
}

function findAndRemoveDuplicates() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data.shift();
  
  const phoneIdx = headers.indexOf('Phone Number');
  const placeIdx = headers.indexOf('API_Place_ID');
  
  const seen = new Set();
  const duplicates = [];

  data.forEach((row, i) => {
    const phone = row[phoneIdx];
    const placeId = row[placeIdx];
    const key = `${phone}|${placeId}`;
    
    if ((phone && seen.has(phone)) || (placeId && seen.has(placeId))) {
      duplicates.push(i + 2);
    } else {
      if (phone) seen.add(phone);
      if (placeId) seen.add(placeId);
    }
  });

  if (duplicates.length > 0) {
    const response = SpreadsheetApp.getUi().alert(
      `Found ${duplicates.length} duplicates. Remove?`,
      SpreadsheetApp.getUi().ButtonSet.YES_NO);

    if (response === SpreadsheetApp.getUi().Button.YES) {
      duplicates.reverse().forEach(row => sheet.deleteRow(row));
      SpreadsheetApp.getUi().alert(`Removed ${duplicates.length} duplicates`);
    }
  } else {
    SpreadsheetApp.getUi().alert('No duplicates found');
  }
}

function generateStatsReport() {
  const config = getConfig();
  const sheets = getSheetNames();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  const verified = ss.getSheetByName(sheets.VERIFIED);
  const errors = ss.getSheetByName(sheets.ERRORS);
  const review = ss.getSheetByName(sheets.REVIEW);

  const stats =
    `Provider Type: ${config.PROVIDER_TYPE}\n` +
    `Target States: ${config.TARGET_STATES}\n\n` +
    `Verified: ${verified ? verified.getLastRow() - 1 : 0}\n` +
    `Needs Review: ${review ? review.getLastRow() - 1 : 0}\n` +
    `Errors: ${errors ? errors.getLastRow() - 1 : 0}`;

  SpreadsheetApp.getUi().alert('Statistics', stats, SpreadsheetApp.getUi().ButtonSet.OK);
}