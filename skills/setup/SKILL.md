---
name: setup
description: "Prepare a repo for kal: check the tools builds need, choose the issue tracker, set the domain-doc layout, record the repo's Verify / Dev server / Teardown / Worktree setup commands, and commit the config. Run once per repo before the other kal skills."
disable-model-invocation: true
---

# kal setup

Write the per-repo configuration the other kal skills rely on:

- **Requirements**: the tools a build needs, with a fix for each one that's missing
- **Issue tracker**: where specs and tickets live (GitHub, GitLab, local markdown, or another tracker you describe)
- **Labels**: the label strings the skills apply
- **Domain docs**: where `GLOSSARY.md` and ADRs live, and how skills read them
- **Commands**: how to verify, serve and tear down this repo, and how to prepare a fresh worktree

This is a guided skill, not a script: explore, show what you found, confirm, then write. Every question to the user goes through **AskUserQuestion** (up to 4 questions per call, 2 to 4 options each, recommended option first and labelled "(Recommended)").

## 1. Explore

Read what's actually there; assume nothing.

- `git remote -v` and `.git/config`: GitHub, GitLab, another host, or no remote?
- `CLAUDE.md` and `AGENTS.md` at the root: which exists? Does either already have `## Agent skills` or `## Commands`?
- `GLOSSARY.md` and `GLOSSARY-MAP.md` at the root; `docs/adr/` and any `src/*/docs/adr/`
- `docs/agents/`: has this skill run before?
- `.scratch/`: a sign the local-markdown tracker is already in use
- Monorepo signs: `pnpm-workspace.yaml`, a `workspaces` field in `package.json`, or a filled `packages/*` each with its own `src/`. Without these, the repo is single-context (nearly all repos are).
- Command sources: `package.json` scripts, `Makefile`, `pyproject.toml`, `go.mod`, `Cargo.toml`, CI config (`.github/workflows/*`, `.gitlab-ci.yml`), `docker-compose*.yml`, the README.
- `.gitignore` (is `.kal/` there?) and `.claude/settings.json` (is kal enabled for the project?)

### Requirements check

Run `kal-doctor`. It checks every tool a build needs (git, tmux, python3, node, Chrome, and `gh`/`glab` when the remote points there), Claude Code's folder trust for this repo, and whether kal is enabled here, printing a fix for each gap. Its setup checks (`docs/agents/`, the Commands block, `.kal/` ignored) will fail until this skill has run; that's expected.

A missing tool doesn't stop setup: planning works without any of them. Carry the list of what's missing (and what it blocks) into the summary.

## 2. Present and ask

Summarise what exists and what's missing, then ask. Skip any question exploration already answered.

**A. Issue tracker.** Specs and tickets are read from and written to here by `/kal:write-spec`, `/kal:slice-tickets`, `/kal:pathfinder` and the builds. Recommend from the remote:

- **GitHub** (remote on github.com): issues in the repo's GitHub Issues, via `gh`
- **GitLab** (remote on gitlab.com or a self-hosted GitLab): issues via [`glab`](https://gitlab.com/gitlab-org/cli)
- **Local markdown** (no remote, or a solo project): files under `.scratch/<feature>/` in the repo
- **Other** (Linear, Jira, …): the user describes the workflow in a paragraph, including how they'd create, link, label, block and close issues. You record it as prose.

**B. Domain docs.** Default to **single-context** (one `GLOSSARY.md` plus `docs/adr/` at the root) and don't ask. Only when exploration found monorepo signs, ask whether they want **multi-context** (a root `GLOSSARY-MAP.md` pointing to one `GLOSSARY.md` per context).

**C. Commands.** Propose each line from what you found (prefer exactly what CI runs), then confirm or correct it with the user:

- **Verify**: the full check CI runs: tests, plus lint and typecheck if CI runs them. Required.
- **Dev server**: serves the app on `127.0.0.1` at port `{port}` (builds substitute the real port). May be `none`.
- **Teardown**: stops whatever the app or its tests leave behind (containers, volumes). May be `none`.
- **Worktree setup**: prepares a fresh checkout, usually installing dependencies. Builds skip it when they can clone the main checkout's dependency folders. May be `none`.

## 3. Show drafts

Before writing anything, show the user:

- The `## Agent skills` and `## Commands` blocks for the chosen root file (see step 4)
- The contents of `docs/agents/issue-tracker.md` and `docs/agents/domain.md`
- The labels you'll create and the files you'll commit

Let them edit before you write.

## 4. Write

**Pick the root file:**

- If `CLAUDE.md` exists, edit it.
- Otherwise, if `AGENTS.md` exists, edit it.
- If neither exists, ask which to create. Don't choose for them.

Never create `AGENTS.md` when `CLAUDE.md` exists, or the reverse. If either block already exists, update it in place; never add a duplicate, and leave the user's other sections alone.

```markdown
## Agent skills

### Issue tracker

[one line: where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Domain docs

[one line: "single-context" or "multi-context"]. See `docs/agents/domain.md`.

## Commands

- Verify: `<command>`
- Dev server: `<command using {port}>` (or `none`)
- Teardown: `<command>` (or `none`)
- Worktree setup: `<command>` (or `none`)
```

**Write `docs/agents/`** from the templates beside this skill:

- [tracker-github.md](./tracker-github.md): GitHub
- [tracker-gitlab.md](./tracker-gitlab.md): GitLab
- [tracker-local.md](./tracker-local.md): local markdown
- [domain.md](./domain.md): how skills read the domain docs, plus the layout

For an "Other" tracker, write `docs/agents/issue-tracker.md` from the user's description. Keep the same sections as the templates (conventions, "publish", "fetch", Pathfinder operations), noting any operation the tracker can't do and the fallback to use instead.

**Labels.** On GitHub or GitLab, create each of these that doesn't exist yet (`gh label create` / `glab label create`):

- `ready-for-agent`: fully specified, an agent can build it
- `backlog`: real work, not yet ready
- `pathfinder:map`
- `pathfinder:research`
- `pathfinder:prototype`
- `pathfinder:interrogate`
- `pathfinder:task`

**Gitignore.** Add `.kal/` to `.gitignore` if it isn't there. That folder holds build runs, reports and dashboard state.

**Commit.** Stage only what this skill wrote or changed: `.claude/settings.json` (so teammates get kal on clone), the root `CLAUDE.md` or `AGENTS.md`, `docs/agents/`, `.gitignore`. Commit them as `chore: set up kal`. Never stage anything else.

## 5. Done

Run `kal-doctor` again and show its output: every setup line should now be `ok`. Tell the user setup is complete, and repeat any remaining `missing` or `warn` lines with their fixes. Mention they can edit `docs/agents/*.md` and the `## Commands` block directly at any time; re-running `/kal:setup` is only needed to switch trackers or start over.

Then use AskUserQuestion to offer the next step: plan a feature with `/kal:interrogate-and-record` (recommended for something that fits one session), chart a bigger effort with `/kal:pathfinder`, or stop here. If they pick one, call the Skill tool with "kal:interrogate-and-record" or "kal:pathfinder".
