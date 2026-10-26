# kal

A Claude Code plugin that takes a feature from a loose idea to merged code: interactive planning, then an AFK build by role agents in tmux or herdr panes.

## Language

### Planning

**Spec**:
The written description of one feature: problem, solution, user stories, implementation and testing decisions, and what's out of scope.
_Avoid_: PRD, design doc

**Ticket**:
One tracer-bullet slice of a spec, sized for a single agent session, with blocking edges to other Tickets.
_Avoid_: task, story, issue (an issue is just where a Ticket may live)

**Seam**:
A public interface where tests observe behavior. The Spec fixes them before any code is written.

**Map**:
Pathfinder's index of a large effort: its destination, decisions so far, fog and out-of-scope items.

### Building

**Run**:
One build of one Spec (or one Ticket), from the first Worker to the final hand-off.
_Avoid_: job, pipeline, session

**Orchestrator**:
The main session driving a Run. It alone writes Run state.
_Avoid_: lead, manager

**Worker**:
An agent running one Role on one Ticket in its own multiplexer pane (tmux or herdr). It closes when its Report is written.
_Avoid_: subagent, teammate

**Role**:
The duty a Worker performs: developer, reviewer, qa, security, bug-fixer or merger.

**Round**:
One pass of a Ticket through development and checks. A Ticket gets at most two fix Rounds before it needs you.

**Report**:
The file a Worker writes for its Round, ending in a Verdict and the commit it applies to.

**Verdict**:
A Report's last word: READY or STUCK (developer), PASS or CHANGES (reviewer, qa, security), FIXED or STUCK (bug-fixer), MERGED, CONFLICT or RED (merger). It only counts for its own commit and Round.

**Integration branch**:
The branch every Ticket of a Run merges into before the final hand-off.
_Avoid_: feature branch

**Relay**:
The Orchestrator clearing its own context and resuming the same Run from disk.
_Avoid_: restart, compaction

**Board**:
The repo's local read-only dashboard of every Run.
_Avoid_: kanban, UI
