/**
 * Universal Provider Verification Suite (v6.0)
 * 
 * Flexible system for verifying healthcare providers (PCPs, OBGYNs, or any specialty).
 * Works across all states with dynamic configuration.
 * 
 * MAJOR IMPROVEMENTS IN v6.0:
 * - Provider-type agnostic (PCPs, OBGYNs, or custom)
 * - State-agnostic with dynamic configuration
 * - Unified "All_Verified_Providers" sheet option
 * - Smart capitalization fixes for names
 * - Improved duplicate handling
 * - Better error recovery
 * 
 * HOW TO USE:
 * 1. Set your Google Places API key in Script Properties
 * 2. Configure PROVIDER_CONFIG below for your use case
 * 3. Save all scripts and reload the spreadsheet
 * 4. Use the "⚡ Provider Suite" menu to run processes
 */

// vv---------------------------------------------------------------------------------vv
// TODO: USER - Master Configuration - UPDATE THESE VALUES
const PROVIDER_CONFIG = {
  // ==== PROVIDER TYPE SETTINGS ====
  PROVIDER_TYPE: 'PCP',  // Options: 'PCP', 'OBGYN', 'SPECIALIST'
  TARGET_STATE: 'TX',     // 2-letter state code (e.g., 'FL', 'CA', 'NY')
  
  // ==== SHEET NAMING STRATEGY ====
  USE_UNIFIED_OUTPUT: true,  // If true, all states go to one master sheet
  
  // Dynamic sheet names (will auto-append state if not unified)
  SHEETS: {
    // Input sheet with raw provider data
    MASTER: function() {
      return `${PROVIDER_CONFIG.PROVIDER_TYPE}_${PROVIDER_CONFIG.TARGET_STATE}_import`;
    },
    
    // Successfully verified providers
    VERIFIED: function() {
      if (PROVIDER_CONFIG.USE_UNIFIED_OUTPUT) {
        return 'nppes_verified';  // Single sheet for all states
      }
      return `${PROVIDER_CONFIG.PROVIDER_TYPE}_${PROVIDER_CONFIG.TARGET_STATE}_verified`;
    },
    
    // Providers needing manual review
    ERRORS: function() {
      if (PROVIDER_CONFIG.USE_UNIFIED_OUTPUT) {
        return 'nppes_errors';
      }
      return `${PROVIDER_CONFIG.PROVIDER_TYPE}_${PROVIDER_CONFIG.TARGET_STATE}_errors`;
    },
    
    // Formatted export-ready data
    FORMATTED: function() {
      if (PROVIDER_CONFIG.USE_UNIFIED_OUTPUT) {
        return 'nppes_formatted';
      }
      return `${PROVIDER_CONFIG.PROVIDER_TYPE}_${PROVIDER_CONFIG.TARGET_STATE}_formatted`;
    }
  },
  
  // ==== COLUMN CONFIGURATION ====
  // These should match your CSV output from the NPPES filter script
  INPUT_COLUMNS: {
    OFFICE: 'Office Name',
    PHONE: 'Phone Number',
    ADDRESS: 'Address',
    CITY: 'City',
    STATE: 'State',
    ZIP: 'ZIP',
    NPI: 'NPI',  // Added for better tracking
    PROVIDER_TYPE_COL: 'Provider Type'  // To track PCP vs OBGYN
  },
  
  OUTPUT_COLUMNS: {
    STATUS: 'Verification_Status',
    NOTES: 'Verification_Notes',
    CORRECTED_NAME: 'API_Corrected_Name',
    CORRECTED_PHONE: 'API_Corrected_Phone',
    CORRECTED_ADDRESS: 'API_Corrected_Address',
    PLACE_ID: 'API_Place_ID',
    VERIFIED_DATE: 'Verification_Date',
    STATE_SOURCE: 'Source_State',  // Track which state this came from
    PROVIDER_TYPE_VERIFIED: 'Provider_Type'  // Track provider type
  },
  
  // ==== SEARCH CUSTOMIZATION ====
  // Customize search queries based on provider type
  SEARCH_KEYWORDS: {
    'PCP': ['primary care', 'family medicine', 'internal medicine'],
    'OBGYN': ['obgyn', 'gynecologist', 'womens health'],
    'SPECIALIST': []  // Add custom keywords as needed
  },
  
  // ==== VERIFICATION SETTINGS ====
  NAME_SIMILARITY_THRESHOLD: 0.65,  // Lowered for PCPs (often have different DBA names)
  REQUIRE_PHONE_FOR_OPERATIONAL: true,  // Stricter for PCPs since you need to call
  
  // ==== SYSTEM SETTINGS ====
  SCRIPT_PROPERTY_KEY: function() {
    return `lastProcessed_${PROVIDER_CONFIG.PROVIDER_TYPE}_${PROVIDER_CONFIG.TARGET_STATE}`;
  },
  BATCH_SIZE: 25,
  MAX_EXECUTION_TIME: 270000,  // 4.5 minutes
  
  // ==== CAPITALIZATION FIX SETTINGS ====
  FIX_CAPITALIZATION: true,  // Auto-fix improper capitalization
  PROTECTED_STRINGS: [  // Don't change these
    'MD', 'DO', 'PA', 'NP', 'RN', 'PhD', 'LLC', 'PC', 'PLLC',
    'II', 'III', 'IV', 'Jr', 'Sr', 'USA', 'US',
    'PCP', 'OBGYN', 'ER', 'ICU', 'NICU', 'OR'
  ]
};
// ^^---------------------------------------------------------------------------------^^

