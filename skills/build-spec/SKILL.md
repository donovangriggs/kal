---
name: build-spec
description: Build a whole spec AFK in tmux. Up to 3 developer workers build tickets in parallel as their blockers merge, each ticket runs the kal pipeline (checks, fixes, merge) into an integration branch, and the end of the spec runs refine-code, a final review, a standards check and full QA before asking how to hand it off. Pauses, resumes, and relays its own context. Invoke only when the user explicitly asks for it or accepts it as the offered next step of another kal skill.
argument-hint: "<spec: issue number, URL or path>"
---

Spec: $ARGUMENTS

You are the **orchestrator** of a **Run** that carries one spec and all its tickets to a single hand-off. Tickets merge into the Run's **integration branch** (`kal/<feature>`). It reaches the branch the user started on (the **target**) only at the end, the way they choose.

The per-ticket pipeline is the one in `/kal:build`. **Read [../build/SKILL.md](../build/SKILL.md) now**, then follow its *Standing rules*, *2. Running a worker*, *3. Develop*, *4. Check*, *5. Fix*, *6. Merge* and *Needs you* for every ticket, with the differences below. Where they disagree, this file wins.

## What's different from /kal:build

- **Many tickets at once.** Developers start only through `kal-next` (section 3), never on your own: it holds the 3 developer slots and the blocking edges. Every other role (checks, bug-fixers, mergers) starts as soon as its step comes up.
- **Merges go into the integration branch**, one at a time, **in the background.** `kal-merge` targets the integration branch by itself, and its full Verify can take minutes, so never block on it: when a ticket reaches `ready-to-merge` and no merge is running, run `kal-set <ticket> Status=merging --log "merging"` and start `kal-merge <ticket file>` with `run_in_background: true`. Other tickets that reach `ready-to-merge` meanwhile wait, and when a merge's completion arrives, act on its exit code (`/kal:build` section 6) and start the next waiting one, lowest number first. Keep scheduling (section 3) while a merge runs. On a resume, a ticket left `merging` with no merge running gets `kal-merge` again.
- **The orchestrator stays responsive.** Handle each worker's completion as it arrives (a background notification starts your turn). Do the step it unblocks, then run sections 3 and 4, and end your turn.
- **Ask late.** A ticket that needs you waits while everything else moves. Questions are batched when `kal-next` says `idle` (section 5).

## 1. Preflight

1. **Fetch the spec and every ticket under it**, the way `docs/agents/issue-tracker.md` says. State the spec's title and the number of tickets. The feature slug is the spec's slug.
2. **Write the mirrors.** Write one mirror per ticket at `.kal/runs/<feature>/tickets/<NN>-<slug>.md`, in the format of `/kal:build`'s Preflight step 2. `NN` follows the slice order: blockers get lower numbers. Translate each ticket's blocking edges into its mirror's `Blocked by:` as mirror numbers. Copy the spec to `.kal/runs/<feature>/spec.md`. Skip any mirror that exists already: that's a resume.
3. **Start.** Run `kal-start .kal/runs/<feature> --mode build-spec`.
   - **Exit 1:** show the line and stop.
   - **Exit 3:** tell the user to run `/kal:setup` and stop.
   - **Exit 4:** another Run is active. Ask: pause it (recommended) / stop. To pause, run `touch <its run dir>/pause`, then tell the user to run this command again once its panes have closed. Then stop.
   - **Exit 0:** `first start`, `resume` or `finished`. On `finished`, say so and stop.
   Then run `kal-board` and print the URL it prints, once: `Board: <url>`. Don't repeat it later.
4. **On a resume:** read `run.md`'s `## Notes` (your handoff from before a Relay) and each mirror's `## Log`. Re-attach a waiter to every worker listed in any `Workers:` line (`kal-worker <role> <ticket> [--as <name>] --attach <pane id>`, in the background). Pick up each ticket from its status. If `run.md` says `Phase: final`, continue at section 6.
5. Go to section 3.

## 2. Each completion

Handle it once. Find the ticket whose `Workers:` lists the completion's pane id. If none does, it was handled already: ignore it. Then:

1. Act on the verdict as `/kal:build` says, then sort its **Proposed tickets** (section 4).
2. **Context check:** run `kal-ctx .kal/runs/<feature>`. If its line ends in `relay`, Relay (section 7) instead of continuing.
3. Run section 3.

## 3. Fill the slots

Run `kal-next .kal/runs/<feature>` after preflight, after every completion and after every merge. Handle every line before you run it again:

- **`start <ticket file>`:** run `kal-begin <ticket file>`, then start its developer (`/kal:build` section 3).
- **`resume <ticket file>`:** a parked ticket whose prerequisite has merged. Run `kal-set <ticket> Status=in-dev Round=<K+1> "Waits on=" --log "resumed: prerequisite merged"`. Then start its developer with the note `resumed: merge the base in, then continue from your previous rounds`. This round doesn't count toward the fix cap.
- **`idle: all merged`:** go to the end of the spec (section 6).
- **`idle: paused`:** say the Run is paused and stop. Running `/kal:build-spec` again resumes it.
- **Any other `idle: …`:** nothing can move without the user. Go to section 5.
- **Nothing printed:** workers are live. End your turn and wait.

