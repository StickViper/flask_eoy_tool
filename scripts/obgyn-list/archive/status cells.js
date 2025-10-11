function onEdit(e, statusColumn = 10, targetSheetName = 'Working List 2025', colorMappings = {
  'Successful Order': '#FFFF00', // Yellow
  'Requested Email': '#00FF00', // Green
  'Potentially Invalid': '#FF0000', // Red
  'Voicemail/No Answer': '#FF00FF', // Fuchsia
  'Not interested': '#FFFFFF', // White
  '': '#FFFFFF' // White
}) {
  // Get the active sheet where the edit was made
  const sheet = e.source.getActiveSheet();
  const sheetName = sheet.getName();

  // Only run the script if the edit is made in the target sheet
  if (sheetName !== targetSheetName) {
    return;
  }
  
  // Get the row and column of the edited cell
  const row = e.range.getRow();
  const col = e.range.getColumn();

  // Check if the edited cell is in the "Call Status" column, and avoid the header row
  if (col === statusColumn && row > 1) {
    const statusValue = e.value.trim(); // Get the new value of the "Call Status" cell and trim whitespace
    
    // Get the range of the entire row that was edited
    const range = sheet.getRange(row, 1, 1, sheet.getLastColumn());

    // Set row background color based on the status value
    const color = colorMappings[statusValue] || colorMappings[''];
    range.setBackground(color);
    
    // Check if the status is "Not interested"
    if (statusValue.toLowerCase() === 'not interested') {
      // Set the cell to the left of the current one (status column) to 0
      sheet.getRange(row, statusColumn - 1).setValue(0);

      // Get the cell to the right of the current one (status column)
      const notesCell = sheet.getRange(row, statusColumn + 1);
      let currentNotes = notesCell.getValue();
      
      // Check if "not interested" is already present in the notes, ignoring case
      if (!currentNotes.toLowerCase().includes('not interested')) {
        // Append "; not interested" if notes are not empty, otherwise just add "not interested"
        if (currentNotes) {
          notesCell.setValue(currentNotes + "; not interested");
        } else {
          notesCell.setValue("not interested");
        }
      }
    }
  }
}

function updateAllCallStatusBasedOnColor(sheetName = 'Working List 2025', statusColumn = 10, notesColumn = 11, colorMappings = {
  '#ffff00': 'Successful Order', // Yellow
  '#00ff00': 'Requested Email', // Green
  '#ff0000': 'Potentially Invalid', // Red
  '#ff00ff': 'Voicemail/No Answer', // Fuchsia
  '#ffffff': '' // White
}) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) return;

  const lastRow = sheet.getLastRow();
  for (let row = 2; row <= lastRow; row++) { // Start from row 2 to avoid header
    // Get the background color of the notes column cell in lowercase
    const backgroundColor = sheet.getRange(row, notesColumn).getBackground().toLowerCase();
    
    // Log the actual background color retrieved
    Logger.log(`Row ${row}: Background Color - ${backgroundColor}`);
    
    let status = colorMappings[backgroundColor] || '';
    
    // Check if the notes column contains "not interested" (case insensitive)
    const notes = sheet.getRange(row, notesColumn).getValue().toLowerCase();
    if (notes.includes('not interested')) {
      status = 'Not Interested';
    }
    
    // Log the status for each row
    Logger.log(`Row ${row}: Status - ${status}`);
    
    // Update the Call Status column with the appropriate status, ensuring it matches validation
    if (['Successful Order', 'Requested Email', 'Potentially Invalid', 'Voicemail/No Answer', 'Not Interested'].includes(status) || status === '') {
      sheet.getRange(row, statusColumn).setValue(status);
      sheet.getRange(row, statusColumn).setBackground(backgroundColor);
    }
  }
}
