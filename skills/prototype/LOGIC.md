# Logic Prototype

One self-contained HTML file, a **shareable demo**, that lets anyone push a state model around by clicking buttons. Use it when the question is about **business rules, state transitions or data shape**: things that read fine in a spec and only feel wrong once real cases run through them.

Nothing to install, so it can go to a librarian, a designer or a product owner, who can feel the model for themselves. That means it speaks their language, not the code's.

## When this mode fits

- "Can a member place a hold on a book they already have on loan?"
- "Does the data model cope with a renewal arriving after the loan went overdue?"
- "I want to try the API's shape before writing it."
- Anything where someone wants to **press buttons and watch the state change**.

If the question is what something should look like, use [UI.md](UI.md) instead.

## Process

### 1. Write the question down

Before any code, state the model being explored and the question it should answer, in one paragraph shown at the top of the page (visible text, not a comment). A demo that answers the wrong question is wasted, and writing it down lets anyone check it later, whether the user is watching now or opens it hours later.

### 2. Keep the logic in a liftable module

Put the logic that answers the question in one `<script>` block, written as a small pure module that could be copied into the real codebase. The page around it is disposable; this module is not.

Pick the shape that matches the question:

- **Pure reducer** `(state, action) => state`: discrete events, one state value.
- **State machine**: explicit states and transitions, best when "which actions are allowed right now" is part of the question.
- **Pure functions over a plain data type**: transformations with no implicit current state.
- **A class or module with a clear method surface**: when the logic genuinely owns ongoing internal state.

Choose for the question, not for whatever is easiest to wire to buttons. Keep it pure: no DOM, no `document`, no click handlers inside it. The page calls the module; nothing flows back. That is what lets the validated reducer, machine or functions move into the real code untouched once the question is settled.

### 3. Build the HTML file

One file of plain HTML, CSS and JavaScript, all inline: no framework, no bundler, no server. It must open by double-click and survive being emailed.

Write every label in **domain language**: buttons and state read like the library, not like the reducer ("Return book", "Fine owed: $1.50", not `dispatch({type: 'RETURN'})`). Explain what is happening in plain words.

Top to bottom:

1. **Title and one-line summary** of what the demo explores (the question from step 1).
2. **Current state**, shown as a readable panel with labelled fields, not a JSON dump, re-rendered after every click. Highlight what just changed where that helps a non-developer follow along.
3. **Free-play buttons**, one per action and always available, so anyone can poke at the model in any order.
4. **Guided scenarios**, one per tab. Each tab has a short plain-language description (the setup and what to watch for) and below it the **buttons to press, in order**. Each step is a real button that performs the action and advances to the next step. Starting a scenario resets to a known initial state so it plays out the same way every time.

Pick scenarios that expose the awkward cases: the happy path, a tricky edge case, and an attempt at something that should be refused.

Clean and restrained: good typography, generous spacing, one accent colour, no animation, nothing that competes with the state and the buttons.

### 4. Hand it over

Send the file or open it for them. The valuable moments are "wait, that shouldn't be allowed" and "huh, I expected X". Those are bugs in the *idea*, which is exactly what the prototype is for. If they ask for new actions or scenarios, add them; prototypes evolve.

### 5. Capture the answer and the prototype

Once it has answered its question, record the answer and capture the prototype as described in [SKILL.md](SKILL.md). For this mode: the validated reducer, machine or functions move into the real module (the decision, absorbed), and the HTML shell goes to the throwaway branch as a primary source. As a single file, it stays trivially re-runnable there.

## Anti-patterns

- **Adding tests.** A prototype that needs tests has stopped being a prototype.
- **Connecting the real database.** Use in-memory state unless persistence is the question.
- **Generalising.** No "what if we later support X". One question.
- **Mixing logic into the page.** If the pure module touches the DOM, `document` or handlers, it can no longer be lifted out.
- **Frameworks, bundlers or servers.** Anything beyond one double-clickable file breaks "shareable".
- **Shipping the HTML shell.** The page exists to be clicked by hand. The module behind it is what's worth keeping.
