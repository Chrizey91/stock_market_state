# ISSUES

Local issue files from `issues/` are provided at start of context. Parse them to understand the open issues.

You will work on the AFK issues only, not the HITL ones.

You've also been passed a file containing the last few commits. Review these to understand what work has been done.

If all AFK tasks are complete, output <promise>NO MORE TASKS</promise>.

# TASK SELECTION

Pick the next task. Prioritize tasks in this order:

1. Critical bugfixes
2. Development infrastructure

Getting development infrastructure like tests and types and dev scripts ready is an important precursor to building features.

3. Tracer bullets for new features

Tracer bullets are small slices of functionality that go through all layers of the system, allowing you to test and validate your approach early. This helps in identifying potential issues and ensures that the overall architecture is sound before investing significant time in development.

TL;DR - build a tiny, end-to-end slice of the feature first, then expand it out.

4. Polish and quick wins
5. Refactors

# EXPLORATION

Explore the repo.

# IMPLEMENTATION

Use the `tdd` skill (Test-driven development / red-green-refactor) to complete the task.
Before starting implementation, you MUST read the skill instructions in `.agents/skills/tdd/SKILL.md` using the `view_file` tool and follow them exactly.

# FEEDBACK LOOPS

Before committing, run the feedback loops:

- `npm run test` to run the tests
- `npm run typecheck` to run the type checker

# COMMIT

Stage and commit your changes using the `run_command` tool:
1. Run `git add <files>` or `git add .` to stage changes.
2. Run `git commit -m "<message>"` with a message that includes:
   - Key decisions made
   - Files changed
   - Blockers or notes for the next iteration

# THE ISSUE

If the task is complete, move the issue file using the `run_command` tool:
1. Ensure the `issues/done/` directory exists (create it using `mkdir -p issues/done` or powershell equivalent if necessary).
2. Move the issue file to `issues/done/` using `git mv issues/<filename> issues/done/`.

If the task is not complete, add a note to the issue file detailing what was done using a file editing tool (like `replace_file_content`).

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
