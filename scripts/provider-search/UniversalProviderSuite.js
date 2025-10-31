/**
 * Manual Provider Verification Suite (v13.0 - Instant Skip/Status Actions)
 * 100% manual verification - works directly on import sheets
 *
 * WORKFLOW:
 * 1. Import NPPES CSV to any sheet
 * 2. Add Search Links (works on selection or whole sheet)
 * 3. Remove Duplicates (works on selection or whole sheet)
 * 4. Manual verification: Sidebar with auto-load + keyboard shortcuts
 * 5. Verified providers copied to All_Verified_Providers (row colored green, hidden)
 * 6. Closed/invalid providers colored red, hidden
 * 7. Needs Review providers colored yellow, NOT hidden
 *
 * KEYBOARD SHORTCUTS:
 * - AUTO: Selecting a new row auto-loads it (500ms polling, 1.5s debounce)
 * - G: Google search (reuses same tab) - DISABLED during loading
 * - Q or 1: Mark Active → INSTANT load of next row (bypasses debounce)
 * - E or 2: Mark Closed → INSTANT load of next row (bypasses debounce)
 * - R or 3: Mark Review → INSTANT reload (bypasses debounce)
 * - S: Skip → INSTANT load of next row (bypasses debounce)
 * - L: Manual reload (always instant)
 * - Ctrl+W: Close search tab (browser native)
 *
 * SMOOTHNESS (v13.0):
 * - Skip (S) immediately loads next row - no wait
 * - Status (Q/E/R) immediately loads next/current row - no wait
 * - Can press S then G immediately - always correct row
 * - Debounce only applies to auto-load (prevents cell edit triggers)
 * - User actions always bypass debounce for instant response
 *
 * DEBOUNCING (v12.9):
 * - Auto-load requires 1.5s row stability (prevents cell edit triggers)
 * - User actions (S/Q/E/R/L) bypass debounce completely
 * - Header row (row 1) always ignored
 *
 * CRITICAL FIXES:
 * - Clean loading state (no old data visible during load)
 * - All actions disabled until currentRow === selectedRow
 * - Keyboard shortcuts blocked during loading
 * - 10-second timeout auto-recovers from stuck loading
 * - Cell edits don't trigger unwanted loads
 *
 * PERFORMANCE OPTIMIZATIONS:
 * - Only reads first 15 columns (was 50+) → 4-5x faster loading
 * - Request tracking ignores stale responses (race condition fix)
 * - Polling: 500ms (balanced, less aggressive)
 * - Color only first 8 visible columns (not entire row)
 * - Simplified All_Verified_Providers columns (8 instead of 11)
 *
 * NO GOOGLE PLACES API - Too expensive and risky
 * NO Session.getActiveUser() - Removed to avoid authorization issues
 */

// ====================================================================================
// MENU & UI
// ====================================================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('⚡ Provider Tools')
    .addItem('📝 Manual Verification Sidebar', 'showVerificationSidebar')
    .addSeparator()
    .addSubMenu(ui.createMenu('🛠️ Quick Tools')
      .addItem('🔗 Add Search Links', 'createGoogleSearchLinks')
      .addItem('🔍 Remove Duplicates', 'findAndRemoveDuplicates')
      .addItem('✨ Fix Capitalization', 'fixCapitalizationInSheet')
      .addItem('📊 Stats Report', 'generateStatsReport'))
    .addToUi();
}

function showVerificationSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('VerificationSidebar')
    .setWidth(350);
  SpreadsheetApp.getUi().showSidebar(html);
}

// ====================================================================================
// MANUAL VERIFICATION (Works on ANY sheet)
// ====================================================================================

/**
 * Detects if office name is a person's name (vs practice name)
 * Person names: "John Smith MD", "Dr. Jane Doe PA-C", "Robert Jones"
 * Practice names: "Houston Medical Center", "Main Street Clinic"
 */
function isPersonName(name) {
  if (!name) return false;

  const nameLower = name.toLowerCase();

  // Has medical credentials = definitely person
  const credentials = ['md', 'do', 'pa', 'np', 'arnp', 'crnp', 'fnp', 'dnp', 'dds', 'dpm', 'phd'];
  if (credentials.some(cred => nameLower.includes(cred))) return true;

  // Has title = person
  if (nameLower.includes('dr.') || nameLower.includes('doctor')) return true;

  // Simple heuristic: 2-3 words with no practice indicators = likely person name
  const words = name.trim().split(/\s+/).filter(w => w.length > 0);
  const practiceWords = ['clinic', 'center', 'medical', 'health', 'hospital', 'associates', 'group', 'practice'];
  const hasPracticeWord = practiceWords.some(pw => nameLower.includes(pw));

  if (!hasPracticeWord && words.length >= 2 && words.length <= 3) return true;

  return false;
}

