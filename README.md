# kal

A Claude Code plugin for planning a feature with you, then building it AFK.

- **Plan** interactively. Every question arrives as a multiple-choice prompt with a recommended answer.
- **Spec and slice** the plan into tickets with blocking edges.
- **Build** with role agents (developer, reviewer, QA, security, bug-fixer, merger), each in its own tmux pane. `/kal:build` works today; whole-spec builds and the dashboard are in progress (see [PLAN.md](PLAN.md), section 14).

## Install

```sh
claude plugin marketplace add donovangriggs/kal      # once per machine (or a local path to this checkout)
claude plugin install kal@kal --scope project         # in each repo
```

Then, inside Claude Code in that repo:

```
/kal:setup
```

Setup checks your tools, picks an issue tracker (GitHub, GitLab, local markdown or another), records the repo's Verify / Dev server / Teardown commands, and commits the config so teammates get kal when they clone.

## Use

| Step | Command | What it does |
|---|---|---|
| Plan a big effort | `/kal:pathfinder` | Charts a map of decision tickets across sessions, until the way to a spec is clear |
| Plan a feature | `/kal:interrogate-and-record` | Interviews you until the design is settled, recording terms in `GLOSSARY.md` and decisions as ADRs |
| Write the spec | `/kal:write-spec` | Turns the conversation into a spec, including the agreed test seams |
| Slice tickets | `/kal:slice-tickets` | Breaks the spec into vertical-slice tickets with blocking edges and a size tier for each |
| Build one ticket | `/kal:build <ticket>` | Inside tmux: a developer builds it test-first, reviewer + QA + security check it in parallel, a bug-fixer handles blocking findings, and it merges into your current branch. Each worker gets its own pane, which closes when it's done |
| Build a whole spec | `/kal:build-spec` | *Coming in milestone 3* |

Each step offers the next one when it finishes, so you rarely need this table.

Skills the agents load themselves: `interrogate`, `domain-language`, `investigate`, `prototype`, `red-green`, `deep-modules`, `best-practices`, `refine-code`, `verify`, `browser-qa`, `security-checklist`.

## Development

```sh
python3 -m unittest discover -s tests     # bin/ scripts against throwaway git repos
claude --plugin-dir .                     # try a local checkout without installing it
```

Workers started from a local checkout get `--plugin-dir` automatically when kal isn't installed for the repo. Claude Code blocks writes inside a loaded plugin's own folder, so test kal on a repo outside this checkout, not on kal itself.

## Updating

Marketplace installs are cached copies. Bump `version` in `.claude-plugin/plugin.json` with every change, then run `claude plugin marketplace update kal`.

## Credits

Adapted from [Matt Pocock's skills](https://github.com/mattpocock/skills) and [ECC](https://github.com/affaan-m/ECC), both MIT. See [NOTICE](NOTICE).
