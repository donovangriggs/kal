---
name: interrogate
description: Interview the user hard about a plan, decision, or idea until both sides share one understanding, asking every question through AskUserQuestion. Use when the user wants their thinking stress-tested, says "grill me", "interrogate this", "poke holes", or another skill asks for an interview.
---

# Interrogate

Keep questioning the user until you and they agree on the whole picture. Treat the topic as a **decision tree**: each decision opens the decisions that depend on it.

## Rounds

Work in **rounds**. The **frontier** is every decision whose prerequisites are already settled, so you can ask it now without guessing at answers you haven't heard. Each round asks the entire frontier, then waits.

A question whose answer hinges on another question in the same round is not on the frontier. Hold it for a later round.

After each round, the answers settle some branches and open others. Recompute the frontier and run the next round.

## Asking: always AskUserQuestion

Every question to the user goes through the **AskUserQuestion** tool. Never ask in plain prose.

- At most **4 questions per call**. A frontier bigger than 4 becomes several calls, back to back, in the same round.
- Each question has **2 to 4 options**. Put your recommended answer first and end its label with "(Recommended)".
- Never add an "Other" option: the tool adds one automatically, and that is where the user types anything you didn't foresee.
- Keep the `header` chip to 12 characters or fewer.
- Write the question so the recommended option reads as the natural yes. Put the reasoning and trade-offs in each option's `description`, not in a wall of text before the call.
- A question with genuinely open answers (a name, a number) still gets 2 to 4 concrete suggestions; the user types their own via "Other".

## Facts versus decisions

**Facts** are your job. When a frontier question needs something knowable from the environment (the filesystem, the code, a tool, the docs), send a subagent to find it. Never ask the user for something you could look up.

Don't stall on the lookup. A running exploration is just an unsettled prerequisite: only the questions downstream of it wait. Ask the rest of the frontier now.

**Decisions** belong to the user. Put each one to them and wait for the answer.

## When to build instead of talk

Some questions are really "how should this look?" or "does this flow feel right?". Words are a poor way to settle those. For such a question, include an option like **"Build a prototype"**. If the user picks it, call the Skill tool with "kal:prototype", let the user react to what it produces, record the outcome (in the glossary or an ADR via kal:domain-language if it qualifies), then resume the interview from the updated frontier.

## Main session only

This skill runs in the user's main session. Subagents and background workers can't reach the user, so they never interrogate; they report what they found instead.

## Done

The interview is over when the frontier is empty: every branch visited, nothing quietly assumed. Summarise the shared understanding, and do not act on it until the user confirms it is right.