/**
 * Builds optimized Google search query
 * For person names: DROP THE NAME - just search address (Google Places won't find "John Smith MD")
 * For practice names: Include name (helps identify specific practice)
 */
function buildSearchQuery(officeName, address, city, state, phone) {
  if (isPersonName(officeName)) {
    // Person name: Drop it entirely - Google Places listing likely under different name
    // Just search address and you'll see what's actually there
    return [address, city, state, phone].filter(Boolean).join(' ');
  } else {
    // Practice name: Include it - likely matches Google Places listing
    return [officeName, address, city, state].filter(Boolean).join(' ');
  }
}

/**
 * Gets the currently selected row number (for auto-load detection)
 */
function getActiveRowNumber() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();
  if (!range) return null;
  return range.getRow();
}

/**
 * Gets data for the active row or first selected/available row
 * Auto-loads first selected row if any, otherwise row 2
 * OPTIMIZED: Only reads first 15 columns (all we need) instead of all 50+ NPPES columns
 */
function getActiveRowData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  let range = sheet.getActiveRange();

  // If no selection or header row selected, try to find first data row
  if (!range || range.getRow() < 2) {
    // Check if there's a selection with multiple rows
    if (range && range.getNumRows() > 1) {
      // Use first row from selection (skip header if selected)
      const firstRow = range.getRow() === 1 ? 2 : range.getRow();
      sheet.setActiveRange(sheet.getRange(firstRow, 1));
      range = sheet.getActiveRange();
    } else {
      // No valid selection - use row 2 (first data row)
      if (sheet.getLastRow() < 2) {
        return { error: "No data rows found in this sheet" };
      }
      sheet.setActiveRange(sheet.getRange(2, 1));
      range = sheet.getActiveRange();
    }
  }

  const row = range.getRow();

  // OPTIMIZATION: Only read first 15 columns (Office Name, Phone, Address, City, State, ZIP, NPI, etc.)
  // NPPES has 50+ columns but we don't need most of them
  const numCols = Math.min(15, sheet.getLastColumn());
  const headers = sheet.getRange(1, 1, 1, numCols).getValues()[0];
  const values = sheet.getRange(row, 1, 1, numCols).getValues()[0];

  const data = {};
  headers.forEach((h, i) => { data[h] = values[i]; });

  const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));

  const officeName = data['Office Name'] || data['Office'] || data['Practice'] || data['Name'];
  const address = data['Address'];
  const city = data['City'];
  const state = data['State'];
  const phoneIdx = findIdx(['phone', 'number']);
  const phone = phoneIdx >= 0 ? data[headers[phoneIdx]] : null;

  const searchQuery = buildSearchQuery(officeName, address, city, state, phone);

  // Check row background color to determine verification status (only first cell for speed)
  const rowColor = sheet.getRange(row, 1).getBackground().toLowerCase();
  let verificationStatus = 'Not verified';
  if (rowColor === '#d9ead3') verificationStatus = 'Verified ✓';
  else if (rowColor === '#f4cccc') verificationStatus = 'Closed ✗';
  else if (rowColor === '#fff2cc') verificationStatus = 'Needs Review ⚠';

  return {
    data: data,
    row: row,
    sheetName: sheet.getName(),
    searchUrl: `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`,
    verificationStatus: verificationStatus
  };
}

/**
 * Updates row status after manual verification
 * status: 'OPERATIONAL' = copy to verified sheet, color green, hide row
 * status: 'CLOSED' = color red, hide row (Invalid list in Working List - separate cross-sheet task)
 * status: 'NEEDS_REVIEW' = color yellow, DON'T hide (needs manual review later)
 */
