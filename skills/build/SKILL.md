---
name: build
description: Build one ticket AFK in tmux or herdr. A developer worker builds it test-first, then reviewer, QA and security workers check it in parallel, a bug-fixer handles blocking findings, and it merges into the current branch. Each worker gets its own pane, which closes when it's done. Invoke only when the user explicitly asks for it or accepts it as the offered next step of another kal skill.
argument-hint: "<ticket: issue number, URL or path>"
---

Ticket: $ARGUMENTS

You are the **orchestrator** of a **Run** that carries one ticket from ready to merged into the branch the user is on. You coordinate; **workers** do the work, each in its own tmux or herdr pane. Vocabulary: `GLOSSARY.md` in the kal plugin.

## Standing rules

- **Workers, never subagents.** Start every worker as `kal-worker <role> <ticket file> …` with the Bash tool's `run_in_background: true`. Its first output line is `<pane id> <session id>` (pane id `%N` in tmux, `wN:pM` in herdr; pass it on as is). Its completion notification, ending in `done` or `stalled`, means the worker has finished. Never poll a worker and never `sleep`.
- **You alone write Run state.** Change the ticket mirror and `run.md` only through `kal-set` (and what `kal-begin` / `kal-merge` write). Log exactly one line per transition (`--log "…"`): no progress notes. Run state must be enough to resume from.
- **Status values:** `in-dev`, `in-review`, `fixing`, `ready-to-merge`, `merging` (a merge is running), `merged`, `parked`, `needs-you`.
- **The main checkout stays on its branch.** You write only under `.kal/` there, apart from closing the ticket the way the tracker doc says. Never push.
- **Models:** pass `--model <your own model id>` to developer and bug-fixer workers, so they run on the session's model. The other roles use their agent's model.
- **Every question to the user goes through AskUserQuestion**, with the recommended option first and labelled "(Recommended)".

## 1. Preflight

1. **Fetch the ticket** the way `docs/agents/issue-tracker.md` says, and state its title. If the reference is ambiguous, ask. Find its spec (its parent issue, or the `spec.md` beside it) and the feature slug. If any ticket blocking it isn't done yet, ask whether to build anyway.
2. **Write the mirror** `.kal/runs/<feature>/tickets/<NN>-<slug>.md`, unless it exists already: then this is a resume, or, if its `Status:` is `merged`, say it's merged already and stop. `NN` is the ticket's two-digit number in its spec's slice order, or `01` if that's unknown. Copy the spec to `.kal/runs/<feature>/spec.md`.
   ```markdown
   # <NN>: <title>

   Status: ready
   Size: <trivial|small|standard|large, from the ticket; standard if missing>
   Source: <issue URL / number / path>
   Blocked by: <NN, NN or none>

   ## What to build
   <the ticket's text>

   ## Acceptance criteria
   - [ ] …

   ## Log
   ```
