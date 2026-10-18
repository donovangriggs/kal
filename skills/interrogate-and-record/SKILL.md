---
name: interrogate-and-record
description: A relentless interview that sharpens a plan or design and writes the domain docs (glossary terms and ADRs) as decisions land. Use when the user wants to plan a feature with docs kept in step. Invoke only when the user explicitly asks for it or accepts it as the offered next step of another kal skill.
---

Call the Skill tool twice: once with "kal:interrogate" and once with "kal:domain-language". Run the interview with both in force.

When a question is about how something should look or behave, offer to settle it with "kal:prototype" instead of debating it.

When the user confirms the shared understanding, use AskUserQuestion to offer the next step: write the spec now (recommended), or stop here. If they accept, call the Skill tool with "kal:write-spec".
