/**
 * Unit Tests for ToolboxSuite.js EOY Automation
 *
 * Run with QUnit (copy to Apps Script) or Node.js + mock framework
 * These tests use the sample data from obgyn-test-samples.csv
 */

// ====================================================================================
// HELPER FUNCTIONS (copied from ToolboxSuite.js for testing)
// ====================================================================================

function normalizePhone(phone) {
  if (!phone || typeof phone.toString !== 'function') return '';
  const phoneStr = phone.toString();
  const mainPhone = phoneStr.split(/\s*[xX]|ext/i)[0].replace(/\D/g, '');
  // Return last 10 digits (handles country codes like +1)
  return mainPhone.slice(-10) || mainPhone;
}

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

function findMostRecentQtyColumn(headers) {
  const qtyColumns = headers.map((h, i) => ({ header: h, index: i }))
    .filter(col => col.header && col.header.toString().toLowerCase().includes('qty'));

  if (qtyColumns.length === 0) return -1;
  if (qtyColumns.length === 1) return qtyColumns[0].index;

  qtyColumns.sort((a, b) => {
    const yearA = parseInt((a.header.match(/\d{4}/) || ['0'])[0]);
    const yearB = parseInt((b.header.match(/\d{4}/) || ['0'])[0]);
    return yearB - yearA;
  });

  return qtyColumns[0].index;
}

// ====================================================================================
// UNIT TESTS
// ====================================================================================

console.log("=" .repeat(80));
console.log("TOOLBOX SUITE EOY AUTOMATION - UNIT TESTS");
console.log("=" .repeat(80));
console.log("");

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, testName, errorMsg) {
  if (condition) {
    console.log(`✓ PASS: ${testName}`);
    testsPassed++;
  } else {
    console.log(`✗ FAIL: ${testName}`);
    if (errorMsg) console.log(`  Error: ${errorMsg}`);
    testsFailed++;
  }
}

function assertEquals(actual, expected, testName) {
  const passed = actual === expected;
  assert(passed, testName, `Expected '${expected}', got '${actual}'`);
}

// ====================================================================================
// TEST SUITE 1: Phone Normalization
// ====================================================================================

console.log("TEST SUITE 1: Phone Normalization");
console.log("-".repeat(80));

assertEquals(
  normalizePhone("(562) 595-7729"),
  "5625957729",
  "Normalize phone with parens and dashes"
);

assertEquals(
  normalizePhone("562.595.7729"),
  "5625957729",
  "Normalize phone with dots"
);

assertEquals(
  normalizePhone("562-595-7729"),
  "5625957729",
  "Normalize phone with dashes only"
);

assertEquals(
  normalizePhone("5625957729"),
  "5625957729",
  "Normalize phone with no formatting"
);

assertEquals(
  normalizePhone("(562) 595-7729 x123"),
  "5625957729",
  "Normalize phone with extension (x)"
);

assertEquals(
  normalizePhone("(562) 595-7729 ext 123"),
  "5625957729",
  "Normalize phone with extension (ext)"
);

assertEquals(
  normalizePhone("+1 (562) 595-7729"),
  "5625957729",
  "Normalize phone with country code (slice last 10)"
);

assertEquals(
  normalizePhone(""),
  "",
  "Handle empty phone"
);

assertEquals(
  normalizePhone(null),
  "",
  "Handle null phone"
);

console.log("");

// ====================================================================================
// TEST SUITE 2: String Similarity
// ====================================================================================

console.log("TEST SUITE 2: String Similarity (Levenshtein Distance)");
console.log("-".repeat(80));

assert(
  calculateSimilarity("Women to Women Medical Center", "Women To Women Medical Center") === 1.0,
  "Identical strings (case insensitive) = 1.0",
  `Got ${calculateSimilarity("Women to Women Medical Center", "Women To Women Medical Center")}`
);

assert(
  calculateSimilarity("Women's Health Center", "Womens Health Center") === 1.0,
  "Missing apostrophe = 1.0",
  `Got ${calculateSimilarity("Women's Health Center", "Womens Health Center")}`
);

const andVsAmpersand = calculateSimilarity("Beach Obstetrics & Gyn", "Beach Obstetrics and Gyn");
assert(
  andVsAmpersand >= 0.85,
  "& vs 'and' ≥ 0.85 threshold",
  `Got ${andVsAmpersand.toFixed(3)}`
);

const muthVariation = calculateSimilarity("Muth And Weber Ob/gyn Medical Group", "Muth & Weber OBGYN Medical Group");
assert(
  muthVariation >= 0.85,
  "Name variations ≥ 0.85 threshold",
  `Got ${muthVariation.toFixed(3)}`
);

const different1 = calculateSimilarity("Women's Health Center", "Women's Health Specialists");
assert(
  different1 < 0.85,
  "Different practices < 0.85 threshold",
  `Got ${different1.toFixed(3)}`
);

const different2 = calculateSimilarity("Beach Obstetrics & Gyn", "Coastal Obstetrics & Gyn");
assert(
  different2 < 0.85,
  "Different city prefix < 0.85 threshold",
  `Got ${different2.toFixed(3)}`
);

console.log("");

// ====================================================================================
// TEST SUITE 3: Column Detection
// ====================================================================================

console.log("TEST SUITE 3: Column Detection");
console.log("-".repeat(80));

const headers1 = ["Practice", "Number", "Address", "Town", "State", "Zip", "2023 QTY", "2024 QTY", "2025 QTY", "CALL STATUS", "Notes"];
assertEquals(
  findMostRecentQtyColumn(headers1),
  8,
  "Find most recent QTY column (2025)"
);

