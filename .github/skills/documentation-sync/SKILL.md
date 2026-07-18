---
name: documentation-sync
description: Keep README.md and inline code comments in sync with recent changes to project structure and codebase capabilities. Scans for new modules, functions, and structural changes, then suggests edits to documentation to reflect current reality.
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
4. **Suggests targeted edits** — Proposes specific updates to README.md and inline comments that fell out of sync
5. **Presents for review** — Shows suggested changes so you can approve before applying

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

### Step 3: Suggest Edits
For each discrepancy found, propose:
- **What's wrong**: Brief description of the mismatch
- **Where**: Specific file and line range (if applicable)
- **Suggested fix**: The exact text change with context

### Step 4: User Review & Apply
Present all suggestions in a structured format so you can:
- Accept individual changes
- Request revisions
- Understand the reasoning for each change

## Output Format

Suggestions appear as a structured review with sections like:

```
## Documentation Update Report

### Changed: Project Structure
**Issue**: src/ folder has new data_processing module not documented

**Location**: README.md#L25-L35 (Project Structure section)

**Current text**:
```
src/
├── models/
└── utils/
```

**Suggested text**:
```
src/
├── data_processing/
│   └── __init__.py
├── models/
└── utils/
```

**Reasoning**: New data_processing module added for pipeline stages

---
```

## Constraints & Safety

- **Approval required**: All changes are suggestions only; you review before applying
- **Single source of truth**: README is canonical; align code to docs when appropriate, update docs when code changes are intentional
- **Comments in code**: Preserve existing code comments; only update when they contradict current behavior
- **No breaking changes**: If a structural change breaks downstream, flag it for discussion

## How to Invoke

From the chat:
```
Use my documentation-sync skill to check if README and comments are current
```

Or programmatically:
```bash
# Review changes since last sync
git log --name-status --oneline HEAD~10..HEAD | grep "^A\|^M\|^D"

# Then run the skill to analyze and suggest updates
```

## See Also

- [README.md](../../../README.md) — Canonical project documentation
- [AGENTS.md](../../../AGENTS.md) — Requirement: "Documentation is Canonical"
