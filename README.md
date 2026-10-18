# kal

A Claude Code plugin that plans a feature with you, then builds it while you're away.

- **Plan** interactively. Every question arrives as a multiple-choice prompt with a recommended answer, and the decisions land in a glossary, ADRs and a spec.
- **Slice** the spec into tickets with blocking edges.
- **Build** AFK. Role agents (developer, reviewer, QA, security, bug-fixer, merger) each work in their own tmux pane, in their own git worktree. Up to 3 tickets are built in parallel, everything is checked, and it merges into an integration branch. A live dashboard shows it all.

## Quickstart

**Requirements:** macOS, git, tmux, Python 3.9+, and Claude Code. Node and Google Chrome are needed for browser QA; `gh` or `glab` if your tickets live on GitHub or GitLab.

```sh
# once per machine
claude plugin marketplace add donovangriggs/kalistera

# once per repo
cd your-repo
claude plugin install kal@kal --scope project
claude                       # accept the folder-trust prompt if it asks
> /kal:setup
```

Setup checks your tools, picks where tickets live (GitHub, GitLab, local markdown, or another tracker you describe), records how the repo verifies, serves and tears down, and commits all of it, so teammates get kal when they clone.

**Then, for each feature:**

```
> /kal:interrogate-and-record     plan it (or /kal:pathfinder for something too big for one session)
> /kal:write-spec                 offered when the plan is settled
> /kal:slice-tickets              offered when the spec is written
```

**Build inside tmux:**

```sh
tmux new -A -s kal claude
> /kal:build-spec <spec>          the whole spec (or /kal:build <ticket> for one ticket)
```

Each step offers the next one when it finishes, so you rarely need to remember the commands.

## How a build runs

```
for each ticket, as soon as its blockers have merged (up to 3 developers at once):
  developer   builds it test-first, at the seams the spec agreed
  reviewer    ┐
  qa          ├ check the same commit, in parallel (qa drives the app in Chrome when there's UI;
  security    ┘ security runs only when the diff touches auth, input, queries, files, secrets...)
  bug-fixer   fixes blocking findings, then only the failed checks re-run (2 rounds at most)
  merge       into the integration branch, after one more Verify

end of the spec:
  refine-code, then final review + standards check + full browser QA in parallel, then fixes
  you choose: open a PR, merge into your branch, or merge into main
```

- **The dashboard:** each build prints a `Board:` URL (`kal-board` prints it any time). It shows every run in the repo: status lanes with a pipeline stepper per ticket, the dependency graph, a timeline of every worker, live panes with each worker's latest action, findings by severity, and a drawer per ticket with its reports, screenshots, verify logs, diff and log.
- **You're asked only when needed:** when a ticket is stuck after 2 fix rounds, the spec turns out wrong, or it's time for the hand-off. Everything else keeps moving meanwhile, and you get a desktop notification.
- **Tickets found along the way:** if a worker finds a missing prerequisite or follow-up, kal creates the ticket, wires its blocking edges, and parks whatever is waiting for it (3 per run before it asks). Anything out of scope is offered to you at the end, to file as backlog.
- **Pause:** `touch .kal/runs/<feature>/pause`. Live workers finish their current step, then the run stops. One feature builds at a time per repo; starting another offers to pause the first.
- **Resume** after a pause, a crash or a closed terminal: run the same command again. Everything resumes from `.kal/runs/<feature>/`.
- **Long runs** clear and resume the orchestrator's own context automatically.

## Safety

- Workers run unattended, with `--permission-mode dontAsk`: any shell command, file edits only inside their worktree and the run folder, no `git push`. A hook blocks destructive git (`stash`, `reset --hard`, `clean`, `checkout --`, `branch -D`, `commit --amend`, force pushes), including through `rtk`.
- Nothing leaves your machine unless you choose "open a PR" at the end.
- The dashboard is read-only, bound to `127.0.0.1`, and serves files only from `.kal/`.

## Troubleshooting

Run `kal-doctor` in the repo: it checks every requirement and prints the fix for each gap.

| Symptom | Fix |
|---|---|
| A build says the folder isn't trusted | Run `claude` in the repo once (without `--dangerously-skip-permissions`) and accept the trust prompt. Workers can't answer it. |
| A worker reports `blocked: … startup prompt` | Something asked an interactive question at startup. Run `claude` in the repo by hand, answer it once, and retry. |
| "not inside tmux" | `tmux new -A -s kal claude`, then run the command again. |
| A worker says a command was denied | Only `git push` and edits outside its worktree are denied by design. Anything else: report it. |
| Another run is active | Pause it (`touch .kal/runs/<other>/pause`) and retry once its panes close. |

## All the skills

| Command | What it does |
|---|---|
| `/kal:setup` | Prepare a repo for kal (run once) |
| `/kal:pathfinder` | Plan something too big for one session as a map of decision tickets |
| `/kal:interrogate-and-record` | Interview you until a design is settled, writing the glossary and ADRs as you go |
| `/kal:write-spec` | Turn the conversation into a spec with agreed test seams |
| `/kal:slice-tickets` | Break a spec into tracer-bullet tickets with blocking edges and sizes |
| `/kal:build <ticket>` | Build one ticket AFK and merge it into your current branch |
| `/kal:build-spec <spec>` | Build a whole spec AFK, then hand it off |
| `/kal:prototype` | Throwaway UI variants or a clickable logic demo, to settle a design question |
| `/kal:refine-code` | A behavior-preserving cleanup, with tests green before and after |

Used by the agents themselves: `interrogate`, `domain-language`, `investigate`, `red-green`, `deep-modules`, `best-practices`, `verify`, `browser-qa`, `security-checklist`.

## Development

```sh
python3 -m unittest discover -s tests     # bin/ scripts against throwaway git repos
claude --plugin-dir .                     # try a local checkout without installing it
```

Workers started from a local checkout get `--plugin-dir` automatically when kal isn't installed for the repo. Claude Code blocks writes inside a loaded plugin's own folder, so test kal on a repo outside this checkout, not on kal itself. Design and decisions: [PLAN.md](PLAN.md). Vocabulary: [GLOSSARY.md](GLOSSARY.md).

**Releasing:** marketplace installs are cached copies. Bump `version` in `.claude-plugin/plugin.json` with every change; users run `claude plugin marketplace update kal`.

## Credits

Adapted from [Matt Pocock's skills](https://github.com/mattpocock/skills) and [ECC](https://github.com/affaan-m/ECC), both MIT. See [NOTICE](NOTICE). The tmux worker mechanics come from final-boss.
