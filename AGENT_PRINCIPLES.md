# AI Agent Principles - Anti-Spaghettification Rules

## Context Window Failure Modes

### 1. The Stub Problem
**Symptom:** Mid-implementation you realize plan is incomplete, but finish anyway with `// TODO: implement this`

**Fix:**
- STOP immediately when plan breaks
- Update TODO.md with blocker
- Ask user for direction
- Don't create incomplete functions that compile but don't work

### 2. Documentation Pollution
**Symptom:** Treating off-hand user comments as canonical truth, or failing to update docs when code changes

**Fix:**
- User's direct edits to docs = canonical
- User's chat messages = clarification only
- When code changes, update docs in same commit
- Delete deprecated info immediately (don't let it linger)

### 3. Solving Already-Solved Problems
**Symptom:** Creating new fuzzy matching function when one exists in line 850

**Fix:**
- Read TODO.md FIRST (it tells you what's actually broken)
- Grep before creating ("does this already exist?")
- Check "Recently Completed" in TODO.md (recent solutions)
- If file >500 lines, read methodically (don't skim)

### 4. Deprecated Info Kills You
**Symptom:** Following outdated patterns from archived code or old docs

**Fix:**
- Delete deprecated code (don't comment it out)
- Move old docs to archive/ with date stamps
- When you spot stale TODO items, remove them
- Check git log to see if "solution" was already tried and reverted

## Architectural Invariants

### Where Truth Lives
- **Column positions:** ToolboxSuite.js lines 160-165 (hardcoded, fragile)
- **Color mappings:** ToolboxSuite.js onEdit() function (never change hex codes)
- **System Properties:** scripts/provider-search/UniversalProviderSuite.js (grep for PropertiesService)
- **Current state:** TODO.md section 0 (Critical Bugs) and git log --oneline -10

### Never Do This
- ❌ Code directly in Google Sheets (always local + clasp push)
- ❌ Move Column J (breaks onEdit trigger everywhere)
- ❌ Change semicolon separator in Notes (breaks parsing)
- ❌ Use sheet-wide filters (breaks multi-user editing)
- ❌ Edit production without backup
- ❌ Create files without checking STRUCTURE.md first

### Always Do This
- ✅ Check git status before starting
- ✅ Read TODO.md section 0 (Critical Bugs) first
- ✅ clasp pull before editing Scripts
- ✅ Test on both OBGYN and PCP when changing ToolboxSuite.js
- ✅ Update TODO.md as you discover tasks (not batch at end)

## Decision Heuristics

**When to ask vs. proceed:**
- Config values unclear? → ASK (don't guess)
- Bug found mid-implementation? → STOP, update TODO, ASK
- Code exists but seems wrong? → Ask before rewriting
- Multiple approaches work? → Document tradeoffs, ASK

**When to refactor vs. add:**
- Function doing 90% of what you need? → Refactor it
- Seeing 3rd copy of same logic? → Extract to shared function
- Dead code found? → Delete it (don't leave it)

**Test coverage:**
- New algorithm (fuzzy matching)? → Unit test first
- Changing EOY automation? → Test sheet with sample data
- Final validation? → Backup + production

## Common Traps

**"I'll clean this up later"** → You won't. Clean now.

**"This is just a quick fix"** → If it touches onEdit or verification, it's not quick. Test both sheets.

**"The docs say X"** → Check git blame. Is that doc 6 months old? Trust recent commits over old docs.

**"I'll document this after"** → No. Update docs in same commit as code.

**"User mentioned Y in passing"** → Don't enshrine it in docs unless they explicitly confirm.

## Before Every Session

```bash
git status              # What's uncommitted?
git log --oneline -10   # Recent context?
cat TODO.md | head -50  # Current priorities?
```

Read TODO.md section 0 (Critical Bugs) - it tells you what's actually broken right now.

## Code Sync Rules

**Source of truth:** Local files in git
**Deployment target:** Google Sheets via clasp
**Never:** Edit in Sheets web UI (breaks sync)

**Shared code (must stay identical):**
- scripts/obgyn-list/ToolboxSuite.js
- scripts/pcp-list/ToolboxSuite.js
- scripts/obgyn-list/DebugRepairSidebar.html
- scripts/pcp-list/DebugRepairSidebar.html

**Process:** Edit OBGYN → test → cp to PCP → test both → commit

## File Hierarchy (No Duplication)

**Purpose → File mapping:**
- Current bugs/tasks → TODO.md
- System overview → MASTER_SYSTEM_DOCUMENTATION.md
- File locations → STRUCTURE.md
- Procedures → OBGYN_CLEANUP_CHECKLIST.md
- Setup → docs/CLASP_SETUP.md
- This file → Meta-rules for AI agents

**If adding info:** Check if it belongs in existing file first. Don't duplicate.

---

**TL;DR:** Read TODO.md first. Don't finish broken implementations. Delete deprecated stuff. Test on both sheets. Update docs in same commit. Check git status.
