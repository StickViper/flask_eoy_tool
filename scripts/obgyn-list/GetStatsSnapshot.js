/**
 * GetStatsSnapshot.js - Helper to extract STATS sheet data
 *
 * Usage: Run getStatsSnapshot() from Apps Script editor
 * Returns: JSON string of STATS sheet data (copy to Claude)
 */

function getStatsSnapshot() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const statsSheet = findStatsSheet(ss);

  if (!statsSheet) {
    Logger.log("ERROR: No STATS sheet found");
    return "No STATS sheet found";
  }

  const lastRow = statsSheet.getLastRow();
  const lastCol = statsSheet.getLastColumn();

  if (lastRow === 0 || lastCol === 0) {
    Logger.log("ERROR: STATS sheet is empty");
    return "STATS sheet is empty";
  }

  const data = statsSheet.getRange(1, 1, lastRow, lastCol).getValues();

  const snapshot = {
    sheetName: statsSheet.getName(),
    spreadsheetName: ss.getName(),
    spreadsheetId: ss.getId(),
    lastRow: lastRow,
    lastCol: lastCol,
    capturedAt: new Date().toISOString(),
    data: data
  };

  const jsonStr = JSON.stringify(snapshot, null, 2);
  Logger.log(jsonStr);

  // Also show in UI for easy copying
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'STATS Snapshot Captured',
    `Sheet: ${statsSheet.getName()}\n` +
    `Rows: ${lastRow}, Cols: ${lastCol}\n\n` +
    `Check "View > Logs" (Ctrl+Enter) to copy JSON data`,
    ui.ButtonSet.OK
  );

  return jsonStr;
}

function findStatsSheet(ss) {
  const sheets = ss.getSheets();

  // Try exact match first
  let statsSheet = ss.getSheetByName('STATS');
  if (statsSheet) return statsSheet;

  // Try case-insensitive match
  for (let sheet of sheets) {
    const name = sheet.getName().toLowerCase();
    if (name === 'stats' || name.includes('stats')) {
      return sheet;
    }
  }

  return null;
}

/**
 * Menu item to run snapshot
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Stats Tools')
    .addItem('📸 Get STATS Snapshot', 'getStatsSnapshot')
    .addToUi();
}
