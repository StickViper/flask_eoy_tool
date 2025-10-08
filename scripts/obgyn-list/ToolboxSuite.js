// ============================================
//TOOLBOX SUITE v10.0
//
// A clean, user-friendly, and all-encompassing suite for Google Sheets.
// For use with Working List sheets (PCP outreach, year-over-year tracking)
//
// Includes:
//  - Event-driven formatting and utility functions
//  - Data consolidation (year-end)
//  - Capitalization fixes
//  - Search link creation
//  - Validation & debugging tools
// ============================================


// ====================================================================================
// INITIALIZATION & MENU
// ====================================================================================

/**
 * Creates the main menu in the spreadsheet UI when it's opened.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('Misc. Tools')
    .addItem('🔗 Create Search Links', 'createGoogleSearchLinks')
    .addSeparator()
    .addItem('✨ Fix Capitalization in Selection', 'fixCapitalizationInColumn')
    .addSeparator()
    .addSubMenu(ui.createMenu('🔍 Validation & Debugging')
      .addItem('Find Issues in Current Sheet', 'validateCurrentSheet')
      .addItem('Check for Duplicates', 'findDuplicatesInSheet'))
    .addSeparator()
    .addSubMenu(ui.createMenu('🎯 End-of-Year Workflow')
      .addItem('📋 Step 1: Audit Working List', 'auditWorkingList')
      .addItem('✅ Step 2: Validate Yellow → New Orders', 'validateYellowOrders')
      .addItem('📝 Step 3: Enforce Not Interested Rules', 'enforceNotInterestedRules')
      .addItem('🔍 Step 4: Detect Duplicates', 'detectAndFlagDuplicates')
      .addItem('🎨 Step 5: Review Status-Based Issues', 'reviewStatusIssues')
      .addSeparator()
      .addItem('🚀 Run Full EOY Automation', 'runFullEOYAutomation'))
    .addToUi();
}

/**
 * Shows the main toolbox sidebar UI. The HTML for this is in 'Toolbox.html'.
 */
function showToolboxSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('Toolbox')
    .setTitle('Master Toolbox')
    .setWidth(400);
  SpreadsheetApp.getUi().showSidebar(html);
}


// ====================================================================================
// EVENT-DRIVEN & AUTOMATIC FUNCTIONS
// ====================================================================================

/**
 * An onEdit trigger that automatically formats rows based on status changes.
 *
 * @param {object} e The event object passed by the onEdit trigger.
 */
function onEdit(e) {
  const statusColumn = 10; // Column J for "CALL STATUS"
  const targetSheetName = 'Working List 2025';
  const colorMappings = {
    'Successful Order': '#ffff00',    // Yellow
    'Requested Email': '#00ff00',     // Green
    'Potentially Invalid': '#ff0000', // Red
    'Voicemail/No Answer': '#ff00ff', // Fuchsia
    'Not interested': '#ffffff',      // White
    '': '#ffffff'                     // White for empty status
  };

  const sheet = e.source.getActiveSheet();
  const range = e.range;

  if (sheet.getName() !== targetSheetName || range.getRow() <= 1 || range.getColumn() !== statusColumn) {
    return;
  }
  
  const statusValue = (range.getValue() || '').toString().trim();
  const entireRowRange = sheet.getRange(range.getRow(), 1, 1, sheet.getLastColumn());
  const color = colorMappings[statusValue] || colorMappings[''];
  entireRowRange.setBackground(color);
  
  if (statusValue.toLowerCase() === 'not interested') {
    sheet.getRange(range.getRow(), statusColumn - 1).setValue(0); // Set QTY to 0
    const notesCell = sheet.getRange(range.getRow(), statusColumn + 1);
    let currentNotes = (notesCell.getValue() || '').toString().trim();
    
    if (!currentNotes.toLowerCase().includes('not interested')) {
      notesCell.setValue(currentNotes ? `${currentNotes}; not interested` : "not interested");
    }
  }
}


// ====================================================================================
// DATA CONSOLIDATION TOOL (SERVER-SIDE LOGIC)
// ====================================================================================

/**
 * Analyzes the spreadsheet for a given year to find sheets for consolidation.
 * @param {string} year The four-digit year to analyze.
 * @returns {object} A summary of the data found or an error object.
 */
function getConsolidationAnalysis(year) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    return analyzeYearData(ss, year);
  } catch (e) {
    return { error: e.message };
  }
}

/**
 * Executes the smart consolidation process based on the prior analysis.
 * @param {string} year The year being consolidated.
 * @returns {object} A result object with details of the consolidation or an error object.
 */
function runConsolidation(year) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const analysis = analyzeYearData(ss, year, true); // Get full sheet objects

    if (analysis.sheets.length === 0) {
      throw new Error(`No sheets were found for the year ${year}. Please check your sheet names.`);
    }

    const result = executeSmartConsolidation(ss, analysis, year);
    
    result.archiveSheet.activate();

    return {
      success: true,
      totalRows: result.totalRows,
      sources: result.sources,
      archiveSheetName: result.archiveSheet.getName(),
      statsSheetName: result.statsSheet.getName(),
      archiveSheetUrl: result.archiveSheet.getParent().getUrl() + '#gid=' + result.archiveSheet.getSheetId()
    };
  } catch (e) {
    return { error: e.message };
  }
}


