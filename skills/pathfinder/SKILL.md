---
name: pathfinder
description: Plan a body of work too big for one agent session by charting it as a shared map of decision tickets on the issue tracker, then resolving those tickets one at a time until the route to the destination is clear. Use when a loose idea is too large or foggy to spec in one sitting. Invoke only when the user explicitly asks for it or accepts it as the offered next step of another kal skill.
---

# Pathfinder

A rough idea has landed. It's too big for one session, and foggy: you can't yet see the route from here to the **destination**. Pathfinding means finding that route, not sprinting at the destination. This skill lays the route out as a **shared map** on the repo's issue tracker, then works its **decision tickets** one at a time until nothing stands in the way. A decision ticket is a question whose answer is a decision, not a chunk of build work.

Naming the destination is the first act of charting, and it shapes every ticket. Usually it's a spec to hand to `/kal:write-spec`. It can also be a decision to lock in before planning, or a change made in place, such as migrating a data structure. The map works for any domain: code, content, operations.

## Decide, don't build

By default pathfinder **plans**. Each ticket settles a decision, and the map is finished when the route is clear: nothing left to decide before someone does the work. Feeling the urge to just start building usually means you've hit the map's edge, and it's time to hand off. An effort can override this in its map's **Notes** and carry execution into the map, but without that, produce decisions, not deliverables.

## Names, not numbers

