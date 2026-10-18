# GLOSSARY.md Format

## Shape

```md
# {Context name}

{One or two sentences on what this context covers and why it exists.}

## Language

**Loan**:
A copy of a title checked out to a member for a fixed period.
_Avoid_: Checkout, borrowing, rental

**Hold**:
A member's place in the queue for the next available copy of a title.
_Avoid_: Reservation, request

**Member**:
A person registered to borrow from the library.
_Avoid_: Patron, user, customer
```

## Rules

- **Pick one word.** When several words name the same idea, choose the best and list the rest under `_Avoid_`.
- **Keep it short.** One or two sentences per term. Say what the thing *is*, not what it does.
- **Only this project's concepts.** General programming ideas (retries, error types, caching) stay out, however much the project uses them. Before adding a term, ask whether it belongs to this domain or to programming in general. Only the first kind goes in.
- **Group when it helps.** Use subheadings when clusters of terms appear. A flat list is fine when everything belongs together.

## One context or several

**One context (most repos):** a single `GLOSSARY.md` at the root.

**Several contexts:** a root `GLOSSARY-MAP.md` lists each context, where its glossary lives, and how the contexts relate:

```md
# Glossary Map

## Contexts

- [Circulation](./src/circulation/GLOSSARY.md): loans, returns, holds and renewals
- [Membership](./src/membership/GLOSSARY.md): member records, cards and suspensions
- [Catalogue](./src/catalogue/GLOSSARY.md): titles, copies and search

## Relationships

- **Circulation → Membership**: Circulation emits `LoanOverdue`; Membership uses it to suspend borrowing
- **Catalogue → Circulation**: Circulation reads copy availability from Catalogue
- **Circulation ↔ Membership**: share the `MemberId` type
```

Work out which applies:

- `GLOSSARY-MAP.md` exists: read it to find the contexts.
- Only a root `GLOSSARY.md` exists: one context.
- Neither exists: create a root `GLOSSARY.md` when the first term settles.

With several contexts, work out which one the current topic belongs to. If it isn't clear, ask.
