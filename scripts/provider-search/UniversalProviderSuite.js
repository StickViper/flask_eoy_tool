/**
 * Manual Provider Verification Suite (v9.0 - NO API)
 * Manual verification tools for healthcare provider lists
 *
 * NO GOOGLE PLACES API - Too expensive and risky for nonprofit
 * All verification is manual with keyboard-driven UI
 */

// ====================================================================================
// MENU & UI
// ====================================================================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu('⚡ Provider Tools')
    .addItem('📝 Manual Verification Tool', 'showVerificationSidebar')
    .addSeparator()
    .addSubMenu(ui.createMenu('🛠️ Quick Tools')
      .addItem('🔗 Add Search Links', 'createGoogleSearchLinks')
      .addItem('🔍 Remove Duplicates', 'findAndRemoveDuplicates')
      .addItem('✅ Copy Verified from Queue', 'copyVerifiedFromQueue')
      .addItem('✨ Fix Capitalization', 'fixCapitalizationInSheet')
      .addItem('📄 Format for Export', 'formatVerifiedSheet')
      .addItem('📊 Stats Report', 'generateStatsReport'))
    .addToUi();
}

function showVerificationSidebar() {
  const html = HtmlService.createHtmlOutputFromFile('VerificationSidebar')
    .setWidth(350);
  SpreadsheetApp.getUi().showSidebar(html);
}

// ====================================================================================
// MANUAL VERIFICATION TOOLS
// ====================================================================================

