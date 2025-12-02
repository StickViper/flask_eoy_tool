# Consolidated Review Questions

**Purpose:** This document consolidates all questions identified during the comprehensive review. It serves as the single source of truth for decisions required to unblock the project.

---

## PART 1: STRATEGIC DECISIONS (High Priority)
*Source: DECISION_QUESTIONS.md*

### Q1: Should status-to-color use exact match or substring match?

**Context:**
The system assigns background colors to rows based on the "Call Status" column (e.g., "Successful Order" → Yellow). This logic exists in two places:
1.  **Google Sheets (JavaScript):** Runs when you edit a cell. Currently requires an **exact match** (e.g., "Successful Order").
2.  **EOY Tool (Python):** Runs during end-of-year cleanup. Currently uses **substring match** (e.g., accepts "Order Successful", "Successful order").

**The Problem:**
Inconsistency. If a user types "Voicemail" (missing "/No Answer"):
- **Google Sheets:** Turns White (no match).
- **EOY Tool:** Counts it as Fuschia (match found).
This leads to data discrepancies where the EOY tool "sees" orders that the Sheet doesn't highlight.

**Options:**
- **A) Enforce Exact Match (Recommended):** Update Python to be strict like JavaScript.
    - *Pros:* 100% consistency between tools. Forces clean data.
    - *Cons:* Users must type exactly (or use dropdowns). Less forgiving of typos.
- **B) Allow Substring Match:** Update JavaScript to be flexible like Python.
    - *Pros:* Easier for users (can type "vm" or "order").
    - *Cons:* Harder to implement in Apps Script. Ambiguity risk (e.g., does "No" match "No Answer" or "Not Interested"?).

**Recommendation:** Option A (Exact Match). It's safer for data integrity.

**Your decision:** [Option A (Exact Match) + Dropdown; I want to enforce drop-down use]

**Agent Response:**
✅ **Confirmed.** I will update the Python script to enforce exact matching and ensure the Google Sheet validation rejects invalid inputs.

---

### Q2: Should there be dropdown validation for Status column?

**Context:**
The "Call Status" column in Google Sheets currently allows **free text**. Users can type anything they want.

**The Problem:**
Free text leads to typos ("Vocemail", "Succesful", "Order confirmed").
- If we choose **Exact Match (Q1)**, these typos will break the color coding immediately.
- Even with **Substring Match**, typos like "Succesful" (missing 's') won't match.

**Options:**
- **A) Add Dropdown Validation (Recommended):** Restrict input to the 5 valid statuses: *Successful Order, Requested Email, Potentially Invalid, Voicemail/No Answer, Not interested*.
    - *Pros:* Prevents typos entirely. Guarantees color coding works.
    - *Cons:* Users cannot type custom notes in the Status column (must use the Notes column instead).
- **B) Keep Free Text:** Allow any input.
    - *Pros:* Maximum freedom for users.
    - *Cons:* High risk of broken data and inconsistent colors. Requires constant manual cleanup.

**Recommendation:** Option A (Add Dropdown).

**Your decision:** [YES - Add Dropdown; Dropdown is already present in sheets, but if you can make it enforceable, that would be great]

**Agent Response:**
✅ **Confirmed.** I will verify the Google Sheet data validation settings to ensure they are set to "Reject input" for invalid entries, making it enforceable.

---

### Q8: Should EOY Apps Script automation be deprecated?

**Context:**
We currently have two tools that do "End of Year" cleanup tasks:
1.  **ToolboxSuite.js (Apps Script):** Runs inside Google Sheets. Has menu items like "Audit Working List" and "Validate Yellow Orders".
2.  **eoy_tool.py (Flask App):** A separate web application designed to replace the Apps Script.

**The Problem:**
Redundancy and Maintenance.
- The Apps Script version is functional but has known bugs (see TODO.md).
- The Flask app is cleaner and more powerful but the "Write Phase" (saving changes) isn't finished yet.
- Maintaining two separate codebases that do the same thing is inefficient and error-prone.

**Options:**
- **A) Keep Both:** Maintain two separate tools indefinitely.
    - *Pros:* Redundancy if one fails.
    - *Cons:* Double the maintenance work. Confusing for users (which one do I use?).