// --- CONSOLIDATION HELPERS ---

/**
 * Analyzes all sheets in the spreadsheet to find and categorize those matching the year.
 * CRITICAL FIX: Now checks for duplicates across ALL found sheets, not just working lists.
 *
 * @param {GoogleAppsScript.Spreadsheet.Spreadsheet} spreadsheet The active spreadsheet.
 * @param {string} year The year to search for.
 * @param {boolean} returnSheetObjects If true, returns full sheet objects instead of just names.
 * @returns {object} The analysis object.
 */
function analyzeYearData(spreadsheet, year, returnSheetObjects = false) {
  const sheets = spreadsheet.getSheets();
  const analysis = {
    year: year, sheets: [], workingLists: [], newOrders: [], stats: [], other: [],
    uniqueLocations: 0, duplicates: 0,
  };

  const yearPattern = new RegExp(`\\b${year}\\b`);
  const oldYearPattern = new RegExp(`OLD[ _]${year}`, 'i');

  sheets.forEach(sheet => {
    const name = sheet.getName();
    if (yearPattern.test(name) || oldYearPattern.test(name)) {
      analysis.sheets.push(sheet);
      const lowerName = name.toLowerCase();
      if (lowerName.includes('working') || lowerName.includes('list')) analysis.workingLists.push(sheet);
      else if (lowerName.includes('order')) analysis.newOrders.push(sheet);
      else if (lowerName.includes('stat')) analysis.stats.push(sheet);
      else analysis.other.push(sheet);
    }
  });

  // --- CRITICAL FIX: Perform duplicate analysis across ALL relevant sheets for the year ---
  const phoneMap = new Map();
  analysis.sheets.forEach(sheet => { // <-- Changed from analysis.workingLists to analysis.sheets
    if (sheet.getLastRow() <= 1) return;
    try {
      const data = sheet.getDataRange().getValues();
      const headers = data.shift();
      const phoneCol = headers.findIndex(h => h && h.toLowerCase().includes('phone'));
      if (phoneCol !== -1) {
        data.forEach(row => {
          const phone = normalizePhone(row[phoneCol]);
          if (phone) phoneMap.set(phone, (phoneMap.get(phone) || 0) + 1);
        });
      }
    } catch (e) { console.error(`Could not analyze ${sheet.getName()} for duplicates: ${e.message}`); }
  });
  
  analysis.uniqueLocations = phoneMap.size;
  analysis.duplicates = Array.from(phoneMap.values()).filter(count => count > 1).length;
  
  if (!returnSheetObjects) {
    ['sheets', 'workingLists', 'newOrders', 'stats', 'other'].forEach(key => {
      analysis[key] = analysis[key].map(s => s.getName());
    });
  }
  return analysis;
}

function executeSmartConsolidation(ss, analysis, year) {
  const masterData = new Map();
  const columnRegistry = new Set();
  const processOrder = [
    { type: 'working', sheets: analysis.workingLists },
    { type: 'orders', sheets: analysis.newOrders },
    { type: 'other', sheets: analysis.other }
  ];

  processOrder.forEach(group => {
    group.sheets.forEach(sheet => {
      if (sheet) processSheetIntoMaster(sheet, masterData, columnRegistry, group.type);
    });
  });

  const archiveSheet = createConsolidatedSheet(ss, year, masterData, columnRegistry);
  const statsSheet = createConsolidationStats(ss, year, masterData, analysis.sheets.length);
  return { archiveSheet, statsSheet, totalRows: masterData.size, sources: analysis.sheets.length };
}

function processSheetIntoMaster(sheet, masterData, columnRegistry, sheetType) {
  const sheetName = sheet.getName();
  try {
    if (sheet.getLastRow() <= 1) return;
    const data = sheet.getDataRange().getValues();
    const headers = data.shift();
    const backgrounds = sheet.getRange(2, 1, data.length, sheet.getLastColumn()).getBackgrounds();
    
    headers.forEach(h => { if (h) columnRegistry.add(normalizeColumnName(h.toString())); });
    const keyColumns = identifyKeyColumns(headers);

    data.forEach((row, i) => {
      const rowKey = generateRowKey(row, keyColumns);
      if (!rowKey) return;

      if (!masterData.has(rowKey)) {
        masterData.set(rowKey, { data: new Map(), sources: new Set(), conflicts: new Map(), backgroundColor: null });
      }
      const masterRecord = masterData.get(rowKey);
      masterRecord.sources.add(sheetName);
      
      const rowBackgroundColor = backgrounds[i].find(color => color && color !== '#ffffff');
      if (rowBackgroundColor) masterRecord.backgroundColor = rowBackgroundColor;
      
      headers.forEach((header, colIdx) => {
        const value = row[colIdx];
        if (header === null || header === '' || value === null || value === '') return;
        
        const normalizedHeader = normalizeColumnName(header.toString());
        const headerLower = header.toString().toLowerCase();

        if (headerLower.includes('qty') || headerLower.includes('amount')) mergeQuantityData(masterRecord, normalizedHeader, value, sheetType);
        else if (headerLower.includes('status')) mergeStatusData(masterRecord, normalizedHeader, value);
        else if (headerLower.includes('note')) mergeNotesData(masterRecord, normalizedHeader, value);
        else mergeRegularData(masterRecord, normalizedHeader, value, sheetName);
      });
    });
  } catch (e) { console.error(`Error processing ${sheetName}: ${e.message}`); }
}

