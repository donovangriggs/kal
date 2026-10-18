---
name: domain-language
description: Actively build and tighten a project's domain model: challenge terms, probe edge cases, and write GLOSSARY.md entries and ADRs the moment they settle. Use when discussing what the project's terms mean, editing GLOSSARY.md, or recording or revising an architecture decision.
---

# Domain Language

Shape the project's domain model while the design is being worked out. This is the **active** practice: questioning words, inventing awkward scenarios, and writing settled terms and decisions down as soon as they settle.

Simply reading `GLOSSARY.md` to use the right words is not this skill; any skill does that in passing. Use this one when the model itself is changing.

## Where things live

Most repos are a single context:

```
/
├── GLOSSARY.md
├── docs/
│   └── adr/
│       ├── 0001-holds-expire-after-seven-days.md
│       └── 0002-fines-computed-nightly.md
└── src/
```

A `GLOSSARY-MAP.md` at the root means several contexts. It points to each one:

```
/
├── GLOSSARY-MAP.md
├── docs/
│   └── adr/                       ← decisions that span contexts
└── src/
    ├── circulation/
    │   ├── GLOSSARY.md
    │   └── docs/adr/              ← decisions local to this context
    └── membership/
        ├── GLOSSARY.md
        └── docs/adr/
```

Create files only when there's something to put in them: `GLOSSARY.md` when the first term settles, `docs/adr/` when the first ADR is needed.

## During the conversation

Any question you put to the user here (a clash, a fuzzy word, an ADR offer) goes through **AskUserQuestion**, following the rules in kal:interrogate: up to 4 questions per call, 2 to 4 options, recommended option first.

**Flag clashes with the glossary.** When the user uses a term in a way that contradicts `GLOSSARY.md`, raise it at once: "The glossary defines a Hold as a reservation on a copy, but you're describing a reservation on a title. Which is it?"

**Pin down fuzzy words.** When a term is vague or overloaded, propose one precise word: "When you say 'account', do you mean the Member or the Staff login? Those are different things."

**Test relationships with scenarios.** When concepts and their boundaries are under discussion, invent concrete cases that push on the edges: "A member returns a book a day late while it has a waiting hold. Who gets the fine, and does the hold jump the queue?"

**Check claims against the code.** When the user says how something works, see whether the code agrees, and say so if it doesn't: "The code cancels every loan on a suspended account, but you just said suspended members keep their current loans. Which is right?"

**Write settled terms immediately.** When a term settles, update `GLOSSARY.md` there and then, in the format in [GLOSSARY-FORMAT.md](./GLOSSARY-FORMAT.md). Don't save them up for later.

The glossary holds meanings only, never implementation details. It is not a spec, a scratch pad or a decision log.

**Offer ADRs rarely.** Offer one only when all three hold:

1. **Costly to undo:** changing course later would hurt.
2. **Puzzling without the backstory:** a future reader would wonder why it was done this way.
3. **A genuine choice:** there were real alternatives and one was picked for reasons.

If any of the three is missing, don't offer it. Write ADRs in the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
