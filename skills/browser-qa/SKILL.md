---
name: browser-qa
description: Check a running web app the way a user would, through the chrome-devtools MCP: console and network health, interactions against acceptance criteria, screenshots, and in full mode breakpoints, accessibility and Web Vitals. Ends with a PASS/CHANGES verdict and a SHIP / SHIP WITH FIXES / DO NOT SHIP summary. Use when a kal QA worker checks a user-visible ticket or a finished spec, or when the user wants a feature tested in the browser.
---

# Browser QA

Drive the app through the **chrome-devtools** MCP tools. Each QA worker gets its own isolated Chrome, so other workers can't interfere.

Tools you'll use (names as the server exposes them; if one is missing in the installed version, use the nearest equivalent and note it in the report):

| Job | Tools |
|---|---|
| Open and move around | `new_page`, `navigate_page`, `select_page`, `wait_for` |
| See the page | `take_snapshot` (accessibility tree with element ids), `take_screenshot` |
| Act like a user | `click`, `fill`, `fill_form`, `type_text`, `press_key`, `hover`, `handle_dialog` |
| Health | `list_console_messages`, `list_network_requests`, `get_network_request` |
| Viewport | `resize_page`, `emulate` |
| Performance | `performance_start_trace`, `performance_stop_trace`, `performance_analyze_insight` |
| Accessibility | `lighthouse_audit`, `take_snapshot`, `evaluate_script` |

Use `take_snapshot` to find elements before you click. Its ids are stable; guessed selectors aren't.

## Safety: read-only by default

- Never run a journey that changes real data (deleting records, payments, mass updates) against production. Mutating journeys need an explicit opt-in **and** a local, staging or preview URL.
- Log in only with seeded test credentials, never real accounts.
- Redact tokens, credentials and personal data before saving any screenshot.

## Setup

Use the URL or port your brief gives you. If none is given, start the app with the `Dev server` line from `CLAUDE.md`'s `## Commands` block, substituting your port. Wait for it to answer before testing.

## Ticket mode (per ticket)

For a user-visible ticket, check exactly what the ticket promises.

1. **Smoke**: open the affected page(s).
   - Console: any errors? Ignore analytics and third-party noise. An error that the integration branch's same page also logs is **pre-existing**: report it as such, it doesn't fail the ticket.
   - Network: any 4xx or 5xx responses from the app's own endpoints?
2. **Each acceptance criterion**: perform it as a user would (navigate, fill, click), then confirm the visible result. Also check the obvious failure path: invalid input shows a clear error state, not a crash or a blank page.
3. **One screenshot per criterion**, saved to your round folder as `qa-<NN>.png` (NN = criterion number), showing the state that proves it.

## Full mode (end of spec)

Everything from ticket mode across the whole feature, plus:

1. **Breakpoints**: screenshot each key page at 375, 768 and 1440 px wide (`resize_page`). Look for overflow, overlapping or clipped elements, and missing content. Check dark mode if the app has one.
2. **Visual regression**: compare against committed baseline screenshots if the repo has them. **No baseline means the visual result is INCONCLUSIVE.** Never report a silent pass.
3. **Accessibility**:
   - Run `lighthouse_audit` (accessibility category) on each key page and report WCAG 2.2 AA violations: contrast, missing labels or alt text, focus order.
   - Tab through each journey with `press_key` to confirm everything is reachable and visibly focused, and check landmarks in `take_snapshot`.
   - An automated pass covers only part of WCAG. Never report "accessible" from it alone.
4. **Web Vitals**: trace the main pages. Targets: LCP under 2.5 s, CLS under 0.1, INP under 200 ms.
5. **Navigation**: every nav link resolves; no dead links.

## Report

```markdown
## Browser QA: <ticket NN | spec> at <sha>

### Smoke
- Console: 0 errors (1 pre-existing: <message>, also on the integration branch)
- Network: all 2xx/3xx

### Acceptance criteria
- [x] 1. Member can renew a loan from the loan list (qa-01.png)
- [ ] 2. Renewal is refused when another member holds the book: no error shown, button stays enabled (qa-02.png)

### Full mode only
- Breakpoints: 375 px: hold queue table overflows horizontally (qa-375-holds.png)
- Visual regression: INCONCLUSIVE (no baselines)
- Accessibility: 2 AA violations: <what, where>
- Web Vitals: LCP 1.4 s, CLS 0.01, INP 120 ms

Summary: SHIP | SHIP WITH FIXES | DO NOT SHIP
Verdict: PASS | CHANGES
At: <sha>
```

- **CHANGES**: any acceptance criterion fails, or there's a new console error or failed request, or (in full mode) a layout breakage or AA violation.
- **PASS**: everything else. Pre-existing issues and INCONCLUSIVE visuals are noted but don't block.
