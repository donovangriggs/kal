---
name: prototype
description: Build throwaway code that answers one design question, either a clickable logic demo or several radically different UI variants. Use when someone wants to check whether a state model or flow feels right, or to see what a screen could look like before committing to it.
---

# Prototype

A prototype is **disposable code whose only job is to answer a question**. The question picks the form.

## Choose the mode

Work out which question is on the table, from the request, the code around it, or by asking (use the AskUserQuestion tool if the user is present):

- **"Does this logic or state model hold up?"** → [LOGIC.md](LOGIC.md). One self-contained HTML file that a non-developer can drive: free-play buttons plus tabbed, guided scenarios that push the model through the cases that are hard to reason about on paper.
- **"What should this look like?"** → [UI.md](UI.md). Several structurally different versions of a screen on one route, flipped between with a URL param and a floating bar.

The two modes produce completely different things, so picking the wrong one wastes the whole effort. If the question is truly ambiguous and nobody is around to ask, follow the surrounding code (a back-end module suggests logic, a page or component suggests UI) and write the assumption at the top of the prototype.

## Rules for both modes

1. **Disposable, and visibly so.** Put it next to the code it's exploring so the context is obvious, but name it so any reader can tell it isn't production. A throwaway UI route follows the project's existing routing convention; never invent a new top-level structure.
2. **One step to run.** A UI prototype starts with a single task-runner command (`pnpm <name>`, `python <path>`, `bun <path>`, and so on). A logic demo is one HTML file you double-click.
3. **In-memory by default.** If persistence is what the prototype is testing, use a scratch database or file named so nobody mistakes it for real data ("PROTOTYPE, safe to delete").
4. **No polish.** No tests, no error handling beyond what keeps it running, no abstractions. Speed of learning is the point.
5. **Show the state.** After every action (logic) or on every variant switch (UI), render the complete relevant state so the change is visible.
6. **Capture it when done.** Fold the validated decision into the real code. Commit the prototype itself to a throwaway branch that never merges, so it survives as a primary source, and leave a pointer to that branch on the related issue. Record the answer too (the verdict and the question it settled) in the issue or a commit message. Main only receives the decision.