//====================================================================================
// SECTION 0: UI MENU & INITIALIZATION
//====================================================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  const menuTitle = `⚡ Provider Suite (${PROVIDER_CONFIG.PROVIDER_TYPE} - ${PROVIDER_CONFIG.TARGET_STATE})`;
  
  ui.createMenu(menuTitle)
    .addItem('📋 View Current Configuration', 'showCurrentConfig')
    .addItem('🔄 Change State/Provider Type', 'showConfigDialog')
    .addSeparator()
    .addItem('▶️ Manual Verification Sidebar', 'showVerificationSidebar')
    .addSeparator()
    .addSubMenu(ui.createMenu('🤖 Automated Verification')
      .addItem('🚀 Start Full Verification', 'startProcessing')
      .addItem('⏸️ Pause Verification', 'pauseProcessing')
      .addItem('▶️ Resume Verification', 'resumeProcessing')
      .addItem('🛑 Stop & Reset', 'resetProcessing'))
    .addSeparator()
    .addSubMenu(ui.createMenu('🛠️ Tools')
      .addItem('🔗 Create Search Links', 'createGoogleSearchLinks')
      .addItem('📄 Format for Export', 'formatVerifiedSheet')
      .addItem('✨ Fix Capitalization', 'fixCapitalizationInSheet')
      .addItem('🔍 Find Duplicates', 'findDuplicates')
      .addItem('📊 Generate Stats Report', 'generateStatsReport'))
    .addToUi();
}

function showCurrentConfig() {
  const ui = SpreadsheetApp.getUi();
  const config = `
Current Configuration:
━━━━━━━━━━━━━━━━━━━━
Provider Type: ${PROVIDER_CONFIG.PROVIDER_TYPE}
Target State: ${PROVIDER_CONFIG.TARGET_STATE}
Output Mode: ${PROVIDER_CONFIG.USE_UNIFIED_OUTPUT ? 'Unified (All States Together)' : 'Separate by State'}

Sheet Names:
• Master: ${PROVIDER_CONFIG.SHEETS.MASTER()}
• Verified: ${PROVIDER_CONFIG.SHEETS.VERIFIED()}
• Errors: ${PROVIDER_CONFIG.SHEETS.ERRORS()}
• Formatted: ${PROVIDER_CONFIG.SHEETS.FORMATTED()}
━━━━━━━━━━━━━━━━━━━━
  `;
  ui.alert('Configuration', config, ui.ButtonSet.OK);
}

function showConfigDialog() {
  const html = HtmlService.createHtmlOutputFromFile('ConfigurationDialog')
    .setTitle('Configure Provider Type & State')
    .setWidth(400)
    .setHeight(300);
  SpreadsheetApp.getUi().showModalDialog(html, 'Provider Configuration');
}

//====================================================================================
// SECTION 1: AUTOMATED VERIFICATION ENGINE
//====================================================================================