function getActiveRowData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();

  if (!range || range.getRow() < 2) {
    return { error: "Please select a data row (not the header)" };
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
// DUPLICATE REMOVAL (UNIVERSAL - WORKS ON ANY SHEET)
// ====================================================================================

function findAndRemoveDuplicates() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data.shift();

  // Smart column detection - works with any sheet that has these columns
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

  const seen = new Map();  // Use Map to store row numbers for debugging
  const duplicates = [];
  const duplicateDetails = [];

  data.forEach((row, i) => {
    const phone = phoneIdx >= 0 ? normalizePhone(row[phoneIdx]) : '';
    const office = officeIdx >= 0 ? String(row[officeIdx]).toLowerCase().trim() : '';
    const address = addressIdx >= 0 ? String(row[addressIdx]).toLowerCase().trim() : '';
    const placeId = placeIdx >= 0 ? row[placeIdx] : '';

    // Check multiple duplicate criteria
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

    if (isDuplicate) {
      duplicates.push(i + 2);  // +2 because we removed header and sheets are 1-indexed
      duplicateDetails.push({
        row: i + 2,
        office: row[officeIdx] || 'N/A',
        reason: duplicateReason
      });
    } else {
      // Track this row
      const rowNum = i + 2;
      if (phone) seen.set(`phone:${phone}`, rowNum);
      if (placeId) seen.set(`place:${placeId}`, rowNum);
      if (office && address) seen.set(`name+addr:${office}:${address}`, rowNum);
    }
  });

  if (duplicates.length > 0) {
    const detailsPreview = duplicateDetails.slice(0, 5).map(d =>
      `Row ${d.row}: ${d.office} (${d.reason})`
    ).join('\n');

    const moreCount = duplicates.length > 5 ? `\n\n...and ${duplicates.length - 5} more` : '';

    const response = SpreadsheetApp.getUi().alert(
      `Found ${duplicates.length} Duplicates`,
      `${detailsPreview}${moreCount}\n\nRemove these duplicate rows?`,
      SpreadsheetApp.getUi().ButtonSet.YES_NO
    );

    if (response === SpreadsheetApp.getUi().Button.YES) {
      duplicates.reverse().forEach(row => sheet.deleteRow(row));
      SpreadsheetApp.getUi().alert(`Removed ${duplicates.length} duplicates`);
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
// COPY VERIFIED FROM REVIEW QUEUE
// ====================================================================================

function copyVerifiedFromQueue() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const queueSheet = ss.getSheetByName('Manual_Review_Queue');

  if (!queueSheet || queueSheet.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert('Review queue is empty or not found.');
    return;
  }

  const data = queueSheet.getDataRange().getValues();
  const headers = data[0];

  // Find column indices
  const finalStatusIdx = headers.indexOf('Final_Status');
  const reviewStatusIdx = headers.indexOf('Review_Status');

  if (finalStatusIdx === -1) {
    SpreadsheetApp.getUi().alert('Review queue missing required columns.');
    return;
  }

  // Find verified rows (Final_Status = 'Operational')
  const verifiedRows = [];
  for (let i = 1; i < data.length; i++) {
    if (data[i][finalStatusIdx] === 'Operational') {
      verifiedRows.push({ rowNum: i + 1, data: data[i] });
    }
  }

  if (verifiedRows.length === 0) {
    SpreadsheetApp.getUi().alert('No verified providers found in queue.');
    return;
  }

  const response = SpreadsheetApp.getUi().alert(
    'Copy Verified Providers',
    `Found ${verifiedRows.length} verified providers.\n\nCopy to "All_Verified_Providers" sheet and hide from queue?`,
    SpreadsheetApp.getUi().ButtonSet.YES_NO
  );

  if (response !== SpreadsheetApp.getUi().Button.YES) return;

  // Get or create verified sheet
  let verifiedSheet = ss.getSheetByName('All_Verified_Providers');
  if (!verifiedSheet) {
    verifiedSheet = ss.insertSheet('All_Verified_Providers');
    const verifiedHeaders = [
      'Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP',
      'Provider_Type', 'Verified_Date', 'Verified_By', 'Source'
    ];
    verifiedSheet.getRange(1, 1, 1, verifiedHeaders.length)
      .setValues([verifiedHeaders])
      .setFontWeight('bold')
      .setBackground('#e8eaf6');
    verifiedSheet.setFrozenRows(1);
  }

  // Copy data
  const officeIdx = headers.indexOf('Office Name');
  const phoneIdx = headers.indexOf('Phone Number');
  const addressIdx = headers.indexOf('Address');
  const cityIdx = headers.indexOf('City');
  const stateIdx = headers.indexOf('State');
  const zipIdx = headers.indexOf('ZIP');
  const providerIdx = headers.indexOf('Provider_Type');
  const reviewerIdx = headers.indexOf('Reviewer');

  verifiedRows.forEach(item => {
    const row = item.data;
    const newRow = [
      row[officeIdx] || '',
      row[phoneIdx] || '',
      row[addressIdx] || '',
      row[cityIdx] || '',
      row[stateIdx] || '',
      row[zipIdx] || '',
      row[providerIdx] || 'PCP',
      new Date(),
      row[reviewerIdx] || Session.getActiveUser().getEmail(),
      'Manual Review Queue'
    ];
    verifiedSheet.appendRow(newRow);
  });

  // Hide rows in queue (don't delete - keeps audit trail)
  verifiedRows.reverse().forEach(item => {
    queueSheet.hideRows(item.rowNum);
  });

  SpreadsheetApp.getUi().alert(
    'Success!',
    `Copied ${verifiedRows.length} providers to "All_Verified_Providers" sheet.\n\nRows hidden in review queue (not deleted).`,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

// ====================================================================================
// UTILITY FUNCTIONS
// ====================================================================================

function createGoogleSearchLinks() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  const headers = data.shift();

  const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));

  const officeIdx = findIdx(['office', 'practice', 'name']);
  if (officeIdx === -1) {
    SpreadsheetApp.getUi().alert('Error: Could not find Office Name column');
    return;
  }

  const addressIdx = findIdx(['address']);
  const cityIdx = findIdx(['city']);
  const stateIdx = findIdx(['state', 'st']);

  const richText = data.map(row => {
    const office = row[officeIdx];
    if (office) {
      const parts = [
        office,
        addressIdx >= 0 ? row[addressIdx] : '',
        cityIdx >= 0 ? row[cityIdx] : '',
        stateIdx >= 0 ? row[stateIdx] : ''
      ].filter(Boolean);
      const url = `https://www.google.com/search?q=${encodeURIComponent(parts.join(' '))}`;
      return [SpreadsheetApp.newRichTextValue().setText(office).setLinkUrl(url).build()];
    }
    return [office];
  });

  if (richText.length > 0) {
    sheet.getRange(2, officeIdx + 1, richText.length, 1).setRichTextValues(richText);
    SpreadsheetApp.getUi().alert(`Added search links to ${richText.length} rows`);
  }
}

function formatVerifiedSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName('All_Verified_Providers');

  if (!source || source.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert('No verified data to format');
    return;
  }

  const data = source.getDataRange().getValues();
  const headers = data.shift();

  const findIdx = (terms) => headers.findIndex(h => h && terms.some(term => h.toLowerCase().includes(term)));

  const officeIdx = findIdx(['office', 'name']);
  const phoneIdx = findIdx(['phone', 'number']);
  const addressIdx = findIdx(['address']);
  const cityIdx = findIdx(['city']);
  const stateIdx = findIdx(['state', 'st']);
  const zipIdx = findIdx(['zip']);

  const formatted = data.map(row => [
    row[officeIdx] || '',
    row[phoneIdx] || '',
    row[addressIdx] || '',
    row[cityIdx] || '',
    row[stateIdx] || '',
    row[zipIdx] || ''
  ]);

  let destSheet = ss.getSheetByName('All_Providers_Formatted');
  if (destSheet) {
    destSheet.clear();
  } else {
    destSheet = ss.insertSheet('All_Providers_Formatted');
  }

  const destHeaders = ['Office Name', 'Phone Number', 'Address', 'City', 'State', 'ZIP'];
  destSheet.getRange(1, 1, 1, 6).setValues([destHeaders]).setFontWeight('bold').setBackground('#e8eaf6');
  destSheet.getRange(2, 1, formatted.length, 6).setValues(formatted);
  destSheet.activate();

  SpreadsheetApp.getUi().alert(`Formatted ${formatted.length} providers`);
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

// Consolidated capitalization fix
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

  // Add periods after single initials
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
  const errors = ss.getSheetByName('All_Provider_Errors');
  const review = ss.getSheetByName('Manual_Review_Queue');

  const stats =
    `Manual Verification Stats:\n\n` +
    `Verified: ${verified ? verified.getLastRow() - 1 : 0}\n` +
    `Needs Review: ${review ? review.getLastRow() - 1 : 0}\n` +
    `Errors: ${errors ? errors.getLastRow() - 1 : 0}`;

  SpreadsheetApp.getUi().alert('Statistics', stats, SpreadsheetApp.getUi().ButtonSet.OK);
}
