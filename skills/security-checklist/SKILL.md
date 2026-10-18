---
name: security-checklist
description: The security checklist kal's security worker reviews against, with safe and unsafe patterns for secrets, input validation, injection, auth, XSS, CSRF, rate limiting, data exposure and dependencies, plus a pre-deploy checklist. Use when code handles authentication, user input, database queries, file paths, external calls, crypto or secrets, or before a production deploy.
---

# Security Checklist

Work through each section that the change touches. For cloud, CI/CD and infrastructure changes, also use [CLOUD.md](CLOUD.md).

Examples use TypeScript; the rule behind each applies in any language.

## 1. Secrets

Never put a secret in source, and fail fast when one is missing.

```typescript
// Unsafe
const catalogKey = 'ck_live_8f2a...'

// Safe
const catalogKey = process.env.CATALOG_API_KEY
if (!catalogKey) throw new Error('CATALOG_API_KEY is not set')
```

- [ ] No keys, tokens, passwords or credentialed connection strings in code or committed config.
- [ ] Local env files (`.env`, `.env.local`) are gitignored; only `.env.example` with placeholders is committed.
- [ ] No secrets in git history (check `git log -p` for the changed files if in doubt).
- [ ] Production secrets live in the hosting platform or a secrets manager.

## 2. Input validation

Validate everything that crosses a trust boundary, with a schema and an allowlist, before using it.

```typescript
const PlaceHold = z.object({
  bookId: z.string().uuid(),
  pickupBranch: z.enum(['central', 'north', 'east']),
  note: z.string().max(200).optional(),
})
const hold = PlaceHold.parse(await req.json()) // reject with 400 on failure
```

File uploads: check size, MIME type **and** extension against allowlists, store outside the web root under a generated name, and never trust the client's filename.

- [ ] Request bodies, params, headers and query strings validated at the boundary.
- [ ] Allowlists, not blocklists.
- [ ] Uploads bounded in size and restricted in type.
- [ ] Validation errors don't echo internals.

## 3. Injection

Never build queries or shell commands out of strings.

```typescript
// Unsafe: SQL injection
await db.query(`SELECT * FROM members WHERE email = '${email}'`)

// Safe: the value travels separately from the query text
await db.query('SELECT * FROM members WHERE email = ?', [email])
```

(Use your driver's placeholder syntax. Postgres drivers number their placeholders, MySQL uses `?`.)

Shell: call programs with an argument array (`execFile('convert', [input, output])`), never interpolate into a shell string. Paths built from user input: resolve and confirm they stay inside the intended directory.

- [ ] All queries parameterized; ORM raw-query escapes used correctly.
- [ ] No user input in shell strings.
- [ ] User-influenced file paths can't traverse out of their directory.

## 4. Authentication and authorization

```typescript
// Unsafe: token readable by any injected script
localStorage.setItem('session', token)

// Safe
res.setHeader('Set-Cookie', `session=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`)
```

Check permission on the server for **every** sensitive action, against the requester, not against anything the client sent:

```typescript
async function waiveFine(fineId: string, requester: User) {
  if (requester.role !== 'librarian') throw new ForbiddenError()
  // ...
}
```

Where the database supports row-level security, enable it so a missed check in app code doesn't leak other members' rows.

- [ ] Passwords hashed with bcrypt, scrypt or argon2; compared with the library's constant-time check.
- [ ] Session tokens in httpOnly, Secure cookies.
- [ ] Every protected route and action checks auth and role server-side.
- [ ] Users can only reach their own records (no ID-swapping).

## 5. XSS

Render user content as text. If you must render user HTML, sanitize it with an allowlist first.

```typescript
const clean = DOMPurify.sanitize(review.html, { ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p'], ALLOWED_ATTR: [] })
```

Set a strict Content-Security-Policy (`default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'`) and loosen it only per source with a reason. `'unsafe-inline'` and `'unsafe-eval'` are debt, not defaults.

- [ ] No raw HTML from users without sanitizing.
- [ ] CSP set.
- [ ] Framework auto-escaping not bypassed casually.

## 6. CSRF

- [ ] State-changing requests require a CSRF token, or rely on `SameSite=Strict`/`Lax` cookies plus an origin check.
- [ ] No state changes on `GET`.

## 7. Rate limiting

- [ ] Public and auth endpoints are rate limited (per IP, and per user once logged in).
- [ ] Expensive operations (search, exports, password reset, anything that sends email) have tighter limits.

## 8. Data exposure

```typescript
// Unsafe
log.info('login', { email, password })
return Response.json({ error: err.message, stack: err.stack }, { status: 500 })

// Safe
log.info('login', { memberId })
log.error('renewal failed', err)
return Response.json({ error: 'Something went wrong. Please try again.' }, { status: 500 })
```

- [ ] No passwords, tokens or personal data in logs.
- [ ] Users see generic errors; details stay in server logs.
- [ ] No stack traces in responses.
- [ ] HTTPS enforced; personal data encrypted at rest where stored.

## 9. Dependencies

Use the stack's audit: `npm audit` / `pnpm audit`, `pip-audit`, `govulncheck`, `cargo audit`.

- [ ] No known high or critical vulnerabilities in what this change adds or upgrades.
- [ ] Lockfile committed; CI installs from it (`npm ci` or equivalent).

## 10. Test the controls

Security behavior deserves tests at the interface:

```typescript
test('a member cannot waive a fine', async () => {
  const res = await api.post(`/fines/${fineId}/waive`, { as: member })
  expect(res.status).toBe(403)
})
```

Cover: unauthenticated → 401, wrong role → 403, invalid input → 400, flooding → 429.

## Pre-deploy checklist

- [ ] Secrets only in env or a secrets manager
- [ ] All input validated
- [ ] Queries parameterized, no shell interpolation
- [ ] User content sanitized; CSP set
- [ ] CSRF protection on
- [ ] Session tokens in httpOnly cookies
- [ ] Authorization on every sensitive action; row-level security where available
- [ ] Rate limits on
- [ ] HTTPS and security headers (CSP, `X-Frame-Options`/`frame-ancestors`, `X-Content-Type-Options`)
- [ ] Errors and logs free of sensitive data
- [ ] Dependency audit clean
- [ ] CORS limited to known origins
- [ ] Uploads bounded and typed

References: OWASP Top 10 (owasp.org/www-project-top-ten), PortSwigger Web Security Academy (portswigger.net/web-security).