## 4. Discovered work

Workers only propose; you decide. Skip any proposal that duplicates an existing ticket, and send back any that is really the current ticket's own job as a finding.

- **Creating a ticket:**
  1. Give it the next free `NN`.
  2. Write its mirror with `Status: ready`, `Blocked by:` (from the proposal), and a `Discovered from: <NN>` line.
  3. Publish it to the tracker with the same blocking edges, labelled `ready-for-agent`.
  4. Log the creation on the ticket it came from.
- **The cap:** at most **3** discovered tickets (mirrors with `Discovered from:`) per Run are created without asking. Past that, write the proposal to `.kal/runs/<feature>/proposals.md` as `awaiting approval` and ask about it with the other questions (section 5).
- **prerequisite:** create it, then park the ticket that needs it: `kal-set <ticket> Status=parked "Waits on=<new NN>" --log "parked: waits on <new NN>"`. Its worktree and branch stay. `kal-next` resumes it once the prerequisite merges.
- **follow-up (in scope):** create it. It joins the queue like any ticket.
- **out-of-scope:** append it to `proposals.md` under `## Out of scope`, for the end (section 6).
- **spec-conflict:** run `kal-set <ticket> Status=needs-you --log "spec conflict: <one line>"`. Tickets that depend on it wait by themselves.

## 5. Questions for the user

When `kal-next` prints an `idle` line naming tickets that need you, ask about all of them at once: up to 4 questions per AskUserQuestion call, more calls if needed. Run `kal-notify "kal: <feature> needs you"` first.

- **A ticket that needs you:** retry with a note (the user types it through Other; add it under `## Comments`, start one more round, re-run the failed step) / I'll take it (leave its worktree; it stays `needs-you`) / drop it (`Status=dropped`; the tickets that depend on it may start, so ask about those too if it matters).
- **A spec conflict:** amend the spec (update it in the tracker and in `.kal/runs/<feature>/spec.md`, then retry the ticket) / drop the ticket / build it as written (retry with that note). Record the decision in an ADR when it qualifies (`kal:domain-language`).
- **Proposals awaiting approval:** one multi-select question. Create the ones picked (section 4).

Then run section 3 again.

## 6. End of the spec

1. **Open Ticket 00:** run `kal-final .kal/runs/<feature>`. Ticket 00 is the whole integration branch: its branch and worktree are the integration branch's, and its base is the target. Every worker below takes `.kal/runs/<feature>/tickets/00-final.md` as its ticket.
2. **Refine:** run a developer with `--model <yours>` and the note `mode: refine: call the Skill tool with "kal:refine-code" for the whole diff against the base (inside a kal build: no gates), and work through .kal/runs/<feature>/refine.md; tests green before and after; commit as refactor:; finish with the full Verify via kal-verify`.
   - **STUCK:** run `kal-set` to log it, and go on without the refine: it's an improvement, not a gate.
3. **Final checks**, all at once, at the same commit:
   - a **reviewer** with `--model <yours>` and the note `mode: final`
   - a **reviewer** with `--as standards` and the note `mode: standards`
   - a **qa** with the notes `mode: full` and `browser: yes|no` (yes when the spec changes something a user sees and the Commands block has a Dev server)
   - a **security** worker, when the whole diff touches a security trigger
4. **Fixes:** the same rules as `/kal:build` section 5, but the fixer is a **developer** with `--model <yours>` and a note naming every report to answer. At most 2 rounds, re-running only the checks that failed. After that, it needs you: ask retry with a note / stop.
5. **Out-of-scope proposals:** if `proposals.md` has any, ask in one multi-select question which to file in the tracker as `backlog`.
6. **Hand-off:** ask how to finish, recommending what fits the repo:
   - **Open a PR:** push the integration branch and open a PR into the target, the way the tracker doc says (`gh pr create` / `glab mr create`). The body summarises the spec and lists the tickets it closes. Then run `kal-finish .kal/runs/<feature> --keep-branch`.
   - **Merge into `<target>`:** run `kal-finish .kal/runs/<feature> --merge-into <target>`.
   - **Merge into `main`:** the main checkout must be on `main` and clean (ask before switching it). Then run `kal-finish .kal/runs/<feature> --merge-into main`.
   - For `kal-finish` exit codes 2 to 5, show its line and ask what to do. Nothing has been merged at that point.
7. **Close** each merged ticket and the spec the way the tracker doc says, unless the PR closes them.
8. Run `kal-notify "kal: <feature> finished"`. Then report: where it landed, tickets merged, dropped and discovered, rounds used, end-of-spec findings by severity, and anything left for the user.

## 7. Relay

When `kal-ctx` says `relay`, your context is getting large. Clear it and resume from disk:

1. Rewrite `run.md`'s `## Notes` so a fresh context can carry on from the files alone: agreements made, deviations from the spec, and for every ticket not merged what it waits on and what you'd do next. Use `kal-set .kal/runs/<feature>/run.md --notes - <<'EOF'` … `EOF`, and use `### ` headings only, never `## `.
2. Run `kal-relay "/kal:build-spec <spec reference>"`.
3. End your turn and start nothing more. The hooks clear your context and type the command. The fresh context resumes (Preflight step 4) and re-attaches to the live workers.
