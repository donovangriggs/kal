---
name: refine-code
description: Restructure code without changing what it does, with tests green before and after every step. Simplifies recently changed code, removes dead code and unused dependencies, and consolidates duplicates. Use when the user wants code cleaned up, simplified or refactored, at the end of a kal spec, or when collected MEDIUM/LOW review findings need clearing.
---

# Refine Code

Same behavior, better structure. If any behavior is meant to change, this is the wrong skill: that's a feature or a fix.

## Two ways this runs

- **Standalone** (the user asked): present the restructure plan first and confirm it with the AskUserQuestion tool before touching code.
- **Inside a kal build** (your brief says so): no gates. Work the plan, commit, report.

## 1. Scope it

- By default, refine the **recently changed** code: the diff the user or brief points at. Don't wander into untouched modules.
- Read any refine list you were given (collected MEDIUM/LOW findings) and fold it in.
- Read the repo's `CLAUDE.md` / lint config so the result matches house style. Consistency with the repo beats any rule here.

## 2. Establish the safety net

Before changing anything, run the tests that cover the code in scope and confirm they're **green**. Detect the command: the `## Commands` block in `CLAUDE.md` first, then `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` or the `Makefile`.

If coverage of the code you're about to move is thin, write **characterization tests** first: tests that pin down what the code does today, right or wrong, through its public interface. Never refactor code nothing tests.

If the tests are red before you start, stop and report it. A red baseline makes "behavior-preserving" unprovable.

## 3. Restructure in small steps

One kind of change at a time. Re-run the tests after each step; if a step turns them red, undo that step instead of debugging forward.

**Simplification targets:**

- Deep nesting → guard clauses and early returns.
- Tangled conditionals → named predicates.
- Callback chains → `async`/`await`.
- Long expression chains → named intermediate values, where that reads better.
- Nested ternaries → plain `if`s.
- Duplicated logic → one shared function.
- Single-use helpers and pass-through wrappers → inline them.
- Stray debug logging and commented-out code → delete.

When the question is *where a module boundary or interface should go*, call the Skill tool with `kal:deep-modules` for the vocabulary and the deletion test.

## 4. Dead-code sweep

Use the stack's detector, not guesswork:

| Stack | Tools |
|---|---|
| JS / TS | `npx knip`, `npx depcheck`, `npx ts-prune` |
| Python | `vulture`, `deptry` |
| Go | `staticcheck` (unused checks), `go mod tidy` |
| Rust | compiler `dead_code` warnings, `cargo udeps` |

Sort each candidate into a risk bucket before removing anything:

- **SAFE**: unused private code, unused imports, dependencies nothing imports.
- **CAREFUL**: anything that might be reached dynamically (string-built imports, reflection, plugin registries, config-driven lookups). Grep for the name as a string before removing.
- **RISKY**: exported or public API, CLI entry points, anything other repos may consume. Leave these alone unless the user explicitly asks.

Remove SAFE first, one bucket at a time (dependencies → exports → files → duplicates), testing after each batch. When in doubt, keep it.

## 5. Finish

- Build, types, lint and tests all green.
- The diff contains no behavior change: no new features, no altered outputs, no changed error messages.
- Commit as `refactor: <what changed>`, one commit per logical restructure.

Report what you simplified, what you removed (with its bucket), anything you deliberately left alone, and why.

## Don't

- Refactor during active feature work on the same code, or right before a release.
- Rename for taste. Rename only when the current name is misleading.
- Mix a refactor and a behavior change in one commit.