const headers2 = ["Practice", "Number", "Address", "2022 QTY", "2021 QTY"];
assertEquals(
  findMostRecentQtyColumn(headers2),
  3,
  "Find most recent QTY when years out of order"
);

const headers3 = ["Practice", "Number", "Address"];
assertEquals(
  findMostRecentQtyColumn(headers3),
  -1,
  "Return -1 when no QTY columns"
);

const headers4 = ["Practice", "Number", "QTY"];
assertEquals(
  findMostRecentQtyColumn(headers4),
  2,
  "Find QTY column without year"
);

console.log("");

// ====================================================================================
// TEST SUITE 4: Network Detection Logic
// ====================================================================================

console.log("TEST SUITE 4: Network Detection Logic");
console.log("-".repeat(80));

// Simulate network detection
function isNetwork(name1, name2, phone1, phone2, addr1, addr2) {
  if (normalizePhone(phone1) !== normalizePhone(phone2)) return false;
  if (addr1.toLowerCase() === addr2.toLowerCase()) return false; // Same address = not network

  const similarity = calculateSimilarity(name1, name2);
  return similarity >= 0.85;
}

assert(
  isNetwork(
    "Pacific Women's Healthcare Associates",
    "Pacific Women's Healthcare Associates",
    "(949) 559-4870",
    "(949) 559-4870",
    "4870 Barranca Pkwy Ste 200",
    "500 Superior Ave, Ste 310"
  ),
  "Same name + same phone + different addresses = NETWORK"
);

assert(
  isNetwork(
    "Muth And Weber Ob/gyn Medical Group",
    "Muth & Weber OBGYN Medical Group",
    "(562) 595-5380",
    "(562) 595-5380",
    "3828 Shaufele Ave, Ste 200",
    "9999 Fake St, Ste 100"
  ),
  "Similar name (fuzzy match) + same phone + different addresses = NETWORK"
);

assert(
  !isNetwork(
    "Women's Health Center",
    "Women's Health Specialists",
    "(555) 123-4567",
    "(555) 123-4567",
    "123 Main St",
    "456 Oak Ave"
  ),
  "Different names + same phone = NOT NETWORK (duplicate for manual review)"
);

assert(
  !isNetwork(
    "Beach Obstetrics & Gyn",
    "Beach Obstetrics & Gyn",
    "(714) 841-9899",
    "(714) 841-9899",
    "19582 Beach Blvd Ste 202",
    "19582 Beach Blvd Ste 202"
  ),
  "Same name + same phone + SAME address = NOT NETWORK (true duplicate)"
);

console.log("");

// ====================================================================================
// TEST SUITE 5: "Not Interested" Validation
// ====================================================================================

console.log("TEST SUITE 5: 'Not Interested' Validation");
console.log("-".repeat(80));

function validateNotInterested(status, notes, qty) {
  const issues = [];
  if (status.toLowerCase().includes('not interested')) {
    if (!(notes || '').toLowerCase().includes('not interested')) {
      issues.push('Missing "not interested" in Notes');
    }
    if (qty !== 0) {
      issues.push(`QTY should be 0 (currently ${qty})`);
    }
  }
  return issues;
}

assert(
  validateNotInterested("Not Interested", "gave my #; not interested", 0).length === 0,
  "Valid Not Interested: has notes + QTY=0"
);

assert(
  validateNotInterested("Not Interested", "gave callback number", 5).length === 2,
  "Invalid Not Interested: missing note + wrong QTY"
);

assert(
  validateNotInterested("Not Interested", "", 10).length === 2,
  "Invalid Not Interested: no notes + wrong QTY"
);

assert(
  validateNotInterested("Not Interested", "not interested", 0).length === 0,
  "Valid Not Interested: minimal valid case"
);

assert(
  validateNotInterested("Successful Order", "", 10).length === 0,
  "Not 'Not Interested' status - no validation needed"
);

console.log("");

// ====================================================================================
// TEST SUITE 6: Edge Cases
// ====================================================================================

console.log("TEST SUITE 6: Edge Cases");
console.log("-".repeat(80));

// Empty/null handling
assert(
  normalizePhone("") === "",
  "Empty phone returns empty string"
);

assert(
  calculateSimilarity("", "anything") === 0,
  "Empty string similarity = 0"
);

// Note: calculateSimilarity handles null by converting to empty string
const nullSim = calculateSimilarity(null, null);
assert(
  nullSim === 1, // Both null → both empty → identical
  "Null strings both convert to empty, so similarity = 1",
  `Got ${nullSim}`
);

// Mixed data types
assert(
  normalizePhone(5625957729) === "5625957729",
  "Normalize numeric phone"
);

// Very long strings
const longName1 = "A".repeat(100);
const longName2 = "A".repeat(99) + "B";
const longSimilarity = calculateSimilarity(longName1, longName2);
assert(
  longSimilarity > 0.98,
  "Long strings with 1 char difference still very similar",
  `Got ${longSimilarity.toFixed(3)}`
);

console.log("");

// ====================================================================================
// TEST SUMMARY
// ====================================================================================

console.log("=" .repeat(80));
console.log("TEST SUMMARY");
console.log("=" .repeat(80));
console.log(`Total Tests: ${testsPassed + testsFailed}`);
console.log(`Passed: ${testsPassed} ✓`);
console.log(`Failed: ${testsFailed} ✗`);
console.log(`Success Rate: ${((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1)}%`);
console.log("");

if (testsFailed === 0) {
  console.log("🎉 ALL TESTS PASSED! 🎉");
} else {
  console.log(`⚠️  ${testsFailed} test(s) failed. Please review.`);
  process.exit(1);
}
