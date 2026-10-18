---
name: red-green
description: Test-driven development in red-to-green vertical slices, testing behaviour only at agreed seams. Use when building a feature or fixing a bug test-first, when someone mentions red-green-refactor or TDD, or when integration tests are wanted.
---

# Red-Green

TDD is the loop of writing a failing test, then making it pass. This skill is the reference that keeps that loop producing tests worth keeping: what makes a good test, where tests belong, the anti-patterns, and the rules of the loop. All of it applies on every cycle, so consult it before and during the loop, not afterwards.

While exploring, read `GLOSSARY.md` if it exists, so test names and interface vocabulary use the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

A good test checks behaviour through a public interface and ignores the implementation. The code underneath can be rewritten completely and the test still holds. It reads like a specification: "member can renew a loan that isn't overdue" says exactly which capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for when to mock.

## Seams: where tests go

A **seam** is the public boundary a test works at: the interface where behaviour can be observed without reaching inside. Tests live at seams, never against internals.

**Test only at agreed seams.** You can't test everything, and agreeing the seams up front puts the effort on the critical paths and complex logic instead of every edge case.

- **The spec has Testing Decisions:** those seams were already agreed with the user during `/kal:write-spec`. Use them as they are; don't ask again.
- **No spec, or it names no seams:** before writing any test, propose the seams and confirm them through the AskUserQuestion tool: "What's the public interface, and which seams should we test?", with a one-line note per seam on what it catches and what it misses. No test goes in at an unconfirmed seam.
- **Running unattended (as a build worker) with no agreed seams:** never ask. Choose the highest existing seam that exercises the ticket's acceptance criteria, and state that choice in your report.

When the shape of the interface is itself the question (how deep the module should be, where the seam belongs, what the interface exposes), call the Skill tool with "kal:deep-modules" for the vocabulary. It is the shared source of the terms module, interface, depth, seam, adapter, leverage and locality: a reference to consult, not a session to run.

## Anti-patterns

- **Coupled to the implementation:** mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The giveaway: the test breaks on a refactor even though behaviour didn't change.
- **Tautological:** the assertion recomputes the expected value the same way the code does (`expect(lateFee(days)).toBe(days * RATE)`, a hand-built snapshot made the same way, a constant compared with itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known literal, a worked example, the spec.
- **Horizontal slicing:** writing all the tests first and then all the code. Batch-written tests check *imagined* behaviour: they test the shape of things rather than what users see, stop noticing real changes, and lock in a test structure before the implementation is understood. Work in **vertical slices**: one test, then the code for it, then the next, each test a **tracer bullet** shaped by what the previous cycle taught you.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to make it pass. Don't anticipate later tests or add speculative features.
- **One slice per cycle.** One seam, one test, one minimal implementation.
- **No refactoring inside the loop.** Restructuring belongs after the build, in review and in `kal:refine-code`, not in the red-to-green cycle.
