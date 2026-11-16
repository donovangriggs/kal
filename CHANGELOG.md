# Changelog

Backfilled from the commit history. Versions match `version` in `.claude-plugin/plugin.json`.

## 0.9.2 (2026-11-15)
- Docs: honest Safety section (workers have a full shell; the git guard is a guardrail, not a sandbox),
  status and support lines, SECURITY.md and this changelog.
- CI: the test suite runs on macOS in GitHub Actions.
- Tests: a test no longer leaves a child process running.

## 0.9.1 (2026-10-26)
- herdr panes carry their Role's color as an emoji in the label.

## 0.9.0 (2026-10-26)
- Builds run in whichever multiplexer you start in: herdr or tmux.
- One place for the multiplexer rule and the herdr socket.
- Fix: a slow multiplexer no longer counts a live Worker as gone.

## 0.8.1 (2026-10-19)
- A repo-wide Backlog view on the Board; runs show from the first second.

## 0.8.0 (2026-10-19)
- AFK all the way: away policy, working browser QA, flake retries.

## 0.7.1 (2026-10-19)
- Follow-up runs for a finished spec; the Board shows what a run filed.

## 0.7.0 (2026-10-19)
- Batch merges: one Verify for every ticket ready together.

## 0.6.0 (2026-10-19)
- One full Verify per ticket, at merge; merges run in the background.

## 0.5.4 (2026-10-19)
- tmux: each worker's pane border and title are colored by role, as on the Board.

## 0.5.3 (2026-10-19)
- Board: a Waiting on blockers lane before Ready.

## 0.5.2 (2026-10-19)
- The full Verify runs once per ticket, in QA beside the review.

## 0.5.1 (2026-10-18)
- Fix: workers stop chasing the base tip.

## 0.5.0 (2026-10-18)
- Polish for first real use (milestone 5). The repo is renamed to kal.

## 0.4.0 (2026-10-18)
- Live local dashboard, the Board (milestone 4).

## 0.3.0 (2026-10-18)
- Whole-spec builds with parallel developers (milestone 3).

## 0.2.0 (2026-10-18)
- Single-ticket build runtime and role agents (milestone 2).

## 0.1.0 (2026-10-18)
- Plugin skeleton and the planning and quality skills (milestone 1).
