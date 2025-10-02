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
  return phone.toString().replace(/\D/g, '');
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