- **B) Deprecate Apps Script (Recommended):** Focus all effort on finishing the Flask app. Remove the EOY functions from Apps Script once Flask is ready.
    - *Pros:* Single source of truth. Modern interface. Easier to test/debug (Python vs JS).
    - *Cons:* Reliance on the Flask app being finished.
- **C) Fix Apps Script Only:** Abandon the Flask app and just fix the bugs in Apps Script.
    - *Pros:* No need to finish the Flask app. Stays inside Google Sheets.
    - *Cons:* Apps Script is harder to maintain and has execution time limits for large datasets.

**Recommendation:** Option B (Deprecate Apps Script eventually).

**Your decision:** [Deprecate (Eventually)]

**Agent Response:**
✅ **Confirmed.** I will prioritize the Flask app development. I will mark the Apps Script EOY functions as "Legacy/Deprecated" in the documentation to prevent future confusion.

---

### Q3: Are shortcuts.js TODOs (Ctrl+F search, Ctrl+E export) planned?

**Context:**
The file `shortcuts.js` contains placeholder code (TODOs) for two features:
1.  **Ctrl+F:** Open a custom search modal.
2.  **Ctrl+E:** Export the current category to CSV.

**The Problem:**
These features are currently **incomplete**. The keyboard listeners exist, but they don't do anything.

**Options:**
- **A) Implement Features (Recommended):** Build the search modal and export logic.
    - *Pros:* High value for users. "Search" and "Export" are standard expectations for data tools.
    - *Cons:* Development effort required.
- **B) Remove TODOs:** Delete the placeholders.
    - *Pros:* Cleans up the code. No broken promises.
    - *Cons:* Users miss out on useful features.

**Recommendation:** Option A (Implement).

**Your decision:** [Implement features; I want to implement a bunch of shortcuts for streamlining this cleanup process, open to suggestions on other shortcuts to implement]

**Agent Response:**
✅ **Confirmed.** I will implement Ctrl+F and Ctrl+E. I have also added a task to "Brainstorm additional shortcuts" to the TODO list.

---

### Q4: Should undo/redo be prioritized?

**Context:**
The EOY Tool UI has "Undo" and "Redo" buttons. The frontend code (`undo.js`) is ready.
However, the **backend (Python)** logic to actually restore the state is missing (marked as TODO).

**The Problem:**
**Misleading UX.** Users see the buttons and expect them to work. If they make a mistake and click "Undo", nothing happens (or worse, it says "Success" but doesn't change data).

**Options:**
- **A) Implement Backend (Recommended):** Finish the feature.
    - *Pros:* Critical safety net for users doing bulk cleanup. High confidence.
    - *Cons:* Complex to implement state restoration correctly.
- **B) Disable/Hide Buttons:** Hide them until the backend is ready.
    - *Pros:* Honest UX. Easy to do.
    - *Cons:* No safety net for users.
- **C) Remove Feature:** Delete `undo.js` entirely.
    - *Pros:* Simplifies codebase.
    - *Cons:* Permanent loss of a useful feature.

**Recommendation:** Option A (Implement). Safety is key for a cleanup tool.

**Your decision:** [Implement Backend (Priority); keep UI, but for UX add 'WIP' to buttons; add implementation planning to TODO]

**Agent Response:**
✅ **Confirmed.** I will add a "(WIP)" label or tooltip to the buttons immediately and add the backend implementation to the high-priority TODO list.

---

### Q5: Should tests have --non-interactive flag?

**Context:**
Some Python scripts (e.g., `eoy_tool.py`) pause execution to ask the user for confirmation: `input("Continue anyway? (y/n): ")`.

**The Problem:**
**Blocks Automation.** We cannot run these tests automatically (e.g., in a CI/CD pipeline or a batch script) because they hang forever waiting for a user to type 'y'.

**Options:**
- **A) Add --assume-yes flag (Recommended):** Allow running with a flag (e.g., `python script.py --yes`) to automatically answer 'y'.
    - *Pros:* Enables automated testing. Keeps safety check for manual runs.
    - *Cons:* Minor code change required.
- **B) Remove Prompts:** Delete the `input()` calls.
    - *Pros:* Simple.
    - *Cons:* Risky. Users might accidentally run destructive actions without warning.

**Recommendation:** Option A (Add flag).

**Your decision:** [Add --assume-yes flag]

**Agent Response:**
✅ **Confirmed.** I will implement the `--assume-yes` argument in the relevant scripts.

---

