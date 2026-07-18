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
4. **Marks contributions** — Distinguishes your inputs from Copilot's responses with clear visual markers
5. **Tracks decisions** — Highlights your key decisions and choices vs. Copilot's suggestions
6. **Creates a labeled file** — Saves with filename format: `{YYYY-MM-DD}_{HHMMSS}_{SUMMARY}_{BRANCH}.md`
7. **Stores in copilot-conversations/** — Places the file in the repo's conversation archive

## Metadata Format

Each exported conversation includes:

```
**Date**: YYYY-MM-DD HH:MM:SS (ET)
**Branch**: branch-name
**Summary**: keyword-one keyword-two
```

This header appears at the top of every exported file, making it easy to scan and filter saved conversations.

## Contribution Markers

The exported conversation clearly distinguishes your contributions from Copilot's:

- **👤 You:** Marks your requests, questions, and user inputs
- **🤖 Copilot:** Marks Copilot's responses and suggestions

Example:
```
👤 You: Can you help me optimize this data pipeline?

🤖 Copilot: I can help with that. Here's a more efficient approach...

👤 You: I like that, let me run a test first.

🤖 Copilot: Good idea. You should...
```

This makes it easy to scan the conversation and see exactly what you decided vs. what was suggested.

## Decision Tracking

In addition to contribution markers, the exported file includes a **Decisions** section that summarizes:

- **Your choices** — What you decided to do and why
- **Alternatives considered** — Options you rejected and your reasoning
- **Copilot suggestions you adopted** — Which recommendations you accepted
- **Copilot suggestions you declined** — Which recommendations you declined and why

Example decision entry:
```
### Decision: Use Pandas instead of Polars
- **Your choice:** Implement with Pandas
- **Reasoning:** Team already familiar with Pandas API
- **Alternative:** Copilot suggested Polars for performance, but rejected due to learning curve
```

This section is placed after the metadata header and before the full conversation transcript, providing a quick reference for the key decisions made during the session.

## Workflow

### Step 1: Request Export
Ask to export the conversation when you want to preserve work. Example prompts:
- "Export this conversation as 'feature-auth'"
- "Save this as 'bug-fix' to copilot-conversations"
- "Export with summary 'debugging pipeline'"

### Step 2: Confirm Metadata
The skill will:
- Generate a timestamp in ET (used as the primary sort key in filename)
- Detect the current git branch (using `git rev-parse --abbrev-ref HEAD`)
- Show the proposed filename for your confirmation

If you want a different summary or the metadata is incorrect, provide corrections.

### Step 3: Save the Conversation
Once confirmed, the skill:
- Creates a new `.md` file in `copilot-conversations/`
- Writes the full conversation transcript with contribution markers (👤 and 🤖)
- Includes a **Decisions** section summarizing your key choices and reasoning
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

## Example Output

Here's what an exported conversation looks like:

```markdown
**Date**: 2026-07-18 13:11:02 (ET)
**Branch**: main
**Summary**: data-cleanup

## Decisions

### Decision 1: Remove duplicate records using Pandas groupby
- **Your choice:** Use `groupby()` and `first()` to keep earliest records
- **Reasoning:** Performance is adequate for dataset size, familiar API
- **Alternative considered:** Copilot suggested dropping by index but you chose timestamp-based approach for data integrity

### Decision 2: Validate cleaned data before export
- **Your choice:** Added unit tests to verify row counts and null values
- **Reasoning:** Catch issues early in pipeline
- **Adopted Copilot suggestion:** Yes, used the pytest framework structure Copilot recommended

## Conversation Transcript

👤 You: I have duplicate records in my dataset. How should I clean this up?

🤖 Copilot: You can use `groupby()` to identify and remove duplicates. Here are two approaches:
1. Keep the first occurrence...
2. Drop by index...

👤 You: I like the first approach. Can you show me how to validate it works?

🤖 Copilot: Sure. Here's a test that checks row counts and verifies data integrity...

👤 You: Perfect. Let me run this and commit the changes.

[... rest of conversation ...]
```

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
