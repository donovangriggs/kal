---
name: slice-tickets
description: Break a spec, plan or the current conversation into tracer-bullet tickets, each sized and declaring which tickets block it, and publish them to the configured tracker (one file per ticket locally, or issues with native blocking links on a real tracker). Invoke only when the user explicitly asks for it or accepts it as the offered next step of another kal skill.
---

# Slice Tickets

Turn a plan, spec or conversation into **tickets**: thin vertical slices, each naming the tickets that **block** it and carrying a size.

The issue tracker should already be configured (see `docs/agents/issue-tracker.md`). If it isn't, tell the user to run `/kal:setup`.

## Process

### 1. Gather context

Start from what's already in the conversation. If the user passes a reference (a spec path, an issue number or URL), fetch it and read the full body and every comment.

### 2. Explore the codebase (if you haven't)

Understand the current state of the code the work touches. Use the vocabulary in `GLOSSARY.md` for ticket titles and descriptions, and respect ADRs in the area.

Look for prefactoring that would make the work easier: make the change easy, then make the easy change.

### 3. Draft vertical slices

Cut the work into **tracer-bullet** tickets.

<slice-rules>

- Each ticket cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests). Vertical, never one horizontal layer.
- A finished ticket can be demoed or verified on its own.
- Each ticket fits comfortably in one fresh context window.
- Prefactoring tickets come first.

</slice-rules>

Give every ticket its **blocking edges**: the tickets that must finish before it can start. A ticket with none can start immediately.

Give every ticket a **size**, which decides how much checking the build pipeline runs on it:

- **trivial**: one file, a few lines, no new contract (copy changes, config, docs).
- **small**: one file or one function, obvious once you've read the code.
- **standard**: two to five files, or one real design choice.
- **large**: many files or cross-cutting, a new external dependency, or a public API.

A ticket that touches authentication or authorization, user input handling, database queries, file system paths, external API calls, cryptography or secrets, or a public API, is **at least standard**, whatever its file count.

**Wide refactors are the one exception to vertical slicing.** A wide refactor is a single mechanical change (renaming a column, retyping a shared symbol) whose **blast radius** spans the codebase, so one edit breaks thousands of call sites and no vertical slice can land green. Sequence it as **expand, migrate, contract** instead:

1. **Expand:** add the new form beside the old one, so nothing breaks.
2. **Migrate:** move call sites across in batches sized by blast radius (per package or directory), each batch its own ticket blocked by the expand. CI stays green throughout because the old form still exists.
3. **Contract:** delete the old form once nothing uses it, in a ticket blocked by every migrate batch.

If even the batches can't stay green alone, keep the sequence, but let the batches share an integration branch and block one final integrate-and-verify ticket. Green is only promised there.

### 4. Check the breakdown with the user

Show the proposed tickets as a numbered list. For each:

- **Title**: short and descriptive.
- **Size**: trivial / small / standard / large.
- **Blocked by**: the tickets that must finish first, if any.
- **Delivers**: the end-to-end behaviour it makes work.

Then ask through the AskUserQuestion tool, in one call:

- Is the granularity right (too coarse / about right / too fine)?
- Are the blocking edges correct, with each ticket depending only on tickets that genuinely gate it?
- Should any tickets be merged or split?

Recommend the answer you believe in for each. Revise and ask again until the user approves.

### 5. Publish to the tracker

Publish the approved tickets. Only the shape of the blocking edges depends on the tracker configured by `/kal:setup`:

- **Local files:** one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first), using the local template below. Never one combined file.
- **A real tracker (GitHub, GitLab, Linear, ...):** one issue per ticket, in dependency order (blockers first) so each ticket's edges can reference real identifiers. Use the platform's native blocking relationship where it has one, otherwise a "Blocked by" section. If the source was an existing issue, make each ticket its sub-issue (see the tracker doc). Apply the `ready-for-agent` label unless told otherwise: the tickets are built to be picked up by agents.

Do NOT close or edit the parent issue.

### 6. Offer the build

Ask with AskUserQuestion whether to start building now, recommending "Run /kal:build-spec". If they say yes, call the Skill tool with "kal:build-spec" and pass the spec reference.

<local-ticket-template>

# <NN>: <Ticket title>

**Size:** trivial | small | standard | large

**Blocked by:** the numbers and titles of the gating tickets, or "None (can start immediately)".

**Status:** ready-for-agent

**What to build:** the end-to-end behaviour this ticket makes work, from the user's point of view, not a per-layer task list.

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

A link to the parent issue, if the source was an existing issue (otherwise leave this section out).

## Size

trivial | small | standard | large

## What to build

The end-to-end behaviour this ticket makes work, from the user's point of view, not a per-layer task list.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- A link to each blocking ticket, or "None (can start immediately)". Leave this section out when the blockers are set as native links.

</issue-template>

In either form, avoid file paths and code: they go stale fast. Exception: when a prototype produced a snippet that pins a decision down more precisely than prose (a state machine, reducer, schema or type shape), inline it and note that it came from a prototype, trimmed to the decision-carrying parts.