### Q6: How should test files (similarity-test.js, ToolboxSuite.test.js) be run?

**Context:**
We have JavaScript test files in `test-data/`. These are **standalone** files, not part of the Google Apps Script environment.

**The Problem:**
**Unclear Execution.** It's not documented how to run them. Do we copy-paste into the browser console? Run with Node.js?

**Options:**
- **A) Node.js (Recommended):** Run via command line (`node test-data/similarity-test.js`).
    - *Pros:* Standard, fast, reproducible.
    - *Cons:* Requires Node.js installed (standard for devs).
- **B) Browser Console:**
    - *Pros:* No install needed.
    - *Cons:* Manual, tedious, hard to automate.

**Recommendation:** Option A (Node.js).

**Your decision:** [A - Node.js; add to TODO; idk wut node.js is, also currently present tests may be deprecated or unnecessary]

**Agent Response:**
ℹ️ **Clarification:** Node.js is simply a tool that lets you run JavaScript files on your computer (like Python) instead of in a browser.
*   **Action:** I will keep these tests because they verify the **fuzzy matching logic**, which is critical for the EOY tool.
*   **Next Step:** I will document exactly how to run them (e.g., `node test-data/similarity-test.js`) in `TEST_RESULTS.md` so you don't need to worry about the details.

---

### Q7: Should 70% match threshold be configurable?

**Context:**
The fuzzy matching algorithm (used to find duplicate providers) considers a match "High Confidence" if the similarity score is **> 70%**.

**The Problem:**
**Hardcoded Value.** The 70% number is buried in the code.
- If 70% is too low, we get false positives (different doctors marked as same).
- If 70% is too high, we miss real duplicates (typos not caught).

**Options:**
- **A) Keep Hardcoded 70% (Recommended for now):**
    - *Pros:* Simple. Test results show it works well (97.6% accuracy on current data).
    - *Cons:* Might need changing for future datasets.
- **B) Make Configurable:** Read from a config file.
    - *Pros:* Flexible.
    - *Cons:* Adds complexity. Users might break it by setting bad values.

**Recommendation:** Option A. Only change if we see actual issues.

**Your decision:** [Value can be hardcoded but must be determined via thorough testing with real data]

**Agent Response:**
✅ **Confirmed.** I will keep it hardcoded for now but add a specific task to "Verify 70% threshold with real data" to the Validation Plan.

---

### Q9: What is GetStatsSnapshot.js used for?

**Context:**
This script creates a menu item "📊 Stats Tools" -> "Get Stats Snapshot". It reads the STATS sheet and returns a JSON string.

**The Problem:**
**Menu Conflict.** Both this script and `ToolboxSuite.js` define an `onOpen()` function. In Apps Script, only one `onOpen()` can run. This means one menu might overwrite the other.

**Options:**
- **A) Dev/Debug Utility (Recommended):** It seems to be a helper for developers to copy-paste stats. It shouldn't be in the production "Misc Tools" menu.
- **B) Merge:** Add its function to the main `ToolboxSuite.js` menu.
- **C) Delete:** If not used anymore.

**Recommendation:** Option A (Treat as Dev Utility).

**Your decision:** [I dont use, so if you don't benefit from it for testing purposes, delete it]

**Agent Response:**
✅ **Confirmed.** I will delete `GetStatsSnapshot.js`.

---

### Q10: Is VerificationSidebar.html polling complexity justified?

**Context:**
The sidebar checks the active row every 300ms ("polling"). It also has logic to ignore "stale" responses (e.g., if you moved to a new row before the old data loaded).

**The Problem:**
**Complexity.** This is a lot of code. Is it over-engineered?

**Options:**
- **A) Keep as-is (Recommended):** The complexity ensures a smooth "follow-me" experience. If we simplify it, the sidebar might lag or show wrong data when users move quickly.
- **B) Simplify:** Remove the debouncing/stale checks.
    - *Pros:* Less code.
    - *Cons:* Worse UX (flickering data).

**Recommendation:** Option A (Keep as-is).

**Your decision:** [We are replacing verification sidebar with flask eoy tool, and ideally its functionality will eventually be merged into flask eoy tool; consider this more or less deprecated (may still have use for a sidebar like this for other functionality but not checking active row)]

**Agent Response:**
✅ **Confirmed.** I will mark `VerificationSidebar.html` and its related code as **Deprecated**. I will not spend time refactoring or simplifying it.

