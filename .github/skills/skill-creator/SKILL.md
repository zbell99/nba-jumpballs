---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance across different agent harnesses. Use when users want to create a reusable skill from scratch, edit or generalize an existing skill, define eval prompts, compare skill-assisted runs against a baseline, or improve skill metadata so the harness invokes it more reliably.
---

# Skill Creator

Create, test, and refine reusable skills in a way that survives changes in model, editor, and harness.

The core loop is simple:

- Understand the job the skill should do
- Draft or revise the skill
- Run realistic test prompts with the skill enabled
- Compare those runs to a baseline when the harness allows it
- Review the outputs qualitatively and, where possible, quantitatively
- Revise the skill based on evidence instead of anecdotes
- Repeat until the skill is stable and general

This works immediately for new skills when the task is drafting the skill, creating eval prompts, reviewing outputs, and iterating on the skill body. The one part that is not universal out of the box is automated trigger optimization, because that depends on how a particular harness exposes routing decisions.

Do not confuse these completion states:

- Drafted skill: the instructions exist and are usable in a chat.
- Packaged skill: the skill folder has the expected files such as `SKILL.md`, `evals/`, `references/`, `assets/`, or `scripts/` when relevant.
- Benchmark-ready skill: the environment has a real way to execute the eval prompts with the skill enabled, run a baseline, capture outputs and transcripts, grade them, and aggregate results.

`evals/evals.json` by itself does not make a skill benchmarkable. It is only the input to a benchmark workflow. If the current harness cannot run the skill programmatically yet, say that clearly and either build the missing runner or fall back to manual review instead of implying the benchmark loop is already available.

Your job is to figure out where the user is in that loop and move them to the next useful step. Sometimes that means drafting a new skill. Sometimes it means improving a messy draft. Sometimes it means skipping formal evaluation and working conversationally because the user just wants to iterate quickly.

## Communicating with the user

Users will vary a lot in how comfortable they are with terms like eval, benchmark, JSON, assertion, schema, or harness. Match their level.

- Use plain language by default
- Explain terms briefly when they matter to the next decision
- Avoid unnecessary jargon when a simpler phrase works
- Keep the user oriented around what happens next, what evidence you need, and what success looks like

## Harness-first thinking

Do not assume a specific product, model, CLI, packaging format, or trigger mechanism. Start by identifying what the current environment can actually do.

### Capabilities to check

Determine which of these are available before prescribing a workflow:

- Skill files or prompt files that can be edited directly
- Tool execution for creating files, running scripts, or launching viewers
- Subagents or parallel workers for side-by-side comparisons
- A harness-specific executor or adapter that can run the skill on eval prompts and save outputs
- A browser or HTML viewer for human review
- A packaging format for exporting the skill
- A trigger mechanism based on metadata, routing rules, tags, descriptions, manifests, or explicit user selection

If a capability is missing, adapt instead of blocking. For example:

- No subagents: run test prompts one at a time
- No browser: present outputs in chat or save static artifacts
- No harness runner for efficacy tests: say the skill is not yet benchmark-ready and build the missing runner before claiming one-command testing exists
- No automated trigger evaluator: use curated trigger and near-miss prompts for manual review
- No packaging step: leave the skill in a clean folder with install notes

## Creating a skill

### Capture intent

Start by understanding the user's intent from the conversation before asking repetitive questions.

Extract what you can from existing context:

- The workflow they want to capture
- The input shapes the skill should expect
- The outputs the skill should produce
- The mistakes they want the skill to avoid
- The tools or files the skill is allowed to use

Then confirm the missing pieces.

Ask questions like these when needed:

1. What should this skill enable the agent to do?
2. When should the harness reach for this skill, and when should it not?
3. What output format or deliverable should the user get?
4. Should this skill include formal evals, or is qualitative review enough?
5. Are there environment constraints like no shell, no browser, no subagents, or read-only installs?

### Interview and research

Proactively ask about:

- Edge cases
- Input and output formats
- Example files or prompts
- Success criteria
- Competing skills or nearby capabilities
- Known failure modes

If the environment provides good research tools, use them. If it does not, rely on the codebase and the conversation. The goal is to reduce ambiguity before you write the skill, not to do broad speculative research.

### Write the SKILL.md

Fill in these pieces:

- `name`: stable identifier
- `description`: what the skill does and when to use it
- `compatibility`: optional; include only when the skill depends on specific tools, runtimes, or file formats
- body: instructions, references, constraints, and examples

