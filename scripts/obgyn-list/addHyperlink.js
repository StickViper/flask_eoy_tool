function createGoogleSearchLinks() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var dataRange = sheet.getDataRange();  // Get all the data in the sheet
  var data = dataRange.getValues();
  
  for (var i = 1; i < data.length; i++) {  // Start from row 2 to avoid the header row
    var office = data[i][0];  // First column (Office name)
    var address = data[i][2]; // Third column (Address)
    var city = data[i][3];    // Fourth column (City)
    var state = data[i][4];   // Fifth column (State)
    var zip = data[i][5];     // Sixth column (Zip code)
    
    // Concatenate all the details into a search query
    var searchQuery = office + " " + address + " " + city + " " + state + " " + zip;
    var searchUrl = 'https://www.google.com/search?q=' + encodeURIComponent(searchQuery);
    
    // Get the range of the first column cell (office name) for each row and set the hyperlink
    var cell = sheet.getRange(i + 1, 1);  // Row i+1, Column 1 (first column)
    cell.setRichTextValue(SpreadsheetApp.newRichTextValue()
        .setText(office)  // Keep the text as the original office name
        .setLinkUrl(searchUrl)  // Attach the Google Search URL as a hyperlink
        .build());
  }
}