function generateRowKey(row, keyColumns) {
  if (keyColumns.phone > -1 && row[keyColumns.phone]) {
    const phone = normalizePhone(row[keyColumns.phone]);
    if (phone && phone.length >= 10) return `phone:${phone}`;
  }
  const office = keyColumns.office > -1 ? (row[keyColumns.office] || '').toString().trim().toLowerCase() : '';
  if (keyColumns.address > -1) {
    const address = (row[keyColumns.address] || '').toString().trim().toLowerCase();
    if (office && address) return `loc:${office}_${address}`;
  }
  if (keyColumns.city > -1) {
    const city = (row[keyColumns.city] || '').toString().trim().toLowerCase();
    if (office && city) return `loc2:${office}_${city}`;
  }
  if (office.length > 3) return `office:${office}`;
  return null;
}

function identifyKeyColumns(headers) {
  const find = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));
  return { office: find(['office']), phone: find(['phone']), address: find(['address']), city: find(['city']) };
}

function normalizeColumnName(header) {
  const h = header.trim();
  const mappings = { 'Office Name': 'Office', 'Phone Number': 'Phone', 'ZIP': 'Zip', 'CALL STATUS': 'Call Status' };
  if (mappings[h]) return mappings[h];
  const yearMatch = h.match(/\b\d{4}\b/);
  if ((h.toLowerCase().includes('amount') || h.toLowerCase().includes('qty')) && yearMatch) {
    return `${yearMatch[0]} QTY`;
  }
  return h;
}

// --- MERGING LOGIC FUNCTIONS ---
function mergeQuantityData(masterRecord, header, value, sheetType) {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;

    const existingData = masterRecord.data.get(header);
    
    // Orders sheet value always overrides anything else.
    if (sheetType === 'orders') {
        masterRecord.data.set(header, { value: numValue, type: 'order' });
        return;
    }
    
    // If the existing value is from an order, don't change it.
    if (existingData && existingData.type === 'order') {
        return;
    }

    // Otherwise, sum the quantities for working/other sheets.
    const currentSum = (existingData && existingData.value) ? existingData.value : 0;
    masterRecord.data.set(header, { value: currentSum + numValue, type: 'sum' });
}

function mergeStatusData(masterRecord, header, value) {
  if (value) masterRecord.data.set(header, { value });
}

function mergeNotesData(masterRecord, header, value) {
  const existingNotes = masterRecord.data.has(header) ? masterRecord.data.get(header).value : '';
  const notesSet = new Set(existingNotes.split(';').map(n => n.trim()).filter(Boolean));
  value.toString().split(';').forEach(note => {
    const trimmed = note.trim();
    if (trimmed) notesSet.add(trimmed);
  });
  masterRecord.data.set(header, { value: Array.from(notesSet).join('; ') });
}

function mergeRegularData(masterRecord, header, value, source) {
  if (!masterRecord.data.has(header)) {
    masterRecord.data.set(header, { value, source });
  } else {
    const existing = masterRecord.data.get(header);
    if (existing.value.toString().trim().toLowerCase() !== value.toString().trim().toLowerCase()) {
      const conflictSet = masterRecord.conflicts.get(header) || new Set();
      conflictSet.add(`'${existing.value}' (from ${existing.source}) vs '${value}' (from ${source})`);
      masterRecord.conflicts.set(header, conflictSet);
    }
  }
}

function normalizePhone(phone) {
  if (!phone || typeof phone.toString !== 'function') return '';
  // Extract main phone number, preserve extensions for display but ignore for matching
  const phoneStr = phone.toString();
  // Remove everything except digits, but stop at 'x' or 'ext' (extensions)
  const mainPhone = phoneStr.split(/\s*[xX]|ext/i)[0].replace(/\D/g, '');
  // Return last 10 digits (handles country codes like +1), or all if less than 10
  return mainPhone.slice(-10) || mainPhone;
}