function updateRowStatus(rowNum, sheetName, status, notes) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) return `Error: Sheet "${sheetName}" not found`;

    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    const rowData = sheet.getRange(rowNum, 1, 1, sheet.getLastColumn()).getValues()[0];

    // Build provider data object
    const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));

    const provider = {
      officeName: rowData[findIdx(['office', 'practice', 'name'])] || '',
      phone: rowData[findIdx(['phone', 'number'])] || '',
      address: rowData[findIdx(['address'])] || '',
      city: rowData[findIdx(['city'])] || '',
      state: rowData[findIdx(['state', 'st'])] || '',
      zip: rowData[findIdx(['zip'])] || '',
      npi: rowData[findIdx(['npi'])] || ''
    };

    if (status === 'OPERATIONAL') {
      // Copy to All_Verified_Providers (simplified for speed)
      const verifiedSheet = getOrCreateSheet('All_Verified_Providers', [
        'Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP', 'NPI', 'Verified_Date'
      ]);

      verifiedSheet.appendRow([
        provider.officeName,
        provider.phone,
        provider.address,
        provider.city,
        provider.state,
        provider.zip,
        provider.npi,
        new Date()
      ]);

      // Color only first 8 columns (what's visible) for speed, then hide
      const numCols = Math.min(8, sheet.getLastColumn());
      sheet.getRange(rowNum, 1, 1, numCols).setBackground('#d9ead3');
      sheet.hideRows(rowNum);

      return `✓ Verified`;

    } else if (status === 'CLOSED') {
      // Color only first 8 columns for speed, then hide
      const numCols = Math.min(8, sheet.getLastColumn());
      sheet.getRange(rowNum, 1, 1, numCols).setBackground('#f4cccc');
      sheet.hideRows(rowNum);

      return `✗ Closed`;

    } else if (status === 'NEEDS_REVIEW') {
      // Color only first 8 columns for speed, DON'T hide
      const numCols = Math.min(8, sheet.getLastColumn());
      sheet.getRange(rowNum, 1, 1, numCols).setBackground('#fff2cc');

      return `⚠ Review`;
    }

    return `Unknown status: ${status}`;
  } catch (e) {
    return `Error: ${e.message}`;
  }
}

/**
 * Moves to next visible row
 * Note: This is ONLY for manual skip (S key), not after hiding rows
 * (hiding a row automatically moves selection, so calling this would skip a row)
 */
function moveToNextRow() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();
  if (!range) return null;

  let currentRow = range.getRow();
  const lastRow = sheet.getLastRow();

  // Skip hidden rows
  while (currentRow < lastRow) {
    currentRow++;
    if (!sheet.isRowHiddenByUser(currentRow)) {
      sheet.getRange(currentRow, 1).activate();
      return currentRow;
    }
  }

  return null; // No more visible rows
}

// ====================================================================================
// DUPLICATE REMOVAL (Universal - works on selection OR active sheet)
// ====================================================================================

