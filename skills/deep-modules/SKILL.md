---
name: deep-modules
description: Shared vocabulary and principles for designing deep modules (much behaviour behind a small interface, at a clean seam). Use when designing or improving a module's interface, looking for deepening opportunities, deciding where a seam belongs, making code more testable or easier for agents to navigate, or when another skill needs these terms.
---

# Deep Modules

Design **deep modules**: plenty of behaviour behind a small interface, sitting at a clean seam, testable through that interface. Use this language and these principles wherever code is being designed or restructured. The aim is leverage for callers, locality for maintainers, and testability for everyone.

## Terms

Use these words exactly. Don't swap in "component", "service", "API" or "boundary": a consistent vocabulary is the point.

**Module**: anything with an interface and an implementation. Deliberately size-agnostic: a function, a class, a package, or a slice spanning several tiers. _Avoid_: unit, component, service.

**Interface**: everything a caller must know to use the module correctly. That includes the type signature, but also invariants, ordering rules, error modes, required configuration and performance characteristics. _Avoid_: API, signature (both mean only the type-level surface).

**Implementation**: the code inside a module. Not the same as an **adapter**: something can be a small adapter with a big implementation (a Postgres repository) or a big adapter with a small implementation (an in-memory fake). Say "adapter" when the seam is the topic, "implementation" otherwise.

**Depth**: leverage at the interface, meaning how much behaviour a caller (or a test) can reach per unit of interface it has to learn. A module is **deep** when a lot of behaviour sits behind a small interface, and **shallow** when the interface is nearly as complicated as what it hides.

**Seam** _(Michael Feathers)_: a place where behaviour can change without editing that place; the *location* where a module's interface lives. Where to put a seam is its own design decision, separate from what goes behind it. _Avoid_: boundary (it collides with DDD's bounded context).

**Adapter**: a concrete thing that satisfies an interface at a seam. It names a *role* (which slot it fills), not its contents.

**Leverage**: what callers gain from depth: more capability per unit of interface learned. One implementation pays off across N call sites and M tests.

**Locality**: what maintainers gain from depth: change, bugs, knowledge and verification gather in one place instead of spreading across callers. Fix it once and it's fixed everywhere.

## Deep versus shallow

**Deep module**: small interface, a lot of implementation.

```
┌─────────────────────┐
│   Small Interface   │  ← few methods, simple parameters
├─────────────────────┤
│                     │
│  Deep Implementation│  ← complex logic kept inside
│                     │
└─────────────────────┘
```

**Shallow module**: large interface, little implementation. Avoid this.

```
┌─────────────────────────────────┐
│       Large Interface           │  ← many methods, complex parameters
├─────────────────────────────────┤
│  Thin Implementation            │  ← mostly passes things through
└─────────────────────────────────┘
```

When designing an interface, ask:

- Can there be fewer methods?
- Can the parameters be simpler?
- Can more of the complexity move inside?

## Principles

- **Depth belongs to the interface, not the implementation.** A deep module can be built from small, mockable, swappable parts inside; they just aren't part of its interface. A module can have **internal seams** (private, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If the complexity disappears with it, it was only passing things through. If the complexity reappears across N callers, it was earning its place.
- **The interface is the test surface.** Callers and tests cross the same seam. Wanting to test *past* the interface usually means the module is the wrong shape.
- **One adapter is a hypothetical seam; two adapters make it real.** Don't introduce a seam unless something actually varies across it.

## Designing for testability

Good interfaces make tests easy to write:

1. **Take dependencies in; don't create them.**

   ```typescript
   // Testable
   function chargeOverdueFine(loan, finesLedger) {}

   // Hard to test
   function chargeOverdueFine(loan) {
     const ledger = new PostgresFinesLedger();
   }
   ```

2. **Return results instead of causing side effects.**

   ```typescript
   // Testable
   function calculateFine(loan, today): Fine {}

   // Hard to test
   function applyFine(loan, today): void {
     loan.member.balance -= fineFor(loan, today);
   }
   ```

3. **Keep the surface small.** Fewer methods means fewer tests; fewer parameters means simpler setup.

## How the terms relate

- A **module** has exactly one **interface**, the surface it shows callers and tests.
- **Depth** is a property of a **module**, measured against its **interface**.
- A **seam** is where a module's **interface** lives.
- An **adapter** sits at a **seam** and satisfies the **interface**.
- **Depth** produces **leverage** for callers and **locality** for maintainers.

## Framings we reject

- **Depth as implementation lines divided by interface lines:** this rewards padding the implementation. We measure depth as leverage instead.
- **"Interface" meaning the TypeScript `interface` keyword or a class's public methods:** too narrow. Here the interface is every fact a caller must know.
- **"Boundary":** overloaded by DDD's bounded context. Say **seam** or **interface**.

## Going further

- **Deepening a cluster of modules given its dependencies:** [DEEPENING.md](DEEPENING.md) covers dependency categories, seam discipline, and replacing tests instead of layering them.
- **Exploring alternative interfaces:** [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md) runs parallel sub-agents that each design the interface a radically different way, then compares them on depth, locality and seam placement.