3. Run `kal-start .kal/runs/<feature>`. It prints one line:
   - **Exit 1:** a check failed. Show the user the line (it's the fix) and stop.
   - **Exit 3:** setup is missing. Tell the user to run `/kal:setup` and stop.
   - **Exit 4:** another Run is active in this repo. Ask: pause it (recommended) / stop. To pause, run `touch <its run dir>/pause`, then tell the user to run this command again once its panes have closed. Then stop.
   - **Exit 0:** `first start`, `resume` or `finished`. On `finished`, say so and stop.
4. Run `kal-board` and print the URL it prints, once: `Board: <url>`. The repo's dashboard shows the Run live. Don't repeat the URL later.
5. Run `kal-begin <ticket file>`. It cuts the branch and worktree from the base branch and readies dependencies. On a resume it just reports what's already there.

**On a resume**, read the mirror's `## Log` and the round folders under `.kal/runs/<feature>/reports/<NN>/`. Re-attach a waiter to each worker listed in `Workers:` (`kal-worker <role> <ticket> --attach <pane id>`, in the background), then continue from the status.

## 2. Running a worker

1. Start `kal-worker <role> <ticket file> [--model …] [--note "…"]…` in the background.
2. Read its first output line. Then run `kal-set <ticket> --worker "<role> <model> <pane id> <HH:MM>" --log "<role> started"`.
3. On its completion, read its report, `.kal/runs/<feature>/reports/<NN>/round-<K>/<report>.md`, and take the last `Verdict:` and `At:` lines. Then run `kal-set <ticket> --no-worker <role>`.
4. **Crash or stall** (`stalled`, no report, or no `Verdict:`): start the same role again with `--respawn`, once. If that prints `needs-human: …`, the ticket needs you (section 6). A respawn doesn't change the round.

Report files: developer `dev.md`, reviewer `review.md`, qa `qa.md`, security `security.md`, bug-fixer `fix.md`, merger `merge.md`.

## 3. Develop

Run the **developer** with `--model <yours>`.

- **READY:** `kal-set <ticket> Status=in-review --log "dev READY at <short sha>"`, then go to Check.
- **STUCK:** treat it as a failed round and go to Fix, with the note `developer STUCK: read dev.md`.

## 4. Check

Decide which checks run, and log the decision in the same `kal-set` line:

- **Size `trivial`:** the reviewer only.
- **Otherwise:** the reviewer and qa, plus security when the diff (`git -C <worktree> diff <base>...HEAD`) touches auth, user input handling, database queries, file paths, external calls, crypto or secrets.
- **qa's notes:** `mode: ticket`, and `browser: yes` when the ticket changes something a user sees in the running app and the Commands block has a Dev server. Otherwise `browser: no`.
- **The reviewer's note:** `mode: ticket`.

Start every chosen check back to back in the background before waiting on any of them; they check the same commit. Record them in one `kal-set … --worker … --worker …`. Act only once all of them have finished.

Then sort the results:

- Append each report's **Non-blocking findings** to `.kal/runs/<feature>/refine.md`, under a `## <NN> round <K>` heading.
- Collect each report's **Proposed tickets** (section 7).
- **Browser not run:** if qa's note said `browser: yes` and its report says `Browser: not run`, the browser server failed. Run qa once more with the note `retry: the browser server failed last time` before acting on the results. If it still says not run, log `browser QA not run: <why>` on the ticket and act on its other results: list it in the final report so the user knows that check didn't happen.
- **Every check PASS:** `kal-set <ticket> Status=ready-to-merge --log "checks PASS at <short sha>"`, then Merge.
- **Any CHANGES:** go to Fix.

## 5. Fix

A ticket gets at most **2 fix rounds**. In round K, once the fixes have run out:

- **If K − 1 < 2** (fix rounds left): run `kal-set <ticket> Status=fixing Round=<K+1> --log "<which checks> CHANGES → round <K+1>"`. Then run the **bug-fixer** with `--model <yours>` and a note naming every report to answer (for example `fix: round-1/review.md, round-1/qa.md`).
  - **FIXED:** re-run **only the checks that returned CHANGES**, at the new head, in this same round. Then sort as in Check.
  - **STUCK:** the ticket needs you.
- **Otherwise:** the ticket needs you, with the reason `CHANGES after 2 fix rounds, see round-<K>/`.

## 6. Merge

Run `kal-merge <ticket file>`:

- **Exit 0:** merged. Go to Finish.
- **Exit 4 (conflict):** run the **merger** with the note `conflict with <base>`.
  - **MERGED:** start a new round that doesn't count toward the cap. Re-run the reviewer only, then merge again.
  - **CONFLICT:** the ticket needs you.
  - **RED:** go to Fix with the note `merger RED: read merge.md`.
- **Exit 5 (RED):** go to Fix with the note `kal-merge RED: read the newest verify-*.log in the round folder`.
- **Exit 2, 3 or 6:** the ticket needs you, with the line it printed as the reason.

## 7. Proposed tickets

Workers only propose. You decide. Skip any proposal that duplicates an existing ticket, and send back any that is really this ticket's own job as a finding.

- **prerequisite:** this ticket can't be done without it. `kal-set <ticket> Status=parked --log "parked: needs <title>"`, then ask: file it now and stop, so you can build it first (recommended) / continue without it / stop.
- **spec-conflict:** park the ticket and ask: amend the spec / drop this ticket / build it as written. Record the decision in the spec, and in an ADR if it qualifies (`kal:domain-language`).
- **follow-up** and **out-of-scope:** keep them for Finish.

## Needs you

Run `kal-set <ticket> Status=needs-you --log "<reason in one line, naming the report>"` and `kal-notify "kal: <NN> needs you"`. Then ask:

- **Retry with a note:** the user types the note through Other. Add it under `## Comments` in the mirror, start one more round and re-run the step that failed.
- **I'll take it from here:** leave the worktree and branch for the user, and say where they are.
- **Stop:** leave everything as it is. Running `/kal:build` with the same ticket later resumes.

## Finish

1. Close the ticket the way the tracker doc says.
2. If any follow-up or out-of-scope proposals were collected, ask in one multi-select question which to file: follow-ups as `ready-for-agent`, out-of-scope ones as `backlog`. Record each filed ticket on the Run so the board shows it: `kal-set .kal/runs/<feature>/run.md --append Filed "- <NN>: <title> | <status> | <tracker path or URL>"`.
3. If `refine.md` has findings for this ticket, mention the count, and offer `/kal:refine-code` on the merged change.
4. Run `kal-set .kal/runs/<feature>/run.md --log "<NN> merged"` and `kal-notify "kal: <NN> merged"`. A single-ticket Run folder stays open: the feature's next `/kal:build` reuses it.
5. Report to the user: the merge commit on the base branch, the rounds used, the checks that ran, and findings by severity.
