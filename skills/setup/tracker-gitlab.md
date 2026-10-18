# Issue tracker: GitLab

This repo's specs and tickets are GitLab issues. Use the [`glab`](https://gitlab.com/gitlab-org/cli) CLI for everything. It picks up the project from `git remote -v` when run inside the clone.

## Conventions

- **Create**: `glab issue create --title "..." --description "..."`, with a heredoc for multi-line descriptions. Add `--label "..."` as needed.
- **Read**: `glab issue view <number> --comments`, or `-F json` for machine-readable output.
- **List**: `glab issue list -O json`, filtered with `--label`.
- **Comment**: `glab issue note <number> --message "..."`. GitLab calls comments "notes".
- **Labels**: `glab issue update <number> --label "..."` and `--unlabel "..."`. Several labels can be comma-separated or passed with repeated flags.
- **Close**: `glab issue close <number>`. It takes no closing comment, so post the explanation first with `glab issue note`, then close.
- **Merge requests**: GitLab's name for PRs. `glab mr create`, `glab mr view`, `glab mr note` and so on, shaped like `gh pr ...` with `note`/`--message` in place of `comment`/`--body`.

GitLab numbers issues and merge requests separately, so `#42` is an issue and `!42` is a merge request.

## Labels

- `ready-for-agent`: fully specified; an agent can build it.
- `backlog`: real work that isn't ready yet.

## When a skill says "publish to the issue tracker"

Create a GitLab issue.

## When a skill says "fetch the ticket"

Run `glab issue view <number> --comments`.

## Pathfinder operations

Used by `/kal:pathfinder`. A **map** is one issue whose tickets are its **child** issues.

- **Map**: an issue labelled `pathfinder:map`, holding the Destination / Notes / Decisions so far / Not yet specified / Out of scope body. `glab issue create --label pathfinder:map ...`. On GitLab tiers with epics, an epic can hold the map instead; a labelled issue works on every tier.
- **Ticket**: an issue whose description starts with `Part of #<map>`, labelled with one of `pathfinder:research`, `pathfinder:prototype`, `pathfinder:interrogate`, `pathfinder:task`. A claimed ticket is assigned to the driving developer.
- **Blocking**: GitLab's **native blocking link**, which shows up in the UI. Add it with the `/blocked_by` quick action posted as a note: `glab issue note <child> --message "/blocked_by #<blocker>"`. Blocking links need Premium or Ultimate; on the free tier, put a `Blocked by: #<n>, #<n>` line at the top of the description instead. A ticket is unblocked once every blocker is closed.
- **Frontier**: the map's open children (`glab issue list -O json`), minus any with an open blocker (a native `blocked_by` link to an open issue, via `glab api projects/:id/issues/<child iid>/links`, or an open issue on its `Blocked by` line) and any with an assignee. The first in map order wins.
- **Claim**: `glab issue update <n> --assignee @me`, as the session's first write.
- **Resolve**: `glab issue note <n> --message "<answer>"`, then `glab issue close <n>`, then add a pointer (gist plus link) to the map's Decisions so far.
