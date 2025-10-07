function countColoredCells(range, color, refreshTrigger) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var range = sheet.getRange(range);
  var backgrounds = range.getBackgrounds();
  var values = range.getValues(); // Get the contents of the cells
  var count = 0;

  for(var i = 0; i < backgrounds.length; i++) {
    for(var j = 0; j < backgrounds[i].length; j++) {
      if(backgrounds[i][j] == color && values[i][j] !== '') {
        count++;
      }
    }
  }

  return count;
}


function refreshCalculations() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var triggerCell = sheet.getRange("Z1");
  var currentValue = triggerCell.getValue();
  triggerCell.setValue(currentValue + 1); // Increment Z1 to trigger recalculation
}
