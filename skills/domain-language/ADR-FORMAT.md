# ADR Format

ADRs live in `docs/adr/`, numbered in sequence: `0001-slug.md`, `0002-slug.md`, and so on. Create the folder only when the first ADR is written.

## Template

```md
# {Short title of the decision}

{One to three sentences: the situation, what was decided, and why.}
```

That is the whole thing. A single paragraph is a complete ADR. What matters is recording *that* the decision was made and *why*, not filling in sections.

## Optional extras

Add these only when they earn their place. Most ADRs need none of them.

- **Status** frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`): for decisions that get revisited.
- **Considered options**: only when the alternatives you turned down are worth remembering.
- **Consequences**: only when a downstream effect isn't obvious.

## Numbering

Find the highest number in `docs/adr/` and add one.

## When an ADR is worth it

All three must be true:

1. **Costly to undo.** Reversing it later would take real effort.
2. **Puzzling without the backstory.** Someone reading the code later would ask "why on earth is it like this?"
3. **A genuine choice.** Real alternatives existed and one was picked for specific reasons.

Easy to reverse? Just reverse it if needed. Unsurprising? Nobody will ask. No real alternative? There's nothing to record beyond "we did the obvious thing".

### Typical candidates

- **The overall shape.** "Circulation and Membership are separate services." "Loan history is append-only; the current state is derived from it."
- **How contexts talk.** "Circulation tells Membership about overdue loans through events, never by calling it directly."
- **Technology with lock-in.** The database, the queue, the auth provider, the hosting target. Not every library: only the ones that would take months to replace.
- **Ownership and scope lines.** "Member contact details belong to Membership; other contexts store only the member ID." The deliberate refusals matter as much as the commitments.
- **Deliberate departures from the obvious.** "Fines are computed by a nightly job, not on each return, because X." Anything a sensible reader would assume was the other way round. These stop the next person from "fixing" something intentional.
- **Constraints the code can't show.** "Member data must stay in the EU." "Catalogue search must answer in under 300ms because the kiosk times out."
- **Non-obvious rejections.** If you weighed a search engine against plain SQL and chose SQL for subtle reasons, write it down, or someone will propose the search engine again next year.
