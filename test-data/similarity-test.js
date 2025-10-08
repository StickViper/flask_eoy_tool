/**
 * Similarity Threshold Testing
 * Tests various office name pairs from real OBGYN data to find optimal threshold
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

// Real examples from OBGYN working list
const testCases = [
  // TRUE NETWORKS (should match)
  {
    name1: "Women to Women Medical Center",
    name2: "Women To Women Medical Center",
    expected: "NETWORK",
    description: "Capitalization difference only"
  },
  {
    name1: "Women's Health Center",
    name2: "Womens Health Center",
    expected: "NETWORK",
    description: "Missing apostrophe"
  },
  {
    name1: "Beach Obstetrics & Gyn",
    name2: "Beach Obstetrics and Gyn",
    expected: "NETWORK",
    description: "& vs 'and'"
  },
  {
    name1: "St Jude Heritage Women's Center",
    name2: "St. Jude Heritage Women's Center",
    expected: "NETWORK",
    description: "Missing period in St."
  },

  // DIFFERENT PRACTICES (should NOT match)
  {
    name1: "Women's Health Center",
    name2: "Women's Health Specialists",
    expected: "DIFFERENT",
    description: "Center vs Specialists"
  },
  {
    name1: "Beach Obstetrics & Gyn",
    name2: "Coastal Obstetrics & Gyn",
    expected: "DIFFERENT",
    description: "Different city prefix"
  },
  {
    name1: "Dr. Cynthia W. Chao, DO",
    name2: "Dr. Mehrdad M. Forghani-Arani, DO",
    expected: "DIFFERENT",
    description: "Different doctors"
  },
  {
    name1: "Sansum Clinic OBGYN",
    name2: "Kern Women's Health Group, Inc.",
    expected: "DIFFERENT",
    description: "Completely different names"
  },

  // EDGE CASES
  {
    name1: "Muth And Weber Ob/gyn Medical Group",
    name2: "Muth & Weber OBGYN Medical Group",
    expected: "NETWORK",
    description: "And/& variation + OB/GYN formatting"
  },
  {
    name1: "Pacific Ob/Gyn",
    name2: "Pacific OBGYN",
    expected: "NETWORK",
    description: "Slash variation"
  }
];

console.log("=" .repeat(80));
console.log("SIMILARITY THRESHOLD TESTING");
console.log("=" .repeat(80));
console.log("");

const thresholds = [0.80, 0.85, 0.90, 0.95];
const results = thresholds.map(threshold => ({
  threshold,
  correctMatches: 0,
  falsePositives: 0,
  falseNegatives: 0
}));

testCases.forEach((test, index) => {
  const score = calculateSimilarity(test.name1, test.name2);
  console.log(`Test #${index + 1}: ${test.description}`);
  console.log(`  Name 1: "${test.name1}"`);
  console.log(`  Name 2: "${test.name2}"`);
  console.log(`  Similarity: ${(score * 100).toFixed(1)}%`);
  console.log(`  Expected: ${test.expected}`);

  thresholds.forEach((threshold, idx) => {
    const predicted = score >= threshold ? "NETWORK" : "DIFFERENT";
    if (predicted === test.expected) {
      results[idx].correctMatches++;
      console.log(`  ✓ Threshold ${threshold}: CORRECT (${predicted})`);
    } else if (test.expected === "NETWORK" && predicted === "DIFFERENT") {
      results[idx].falseNegatives++;
      console.log(`  ✗ Threshold ${threshold}: FALSE NEGATIVE (missed network)`);
    } else {
      results[idx].falsePositives++;
      console.log(`  ✗ Threshold ${threshold}: FALSE POSITIVE (wrong match)`);
    }
  });
  console.log("");
});

console.log("=" .repeat(80));
console.log("RESULTS SUMMARY");
console.log("=" .repeat(80));
results.forEach(r => {
  const accuracy = (r.correctMatches / testCases.length * 100).toFixed(1);
  console.log(`Threshold ${r.threshold}:`);
  console.log(`  Accuracy: ${accuracy}% (${r.correctMatches}/${testCases.length} correct)`);
  console.log(`  False Positives: ${r.falsePositives} (marked different practices as same network)`);
  console.log(`  False Negatives: ${r.falseNegatives} (missed actual networks)`);
  console.log("");
});

console.log("=" .repeat(80));
console.log("RECOMMENDATION");
console.log("=" .repeat(80));
const best = results.reduce((best, curr) =>
  curr.correctMatches > best.correctMatches ? curr : best
);
console.log(`Best threshold: ${best.threshold} with ${best.correctMatches}/${testCases.length} correct`);
console.log(`False positives: ${best.falsePositives}, False negatives: ${best.falseNegatives}`);
