# Issue tracker: GitHub

This repo's specs and tickets are GitHub issues. Use the `gh` CLI for everything. It picks up the repo from `git remote -v` when run inside the clone.

## Conventions

- **Create**: `gh issue create --title "..." --body "..."`, with a heredoc for multi-line bodies. Add `--label "..."` as needed.
- **Read**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`, filtered with `--label` and `--state`.
- **Comment**: `gh issue comment <number> --body "..."`.
- **Labels**: `gh issue edit <number> --add-label "..."` and `--remove-label "..."`.
- **Close**: `gh issue close <number> --comment "..."`.
- **Sub-issue of a parent**: `gh issue create --parent <parent> ...`, or afterwards `gh issue edit <parent> --add-sub-issue <child>` (`gh` 2.94 or later). With an older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child database id>` (see **Blocking** below for the database id). Where sub-issues aren't available, start the child body with `Part of #<parent>`.

GitHub numbers issues and PRs in one sequence, so `#42` could be either. Try `gh issue view 42` first and fall back to `gh pr view 42`.

## Labels

- `ready-for-agent`: fully specified; an agent can build it.
- `backlog`: real work that isn't ready yet.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the ticket"

Read it as in **Read** above.

## Pathfinder operations

Used by `/kal:pathfinder`. A **map** is one issue whose tickets are its **child** issues.

- **Map**: an issue labelled `pathfinder:map`, holding the Destination / Notes / Decisions so far / Not yet specified / Out of scope body. `gh issue create --label pathfinder:map ...`.
- **Ticket**: a sub-issue of the map (see **Sub-issue of a parent**). Without sub-issues, list the child in a task list in the map body and start the child body with `Part of #<map>`. Labels: one of `pathfinder:research`, `pathfinder:prototype`, `pathfinder:interrogate`, `pathfinder:task`. A claimed ticket is assigned to the driving developer.
- **Blocking**: GitHub's **native issue dependencies**, which show up in the UI. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker database id>`. The database id is numeric (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`), not the `#number` or `node_id`. `issue_dependencies_summary.blocked_by` counts open blockers only. Where dependencies aren't available, put a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked once every blocker is closed.
- **Frontier**: the map's open children (`gh issue list --state open`, limited to its sub-issues or task list), minus any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue on its `Blocked by` line) and any with an assignee. The first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, as the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then add a pointer (gist plus link) to the map's Decisions so far.
