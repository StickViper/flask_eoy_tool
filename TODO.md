# JGDC Master TODO List

## 🔴 CRITICAL (Blocking Current Work)

### Data Quality
- [ ] **Fix capitalization at ALL stages of pipeline**
  - [x] Python script (nppes_filter_pcps.py) - DONE
  - [x] Google Sheets toolbox (ToolboxSuite.js) - DONE
  - [ ] Apply to existing Working List data (run fix on all sheets)
  - [ ] Apply to existing Provider Search data
  - [ ] Document when/where to run fixes

- [ ] **Validate specialist contamination in existing data**
  - [x] Identify contaminated taxonomy codes (ER, hospitalists, students) - DONE
  - [ ] Audit existing Working Lists for specialists
  - [ ] Remove contaminated entries from active lists
  - [ ] Re-filter TX, TN, OR, OK with v3.0 script

- [ ] **Implement "Not Interested" workflow enforcement**
  - [ ] Design dropdown options (General / Wrong Specialty / Closed-Moved)
  - [ ] Auto-fill notes based on selection
  - [ ] Decide: Soft validation vs. hard enforcement vs. protected columns
  - [ ] Update onEdit trigger to handle new workflow

## 🟠 HIGH PRIORITY (Next 2 Weeks)

### Validation & Debugging Tools

- [ ] **Build validation script for Working Lists**
  - [ ] Check: Yellow rows not in New Orders sheet
  - [ ] Check: "Not interested" missing notes or 0 in QTY
  - [ ] Check: Potential duplicates (same phone/address)
  - [ ] Check: QTY mismatches vs New Orders
  - [ ] Check: Missing required data (phone, address)
  - [ ] Output: Hidden "⚠️" column with issue flags (quiet, non-intrusive)
  - [ ] Add "Clear all warnings" function

- [ ] **Duplicate detection & resolution**
  - [ ] Find duplicates by phone number
  - [ ] Find duplicates by address
  - [ ] Find duplicates by office name
  - [ ] Create duplicate review UI (sidebar?)
  - [ ] Auto-merge clear duplicates
  - [ ] Flag ambiguous duplicates for manual review
  - [ ] Check if duplicate orders shipped (cross-reference New Orders)

### Automation Gaps

- [ ] **Automate CSV import workflow**
  - [ ] Design UI for batch size selection
  - [ ] Preview # of providers per state before import
  - [ ] Auto-create properly named sheets
  - [ ] Set up column mapping/validation
  - [ ] Handle import errors gracefully

- [ ] **Annual re-verification scheduler**
  - [ ] Design: When to re-verify (yearly? per call cycle?)
  - [ ] Mark providers as "needs re-verification" after X months
  - [ ] Batch re-verification process
  - [ ] Update verification dates

## 🟡 MEDIUM PRIORITY (Within Month)

### Code Quality & Maintainability

- [ ] **Set up version control properly**
  - [ ] Initialize git repo (`git init`)
  - [ ] Create `.gitignore` (exclude CSVs, API keys)
  - [ ] Set up clasp for Google Apps Script sync
  - [ ] Document clasp workflow for team
  - [ ] Create branches for testing changes

- [ ] **Improve error handling**
  - [ ] Add try-catch blocks to all API calls
  - [ ] Better error messages for users
  - [ ] Log errors to separate sheet for debugging
  - [ ] Graceful degradation when APIs fail

- [ ] **Code documentation**
  - [ ] Add JSDoc comments to all functions
  - [ ] Create inline examples for complex functions
  - [ ] Document all CONFIG options
  - [ ] Create troubleshooting guide

### User Experience

- [ ] **Implement Filter Views safely**
  - [ ] Research: Can filter views break active routes?
  - [ ] Create saved filter views for common tasks:
    - Uncalled providers
    - Successful orders
    - Needs follow-up
  - [ ] Document how to use without breaking workflow
  - [ ] Train coworkers on filter views

- [ ] **Improve consolidation workflow**
  - [ ] Add pre-consolidation validation checklist
  - [ ] Automate year-transition steps:
    - Add new QTY column
    - Duplicate & rename sheets with "OLD" prefix
    - Clear New Orders
    - Clear colors/statuses (preserve emails in Notes)
    - Update STATS tab formulas
    - Update dashboard IMPORTRANGE links
  - [ ] Create "Year-End Wizard" UI
  - [ ] Dry-run mode for consolidation

## 🟢 LOW PRIORITY (Nice to Have)

### Features

- [ ] **Enhanced search functionality**
  - [ ] Search by provider name across all sheets
  - [ ] Search by phone number
  - [ ] Search by city/zip code
  - [ ] "Find me in list" function for providers

