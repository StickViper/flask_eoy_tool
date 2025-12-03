# Notes Pattern Analysis Workflow

## Overview

This workflow enables **data-driven pattern recognition** for notes fields with **human-in-the-loop LLM categorization**.

Instead of hardcoding assumptions about what notes mean, we:
1. Extract real patterns from actual data
2. Use LLM (Claude/GPT) to categorize intelligently
3. Associate specific actions with each pattern type
4. Apply patterns during validation and cleanup

## Workflow Steps

### 1. Extract Note Patterns

**Endpoint:** `/api/analyze_notes`

```bash
curl http://localhost:5000/api/analyze_notes
```

Returns JSON with:
- All unique note chunks (semicolon-separated)
- Frequency count for each chunk
- Percentage of total rows
- Example row numbers

### 2. Download for Analysis

**Endpoint:** `/api/download_notes_csv`

```bash
curl http://localhost:5000/api/download_notes_csv -o notes_analysis.csv
```

Exports CSV with columns:
- `chunk` - The note text
- `count` - How many times it appears
- `pct` - Percentage of all rows
- `example_rows` - Row numbers (first 3)

### 3. Categorize with LLM

**Manual Step:** Review CSV with Claude or GPT

Example prompt:
```
I've extracted all note chunks from a provider database.
Please categorize these into types based on their semantic meaning:

- PHONE_CONTEXT: VM counts, call attempts
- STATUS_UPDATES: "sent", "mailed", delivery tracking
- NETWORK_NOTATION: Network membership indicators
- PROVIDER_STATUS: Retired, closed, moved
- DATA_QUALITY: Bad address, wrong number
- OTHER: Describe new categories

For each chunk, suggest:
- Which category it belongs to
- Whether notes should be PRESERVED, FLAG_REVIEW, or SAFE_TO_MODIFY
- Which actions make sense (add_vm_note, remove_sent, merge_rows, etc.)
```

### 4. Update Configuration

**File:** `config/notes_patterns.json`

Add categorized patterns:

```json
{
  "phone_context": {
    "description": "Tech-added phone call tracking",
    "action": "PRESERVE",
    "suggested_actions": ["add_vm_note", "mark_not_found"],
    "patterns": [
      "vm x2",
      "vm x3",
      "spoke with",
      "left message",
      "no answer"
    ]
  }
}
```

**Actions:**
- `PRESERVE` - Never auto-modify these notes
- `FLAG_REVIEW` - Highlight for manual review
- `SAFE_TO_MODIFY` - Can be changed/removed safely

**Suggested Actions:**
- `add_vm_note` - Increment VM counter
- `remove_sent` - Remove "sent" indicators
- `change_status` - Update status field
- `merge_rows` - Combine network members
- `mass_invalid` - Mark network as invalid
- `mark_not_found` - Add "not found in new orders"
- `change_to_white` - Reset to "Not Interested"
- `send_to_manual_review` - Flag for human review

### 5. Use in Validation

**Class:** `NotesValidator`

```python
from eoy_tool import notes_validator

# Categorize a single note chunk
result = notes_validator.get_note_category("vm x3")
# Returns: {
#   'category': 'phone_context',
#   'action': 'PRESERVE',
#   'suggested_actions': ['add_vm_note', 'mark_not_found'],
#   'description': 'Tech-added phone call tracking'
# }

# Categorize all chunks in notes field
notes = "vm x2; sent 1/15; network (~3)"
results = notes_validator.categorize_notes(notes)
# Returns list of categorized chunks

# Check if notes should be preserved
should_preserve, reason = notes_validator.should_preserve_notes(notes)
# Returns: (True, "Contains phone_context: vm x2")
```

## Example Usage in Actions

### Before Auto-Modifying Notes:
```python
@app.route('/api/remove_sent', methods=['POST'])
def api_remove_sent():
    """Remove 'sent' from notes - but check for protected patterns first"""

    for row in selected_rows:
        # Check if notes should be preserved
        should_preserve, reason = notes_validator.should_preserve_notes(row.notes)

        if should_preserve:
            # Skip this row or flag for manual review
            continue

        # Safe to modify - categorized as STATUS_UPDATES
        row.notes = row.notes.replace('sent', '').strip('; ')
```

### Suggesting Actions Based on Patterns:
```python
# When displaying notes, show suggested actions
categorized = notes_validator.categorize_notes(row.notes)

for item in categorized:
    print(f"Note: {item['chunk']}")
    print(f"Category: {item['category']}")
    print(f"Suggested actions: {', '.join(item['suggested_actions'])}")
```

## Benefits

✅ **Data-driven** - Patterns based on real data, not assumptions
✅ **Human oversight** - LLM categorization ensures accuracy
✅ **Configurable** - Easy to update patterns as data evolves
✅ **Actionable** - Each pattern type has specific suggested actions
✅ **Safe** - Prevents accidental deletion of important tech notes

## Next Steps

1. Run analysis on real data once Sheets access is working
2. Export top 200 unique chunks
3. Categorize with Claude/GPT
4. Update `notes_patterns.json` with real categories
5. Test validation during cleanup actions
