// CONSOLIDATED CAPITALIZATION FIX - Bug-Free Version
// Fixes: "Md." → "MD.", "Do." → "DO.", "women's" → "Women's" (not "Women'S")

// Configuration for capitalization rules
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

/**
 * Fix capitalization issues in provider names.
 * Handles: ALL CAPS, ProperCase damage, Mc/Mac, apostrophes, hyphens, periods
 *
 * BUGS FIXED:
 * - "Md." now becomes "MD." (not "Md.")
 * - "Do." now becomes "DO." (not "Do.")
 * - "women's" now becomes "Women's" (not "Women'S")
 *
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
    // Apostrophes (o'donnell → O'Donnell, women's → Women's)
    else if (cleanWord.includes("'")) {
      const parts = cleanWord.split("'");
      let afterApostrophe = '';
      if (parts[1]) {
        // FIX: If just possessive 's', keep lowercase; otherwise capitalize (O'Donnell)
        afterApostrophe = parts[1].toLowerCase() === 's' ? 's' :
                         parts[1].charAt(0).toUpperCase() + parts[1].slice(1).toLowerCase();
      }
      const formatted = parts[0].charAt(0).toUpperCase() + parts[0].slice(1).toLowerCase() +
        "'" + afterApostrophe;
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