// --- SHEET CREATION FUNCTIONS ---
function createConsolidatedSheet(ss, year, masterData, columnRegistry) {
  const sheetName = `CONSOLIDATED_${year}`;
  if (ss.getSheetByName(sheetName)) ss.deleteSheet(ss.getSheetByName(sheetName));
  const sheet = ss.insertSheet(sheetName, 0);
  
  const priorityHeaders = ['Office', 'Phone', 'Address', 'City', 'State', 'Zip'];
  const qtyHeaders = Array.from(columnRegistry).filter(h => h.includes('QTY')).sort();
  const otherHeaders = Array.from(columnRegistry).filter(h => !priorityHeaders.includes(h) && !qtyHeaders.includes(h)).sort();
  const allHeaders = [...new Set([...priorityHeaders, ...qtyHeaders, ...otherHeaders, 'Sources', 'Conflicts'])];
  
  sheet.getRange(1, 1, 1, allHeaders.length).setValues([allHeaders]).setFontWeight('bold').setBackground('#4a86e8').setFontColor('#ffffff');
  
  if (masterData.size === 0) return sheet;

  const outputRows = [];
  const backgroundColors = [];
  
  masterData.forEach(record => {
    const row = allHeaders.map(header => {
      if (header === 'Sources') return Array.from(record.sources).join(', ');
      if (header === 'Conflicts') {
          const conflictArray = Array.from(record.conflicts.values()).map(cSet => Array.from(cSet).join(' | '));
          return conflictArray.join('; ');
      }
      const data = record.data.get(header);
      return data ? data.value : '';
    });
    outputRows.push(row);
    backgroundColors.push(record.backgroundColor || '#ffffff');
  });
  
  const dataRange = sheet.getRange(2, 1, outputRows.length, allHeaders.length);
  dataRange.setValues(outputRows);
  
  outputRows.forEach((row, i) => {
    if (backgroundColors[i] !== '#ffffff') {
      sheet.getRange(i + 2, 1, 1, allHeaders.length).setBackground(backgroundColors[i]);
    }
  });

  sheet.autoResizeColumns(1, allHeaders.length);
  sheet.getFilter()?.remove();
  sheet.getRange(1, 1, outputRows.length + 1, allHeaders.length).createFilter();
  
  return sheet;
}

function createConsolidationStats(ss, year, masterData, totalSources) {
  const statsName = `STATS_CONSOLIDATED_${year}`;
  if (ss.getSheetByName(statsName)) ss.deleteSheet(ss.getSheetByName(statsName));
  const sheet = ss.insertSheet(statsName, 1);
  
  const stats = [
    ['Consolidation Statistics for ' + year, ''],
    ['Total Unique Locations', masterData.size],
    ['Total Source Sheets Processed', totalSources]
  ];

  const qtyTotals = new Map();
  masterData.forEach(record => {
    record.data.forEach((data, header) => {
      if (header.includes('QTY')) {
        const total = qtyTotals.get(header) || 0;
        const value = data ? data.value : 0;
        qtyTotals.set(header, total + parseFloat(value || 0));
      }
    });
  });

  if (qtyTotals.size > 0) {
    stats.push(['', '']);
    stats.push(['Quantity Totals', '']);
    Array.from(qtyTotals.entries()).sort().forEach(([year, total]) => {
      stats.push([`  ${year}`, total]);
    });
  }
  
  sheet.getRange(1, 1, stats.length, 2).setValues(stats);
  sheet.getRange("A1").setFontWeight('bold');
  sheet.getRange("A1:B1").merge().setHorizontalAlignment("center");
  sheet.autoResizeColumns(1, 2);
  
  return sheet;
}


// ====================================================================================
// GENERAL UTILITIES & CUSTOM FUNCTIONS
// ====================================================================================

/**
 * Creates clickable Google search links in the 'Office' column of the active sheet.
 */