function startProcessing() {
  const ui = SpreadsheetApp.getUi();
  
  // Confirm configuration
  const response = ui.alert(
    'Start Verification',
    `Ready to process ${PROVIDER_CONFIG.PROVIDER_TYPE} providers in ${PROVIDER_CONFIG.TARGET_STATE}.\n\nContinue?`,
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) return;
  
  _deleteTriggers();
  PropertiesService.getScriptProperties().setProperty(PROVIDER_CONFIG.SCRIPT_PROPERTY_KEY(), '1');
  _log(`Verification started for ${PROVIDER_CONFIG.PROVIDER_TYPE} in ${PROVIDER_CONFIG.TARGET_STATE}`);
  
  // Set up sheets with appropriate headers
  const verifiedHeaders = [
    'Office Name', 'Phone Number', 'Address',
    'API_Corrected_Name', 'API_Corrected_Phone', 'API_Corrected_Address',
    'API_Place_ID', 'Source_State', 'Provider_Type', 'Verification_Date'
  ];
  
  const errorHeaders = [
    'Office Name', 'Address', 'State', 'Provider_Type', 'Original_Row', 'Error_Note', 'Date_Added'
  ];
  
  _getOrCreateSheet(PROVIDER_CONFIG.SHEETS.VERIFIED(), verifiedHeaders);
  _getOrCreateSheet(PROVIDER_CONFIG.SHEETS.ERRORS(), errorHeaders);
  
  // Add output columns to master sheet
  const masterSheet = getSheet(PROVIDER_CONFIG.SHEETS.MASTER());
  if (!masterSheet) {
    ui.alert(`Error: Master sheet "${PROVIDER_CONFIG.SHEETS.MASTER()}" not found!`);
    return;
  }
  
  _addMissingColumns(masterSheet, Object.values(PROVIDER_CONFIG.OUTPUT_COLUMNS));
  
  processNextBatch_API();
}

function processNextBatch_API() {
  const scriptStartTime = new Date().getTime();
  const apiKey = getApiKey();
  if (!apiKey) {
    _log('CRITICAL: No API key found!', 'ERROR');
    return;
  }
  
  const masterSheet = getSheet(PROVIDER_CONFIG.SHEETS.MASTER());
  if (!masterSheet) {
    _log(`Master sheet "${PROVIDER_CONFIG.SHEETS.MASTER()}" not found`, 'ERROR');
    return;
  }
  
  const columnMap = _getColumnMap(masterSheet);
  const lastRow = masterSheet.getLastRow();
  const lastProcessed = parseInt(
    PropertiesService.getScriptProperties().getProperty(PROVIDER_CONFIG.SCRIPT_PROPERTY_KEY()) || '1'
  );
  const startRow = lastProcessed + 1;
  
  if (startRow > lastRow) {
    _log(`All rows processed for ${PROVIDER_CONFIG.TARGET_STATE}!`, 'SUCCESS');
    _deleteTriggers();
    _showCompletionNotification();
    return;
  }
  
  const endRow = Math.min(startRow + PROVIDER_CONFIG.BATCH_SIZE - 1, lastRow);
  _log(`Processing rows ${startRow} to ${endRow} of ${lastRow}`);
  
  const range = masterSheet.getRange(startRow, 1, endRow - startRow + 1, masterSheet.getLastColumn());
  const data = range.getValues();
  
  const batchResults = processBatch(data, startRow, columnMap, apiKey);
  updateSheetsWithResults(batchResults, columnMap);
  
  PropertiesService.getScriptProperties().setProperty(
    PROVIDER_CONFIG.SCRIPT_PROPERTY_KEY(), 
    endRow.toString()
  );
  
  // Continue processing
  if (endRow < lastRow && (new Date().getTime() - scriptStartTime) < PROVIDER_CONFIG.MAX_EXECUTION_TIME) {
    processNextBatch_API();
  } else if (endRow < lastRow) {
    _createTrigger();
  }
}

