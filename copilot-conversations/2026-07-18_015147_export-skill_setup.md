**Date**: 2026-07-18 01:51:47 (UTC)  
**Branch**: setup  
**Summary**: export-skill

---

# Export Conversation — Creating the export-conversation Skill

## Initial Request

User requested creation of an export-conversation skill to preserve Copilot conversations with structured metadata. Each conversation should be labeled with:
- Timestamp
- Git branch
- One-to-two word summary

## Skill Creation Process

### Step 1: Understanding Requirements
- Conversations needed to be preserved in `copilot-conversations/` folder
- Each export should include metadata: timestamp, git branch, summary
- Files should be properly ordered by time
- Format should be markdown for readability

### Step 2: Skill Development
Created `/Users/zbell/Dev/GitHub/nba-jumpballs/.github/skills/export-conversation/` with:

#### SKILL.md — Main skill documentation
Comprehensive skill guide including:
- **When to Use**: Run when completing significant conversations, resolving problems, reaching milestones
- **What It Does**: Captures conversation, extracts metadata, adds summary, creates labeled file
- **Metadata Format**: Includes Date (UTC), Branch name, and Summary
- **Workflow**: Three-step process (Request Export → Confirm Metadata → Save)
- **Filename Convention**: `{YYYY-MM-DD}_{HHMMSS}_{SUMMARY}_{BRANCH}.md`
- **Tips for Summaries**: Action words (Feature, Bug-Fix, Refactor, Debug, Setup, Config, Review) + topic words (Auth, Pipeline, API, Database, UI, Tests)
- **Retrieval Instructions**: How to list, search, and retrieve exported conversations

#### evals/evals.json — Test prompts
Three evaluation test cases:
1. Basic export flow with summary 'skill-creation'
2. Verify git branch detection and metadata accuracy with 'bug-fix' summary
3. Ensure persistence and proper chronological ordering with 'feature-auth' summary

### Step 3: Filename Format Adjustment
User feedback: timestamp should come first for proper alphabetical/chronological ordering.

**Initial design**: `{SUMMARY}_{YYYY-MM-DD}_{HHMMSS}_{BRANCH}.md`  
**Updated design**: `{YYYY-MM-DD}_{HHMMSS}_{SUMMARY}_{BRANCH}.md`

Updated all documentation and eval prompts to reflect this convention.

### Step 4: Applying the Skill
User requested to export this conversation using the newly created skill with summary "export-skill".

## Conversation Export
This file was created using the export-conversation skill workflow:
1. Captured the full conversation about skill creation
2. Detected current git branch: `setup`
3. Generated timestamp: 2026-07-18 01:51:47 UTC
4. Applied summary: export-skill
5. Created file with proper naming convention

## Key Decisions Made
1. **Metadata in filename first**: Enables chronological sorting by default
2. **UTC timestamps**: Consistent across timezones and systems
3. **Markdown format**: Readable in any text editor, displayable on GitHub
4. **Workflow guidance**: User-friendly prompts for requesting exports, confirming metadata, and retrieving conversations
5. **Practical examples**: Provided real-world use cases (Feature-Auth, Bug-Fix, Refactor) to guide users

## Files Created
- `/Users/zbell/Dev/GitHub/nba-jumpballs/.github/skills/export-conversation/SKILL.md`
- `/Users/zbell/Dev/GitHub/nba-jumpballs/.github/skills/export-conversation/evals/evals.json`
- `/Users/zbell/Dev/GitHub/nba-jumpballs/copilot-conversations/2026-07-18_015147_export-skill_setup.md` (this file)

## Next Steps
The export-conversation skill is now:
- ✅ Drafted and documented
- ✅ Packaged with evaluation prompts
- ✅ Ready for manual testing in future conversations
- 📋 Available for use whenever a conversation needs to be preserved
