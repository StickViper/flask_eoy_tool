# JGDC Master TODO List

## 🔴 IMMEDIATE PRIORITIES (Current Session)

### 0. OBGYN EOY Cleanup Tool (December 2024)

**Status:** ✅ FLASK WEB APP BUILT - Read-only mode working, write phase not implemented
**Last Updated:** 2025-11-17

#### ✅ COMPLETED:
- [x] **Flask web application built** (`scripts/eoy_tool.py`, 1349 lines)
  - Backend: Flask + gspread + rapidfuzz
  - Frontend: HTML templates + vanilla JS + CSS
  - Design: "Data Atelier" aesthetic (warm colors, easy on eyes for 2-4hr sessions)
- [x] **Data loading works** (11 API calls, well under 60/min quota)
  - Working List: 737 rows
  - New Orders: 241 rows
  - Status-to-color mapping (avoids reading 737 cell colors individually)
- [x] **All validation pipelines implemented:**
  - ✅ Yellow→NO fuzzy matching (97.6% high confidence, per TEST_RESULTS.md)
  - ✅ Duplicate detection (exact matches, networks, similar entries)
  - ✅ Status issue flagging (voicemail, email sent, potentially invalid)
  - ✅ 11 review categories with row grouping
- [x] **UI features working:**
  - ✅ Expandable match details (click ▶ to see NO row, confidence %)
  - ✅ Visual duplicate grouping (color-coded borders)
  - ✅ Multi-select (shift/ctrl click)
  - ✅ Sortable columns
  - ✅ Progress auto-save to JSON
  - ✅ Keyboard shortcuts
- [x] **Testing framework created** (`scripts/test_eoy_output.py`)
  - All 8 tests passing (as of 2024-11-16)
  - Match accuracy: 97.6% high confidence
- [x] **Documentation complete** (docs/README.md - 447 lines, current and accurate)

#### ❌ NOT YET IMPLEMENTED (Write Phase):
- [ ] Writing changes to Google Sheets (batch updates)
- [ ] Shadow worksheet creation (_CLEANUP suffix)
- [ ] Undo/redo restore logic (stack exists, restore not implemented)
- [ ] Full edit modal for complex edits
- [ ] Some bulk action handlers

#### 🔧 CURRENT STATE:
**What works:** Load data → Run validations → Review in UI → See match details
**What doesn't:** Actually writing changes back to Google Sheets

**To use tool:**
```bash
cd C:\Users\noagi\Desktop\JGDC
python scripts/eoy_tool.py
# Open http://127.0.0.1:5000
```

#### 📦 ARCHIVED PLANNING DOCS:
These described a Textual TUI that was never built - Flask web app was built instead:
- `docs/archive/EOY_TOOL_ARCHITECTURE_V2.md` (Textual UI design)
- `docs/archive/ARCHITECTURE_GAP_ANALYSIS.md` (planning)
- `docs/archive/UNRESOLVED_QUESTIONS.md` (pre-build questions)

#### ✅ COMPLETE - COMPREHENSIVE TEST SUITE

**Status:** ✅ **COMPLETE** - 124 tests passing, 34% code coverage (2025-11-24)

**Test Framework:** pytest with fixtures, parametrization, and coverage reporting

**Test Phases Completed:**

**Phase 1: Status-to-color mapping (38 tests)**
- ✅ Exact match enforcement (NOT substring matching)
- ✅ Case insensitivity (successful order = SUCCESSFUL ORDER)
- ✅ Edge cases (empty string, None, whitespace, unknown status)
- ✅ All 5 color mappings (yellow, fuschia, green, red, white)
- ✅ Meta-tests proving tests catch 8 bug types

