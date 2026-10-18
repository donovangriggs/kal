---
name: write-spec
description: "Turn what's already been discussed into a spec and publish it to the repo's issue tracker, without interviewing the user again: synthesis only, plus a confirmation of the test seams. Invoke only when the user explicitly asks for it or accepts it as the offered next step of another kal skill."
---

Write a spec from the current conversation and what you know of the codebase. Do **not** run an interview: everything needed should already be in context. The one question you ask is the seam check in step 3.

The issue tracker should already be configured (see `docs/agents/issue-tracker.md`). If it isn't, tell the user to run `/kal:setup`.

## Process

1. **Know the codebase.** If you haven't explored the area this touches, do it now. Use the vocabulary in `GLOSSARY.md` throughout the spec, and respect any ADRs covering that area.

2. **Check for unmerged dependencies.** If the spec relies on code that only exists on another feature's unmerged branch (another integration branch, or an open PR not yet on main), warn the user before going further: every build starts from main, so that feature has to merge first.

3. **Agree the test seams.** Work out where the feature will be tested. Prefer seams that already exist over new ones, and the highest seam available over lower ones. If a new seam is needed, put it as high as you can. Fewer seams is better; one is ideal. Confirm them with the user through the AskUserQuestion tool: one question listing the proposed seams with a one-line note on what each catches and what it misses, with "use these seams" as the recommended option. These seams are what the developer agents will test at later, without asking again.

4. **Write and publish.** Fill in the template below, publish it to the issue tracker, and apply the `ready-for-agent` label. No further triage is needed.

5. **Offer the next step.** Ask with AskUserQuestion whether to slice the spec into tickets now, recommending "Run /kal:slice-tickets". If they say yes, call the Skill tool with "kal:slice-tickets".

<spec-template>

## Problem Statement

What problem the user faces, told from their point of view.

## Solution

How the feature solves it, told from the user's point of view.

## User Stories

A LONG numbered list, covering every aspect of the feature, each in the form:

1. As a <actor>, I want <capability>, so that <benefit>

<user-story-example>
1. As a library member, I want to renew a loan from my account page, so that I can keep a book longer without visiting the desk
</user-story-example>

## Implementation Decisions

The decisions made so far, for example:

- the modules to build or change
- the interfaces of those modules that change
- technical clarifications from the developer
- architectural decisions
- schema changes
- API contracts
- specific interactions

No file paths and no code: both go stale fast.

Exception: when a prototype produced a snippet that pins a decision down more precisely than prose (a state machine, reducer, schema or type shape), inline it under the relevant decision and note that it came from a prototype. Trim it to the decision-carrying parts; it isn't a working demo.

## Testing Decisions

- What makes a good test here: external behaviour only, never implementation details.
- The agreed test seams from step 3, each with what it covers.
- Which modules get tested.
- Prior art: similar tests already in the codebase.

## Out of Scope

What this spec deliberately does not cover.

## Further Notes

Anything else worth knowing about the feature.

</spec-template>
