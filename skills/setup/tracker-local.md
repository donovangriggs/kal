# Issue tracker: local markdown

This repo's specs and tickets are markdown files under `.scratch/`.

## Conventions

- One folder per feature: `.scratch/<feature-slug>/`.
- The spec is `.scratch/<feature-slug>/spec.md`.
- Tickets are one file each at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`. Never put several tickets in one file.
- Each ticket has a `Status:` line near the top: `ready-for-agent`, `backlog` or `done` (builds track their own progress separately in `.kal/`).
- Comments and discussion are appended at the bottom of the file under `## Comments`.

## When a skill says "publish to the issue tracker"

Create a file under `.scratch/<feature-slug>/`, creating the folder if needed.

## When a skill says "fetch the ticket"

Read the file at the given path. The user usually passes the path or the ticket number.

## When a skill says "close the ticket"

Set the ticket's `Status:` line to `done`, add one line under `## Comments` saying what merged and where, and commit only that file (`chore: close <NN>`).

## Pathfinder operations

Used by `/kal:pathfinder`. A **map** is a file with one **child** file per ticket.

- **Map**: `.scratch/<effort>/map.md`, holding the Destination / Notes / Decisions so far / Not yet specified / Out of scope body.
- **Ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, numbered from `01`, with the question as its body. A `Type:` line holds the ticket type (`research`, `prototype`, `interrogate` or `task`). A `Status:` line holds `claimed` or `resolved`; no line means open.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked once every file it lists is `resolved`.
- **Frontier**: the files in `.scratch/<effort>/issues/` that are open, unblocked and unclaimed. The lowest number wins.
- **Claim**: set `Status: claimed` and save, before any other work.
- **Resolve**: append the answer under `## Answer`, set `Status: resolved`, then add a pointer (gist plus link) to Decisions so far in `map.md`.
