# Domain docs

How kal skills use this repo's domain documentation while exploring the code.

## Read these first

- **`GLOSSARY.md`** at the root, or
- **`GLOSSARY-MAP.md`** at the root, if present: it points to one `GLOSSARY.md` per context. Read each one relevant to the topic.
- **`docs/adr/`**: read the ADRs that touch the area you're about to work in. In a multi-context repo, also check `src/<context>/docs/adr/` for decisions local to that context.

If any of these don't exist, **carry on silently**. Don't mention that they're missing and don't suggest creating them. `kal:domain-language` (used by `/kal:interrogate-and-record` and `/kal:pathfinder`) creates them when a term or decision actually settles.

## Layout

Single-context repo (most repos):

```
/
├── GLOSSARY.md
├── docs/adr/
│   ├── 0001-holds-expire-after-seven-days.md
│   └── 0002-fines-computed-nightly.md
└── src/
```

Multi-context repo (a `GLOSSARY-MAP.md` exists at the root):

```
/
├── GLOSSARY-MAP.md
├── docs/adr/                          ← decisions that span contexts
└── src/
    ├── circulation/
    │   ├── GLOSSARY.md
    │   └── docs/adr/                  ← decisions local to this context
    └── membership/
        ├── GLOSSARY.md
        └── docs/adr/
```

## Speak the glossary's language

Whenever your output names a domain concept (an issue title, a refactor proposal, a hypothesis, a test name), use the word the glossary defines. Don't drift into the synonyms it lists under `_Avoid_`.

If the concept you need isn't in the glossary, that's a signal. Either you're inventing language the project doesn't use (reconsider), or there's a real gap (note it for `kal:domain-language`).

## Call out ADR conflicts

If your output contradicts an existing ADR, say so explicitly rather than quietly overriding it:

> _This contradicts ADR-0002 (fines computed nightly), but it's worth reopening because…_