function processBatch(dataRows, startRow, columnMap, apiKey) {
  const cache = CacheService.getScriptCache();
  const results = [];
  const searchRequests = [];
  const rowsToProcess = [];
  
  // Build search queries with provider-type specific keywords
  dataRows.forEach((row, i) => {
    const currentRow = startRow + i;
    const officeName = row[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.OFFICE]];
    const address = row[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.ADDRESS]];
    const city = row[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.CITY]];
    const state = row[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.STATE]];
    
    if (!officeName || !address) {
      results.push({
        originalRow: currentRow,
        status: 'Error',
        notes: 'Missing required data'
      });
      return;
    }
    
    // Build enhanced search query
    let searchQuery = `${officeName} ${address} ${city} ${state}`;
    
    // Add provider-type specific keywords for better results
    const keywords = PROVIDER_CONFIG.SEARCH_KEYWORDS[PROVIDER_CONFIG.PROVIDER_TYPE] || [];
    if (keywords.length > 0 && Math.random() > 0.7) {  // Add keywords 30% of the time
      searchQuery += ' ' + keywords[0];
    }
    
    const cacheKey = `place_${searchQuery}`.replace(/[^a-zA-Z0-9]/g, '');
    const cachedResult = cache.get(cacheKey);
    
    if (cachedResult) {
      results.push({
        originalRow: currentRow,
        ...JSON.parse(cachedResult),
        fromCache: true
      });
    } else {
      rowsToProcess.push({
        originalRow: currentRow,
        cacheKey: cacheKey,
        officeName: officeName,
        originalData: row
      });
      searchRequests.push(_buildPlaceSearchRequest(searchQuery, apiKey));
    }
  });
  
  // Process API requests in batch
  if (searchRequests.length > 0) {
    _log(`Searching for ${searchRequests.length} places...`);
    const responses = UrlFetchApp.fetchAll(searchRequests);
    
    responses.forEach((response, i) => {
      const rowInfo = rowsToProcess[i];
      try {
        const placeData = JSON.parse(response.getContentText());
        const result = _processPlaceData(placeData, rowInfo);
        
        // Cache the result
        cache.put(rowInfo.cacheKey, JSON.stringify(result), 21600);  // 6 hours
        results.push({
          originalRow: rowInfo.originalRow,
          ...result
        });
      } catch (e) {
        results.push({
          originalRow: rowInfo.originalRow,
          status: 'Error',
          notes: `API Error: ${e.message}`
        });
      }
    });
  }
  
  return results;
}

function updateSheetsWithResults(results, columnMap) {
  const masterSheet = getSheet(PROVIDER_CONFIG.SHEETS.MASTER());
  const verifiedSheet = getSheet(PROVIDER_CONFIG.SHEETS.VERIFIED());
  const errorSheet = getSheet(PROVIDER_CONFIG.SHEETS.ERRORS());
  
  const masterUpdates = {};
  const verifiedAppends = [];
  const errorAppends = [];
  const processedIds = _getExistingIds(verifiedSheet, 'API_Place_ID');
  
  results.forEach(result => {
    const row = result.originalRow;
    const rowData = masterSheet.getRange(row, 1, 1, masterSheet.getLastColumn()).getValues()[0];
    
    masterUpdates[row] = {};
    
    if (result.placeId && result.status === 'OPERATIONAL') {
      // Successfully verified
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.STATUS]] = 'Verified - Operational';
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.PLACE_ID]] = result.placeId;
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.CORRECTED_NAME]] = result.correctedName || '';
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.CORRECTED_PHONE]] = result.correctedPhone || '';
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.CORRECTED_ADDRESS]] = result.correctedAddress || '';
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.VERIFIED_DATE]] = new Date();
      
      // Check for duplicates
      if (!processedIds.has(result.placeId)) {
        // Apply capitalization fixes if enabled
        const officeName = PROVIDER_CONFIG.FIX_CAPITALIZATION ? 
          _fixCapitalization(rowData[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.OFFICE]]) :
          rowData[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.OFFICE]];
        
        verifiedAppends.push([
          officeName,
          rowData[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.PHONE]],
          rowData[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.ADDRESS]],
          result.correctedName || '',
          result.correctedPhone || '',
          result.correctedAddress || '',
          result.placeId,
          PROVIDER_CONFIG.TARGET_STATE,
          PROVIDER_CONFIG.PROVIDER_TYPE,
          new Date()
        ]);
        processedIds.add(result.placeId);
      } else {
        masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.NOTES]] = 'Duplicate of existing verified entry';
      }
    } else {
      // Error or needs review
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.STATUS]] = result.status || 'Error';
      masterUpdates[row][columnMap[PROVIDER_CONFIG.OUTPUT_COLUMNS.NOTES]] = result.notes || 'Verification failed';
      
      errorAppends.push([
        rowData[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.OFFICE]],
        rowData[columnMap[PROVIDER_CONFIG.INPUT_COLUMNS.ADDRESS]],
        PROVIDER_CONFIG.TARGET_STATE,
        PROVIDER_CONFIG.PROVIDER_TYPE,
        row,
        result.notes || 'Verification failed',
        new Date()
      ]);
    }
  });
  
  // Apply updates
  _batchUpdateMaster(masterSheet, masterUpdates);
  
  if (verifiedAppends.length > 0) {
    verifiedSheet.getRange(
      verifiedSheet.getLastRow() + 1, 1,
      verifiedAppends.length, verifiedAppends[0].length
    ).setValues(verifiedAppends);
    _log(`Added ${verifiedAppends.length} verified providers`);
  }
  
  if (errorAppends.length > 0) {
    errorSheet.getRange(
      errorSheet.getLastRow() + 1, 1,
      errorAppends.length, errorAppends[0].length
    ).setValues(errorAppends);
    _log(`Added ${errorAppends.length} to error review`);
  }
  
  SpreadsheetApp.flush();
}

