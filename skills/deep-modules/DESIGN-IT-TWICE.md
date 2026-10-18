# Design It Twice

When the user wants to explore alternative interfaces for a module being deepened, use parallel sub-agents. The idea comes from Ousterhout's "design it twice": your first design is rarely your best.

Uses the terms in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem

Before spawning anything, write the user a short explanation of the problem space for this candidate:

- the constraints any new interface has to meet,
- the dependencies it relies on, and which category each falls into (see [DEEPENING.md](DEEPENING.md)),
- a rough code sketch to make the constraints concrete. It is an illustration, not a proposal.

Show it to the user, then go straight to step 2. They read and think while the sub-agents work.

### 2. Spawn sub-agents

Launch 3 or more sub-agents in parallel. Each must produce a **radically different** interface for the deepened module.

Give each one its own technical brief (file paths, coupling details, the dependency category from [DEEPENING.md](DEEPENING.md), what sits behind the seam). The brief is separate from the user-facing explanation in step 1. Give each agent a different design constraint:

- Agent 1: "Minimise the interface: 1 to 3 entry points at most. Maximise leverage per entry point."
- Agent 2: "Favour flexibility: cover the widest range of callers and leave room to extend."
- Agent 3: "Serve the typical caller first: the everyday call should take one line."
- Agent 4 (where it applies): "Design around ports and adapters for the cross-seam dependencies."

Put both this skill's vocabulary and the project's `GLOSSARY.md` vocabulary in every brief, so each design names things consistently with the architecture language and the domain language.

Each sub-agent returns:

1. the interface (types, methods, parameters, plus invariants, ordering and error modes),
2. a usage example showing how callers use it,
3. what the implementation hides behind the seam,
4. its dependency strategy and adapters (see [DEEPENING.md](DEEPENING.md)),
5. trade-offs: where leverage is high and where it's thin.

### 3. Present and compare

Present the designs one after another so the user can take each in, then compare them in prose by **depth** (leverage at the interface), **locality** (where change concentrates) and **seam placement**.

Finish with your own recommendation: which design is strongest and why. If parts of different designs combine well, propose the hybrid. Be opinionated: the user wants a clear read, not a menu.