- [ ] **Reporting & Analytics**
  - [ ] Success rate by state
  - [ ] Success rate by provider type
  - [ ] Call efficiency metrics (calls per order)
  - [ ] Year-over-year comparison
  - [ ] Export reports for board meetings

- [ ] **Coworker guardrails**
  - [ ] Protected ranges for critical columns (QTY, Notes when "not interested")
  - [ ] Data validation rules for dropdown fields
  - [ ] Automated reminders (e.g., "Don't forget to add 0 to QTY!")
  - [ ] Undo protection (warning before deleting data)

### Data Management

- [ ] **Better organization handling**
  - [ ] Improve clinic vs. individual detection
  - [ ] Flag when clinic + individual both exist at same address
  - [ ] Smart merge suggestions
  - [ ] Track which NPIs are clinics vs. individuals

- [ ] **Name pattern filtering optimization**
  - [ ] Enable toggleable name filtering in Python script
  - [ ] Build pattern library from actual data
  - [ ] Create "review excluded" UI
  - [ ] Allow re-adding false positives

## 📋 MAINTENANCE & OPERATIONS

### Regular Tasks

- [ ] **Monthly:**
  - [ ] Audit specialist contamination in new imports
  - [ ] Check for duplicate entries
  - [ ] Validate STATS tab accuracy
  - [ ] Review API usage/costs

- [ ] **Quarterly:**
  - [ ] Update NPPES data (new download from CMS)
  - [ ] Re-verify closed/inactive providers
  - [ ] Clean up Invalid/Inactive List

- [ ] **Annually:**
  - [ ] Year-end consolidation
  - [ ] Archive old year sheets
  - [ ] Update all year references in code
  - [ ] Review and optimize workflow

### Technical Debt

- [ ] **Fix jank STATS tab trigger**
  - Current: Updates random cell to force recalc
  - Better: Proper refresh mechanism
  - Best: Real-time formula updates

- [ ] **Standardize sheet naming**
  - Document naming conventions
  - Rename inconsistent sheets
  - Update all hardcoded sheet references in code

- [ ] **Optimize performance**
  - Batch API calls more efficiently
  - Reduce sheet read/write operations
  - Cache frequently accessed data
  - Profile slow operations

## 🔬 RESEARCH & EXPLORATION

- [ ] **Explore Google Sheets API limits**
  - How many API calls can we make?
  - Rate limiting strategies
  - Alternative APIs if we hit limits

- [ ] **Investigate automated calling integrations**
  - Can we integrate with a dialer?
  - Auto-populate call results?
  - Voice recording transcription?

- [ ] **Better duplicate detection algorithms**
  - Fuzzy matching for office names
  - Address normalization (Suite 100 vs. Ste 100)
  - Phone number formatting variations

- [ ] **Machine learning for verification**
  - Can we predict "not interested" based on patterns?
  - Auto-flag likely closed practices?
  - Recommend similar providers when one is invalid?

## 📝 DOCUMENTATION NEEDED

- [ ] **User guides**
  - [ ] How to run yearly consolidation
  - [ ] How to add new states
  - [ ] How to handle duplicates
  - [ ] How to use filter views safely
  - [ ] Troubleshooting common errors

- [ ] **Developer guides**
  - [ ] How to modify NPPES filter script
  - [ ] How to add new validation checks
  - [ ] How to update API integrations
  - [ ] Testing checklist before deploying changes

- [ ] **Process documentation**
  - [ ] Full workflow diagram
  - [ ] Decision trees for edge cases
  - [ ] Data dictionary (what each column means)
  - [ ] When to escalate issues

---

## Recently Completed ✅

- [x] Spot-check TX, TN, OR, OK providers for capitalization issues
- [x] Analyze specialist contamination in filtered data
- [x] Design tighter NPPES taxonomy filter
- [x] Implement updated NPPES filter script (v3.0) with:
  - Tightened taxonomy codes (4 only)
  - Organization handling (independent clinics)
  - Capitalization fixes (6 types)
  - Dry-run preview mode
  - Excluded providers audit trail
- [x] Add capitalization fix to ToolboxSuite.js
- [x] Create README.md documenting project structure
- [x] Create master TODO.md (this file)

---

## Notes & Ideas

- Consider building a dashboard sheet that shows progress across all states
- Explore using Google Forms for manual verification instead of sidebar?
- Could we use Zapier/Make.com to automate some steps?
- Build a "health check" function that runs all validations at once
- Create video tutorials for new volunteers
- Set up automated backups of sheets before major changes