//====================================================================================
// SECTION 2: CAPITALIZATION FIX TOOLS
//====================================================================================

function fixCapitalizationInSheet() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  const response = ui.alert(
    'Fix Capitalization',
    `This will fix capitalization in the Office Name column of "${sheet.getName()}".\n\nContinue?`,
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) return;
  
  const dataRange = sheet.getDataRange();
  const data = dataRange.getValues();
  const headers = data[0];
  
  const officeIdx = headers.indexOf('Office Name');
  if (officeIdx === -1) {
    ui.alert('Error: Could not find "Office Name" column');
    return;
  }
  
  let fixedCount = 0;
  for (let i = 1; i < data.length; i++) {
    const original = data[i][officeIdx];
    if (original && typeof original === 'string') {
      const fixed = _fixCapitalization(original);
      if (fixed !== original) {
        sheet.getRange(i + 1, officeIdx + 1).setValue(fixed);
        fixedCount++;
      }
    }
  }
  
  ui.alert(`Fixed capitalization for ${fixedCount} entries`);
}

function _fixCapitalization(text) {
  if (!text || typeof text !== 'string') return text;
  
  // Split by spaces and process each word
  const words = text.split(/\s+/);
  const fixed = words.map(word => {
    // Check if it's a protected string
    const upperWord = word.toUpperCase();
    if (PROVIDER_CONFIG.PROTECTED_STRINGS.includes(upperWord)) {
      return upperWord;
    }
    
    // Check for hyphenated words
    if (word.includes('-')) {
      return word.split('-').map(part => _capitalizeWord(part)).join('-');
    }
    
    // Check for possessives
    if (word.includes("'")) {
      const parts = word.split("'");
      return _capitalizeWord(parts[0]) + "'" + (parts[1] || '');
    }
    
    return _capitalizeWord(word);
  });
  
  return fixed.join(' ');
}

function _capitalizeWord(word) {
  if (!word) return word;
  // Special handling for 'Mc' and 'Mac' surnames
  if (word.toLowerCase().startsWith('mc') && word.length > 2) {
    return 'Mc' + word.charAt(2).toUpperCase() + word.slice(3).toLowerCase();
  }
  if (word.toLowerCase().startsWith('mac') && word.length > 3) {
    return 'Mac' + word.charAt(3).toUpperCase() + word.slice(4).toLowerCase();
  }
  // Standard title case
  return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}

//====================================================================================
// SECTION 3: LINK CREATOR & FORMATTER
//====================================================================================

function createGoogleSearchLinks() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  
  ui.alert('Creating search links... This may take a moment.');
  
  const dataRange = sheet.getDataRange();
  const data = dataRange.getValues();
  const headers = data.shift();
  
  const linkColumnIdx = headers.indexOf('Office Name');
  if (linkColumnIdx === -1) {
    ui.alert('Error: Could not find "Office Name" column');
    return;
  }
  
  const addressIdx = headers.indexOf('Address');
  const cityIdx = headers.indexOf('City');
  const stateIdx = headers.indexOf('State');
  
  const richTextValues = data.map(row => {
    const office = row[linkColumnIdx];
    if (office && typeof office === 'string') {
      const searchParts = [
        office,
        row[addressIdx] || '',
        row[cityIdx] || '',
        row[stateIdx] || ''
      ].filter(Boolean);
      
      const searchQuery = searchParts.join(' ');
      const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
      
      return [SpreadsheetApp.newRichTextValue()
        .setText(office)
        .setLinkUrl(searchUrl)
        .build()];
    }
    return [office];
  });
  
  if (richTextValues.length > 0) {
    sheet.getRange(2, linkColumnIdx + 1, richTextValues.length, 1)
      .setRichTextValues(richTextValues);
    ui.alert('Search links created successfully!');
  }
}