Every map and ticket is an issue, so it has a title. In everything the user reads (your messages, the map's Decisions so far), refer to it by that title, never by a bare id, number or slug. A row of `#42, #43, #44` tells a reader nothing; titles read at a glance. Keep the link, but wrap it in the title: the id rides inside the name, it never replaces it.

## Talking to the user

Every question you put to the user goes through **AskUserQuestion**, under the rules in kal:interrogate: up to 4 questions per call, 2 to 4 options each, recommended option first and labelled "(Recommended)".

## The map

The map is one issue on the repo's tracker, labelled `pathfinder:map`. It is the canonical artifact, and its tickets are child issues of it.

The map is an **index**, not a store. It lists decisions made and points at the tickets holding the detail. Each decision lives in exactly one place, its ticket. The map only gives the gist and the link; it never repeats the decision.

**How maps, child tickets, blocking and frontier queries are stored depends on the tracker.** The tracker doc (`docs/agents/issue-tracker.md`) should already be available. If it isn't, tell the user to run `/kal:setup`. Follow its "Pathfinder operations" section for how this repo does each one. If no tracker is configured at all, use the local-markdown layout.

### Map body

The whole effort at low resolution, loaded once per session. Open tickets are **not** listed in it: they're found by querying the map's open children.

```markdown
## Destination

<one or two lines: what reaching the end of this map looks like (the spec, decision or change). Every session orients to this before picking a ticket.>

## Notes

<the domain; skills every session should load; standing preferences for this effort>

## Decisions so far

<!-- the index: one line per closed ticket, enough to judge relevance; follow the link for the detail -->

- [<closed ticket title>](link): <one-line gist of the answer>

## Not yet specified

<!-- the fog: in-scope questions too blurry to ticket yet; they graduate as the frontier moves -->

## Out of scope

<!-- work ruled beyond the destination; closed, never graduates -->
```

### Tickets

Each ticket is a **child issue** of the map, and its tracker id is its identity. The body is the question, sized for a single agent session of about 100K tokens:

```markdown
## Question

<the decision or investigation this ticket settles>
```

Each ticket has exactly one `pathfinder:<type>` label: `research`, `prototype`, `interrogate` or `task` (see Ticket types). The map and its tickets carry only `pathfinder:` labels, never `ready-for-agent` or other workflow labels: they are decisions, not implementation work.

A session **claims** a ticket by assigning it to the developer driving the map. That's the very first write, before any work, so parallel sessions skip it. The assignment *is* the claim: an open, unassigned ticket is up for grabs.

Blocking uses the tracker's **native** dependency link. That matters because the tracker's own UI then shows the frontier, so the user can see what's takeable without opening the map. Only a tracker with no native blocking falls back to a line in the body. A ticket is **unblocked** when every ticket blocking it is closed. The **frontier** is every open, unblocked, unclaimed child: the edge of what's known.

The answer is not part of the body. It's recorded when the ticket resolves (see Working the map). Anything made while resolving a ticket is linked from the issue, never pasted into it.

## Ticket types

Every ticket is either **HITL** (human in the loop: resolved together with a human who answers for themselves) or **AFK** (the agent works alone). A HITL ticket only resolves through that live exchange. The agent never fills in the human's side; an interviewer answering its own questions has broken the rule.

- **Research** (AFK): reading docs, third-party APIs or local knowledge to surface a fact a decision is waiting on. Resolved by a subagent that calls the Skill tool with "kal:investigate". Use it when the knowledge lives outside the current repo.
- **Prototype** (HITL): raise the fidelity of the discussion with something cheap and concrete to react to: an outline, a rough draft, a stub, or UI or logic code. Call the Skill tool with "kal:prototype" and link the result from the ticket. Use it when the real question is "how should it look?" or "how should it behave?".
- **Interrogate** (HITL): a conversation, and the default type. Call the Skill tool twice, with "kal:interrogate" and "kal:domain-language".
- **Task** (HITL or AFK): hands-on work that must happen before a *decision* can be made. There's nothing to decide, prototype or research, but the discussion is stuck until it's done: signing up for a service to evaluate its API, getting access, loading sample data to see its shape. It's the one type that *does* rather than decides, and it justifies itself by unblocking a decision, not by delivering the destination. The agent does it alone where it can (AFK); otherwise it gives the user an exact checklist (HITL). It resolves when the work is done, and the answer records what was done plus any facts later tickets depend on (where credentials live, new URLs, row counts).

## The fog

The map is incomplete on purpose: don't chart what you can't see yet. Beyond the live tickets is the **fog**: the dim outline of decisions and investigations you know are coming but can't pin down, because they depend on questions still open. Each resolved ticket clears some fog, and whatever has become specifiable graduates into new tickets, until the route is clear and no tickets remain.

The map's **Not yet specified** section is where that outline is written down: the suspected question, the area to come back to. It's the uncharted territory *towards* the destination; everything in it is in scope, just not sharp enough to ticket. Write as loosely or fully as you can see. It also tells collaborators where the effort is heading.

**Fog or ticket?** The test is whether you can phrase the question precisely now, *not* whether you can answer it now.

- **Ticket** when the question is already sharp, even if it's blocked and can't be worked yet.
- **Not yet specified** when you can't phrase it that sharply. Don't pre-cut the fog into ticket-sized pieces: it's coarser than a ticket, and one patch may become several tickets, or none, once the frontier reaches it.

Not yet specified never holds what's already decided (Decisions so far), what's already a live ticket, or what's out of scope.

## Out of scope

Fog only gathers *towards* the destination. The destination sets the scope, so anything past it is **out of scope**: not fog, and not part of Not yet specified. It has its own **Out of scope** section listing work consciously excluded from *this* effort. It lands there because of scope, not because it's blurry.

Out-of-scope work never graduates, because the frontier stops at the destination. It only returns if the destination is redrawn, and then as a new effort, not a continuation.

Ruling something out is a scoping act, not a step on the route. When an existing ticket turns out to lie past the destination (scoped in by mistake while charting, or revealed by an answer), **close it** so it's clearly off the frontier, and add one line to **Out of scope**: the gist, why it's out, and a link to the closed ticket. It stays out of Decisions so far, which records only the route actually walked.

## Running it

Two modes. In either, **resolve at most one ticket per session**, except research tickets.

### Charting a new map

The user arrives with a loose idea.

1. **Name the destination.** Call the Skill tool with "kal:interrogate" and "kal:domain-language" to pin down what the map is heading for: the spec, decision or change. The destination fixes the scope, so settle it first.
2. **Survey the frontier.** Interrogate again, this time **breadth-first**: cover the whole space instead of going deep on one thread, surfacing the open decisions and the first steps that can be taken now. **If no fog turns up** (the route is already clear and the whole thing fits in one session), there's no need for a map. Stop and ask the user how they want to proceed, offering `/kal:interrogate-and-record` then `/kal:write-spec` as the recommended path.
3. **Create the map** (label `pathfinder:map`) with Destination and Notes filled in, Decisions so far empty, and the fog sketched into Not yet specified.
4. **Create the tickets you can specify now** as child issues of the map. Then wire the blocking links in a **second pass**, because issues need ids before they can reference each other. Write any cross-references in that pass too, using real ids: a placeholder like `#<n>` auto-links to some unrelated issue. Wiring sorts tickets into the frontier and the blocked. Anything you can't specify yet stays in the fog.
5. **Launch the research.** For each `research` ticket just created, start a subagent that calls the Skill tool with "kal:investigate", all in parallel. Each saves its findings on a throwaway `research/<name>` branch and leaves a pointer to it on the ticket. Push the branch but open no PR: it is never merged.
6. **Stop.** Charting is a session's whole job; it resolves nothing by hand.

### Working the map

The user arrives with a map (URL or number). A ticket is **optional**: without one, you pick the next decision, not the user.

1. **Load the map**: the low-resolution view, not every ticket body.
2. **Pick the ticket.** If the user named one, use it. Otherwise take the first frontier ticket in map order. **Claim it** by assigning it before doing anything else.
3. **Resolve it** as the type its `pathfinder:<type>` label says. Read the label: the body never states the type. **Zoom in as needed**: fetch the full body of any related or closed ticket when you need it, and call the Skill tool for any skills the map's Notes name. When unsure, call "kal:interrogate" and "kal:domain-language".
4. **Record the answer**: post it as a **resolution comment**, **close** the ticket, and **add a pointer** (gist plus link) to the map's Decisions so far.
5. **Update the map.** Create newly surfaced tickets (create, then wire). Graduate any fog the answer has made specifiable, removing each graduated patch from Not yet specified so it lives only as its new ticket. If the answer shows a ticket (this one or another) lies past the destination, **rule it out of scope** instead of resolving it on the route. If the decision invalidates other parts of the map, update or delete those tickets.
6. **When the frontier and the fog are both empty**, the route is clear. If the destination is a spec, use AskUserQuestion to offer writing it now (recommended), or stopping here. If they accept, call the Skill tool with "kal:write-spec".

The user may run unblocked tickets in parallel sessions, so expect other sessions to be editing the tracker at the same time.
