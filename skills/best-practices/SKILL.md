---
name: best-practices
description: The baseline coding standard kal checks code against when a repo documents little or nothing of its own. Covers naming, simplicity, immutability, error handling, types, async, comments, tests, and a code-smell baseline. Use when reviewing code quality, running the standards check, or writing code in a repo with no documented conventions.
---

# Best Practices

This is the **floor**, not the ceiling. It applies only where the repo is silent.

## Layering: who wins

Check sources in this order. A higher layer always overrides a lower one.

1. **The repo's own docs**: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, and lint/format config. If the repo endorses something this skill would flag, drop the flag.
2. **This skill's principles** (below).
3. **The smell baseline** (at the end). Smells are always judgement calls, never hard violations.

Skip anything a formatter, linter or type checker already enforces. Tooling catches it faster than a reviewer.

When you report a finding, cite its source: the repo doc and rule, "best-practices: <principle>", or "possible <smell>".

## Principles

- **Readable first.** Code is read far more often than it's written. Prefer names that explain over comments that explain.
- **Simplest thing that works.** No premature optimization, no cleverness that costs the next reader time.
- **Don't repeat logic.** Extract a shape the second time it appears with the same meaning, not the second time it merely looks similar.
- **Build only what's needed.** No parameters, hooks or layers for requirements nobody has.

## Naming

Variables say what they hold. Booleans read as questions. Functions start with a verb.

```typescript
// Good
const overdueLoans = loans.filter(isOverdue)
const hasActiveHold = holds.some((h) => h.memberId === member.id)
async function renewLoan(loanId: string) {}

// Bad
const list = loans.filter(check)
const flag = holds.some((h) => h.memberId === member.id)
async function loan(id: string) {}
```

## Immutability by default

Return new values instead of changing the ones you were given. Mutate only when there's a measured reason, and say so in a comment.

```typescript
// Good
const renewed = { ...loan, dueDate: addDays(loan.dueDate, 14) }
const queue = [...holdQueue, newHold]

// Bad
loan.dueDate = addDays(loan.dueDate, 14)
holdQueue.push(newHold)
```

## Errors

- Fail loudly at the point you can say what went wrong; don't swallow errors in empty `catch` blocks.
- Check results that can fail (HTTP status, parse results) before using them.
- Wrap low-level errors with context the caller can act on. Log internals on the server; show users a plain message.

```typescript
async function fetchMember(id: string): Promise<Member> {
  const res = await fetch(`/api/members/${id}`)
  if (!res.ok) throw new Error(`Member ${id} lookup failed: HTTP ${res.status}`)
  return res.json()
}
```

## Types

Model the domain precisely. Union types over loose strings, no `any` in production code.

```typescript
type LoanStatus = 'active' | 'overdue' | 'returned'
interface Loan { id: string; memberId: string; dueDate: Date; status: LoanStatus }
```

## Async

Run independent work concurrently. Await in sequence only when a step needs the previous one's result.

```typescript
const [member, loans, holds] = await Promise.all([getMember(id), getLoans(id), getHolds(id)])
```

## Control flow

Guard clauses beat nesting. Return early, keep the happy path at the left margin.

```typescript
function canRenew(loan: Loan, member: Member): boolean {
  if (member.suspended) return false
  if (loan.status !== 'active') return false
  if (loan.renewals >= MAX_RENEWALS) return false
  return !hasHoldFromAnotherMember(loan)
}
```

Name unexplained numbers: `MAX_RENEWALS = 2`, `GRACE_PERIOD_DAYS = 3`. Common literals (0, 1, HTTP codes, 1000 ms) don't need names.

## Size

A function doing several jobs should be split by job, not by line count. Exhaustive switches, config objects and test tables can be long. A file that changes for many unrelated reasons should be split by reason.

## Comments

Explain **why**, never what. A comment that restates the code is noise; one that records a constraint saves the next reader an hour.

```typescript
// The catalog API rate-limits at 10 req/s; back off instead of hammering it during outages.
const delay = Math.min(1000 * 2 ** attempt, 30_000)
```

Document public interfaces (exported functions, endpoints) with their contract: inputs, outputs, errors. Self-describing internal helpers need nothing.

## Frontend (when applicable)

- Components typed with explicit props; one job per component.
- State updates that depend on previous state use the functional form.
- Clear conditional rendering over nested ternaries.
- Effects list every dependency; no state updates during render.
- Stable keys from data, never the array index for reorderable lists.

## APIs (when applicable)

- Resource-oriented routes (`GET /members/:id/loans`, `POST /loans`), filtering through query params.
- One consistent response and error shape across endpoints.
- Validate every request body at the boundary with a schema; return 400 with field-level detail.
- Fetch only the columns you need, and paginate anything user-facing.

## Tests

- Test names describe behavior: "rejects renewal when another member holds the book", not "test renew".
- Arrange, act, assert. One behavior per test.
- Expected values come from an independent source (a literal, the spec), never recomputed the way the code computes them.

## Smell baseline

Judgement calls only. Name the smell ("possible Feature Envy") and quote the code. Each reads *what it looks like → the usual fix*.

- **Mysterious Name**: a name that doesn't reveal what the thing does or holds → rename; if no honest name comes, the design is unclear.
- **Duplicated Code**: the same logic shape in more than one place in the change → extract it once, call it from both.
- **Feature Envy**: a function more interested in another object's data than its own → move it next to the data.
- **Data Clumps**: the same few fields or parameters always travel together → give them one type.
- **Primitive Obsession**: a string or number standing in for a domain concept → give the concept a small type.
- **Repeated Switches**: the same branching on the same type in several places → one shared map, or polymorphism.
- **Shotgun Surgery**: one logical change forces scattered edits across many files → gather what changes together.
- **Divergent Change**: one module edited for several unrelated reasons → split it so each part changes for one reason.
- **Speculative Generality**: abstractions, parameters or hooks no requirement asks for → delete and inline until a real need appears.
- **Message Chains**: callers walking `a.b().c().d()` → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that only forwards calls → remove it and call the real target.
- **Refused Bequest**: a subclass that ignores or overrides most of what it inherits → replace inheritance with composition.