function formatVerifiedSheet() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sourceSheet = ss.getSheetByName(PROVIDER_CONFIG.SHEETS.VERIFIED());
  
  if (!sourceSheet) {
    ui.alert(`Source sheet "${PROVIDER_CONFIG.SHEETS.VERIFIED()}" not found`);
    return;
  }
  
  const sourceData = sourceSheet.getDataRange().getValues();
  const headers = sourceData.shift();
  
  const nameIdx = headers.indexOf('API_Corrected_Name');
  const phoneIdx = headers.indexOf('API_Corrected_Phone');
  const addressIdx = headers.indexOf('API_Corrected_Address');
  
  if (nameIdx === -1 || phoneIdx === -1 || addressIdx === -1) {
    ui.alert('Could not find required columns in verified sheet');
    return;
  }
  
  const formattedData = [];
  const addressRegex = /^(.*),\s*(.*?),\s*([A-Z]{2})\s*(\d{5})(?:[-\s]\d{4})?,?\s*USA?$/i;
  
  sourceData.forEach(row => {
    const name = row[nameIdx] || row[headers.indexOf('Office Name')];
    const phone = row[phoneIdx] || row[headers.indexOf('Phone Number')];
    const fullAddress = row[addressIdx] || row[headers.indexOf('Address')];
    
    const match = fullAddress ? fullAddress.match(addressRegex) : null;
    
    if (match) {
      formattedData.push([
        name,
        phone,
        match[1].trim(),  // Street
        match[2].trim(),  // City
        match[3].toUpperCase(),  // State
        match[4]  // ZIP
      ]);
    } else {
      // Fallback: use original columns if available
      formattedData.push([
        name,
        phone,
        fullAddress,
        row[headers.indexOf('City')] || '',
        row[headers.indexOf('State')] || '',
        row[headers.indexOf('ZIP')] || ''
      ]);
    }
  });
  
  if (formattedData.length > 0) {
    let destSheet = ss.getSheetByName(PROVIDER_CONFIG.SHEETS.FORMATTED());
    if (destSheet) {
      destSheet.clear();
    } else {
      destSheet = ss.insertSheet(PROVIDER_CONFIG.SHEETS.FORMATTED());
    }
    
    const destHeaders = ['Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP'];
    destSheet.getRange(1, 1, 1, destHeaders.length)
      .setValues([destHeaders])
      .setFontWeight('bold');
    
    destSheet.getRange(2, 1, formattedData.length, formattedData[0].length)
      .setValues(formattedData);
    
    destSheet.activate();
    ui.alert(`Formatted ${formattedData.length} providers for export`);
  } else {
    ui.alert('No data to format');
  }
}

//====================================================================================
// SECTION 4: STATS & REPORTING
//====================================================================================

function generateStatsReport() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  const verifiedSheet = ss.getSheetByName(PROVIDER_CONFIG.SHEETS.VERIFIED());
  const errorSheet = ss.getSheetByName(PROVIDER_CONFIG.SHEETS.ERRORS());
  const masterSheet = ss.getSheetByName(PROVIDER_CONFIG.SHEETS.MASTER());
  
  let stats = `
📊 PROVIDER VERIFICATION STATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provider Type: ${PROVIDER_CONFIG.PROVIDER_TYPE}
Target State: ${PROVIDER_CONFIG.TARGET_STATE}
`;
  
  if (masterSheet) {
    const totalRows = masterSheet.getLastRow() - 1;  // Minus header
    stats += `\nTotal Providers to Process: ${totalRows}`;
  }
  
  if (verifiedSheet && verifiedSheet.getLastRow() > 1) {
    const verifiedCount = verifiedSheet.getLastRow() - 1;
    stats += `\nVerified Operational: ${verifiedCount}`;
    
    // Count by state if unified output
    if (PROVIDER_CONFIG.USE_UNIFIED_OUTPUT) {
      const data = verifiedSheet.getDataRange().getValues();
      const headers = data.shift();
      const stateIdx = headers.indexOf('Source_State');
      
      if (stateIdx !== -1) {
        const stateCounts = {};
        data.forEach(row => {
          const state = row[stateIdx];
          if (state) {
            stateCounts[state] = (stateCounts[state] || 0) + 1;
          }
        });
        
        stats += '\n\nBy State:';
        Object.keys(stateCounts).sort().forEach(state => {
          stats += `\n  ${state}: ${stateCounts[state]}`;
        });
      }
    }
  }
  
  if (errorSheet && errorSheet.getLastRow() > 1) {
    const errorCount = errorSheet.getLastRow() - 1;
    stats += `\n\nNeeding Manual Review: ${errorCount}`;
  }
  
  stats += '\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
  
  ui.alert('Statistics Report', stats, ui.ButtonSet.OK);
}

