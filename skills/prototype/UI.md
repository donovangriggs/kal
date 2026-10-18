# UI Prototype

Build **several radically different versions** of a screen on one route, switched with a floating bar at the bottom. The user flips between them in the browser, picks one (or takes pieces from several), and the rest get thrown away.

If the question is about logic or state rather than looks, use [LOGIC.md](LOGIC.md) instead.

## When this mode fits

- "What should the member's loans page look like?"
- "Show me a few options for the catalogue search results before we commit."
- "Try a different layout for the account settings screen."
- Any time someone would otherwise spend a day choosing between three vague mockups in their head.

## Where the variants live: strongly prefer an existing page

A UI is much easier to judge **inside the real app**: real header, real navigation, real data, real density. On an empty route every variant looks fine.

### Option A: inside an existing page (the default)

The route already exists. Render the variants **on that route**, chosen by a `?variant=` search param. Data fetching, params and auth stay exactly as they are; only the rendered subtree changes.

This still applies when the thing being designed has no page yet but would naturally sit inside one (a new panel on the dashboard, a new card in settings, a new step in an existing flow). Mount the variants inside the host page.

### Option B: a new page (last resort)

Only when the thing genuinely has nowhere to live, such as a brand-new top-level area or a flow that can't sensibly be embedded. Create a **throwaway route** using the project's existing routing convention, named so it is obviously a prototype (put `prototype` in the path or filename), with the same `?variant=` mechanism.

Before choosing B, check again that no existing page could host it. An empty route hides problems a populated one would reveal.

The floating bar is identical in both options.

## Process

### 1. State the question and pick N

Default to **3 variants**, cap at **5**. Past that they stop being radically different and become noise.

Write the plan in one line at the prototype's location or in a comment at the top of the file, so it holds whether or not the user is around to push back:

> "Three variants of the loans page, switchable via `?variant=`, on the existing `/account/loans` route."

### 2. Draft structurally different variants

Each variant respects:

- the page's purpose and the data it actually has,
- the project's component library and styling approach (Tailwind, shadcn, MUI, plain CSS, whatever is in use),
- a clear exported name: `VariantA`, `VariantB`, `VariantC`.

Variants must differ in **structure**: layout, information hierarchy, primary action. Colour changes don't count. Three card grids with different padding is wallpaper, not a prototype. If two drafts come out too similar, redo one with an explicit constraint such as "no card grid".

### 3. Wire up a switcher

One switch on the route:

```tsx
// sketch only, adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA loans={loans} member={member} />}
    {variant === 'B' && <VariantB loans={loans} member={member} />}
    {variant === 'C' && <VariantC loans={loans} member={member} />}
    <PrototypeSwitcher variants={['A', 'B', 'C']} current={variant} />
  </>
);
```

Option A: keep all existing data fetching above the switch; only the subtree changes per variant.
Option B: the throwaway route (e.g. under `/prototype/<name>`) mounts the same switch.

### 4. Build the floating bar

A small fixed bar, bottom centre, with:

- **left arrow**: previous variant, wrapping around,
- **label**: the current key, plus the variant's name if it exports one, e.g. `B (Timeline layout)`,
- **right arrow**: next variant, wrapping around.

Behaviour:

- Arrows update the URL param through the framework's router (`router.replace` in Next, `navigate` in React Router, and so on), so a variant can be shared and survives a reload.
- The `←` and `→` keys also cycle, except while focus is in an `<input>`, `<textarea>` or `[contenteditable]`.
- It looks clearly separate from the design under test: high-contrast pill, soft shadow.
- It never renders in production: gate it on `process.env.NODE_ENV !== 'production'` or the equivalent, so an accidental merge can't ship it.

Make it one shared component that both options reuse, stored wherever shared UI lives in the project.

### 5. Hand it over

Give the URL and the `?variant=` keys. The best feedback usually sounds like **"the header from B with the list from C"**, which is the design they actually want.

### 6. Capture the answer and clean up

Once a variant wins, record the answer (which one and why), then capture the prototype as described in [SKILL.md](SKILL.md). The winner goes into the real code; everything else goes to the throwaway branch, not main:

- **Option A:** fold the winner into the existing page; remove the losing variants and the switcher from main.
- **Option B:** promote the winner to a real route; remove the throwaway route and the switcher from main.

The complete set of variants is the primary source, so it is kept on the throwaway branch rather than deleted. Variant components and switchers left on main rot quickly and confuse the next reader.

## Anti-patterns

- **Variants that only change colour or copy.** That's a tweak. Real variants disagree about structure.
- **Sharing too much between variants.** A shared header is fine; a shared layout defeats the point. Each variant should be free to throw the layout away.
- **Real mutations.** Read-only is fine. If a variant must mutate, point it at a stub: the question is how it looks, not whether the back end works.
- **Promoting prototype code straight to production.** It was written without tests or error handling. Rewrite it properly when you fold it in.