---

### Q11: Is beforeunload auto-save acceptable?

**Context:**
The Flask tool saves your work when you close the tab (`beforeunload` event).

**The Problem:**
**Reliability.** Browsers don't guarantee this event fires (e.g., if the browser crashes or force-quits). The README explicitly warns about this.

**Options:**
- **A) Keep as-is (Manual recommended):** Rely on users pressing Ctrl+S. Use `beforeunload` as a "best effort" backup.
    - *Pros:* Simple.
    - *Cons:* Risk of data loss if user forgets to save.
- **B) Add Periodic Auto-save:** Save every 30 seconds.
    - *Pros:* Safer.
    - *Cons:* More server traffic. Complexity (handling race conditions).

**Recommendation:** Option A. Manual save is standard for this type of bulk edit tool.

**Your decision:** [Keep as-is (Manual recommended)]

**Agent Response:**
✅ **Confirmed.** I will ensure the UI clearly encourages manual saving.

---

### Q13: Where are keyboard shortcuts handled (HTML vs backend)?

**Context:**
Shortcuts like 'G' (Google Search) and 'S' (Save) are documented in the backend file header.

**The Question:**
Where is the *actual code* that listens for these keys?

**Answer:**
**Client-side (HTML).** The code is in `VerificationSidebar.html`.
- *Why this matters:* If we want to change shortcuts, we edit the HTML file, not the backend `.js` file.

**Your answer:** [Client-side (HTML); probably not used?]

**Agent Response:**
ℹ️ **Clarification:** These shortcuts *are* used if you are using the Sidebar. However, since you decided to deprecate the Sidebar (Q10), these are now low priority. I will leave them as-is.

---

### Q12: Should spot_check_taxonomy.py sample randomly instead of first 30?

**Context:**
This script checks if the filtering logic is working by showing a sample of 30 providers. Currently, it takes the **first 30 rows** (`head(30)`).

**The Problem:**
**Bias.** The data might be sorted (e.g., all "A" names, or all from one city). The first 30 might not be representative.

**Options:**
- **A) Random Sample (Recommended):** Pick 30 random rows.
- **B) First 30:** Keep as-is.

**Recommendation:** Option A.

**Your decision:** [YES - Random Sample; more sampled as well; dunno if used, make sure useless code is deleted or archived based on functionality]

**Agent Response:**
✅ **Confirmed.** I will update the script to use random sampling (`df.sample()`) and verify if the script is still useful for your workflow. If not, I will archive it.

---

### Q14 (new): Should DebugRepairSidebar prompt() be upgraded?

**Context:**
When editing notes in the sidebar, the tool uses a browser `prompt()` popup (like an alert box).

**The Problem:**
**Bad UX.** `prompt()` is ugly, blocks the entire browser, and users often accidentally dismiss it.

**Options:**
- **A) Keep as-is:** Low effort.
- **B) Upgrade to Inline Editing (Recommended):** Let users type directly in the sidebar text area.
    - *Pros:* Modern, smoother experience.
    - *Cons:* Minor code update needed.

**Recommendation:** Option B.

**Your decision:** [B (add to TODO) if part of likely future use; otherwise will likely be deleted as part of future cleanup?]

**Agent Response:**
ℹ️ **Recommendation:** Since you decided to deprecate the Sidebar (Q10), I recommend **skipping** this upgrade. It's not worth the effort for a deprecated tool. I will leave the `prompt()` as-is.

---

### Q15 (new): Should NPPES column names have defensive checks?

**Context:**
The script hardcodes column names like "Provider First Name".

**The Problem:**
**Brittleness.** If the government (NPPES) changes their CSV format even slightly (e.g., "Provider Legal First Name"), our script will crash with a confusing error.

**Options:**
- **A) Add Defensive Checks (Recommended):** Check if columns exist at the start and print a clear error if missing.
- **B) Accept Risk:** Assume format won't change.

**Recommendation:** Option A.

**Your decision:** [A - Add Defensive Checks; add to TODO]

**Agent Response:**
✅ **Confirmed.** I will add this to the TODO list and implement the checks.

---

## PART 2: DOCUMENTATION & CODE CLEANUP
*Source: REVIEW_QUESTIONS.md & CODE_REVIEW_QUESTIONS.md*

### Q16: Where IS nppes_filter_pcps.py actually located?