function findDuplicates() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data.shift();
  
  const phoneIdx = headers.indexOf('Phone Number');
  const npiIdx = headers.indexOf('NPI');
  
  const duplicates = {
    phones: {},
    npis: {}
  };
  
  data.forEach((row, i) => {
    const phone = row[phoneIdx];
    const npi = row[npiIdx];
    
    if (phone) {
      if (!duplicates.phones[phone]) duplicates.phones[phone] = [];
      duplicates.phones[phone].push(i + 2);  // +2 for header and 0-index
    }
    
    if (npi) {
      if (!duplicates.npis[npi]) duplicates.npis[npi] = [];
      duplicates.npis[npi].push(i + 2);
    }
  });
  
  let report = 'DUPLICATE REPORT\n━━━━━━━━━━━━━━━━\n';
  let phoneDups = 0, npiDups = 0;
  
  Object.keys(duplicates.phones).forEach(phone => {
    if (duplicates.phones[phone].length > 1) {
      phoneDups++;
    }
  });
  
  Object.keys(duplicates.npis).forEach(npi => {
    if (duplicates.npis[npi].length > 1) {
      npiDups++;
    }
  });
  
  report += `Duplicate Phone Numbers: ${phoneDups}\n`;
  report += `Duplicate NPIs: ${npiDups}\n`;
  
  ui.alert('Duplicates Found', report, ui.ButtonSet.OK);
}

//====================================================================================
// SECTION 5: CORE UTILITIES
//====================================================================================

function getApiKey() {
  const apiKey = PropertiesService.getScriptProperties().getProperty('PLACES_API_KEY');
  if (!apiKey) {
    SpreadsheetApp.getUi().alert(
      'API Key Missing',
      'Please set PLACES_API_KEY in Script Properties\n(File > Project properties)',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return null;
  }
  return apiKey;
}

function _buildPlaceSearchRequest(query, apiKey) {
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

function _processPlaceData(data, rowInfo) {
  if (!data.places || data.places.length === 0) {
    return { status: 'Error', notes: 'Not found on Google Maps' };
  }
  
  const place = data.places[0];
  const result = {
    placeId: place.id,
    status: place.businessStatus || 'UNKNOWN',
    correctedName: place.displayName?.text || '',
    correctedPhone: place.nationalPhoneNumber || '',
    correctedAddress: place.formattedAddress || ''
  };
  
  // Special handling for PCPs - require phone for operational status
  if (PROVIDER_CONFIG.REQUIRE_PHONE_FOR_OPERATIONAL && 
      PROVIDER_CONFIG.PROVIDER_TYPE === 'PCP' &&
      result.status === 'OPERATIONAL' && 
      !result.correctedPhone) {
    result.status = 'NEEDS_REVIEW';
    result.notes = 'Operational but no phone found';
  }
  
  // Check name similarity
  const similarity = _calculateSimilarity(rowInfo.officeName, result.correctedName);
  if (similarity < PROVIDER_CONFIG.NAME_SIMILARITY_THRESHOLD) {
    result.notes = (result.notes || '') + ` Name mismatch (${Math.round(similarity * 100)}% match)`;
  }
  
  return result;
}

function _getColumnMap(sheet) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const map = {};
  const allCols = { ...PROVIDER_CONFIG.INPUT_COLUMNS, ...PROVIDER_CONFIG.OUTPUT_COLUMNS };
  
  Object.keys(allCols).forEach(key => {
    const colName = allCols[key];
    map[colName] = headers.indexOf(colName);
  });
  
  return map;
}

function getSheet(name) {
  return SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
}

function _getOrCreateSheet(name, headers = []) {
  let sheet = getSheet(name);
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet(name);
    if (headers.length > 0) {
      sheet.getRange(1, 1, 1, headers.length)
        .setValues([headers])
        .setFontWeight('bold');
    }
    _log(`Created sheet: "${name}"`);
  }
  return sheet;
}

function _addMissingColumns(sheet, columnsToAdd) {
  if (!sheet) return;
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  let lastCol = sheet.getLastColumn();
  
  columnsToAdd.forEach(col => {
    if (headers.indexOf(col) === -1) {
      lastCol++;
      sheet.getRange(1, lastCol).setValue(col).setFontWeight('bold');
      _log(`Added column "${col}" to ${sheet.getName()}`);
    }
  });
}

