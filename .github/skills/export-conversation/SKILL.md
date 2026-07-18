---
name: export-conversation
description: Export and preserve Copilot conversations with structured metadata. Each conversation is labeled with timestamp, git branch, and a concise 1-2 word summary, enabling easy retrieval and reference to past work.
---

# Export Conversation

Preserve development conversations for future reference and continuity.

## When to Use

Invoke this skill when:
- You complete a significant conversation that should be referenced later
- You resolve a complex problem and want to preserve the solution process
- You reach a milestone (new feature, bug fix, refactor, architecture decision)
- You want to document context for future team members or your future self
- You're wrapping up a feature branch with important decisions made during development

## What It Does

1. **Captures the conversation** — Saves the full chat transcript from the current Copilot session
2. **Extracts metadata** — Automatically determines git branch and current timestamp
3. **Adds a summary** — Prompts for a 1-2 word summary that describes the conversation purpose
4. **Creates a labeled file** — Saves with filename format: `{YYYY-MM-DD}_{HHMMSS}_{SUMMARY}_{BRANCH}.md`
5. **Stores in copilot-conversations/** — Places the file in the repo's conversation archive

## Metadata Format

Each exported conversation includes:

```
**Date**: YYYY-MM-DD HH:MM:SS (UTC)
**Branch**: branch-name
**Summary**: keyword-one keyword-two
```

This header appears at the top of every exported file, making it easy to scan and filter saved conversations.

## Workflow

### Step 1: Request Export
Ask to export the conversation when you want to preserve work. Example prompts:
- "Export this conversation as 'feature-auth'"
- "Save this as 'bug-fix' to copilot-conversations"
- "Export with summary 'debugging pipeline'"

### Step 2: Confirm Metadata
The skill will:
- Generate a timestamp (used as the primary sort key in filename)
- Detect the current git branch (using `git rev-parse --abbrev-ref HEAD`)
- Show the proposed filename for your confirmation

If you want a different summary or the metadata is incorrect, provide corrections.

### Step 3: Save the Conversation
Once confirmed, the skill:
- Creates a new `.md` file in `copilot-conversations/`
- Writes the full conversation transcript
- Includes the metadata header
- Commits the file (optional, use `git add` + `git commit` if desired)

## Filename Convention

All exported conversations follow this pattern:

```
{YYYY-MM-DD}_{HHMMSS}_{SUMMARY}_{BRANCH}.md
```

Examples:
- `2026-07-17_143022_Feature-Auth_main.md` — Feature work on main branch
- `2026-07-17_094530_Bug-Fix_setup.md` — Debugging session on setup branch
- `2026-07-17_154700_Refactor_optimize.md` — Code refactoring work

Replace spaces in summary with hyphens for valid filenames.

## Tips for Good Summaries

- Use **action words**: Feature, Bug-Fix, Refactor, Debug, Setup, Config, Review
- Use **topic words**: Auth, Pipeline, API, Database, UI, Tests
- Keep it **short and specific**: "Bug-Fix-Parser" is better than "Bug-Fix-Long-Pipeline-Parser"
- Avoid **vague terms**: "Work" or "Stuff" won't help you find it later

## Retrieving Exported Conversations

List all exported conversations:
```bash
ls -la copilot-conversations/
```

Search by keyword or date:
```bash
grep -l "Summary.*Feature" copilot-conversations/*.md
grep -l "2026-07-17" copilot-conversations/*.md
```

Retrieve a specific conversation (replace filename):
```bash
cat copilot-conversations/FILENAME.md
```

## Integration Notes

- Exported conversations should be committed to git so they're available to future sessions
- Store only meaningful conversations; skip trivial troubleshooting unless it might recur
- Conversations are markdown for easy readability in any text editor or on GitHub
- Consider exporting at natural breakpoints: after a feature is complete, after a major bug is resolved, after significant discussion of architecture
