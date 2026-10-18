---
name: verify
description: Run the repo's quality gates in six phases (build, types, lint, tests, secret and debug-leftover scan, diff review) and report PASS or FAIL. Detects each repo's own commands. Use after finishing a feature, fix or refactor, before opening a PR, or when a kal QA worker needs a verification pass.
---

# Verify

Six phases, in order. Each phase reports its own result; the run passes only if every phase passes.

## Find the commands

Use the repo's own commands, never guessed ones:

1. The `## Commands` block in `CLAUDE.md`. Its `Verify` line is the full check CI runs; prefer it whenever it exists.
2. Otherwise the manifest: `package.json` scripts (pick the package manager from the lockfile), `pyproject.toml`, `go.mod`, `Cargo.toml`, `Makefile`, or the CI workflow.

A phase whose tool the repo doesn't use is reported as `SKIP (not configured)`, not as a failure.

Always run with `set -o pipefail` so a phase's exit status survives truncated output (`2>&1 | tail -50`).

## Reuse a result at the same commit

If you were given a results folder and a commit sha:

- Before running, look for `<results>/<sha>.log`. If it exists and ends in `Overall: PASS`, report that result and stop. Nothing changed since it passed.
- After running, save the full report to `<results>/<sha>.log`.

Only reuse when the working tree is clean at that sha (`git status --porcelain` is empty). Uncommitted changes mean the saved result doesn't cover what's there.

## Phases

1. **Build.** The project's build. If it fails, stop and report: nothing downstream is meaningful.
2. **Types.** `tsc --noEmit`, `pyright`/`mypy`, or the stack's equivalent. Report the count and the first errors.
3. **Lint.** The configured linter. Report errors and warnings separately.
4. **Tests.** The full suite. Report total, passed, failed and skipped, and coverage if the repo already measures it. Don't invent a coverage threshold the repo doesn't set.
5. **Leak scan**, over the files changed in this diff:
   - hardcoded secrets: `sk-`, `api_key`, `secret`, `password =`, private key headers, connection strings with credentials;
   - debug leftovers: `console.log`, `print(` / `pprint(` debugging, `debugger`, `.only(` in tests.
   Test fixtures and `.env.example` don't count.
6. **Diff review.** `git diff --stat` against the base. Read each changed file for unintended edits, files that shouldn't be in the change (lockfile churn, generated output, local config), and missing error handling.

## Report

```
VERIFY REPORT  (at <sha>)
Build:    PASS | FAIL
Types:    PASS | FAIL (N errors) | SKIP
Lint:     PASS | FAIL (N errors, M warnings) | SKIP
Tests:    PASS | FAIL (passed/total, coverage if measured)
Leaks:    PASS | FAIL (N findings)
Diff:     N files changed; <anything unintended>

Overall:  PASS | FAIL

To fix:
1. <file:line: what, and the command output that shows it>
```

Any phase FAIL makes the overall result FAIL. Lint warnings alone don't fail the run unless the repo's lint config treats them as errors.