function _batchUpdateMaster(sheet, updates) {
  Object.keys(updates).forEach(row => {
    Object.keys(updates[row]).forEach(col => {
      if (col > -1) {
        sheet.getRange(parseInt(row), parseInt(col) + 1)
          .setValue(updates[row][col]);
      }
    });
  });
}

function _getExistingIds(sheet, columnName) {
  const ids = new Set();
  if (!sheet || sheet.getLastRow() < 2) return ids;
  
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const colNum = headers.indexOf(columnName) + 1;
  
  if (colNum > 0) {
    const existingIds = sheet.getRange(2, colNum, sheet.getLastRow() - 1, 1).getValues();
    existingIds.forEach(id => {
      if (id[0]) ids.add(id[0]);
    });
  }
  
  return ids;
}

function _calculateSimilarity(str1, str2) {
  str1 = (str1 || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  str2 = (str2 || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  
  if (str1 === str2) return 1;
  if (str1.length === 0 || str2.length === 0) return 0;
  
  const len1 = str1.length;
  const len2 = str2.length;
  const matrix = [];
  
  for (let i = 0; i <= len1; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= len2; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,      // deletion
        matrix[i][j - 1] + 1,      // insertion
        matrix[i - 1][j - 1] + cost  // substitution
      );
    }
  }
  
  const distance = matrix[len1][len2];
  return 1 - (distance / Math.max(len1, len2));
}

function _showCompletionNotification() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'Verification Complete!',
    `All ${PROVIDER_CONFIG.PROVIDER_TYPE} providers in ${PROVIDER_CONFIG.TARGET_STATE} have been processed.\n\nCheck the verified and error sheets for results.`,
    ui.ButtonSet.OK
  );
}

function _log(message, level = 'INFO') {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [${level}] ${message}`);
  Logger.log(`[${level}] ${message}`);
}

function _createTrigger() {
  _deleteTriggers();
  ScriptApp.newTrigger('processNextBatch_API')
    .timeBased()
    .after(2 * 60 * 1000)  // 2 minutes
    .create();
  _log('Next batch scheduled in 2 minutes');
}

function _deleteTriggers() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'processNextBatch_API') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

function pauseProcessing() {
  _deleteTriggers();
  SpreadsheetApp.getUi().alert('Processing paused. Use "Resume" to continue.');
}

function resumeProcessing() {
  processNextBatch_API();
}

//====================================================================================
// SECTION 6: MANUAL VERIFICATION SIDEBAR
//====================================================================================

function showVerificationSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('VerificationSidebar')
    .setTitle('Manual Verification')
    .setWidth(350);
  SpreadsheetApp.getUi().showSidebar(html);
}

function getActiveRowData() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const range = sheet.getActiveRange();
  
  if (range.getRow() < 2) {
    return { error: "Please select a data row (not the header)" };
  }
  
  const rowNum = range.getRow();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const rowValues = sheet.getRange(rowNum, 1, 1, sheet.getLastColumn()).getValues()[0];
  
  const data = {};
  headers.forEach((header, i) => {
    data[header] = rowValues[i];
  });
  
  return {
    data: data,
    row: rowNum,
    sheetName: sheet.getName(),
    providerType: PROVIDER_CONFIG.PROVIDER_TYPE,
    state: PROVIDER_CONFIG.TARGET_STATE
  };
}

function updateRowStatus(rowNum, sheetName, status, notes) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    const statusCol = headers.indexOf('Verification_Status') + 1;
    const notesCol = headers.indexOf('Verification_Notes') + 1;
    const dateCol = headers.indexOf('Verification_Date') + 1;
    
    let color = null;
    let statusText = '';
    
    switch (status) {
      case 'OPERATIONAL':
        color = '#d9ead3';
        statusText = 'Manual - Verified Operational';
        break;
      case 'CLOSED':
        color = '#f4cccc';
        statusText = 'Manual - Verified Closed';
        break;
      case 'NEEDS_INFO':
        color = '#fff2cc';
        statusText = 'Manual - Needs More Info';
        break;
    }
    
    if (statusCol > 0) sheet.getRange(rowNum, statusCol).setValue(statusText);
    if (notesCol > 0) sheet.getRange(rowNum, notesCol).setValue(notes);
    if (dateCol > 0) sheet.getRange(rowNum, dateCol).setValue(new Date());
    
    if (color) {
      sheet.getRange(rowNum, 1, 1, sheet.getLastColumn()).setBackground(color);
    }
    
    return `Row ${rowNum} updated successfully!`;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}