function findAndRemoveDuplicates() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const selection = sheet.getActiveRange();

  let data, startRow, numRows;

  // If user selected specific rows, only check those
  if (selection && selection.getNumRows() > 1) {
    startRow = selection.getRow();
    numRows = selection.getNumRows();

    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    data = [headers].concat(sheet.getRange(startRow, 1, numRows, sheet.getLastColumn()).getValues());

    SpreadsheetApp.getUi().alert(
      'Checking Selection',
      `Checking ${numRows} selected rows for duplicates...`,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } else {
    // Check entire active sheet
    data = sheet.getDataRange().getValues();
    startRow = 2; // Skip header
    numRows = data.length - 1;

    SpreadsheetApp.getUi().alert(
      'Checking Entire Sheet',
      `Checking all ${numRows} rows in "${sheet.getName()}" for duplicates...`,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }

  const headers = data[0];
  const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));

  const phoneIdx = findIdx(['phone', 'number']);
  const officeIdx = findIdx(['office', 'practice', 'name']);
  const addressIdx = findIdx(['address']);
  const placeIdx = findIdx(['place', 'placeid', 'place_id']);

  if (phoneIdx === -1 && officeIdx === -1 && addressIdx === -1) {
    SpreadsheetApp.getUi().alert(
      'Cannot Find Standard Columns',
      'This sheet needs at least one of: Office Name, Phone Number, or Address',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return;
  }

  const seen = new Map();
  const duplicates = [];
  const duplicateDetails = [];

  data.slice(1).forEach((row, i) => {
    const phone = phoneIdx >= 0 ? normalizePhone(row[phoneIdx]) : '';
    const office = officeIdx >= 0 ? String(row[officeIdx]).toLowerCase().trim() : '';
    const address = addressIdx >= 0 ? String(row[addressIdx]).toLowerCase().trim() : '';
    const placeId = placeIdx >= 0 ? row[placeIdx] : '';

    let isDuplicate = false;
    let duplicateReason = '';

    if (phone && seen.has(`phone:${phone}`)) {
      isDuplicate = true;
      duplicateReason = `Same phone as row ${seen.get(`phone:${phone}`)}`;
    } else if (placeId && seen.has(`place:${placeId}`)) {
      isDuplicate = true;
      duplicateReason = `Same Place ID as row ${seen.get(`place:${placeId}`)}`;
    } else if (office && address && seen.has(`name+addr:${office}:${address}`)) {
      isDuplicate = true;
      duplicateReason = `Same office + address as row ${seen.get(`name+addr:${office}:${address}`)}`;
    }

    const actualRow = startRow + i;

    if (isDuplicate) {
      duplicates.push(actualRow);
      duplicateDetails.push({
        row: actualRow,
        office: row[officeIdx] || 'N/A',
        reason: duplicateReason
      });
    } else {
      if (phone) seen.set(`phone:${phone}`, actualRow);
      if (placeId) seen.set(`place:${placeId}`, actualRow);
      if (office && address) seen.set(`name+addr:${office}:${address}`, actualRow);
    }
  });

  if (duplicates.length > 0) {
    const detailsPreview = duplicateDetails.slice(0, 5).map(d =>
      `Row ${d.row}: ${d.office} (${d.reason})`
    ).join('\n');

    const moreCount = duplicates.length > 5 ? `\n\n...and ${duplicates.length - 5} more` : '';

    const response = SpreadsheetApp.getUi().alert(
      `Found ${duplicates.length} Duplicates`,
      `${detailsPreview}${moreCount}\n\nHIDE these duplicate rows? (Data preserved, not deleted)`,
      SpreadsheetApp.getUi().ButtonSet.YES_NO
    );

    if (response === SpreadsheetApp.getUi().Button.YES) {
      // Hide rows instead of deleting (preserves data)
      duplicates.reverse().forEach(rowNum => {
        sheet.hideRows(rowNum);
      });
      SpreadsheetApp.getUi().alert(`Hidden ${duplicates.length} duplicate rows (data preserved)`);
    }
  } else {
    SpreadsheetApp.getUi().alert('No duplicates found');
  }
}

function normalizePhone(phone) {
  if (!phone) return '';
  const phoneStr = phone.toString();
  const mainPhone = phoneStr.split(/\s*[xX]|ext/i)[0].replace(/\D/g, '');
  return mainPhone.slice(-10);
}

// ====================================================================================
// SEARCH LINKS (Works on selection OR active sheet)
// ====================================================================================

function createGoogleSearchLinks() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const selection = sheet.getActiveRange();

  let data, headers, startRow, numRows;

  // If user selected specific rows, only add links to those
  if (selection && selection.getNumRows() > 1) {
    startRow = selection.getRow();
    numRows = selection.getNumRows();

    headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    data = sheet.getRange(startRow, 1, numRows, sheet.getLastColumn()).getValues();

    SpreadsheetApp.getUi().alert(
      'Adding Links to Selection',
      `Adding search links to ${numRows} selected rows...`,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } else {
    // Add links to entire sheet
    const allData = sheet.getDataRange().getValues();
    headers = allData[0];
    data = allData.slice(1);
    startRow = 2;
    numRows = data.length;

    SpreadsheetApp.getUi().alert(
      'Adding Links to Entire Sheet',
      `Adding search links to all ${numRows} rows in "${sheet.getName()}"...`,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }

  const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));

  const officeIdx = findIdx(['office', 'practice', 'name']);
  if (officeIdx === -1) {
    SpreadsheetApp.getUi().alert('Error: Could not find Office Name column');
    return;
  }

  const addressIdx = findIdx(['address']);
  const cityIdx = findIdx(['city']);
  const stateIdx = findIdx(['state', 'st']);
  const phoneIdx = findIdx(['phone', 'number']);

  const richText = data.map(row => {
    const office = row[officeIdx];
    if (office) {
      const address = addressIdx >= 0 ? row[addressIdx] : '';
      const city = cityIdx >= 0 ? row[cityIdx] : '';
      const state = stateIdx >= 0 ? row[stateIdx] : '';
      const phone = phoneIdx >= 0 ? row[phoneIdx] : '';

      // Use smart query builder - address first for person names
      const searchQuery = buildSearchQuery(office, address, city, state, phone);
      const url = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;

      return [SpreadsheetApp.newRichTextValue().setText(office).setLinkUrl(url).build()];
    }
    return [office];
  });

  if (richText.length > 0) {
    sheet.getRange(startRow, officeIdx + 1, richText.length, 1).setRichTextValues(richText);
    SpreadsheetApp.getUi().alert(`✓ Added search links to ${richText.length} rows`);
  }
}