The metadata should reflect the harness. Some systems key mostly off a free-text description. Others use separate manifests, tags, or routing tables. If the current harness has a known trigger surface, write to that surface directly.

### Skill writing guide

#### Anatomy of a skill

```text
skill-name/
├── SKILL.md or equivalent instructions file
├── evals/
│   └── evals.json
├── scripts/
├── references/
└── assets/
```

Use the local conventions of the harness if they differ. The important part is to keep the skill self-contained and easy to inspect.

If the user wants one-command efficacy testing, treat `scripts/` as functionally required, not optional. That runner may be generic across many skills or bundled with the skill itself, but someone must own the execution path that turns eval prompts into transcripts, outputs, grades, and benchmark artifacts.

#### Progressive disclosure

Keep the main skill file focused. Put bulky or specialized material in supporting files.

- Keep the top-level description concise and high-signal
- Put the durable workflow in the main file
- Put schemas, examples, templates, and helper scripts in supporting files
- Point clearly to those files when the agent should read them

#### Principle of lack of surprise

The skill should only do what its description prepares the user and the harness to expect. Do not include hidden side effects, misleading behavior, exploit code, or instructions that would compromise the user's system or data.

#### Writing patterns

Prefer imperative guidance with reasoning.

Good pattern:

```markdown
## Review structure
Use this structure so the user can compare runs quickly:

# Summary
## What changed
## What improved
## What still fails
```

Examples help when the output shape matters.

### Writing style

Explain why an instruction matters. Avoid brittle prompt lawyering unless the task truly requires exact structure.

Use strong constraints only when they protect correctness, safety, or interoperability.

## Test cases

After drafting the skill, create 2-3 realistic test prompts that a real user would plausibly write. Share them with the user before running them when practical.