**Phase 2: Fuzzy matching & duplicate detection (48 tests)**
- ✅ Normalization functions (name, address, phone)
- ✅ 70/30 name/address weighting verified
- ✅ token_set_ratio matching behavior
- ✅ Exact duplicates (same phone + name + address)
- ✅ Networks (same phone, ≥85% name similarity, <70% address difference)
- ✅ Fuzzy duplicates (same phone, neither exact nor network)
- ✅ Network notation format (~# for multiple locations)

**Phase 3: Categorization & undo/redo (38 tests)**
- ✅ All 11 review categories defined and populated
- ✅ Category filtering (empty categories removed)
- ✅ Row number sorting within categories
- ✅ Undo stack: sequential IDs, timestamps, 50-action limit
- ✅ Redo stack: action movement between stacks
- ✅ Action types: edit, delete, batch operations
- ✅ State serialization for JSON storage

**Code Coverage:** 34% of eoy_tool.py (219/647 lines)
- Covers critical validation logic
- Flask routes and gspread tested manually

**Run Tests:**
```bash
cd scripts
python -m pytest ../tests/ -v
python -m pytest ../tests/ --cov=eoy_tool --cov-report=html
```

**Test Files:**
- `tests/test_status_to_color.py` (31 tests)
- `tests/test_verification.py` (7 meta-tests)
- `tests/test_fuzzy_matching.py` (26 tests)
- `tests/test_duplicates.py` (22 tests)
- `tests/test_categorization.py` (16 tests)
- `tests/test_undo_redo.py` (22 tests)
- `tests/conftest.py` (fixtures with realistic data)

#### 📋 NEXT STEPS (Prioritized Implementation Roadmap):

**PHASE 1: CRITICAL - Write & Safety (Est. 8-12 hours)**
1. ✅ **Write Phase Implementation** - HIGHEST PRIORITY
   - Batch Google Sheets updates (`gspread.batch_update()`)
   - Shadow worksheets with _CLEANUP suffix
   - Dry-run preview (show exact changes before writing)
   - Backup snapshot creation (auto-create "WL_2025_backup_timestamp")
   - Pre-write validation (catch errors before committing)
   - Incremental save (save progress without finishing everything)

2. ✅ **Change Summary & Audit Trail**
   - Changes Made Report (HTML + exportable PDF/Excel)
   - Before/After comparison view
   - Undo log export for auditing
   - Decision documentation (WHY decisions were made, who, when)

3. ✅ **Validation Checkpoints**
   - Pre-write validation rules engine
   - Required field checks (address, phone, status)
   - Consistency checks (status vs notes, qty logic)
   - Duplicate detection on write
   - Warning system with override capability

**PHASE 2: HIGH VALUE - Prevention & Efficiency (Est. 6-8 hours)**

4. ✅ **Real-Time Duplicate Detection for Route Technicians** - NEW PRIORITY
   - **Google Colab Validation Tool** (simplified interface for techs)
     - Upload WL CSV or connect to Google Sheet
     - Instant duplicate/network detection as techs add rows
     - Visual feedback: "⚠️ Possible network: 3 providers share (555) 123-4567"
     - Export cleaned CSV for import
     - No technical knowledge required

   - **Fast Lookup System** (not full fuzzy matching every time)
     - Phone number index (O(1) lookup for shared phones)
     - Practice name trigram index (fast similarity search)
     - Address normalization cache
     - Network detection algorithm (≥85% name match + same phone)

   - **Real-Time Feedback Options:**
     - Option A: Google Apps Script add-on (runs on sheet edit)
     - Option B: Pre-import validation (Colab tool before adding to WL)
     - Option C: Daily validation report (email to engineer with flags)

   - **Validation Rules for Entry:**
     - Phone format validation (normalize to (XXX) XXX-XXXX)
     - Address completeness check
     - Practice name capitalization
     - Immediate "Already exists?" check against WL
     - Network membership suggestion

5. ✅ **Progress Dashboard** (Technical Implementation - see details below)
   - Real-time category completion tracking
   - Estimated time remaining calculation
   - Visual progress bars with color coding
   - Issue priority scoring (high/medium/low confidence)
   - Auto-refresh on action completion

6. ✅ **Batch Operations UI**
   - Pattern-based cleanup wizard
   - Preview changes before applying
   - Multi-category bulk actions
   - Confidence-based auto-suggestions

**PHASE 3: NICE TO HAVE - Enhancement (Est. 4-6 hours)**

7. ⏸️ **Route Tech Integration**
   - Weekly pre-cleanup validation runs
   - "Route Tech Notes" field for context
   - Flagging system for engineer review
   - Clean data handoff workflow

8. ⏸️ **Phone Number Intelligence**
   - Format normalization (all → (XXX) XXX-XXXX)
   - Twilio validation integration (optional, $0.005/call)
   - Network detection by shared phone
   - Duplicate phone flagging

9. ⏸️ **Year-Over-Year Analytics**
   - Provider retention analysis (2024 → 2025)
   - Reasons for invalidity breakdown
   - Growth rate calculations
   - Export trend reports

**PHASE 4: FUTURE - Advanced Features**

10. ⏸️ **Email Template Generation**
    - Mail merge with {practice_name}, {doctor_name}, {city}
    - Bulk send via Gmail API
    - Track sent/bounced/responded
    - Log in notes column

11. ⏸️ **Address Standardization**
    - USPS validation API integration
    - Geocoding for route optimization
    - Move detection (provider relocated)

12. ⏸️ **Multi-User Collaboration**
    - Row locking during edits
    - Change attribution
    - Comment threads
    - Review workflow

**APPS SCRIPT EOY AUTOMATION:**
- Still exists in `scripts/obgyn-list/ToolboxSuite.js`
- Steps 1-5 work (per commit `d219925`: "Mark EOY Steps 1, 2, network notation as FIXED/VERIFIED")
- See `docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md` for usage
- Flask tool is intended to replace this, but both currently functional

---

## 🔬 TECHNICAL SPECIFICATIONS

### Progress Dashboard Implementation Details

**Data Structure:**
```python
@dataclass
class CategoryProgress:
    category_id: str
    name: str
    total_rows: int
    reviewed_rows: int  # Rows with action != None
    completion_pct: float
    avg_time_per_row: float  # Seconds
    estimated_remaining: float  # Minutes
    confidence: str  # "high", "medium", "low"
    priority: int  # 1 (highest) to 5 (lowest)

@dataclass
class OverallProgress:
    categories: List[CategoryProgress]
    total_issues: int
    resolved_issues: int
    completion_pct: float
    time_elapsed: float  # Minutes since session start
    estimated_total_time: float  # Minutes
    actions_taken: int  # Number of undo stack entries
```

**API Endpoints:**
```python
@app.route('/api/progress/dashboard', methods=['GET'])
def api_progress_dashboard():
    """Return comprehensive progress statistics"""

    # Calculate per-category progress
    category_progress = []
    for category in state.categories:
        # Count rows with actions (reviewed)
        reviewed = sum(1 for row_num in category.row_nums
                      if any(r.row_num == row_num and r.action
                            for r in state.wl_rows))

        total = len(category.row_nums)
        completion = (reviewed / total * 100) if total > 0 else 0

        # Estimate time based on category complexity
        time_per_row = get_category_avg_time(category.id)
        remaining = (total - reviewed) * time_per_row / 60  # Minutes

        # Confidence based on match scores
        confidence = calculate_category_confidence(category)

        # Priority: exact_dupes=1, networks=2, fuzzy=3, etc.
        priority = CATEGORY_PRIORITIES.get(category.id, 5)

        category_progress.append({
            'category_id': category.id,
            'name': category.name,
            'total': total,
            'reviewed': reviewed,
            'completion_pct': round(completion, 1),
            'estimated_remaining_min': round(remaining, 1),
            'confidence': confidence,
            'priority': priority
        })

    # Sort by priority
    category_progress.sort(key=lambda x: x['priority'])

    # Overall statistics
    total_issues = sum(len(c.row_nums) for c in state.categories)
    resolved = sum(1 for row in state.wl_rows if row.action)
    overall_completion = (resolved / total_issues * 100) if total_issues > 0 else 0

    # Time tracking
    session_start = state.session_start_time
    elapsed = (datetime.now() - session_start).total_seconds() / 60

    # Estimate total time based on current velocity
    if resolved > 0 and elapsed > 0:
        time_per_issue = elapsed / resolved
        remaining_issues = total_issues - resolved
        estimated_remaining = remaining_issues * time_per_issue
        estimated_total = elapsed + estimated_remaining
    else:
        estimated_total = 0
        estimated_remaining = 0

    return jsonify({
        'success': True,
        'categories': category_progress,
        'overall': {
            'total_issues': total_issues,
            'resolved': resolved,
            'completion_pct': round(overall_completion, 1),
            'time_elapsed_min': round(elapsed, 1),
            'estimated_remaining_min': round(estimated_remaining, 1),
            'estimated_total_min': round(estimated_total, 1),
            'actions_taken': len(state.undo_stack)
        }
    })

def get_category_avg_time(category_id: str) -> float:
    """Estimate average time per row based on category complexity"""
    # Empirical estimates (seconds per row)
    CATEGORY_TIME_ESTIMATES = {
        'exact_dupes': 10,      # Fast: obvious duplicates
        'networks': 30,          # Medium: verify network membership
        'fuzzy_dupes': 45,       # Slow: careful matching needed
        'yellow_95': 20,         # Fast: high confidence matches
        'yellow_80': 40,         # Medium: verify fuzzy matches
        'yellow_low': 50,        # Slow: manual investigation
        'orphan_no': 60,         # Slow: check against invalid list
        'green_sent': 15,        # Fast: simple status change
        'fuschia_vm': 25,        # Medium: VM counter logic
        'red_invalid': 20,       # Fast: move to invalid
        'not_interested_invalid': 35,  # Medium: verify notes
        'manual_review': 60      # Slow: complex edge cases
    }
    return CATEGORY_TIME_ESTIMATES.get(category_id, 30)

def calculate_category_confidence(category) -> str:
    """Calculate confidence level based on match scores"""
    if not category.row_nums:
        return "high"

    # For categories with match confidence data
    if category.id in ['yellow_95', 'yellow_80', 'fuzzy_dupes']:
        avg_confidence = 0
        count = 0
        for row_num in category.row_nums:
            row = next((r for r in state.wl_rows if r.row_num == row_num), None)
            if row:
                avg_confidence += row.match_confidence
                count += 1

        if count > 0:
            avg_confidence /= count
            if avg_confidence >= 95:
                return "high"
            elif avg_confidence >= 80:
                return "medium"
            else:
                return "low"

    # Default confidence by category type
    CATEGORY_CONFIDENCE = {
        'exact_dupes': 'high',
        'networks': 'high',
        'orphan_no': 'low',
        'manual_review': 'low'
    }
    return CATEGORY_CONFIDENCE.get(category.id, 'medium')
```

**Frontend Implementation:**
```javascript
// Auto-refresh progress dashboard every 30 seconds
let progressInterval;

async function loadProgressDashboard() {
    const response = await fetch('/api/progress/dashboard');
    const data = await response.json();

    if (data.success) {
        renderProgressDashboard(data);
    }
}

function renderProgressDashboard(data) {
    const container = document.getElementById('progress-dashboard');

    // Overall progress bar
    const overall = data.overall;
    const overallHtml = `
        <div class="overall-progress">
            <h3>Overall Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${overall.completion_pct}%">
                    ${overall.completion_pct}%
                </div>
            </div>
            <div class="progress-stats">
                <span>${overall.resolved} / ${overall.total_issues} issues resolved</span>
                <span>⏱️ ${overall.time_elapsed_min.toFixed(1)} min elapsed</span>
                <span>📊 ${overall.estimated_remaining_min.toFixed(1)} min remaining</span>
                <span>🔄 ${overall.actions_taken} actions taken</span>
            </div>
        </div>
    `;

    // Category breakdown
    let categoriesHtml = '<div class="categories-progress">';
    for (const cat of data.categories) {
        const statusIcon = cat.completion_pct === 100 ? '✅' :
                          cat.completion_pct > 0 ? '⚠️' : '⏳';
        const confidenceColor = cat.confidence === 'high' ? 'green' :
                               cat.confidence === 'medium' ? 'orange' : 'red';

        categoriesHtml += `
            <div class="category-progress">
                <div class="category-header">
                    <span class="category-name">${statusIcon} ${cat.name}</span>
                    <span class="category-stats">
                        ${cat.reviewed}/${cat.total}
                        <span class="confidence-badge" style="background: ${confidenceColor}">
                            ${cat.confidence}
                        </span>
                    </span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${cat.completion_pct}%">
                        ${cat.completion_pct}%
                    </div>
                </div>
                <div class="category-estimate">
                    Est. ${cat.estimated_remaining_min.toFixed(1)} min remaining
                </div>
            </div>
        `;
    }
    categoriesHtml += '</div>';

    container.innerHTML = overallHtml + categoriesHtml;
}

// Start auto-refresh
function startProgressTracking() {
    loadProgressDashboard();
    progressInterval = setInterval(loadProgressDashboard, 30000);
}

// Stop on page unload
window.addEventListener('beforeunload', () => {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
});
```

**CSS Styling:**
```css
.overall-progress {
    background: #fff8f0;
    border: 2px solid #e8d5c4;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.progress-bar {
    width: 100%;
    height: 30px;
    background: #f0f0f0;
    border-radius: 15px;
    overflow: hidden;
    margin: 10px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    transition: width 0.5s ease;
}

.progress-stats {
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    color: #666;
}

.category-progress {
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 15px;
    margin-bottom: 10px;
}

.confidence-badge {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    color: white;
    font-weight: bold;
}
```

---

### Google Colab Validation Tool for Route Technicians

**Concept:** Simplified duplicate detection that techs can run before adding rows to WL

**Colab Notebook Structure:**
```python
# Cell 1: Installation & Setup
!pip install pandas rapidfuzz gspread google-auth

from google.colab import auth
from google.auth import default
import gspread
import pandas as pd
from rapidfuzz import fuzz
from IPython.display import HTML, display

# Authenticate with Google
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

print("✅ Setup complete! Ready to validate providers.")

# Cell 2: Configuration (Tech fills this out)
SPREADSHEET_ID = "1z1YC98ALnwu_HLth1gA1RM4U_LsqASaGiTcqY7_dwj0"  # Your WL sheet ID
WORKSHEET_NAME = "Working List - OBGYN"  # Which tab to check against

# Cell 3: Load Existing Working List
print("📥 Loading existing Working List...")
sh = gc.open_by_key(SPREADSHEET_ID)
worksheet = sh.worksheet(WORKSHEET_NAME)
existing_data = worksheet.get_all_records()
existing_df = pd.DataFrame(existing_data)

print(f"✅ Loaded {len(existing_df)} existing providers")
print(f"   Columns: {', '.join(existing_df.columns[:5])}...")

# Cell 4: Upload New Providers to Validate
from google.colab import files

print("📤 Upload your CSV file with new providers to add:")
uploaded = files.upload()

# Load the uploaded file
new_filename = list(uploaded.keys())[0]
new_df = pd.read_csv(new_filename)

print(f"✅ Loaded {len(new_df)} new providers to validate")
print(f"   Columns: {', '.join(new_df.columns)}")

# Cell 5: Validation Logic
def normalize_phone(phone):
    """Normalize phone to (XXX) XXX-XXXX format"""
    if pd.isna(phone):
        return ""
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return str(phone)

def check_duplicates(new_row, existing_df):
    """Check if new row is duplicate/network of existing providers"""
    new_phone = normalize_phone(new_row.get('Phone', ''))
    new_practice = str(new_row.get('Practice Name', ''))
    new_address = str(new_row.get('Address', ''))

    issues = []

    # Check for exact phone match
    phone_matches = existing_df[existing_df['Phone'] == new_phone]

    if len(phone_matches) > 0:
        for _, existing in phone_matches.iterrows():
            # Calculate name similarity
            name_score = fuzz.token_set_ratio(new_practice, existing['Practice Name'])
            address_score = fuzz.ratio(new_address, existing['Address'])

            if name_score >= 95 and address_score >= 95:
                issues.append({
                    'type': 'EXACT DUPLICATE',
                    'severity': 'HIGH',
                    'message': f"Exact match found: {existing['Practice Name']} (Row {existing.get('Row', '?')})",
                    'name_score': name_score,
                    'address_score': address_score
                })
            elif name_score >= 85 and address_score < 70:
                issues.append({
                    'type': 'NETWORK MEMBER',
                    'severity': 'MEDIUM',
                    'message': f"Possible network with: {existing['Practice Name']} (Row {existing.get('Row', '?')})",
                    'name_score': name_score,
                    'address_score': address_score
                })

    # Check for similar name (even without phone match)
    for _, existing in existing_df.iterrows():
        name_score = fuzz.token_set_ratio(new_practice, existing['Practice Name'])
        if name_score >= 90:
            address_score = fuzz.ratio(new_address, existing['Address'])
            if address_score >= 85:
                # High similarity even without phone match
                issues.append({
                    'type': 'FUZZY DUPLICATE',
                    'severity': 'MEDIUM',
                    'message': f"Very similar to: {existing['Practice Name']} (Row {existing.get('Row', '?')})",
                    'name_score': name_score,
                    'address_score': address_score
                })

    return issues

# Cell 6: Run Validation
print("🔍 Validating new providers against existing Working List...\n")

validation_results = []

for idx, row in new_df.iterrows():
    issues = check_duplicates(row, existing_df)

    validation_results.append({
        'row_num': idx + 2,  # Excel row (header = 1)
        'practice': row.get('Practice Name', 'N/A'),
        'phone': normalize_phone(row.get('Phone', '')),
        'issues': issues,
        'status': 'BLOCKED' if any(i['severity'] == 'HIGH' for i in issues) else
                  'WARNING' if len(issues) > 0 else 'OK'
    })

# Cell 7: Display Results with Color Coding
def display_validation_results(results):
    """Display results as styled HTML table"""

    blocked = [r for r in results if r['status'] == 'BLOCKED']
    warnings = [r for r in results if r['status'] == 'WARNING']
    ok = [r for r in results if r['status'] == 'OK']

    print(f"📊 Validation Summary:")
    print(f"   🔴 {len(blocked)} BLOCKED (exact duplicates - DO NOT ADD)")
    print(f"   🟡 {len(warnings)} WARNINGS (possible networks - review carefully)")
    print(f"   🟢 {len(ok)} OK (safe to add)")
    print()

    # Build HTML table
    html = """
    <style>
        .validation-table { border-collapse: collapse; width: 100%; font-family: Arial; }
        .validation-table th { background: #333; color: white; padding: 10px; text-align: left; }
        .validation-table td { padding: 8px; border-bottom: 1px solid #ddd; }
        .status-blocked { background: #ffebee; border-left: 4px solid #f44336; }
        .status-warning { background: #fff8e1; border-left: 4px solid #ff9800; }
        .status-ok { background: #e8f5e9; border-left: 4px solid #4caf50; }
        .issue-high { color: #d32f2f; font-weight: bold; }
        .issue-medium { color: #f57c00; }
    </style>
    <table class="validation-table">
        <tr>
            <th>Row</th>
            <th>Practice Name</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Issues</th>
        </tr>
    """

    for result in results:
        status_class = f"status-{result['status'].lower()}"
        status_icon = {'BLOCKED': '🔴', 'WARNING': '🟡', 'OK': '🟢'}[result['status']]

        issues_html = ""
        for issue in result['issues']:
            severity_class = f"issue-{issue['severity'].lower()}"
            issues_html += f"<div class='{severity_class}'>"
            issues_html += f"<strong>{issue['type']}:</strong> {issue['message']}"
            issues_html += f" (Name: {issue['name_score']}%, Addr: {issue['address_score']}%)"
            issues_html += f"</div>"

        if not issues_html:
            issues_html = "✅ No issues found"

        html += f"""
        <tr class="{status_class}">
            <td>{result['row_num']}</td>
            <td>{result['practice']}</td>
            <td>{result['phone']}</td>
            <td>{status_icon} {result['status']}</td>
            <td>{issues_html}</td>
        </tr>
        """

    html += "</table>"
    display(HTML(html))

display_validation_results(validation_results)

# Cell 8: Export Clean Results
# Filter to only OK rows
clean_rows = [r for r in validation_results if r['status'] == 'OK']
clean_df = new_df.iloc[[r['row_num'] - 2 for r in clean_rows]]

if len(clean_df) > 0:
    print(f"\n✅ {len(clean_df)} providers ready to add to Working List")
    print("📥 Downloading clean CSV...")
    clean_df.to_csv('validated_providers_CLEAN.csv', index=False)
    files.download('validated_providers_CLEAN.csv')
else:
    print("\n⚠️ No clean providers to export (all have issues)")

# Cell 9: Instructions for Technician
print("""
🎯 NEXT STEPS FOR TECHNICIAN:

1. Review the table above:
   - 🔴 BLOCKED rows: DO NOT ADD (exact duplicates already in WL)
   - 🟡 WARNING rows: Check carefully - might be network or similar provider
   - 🟢 OK rows: Safe to add

2. If you downloaded 'validated_providers_CLEAN.csv':
   - Open the file
   - Copy the rows
   - Paste into Working List spreadsheet

3. For WARNING rows:
   - Ask engineer to review before adding
   - Include row numbers in your message

4. For BLOCKED rows:
   - Mark as "Already in database" in your tracking sheet
   - Do NOT add to Working List
""")
```

**Key Features:**
- ✅ No technical knowledge required (just upload CSV)
- ✅ Clear visual feedback (red/yellow/green)
- ✅ Explains WHY each row is flagged
- ✅ Shows match scores for transparency
- ✅ Exports only clean rows for import
- ✅ Normalizes phone numbers automatically
- ✅ Checks both exact duplicates and networks
- ✅ Works with any spreadsheet (just change ID)

**Usage for Technicians:**
1. Open Colab notebook (shared link)
2. Click "Runtime" → "Run all"
3. Authenticate with Google (one-time)
4. Upload CSV with new providers
5. Review colored table
6. Download clean CSV if any rows pass
7. Report warnings to engineer

---

### Real-Time Duplicate Detection Architecture

**Option A: Google Apps Script Add-On (Runs on Sheet Edit)**

```javascript
// Trigger: onEdit(e)
function checkDuplicateOnEdit(e) {
    const sheet = e.source.getActiveSheet();
    const range = e.range;
    const row = range.getRow();

    // Only check Working List sheet
    if (sheet.getName() !== "Working List - OBGYN") return;

    // Only check if editing Practice Name, Phone, or Address columns
    const col = range.getColumn();
    const PRACTICE_COL = 2;  // Column B
    const PHONE_COL = 3;     // Column C
    const ADDRESS_COL = 4;   // Column D

    if (![PRACTICE_COL, PHONE_COL, ADDRESS_COL].includes(col)) return;

    // Get data from current row
    const rowData = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
    const practice = rowData[PRACTICE_COL - 1];
    const phone = rowData[PHONE_COL - 1];
    const address = rowData[ADDRESS_COL - 1];

    // Check against all OTHER rows
    const allData = sheet.getDataRange().getValues();

    let duplicates = [];
    let networks = [];

    for (let i = 1; i < allData.length; i++) {  // Skip header
        if (i + 1 === row) continue;  // Skip self

        const existingPhone = allData[i][PHONE_COL - 1];
        const existingPractice = allData[i][PRACTICE_COL - 1];
        const existingAddress = allData[i][ADDRESS_COL - 1];

        // Exact phone match
        if (normalizePhone(phone) === normalizePhone(existingPhone)) {
            const nameSim = calculateSimilarity(practice, existingPractice);
            const addrSim = calculateSimilarity(address, existingAddress);

            if (nameSim > 0.95 && addrSim > 0.95) {
                duplicates.push({row: i + 1, practice: existingPractice});
            } else if (nameSim > 0.85 && addrSim < 0.70) {
                networks.push({row: i + 1, practice: existingPractice});
            }
        }
    }

    // Show warning if duplicates found
    if (duplicates.length > 0) {
        const ui = SpreadsheetApp.getUi();
        const msg = `⚠️ DUPLICATE DETECTED!\n\n` +
                    `This provider appears to already exist:\n` +
                    duplicates.map(d => `Row ${d.row}: ${d.practice}`).join('\n') +
                    `\n\nDo you want to keep this entry?`;

        const response = ui.alert('Duplicate Found', msg, ui.ButtonSet.YES_NO);

        if (response === ui.Button.NO) {
            // Delete the row
            sheet.deleteRow(row);
            ui.alert('Row deleted', 'Duplicate row has been removed.', ui.ButtonSet.OK);
        } else {
            // Highlight in yellow
            range.setBackground('#fff59d');
        }
    } else if (networks.length > 0) {
        const ui = SpreadsheetApp.getUi();
        const msg = `💡 POSSIBLE NETWORK DETECTED\n\n` +
                    `This provider might belong to a network:\n` +
                    networks.map(n => `Row ${n.row}: ${n.practice}`).join('\n') +
                    `\n\nShould I add network notation?`;

        const response = ui.alert('Network Suggestion', msg, ui.ButtonSet.YES_NO);

        if (response === ui.Button.YES) {
            // Add network notation to notes
            const notesCol = 10;  // Adjust based on your sheet
            const currentNotes = sheet.getRange(row, notesCol).getValue();
            const networkName = extractCommonWords(practice, networks[0].practice);
            sheet.getRange(row, notesCol).setValue(`${networkName} network (~${networks.length + 1}); ${currentNotes}`);
        }
    }
}

function normalizePhone(phone) {
    return String(phone).replace(/\D/g, '');
}

function calculateSimilarity(str1, str2) {
    // Simple Jaccard similarity (can upgrade to Levenshtein)
    const set1 = new Set(str1.toLowerCase().split(/\s+/));
    const set2 = new Set(str2.toLowerCase().split(/\s+/));
    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([...set1, ...set2]);
    return intersection.size / union.size;
}
```

**Option B: Pre-Import Validation (Colab Tool - Described Above)**

**Option C: Daily Validation Report (Email to Engineer)**

```python
# Cloud Function or GitHub Action (runs daily)
def send_daily_validation_report():
    """Email engineer with flagged duplicates/networks added today"""

    # Load WL data
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet("Working List - OBGYN")
    data = worksheet.get_all_records()

    # Filter to rows added today (check timestamp column)
    today = datetime.now().date()
    new_rows = [r for r in data if parse_date(r.get('Date Added')) == today]

    if not new_rows:
        return  # No new rows, skip email

    # Check each new row for duplicates
    issues = []
    for row in new_rows:
        dupes = check_duplicates(row, data)
        if dupes:
            issues.append({'row': row, 'duplicates': dupes})

    if not issues:
        return  # No issues, skip email

    # Send email
    send_email(
        to="engineer@jgdc.org",
        subject=f"⚠️ Daily WL Validation: {len(issues)} potential duplicates found",
        body=format_validation_email(issues)
    )
```

---

## 🟠 HIGH PRIORITY (After OBGYN Reset)

### 2. PECOS Cross-Reference Integration

**Goal:** Reduce closed/inactive providers by 40%, increase call success rate from 25% to 35-40%

- [ ] **Build PECOS cross-reference script** (`scripts/pecos_cross_reference.py`)
  - **Input:** NPPES filtered CSV (e.g., `FILTERED_PCP_TX_2024.csv`)
  - **Process:**
    - Query CMS PECOS API by NPI
    - Keep only Medicare-enrolled providers (active enrollment)
    - Filter out closed/inactive providers automatically
  - **Output:** PECOS-verified CSV (e.g., `FILTERED_PCP_TX_2024_PECOS.csv`)
  - **Benefits:**
    - FREE (PECOS API is free, unlimited)
    - Eliminates 40-50% of closed providers
    - More current than NPPES (revalidates every 5 years)
    - Specialty info more accurate
  - **Time:** 2-3 hours to build, instant to run

- [ ] **Test PECOS filtering on recent NPPES export**
  - Run on 1000 TX providers
  - Measure: How many filtered out? (expect ~400-500 remaining)
  - Manual spot check: Are filtered providers actually closed?
  - Measure call success rate improvement

- [ ] **Optional: Add Twilio phone validation** (if PECOS alone insufficient)
  - Cost: $0.005 per phone = $5 per 1000 providers
  - Validates phone number exists and is reachable
  - Further reduces closed providers
  - Decision: Run after PECOS test to see if needed

### 3. Provider Filtering Improvements

**From `docs/FILTERING_IMPROVEMENTS_BRAINSTORM.md`:**

- [ ] **Expand organization blacklist** (nppes_filter_pcps.py)
  - Add: dermatology, dental, veterinary, chiropractic, etc.
  - Test on recent NPPES export
  - Measure over-filtering rate

- [ ] **Secondary taxonomy code check**
  - NPPES has up to 15 taxonomy codes per provider
  - Check if ANY code indicates specialist (not just primary)
  - Catches multi-specialty groups

### 4. Documentation & Testing

- [ ] **Create test data generator** (`scripts/test_data_generator.py`)
  - Generate 150-200 realistic EOY test cases
  - All edge cases: perfect matches, fuzzy matches, duplicates, status issues
  - Upload to "EOY Test - PCP" sheet once
  - Use for fast iteration during development

- [ ] **Document local Python workflow**
  - When to use Apps Script vs Python
  - gspread setup guide
  - EOY tool usage guide
  - PECOS integration guide

---

## 🟡 MEDIUM PRIORITY (This Month)

### Code Quality

- [ ] **Test capitalization fixes across both sheets**
  - Verify Mc/Mac names work
  - Test credential standardization (MD, DO, etc.)
  - Check apostrophe handling (O'Donnell)
  - Confirm mixed case suffixes (Jr, Sr)

- [ ] **Add error handling to EOY automation**
  - Graceful failures if columns missing
  - Better error messages for users
  - Rollback option if automation fails mid-process

- [ ] **Consolidation function improvements**
  - The current consolidation logic is complex
  - Add dry-run preview mode
  - Better conflict resolution UI
  - Test with multiple data sources

### User Experience

- [ ] **Improve duplicate detection accuracy**
  - Fuzzy matching for office names (optional)
  - Address normalization (Suite vs Ste)
  - Phone number format variations
  - Consider name similarity scoring

- [ ] **Better status-based review workflow**
  - Create actionable checklists for each status type
  - Add quick-action buttons (move to invalid list, etc.)
  - Track review progress

---

## 🟢 LOW PRIORITY (Future Enhancements)

### Automation Gaps

- [ ] **CSV import automation**
  - Auto-create properly named sheets
  - Map columns automatically
  - Validate data on import

- [ ] **Annual re-verification scheduler**
  - Mark providers needing re-verification
  - Batch re-verification process
  - Update verification dates

### Features

- [ ] **Enhanced search functionality**
  - Search across all sheets
  - Find provider by phone/name/city
  - "Where is this provider?" tool

- [ ] **Reporting & Analytics**
  - Success rate by state
  - Call efficiency metrics
  - Year-over-year comparison
  - Export board reports

### Technical Debt

- [ ] **Standardize sheet naming conventions**
  - Document naming rules
  - Update hardcoded references
  - Create config file for sheet names

- [ ] **Optimize performance**
  - Batch API calls more efficiently
  - Reduce sheet read/write operations
  - Cache frequently accessed data

---

## ✅ RECENTLY COMPLETED (This Session)

### Previous Session:
- [x] Updated Python config for OBGYN filtering (TX, WA, CO, PA)
- [x] Changed OUTPUT_PREFIX to 'FILTERED_obgyns'
- [x] Added centralized API usage tracker (3000 limit)
- [x] Added pre-flight safety check before verification starts
- [x] Added in-flight safety check during batch processing
- [x] Enhanced showApiUsage() with limit status and percentages
- [x] Built EOY automation suite (6 validation steps) - ⚠️ found bugs, see section 0
  - Yellow → New Orders validation (❌ BROKEN - phone not in New Orders)
  - Not Interested rule enforcement (✅ works)
  - Duplicate detection (⚠️ works but network notation format wrong)
  - Status-based review (✅ works)
  - Hidden Debug/Issues column creation (✅ works)
- [x] Added EOY workflow menu to Misc. Tools
- [x] Pushed all changes to Google Sheets via clasp
- [x] Verified OBGYN taxonomy codes in filter script

### Current Session (Bug Fixes):
- [x] Audited codebase for half-implemented features
- [x] Fixed DebugRepairSidebar field name mismatches
- [x] Added detailed TODO section for remaining bugs
- [x] Pushed DebugRepairSidebar fixes to both OBGYN and PCP sheets

---

## 📋 MAINTENANCE TASKS

### Regular (Monthly)
- [ ] Check for specialist contamination in new imports
- [ ] Review API usage trends
- [ ] Validate STATS tab accuracy

### Quarterly
- [ ] Update NPPES data (download from CMS)
- [ ] Re-verify closed/inactive providers
- [ ] Clean up Invalid/Inactive List

### Annually
- [ ] Run full EOY workflow
- [ ] Archive old year sheets
- [ ] Update year references in code
- [ ] Review and optimize entire workflow

---

## 🔬 RESEARCH & EXPLORATION

- [ ] **Explore OBGYN-specific filtering needs**
  - Are there OBGYN specialists we should exclude? (e.g., maternal-fetal medicine)
  - Should we include OB/GYN nurse practitioners?
  - Geographic concentration differences vs PCP

- [ ] **Better duplicate detection algorithms**
  - Levenshtein distance for name matching
  - Address parsing libraries
  - Phone number similarity scoring

- [ ] **EOY automation phase 2**
  - Sheet duplication with OLD prefix
  - Formula updates in STATS tab
  - IMPORTRANGE link updates
  - Complexity: Very High

---

## 📝 NOTES & DECISIONS

### Python Setup
- **Pandas required:** Script will fail without pandas installed
- **Installation:** `pip install pandas` (or `pip3` on some systems)
- **Testing:** Always run with `DRY_RUN = True` first

### API Limits
- **Free tier:** 3000 Places API calls per month
- **Current buffer:** 200-call safety margin (warning at 2800)
- **Actual usage:** Counter persists in ScriptProperties across sessions
- **Reset:** Manual via "API Usage" menu item

### EOY Workflow Philosophy
- **Flag, don't fix:** Most issues are flagged for manual review
- **Exception:** "Not interested" rules are auto-fixed (low risk)
- **Hidden column:** Debug/Issues column is auto-hidden to avoid clutter
- **Dry-run first:** All functions support dry-run mode for safety

### OBGYN vs PCP Differences
- **Taxonomy codes:** OBGYN uses 207V* codes
- **Provider density:** OBGYNs are less common than PCPs
- **Filtering ratio:** May need different input:output ratio
- **Organization handling:** Same rules apply (independent clinics only)

---

## 🎯 SUCCESS METRICS

### This Campaign (OBGYN 2025)
- [ ] 200 verified OBGYNs in TX
- [ ] 40 verified OBGYNs each in WA, CO, PA
- [ ] Total API calls < 3000
- [ ] Zero duplicate orders shipped
- [ ] Clean EOY transition with no data loss

### Long-term
- Reduce manual EOY work by 80%
- Zero formatting errors in consolidated data
- < 5% duplicate rate across all sheets
- 100% of yellow rows accounted for in New Orders

---

## 🚨 KNOWN ISSUES & RISKS

### Critical (Must Fix Now)
- **EOY Step 2 broken:** Uses phone matching but phone not in New Orders sheet
- **EOY Step 1 incomplete:** Doesn't populate Debug column, only shows alert
- **Network notation wrong format:** Uses generic text instead of "network-name network (~8);"

### High Risk
- **Pandas not installed:** BLOCKING Python script execution
- **Messy copy-pastes in New Orders:** Yellow validation will find many issues (once Step 2 fixed)
- **OBGYN sheet not connected to ToolboxSuite:** EOY automation won't work until connected

### Medium Risk
- **Missing filter view functions:** `showDebugFilter()`, `clearDebugFilter()`, `showColorFilter()` not implemented
- **Edge cases in "not interested" logic:** Need to test variations in Notes column
- **Duplicate detection false positives:** Phone number formatting variations
- **Status-based review complexity:** Many edge cases to handle

### Low Risk
- **API limit exceeded:** Unlikely with current safeguards (3000 limit, 465 expected usage)
- **Unused validation menu stubs:** Don't break anything but clutter the menu

---

## 💡 IDEAS FOR FUTURE

- Video tutorials for volunteers
- Automated backups before major changes
- Dashboard showing campaign progress
- Integration with dialer software
- Machine learning for predicting "not interested"
- Zapier/Make.com automation for some steps
