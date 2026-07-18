# Agents.md — NBA Jumpballs

This document contains **foundational rules and constraints** for all agents working on nba-jumpballs.

## Documentation is Canonical

When file structure, code organization, or architecture changes occur, agents must maintain documentation consistency. The README file is the canonical sources of truth, keep them updated as such. If you make changes, update documentation afterwards by running the documentation-sync skill.

## Critical Constraints (Non-Negotiable)

### Agent Autonomy
- **Never run commands without explicit permission** — this includes terminal commands, git operations, deployments, API calls, or any system-modifying action
- You may edit files, especially when a skill that suggests changes is invoked. However, your default action should not be to make edits when the user is just asking a question
- Write the minimal code that satisfies the requirement. No extra error handling, config files, classes, or abstraction unless asked. Prefer flat over nested, simple over clever.

### Configuration & Security
- **Never commit** `.env` or any file containing credentials
- **Never hardcode** Redis host, DynamoDB table names, AWS credentials, or API keys in source
- `.env.example` is the authoritative source for required environment variables

### Code Quality
- **Single source of truth** — each concept documented in ONE primary location
  - README = project overview and quick orientation
  - Code comments = implementation-level details
- Changes to shared code require verification that breaking changes are identified and communicated

## Where to Find Information

- **Project overview, quick start, data flow** → [README.md](README.md)
- **Key code structure** → [README.md](README.md#project-structure)