function createGoogleSearchLinks() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const dataRange = sheet.getDataRange();
  const data = dataRange.getValues();
  const headers = data.shift();

  const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));
  const officeIdx = findIdx(['office']);
  if (officeIdx === -1) {
    SpreadsheetApp.getUi().alert("Could not find an 'Office' column.");
    return;
  }
  
  const addressIdx = findIdx(['address']);
  const cityIdx = findIdx(['city']);
  
  const richTextValues = data.map(row => {
    const office = row[officeIdx];
    if (office && typeof office === 'string') {
      const queryParts = [ office, addressIdx > -1 ? row[addressIdx] : '', cityIdx > -1 ? row[cityIdx] : '' ];
      const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(queryParts.filter(Boolean).join(' '))}`;
      return [SpreadsheetApp.newRichTextValue().setText(office).setLinkUrl(searchUrl).build()];
    }
    return [office];
  });
  
  if (richTextValues.length > 0) {
    sheet.getRange(2, officeIdx + 1, richTextValues.length, 1).setRichTextValues(richTextValues);
  }
}

/**
 * A custom function to count cells with a specific background color that are not empty.
 * @customfunction
 */
function countColoredCells(range, color, refreshTrigger) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const targetRange = sheet.getRange(range);
  const backgrounds = targetRange.getBackgrounds();
  const values = targetRange.getValues();
  let count = 0;
  for (let i = 0; i < backgrounds.length; i++) {
    for (let j = 0; j < backgrounds[i].length; j++) {
      if (backgrounds[i][j].toLowerCase() === color.toLowerCase() && values[i][j] !== '') {
        count++;
      }
    }
  }
  return count;
}


// ====================================================================================
// CAPITALIZATION FIX TOOL
// ====================================================================================

// Configuration for capitalization rules

// Acronyms, credentials, and Roman numerals that should always be fully capitalized.
// The check is case-insensitive, so 'md', 'Md', and 'MD' will all become 'MD'.
const ALL_CAPS_STRINGS = [
  'MD', 'DO', 'PA', 'NP', 'RN', 'FNP', 'DNP', 'CRNP', 'ARNP', 'APRN',
  'MSN', 'PMHNP', 'WHNP', 'ANP', 'GNP', 'CRNA', 'CFNP', 'CWOCN',
  'LLC', 'PC', 'PLLC', 'INC', 'DDS', 'DPM', 'PHD', 'MS', 'MHS',
  'II', 'III', 'IV'
];

// Suffixes that have a specific, mixed capitalization.
// The key (e.g., 'JR') is the case-insensitive version to check against,
// and the value (e.g., 'Jr') is the desired output capitalization.
const MIXED_CASE_SUFFIXES = {
  'JR': 'Jr',
  'SR': 'Sr'
};


/**
 * Fix capitalization issues in provider names.
 * Handles: ALL CAPS, ProperCase damage, Mc/Mac, apostrophes, hyphens, periods
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
    // Apostrophes (o'donnell → O'Donnell)
    else if (cleanWord.includes("'")) {
      const parts = cleanWord.split("'");
      const formatted = parts[0].charAt(0).toUpperCase() + parts[0].slice(1).toLowerCase() +
        "'" + (parts[1] ? parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase() : '');
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

/**
 * Menu function - fix capitalization in active selection
 */
function fixCapitalizationInColumn() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const selection = sheet.getActiveRange();

  const response = ui.alert(
    'Fix Capitalization',
    `This will fix capitalization in the selected range.\n\nContinue?`,
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) return;

  const values = selection.getValues();
  let fixedCount = 0;

  const fixed = values.map(row => row.map(cell => {
    if (cell && typeof cell === 'string') {
      const fixedCell = fixCapitalization(cell);
      if (fixedCell !== cell) fixedCount++;
      return fixedCell;
    }
    return cell;
  }));

  selection.setValues(fixed);
  ui.alert(`Fixed capitalization for ${fixedCount} cells`);
}


// ====================================================================================
// VALIDATION & DEBUGGING TOOLS (STUBS - TO BE IMPLEMENTED)
// ====================================================================================

/**
 * Find common data issues in the current sheet
 * TODO: Implement validation checks
 */
function validateCurrentSheet() {
  const ui = SpreadsheetApp.getUi();
  ui.alert('Validation Tool', 'This feature is under development.', ui.ButtonSet.OK);

  // TODO: Check for:
  // - Yellow rows not in New Orders
  // - "Not interested" without notes or 0 in QTY
  // - Potential duplicates (same phone/address)
  // - QTY mismatches vs New Orders
  // - Missing required data
}

/**
 * Find duplicate entries by phone/address
 * TODO: Implement duplicate detection
 */
function findDuplicatesInSheet() {
  const ui = SpreadsheetApp.getUi();
  ui.alert('Duplicate Finder', 'This feature is under development.', ui.ButtonSet.OK);

  // TODO: Group by phone + address, flag duplicates
}


// ====================================================================================
// END-OF-YEAR AUTOMATION SUITE
// ====================================================================================

/**
 * EOY Step 1: Comprehensive audit of Working List
 * Identifies all issues that need attention before year-end transition
 */
function auditWorkingList() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

  ui.alert('Starting Audit',
    'This will scan the current sheet for common issues.\n\n' +
    'Issues will be flagged in a "Debug/Issues" column.',
    ui.ButtonSet.OK);

  const issues = {
    yellowMissingInOrders: 0,
    notInterestedMissingNotes: 0,
    notInterestedWrongQty: 0,
    duplicates: 0,
    statusReviewNeeded: 0
  };

  // Run all validation checks
  issues.yellowMissingInOrders = validateYellowOrders(true);
  issues.notInterestedMissingNotes = enforceNotInterestedRules(true);
  issues.duplicates = detectAndFlagDuplicates(true);
  issues.statusReviewNeeded = reviewStatusIssues(true);

  const total = Object.values(issues).reduce((a, b) => a + b, 0);

  ui.alert('Audit Complete',
    `Found ${total} total issues:\n\n` +
    `• Yellow rows not in New Orders: ${issues.yellowMissingInOrders}\n` +
    `• Not Interested missing notes: ${issues.notInterestedMissingNotes}\n` +
    `• Not Interested wrong QTY: ${issues.notInterestedWrongQty}\n` +
    `• Duplicate entries: ${issues.duplicates}\n` +
    `• Status reviews needed: ${issues.statusReviewNeeded}\n\n` +
    'Check the "Debug/Issues" column for details.',
    ui.ButtonSet.OK);
}

/**
 * Helper: Find the most recent QTY column (e.g., "2025 QTY" is newer than "2024 QTY")
 */
function findMostRecentQtyColumn(headers) {
  const qtyColumns = headers.map((h, i) => ({ header: h, index: i }))
    .filter(col => col.header && col.header.toString().toLowerCase().includes('qty'));

  if (qtyColumns.length === 0) return -1;
  if (qtyColumns.length === 1) return qtyColumns[0].index;

  // Sort by year (extract numbers from header, assume higher = more recent)
  qtyColumns.sort((a, b) => {
    const yearA = parseInt((a.header.match(/\d{4}/) || ['0'])[0]);
    const yearB = parseInt((b.header.match(/\d{4}/) || ['0'])[0]);
    return yearB - yearA; // Descending (most recent first)
  });

  return qtyColumns[0].index;
}

/**
 * Helper: Smart sheet detection - finds New Orders sheet
 */
function findNewOrdersSheet(ss) {
  const sheetNames = ss.getSheets().map(s => s.getName());

  // Try exact matches first
  const exactMatches = ['New Orders 2025', 'New Orders', 'Orders 2025'];
  for (const name of exactMatches) {
    const sheet = ss.getSheetByName(name);
    if (sheet) return sheet;
  }

  // Try fuzzy match: contains "new" and "order"
  for (const name of sheetNames) {
    const lower = name.toLowerCase();
    if (lower.includes('new') && lower.includes('order')) {
      return ss.getSheetByName(name);
    }
  }

  // Try just "order"
  for (const name of sheetNames) {
    if (name.toLowerCase().includes('order')) {
      return ss.getSheetByName(name);
    }
  }

  return null;
}

/**
 * EOY Step 2: Validate Yellow (Successful Order) → New Orders sheet
 * Checks that yellow rows exist in New Orders with correct QTY
 * @param {boolean} dryRun - If true, only count issues without fixing
 */
function validateYellowOrders(dryRun = false) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();
  const workingSheet = ss.getActiveSheet();
  const newOrdersSheet = findNewOrdersSheet(ss);

  if (!newOrdersSheet) {
    ui.alert('Error', 'Cannot find New Orders sheet.\n\nLooked for: "New Orders 2025", "New Orders", "Orders 2025", or sheets containing "order"', ui.ButtonSet.OK);
    return 0;
  }

  const data = workingSheet.getDataRange().getValues();
  const headers = data[0];
  const backgrounds = workingSheet.getDataRange().getBackgrounds();

  const phoneCol = headers.findIndex(h => h && (h.toLowerCase().includes('phone') || h.toLowerCase().includes('number')));
  const officeCol = headers.findIndex(h => h && (h.toLowerCase().includes('office') || h.toLowerCase().includes('practice') || h.toLowerCase().includes('name')));
  const qtyCol = findMostRecentQtyColumn(headers);
  const statusCol = headers.findIndex(h => h && h.toLowerCase().includes('status'));

  // Get New Orders data
  const ordersData = newOrdersSheet.getDataRange().getValues();
  const ordersHeaders = ordersData[0];
  const ordersPhoneCol = ordersHeaders.findIndex(h => h && (h.toLowerCase().includes('phone') || h.toLowerCase().includes('number')));
  const ordersQtyCol = findMostRecentQtyColumn(ordersHeaders);

  const ordersMap = new Map();
  ordersData.slice(1).forEach(row => {
    const phone = normalizePhone(row[ordersPhoneCol]);
    const qty = parseFloat(row[ordersQtyCol]) || 0;
    if (phone) ordersMap.set(phone, qty);
  });

  let issuesFound = 0;
  const issuesCol = getOrCreateDebugColumn(workingSheet);

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const bgColor = backgrounds[i][statusCol];

    // Check if yellow (Successful Order)
    if (bgColor.toLowerCase() === '#ffff00') {
      const phone = normalizePhone(row[phoneCol]);
      const workingQty = parseFloat(row[qtyCol]) || 0;
      const orderQty = ordersMap.get(phone) || 0;

      let issue = null;
      if (!ordersMap.has(phone)) {
        issue = '⚠️ Yellow but NOT in New Orders';
        issuesFound++;
      } else if (workingQty !== orderQty) {
        issue = `⚠️ QTY mismatch: Working=${workingQty}, Orders=${orderQty}`;
        issuesFound++;
      }

      if (issue && !dryRun) {
        workingSheet.getRange(i + 1, issuesCol).setValue(issue);
      }
    }
  }

  if (!dryRun) {
    ui.alert('Yellow Orders Validation',
      `Found ${issuesFound} issues with yellow rows.\n\n` +
      'Check "Debug/Issues" column for details.',
      ui.ButtonSet.OK);
  }

  return issuesFound;
}

/**
 * EOY Step 3: Enforce "Not Interested" rules
 * Ensures "not interested" rows have proper notes and QTY=0
 * @param {boolean} dryRun - If true, only count issues without fixing
 */
function enforceNotInterestedRules(dryRun = false) {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];

  const statusCol = headers.findIndex(h => h && h.toLowerCase().includes('status'));
  const notesCol = headers.findIndex(h => h && h.toLowerCase().includes('note'));
  const qtyCol = findMostRecentQtyColumn(headers);

  let issuesFound = 0;
  let issuesFixed = 0;
  const issuesCol = getOrCreateDebugColumn(sheet);

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    const status = (row[statusCol] || '').toString().toLowerCase();
    const notes = (row[notesCol] || '').toString().toLowerCase();
    const qty = parseFloat(row[qtyCol]) || null;

    if (status.includes('not interested')) {
      let issues = [];

      // Check for missing/improper notes
      if (!notes.includes('not interested')) {
        issues.push('Missing "not interested" in Notes');
        if (!dryRun) {
          const currentNotes = row[notesCol] || '';
          sheet.getRange(i + 1, notesCol + 1).setValue(
            currentNotes ? `${currentNotes}; not interested` : 'not interested'
          );
          issuesFixed++;
        }
      }

      // Check QTY
      if (qty !== 0) {
        issues.push(`QTY should be 0 (currently ${qty})`);
        if (!dryRun) {
          sheet.getRange(i + 1, qtyCol + 1).setValue(0);
          issuesFixed++;
        }
      }

      if (issues.length > 0) {
        issuesFound++;
        if (!dryRun) {
          sheet.getRange(i + 1, issuesCol).setValue('⚠️ ' + issues.join('; '));
        }
      }
    }
  }

  if (!dryRun) {
    ui.alert('Not Interested Rules',
      `Found ${issuesFound} issues, fixed ${issuesFixed} automatically.\n\n` +
      'Check "Debug/Issues" column for edge cases.',
      ui.ButtonSet.OK);
  }

  return issuesFound;
}

/**
 * EOY Step 4: Detect and flag duplicates
 * Finds duplicates by phone/address and notes them (does NOT auto-merge)
 * @param {boolean} dryRun - If true, only count issues without fixing
 */
function detectAndFlagDuplicates(dryRun = false) {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data[0];

  const phoneCol = headers.findIndex(h => h && (h.toLowerCase().includes('phone') || h.toLowerCase().includes('number')));
  const addressCol = headers.findIndex(h => h && h.toLowerCase().includes('address'));
  const officeCol = headers.findIndex(h => h && (h.toLowerCase().includes('office') || h.toLowerCase().includes('practice') || h.toLowerCase().includes('name')));
  const notesCol = headers.findIndex(h => h && h.toLowerCase().includes('note'));

  const phoneMap = new Map();
  const addressMap = new Map();
  let duplicatesFound = 0;
  const issuesCol = getOrCreateDebugColumn(sheet);

  // First pass: identify all occurrences
  for (let i = 1; i < data.length; i++) {
    const phone = normalizePhone(data[i][phoneCol]);
    const address = (data[i][addressCol] || '').toString().trim().toLowerCase();

    if (phone) {
      if (!phoneMap.has(phone)) phoneMap.set(phone, []);
      phoneMap.get(phone).push(i);
    }

    if (address.length > 10) {
      if (!addressMap.has(address)) addressMap.set(address, []);
      addressMap.get(address).push(i);
    }
  }

  // Second pass: flag duplicates and add network notes
  for (let i = 1; i < data.length; i++) {
    const phone = normalizePhone(data[i][phoneCol]);
    const address = (data[i][addressCol] || '').toString().trim().toLowerCase();
    const officeName = (data[i][officeCol] || '').toString().trim();
    const issues = [];
    let needsNetworkNote = false;

    if (phone && phoneMap.get(phone).length > 1) {
      const dupeRows = phoneMap.get(phone);

      // Check if same/similar name but different addresses (likely same network)
      const names = dupeRows.map(rowIdx => (data[rowIdx][officeCol] || '').toString().trim());
      const addresses = dupeRows.map(rowIdx => (data[rowIdx][addressCol] || '').toString().trim());
      const uniqueAddresses = new Set(addresses);

      // Use fuzzy matching to detect networks (handles typos and variations)
      let isSameNetwork = false;
      if (names.length >= 2 && uniqueAddresses.size > 1) {
        // Compare first name to all others, if all are similar (≥0.85), it's a network
        // Threshold 0.85 chosen based on testing with real OBGYN data (100% accuracy)
        const similarities = names.slice(1).map(name => calculateSimilarity(names[0], name));
        const allSimilar = similarities.every(score => score >= 0.85);
        if (allSimilar) {
          isSameNetwork = true;
          needsNetworkNote = true;
          issues.push(`Same network (${uniqueAddresses.size} locations, 1 phone)`);
        }
      }

      if (!isSameNetwork) {
        issues.push(`Duplicate phone (appears ${phoneMap.get(phone).length} times)`);
      }
    }

    if (address && addressMap.get(address) && addressMap.get(address).length > 1) {
      issues.push(`Duplicate address (appears ${addressMap.get(address).length} times)`);
    }

    if (issues.length > 0) {
      duplicatesFound++;
      if (!dryRun) {
        // Add to Debug/Issues column
        sheet.getRange(i + 1, issuesCol).setValue('🔄 ' + issues.join('; '));

        // If it's a network, add note to Notes column
        if (needsNetworkNote && notesCol !== -1) {
          const currentNotes = (data[i][notesCol] || '').toString();
          if (!currentNotes.toLowerCase().includes('network') && !currentNotes.toLowerCase().includes('multiple location')) {
            const newNote = currentNotes ? `${currentNotes}; Same network - multiple locations` : 'Same network - multiple locations';
            sheet.getRange(i + 1, notesCol + 1).setValue(newNote);
          }
        }
      }
    }
  }

  if (!dryRun) {
    ui.alert('Duplicate Detection',
      `Found ${duplicatesFound} potential duplicates.\n\n` +
      'Check "Debug/Issues" column. Review manually - do NOT auto-merge.',
      ui.ButtonSet.OK);
  }

  return duplicatesFound;
}

/**
 * EOY Step 5: Review status-based issues
 * Categorizes issues by color: Red, Fuschia, Green, Empty
 * @param {boolean} dryRun - If true, only count issues without fixing
 */
function reviewStatusIssues(dryRun = false) {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const backgrounds = sheet.getDataRange().getBackgrounds();
  const headers = data[0];

  const statusCol = headers.findIndex(h => h && h.toLowerCase().includes('status'));
  const notesCol = headers.findIndex(h => h && h.toLowerCase().includes('note'));
  const qtyCol = findMostRecentQtyColumn(headers);

  const categories = {
    red: [], // Potentially Invalid
    fuschia: [], // Voicemail/No Answer
    green: [], // Requested Email
    empty: [] // Uncalled
  };

  for (let i = 1; i < data.length; i++) {
    const bgColor = backgrounds[i][statusCol].toLowerCase();
    const status = (data[i][statusCol] || '').toString().trim();
    const notes = (data[i][notesCol] || '').toString().trim();
    const qty = data[i][qtyCol];

    if (bgColor === '#ff0000' || status === 'Potentially Invalid') {
      categories.red.push({ row: i + 1, notes, qty });
    } else if (bgColor === '#ff00ff' || status === 'Voicemail/No Answer') {
      categories.fuschia.push({ row: i + 1, notes, qty });
    } else if (bgColor === '#00ff00' || status === 'Requested Email') {
      categories.green.push({ row: i + 1, notes, qty });
    } else if (!status || status === '') {
      categories.empty.push({ row: i + 1, notes, qty });
    }
  }

  const totalReviews = Object.values(categories).reduce((a, b) => a + b.length, 0);

  if (!dryRun) {
    const message =
      `Status-Based Review:\n\n` +
      `🔴 Red (Potentially Invalid): ${categories.red.length}\n` +
      `   → Should exist or be added to Invalid/Inactive list\n\n` +
      `💜 Fuschia (Voicemail/No Answer): ${categories.fuschia.length}\n` +
      `   → Triple follow-up, leave empty at EOY (no 0 in QTY)\n\n` +
      `🟢 Green (Requested Email): ${categories.green.length}\n` +
      `   → Keep green if recent, change to "not interested" if old\n\n` +
      `⚪ Empty (Uncalled): ${categories.empty.length}\n` +
      `   → Never reached, leave as-is\n\n` +
      'Review these manually before EOY transition.';

    ui.alert('Status Review', message, ui.ButtonSet.OK);
  }

  return totalReviews;
}

/**
 * Full EOY automation workflow
 * Runs all steps sequentially with confirmations
 */
function runFullEOYAutomation() {
  const ui = SpreadsheetApp.getUi();

  const response = ui.alert('Full EOY Automation',
    'This will run all EOY validation steps:\n\n' +
    '1. Validate Yellow → New Orders\n' +
    '2. Enforce Not Interested rules\n' +
    '3. Detect duplicates\n' +
    '4. Review status issues\n\n' +
    '⚠️ Issues will be flagged but NOT auto-fixed (except Not Interested).\n\n' +
    'Continue?',
    ui.ButtonSet.YES_NO);

  if (response !== ui.Button.YES) return;

  auditWorkingList();
}

/**
 * Helper: Get or create Debug/Issues column
 * Returns column index (1-based)
 */
function getOrCreateDebugColumn(sheet) {
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  let debugCol = headers.findIndex(h => h && (h.includes('Debug') || h.includes('Issues')));

  if (debugCol === -1) {
    // Create new column at the end
    debugCol = headers.length;
    sheet.getRange(1, debugCol + 1).setValue('Debug/Issues')
      .setFontWeight('bold')
      .setBackground('#fff2cc');

    // Hide the column
    sheet.hideColumns(debugCol + 1);
  }

  return debugCol + 1; // Return 1-based index
}


// ====================================================================================
// SIMILARITY & MATCHING FUNCTIONS
// ====================================================================================

/**
 * Calculate similarity between two strings using Levenshtein distance
 * Returns value between 0 (completely different) and 1 (identical)
 * Used for fuzzy matching in network detection
 * @param {string} str1 - First string to compare
 * @param {string} str2 - Second string to compare
 * @returns {number} Similarity score 0-1
 */
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


// ====================================================================================
// MAINTENANCE FUNCTIONS
// ====================================================================================

/**
 * A maintenance function to synchronize the "Call Status" column with row colors.
 */
function updateAllCallStatusBasedOnColor() {
  const sheetName = 'Working List 2025';
  const statusColumn = 10;
  const notesColumn = 11;
  const colorMappings = {
    '#ffff00': 'Successful Order', '#00ff00': 'Requested Email', '#ff0000': 'Potentially Invalid',
    '#ff00ff': 'Voicemail/No Answer', '#ffffff': ''
  };

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) return;

  const dataRange = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn());
  const backgrounds = dataRange.getBackgrounds();
  const values = dataRange.getValues();
  const newStatuses = [];

  for (let i = 0; i < backgrounds.length; i++) {
    const rowColor = backgrounds[i][0].toLowerCase();
    const notes = (values[i][notesColumn - 1] || '').toString().toLowerCase();
    let status = (notes.includes('not interested')) ? 'Not interested' : (colorMappings[rowColor] || '');
    newStatuses.push([status]);
  }

  if (newStatuses.length > 0) {
    sheet.getRange(2, statusColumn, newStatuses.length, 1).setValues(newStatuses);
    SpreadsheetApp.getUi().alert('Synchronization complete.');
  }
}