---
name: documentation-sync
description: Keep README.md and inline code comments in sync with recent changes to project structure and codebase capabilities. Scans for new modules, functions, and structural changes, then automatically applies edits to documentation to reflect current reality.
---

# Documentation Sync

Keep documentation accurate as code evolves.

## When to Use

Run this skill after:
- Adding or restructuring modules in `src/` or `models/`
- Changing project architecture or data flow
- Adding significant new functions or classes
- Refactoring existing code
- Changing environment or configuration requirements

Explicitly invoke when you want to audit and refresh documentation.

## What It Does

1. **Scans recent code changes** — Identifies new files, deleted files, moved modules, and structural changes
2. **Compares against README.md** — Checks if the project structure documentation matches reality
3. **Detects capability changes** — Notes new analysis capabilities or data processing steps
4. **Applies targeted edits** — Updates README.md and inline comments automatically to reflect current state
5. **Confirms changes** — Reports what was updated

## Workflow

### Step 1: Identify Changes
Run git commands to detect:
- New files in `src/`, `models/`, `data/`, `tests/`
- Deleted or moved files
- Modified structure or imports

### Step 2: Audit Documentation
Check [README.md](../../../README.md) for these sections:
- Project overview and purpose
- Project structure
- Data flow and pipeline
- Key capabilities and features
- Setup and requirements

### Step 3: Apply Edits
For each discrepancy found:
- Update README.md directly with corrected documentation
- Update inline code comments if they contradict current behavior
- Preserve all intentional changes

### Step 4: Confirm Changes
Report which sections were updated and why

## Output

After running the skill, you'll see a summary like:

```
✅ Updated README.md
  - Project Structure: Added helpers/ module and data_processing functions
  - Pipeline: Expanded with filter_jumpball_data.py and player_data.py details
  
2 sections updated, 0 conflicts detected
```

## Constraints & Safety

- **Conservative scope**: Only update Project Structure and Pipeline sections; don't modify other README content unless discrepancies are clear
- **Single source of truth**: README is canonical; align code to docs when appropriate, update docs when code changes are intentional
- **Comments in code**: Preserve existing code comments; only update when they contradict current behavior
- **No breaking changes**: If a structural change breaks downstream, log it for awareness but still update docs to reflect reality

## How to Invoke

From the chat:
```
Use my documentation-sync skill to update README and comments with recent changes
```

The skill will:
- Scan for new/deleted/moved files in `src/`, `models/`, `data/`, `tests/`
- Identify discrepancies between code structure and README.md
- Apply fixes directly to README.md
- Report what was updated and why

## See Also

- [README.md](../../../README.md) — Canonical project documentation
- [AGENTS.md](../../../AGENTS.md) — Requirement: "Documentation is Canonical"