**Context:**
The file `nppes_filter_pcps.py` exists in two places:
1.  `data/nppes/.../nppes_filter_pcps.py`
2.  `scripts/nppes-filter/nppes_filter_pcps.py`

**The Problem:**
**Duplication.** Which one is the "real" one? The `scripts/` version has a header saying "v3.0 - Enhanced Edition", while the `data/` one seems to be a backup.

**Decision:** [Delete data/ copy]
- **Reason:** `scripts/` is the standard location for code. The `data/` folder should only contain data.

**Agent Response:**
✅ **Confirmed.** I will delete the copy in `data/`.

---

### Q17: Should Google Apps Script IDs be redacted from README?

**Context:**
The README contains actual Script IDs (e.g., `1FXjGC...`).

**The Problem:**
**Security.** While not as critical as API keys, these IDs identify our specific internal projects.

**Decision:** [No]
- **Reason:** Not public/shared repository.

**Agent Response:**
✅ **Confirmed.** I will leave the IDs in the README for easier access.

---

### Q18: What are the actual current target states?

**Context:**
Different files list different target states:
- README says "TX, TN, OK, OR".
- TODO.md says "TX, WA, CO, PA".

**Decision:** [No current target states, decided on a case-by-case basis; maybe should be implemented as cli args somehow?]

**Agent Response:**
✅ **Confirmed.** I will remove the hardcoded lists from the documentation and code. I will implement CLI arguments (e.g., `--states TX WA`) to allow you to specify them at runtime.

---

### Q19: Why no mention of the EOY Flask tool at all in root README?

**Context:**
The root `README.md` describes the project but completely omits the `scripts/eoy_tool.py` (Flask app).

**The Problem:**
**Missing Documentation.** A new developer wouldn't know the Flask tool exists.

**Decision:** [Confirmed Missing; missing because README was not updated by previous agent after latest code changes; make sure whenever docs are updated date (from system check) is updated as well for future agent reference]
- **Action:** Update README to include the Flask tool section.

**Agent Response:**
✅ **Confirmed.** I will update the README and add a "Last Updated: [Date]" field to all documentation files I touch.

---

### Q20: Are TEST_RESULTS.md tests still valid?

**Context:**
`TEST_RESULTS.md` claims the tool is "Production Ready".

**The Problem:**
**Inaccurate.** The tool is read-only. The "Write Phase" is missing.

**Decision:** [Only partially valid for READ logic only]
- **Action:** Update document to clarify.

**Agent Response:**
✅ **Confirmed.** I will update `TEST_RESULTS.md` to explicitly state that only the **Read/Validation** logic is production-ready.

---

### Q21: Is Google Places API still being used?

**Context:**
Some code references Google Places API, but README says "NO GOOGLE PLACES API".

**Decision:** [NO - API Abandoned]
- **Reason:** Explicitly removed in Oct 2025. Any remaining code is dead code.

**Agent Response:**
✅ **Confirmed.** I will remove any lingering references to the Google Places API.

---

### Q22: spot_check_taxonomy.py Hardcoded Filename

**Context:**
Script hardcodes `'FILTERED_pcps_ALL_20251018.csv'`.

**The Problem:**
Script fails if the filename changes (which happens every run).

**Decision:** [YES - Use CLI Args]
- **Action:** Update script to accept filename as an argument (`python script.py my_file.csv`).

**Agent Response:**
✅ **Confirmed.** I will update the script to use `argparse` for the filename.

---

### Q23: ToolboxSuite.js Duplication

**Context:**
`scripts/obgyn-list/ToolboxSuite.js` and `scripts/pcp-list/ToolboxSuite.js` are identical.

**Decision:** [YES - Identical]
- **Action:** Keep as is for now (Google Apps Script requires files to be in the project folder), but ensure they stay in sync (perhaps by also noting date at top of file whenever updating for future agent reference).

**Agent Response:**
✅ **Confirmed.** I will add a header comment to both files: `// SYNCED: [Date] - Ensure changes are mirrored in [other path]`.

---

### Q24: debug_color_reading.py Redundancy

**Context:**
This script is a primitive version of `test_critical_assumptions.py`.

**Decision:** [YES - Delete]
- **Reason:** Obsolete.

**Agent Response:**
✅ **Confirmed.** I will delete the file.

---

### Q25: debug_color_reading.py Hardcoded Range

