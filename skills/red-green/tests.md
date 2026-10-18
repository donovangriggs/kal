# Good and Bad Tests

## Good tests

**Integration style:** exercise real interfaces, not mocks of internal parts.

```typescript
// GOOD: checks behaviour a caller can observe
test("member can renew a loan that isn't overdue", async () => {
  const member = await registerMember({ name: "Ada" });
  const loan = await lendBook(member, copyOf("Dune"));
  const renewed = await renewLoan(loan.id);
  expect(renewed.dueDate).toEqual(addDays(loan.dueDate, 14));
});
```

What makes it good:

- it checks behaviour callers care about,
- it uses only the public API,
- it survives internal refactors,
- it describes WHAT, not HOW,
- it makes one logical assertion.

## Bad tests

**Implementation-detail tests:** tied to internal structure.

```typescript
// BAD: checks that an internal collaborator was called
test("renewLoan calls dueDateCalculator.extend", async () => {
  const calc = jest.mock(dueDateCalculator);
  await renewLoan(loan.id);
  expect(calc.extend).toHaveBeenCalledWith(loan.dueDate, 14);
});
```

Warning signs:

- mocking internal collaborators,
- testing private methods,
- asserting on call counts or call order,
- the test breaks during a refactor that didn't change behaviour,
- the test name describes HOW instead of WHAT,
- verifying through some other route instead of the interface.

```typescript
// BAD: goes around the interface to check the result
test("placeHold writes a row to the holds table", async () => {
  await placeHold(member.id, "Dune");
  const row = await db.query("SELECT * FROM holds WHERE member_id = ?", [member.id]);
  expect(row).toBeDefined();
});

// GOOD: checks the result through the interface
test("a placed hold shows up in the member's holds", async () => {
  await placeHold(member.id, "Dune");
  const holds = await listHolds(member.id);
  expect(holds.map((h) => h.title)).toEqual(["Dune"]);
});
```

**Tautological tests:** the expected value restates the implementation, so the test passes by construction.

```typescript
// BAD: expected value is computed the same way the code computes it
test("totalFines adds up every overdue fine", () => {
  const fines = [{ amount: 1.5 }, { amount: 0.75 }];
  const expected = fines.reduce((sum, f) => sum + f.amount, 0);
  expect(totalFines(fines)).toBe(expected);
});

// GOOD: expected value is an independent, known literal
test("totalFines adds up every overdue fine", () => {
  expect(totalFines([{ amount: 1.5 }, { amount: 0.75 }])).toBe(2.25);
});
```
