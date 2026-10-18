# When to Mock

Mock only at **system boundaries**:

- external APIs (email, SMS, payment providers, a book-metadata service)
- databases, sometimes (a test database is usually better)
- time and randomness
- the file system, sometimes

Never mock:

- your own classes or modules
- internal collaborators
- anything you control

## Designing for mocks at the boundary

Make boundary interfaces easy to stand in for.

**1. Inject dependencies**

Pass external dependencies in instead of constructing them inside:

```typescript
// Easy to mock
function sendOverdueNotice(loan, mailer) {
  return mailer.send(loan.member.email, overdueMessage(loan));
}

// Hard to mock
function sendOverdueNotice(loan) {
  const mailer = new SmtpMailer(process.env.SMTP_URL);
  return mailer.send(loan.member.email, overdueMessage(loan));
}
```

**2. Prefer SDK-style interfaces to one generic fetcher**

Give each external operation its own function instead of one function with branching logic:

```typescript
// GOOD: each function can be mocked independently
const catalogue = {
  getBook: (isbn) => fetch(`/books/${isbn}`),
  searchBooks: (query) => fetch(`/books?q=${encodeURIComponent(query)}`),
  reserveCopy: (isbn) => fetch(`/books/${isbn}/reserve`, { method: "POST" }),
};

// BAD: the mock has to branch on its arguments
const catalogue = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

With the SDK shape:

- each mock returns one specific shape,
- test setup needs no conditional logic,
- it's obvious which endpoints a test touches,
- every endpoint is typed on its own.
