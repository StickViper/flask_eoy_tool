/**
 * Universal Provider Verification Suite (v8.0 - RESTRUCTURED)
 * Complete rewrite with better architecture
 */

// ====================================================================================
// CONFIGURATION MANAGEMENT
// ====================================================================================

const DEFAULT_CONFIG = {
  PROVIDER_TYPE: 'PCP',
  TARGET_STATE: 'TX',
  USE_UNIFIED_OUTPUT: true,
  MAX_BATCHES_PER_RUN: 0,
  BATCH_SIZE: 25,
  MAX_EXECUTION_TIME: 270000,
  NAME_SIMILARITY_THRESHOLD: 0.65,
  HIGH_CONFIDENCE_THRESHOLD: 0.85,
  REQUIRE_PHONE_FOR_OPERATIONAL: true,
  CACHE_DURATION: 21600,
  FIX_CAPITALIZATION: true,
  API_CALL_LIMIT: 3000,  // Hard limit before charges apply
  API_WARNING_THRESHOLD: 2800  // Warn when approaching limit
};

function getConfig() {
  const props = PropertiesService.getScriptProperties();
  
  return {
    PROVIDER_TYPE: props.getProperty('providerType') || DEFAULT_CONFIG.PROVIDER_TYPE,
    TARGET_STATE: props.getProperty('targetState') || DEFAULT_CONFIG.TARGET_STATE,
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
  if (configData.state) {
    props.setProperty('targetState', configData.state);
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
  const prefix = `${config.PROVIDER_TYPE}_${config.TARGET_STATE}`;
  
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
  
  ui.createMenu(`⚡ Provider Suite (${config.PROVIDER_TYPE} - ${config.TARGET_STATE})`)
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
    `Target State: ${config.TARGET_STATE}\n` +
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
    `Ready to process ${config.PROVIDER_TYPE} providers in ${config.TARGET_STATE}\n\n` +
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

  processNextBatch();

  ui.alert('Processing Started',
    'Verification is running in the background.\n\nYou can close this sheet.',
    ui.ButtonSet.OK);
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
  return {
    url: 'https://places.googleapis.com/v1/places:searchText',
    method: 'post',
    contentType: 'application/json',
    headers: {
      'X-Goog-Api-Key': apiKey,
      'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.businessStatus'
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
  
  const result = {
    placeId: place.id,
    status: place.businessStatus || 'UNKNOWN',
    correctedName: place.displayName?.text || '',
    correctedPhone: place.nationalPhoneNumber || '',
    correctedAddress: place.formattedAddress || '',
    confidence: 0
  };

  // Calculate confidence
  let points = 0;
  let maxPoints = 100;

  // Name similarity (40%)
  if (rowInfo.officeName && result.correctedName) {
    points += calculateSimilarity(rowInfo.officeName, result.correctedName) * 40;
  }

  // Phone match (30%)
  if (rowInfo.phone && result.correctedPhone) {
    if (normalizePhone(rowInfo.phone) === normalizePhone(result.correctedPhone)) {
      points += 30;
    }
  } else if (result.correctedPhone) {
    points += 15;
  }

  // Business status (30%)
  if (result.status === 'OPERATIONAL') {
    points += 30;
  } else if (result.status === 'CLOSED_TEMPORARILY') {
    points += 15;
  }

  result.confidence = points / maxPoints;

  // Determine success
  result.success = result.confidence >= config.HIGH_CONFIDENCE_THRESHOLD && 
                   result.status === 'OPERATIONAL';
  result.needsReview = result.confidence >= config.NAME_SIMILARITY_THRESHOLD && 
                       result.confidence < config.HIGH_CONFIDENCE_THRESHOLD;
  result.notes = result.success ? 'Verified' : 
                 result.needsReview ? `Low confidence (${Math.round(result.confidence * 100)}%)` :
                 'Failed verification';

  return result;
}

function recordResult(rowNumber, rowData, colMap, verification) {
  const config = getConfig();
  const sheets = getSheetNames();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  if (verification.success) {
    // Add to verified sheet
    const verifiedSheet = getOrCreateSheet(sheets.VERIFIED, getVerifiedHeaders());
    const newRow = [
      rowData[colMap['Office Name']],
      rowData[colMap['Phone Number']],
      rowData[colMap['Address']],
      rowData[colMap['City']],
      rowData[colMap['State']],
      rowData[colMap['ZIP']],
      verification.correctedName,
      verification.correctedPhone,
      verification.correctedAddress,
      verification.placeId,
      config.TARGET_STATE,
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
      rowData[colMap['Office Name']],
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
  const errorSheet = getOrCreateSheet(sheets.ERRORS, getErrorHeaders());
  
  const newRow = [
    rowData[colMap['Office Name']] || '',
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
  
  return map;
}

// ====================================================================================
// PROGRESS TRACKING
// ====================================================================================

function getProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATE}`;
  
  return {
    lastProcessedRow: parseInt(props.getProperty(key) || '1')
  };
}

function saveProcessingProgress(row) {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATE}`;
  props.setProperty(key, row.toString());
}

function resetProcessingProgress() {
  const props = PropertiesService.getScriptProperties();
  const config = getConfig();
  const key = `progress_${config.PROVIDER_TYPE}_${config.TARGET_STATE}`;
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
    state: config.TARGET_STATE,
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
  return phone.toString().replace(/\D/g, '').slice(-10);
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

function fixCapitalization(text) {
  if (!text) return text;
  
  const protected = ['MD', 'DO', 'PA', 'NP', 'RN', 'PhD', 'LLC', 'PC', 'PLLC', 'II', 'III', 'IV', 'Jr', 'Sr'];
  
  return text.split(/\s+/).map(word => {
    if (protected.includes(word.toUpperCase())) {
      return word.toUpperCase();
    }
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');
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
    `Target State: ${config.TARGET_STATE}\n\n` +
    `Verified: ${verified ? verified.getLastRow() - 1 : 0}\n` +
    `Needs Review: ${review ? review.getLastRow() - 1 : 0}\n` +
    `Errors: ${errors ? errors.getLastRow() - 1 : 0}`;

  SpreadsheetApp.getUi().alert('Statistics', stats, SpreadsheetApp.getUi().ButtonSet.OK);
}