// ====================================================================================
// UTILITY FUNCTIONS
// ====================================================================================

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
  }

  return sheet;
}

function fixCapitalizationInSheet() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const selection = sheet.getActiveRange();

  if (!selection) {
    SpreadsheetApp.getUi().alert('Please select cells to fix');
    return;
  }

  const data = selection.getValues();
  let fixed = 0;

  for (let i = 0; i < data.length; i++) {
    for (let j = 0; j < data[i].length; j++) {
      const original = data[i][j];
      if (original && typeof original === 'string') {
        const corrected = fixCapitalization(original);
        if (corrected !== original) {
          data[i][j] = corrected;
          fixed++;
        }
      }
    }
  }

  selection.setValues(data);
  SpreadsheetApp.getUi().alert(`Fixed ${fixed} entries`);
}

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

function fixCapitalization(name) {
  if (!name || typeof name !== 'string') return name;
  name = name.trim();

  // Fix credential periods
  name = name.replace(/\b([a-z])\.([a-z])\.([a-z])\.([a-z])\b/gi, (m, a, b, c, d) =>
    a.toUpperCase() + b.toUpperCase() + c.toUpperCase() + d.toUpperCase());
  name = name.replace(/\b([a-z])\.([a-z])\.([a-z])\b/gi, (m, a, b, c) =>
    a.toUpperCase() + b.toUpperCase() + c.toUpperCase());
  name = name.replace(/\b([a-z])\.([a-z])\b/gi, (m, a, b) =>
    a.toUpperCase() + b.toUpperCase());

  name = name.replace(/\b([A-Z])\s+(?=[A-Z][a-z])/g, '$1. ');

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

    if (ALL_CAPS_STRINGS.includes(upperCleanWord)) {
      fixed.push(upperCleanWord + punctuation);
    } else if (MIXED_CASE_SUFFIXES[upperCleanWord]) {
      fixed.push(MIXED_CASE_SUFFIXES[upperCleanWord] + punctuation);
    } else if (/^[A-Z]\.$/.test(word)) {
      fixed.push(word.toUpperCase());
    } else if (cleanWord.toLowerCase().startsWith('mc') && cleanWord.length > 2) {
      const formatted = 'Mc' + cleanWord.charAt(2).toUpperCase() + cleanWord.slice(3).toLowerCase();
      fixed.push(formatted + punctuation);
    } else if (cleanWord.toLowerCase().startsWith('mac') && cleanWord.length > 3) {
      const formatted = 'Mac' + cleanWord.charAt(3).toUpperCase() + cleanWord.slice(4).toLowerCase();
      fixed.push(formatted + punctuation);
    } else if (cleanWord.includes('-')) {
      const parts = cleanWord.split('-');
      const formatted = parts.map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join('-');
      fixed.push(formatted + punctuation);
    } else if (cleanWord.includes("'")) {
      const parts = cleanWord.split("'");
      let afterApostrophe = '';
      if (parts[1]) {
        afterApostrophe = parts[1].toLowerCase() === 's' ? 's' :
                         parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase();
      }
      const formatted = parts[0].charAt(0).toUpperCase() + parts[0].slice(1).toLowerCase() +
        "'" + afterApostrophe;
      fixed.push(formatted + punctuation);
    } else {
      const formatted = cleanWord.charAt(0).toUpperCase() + cleanWord.slice(1).toLowerCase();
      fixed.push(formatted + punctuation);
    }
  }

  let finalName = fixed.join(' ');
  if (finalName.endsWith('.')) {
    finalName = finalName.slice(0, -1);
  }

  return finalName;
}

function generateStatsReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const verified = ss.getSheetByName('All_Verified_Providers');

  const stats =
    `Manual Verification Stats:\n\n` +
    `Verified: ${verified ? verified.getLastRow() - 1 : 0}\n\n` +
    `Note: Invalid/Inactive List is in Working List sheets (OBGYN/PCP), not Provider Search.`;

  SpreadsheetApp.getUi().alert('Statistics', stats, SpreadsheetApp.getUi().ButtonSet.OK);
}
