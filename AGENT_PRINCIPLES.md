# AI Agent Principles - Anti-Spaghettification Rules

**Last Modified:** 2025-11-17

## Source of Truth Hierarchy

1. **User's direct instructions** (highest priority - overrides everything)
2. **Code that user confirms works** ("this is tested", "this works")
3. **Recent git commits** (check `git log --oneline -10`)
4. **Files with recent "Last Modified" dates** (check top of file)
5. **Old documentation** (lowest priority - verify before trusting)

**Rule:** When in doubt, ask the user. Docs are for LLMs, not humans - user may not have read them.

---

## Critical: LLMs Are Time-Blind

**NEVER trust your sense of dates!** LLMs have a knowledge cutoff and cannot know the current date.

**Before flagging any date as "future" or "past":**
```bash
date  # Check system date FIRST
```

**Example of failure:**
- LLM thinks it's 2024
- Flags "October 2025" as future date
- System date is actually November 2025
- "October 2025" is 1 month ago (CORRECT)

**Always check:**
- System date with `date` command
- Git commit dates with `git log --oneline -10`
- File "Last Modified" headers

---

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

### 5. Trust Nothing - All Code is Unverified Until Proven
**Symptom:** Assuming code in repo is functional and complete

**Reality:**
- Code may be half-implemented stubs (compiles but doesn't work)
- Functions may exist but have never been tested
- Documentation may describe ideal state, not current reality
- Previous AI sessions may have created broken implementations

**Fix:**
- **ALWAYS treat code as incomplete** unless:
  - User explicitly says "this works" or "this is tested"
  - You test it yourself and it works
  - Recent git commit message says it's verified/working
- **Use existing code as reference**, not truth
  - Read it to understand intent
  - Don't copy/paste without verifying logic
  - Check for TODOs, stubs, placeholder logic
- **When writing new code:**
  - Don't assume helper functions work (test them)
  - Don't trust variable names match reality (check actual data)
  - Don't assume error handling exists (it probably doesn't)
- **Red flags that code is untested:**
  - No error handling
  - Generic variable names (data, result, items)
  - TODOs or comments like "fix this later"
  - Function exists but isn't called anywhere

## Architectural Invariants

### Where Truth Lives
- **Column positions:** ToolboxSuite.js `statusColumn` variable (currently column 10 = "CALL STATUS", column 11 = "Notes")
- **Color mappings:** ToolboxSuite.js `onEdit()` function (never change hex codes)
- **System Properties:** scripts/provider-search/UniversalProviderSuite.js (grep for PropertiesService)
- **Current state:** TODO.md section 0 (Critical Bugs) and `git log --oneline -10`

### Never Do This
- ❌ Code directly in Google Sheets (always local + clasp push)
- ❌ Move Column J (column 10 = CALL STATUS - breaks onEdit trigger everywhere)
- ❌ Change semicolon separator in Notes column (column 11 - breaks note parsing/merging)
- ❌ Use sheet-wide filters (breaks multi-user editing)
- ❌ Edit production without backup
- ❌ Hard-code line numbers or column numbers in docs (use variable/function names instead)

### Always Do This
- ✅ Check git status before starting
- ✅ Read TODO.md section 0 (Critical Bugs) first
- ✅ `clasp pull` before editing Apps Script files (.js/.html in scripts/*/`)
- ✅ When changing ToolboxSuite.js: Don't assume it works on both OBGYN and PCP sheets without user testing
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

**"The docs say X"** → Check "Last Modified" date at top of file. Old docs may be outdated. Trust recent commits over old docs.

**"I'll document this after"** → No. Update docs in same commit as code.

**"User mentioned Y in passing"** → Don't enshrine it in docs unless they explicitly confirm.

## Before Every Session

```bash
git status              # What's uncommitted?
git log --oneline -10   # Recent context?
cat TODO.md | head -50  # Current priorities?
ls -la *.md | head -20  # What docs exist? Check Last Modified dates
```

Read TODO.md section 0 (Critical Bugs) - it tells you what's actually broken right now.

**Session startup checklist:**
1. Check git status - any uncommitted changes?
2. Scan recent commits to understand what was done last
3. Read TODO.md section 0 to know current blockers
4. Check which markdown docs exist and when they were last modified
5. Ask user what they want to work on (don't assume based on docs)

## Code Sync Rules

**Source of truth:** Local files in git
**Deployment target:** Google Sheets via clasp
**Never:** Edit in Sheets web UI (creates conflicts with local files)

**Shared code (must stay identical):**
- scripts/obgyn-list/ToolboxSuite.js
- scripts/pcp-list/ToolboxSuite.js
- scripts/obgyn-list/DebugRepairSidebar.html
- scripts/pcp-list/DebugRepairSidebar.html

**Verification:** If unsure whether files are still identical, check the code yourself (grep for functions or compare key sections)

## File Hierarchy (No Duplication)

**Purpose → File mapping:**
- Current bugs/tasks → TODO.md
- System overview → MASTER_SYSTEM_DOCUMENTATION.md (verify if current)
- File locations → STRUCTURE.md (verify if current)
- Procedures → docs/OBGYN_CLEANUP_CHECKLIST_DEPRECATED.md (deprecated - check for newer version)
- Setup → docs/CLASP_SETUP.md (verify if current)
- This file → Meta-rules for AI agents

**If adding info:** Check if it belongs in existing file first. Don't duplicate.

---

**TL;DR:** Read TODO.md first. Don't finish broken implementations. Delete deprecated info (archive old files if not wrong). Test on both sheets. Update docs in same commit. Check git status. User is source of truth.