Save test cases to `evals/evals.json` when the skill repository uses file-based evals.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User task prompt",
      "expected_output": "Description of a successful result",
      "files": []
    }
  ]
}
```

If the local schema differs, follow the local schema instead. Use `references/schemas.md` as the default schema reference for this skill package.

## Running and evaluating test cases

Treat this as one continuous workflow. Do not stop after drafting prompts if the user asked for a real evaluation loop.

Before you describe the workflow as script-runnable, verify that the current environment has a usable execution harness. This can be:

- a benchmark runner script already present in the skill package
- a shared runner in the local skill-creator toolkit
- a harness adapter that can launch skill-enabled and baseline runs programmatically

If none of those exist, do not tell the user the skill is fully testable by script yet. The next task is to build that missing runner or adapter.

Store outputs in a sibling workspace such as `<skill-name>-workspace/`, grouped by iteration and eval name.

`evals/evals.json` is a test case inventory, not the runner. The runner is responsible for consuming those evals, executing with-skill and baseline runs, saving artifacts, and invoking grading plus aggregation.

### Step 1: Run skill-assisted and baseline cases

If the harness supports side-by-side comparison, run every eval in both modes within the same overall pass:

- `with_skill`: the skill enabled
- `baseline`: no skill, or the previous/original version of the skill

Use the strongest baseline the environment allows:

- Creating a new skill: compare against no skill if possible
- Improving an existing skill: compare against the original or previous revision
- No baseline support: run only the skill-assisted case and rely more heavily on qualitative review

For each eval, create metadata such as:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

Prefer descriptive directory names over anonymous counters when the filesystem layout allows it.

### Step 2: Draft assertions while runs are happening

If runs are asynchronous, use that time to define assertions. If runs are synchronous, do this immediately after capturing outputs.

Good assertions are:

- objectively checkable
- easy to understand in a report
- aligned with what the user actually cares about

Do not force quantitative assertions onto subjective tasks like writing voice, visual taste, or general creativity. Use human review for those.

### Step 3: Capture execution metadata

If the harness exposes timing, token counts, or tool counts, save them. If it does not, omit them rather than inventing them.

Example timing file:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

### Step 4: Grade, aggregate, and review

Once all runs are finished:

1. Grade each run against its assertions. Save `grading.json` if the workflow uses file-based grading.
2. Aggregate results into a benchmark when the data is rich enough to justify it.
3. Do a short analyst pass. Look for weak assertions, flaky evals, non-discriminating checks, and time or token regressions.
4. Present the results in the best review surface the harness allows.

Possible review surfaces:

- HTML viewer
- static HTML file
- notebook or dashboard
- markdown summary in chat
- side-by-side folder of artifacts

Use the included viewer and scripts when they fit the current environment. If they do not fit, keep the review loop intact with simpler artifacts instead of forcing a broken workflow.

### Step 5: Collect feedback

Focus revisions on the runs where the user found concrete issues. Empty feedback usually means the run was acceptable.

Whether feedback arrives through a browser form, downloaded JSON, issue comments, or chat, normalize it into a small set of actionable complaints before editing the skill.

## Improving the skill

This is the core of the loop.

### How to think about improvements

1. Generalize from the feedback. Do not overfit the skill to the exact eval prompts.
2. Keep the skill lean. Remove instructions that create noise or duplicate what the base agent already does well.
3. Explain the why. Skills are more robust when the instructions teach judgment instead of only imposing rules.
4. Look for repeated work. If every run recreates the same helper script or template, bundle it.
5. Preserve portability. If you add harness-specific branches, isolate them clearly so the core workflow remains portable.

### Iteration loop

After improving the skill:

1. Apply the revision
2. Rerun the eval set into a new iteration directory when possible
3. Compare against the prior baseline if that comparison is still meaningful
4. Review outputs with the user
5. Repeat until the skill is stable, the user is satisfied, or further changes are not producing meaningful gains

## Advanced: blind comparison

If the user wants a more rigorous A/B comparison, use an independent grader or reviewer that does not know which output came from which version. This is optional and only useful when the environment supports an actually independent comparison.

## Trigger optimization

How a harness decides to invoke a skill varies. Some rely on free-text descriptions. Others use metadata fields, rules, tags, manifests, or explicit user selection. Optimize for the mechanism the current harness actually uses.

Treat automated trigger optimization as optional advanced tooling, not as a prerequisite for creating a good new skill. A new skill can still be drafted, tested, reviewed, and improved without any trigger adapter.

### Step 1: Generate trigger eval queries

Create a set of realistic should-trigger and should-not-trigger prompts.

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Make these prompts realistic, detailed, and slightly messy. The best negative cases are near-misses, not obviously unrelated requests.

### Step 2: Review the eval set with the user

Use the best editing surface available. An HTML editor is fine if the harness can open one. Otherwise review the JSON directly in chat or in files.

### Step 3: Evaluate the trigger behavior

If the environment has an automated trigger-eval loop, use it. If it does not, run a manual review:

- inspect whether the harness chose the skill for each prompt
- note false positives and false negatives
- revise the metadata or routing rules
- rerun the same eval set

The included optimization scripts are adapter-based. Use them only when you have:

- a harness adapter that can answer whether the skill triggered for a given prompt
- a rewrite command that can propose revised metadata or descriptions

If you do not have those adapters yet, do the trigger review manually and keep moving.

### Step 4: Apply the result

Update the routing metadata, description, manifest, or selector rules with the best-performing revision. Show the user the before and after.

## Packaging and delivery

If the harness has a formal packaging step, package the skill. If it does not, leave the skill in a clean folder with everything needed to install or copy it manually.

When updating an existing installed skill:

- preserve the original name unless the user asks for a rename
- edit a writable copy if the installed location is read-only
- keep exported filenames and folder names consistent with local conventions

## Harness adaptation patterns

Use the workflow that matches the current environment.

### Full-featured harness

Use when you have file editing, script execution, subagents or parallel workers, and a browser or static viewer.

- draft the skill
- run with-skill and baseline evals
- capture metrics
- generate a viewer or report
- collect feedback
- iterate

If trigger automation adapters exist for this harness, you can also run automated trigger optimization. Otherwise do trigger review manually.

### Limited harness

Use when you can edit files and run prompts, but not parallel workers or a browser.

- draft the skill
- run evals serially
- save outputs in folders
- present results directly in chat or markdown
- collect feedback inline
- iterate

Assume manual trigger review unless the harness already has working adapters.

### Minimal harness

Use when you can mainly edit text and reason in chat.

- draft the skill
- create test prompts
- do a dry-run walkthrough of how the skill would respond
- identify likely failure modes
- leave a clear follow-up plan for real execution in the user's preferred environment

Do not block on trigger automation in this mode.

## Reference files

Read these when they are useful to the current step:

- `agents/grader.md`: grading guidance for assertions
- `agents/comparator.md`: blind comparison workflow
- `agents/analyzer.md`: benchmark analysis guidance
- `references/schemas.md`: JSON shapes for evals and reports

## Core reminder

Keep the loop evidence-driven:

- define the skill clearly
- test it on realistic prompts
- compare against a baseline when you can
- review both outputs and failure modes
- revise the skill, not just the examples
- stop when the user is satisfied or the next iteration is unlikely to pay off