**Context:**
Hardcodes "rows 2-52".

**Decision:** [Irrelevant?]
- **Action:** [Ignore??]

**Agent Response:**
✅ **Resolved.** Since we are deleting `debug_color_reading.py` (Q24), this issue is resolved.

---

### Q28: Hardcoded year 2025

**Context:**
`year=2025` is hardcoded in many places.

**Decision:** [Pass as Parameter / Config; add figuring out ideal implementation to TODO]
- **Reason:** Tool will break in 2026 otherwise.

**Agent Response:**
✅ **Confirmed.** I will add "Implement configurable year parameter" to the TODO list.

---

### Q29: eoy_tool.py Unused Import

**Context:**
Imports `get_effective_format` but never uses it.

**Decision:** [Delete if will not be used]

**Agent Response:**
✅ **Confirmed.** I will remove the import.

---

### Q30: eoy_tool.py Hardcoded Secret Key

**Context:**
`app.secret_key = 'eoy-cleanup-tool-secret-key-2025'`

**Decision:** [Need secret key? Security is not major concern as internal tool]

**Agent Response:**
ℹ️ **Clarification:** Flask **requires** a secret key to manage user sessions (even for simple tools).
*   **Action:** Since security is not a major concern, I will leave it hardcoded but update the variable name to be more generic (removing the year) or use a simple environment variable check if available.

---

### Q31: nppes_filter_pcps.py Parameterization

**Context:**
Target states and input files are hardcoded.

**Decision:** [YES - Use CLI Args]
- **Action:** Use `argparse` to make the script reusable.

**Agent Response:**
✅ **Confirmed.** I will implement CLI arguments.

---

### Q32: nppes_filter_pcps.py Output Directory

**Context:**
Saves files to the current folder.

**Decision:** [YES - Add --output-dir]
- **Reason:** Prevents clutter.

**Agent Response:**
✅ **Confirmed.** I will implement the `--output-dir` argument.

---

### Q33: Conflicting onOpen() functions

**Context:**
`GetStatsSnapshot.js` and `ToolboxSuite.js` both define `onOpen()`.

**Decision:** [Check if resolved after addressing these Qs]

**Agent Response:**
✅ **Resolved.** You decided to delete `GetStatsSnapshot.js` in **Q9**. This removes the conflict entirely.

---

### Q34: QuickStartWizard.html Status

**Context:**
An old HTML wizard for setting up the sheet.

**The Problem:**
It relies on the abandoned Google Places API and missing backend functions.

**Decision:** [Delete/Archive]
- **Reason:** Dead code.

**Agent Response:**
✅ **Confirmed.** I will delete the file.

---

### Q35: QuickStartWizard Config Structure

**Decision:** [Broken Feature]

**Agent Response:**
✅ **Resolved.** Deleting the wizard (Q34) resolves this.

---

### Q36: DebugRepairSidebar.html missing backend function `updateNotes()`

**Context:**
The sidebar calls `google.script.run.updateNotes()`, but that function doesn't exist in the backend (`ToolboxSuite.js`).

**The Problem:**
**Crash.** Clicking "Save Notes" will fail.

**Decision:** [Check if resolved after addressing these Qs]

**Agent Response:**
ℹ️ **Action:** Since you decided to deprecate the Sidebar (Q10), I will **skip** fixing this bug unless you specifically need it. I will assume "No Fix" for now.

---

### Q37: Field naming inconsistency (Office Name vs Office)

**Context:**
Sidebar uses "Office Name", Backend uses "Office".

**Decision:** [Standardize on actual sheet column names]

**Agent Response:**
✅ **Confirmed.** I will check the actual sheet headers and ensure the code matches them.

---

### Q38: DebugRepairSidebar status colors mismatch?

**Context:**
Sidebar CSS hardcodes colors based on exact status names.

**Decision:** [Check if resolved after addressing these Qs]

**Agent Response:**
✅ **Resolved.** You decided to enforce **Exact Match** in **Q1**. This means the Sidebar's exact matching logic is now **correct** and consistent with the rest of the system.

---

### Q39: category.html Context Menu TODO

**Context:**
Comment says `// TODO: implement row context menu`.

**Decision:** [Check if resolved after addressing these Qs]

**Agent Response:**
✅ **Action:** I will delete this TODO comment to clean up the code, as it is low priority and not part of the current plan.
